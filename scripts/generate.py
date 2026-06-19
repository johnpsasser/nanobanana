#!/usr/bin/env python3
"""
Nano Banana Pro Image Generator
Generates and edits images using Google's Gemini 3 Pro Image model via the
Gemini API.

Usage:
    python generate.py "An enhanced prompt describing the image"
    python generate.py "A 9:16 movie poster ..." --aspect-ratio 9:16 --resolution 2K
    python generate.py "Make the sky a dramatic sunset" --image photo.png
    python generate.py "A quick sketch of a fox" --fast
"""

import argparse
import importlib
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Nano Banana Pro (GA). Best for text rendering, reasoning, and high fidelity.
DEFAULT_MODEL = "gemini-3-pro-image"
# Nano Banana (Flash, GA). Faster and cheaper, good for drafts/iteration.
FAST_MODEL = "gemini-3.1-flash-image"

ASPECT_RATIOS = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]
RESOLUTIONS = ["1K", "2K", "4K"]


def _pip_install(package):
    """Install a package, trying strategies that work in externally-managed envs."""
    for extra in (["--user"], ["--break-system-packages"], []):
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", *extra, package],
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            continue
    return False


def _ensure(import_callable, package):
    """Return the result of import_callable(), auto-installing `package` if needed.

    Installs and re-imports in the same process so the user never has to re-run
    the command after a first-time dependency install.
    """
    try:
        return import_callable()
    except ImportError:
        print(f"Required package '{package}' is not installed. Installing...")
        if not _pip_install(package):
            print(f"\nERROR: Failed to auto-install '{package}'.")
            print("\nPlease install it manually with one of:")
            print(f"  pip install --user {package}")
            print(f"  pip install --break-system-packages {package}")
            print("\nOr use a virtual environment:")
            print("  python3 -m venv venv && source venv/bin/activate")
            print(f"  pip install {package}")
            sys.exit(1)
        importlib.invalidate_caches()
        try:
            return import_callable()
        except ImportError:
            print(f"\nInstalled '{package}', but it is not importable in this "
                  f"interpreter ({sys.executable}).")
            print("If you use a virtualenv or pyenv, install it there and re-run.")
            sys.exit(1)


def _import_genai():
    from google import genai
    from google.genai import types
    return genai, types


def _import_pil():
    from PIL import Image
    return Image


