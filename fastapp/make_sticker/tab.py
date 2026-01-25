import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


def calculate_text_size(text, font):
    """Calculate the required size for the text."""
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def fit_text_to_width(max_width, text, font_path, min_size=18, max_size=72):
    """Find largest font size that fits within max_width."""
    for size in range(max_size, min_size - 1, -2):
        font = ImageFont.truetype(str(font_path), size)
        bbox = font.getbbox(text)
        text_w = bbox[2] - bbox[0]
        if text_w <= max_width:
            return font, size, text

    # At minimum size, truncate if needed
    font = ImageFont.truetype(str(font_path), min_size)
    while len(text) > 3:
        bbox = font.getbbox(text + "...")
        if bbox[2] - bbox[0] <= max_width:
            return font, min_size, text + "..."
        text = text[:-1]

    return font, min_size, text


def get_subject_bounds(image):
    """Get the bounding box of the subject (non-transparent pixels)."""
    alpha = image.split()[3]  # Get alpha channel
    bbox = alpha.getbbox()
    return bbox  # (left, top, right, bottom)


def create_organic_tab(input_path, output_path, tab_text: str = "sticker"):
    """Create an image with a subtle text tab attached to the subject."""
    # Load image
    image = Image.open(input_path).convert('RGBA')
    img_w, img_h = image.width, image.height

    # Font path
    font_path = Path(__file__).parent / "fonts" / "Inter-Bold.ttf"

    # Get subject bounding box
    subject_bbox = get_subject_bounds(image)
    if subject_bbox is None:
        image.save(output_path)
        return output_path

    subj_left, subj_top, subj_right, subj_bottom = subject_bbox
    subj_width = subj_right - subj_left
    subj_center_x = subj_left + subj_width // 2

    # Fixed modest font size - subtle, not dominant
    font_size = 24
    font = ImageFont.truetype(str(font_path), font_size)
    text_w, text_h = calculate_text_size(tab_text, font)

    # Tight padding around text
    padding_x = 12
    padding_y = 6

    # Banner sized to fit text snugly
    banner_width = text_w + padding_x * 2
    banner_height = text_h + padding_y * 2

    # Center banner horizontally on subject
    banner_left = subj_center_x - banner_width // 2
    banner_right = banner_left + banner_width

    # Banner mostly hidden behind subject - only text portion visible below
    # Position so top half is behind subject, bottom half (with text) peeks out
    hidden_amount = banner_height // 2 + padding_y
    banner_top = subj_bottom - hidden_amount
    banner_bottom = banner_top + banner_height

    # Expand canvas if needed
    if banner_bottom > img_h:
        new_h = banner_bottom + 5
        expanded = Image.new('RGBA', (img_w, new_h), (0, 0, 0, 0))
        expanded.paste(image, (0, 0))
        image = expanded
        img_h = new_h

    # Create banner overlay
    banner = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(banner)

    # Banner color - matches border color exactly
    banner_color = (173, 216, 230, 255)  # Fully opaque, same as border

    # Draw tight rounded rectangle
    radius = min(10, banner_height // 3)
    draw.rounded_rectangle(
        [banner_left, banner_top, banner_right, banner_bottom],
        radius=radius,
        fill=banner_color
    )

    # Composite - banner BEHIND image so subject covers top of pill
    result = Image.alpha_composite(banner, image)

    # Draw text centered in banner
    draw = ImageDraw.Draw(result)
    text_x = banner_left + padding_x
    text_y = banner_top + padding_y

    # Subtle shadow
    draw.text((text_x + 1, text_y + 1), tab_text, fill=(0, 0, 0, 80), font=font)
    draw.text((text_x, text_y), tab_text, fill='white', font=font)

    # Crop to content
    final_bbox = result.getbbox()
    if final_bbox:
        result = result.crop(final_bbox)

    result.save(output_path)
    return output_path
