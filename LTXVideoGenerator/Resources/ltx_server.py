#!/usr/bin/env python3
import sys
import json
import traceback
import os
import contextlib

# Unbuffer stdout/stderr
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

def log_err(msg):
    print(msg, file=sys.stderr, flush=True)

def setup_prompts():
    try:
        from pathlib import Path
        import shutil
        # Ensure we can import the text encoder module to find its path
        import mlx_video.models.ltx.text_encoder as te

        resources_path = Path(__file__).parent
        bundled_prompts = resources_path / "prompts"
        target_dir = Path(te.__file__).parent / "prompts"

        for name in ["gemma_t2v_system_prompt.txt", "gemma_i2v_system_prompt.txt"]:
            src = bundled_prompts / name
            dst = target_dir / name
            if src.exists() and not dst.exists():
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                log_err(f"STATUS:Injected missing prompt: {name}")
    except Exception as e:
        # Don't fail hard if prompt injection fails, just warn
        log_err(f"STATUS:Warning: could not inject prompts: {e}")

def main():
    log_err("STATUS:Initializing LTX Server...")

    try:
        from mlx_video.generate_av import generate_av
        setup_prompts()
        log_err("STATUS:MLX Video module loaded")
    except ImportError as e:
        log_err(f"ERROR:Failed to import mlx_video: {e}")
        # We don't exit here, we wait for a request to fail it, or just exit?
        # If we exit, Swift will know.
        sys.exit(1)

    log_err("SERVER_READY")

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                log_err(f"ERROR:Invalid JSON received")
                continue

            cmd = request.get("command")
            if cmd == "ping":
                print(json.dumps({"status": "pong"}), flush=True)
                continue

            if cmd == "generate":
                params = request.get("params", {})

                # Redirect stdout to stderr to capture library logs as progress/logs
                # and keep stdout clean for our JSON response
                original_stdout_fd = os.dup(1)
                os.dup2(2, 1)

                result = {}

                try:
                    # Map params to kwargs
                    kwargs = {
                        "prompt": params.get("prompt"),
                        "height": params.get("height", 512),
                        "width": params.get("width", 512),
                        "num_frames": params.get("num_frames", 65),
                        "seed": params.get("seed", 42),
                        "fps": params.get("fps", 24),
                        "output_path": params.get("output_path", "output.mp4"),
                        "model_repo": params.get("model_repo", "notapalindrome/ltx2-mlx-av"),
                    }

                    if params.get("image"):
                        kwargs["image"] = params["image"]
                        kwargs["image_strength"] = params.get("image_strength", 1.0)
                        kwargs["image_frame_idx"] = params.get("image_frame_idx", 0)

                    if params.get("tiling") and params["tiling"] != "auto":
                        kwargs["tiling"] = params["tiling"]

                    if params.get("no_audio"):
                        kwargs["no_audio"] = True

                    if params.get("save_audio_separately"):
                        kwargs["save_audio_separately"] = True

                    if params.get("repetition_penalty"):
                        kwargs["repetition_penalty"] = params["repetition_penalty"]
                    if params.get("top_p"):
                        kwargs["top_p"] = params["top_p"]

                    if params.get("enhance_prompt"):
                        kwargs["enhance_prompt"] = True

                    if params.get("use_uncensored_enhancer"):
                        kwargs["use_uncensored_enhancer"] = True

                    if params.get("temperature"):
                        kwargs["temperature"] = params["temperature"]

                    # Run generation
                    generate_av(**kwargs)

                    # Prepare result
                    result = {
                        "success": True,
                        "video_path": kwargs["output_path"],
                        "seed": kwargs["seed"],
                        "mode": "i2v" if kwargs.get("image") else "t2v",
                        "has_audio": not kwargs.get("no_audio", False)
                    }
                except Exception as e:
                    traceback.print_exc(file=sys.stderr)
                    result = {
                        "success": False,
                        "error": str(e)
                    }
                finally:
                    # Restore stdout
                    sys.stdout.flush()
                    os.dup2(original_stdout_fd, 1)
                    os.close(original_stdout_fd)

                # Send response to original stdout
                print(json.dumps(result), flush=True)

        except KeyboardInterrupt:
            break
        except Exception as e:
            log_err(f"ERROR:Server loop error: {e}")
            break

if __name__ == "__main__":
    main()
