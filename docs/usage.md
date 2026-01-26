---
layout: default
title: Usage Guide
nav_order: 3
---

# Usage Guide
{: .no_toc }

Learn how to get the best results from LTX Video Generator.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Basic Workflow

### 1. Write Your Prompt

Enter a descriptive text prompt in the main text field. The more detail you provide, the better the results.

**Good prompt:**
> "The camera slowly pans across a misty forest at dawn, with rays of golden sunlight filtering through the trees"

**Less effective:**
> "forest"

### 2. Choose a Preset

Select a preset from the dropdown to quickly configure parameters:

| Preset | Resolution | Frames | Steps | Best For |
|:-------|:-----------|:-------|:------|:---------|
| Quick Preview | 512×320 | 49 | 20 | Quick tests |
| Standard | 768×512 | 97 | 28 | Balanced quality |
| High Quality | 768×512 | 121 | 28 | Best results |
| Portrait | 512×768 | 97 | 28 | Vertical videos |
| Square | 512×512 | 97 | 28 | Social media |

{: .tip }
The LTX-2 Distilled model uses a 2-stage generation pipeline for high quality output.

### 3. Generate

Click the **Generate** button. Progress shows:
- Model loading status
- Stage 1 and Stage 2 denoising progress
- Video encoding and saving

### 4. View Results

- **Queue** sidebar shows real-time progress
- **History** tab displays all generated videos with thumbnails
- Videos save to your configured output directory

## Image-to-Video

You can animate images into videos:

1. Expand the **Image to Video** section
2. Click **Select Image** to choose a source image
3. Adjust **Image Strength** (1.0 = full influence, 0.0 = ignore image)
4. The first frame will be conditioned on your image

## Writing Effective Prompts

### Include Camera Movement

```
"The camera slowly pans left revealing..."
"A drone shot flying over..."
"Close-up tracking shot of..."
"The camera pushes in toward..."
```

### Describe Motion

```
"waves gently crashing on the shore"
"leaves falling in slow motion"
"clouds drifting across the sky"
"a person walking through..."
```

### Specify Lighting

```
"at golden hour with warm lighting"
"under dramatic storm clouds"
"illuminated by neon city lights"
"in soft diffused morning light"
```

### Add Atmosphere

```
"with fog rolling through the valley"
"rain drops falling on the window"
"dust particles floating in sunbeams"
"snow gently falling"
```

## Using the Queue

### Add Multiple Generations

1. Write your prompt
2. Click **Add to Queue** (instead of Generate)
3. Modify the prompt or parameters
4. Add more to the queue
5. Videos generate one after another

### Batch Variations

Click the batch menu (stack icon) to:
- Generate 3 variations
- Generate 5 variations
- Each uses a random seed for different results

### Queue Management

- **Cancel** the current generation with the X button
- **Remove** pending items from the queue
- **Clear** the entire queue with the Clear button

## History Features

### Browse Videos

- Thumbnails show a frame from each video
- Sort by newest, oldest, or prompt alphabetically
- Search prompts to find specific videos

### Video Details

Click a video to see:
- Full video preview (loops automatically)
- Original prompt
- All generation parameters
- Timestamp and generation duration
- Seed value for reproducibility

### Actions

- **Show in Finder** - Reveal the video file
- **Share** - Share via macOS share sheet
- **Reuse Prompt** - Copy prompt back to input
- **Delete** - Remove video

## Tips for Best Results

### Start Small

- Use **Quick Preview** preset first
- Iterate on prompts quickly
- Only increase quality for final renders

### Use Negative Prompts

Click the disclosure arrow to add negative prompts:
```
worst quality, blurry, jittery, distorted, watermark
```

### Reproducible Results

- Note the seed value of good generations
- Enter the same seed to reproduce results
- Useful for making variations with slight prompt changes

### Memory Management

- Higher resolutions use more memory
- Close other apps if you encounter issues
- 32GB RAM minimum, 64GB recommended
