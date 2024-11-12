from PIL import Image, ImageDraw, ImageFont
import numpy as np
from enum import Enum

class Edge(Enum):
    TOP = 'top'
    BOTTOM = 'bottom'
    LEFT = 'left'
    RIGHT = 'right'

def load_image(input_path):
    """Load and convert the image to RGBA format."""
    image = Image.open(input_path).convert('RGBA')
    return image

def find_border(image, draw_path=False):
    """
    Find the border color by traversing from the bottom center upwards.
    Optionally draw a red path during traversal.
    """
    width, height = image.size
    x = width // 2
    y = height - 1
    pixels = np.array(image)
    border_color = None

    # Create a draw object if we want to visualize the path
    result = image.copy()
    draw = ImageDraw.Draw(result) if draw_path else None

    # Traverse upward to find the first non-transparent pixel
    while y >= 0:
        pixel = pixels[y, x]
        if pixel[3] != 0:  # Check alpha channel
            border_color = tuple(pixel)
            break
        if draw_path:
            draw.point((x, y), fill=(255, 0, 0, 255))  # Draw red path
        y -= 1

    if border_color is None:
        raise ValueError("Could not find border color")
    
    return result, (x, y), border_color

def _draw_tab(draw, position, tab_size, fill_color, rounded_side: Edge, corner_radius: 10):
    """Draw a rectangle tab with rounded corners on only one specified side."""
    tab_x, tab_y = position
    tab_width, tab_height = tab_size

    if rounded_side == Edge.TOP:
        # Rounded corners on the top side only
        draw.polygon([
            (tab_x + corner_radius, tab_y),  # Start right of left rounded corner
            (tab_x + tab_width - corner_radius, tab_y),  # End left of right rounded corner
            (tab_x + tab_width, tab_y + corner_radius),  # Right rounded corner
            (tab_x + tab_width, tab_y + tab_height),  # Bottom right
            (tab_x, tab_y + tab_height),  # Bottom left
            (tab_x, tab_y + corner_radius),  # Left rounded corner
        ], fill=fill_color)
        # Draw left and right top rounded corners
        draw.pieslice([(tab_x, tab_y), (tab_x + 2*corner_radius, tab_y + 2*corner_radius)], 180, 270, fill=fill_color)
        draw.pieslice([(tab_x + tab_width - 2*corner_radius, tab_y), (tab_x + tab_width, tab_y + 2*corner_radius)], 270, 360, fill=fill_color)
    
    elif rounded_side == Edge.BOTTOM:
        # Rounded corners on the bottom side only
        draw.polygon([
            (tab_x, tab_y),  # Top left
            (tab_x + tab_width, tab_y),  # Top right
            (tab_x + tab_width, tab_y + tab_height - corner_radius),  # Bottom right before rounding
            (tab_x + tab_width - corner_radius, tab_y + tab_height),  # Bottom right rounded corner
            (tab_x + corner_radius, tab_y + tab_height),  # Bottom left rounded corner
            (tab_x, tab_y + tab_height - corner_radius)  # Bottom left before rounding
        ], fill=fill_color)
        # Draw bottom left and right rounded corners
        draw.pieslice([(tab_x, tab_y + tab_height - 2*corner_radius), (tab_x + 2*corner_radius, tab_y + tab_height)], 90, 180, fill=fill_color)
        draw.pieslice([(tab_x + tab_width - 2*corner_radius, tab_y + tab_height - 2*corner_radius), (tab_x + tab_width, tab_y + tab_height)], 0, 90, fill=fill_color)

    elif rounded_side == Edge.LEFT:
        # Rounded corners on the left side only
        draw.polygon([
            (tab_x + corner_radius, tab_y),  # Top right of left rounded corner
            (tab_x + tab_width, tab_y),  # Top right
            (tab_x + tab_width, tab_y + tab_height),  # Bottom right
            (tab_x + corner_radius, tab_y + tab_height),  # Bottom left of left rounded corner
            (tab_x, tab_y + tab_height - corner_radius),  # Bottom left rounded corner
            (tab_x, tab_y + corner_radius)  # Top left rounded corner
        ], fill=fill_color)
        # Draw top and bottom left rounded corners
        draw.pieslice([(tab_x, tab_y), (tab_x + 2*corner_radius, tab_y + 2*corner_radius)], 180, 270, fill=fill_color)
        draw.pieslice([(tab_x, tab_y + tab_height - 2*corner_radius), (tab_x + 2*corner_radius, tab_y + tab_height)], 90, 180, fill=fill_color)

    elif rounded_side == Edge.RIGHT:
        # Rounded corners on the right side only
        draw.polygon([
            (tab_x, tab_y),  # Top left
            (tab_x + tab_width - corner_radius, tab_y),  # Right before top rounded corner
            (tab_x + tab_width, tab_y + corner_radius),  # Top right rounded corner
            (tab_x + tab_width, tab_y + tab_height - corner_radius),  # Bottom right rounded corner
            (tab_x + tab_width - corner_radius, tab_y + tab_height),  # Bottom left of right rounded corner
            (tab_x, tab_y + tab_height)  # Bottom left
        ], fill=fill_color)
        # Draw top and bottom right rounded corners
        draw.pieslice([(tab_x + tab_width - 2*corner_radius, tab_y), (tab_x + tab_width, tab_y + 2*corner_radius)], 270, 360, fill=fill_color)
        draw.pieslice([(tab_x + tab_width - 2*corner_radius, tab_y + tab_height - 2*corner_radius), (tab_x + tab_width, tab_y + tab_height)], 0, 90, fill=fill_color)

