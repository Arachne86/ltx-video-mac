#!/usr/bin/env python3
"""Unified Audio-Video Generator with LoRA Support.

This script extends mlx_video.generate_av to support loading and applying LoRA weights.
"""

import sys
import os
import argparse
import json
import time
from pathlib import Path
from typing import Optional, Dict

import mlx.core as mx
import mlx.nn as nn
import numpy as np

# Import internals from mlx_video
try:
    from mlx_video.models.ltx.config import LTXModelConfig, LTXModelType, LTXRopeType
    from mlx_video.models.ltx.ltx import LTXModel
    from mlx_video.models.ltx.transformer import Modality
    from mlx_video.convert import (
        sanitize_transformer_weights,
        sanitize_audio_vae_weights,
        sanitize_vocoder_weights,
    )
    from mlx_video.utils import (
        to_denoised,
        get_model_path,
        load_image,
        prepare_image_for_encoding,
    )
    from mlx_video.models.ltx.video_vae.decoder import load_vae_decoder
    from mlx_video.models.ltx.video_vae.encoder import load_vae_encoder
    from mlx_video.models.ltx.video_vae.tiling import TilingConfig
    from mlx_video.models.ltx.upsampler import load_upsampler, upsample_latents
    from mlx_video.conditioning import VideoConditionByLatentIndex, apply_conditioning
    from mlx_video.conditioning.latent import LatentState, apply_denoise_mask

    # Import logic from generate_av
    from mlx_video.generate_av import (
        STAGE_1_SIGMAS,
        STAGE_2_SIGMAS,
        DEFAULT_HF_MODEL,
        DEFAULT_UNIFIED_TEXT_ENCODER,
        is_unified_mlx_model,
        load_unified_weights,
        AUDIO_SAMPLE_RATE,
        AUDIO_LATENT_SAMPLE_RATE,
        AUDIO_MEL_BINS,
        AUDIO_LATENTS_PER_SECOND,
        create_video_position_grid,
        create_audio_position_grid,
        compute_audio_frames,
        denoise_av,
        load_audio_decoder,
        load_vocoder,
        save_audio,
        mux_video_audio,
        Colors
    )
except ImportError as e:
    print(f"Error importing mlx_video: {e}", file=sys.stderr)
    sys.exit(1)


def status_output(message: str):
    """Output status message for Swift to parse."""
    print(f"STATUS:{message}", file=sys.stderr)
    sys.stderr.flush()

def progress_output(stage: int, step: int, total_steps: int, message: str = ""):
    """Output progress for Swift to parse."""
    print(f"STAGE:{stage}:STEP:{step}:{total_steps}:{message}", file=sys.stderr)
    sys.stderr.flush()

