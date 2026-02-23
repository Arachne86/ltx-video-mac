#!/usr/bin/env python3
"""Preview enhanced prompt without running full video generation.

Outputs JSON: {"enhanced_prompt": "..."} or {"error": "..."}
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Preview Gemma-enhanced prompt")
    parser.add_argument("--prompt", "-p", required=True, help="User prompt to enhance")
    parser.add_argument(
        "--model-repo",
        default="notapalindrome/ltx2-mlx-av",
        help="Model repository (unified AV)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.9,
        help="Sampling temperature for enhancement",
    )
    parser.add_argument(
        "--image",
        default=None,
        help="Image path for I2V (uses i2v system prompt if set)",
    )
    parser.add_argument(
        "--resources-path",
        default=None,
        help="App Resources path for bundled prompts (pre-flight injection)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    try:
        # Pre-flight: inject bundled prompts if mlx_video is missing them
        if args.resources_path:
            try:
                from pathlib import Path as P
                import shutil

                resources_path = P(args.resources_path)
                bundled_prompts = resources_path / "ltx_mlx" / "models" / "ltx" / "prompts"
                import mlx_video.models.ltx.text_encoder as te

                target_dir = P(te.__file__).parent / "prompts"
                for name in ["gemma_t2v_system_prompt.txt", "gemma_i2v_system_prompt.txt"]:
                    src = bundled_prompts / name
                    dst = target_dir / name
                    if src.exists() and not dst.exists():
                        target_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)
            except Exception:
                pass  # Non-fatal

        from mlx_video.utils import get_model_path
        from mlx_video.models.ltx.text_encoder import LTX2TextEncoder

        model_path = get_model_path(args.model_repo)
        model_path = Path(model_path)

        # Unified MLX models (e.g. notapalindrome/ltx2-mlx-av) have model.safetensors but no
        # text_config in config.json. The text encoder must load from the HuggingFace model.
        is_unified = (
            (model_path / "model.safetensors").exists()
            and not (model_path / "ltx-2-19b-distilled.safetensors").exists()
        )
        if is_unified:
            text_encoder_path = get_model_path("Lightricks/LTX-2")
        else:
            text_encoder_path = model_path

        text_encoder = LTX2TextEncoder()
        text_encoder.load(model_path=model_path, text_encoder_path=text_encoder_path)
        import mlx.core as mx

        mx.eval(text_encoder.parameters())

        is_i2v = args.image is not None
        system_prompt = None
        if is_i2v:
            try:
                import mlx_video.models.ltx.text_encoder as te
                prompt_path = Path(te.__file__).parent / "prompts" / "gemma_i2v_system_prompt.txt"
                if prompt_path.exists():
                    system_prompt = prompt_path.read_text().strip()
            except Exception:
                pass

        enhanced = text_encoder.enhance_t2v(
            args.prompt,
            max_tokens=256,
            temperature=args.temperature,
            seed=args.seed,
            verbose=False,
            system_prompt=system_prompt,
        )

        del text_encoder
        mx.clear_cache()

        print(json.dumps({"enhanced_prompt": enhanced}))

    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