def write_text(draw, text, position, tab_size, font=None):
    """Write centered text within the specified tab area."""
    tab_x, tab_y = position
    tab_width, tab_height = tab_size

    # Get text size and calculate position
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Center the text in the tab
    text_x = tab_x + (tab_width - text_width) // 2
    border_height_offset = -10 # we want the words a little on the border and a little on the tab
    text_y = border_height_offset + tab_y + (tab_height - text_height) // 2

    # Draw text in white
    draw.text((text_x, text_y), text, fill='white', font=font)

def clean_up_pixels(pixels, tab_position, tab_size, border_color):
    """Clean up pixels between the tab and border by filling with the border color."""
    tab_x, tab_y = tab_position
    tab_width, tab_height = tab_size
    border_color_array = np.array(border_color)

    # Define and clean the tab area
    cleanup_region = pixels[tab_y:tab_y + tab_height, tab_x:tab_x + tab_width]
    mask = (cleanup_region[:, :, 3] != 0) & \
           ~np.all(cleanup_region == border_color_array, axis=-1)
    cleanup_region[mask] = border_color_array

    # Update the original pixels with the cleaned-up region
    pixels[tab_y:tab_y + tab_height, tab_x:tab_x + tab_width] = cleanup_region

"""
- must do immediately after creating a border
  - the border-find algorithm relies on there not being any gradient to the border
"""
def tab(input_path, output_path, tab_text: str):
    # 1. Load image
    image = load_image(input_path)

    # 2. Find border and mark path
    result, (border_x, border_y), border_color = find_border(image)

    # 3. Prepare font and measure text dimensions
    font = ImageFont.load_default()
    text_bbox = font.getbbox(tab_text)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Add padding to the width to ensure text fits comfortably within the tab
    padding = 10
    tab_width = max(80, text_width + 2 * padding)  # Minimum width of 80
    tab_height = max(15, text_height + padding)

    # Calculate tab position centered at the border_x
    tab_position = (border_x - tab_width // 2, border_y)

    # 4. Draw the tab
    draw = ImageDraw.Draw(result)
    _draw_tab(draw, tab_position, (tab_width, tab_height), fill_color=border_color, rounded_side=Edge.BOTTOM, corner_radius=10)

    # 5. Write text inside the tab, centered
    text_position = (tab_position[0] + (tab_width - text_width) // 2, tab_position[1] + (tab_height - text_height) // 2)
    draw.text(text_position, tab_text, font=font, fill="black")

    # 6. Clean up any stray pixels between the tab and border
    pixels_result = np.array(result)
    # clean_up_pixels(pixels_result, tab_position, (tab_width, tab_height), border_color)

    # Convert back to image and save
    final_result = Image.fromarray(pixels_result)
    final_result.save(output_path)
    return output_path

# Example usage:
if __name__ == '__main__':
    tab("workspace/tab_input/border_atWork.png", "workspace/output/tabbed2.png", tab_text="lee apple")


#     # Algorithm
#     # 1. find a tab placement point
#     # 1.1 start in center bottom 
#     # 1.2 walk toward center until you find a pixel that is not empty
#     # 1.2.1 note: the first pixel that is not empty is beginning of the border
#     # 2. create a rounded tab in the color of the pixel that you found
#     # 3. write "tab_here" inside of that rounded tab
#     # 4. save the tab onto the image  
#     # 5. cleanup
#     # 5.1 check for any pixels between the newly created tab and the border that are not the border's color
#     # 5.1 replace those pixels with the border's color