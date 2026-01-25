"""
Non-AI artistic filters for sticker creation.
These filters provide a sticker-like look without using AI models.
"""

from PIL import Image, ImageFilter, ImageEnhance, ImageOps
from fastapp.make_sticker.config import StickerConfig


def apply_artistic_filter(input_path: str, output_path: str, config: StickerConfig) -> str:
    """
    Apply non-AI artistic filters to create a sticker-like look.
    Combines edge enhancement, color quantization, and bilateral filtering.

    Args:
        input_path: Path to input image
        output_path: Path for output image
        config: Sticker configuration

    Returns:
        Path to the filtered image
    """
    img = Image.open(input_path)

    # Ensure we're working with RGBA
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Preserve alpha channel
    alpha = img.split()[3] if img.mode == 'RGBA' else None

    # Convert to RGB for processing
    rgb_img = img.convert('RGB')

    # Step 1: Bilateral filter for smoothing while preserving edges
    rgb_img = bilateral_filter(rgb_img, d=9, sigma_color=75, sigma_space=75)

    # Step 2: Color quantization for sticker-like flat colors
    rgb_img = quantize_colors(rgb_img, n_colors=16)

    # Step 3: Edge enhancement to make outlines pop
    rgb_img = enhance_edges(rgb_img, strength=1.5)

    # Step 4: Posterize for a more graphic look
    rgb_img = posterize(rgb_img, bits=5)

    # Step 5: Increase saturation for vibrant sticker colors
    rgb_img = enhance_saturation(rgb_img, factor=1.3)

    # Restore alpha channel
    if alpha:
        rgb_img = rgb_img.convert('RGBA')
        r, g, b, _ = rgb_img.split()
        result = Image.merge('RGBA', (r, g, b, alpha))
    else:
        result = rgb_img

    result.save(output_path)
    return output_path


def bilateral_filter(img: Image.Image, d: int = 9, sigma_color: float = 75, sigma_space: float = 75) -> Image.Image:
    """
    Apply bilateral filter for edge-preserving smoothing.
    Uses multiple passes of Pillow's built-in filters to approximate bilateral filtering.

    This smooths out noise and details while keeping strong edges intact,
    giving the image a cleaner, more cartoon-like appearance.
    """
    # Apply edge-preserving smooth using multiple passes
    # ModeFilter preserves edges while smoothing
    result = img.copy()

    # Apply gentle smoothing that preserves edges
    for _ in range(2):
        result = result.filter(ImageFilter.ModeFilter(size=3))

    # Apply slight blur to further smooth while keeping structure
    result = result.filter(ImageFilter.GaussianBlur(radius=0.5))

    return result


def quantize_colors(img: Image.Image, n_colors: int = 16) -> Image.Image:
    """
    Reduce the number of colors in an image for a sticker-like flat color look.

    Args:
        img: Input PIL Image
        n_colors: Number of colors to reduce to (default 16)

    Returns:
        Image with reduced color palette
    """
    # Convert to P mode (palette) with limited colors
    quantized = img.quantize(colors=n_colors, method=Image.Quantize.MEDIANCUT)

    # Convert back to RGB
    return quantized.convert('RGB')


def enhance_edges(img: Image.Image, strength: float = 1.5) -> Image.Image:
    """
    Enhance edges to make outlines more visible, giving a drawn look.

    Args:
        img: Input PIL Image
        strength: Edge enhancement strength (1.0 = original, higher = more edges)

    Returns:
        Image with enhanced edges
    """
    # Create edge-enhanced version
    edge_enhanced = img.filter(ImageFilter.EDGE_ENHANCE_MORE)

    # Blend original with edge-enhanced based on strength
    if strength == 1.0:
        return img
    elif strength > 1.0:
        # Blend towards edge-enhanced
        blend_factor = min(strength - 1.0, 1.0)
        return Image.blend(img, edge_enhanced, blend_factor)
    else:
        # Less than 1.0 means softer edges (rare use case)
        return img


def posterize(img: Image.Image, bits: int = 5) -> Image.Image:
    """
    Posterize the image to reduce tonal levels, creating a graphic poster effect.

    Args:
        img: Input PIL Image
        bits: Number of bits to keep (1-8, lower = more posterized)

    Returns:
        Posterized image
    """
    return ImageOps.posterize(img, bits)


def enhance_saturation(img: Image.Image, factor: float = 1.3) -> Image.Image:
    """
    Enhance color saturation for more vibrant sticker colors.

    Args:
        img: Input PIL Image
        factor: Saturation factor (1.0 = original, higher = more saturated)

    Returns:
        Image with enhanced saturation
    """
    enhancer = ImageEnhance.Color(img)
    return enhancer.enhance(factor)