def validate_api_key():
    """Validate that the GEMINI_API_KEY environment variable is set."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable is not set.")
        print("\nTo fix this, set your API key:")
        print("  export GEMINI_API_KEY='your-api-key-here'")
        print("\nGet your API key at: https://aistudio.google.com/apikey")
        sys.exit(1)
    return api_key


def load_reference_images(paths):
    """Load reference/input images for editing, as PIL.Image objects."""
    if not paths:
        return []
    Image = _ensure(_import_pil, "pillow")
    images = []
    for path in paths:
        p = Path(path)
        if not p.is_file():
            print(f"ERROR: Reference image not found: {path}")
            sys.exit(1)
        try:
            images.append(Image.open(p))
        except Exception as e:
            print(f"ERROR: Could not open reference image '{path}': {e}")
            sys.exit(1)
    return images


def generate_image(prompt, model, aspect_ratio=None, resolution=None, reference_images=None):
    """
    Generate (or edit) an image using Nano Banana Pro / Nano Banana.

    Args:
        prompt: The enhanced image generation prompt.
        model: The Gemini image model ID to use.
        aspect_ratio: Optional aspect ratio string (e.g. "16:9").
        resolution: Optional output resolution ("1K", "2K", "4K").
        reference_images: Optional list of PIL.Image objects to edit/combine.

    Returns:
        Image object or None if generation failed.
    """
    genai, types = _ensure(_import_genai, "google-genai")
    try:
        api_key = validate_api_key()
        client = genai.Client(api_key=api_key)

        label = "Nano Banana" if model == FAST_MODEL else "Nano Banana Pro"
        action = "Editing" if reference_images else "Generating"
        print(f"{action} image with {label} ({model})...")
        print(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        if aspect_ratio or resolution:
            print(f"Output: aspect_ratio={aspect_ratio or 'default'}, "
                  f"resolution={resolution or 'default'}")
        if reference_images:
            print(f"Reference images: {len(reference_images)}")
        print()

        # Build the optional image_config (aspect ratio / resolution).
        image_config_kwargs = {}
        if aspect_ratio:
            image_config_kwargs["aspect_ratio"] = aspect_ratio
        if resolution:
            image_config_kwargs["image_size"] = resolution

        config = None
        if image_config_kwargs:
            config = types.GenerateContentConfig(
                image_config=types.ImageConfig(**image_config_kwargs)
            )

        # Text prompt first, then any reference images for editing.
        contents = [prompt, *(reference_images or [])]

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        parts = getattr(response, "parts", None) or []
        for part in parts:
            if getattr(part, "text", None):
                print(f"Model response: {part.text}")
            elif getattr(part, "inline_data", None) is not None:
                print("Image generated successfully!")
                return part.as_image()

        print("ERROR: No image data found in API response.")
        print("The model may have refused the request or returned text only.")
        return None

    except Exception as e:
        print(f"ERROR: Failed to generate image: {str(e)}")

        error_str = str(e).lower()
        if "api key" in error_str or "authentication" in error_str:
            print("\nPossible causes:")
            print("  - Invalid API key")
            print("  - API key not properly set in GEMINI_API_KEY environment variable")
            print("  - API key may have been revoked or expired")
        elif "quota" in error_str or "rate limit" in error_str:
            print("\nPossible causes:")
            print("  - API quota exceeded")
            print("  - Rate limit reached")
            print("  - Try again in a few moments")
        elif "not found" in error_str or "model" in error_str:
            print("\nPossible causes:")
            print(f"  - The model '{model}' is not available to your API key/region")
            print("  - Try the default Pro model, or '--fast' for the Flash model")
        elif "network" in error_str or "connection" in error_str:
            print("\nPossible causes:")
            print("  - Network connectivity issues")
            print("  - Firewall blocking API requests")
            print("  - Check your internet connection")

        return None


def save_image(image, output_dir="."):
    """Save the generated image to a timestamped PNG file."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"nanobanana_{timestamp}.png"
        filepath = Path(output_dir) / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if hasattr(image, "save"):
            try:
                image.save(filepath, "PNG")
            except TypeError:
                # Gemini Image object takes only filepath
                image.save(str(filepath))
        else:
            # Fallback for raw bytes
            with open(filepath, "wb") as f:
                f.write(image)
        print(f"\nImage saved to: {filepath.absolute()}")
        return filepath

    except Exception as e:
        print(f"ERROR: Failed to save image: {str(e)}")
        print("\nPossible causes:")
        print("  - Insufficient permissions to write to the directory")
        print("  - Disk space full")
        print("  - Invalid output directory path")
        return None


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate or edit images with Nano Banana Pro (Gemini 3 Pro Image).",
    )
    parser.add_argument("prompt", nargs="+", help="The enhanced image prompt.")
    parser.add_argument(
        "--fast",
        action="store_true",
        help=f"Use the faster, cheaper Flash model ({FAST_MODEL}) instead of Pro.",
    )
    parser.add_argument(
        "--model",
        help=f"Explicit model ID (overrides --fast). Default: {DEFAULT_MODEL}.",
        default=None,
    )
    parser.add_argument(
        "--aspect-ratio",
        choices=ASPECT_RATIOS,
        help="Output aspect ratio (e.g. 16:9, 9:16, 1:1).",
    )
    parser.add_argument(
        "--resolution",
        choices=RESOLUTIONS,
        help="Output resolution. Default is the model default (1K).",
    )
    parser.add_argument(
        "--image",
        action="append",
        metavar="PATH",
        help="Reference/input image to edit or combine. Repeatable.",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to save the image (default: current directory).",
    )
    return parser.parse_args(argv)


def main():
    args = parse_args()

    prompt = " ".join(args.prompt).strip()
    if not prompt:
        print("ERROR: Prompt cannot be empty.")
        sys.exit(1)

    model = args.model or (FAST_MODEL if args.fast else DEFAULT_MODEL)
    reference_images = load_reference_images(args.image)

    image = generate_image(
        prompt,
        model=model,
        aspect_ratio=args.aspect_ratio,
        resolution=args.resolution,
        reference_images=reference_images,
    )
    if image is None:
        sys.exit(1)

    filepath = save_image(image, output_dir=args.output_dir)
    if filepath is None:
        sys.exit(1)

    print("\n✓ Image generation complete!")
    print(f"✓ Saved as: {filepath.name}")


if __name__ == "__main__":
    main()
