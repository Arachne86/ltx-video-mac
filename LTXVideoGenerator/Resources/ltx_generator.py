#!/usr/bin/env python3
"""
LTX Video Generator - Python Helper Script

This script provides the core video generation functionality using the LTX-2 model.
It can be used standalone for testing or invoked by the Swift app via PythonKit.
"""

import argparse
import json
import sys
from pathlib import Path

import torch
from diffusers import LTXPipeline
from diffusers.utils import export_to_video


class LTXGenerator:
    """LTX-2 Video Generator wrapper."""
    
    def __init__(self, device: str = "mps"):
        self.device = device
        self.pipe = None
        
    def load_model(self) -> None:
        """Load the LTX-2 model."""
        print("Loading LTX-2 model...", file=sys.stderr)
        
        self.pipe = LTXPipeline.from_pretrained(
            "Lightricks/LTX-2",
            torch_dtype=torch.float16,
            variant="fp16"
        )
        self.pipe.to(self.device)
        
        print("Model loaded successfully!", file=sys.stderr)
    
    def generate(
        self,
        prompt: str,
        output_path: str,
        negative_prompt: str = "",
        num_inference_steps: int = 50,
        guidance_scale: float = 5.0,
        width: int = 768,
        height: int = 512,
        num_frames: int = 97,
        fps: int = 24,
        seed: int | None = None,
    ) -> dict:
        """
        Generate a video from a text prompt.
        
        Returns:
            dict with 'video_path' and 'seed' keys
        """
        if self.pipe is None:
            self.load_model()
        
        # Set up generator with seed
        if seed is None:
            seed = torch.randint(0, 2**31, (1,)).item()
        
        generator = torch.Generator(device=self.device)
        generator.manual_seed(seed)
        
        print(f"Generating video with seed {seed}...", file=sys.stderr)
        print(f"  Prompt: {prompt[:100]}...", file=sys.stderr)
        print(f"  Size: {width}x{height}, {num_frames} frames", file=sys.stderr)
        
        # Generate
        result = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt if negative_prompt else None,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            width=width,
            height=height,
            num_frames=num_frames,
            generator=generator,
        )
        
        # Export video
        video_frames = result.frames
        export_to_video(video_frames, output_path, fps=fps)
        
        print(f"Video saved to: {output_path}", file=sys.stderr)
        
        return {
            "video_path": output_path,
            "seed": seed,
        }
    
    def unload_model(self) -> None:
        """Unload model and free memory."""
        self.pipe = None
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()


def main():
    parser = argparse.ArgumentParser(description="LTX-2 Video Generator")
    parser.add_argument("prompt", help="Text prompt for video generation")
    parser.add_argument("-o", "--output", default="output.mp4", help="Output video path")
    parser.add_argument("-n", "--negative-prompt", default="", help="Negative prompt")
    parser.add_argument("--steps", type=int, default=50, help="Inference steps")
    parser.add_argument("--guidance", type=float, default=5.0, help="Guidance scale")
    parser.add_argument("--width", type=int, default=768, help="Video width")
    parser.add_argument("--height", type=int, default=512, help="Video height")
    parser.add_argument("--frames", type=int, default=97, help="Number of frames")
    parser.add_argument("--fps", type=int, default=24, help="Frames per second")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    
    args = parser.parse_args()
    
    generator = LTXGenerator()
    
    result = generator.generate(
        prompt=args.prompt,
        output_path=args.output,
        negative_prompt=args.negative_prompt,
        num_inference_steps=args.steps,
        guidance_scale=args.guidance,
        width=args.width,
        height=args.height,
        num_frames=args.frames,
        fps=args.fps,
        seed=args.seed,
    )
    
    if args.json:
        print(json.dumps(result))
    else:
        print(f"\nGenerated: {result['video_path']}")
        print(f"Seed: {result['seed']}")


if __name__ == "__main__":
    main()
