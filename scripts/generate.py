#!/usr/bin/env python3
"""
Nano Banana Pro Image Generator
Generates images using Google's Gemini 3 Pro Image model via the Gemini API.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Required package 'google-genai' is not installed.")
    print("Attempting to install automatically...")
    try:
        import subprocess

        # Try with --user flag first (works in externally managed environments)
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user", "google-genai"],
            capture_output=True,
            text=True,
            check=True
        )
        print("Successfully installed google-genai!")
        print("Please run the command again to use the newly installed package.")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        # If --user fails, try with --break-system-packages
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--break-system-packages", "google-genai"],
                capture_output=True,
                text=True,
                check=True
            )
            print("Successfully installed google-genai!")
            print("Please run the command again to use the newly installed package.")
            sys.exit(0)
        except subprocess.CalledProcessError:
            print(f"\nERROR: Failed to auto-install google-genai.")
            print("\nPlease install manually with one of:")
            print("  pip install --user google-genai")
            print("  pip install --break-system-packages google-genai")
            print("\nOr use a virtual environment:")
            print("  python3 -m venv venv")
            print("  source venv/bin/activate")
            print("  pip install google-genai")
            sys.exit(1)
    except Exception as e:
        print(f"\nERROR: Unexpected error during installation: {str(e)}")
        print("\nPlease install manually with: pip install --user google-genai")
        sys.exit(1)


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


def generate_image(prompt):
    """
    Generate an image using Nano Banana Pro (Gemini 3 Pro Image).

    Args:
        prompt: The enhanced image generation prompt

    Returns:
        PIL.Image object or None if generation failed
    """
    try:
        # Initialize the Gemini client
        api_key = validate_api_key()
        client = genai.Client(api_key=api_key)

        print(f"Generating image with Nano Banana Pro...")
        print(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n")

        # Generate the image
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=[prompt],
        )

        # Extract the image from the response
        for part in response.parts:
            if part.text is not None:
                print(f"Model response: {part.text}")
            elif part.inline_data is not None:
                print("Image generated successfully!")
                return part.as_image()

        print("ERROR: No image data found in API response.")
        return None

    except Exception as e:
        print(f"ERROR: Failed to generate image: {str(e)}")

        # Provide helpful error messages for common issues
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
        elif "network" in error_str or "connection" in error_str:
            print("\nPossible causes:")
            print("  - Network connectivity issues")
            print("  - Firewall blocking API requests")
            print("  - Check your internet connection")

        return None


def save_image(image, output_dir="."):
    """
    Save the generated image to a file with a timestamped name.

    Args:
        image: PIL.Image object or Gemini Image object
        output_dir: Directory to save the image (default: current directory)

    Returns:
        Path to the saved file or None if save failed
    """
    try:
        # Create a timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"nanobanana_{timestamp}.png"
        filepath = Path(output_dir) / filename

        # Save the image - handle both PIL and Gemini image types
        if hasattr(image, 'save'):
            try:
                image.save(filepath, "PNG")
            except TypeError:
                # Gemini Image object takes only filepath
                image.save(str(filepath))
        else:
            # Fallback for raw bytes
            with open(filepath, 'wb') as f:
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


def main():
    """Main entry point for the image generator."""
    if len(sys.argv) < 2:
        print("ERROR: No prompt provided.")
        print("\nUsage: python generate.py \"Your image prompt here\"")
        print("\nExample:")
        print("  python generate.py \"A fluffy cat sitting on a cloud\"")
        sys.exit(1)

    # Get the prompt from command-line arguments
    prompt = " ".join(sys.argv[1:])

    if not prompt.strip():
        print("ERROR: Prompt cannot be empty.")
        sys.exit(1)

    # Generate the image
    image = generate_image(prompt)
    if image is None:
        sys.exit(1)

    # Save the image
    filepath = save_image(image)
    if filepath is None:
        sys.exit(1)

    print("\n✓ Image generation complete!")
    print(f"✓ Saved as: {filepath.name}")


if __name__ == "__main__":
    main()
