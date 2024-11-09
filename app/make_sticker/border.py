import numpy as np
from PIL import Image, ImageFilter

def _create_mask(image: Image, alpha_threshold: int = 5):
    # Convert image to a NumPy array
    image_array = np.array(image)

    # Create a mask based on the alpha channel
    alpha_channel = image_array[:, :, 3]  # Extract the alpha channel
    mask_array = np.where(alpha_channel > alpha_threshold, 255, 0).astype(np.uint8)

    # Convert mask array back to a Pillow image
    mask = Image.fromarray(mask_array, mode="L")
    return mask

def border(input_path, output_path, border_size=15, border_color=(173, 216, 230)):
    image = Image.open(input_path).convert("RGBA")

    alpha_threshold = 5
    mask = _create_mask(image, alpha_threshold)

    # Dilate the mask for the border effect
    dilated_mask = mask.filter(ImageFilter.MaxFilter(size=border_size))

    # Create a border image with the specified color
    border_image = Image.new("RGBA", image.size, border_color + (255,))
    border_inside = Image.composite(border_image, image, dilated_mask)

    # Composite the final result
    result = Image.composite(image, border_inside, mask)
    result.save(output_path)
    return output_path


if __name__ == "__main__":
    border_color = (173, 216, 230)
    border("workspace/border_input/border_improve.png", "workspace/output/bordered-border_improve.png", border_color=border_color)