def apply_lora_weights(model: nn.Module, lora_path: str, strength: float = 1.0):
    """Load and apply LoRA weights to the model."""
    if not os.path.exists(lora_path):
        print(f"{Colors.RED}❌ LoRA file not found: {lora_path}{Colors.RESET}", file=sys.stderr)
        return

    print(f"{Colors.MAGENTA}✨ Applying LoRA: {os.path.basename(lora_path)} (strength={strength}){Colors.RESET}", file=sys.stderr)

    try:
        lora_weights = mx.load(lora_path)
    except Exception as e:
        print(f"{Colors.RED}❌ Failed to load LoRA: {e}{Colors.RESET}", file=sys.stderr)
        return

    # Helper to sanitize keys
    def sanitize_key(key):
        # Remove prefixes
        key = key.replace("model.diffusion_model.", "")
        if key.startswith("transformer."):
             key = key.replace("transformer.", "")

        # Mapping rules
        key = key.replace(".to_out.0.", ".to_out.")
        key = key.replace(".ff.net.0.proj.", ".ff.proj_in.")
        key = key.replace(".ff.net.2.", ".ff.proj_out.")
        key = key.replace(".audio_ff.net.0.proj.", ".audio_ff.proj_in.")
        key = key.replace(".audio_ff.net.2.", ".audio_ff.proj_out.")
        key = key.replace(".linear_1.", ".linear1.")
        key = key.replace(".linear_2.", ".linear2.")

        return key

    # Group weights by target module
    lora_groups = {}

    for key, value in lora_weights.items():
        if "lora" not in key:
            continue

        if "alpha" in key:
            continue

        is_down = "lora_down" in key or "lora_A" in key
        is_up = "lora_up" in key or "lora_B" in key

        if not (is_down or is_up):
            continue

        if "lora_down" in key:
            base_name = key.split(".lora_down")[0]
            type_ = "down"
        elif "lora_up" in key:
            base_name = key.split(".lora_up")[0]
            type_ = "up"
        elif "lora_A" in key:
            base_name = key.split(".lora_A")[0]
            type_ = "down"
        elif "lora_B" in key:
            base_name = key.split(".lora_B")[0]
            type_ = "up"
        else:
            continue

        sanitized_base = sanitize_key(base_name)

        if sanitized_base not in lora_groups:
            lora_groups[sanitized_base] = {}

        lora_groups[sanitized_base][type_] = value

        alpha_key_candidates = [
            f"{base_name}.lora.alpha",
            f"{base_name}.alpha",
            f"{base_name}.lora_alpha"
        ]
        for ak in alpha_key_candidates:
            if ak in lora_weights:
                lora_groups[sanitized_base]["alpha"] = lora_weights[ak]
                break

    applied_count = 0

    for module_name, weights in lora_groups.items():
        if "down" not in weights or "up" not in weights:
            continue

        down = weights["down"]
        up = weights["up"]

        # Find module in model
        parts = module_name.split('.')
        curr = model
        valid_path = True

        for part in parts:
            if hasattr(curr, part):
                curr = getattr(curr, part)
            elif isinstance(curr, dict) and part in curr:
                curr = curr[part]
            elif isinstance(curr, dict) and part.isdigit() and int(part) in curr:
                 curr = curr[int(part)]
            elif isinstance(curr, list) and part.isdigit():
                 idx = int(part)
                 if idx < len(curr):
                     curr = curr[idx]
                 else:
                     valid_path = False; break
            elif hasattr(curr, "transformer_blocks") and part == "transformer_blocks":
                 curr = curr.transformer_blocks
            else:
                 valid_path = False
                 break

        if not valid_path or not isinstance(curr, nn.Linear):
            continue

        rank = down.shape[0]

        alpha = weights.get("alpha")
        if alpha is not None:
            if isinstance(alpha, mx.array):
                alpha = alpha.item()
            scale = alpha / rank
        else:
            scale = 1.0

        delta = (up @ down) * (scale * strength)

        if delta.dtype != curr.weight.dtype:
            delta = delta.astype(curr.weight.dtype)

        curr.weight = curr.weight + delta
        applied_count += 1

    print(f"{Colors.GREEN}✓ Applied LoRA to {applied_count} layers{Colors.RESET}", file=sys.stderr)


