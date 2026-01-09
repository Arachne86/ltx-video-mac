---
layout: default
title: Parameters
nav_order: 4
---

# Parameters Reference
{: .no_toc }

Detailed explanation of all generation parameters.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Resolution

### Width & Height

Controls the dimensions of the generated video in pixels.

| Setting | Range | Default |
|:--------|:------|:--------|
| Width | 256-1280 | 512 |
| Height | 256-1280 | 320 |

**Tips:**
- Both dimensions should be divisible by 64 for best results
- Higher resolutions require more memory and time
- Start with smaller sizes for testing

### Common Aspect Ratios

| Aspect | Width × Height | Use Case |
|:-------|:---------------|:---------|
| 16:10 | 512×320, 640×400, 768×480 | Standard |
| 16:9 | 768×432, 1024×576 | Widescreen |
| 9:16 | 384×640, 432×768 | Portrait/Mobile |
| 1:1 | 512×512 | Social media |
| 2.4:1 | 768×320 | Cinematic |

---

## Frames

### Number of Frames

Total frames to generate. More frames = longer video.

| Setting | Range | Default |
|:--------|:------|:--------|
| Frames | 9-121 | 25 |

**Duration calculation:**
```
Duration (seconds) = Frames ÷ FPS
```

Examples at 24 FPS:
- 25 frames = ~1 second
- 49 frames = ~2 seconds
- 73 frames = ~3 seconds
- 97 frames = ~4 seconds

### FPS (Frames Per Second)

Playback speed of the generated video.

| Setting | Range | Default |
|:--------|:------|:--------|
| FPS | 8-30 | 24 |

**Tips:**
- 24 FPS: Cinematic feel
- 30 FPS: Smooth motion
- 12-15 FPS: Animation style

---

## Quality Settings

### Inference Steps

Number of denoising steps. More steps = higher quality but slower.

| Setting | Range | Default |
|:--------|:------|:--------|
| Steps | 10-100 | 40 |

**Recommendations:**
- 20-25: Fast preview
- 35-45: Good quality
- 50+: Maximum quality

The quality improvement diminishes after ~50 steps.

### Guidance Scale

How closely the model follows your prompt.

| Setting | Range | Default |
|:--------|:------|:--------|
| Guidance | 1.0-20.0 | 7.5 |

**Effects:**
- **Low (1-3):** More creative, may ignore prompt details
- **Medium (5-8):** Balanced adherence
- **High (10+):** Strict prompt following, may reduce quality

**Recommended range:** 5.0 - 10.0

---

## Seed

### Random Seed

Controls the randomness of generation.

| Setting | Range | Default |
|:--------|:------|:--------|
| Seed | 0-2147483647 | Random |

**Usage:**
- **Same seed + same parameters = identical output**
- Leave at -1 for random seed each time
- Save the seed of good results to reproduce them
- Try seeds ±1 from good results for variations

---

## Prompts

### Main Prompt

Describe what you want to see in the video.

**Best practices:**
- Be descriptive and specific
- Include camera movement if desired
- Describe motion and action
- Mention lighting and atmosphere

### Negative Prompt

Describe what you want to avoid.

**Common negative prompts:**
```
worst quality, low quality, blurry, 
jittery motion, distorted, 
watermark, text, logo,
static, still image
```

---

## Presets

Presets provide quick access to common configurations:

### Fast Preview
```
512×320, 25 frames, 25 steps
```
Quick testing, ~30 seconds

### Standard
```
640×384, 49 frames, 40 steps
```
Good balance, ~2 minutes

### High Quality
```
768×512, 65 frames, 50 steps
```
Best results, ~5+ minutes

### Portrait
```
384×640, 41 frames, 35 steps
```
Vertical format for mobile

### Square
```
512×512, 41 frames, 35 steps
```
Social media format

### Cinematic
```
768×320, 49 frames, 40 steps
```
Ultra-wide aspect ratio

---

## Performance Notes

### Memory Usage

Approximate VRAM requirements:
- 512×320: ~8GB
- 640×384: ~12GB
- 768×512: ~16GB

### Generation Time

Rough estimates on M2 Max:
- Fast Preview: 30-60 seconds
- Standard: 1-2 minutes
- High Quality: 3-5 minutes

Times vary based on:
- Chip (M1/M2/M3/M4)
- RAM amount
- Other running applications
