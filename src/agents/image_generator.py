"""Image generator agent using SDXL (Stable Diffusion XL) locally via GPU."""

import os
import torch
from datetime import datetime
from pathlib import Path
from src.state import CampaignState

# Lazy-loaded pipeline (loaded once, reused across runs)
_pipeline = None


def _get_pipeline():
    """Load SDXL pipeline once and cache it."""
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    from diffusers import AutoPipelineForText2Image

    print("[IMAGE GENERATOR] Loading SDXL-Turbo model (first run takes a few minutes)...")

    _pipeline = AutoPipelineForText2Image.from_pretrained(
        "stabilityai/sdxl-turbo",
        torch_dtype=torch.float16,
        variant="fp16",
    )
    _pipeline = _pipeline.to("cuda")
    _pipeline.enable_attention_slicing()
    _pipeline.vae.enable_slicing()

    print("[IMAGE GENERATOR] SDXL model loaded.")
    return _pipeline


def _build_image_prompt(state: CampaignState) -> str:
    """Build a short SDXL prompt (max ~60 words / 77 CLIP tokens)."""
    product = state.get("product_description", "")
    positioning = state.get("positioning", "")

    # Extract first sentence of positioning for style hint
    style_hint = positioning.split(".")[0][:80] if positioning else "premium sustainable product"

    # Keep product short — first 60 chars
    product_short = product[:60].strip()

    prompt = (
        f"Professional product photo, {product_short}, "
        f"{style_hint}, "
        "clean white background, commercial photography, 4k, photorealistic"
    )
    return prompt


def image_generator_node(state: CampaignState) -> dict:
    """Generate a campaign visual using SDXL.

    Reads: product_description, positioning, tone_of_voice
    Writes: image_path
    """
    print("\n" + "=" * 60)
    print("[IMAGE GENERATOR] Generating campaign visual with SDXL...")
    print("=" * 60)

    try:
        pipe = _get_pipeline()
        prompt = _build_image_prompt(state)
        negative_prompt = "blurry, low quality, text, watermark, logo, ugly, deformed"

        print(f"[IMAGE GENERATOR] Prompt: {prompt[:150]}...")

        image = pipe(
            prompt=prompt,
            num_inference_steps=10,
            guidance_scale=0.0,  # SDXL-Turbo uses guidance_scale=0
            height=512,
            width=512,
        ).images[0]

        output_dir = Path("campaigns/images")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = str(output_dir / f"campaign_{timestamp}.png")
        image.save(image_path)

        print(f"[IMAGE GENERATOR] Image saved: {image_path}")
        return {"image_path": image_path}

    except torch.cuda.OutOfMemoryError:
        print("[IMAGE GENERATOR] WARNING: GPU out of memory. Falling back to CPU offload...")
        global _pipeline
        _pipeline = None

        from diffusers import AutoPipelineForText2Image
        pipe = AutoPipelineForText2Image.from_pretrained(
            "stabilityai/sdxl-turbo",
            torch_dtype=torch.float16,
            variant="fp16",
        )
        pipe.enable_model_cpu_offload()
        _pipeline = pipe

        prompt = _build_image_prompt(state)
        image = pipe(
            prompt=prompt,
            num_inference_steps=4,
            guidance_scale=0.0,
            height=512,
            width=512,
        ).images[0]

        output_dir = Path("campaigns/images")
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = str(output_dir / f"campaign_{timestamp}.png")
        image.save(image_path)

        print(f"[IMAGE GENERATOR] Image saved (CPU offload): {image_path}")
        return {"image_path": image_path}

    except Exception as e:
        print(f"[IMAGE GENERATOR] ERROR: {e}")
        return {"image_path": None}