def generate_video_with_audio_lora(
    model_repo: str,
    text_encoder_repo: Optional[str],
    prompt: str,
    height: int = 512,
    width: int = 512,
    num_frames: int = 33,
    seed: int = 42,
    fps: int = 24,
    output_path: str = "output_av.mp4",
    output_audio_path: Optional[str] = None,
    save_audio_separately: bool = False,
    verbose: bool = True,
    enhance_prompt: bool = False,
    use_uncensored_enhancer: bool = False,
    max_tokens: int = 512,
    temperature: float = 0.7,
    image: Optional[str] = None,
    image_strength: float = 1.0,
    image_frame_idx: int = 0,
    tiling: str = "auto",
    lora_path: Optional[str] = None,
    lora_strength: float = 1.0,
):
    """Generate video with synchronized audio from text prompt, optionally conditioned on an image and LoRA."""
    start_time = time.time()

    # Validate dimensions
    assert height % 64 == 0, f"Height must be divisible by 64, got {height}"
    assert width % 64 == 0, f"Width must be divisible by 64, got {width}"

    if num_frames % 8 != 1:
        adjusted_num_frames = round((num_frames - 1) / 8) * 8 + 1
        print(
            f"{Colors.YELLOW}⚠️  Adjusted frames to {adjusted_num_frames}{Colors.RESET}"
        )
        num_frames = adjusted_num_frames

    # Calculate audio frames
    audio_frames = compute_audio_frames(num_frames, fps)

    is_i2v = image is not None
    mode_str = "I2V+Audio" if is_i2v else "T2V+Audio"
    print(
        f"{Colors.BOLD}{Colors.CYAN}🎬 [{mode_str}] Generating {width}x{height} video with {num_frames} frames + audio{Colors.RESET}"
    )
    print(
        f"{Colors.DIM}Audio: {audio_frames} latent frames @ {AUDIO_SAMPLE_RATE}Hz{Colors.RESET}"
    )
    print(
        f"{Colors.DIM}Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}{Colors.RESET}"
    )
    if is_i2v:
        print(
            f"{Colors.DIM}Image: {image} (strength={image_strength}, frame={image_frame_idx}){Colors.RESET}"
        )

    model_path = get_model_path(model_repo)

    # Check if using unified MLX model format
    use_unified = is_unified_mlx_model(model_path)
    if use_unified:
        print(
            f"{Colors.DIM}Using unified MLX model format (no Lightricks download){Colors.RESET}"
        )
        hf_model_path = model_path
        text_encoder_path = get_model_path(
            text_encoder_repo or DEFAULT_UNIFIED_TEXT_ENCODER
        )
    else:
        text_encoder_path = (
            model_path
            if text_encoder_repo is None
            else get_model_path(text_encoder_repo)
        )
        hf_model_path = model_path

    # Calculate latent dimensions
    stage1_h, stage1_w = height // 2 // 32, width // 2 // 32
    stage2_h, stage2_w = height // 32, width // 32
    latent_frames = 1 + (num_frames - 1) // 8

    mx.random.seed(seed)

    # Load text encoder with audio embeddings
    print(f"{Colors.BLUE}📝 Loading text encoder...{Colors.RESET}")
    from mlx_video.models.ltx.text_encoder import LTX2TextEncoder

    text_encoder = LTX2TextEncoder()
    text_encoder.load(
        model_path=hf_model_path,
        text_encoder_path=text_encoder_path,
        use_unified=use_unified,
    )
    mx.eval(text_encoder.parameters())

    # Optionally enhance prompt
    if enhance_prompt:
        if use_uncensored_enhancer:
            from mlx_video.models.ltx.enhance_prompt import enhance_with_model

            print(f"{Colors.MAGENTA}✨ Enhancing prompt (uncensored)...{Colors.RESET}")
            system_prompt = None
            if is_i2v:
                from mlx_video.models.ltx.enhance_prompt import _load_system_prompt
                # Fix: Look for prompt in script dir or resources
                try:
                    system_prompt = _load_system_prompt("gemma_i2v_system_prompt.txt")
                except:
                     pass # Fallback to default
            prompt = enhance_with_model(
                prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                seed=seed,
                max_tokens=max_tokens,
                verbose=verbose,
            )
        else:
            print(f"{Colors.MAGENTA}✨ Enhancing prompt...{Colors.RESET}")
            prompt = text_encoder.enhance_t2v(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                seed=seed,
                verbose=verbose,
            )
        print(
            f"{Colors.DIM}Enhanced: {prompt[:150]}{'...' if len(prompt) > 150 else ''}{Colors.RESET}"
        )
        # Capture for Swift
        print(f"ENHANCED_PROMPT: {prompt}", file=sys.stderr)

    # Get both video and audio embeddings
    video_embeddings, audio_embeddings = text_encoder(prompt)
    model_dtype = video_embeddings.dtype
    mx.eval(video_embeddings, audio_embeddings)

    del text_encoder
    mx.clear_cache()

    # Load transformer with AudioVideo config
    print(f"{Colors.BLUE}🤖 Loading transformer (A/V mode)...{Colors.RESET}")
    if use_unified:
        sanitized = load_unified_weights(model_path, "transformer.")
    else:
        raw_weights = mx.load(str(model_path / "ltx-2-19b-distilled.safetensors"))
        sanitized = sanitize_transformer_weights(raw_weights)
        sanitized = {
            k: v.astype(mx.bfloat16) if v.dtype == mx.float32 else v
            for k, v in sanitized.items()
        }

    config = LTXModelConfig(
        model_type=LTXModelType.AudioVideo,
        num_attention_heads=32,
        attention_head_dim=128,
        in_channels=128,
        out_channels=128,
        num_layers=48,
        cross_attention_dim=4096,
        caption_channels=3840,
        audio_num_attention_heads=32,
        audio_attention_head_dim=64,
        audio_in_channels=AUDIO_LATENT_CHANNELS * AUDIO_MEL_BINS,
        audio_out_channels=AUDIO_LATENT_CHANNELS * AUDIO_MEL_BINS,
        audio_cross_attention_dim=2048,
        rope_type=LTXRopeType.SPLIT,
        double_precision_rope=True,
        positional_embedding_theta=10000.0,
        positional_embedding_max_pos=[20, 2048, 2048],
        audio_positional_embedding_max_pos=[20],
        use_middle_indices_grid=True,
        timestep_scale_multiplier=1000,
    )

    transformer = LTXModel(config)
    transformer.load_weights(list(sanitized.items()), strict=False)

    # --- APPLY LORA HERE ---
    if lora_path:
        apply_lora_weights(transformer, lora_path, lora_strength)
    # -----------------------

    mx.eval(transformer.parameters())

    # Load VAE encoder and encode image for I2V conditioning
    stage1_image_latent = None
    stage2_image_latent = None
    if is_i2v:
        print(
            f"{Colors.BLUE}🖼️  Loading VAE encoder and encoding image...{Colors.RESET}"
        )
        vae_encoder = load_vae_encoder(
            (
                str(hf_model_path / "ltx-2-19b-distilled.safetensors")
                if not use_unified
                else str(model_path)
            ),
            use_unified=use_unified,
        )
        mx.eval(vae_encoder.parameters())

        input_image = load_image(
            image, height=height // 2, width=width // 2, dtype=model_dtype
        )
        stage1_image_tensor = prepare_image_for_encoding(
            input_image, height // 2, width // 2, dtype=model_dtype
        )
        stage1_image_latent = vae_encoder(stage1_image_tensor)
        mx.eval(stage1_image_latent)

        input_image = load_image(image, height=height, width=width, dtype=model_dtype)
        stage2_image_tensor = prepare_image_for_encoding(
            input_image, height, width, dtype=model_dtype
        )
        stage2_image_latent = vae_encoder(stage2_image_tensor)
        mx.eval(stage2_image_latent)

        del vae_encoder
        mx.clear_cache()

    # Initialize latents
    print(
        f"{Colors.YELLOW}⚡ Stage 1: Generating at {width//2}x{height//2} (8 steps)...{Colors.RESET}"
    )
    mx.random.seed(seed)

    video_positions = create_video_position_grid(
        1, latent_frames, stage1_h, stage1_w
    )  # float32
    audio_positions = create_audio_position_grid(1, audio_frames)  # float32
    mx.eval(video_positions, audio_positions)

    video_state1 = None
    video_latent_shape = (1, 128, latent_frames, stage1_h, stage1_w)
    if is_i2v and stage1_image_latent is not None:
        video_state1 = LatentState(
            latent=mx.zeros(video_latent_shape, dtype=model_dtype),
            clean_latent=mx.zeros(video_latent_shape, dtype=model_dtype),
            denoise_mask=mx.ones((1, 1, latent_frames, 1, 1), dtype=model_dtype),
        )
        conditioning = VideoConditionByLatentIndex(
            latent=stage1_image_latent,
            frame_idx=image_frame_idx,
            strength=image_strength,
        )
        video_state1 = apply_conditioning(video_state1, [conditioning])

        noise = mx.random.normal(video_latent_shape).astype(model_dtype)
        noise_scale = mx.array(STAGE_1_SIGMAS[0], dtype=model_dtype)  # 1.0
        scaled_mask = video_state1.denoise_mask * noise_scale
        video_state1 = LatentState(
            latent=noise * scaled_mask
            + video_state1.latent * (mx.array(1.0, dtype=model_dtype) - scaled_mask),
            clean_latent=video_state1.clean_latent,
            denoise_mask=video_state1.denoise_mask,
        )
        video_latents = video_state1.latent
        mx.eval(video_latents)
    else:
        video_latents = mx.random.normal(video_latent_shape).astype(model_dtype)
        mx.eval(video_latents)

    audio_latents = mx.random.normal(
        (1, AUDIO_LATENT_CHANNELS, audio_frames, AUDIO_MEL_BINS)
    ).astype(model_dtype)
    mx.eval(audio_latents)

    # Stage 1 denoising
    video_latents, audio_latents = denoise_av(
        video_latents,
        audio_latents,
        video_positions,
        audio_positions,
        video_embeddings,
        audio_embeddings,
        transformer,
        STAGE_1_SIGMAS,
        verbose=verbose,
        video_state=video_state1,
        stage=1,
    )

    # Upsample video latents
    print(f"{Colors.MAGENTA}🔍 Upsampling video latents 2x...{Colors.RESET}")
    upsampler = load_upsampler(
        (
            str(hf_model_path / "ltx-2-spatial-upscaler-x2-1.0.safetensors")
            if not use_unified
            else str(model_path)
        ),
        use_unified=use_unified,
    )
    mx.eval(upsampler.parameters())

    vae_model_path = (
        str(hf_model_path / "ltx-2-19b-distilled.safetensors")
        if not use_unified
        else str(model_path)
    )

    vae_decoder = load_vae_decoder(
        vae_model_path,
        timestep_conditioning=None,
        use_unified=use_unified,
    )

    # Optimization: Extract stats and unload VAE decoder to save VRAM during Stage 2
    latents_mean = vae_decoder.latents_mean
    latents_std = vae_decoder.latents_std
    del vae_decoder
    mx.clear_cache()

    video_latents = upsample_latents(
        video_latents, upsampler, latents_mean, latents_std
    )
    mx.eval(video_latents)

    del upsampler
    mx.clear_cache()

    # Stage 2: Refine at full resolution
    print(
        f"{Colors.YELLOW}⚡ Stage 2: Refining at {width}x{height} (3 steps)...{Colors.RESET}"
    )
    video_positions = create_video_position_grid(
        1, latent_frames, stage2_h, stage2_w
    )  # float32
    mx.eval(video_positions)

    video_state2 = None
    if is_i2v and stage2_image_latent is not None:
        video_state2 = LatentState(
            latent=video_latents,
            clean_latent=mx.zeros_like(video_latents),
            denoise_mask=mx.ones((1, 1, latent_frames, 1, 1), dtype=model_dtype),
        )
        conditioning = VideoConditionByLatentIndex(
            latent=stage2_image_latent,
            frame_idx=image_frame_idx,
            strength=image_strength,
        )
        video_state2 = apply_conditioning(video_state2, [conditioning])

        video_noise = mx.random.normal(video_latents.shape).astype(model_dtype)
        noise_scale = mx.array(STAGE_2_SIGMAS[0], dtype=model_dtype)
        scaled_mask = video_state2.denoise_mask * noise_scale
        video_state2 = LatentState(
            latent=video_noise * scaled_mask
            + video_state2.latent * (mx.array(1.0, dtype=model_dtype) - scaled_mask),
            clean_latent=video_state2.clean_latent,
            denoise_mask=video_state2.denoise_mask,
        )
        video_latents = video_state2.latent
        mx.eval(video_latents)

        audio_noise = mx.random.normal(audio_latents.shape).astype(model_dtype)
        one_minus_scale = mx.array(1.0, dtype=model_dtype) - noise_scale
        audio_latents = audio_noise * noise_scale + audio_latents * one_minus_scale
        mx.eval(audio_latents)
    else:
        noise_scale = mx.array(STAGE_2_SIGMAS[0], dtype=model_dtype)
        one_minus_scale = mx.array(1.0, dtype=model_dtype) - noise_scale
        video_noise = mx.random.normal(video_latents.shape).astype(model_dtype)
        audio_noise = mx.random.normal(audio_latents.shape).astype(model_dtype)
        video_latents = video_noise * noise_scale + video_latents * one_minus_scale
        audio_latents = audio_noise * noise_scale + audio_latents * one_minus_scale
        mx.eval(video_latents, audio_latents)

    video_latents, audio_latents = denoise_av(
        video_latents,
        audio_latents,
        video_positions,
        audio_positions,
        video_embeddings,
        audio_embeddings,
        transformer,
        STAGE_2_SIGMAS,
        verbose=verbose,
        video_state=video_state2,
        stage=2,
    )

    del transformer
    mx.clear_cache()

    # Decode video with tiling
    print(f"{Colors.BLUE}🎞️  Decoding video...{Colors.RESET}")

    # Reload VAE decoder for decoding
    print(f"{Colors.BLUE}🎞️  Reloading VAE decoder...{Colors.RESET}")
    vae_decoder = load_vae_decoder(
        vae_model_path,
        timestep_conditioning=None,
        use_unified=use_unified,
    )

    if tiling == "none":
        tiling_config = None
    elif tiling == "auto":
        tiling_config = TilingConfig.auto(height, width, num_frames)
    elif tiling == "default":
        tiling_config = TilingConfig.default()
    elif tiling == "aggressive":
        tiling_config = TilingConfig.aggressive()
    elif tiling == "conservative":
        tiling_config = TilingConfig.conservative()
    elif tiling == "spatial":
        tiling_config = TilingConfig.spatial_only()
    elif tiling == "temporal":
        tiling_config = TilingConfig.temporal_only()
    else:
        tiling_config = TilingConfig.auto(height, width, num_frames)

    if tiling_config is not None:
        video = vae_decoder.decode_tiled(
            video_latents, tiling_config=tiling_config, debug=verbose
        )
    else:
        video = vae_decoder(video_latents)
    mx.eval(video)

    # Unload VAE decoder immediately to save memory
    del vae_decoder
    mx.clear_cache()

    video = mx.squeeze(video, axis=0)
    video = mx.transpose(video, (1, 2, 3, 0))
    video = mx.clip((video + 1.0) / 2.0, 0.0, 1.0)
    video = (video * 255).astype(mx.uint8)
    video_np = np.array(video)

    # Decode audio
    print(f"{Colors.BLUE}🔊 Decoding audio...{Colors.RESET}")
    audio_decoder = load_audio_decoder(model_path, use_unified=use_unified)
    vocoder = load_vocoder(model_path, use_unified=use_unified)
    mx.eval(audio_decoder.parameters(), vocoder.parameters())

    mel_spectrogram = audio_decoder(audio_latents)
    mx.eval(mel_spectrogram)

    audio_waveform = vocoder(mel_spectrogram)
    mx.eval(audio_waveform)

    audio_np = np.array(audio_waveform)
    if audio_np.ndim == 3:
        audio_np = audio_np[0]

    del audio_decoder, vocoder
    mx.clear_cache()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    temp_video_path = output_path.with_suffix(".temp.mp4")

    try:
        import cv2
        h, w = video_np.shape[1], video_np.shape[2]
        fourcc = cv2.VideoWriter_fourcc(*"avc1")
        out = cv2.VideoWriter(str(temp_video_path), fourcc, fps, (w, h))
        for frame in video_np:
            out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        out.release()
    except Exception as e:
        print(f"{Colors.RED}❌ Video encoding failed: {e}{Colors.RESET}")
        return None, None

    keep_audio_file = save_audio_separately or output_audio_path is not None
    if output_audio_path is not None:
        audio_path = Path(output_audio_path)
    elif save_audio_separately:
        audio_path = output_path.with_suffix(".wav")
    else:
        import tempfile
        fd, tmp = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        audio_path = Path(tmp)

    save_audio(audio_np, audio_path, AUDIO_SAMPLE_RATE)

    if mux_video_audio(temp_video_path, audio_path, output_path):
        temp_video_path.unlink()
        if not keep_audio_file:
            audio_path.unlink()
    else:
        temp_video_path.rename(output_path)
        if not keep_audio_file:
            audio_path.unlink()

    elapsed = time.time() - start_time
    print(
        f"{Colors.BOLD}{Colors.GREEN}🎉 Done! Generated in {elapsed:.1f}s{Colors.RESET}"
    )

    return video_np, audio_np