def enhance_contrast(img: Image.Image, factor: float = 1.2) -> Image.Image:
    """
    Enhance contrast for bolder colors.

    Args:
        img: Input PIL Image
        factor: Contrast factor (1.0 = original, higher = more contrast)

    Returns:
        Image with enhanced contrast
    """
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(factor)


# Alternative filter presets that users might want

def apply_bold_filter(input_path: str, output_path: str, config: StickerConfig) -> str:
    """
    Bold sticker style - high contrast, strong edges, limited colors.
    Good for images that need to stand out.
    """
    img = Image.open(input_path)

    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    alpha = img.split()[3] if img.mode == 'RGBA' else None
    rgb_img = img.convert('RGB')

    # More aggressive processing for bold look
    rgb_img = bilateral_filter(rgb_img)
    rgb_img = quantize_colors(rgb_img, n_colors=12)
    rgb_img = enhance_edges(rgb_img, strength=2.0)
    rgb_img = posterize(rgb_img, bits=4)
    rgb_img = enhance_saturation(rgb_img, factor=1.5)
    rgb_img = enhance_contrast(rgb_img, factor=1.3)

    if alpha:
        rgb_img = rgb_img.convert('RGBA')
        r, g, b, _ = rgb_img.split()
        result = Image.merge('RGBA', (r, g, b, alpha))
    else:
        result = rgb_img

    result.save(output_path)
    return output_path


def apply_soft_filter(input_path: str, output_path: str, config: StickerConfig) -> str:
    """
    Soft sticker style - gentle smoothing, pastel-like colors.
    Good for cuter, softer looking stickers.
    """
    img = Image.open(input_path)

    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    alpha = img.split()[3] if img.mode == 'RGBA' else None
    rgb_img = img.convert('RGB')

    # Gentler processing for soft look
    rgb_img = bilateral_filter(rgb_img)
    rgb_img = quantize_colors(rgb_img, n_colors=24)  # More colors
    rgb_img = posterize(rgb_img, bits=6)  # Less posterization
    rgb_img = enhance_saturation(rgb_img, factor=1.1)  # Subtle saturation

    # Slight brightness boost for pastel effect
    brightness = ImageEnhance.Brightness(rgb_img)
    rgb_img = brightness.enhance(1.1)

    if alpha:
        rgb_img = rgb_img.convert('RGBA')
        r, g, b, _ = rgb_img.split()
        result = Image.merge('RGBA', (r, g, b, alpha))
    else:
        result = rgb_img

    result.save(output_path)
    return output_path


def apply_comic_filter(input_path: str, output_path: str, config: StickerConfig) -> str:
    """
    Comic book style - strong outlines, halftone-like effect.
    Good for action or dramatic stickers.
    """
    img = Image.open(input_path)

    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    alpha = img.split()[3] if img.mode == 'RGBA' else None
    rgb_img = img.convert('RGB')

    # Comic book processing
    rgb_img = bilateral_filter(rgb_img)
    rgb_img = quantize_colors(rgb_img, n_colors=8)  # Very limited palette
    rgb_img = enhance_edges(rgb_img, strength=2.0)  # Strong edges
    rgb_img = posterize(rgb_img, bits=3)  # Heavy posterization
    rgb_img = enhance_contrast(rgb_img, factor=1.5)  # High contrast
    rgb_img = enhance_saturation(rgb_img, factor=1.4)

    if alpha:
        rgb_img = rgb_img.convert('RGBA')
        r, g, b, _ = rgb_img.split()
        result = Image.merge('RGBA', (r, g, b, alpha))
    else:
        result = rgb_img

    result.save(output_path)
    return output_path


# Style mapping for easy lookup
FILTER_STYLES = {
    'filter': apply_artistic_filter,      # Default non-AI filter
    'filter_bold': apply_bold_filter,     # Bold/vibrant style
    'filter_soft': apply_soft_filter,     # Soft/pastel style
    'filter_comic': apply_comic_filter,   # Comic book style
}


def get_available_filter_styles() -> list:
    """Return list of available filter styles for UI."""
    return [
        {'value': 'filter', 'label': 'Artistic Filter (Standard)'},
        {'value': 'filter_bold', 'label': 'Bold & Vibrant'},
        {'value': 'filter_soft', 'label': 'Soft & Pastel'},
        {'value': 'filter_comic', 'label': 'Comic Book'},
    ]