def main():
    # Redirect stdout to stderr to prevent log pollution of the JSON output
    original_stdout = sys.stdout
    sys.stdout = sys.stderr

    parser = argparse.ArgumentParser(
        description="LTX-2 Unified Audio-Video Generation with MLX and LoRA"
    )
    parser.add_argument(
        "--prompt", "-p", type=str, required=True, help="Text prompt for generation"
    )
    parser.add_argument(
        "--height",
        "-H",
        type=int,
        default=512,
        help="Output video height (must be divisible by 64)",
    )
    parser.add_argument(
        "--width",
        "-W",
        type=int,
        default=512,
        help="Output video width (must be divisible by 64)",
    )
    parser.add_argument(
        "--num-frames",
        "-n",
        type=int,
        default=65,
        help="Number of frames",
    )
    parser.add_argument(
        "--seed", "-s", type=int, default=42, help="Random seed for reproducibility"
    )
    parser.add_argument("--fps", type=int, default=24, help="Frames per second")
    parser.add_argument(
        "--output-path", "-o", type=str, default="output.mp4", help="Output video path"
    )
    parser.add_argument(
        "--model-repo",
        type=str,
        default="notapalindrome/ltx2-mlx-av",
        help="Model repository ID",
    )
    parser.add_argument(
        "--image",
        "-i",
        type=str,
        default=None,
        help="Input image for image-to-video generation",
    )
    parser.add_argument(
        "--image-strength",
        type=float,
        default=1.0,
        help="Image conditioning strength (0.0-1.0)",
    )
    parser.add_argument(
        "--tiling",
        type=str,
        default="auto",
        choices=[
            "auto",
            "none",
            "default",
            "aggressive",
            "conservative",
            "spatial",
            "temporal",
        ],
        help="Tiling mode for VAE decoding",
    )
    parser.add_argument(
        "--no-audio",
        action="store_true",
        default=False,
        help="Disable audio generation (video only)",
    )
    parser.add_argument(
        "--repetition-penalty",
        type=float,
        default=1.2,
        help="Gemma prompt enhancement repetition penalty (1.0-2.0)",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=0.9,
        help="Gemma prompt enhancement top-p sampling (0.0-1.0)",
    )

    # LoRA arguments
    parser.add_argument(
        "--lora",
        type=str,
        default=None,
        help="Path to LoRA safetensors file",
    )
    parser.add_argument(
        "--lora-strength",
        type=float,
        default=1.0,
        help="Strength of LoRA (default: 1.0)",
    )

    # Enhancement args
    parser.add_argument(
        "--enhance-prompt", action="store_true", help="Enhance prompt using Gemma"
    )
    parser.add_argument(
        "--use-uncensored-enhancer",
        action="store_true",
        help="Use uncensored Gemma 12B for prompt enhancement",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Temperature for prompt enhancement",
    )
    parser.add_argument(
        "--save-audio-separately",
        action="store_true",
        help="Keep the .wav audio file",
    )

    args = parser.parse_args()

    try:
        status_output("Loading unified audio-video model...")

        is_i2v = args.image is not None
        mode_str = "I2V" if is_i2v else "T2V"
        status_output(
            f"Starting {mode_str} generation with audio: {args.width}x{args.height}, {args.num_frames} frames"
        )

        if args.lora:
            status_output(f"Using LoRA: {os.path.basename(args.lora)} (strength={args.lora_strength})")

        # Disable audio if requested
        if args.no_audio:
            status_output("Audio generation disabled")

        audio_label = "without" if args.no_audio else "with synchronized"
        status_output(f"Generating video {audio_label} audio...")

        generate_video_with_audio_lora(
            model_repo=args.model_repo,
            text_encoder_repo=None,
            prompt=args.prompt,
            height=args.height,
            width=args.width,
            num_frames=args.num_frames,
            seed=args.seed,
            fps=args.fps,
            output_path=args.output_path,
            output_audio_path=None,
            save_audio_separately=args.save_audio_separately,
            verbose=True,
            enhance_prompt=args.enhance_prompt,
            use_uncensored_enhancer=args.use_uncensored_enhancer,
            temperature=args.temperature,
            image=args.image,
            image_strength=args.image_strength,
            tiling=args.tiling,
            lora_path=args.lora,
            lora_strength=args.lora_strength,
        )

        status_output(f"Video with audio saved to: {args.output_path}")
        print("SUCCESS", file=sys.stderr)

        # Output JSON result for Swift to parse
        result = {
            "video_path": args.output_path,
            "seed": args.seed,
            "mode": "i2v" if is_i2v else "t2v",
            "has_audio": not args.no_audio,
        }
        print(json.dumps(result))

    except ImportError as e:
        error_msg = f"mlx-video-with-audio not installed: {e}. Run: pip install mlx-video-with-audio"
        status_output(f"ERROR: {error_msg}")
        print(json.dumps({"success": False, "error": error_msg}))
        sys.exit(1)
    except Exception as e:
        import traceback
        error_msg = f"{e}\n{traceback.format_exc()}"
        status_output(f"ERROR: {error_msg}")
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
