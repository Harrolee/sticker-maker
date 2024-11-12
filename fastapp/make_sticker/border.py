import numpy as np
from scipy.ndimage import gaussian_filter, binary_erosion, binary_dilation
from PIL import Image, ImageFilter

def _create_mask(image: Image, alpha_threshold=5, erosion_iterations=1, dilation_iterations=1, smooth_edges_sigma=1.0):
    # Step 1: Convert image to a binary mask based on the alpha channel
    image_array = np.array(image)
    alpha_channel = image_array[:, :, 3]
    mask_array = np.where(alpha_channel > alpha_threshold, 1, 0).astype(np.uint8)  # Binary mask (0 or 1)

    # Step 2: Refine the mask with morphological operations
    mask_array = binary_erosion(mask_array, iterations=erosion_iterations)
    mask_array = binary_dilation(mask_array, iterations=dilation_iterations)

    # Step 3: Smooth the edges of the mask
    mask_array = gaussian_filter(mask_array.astype(float), sigma=smooth_edges_sigma)
    mask_array = np.clip(mask_array * 255, 0, 255).astype(np.uint8)  # Convert back to 0-255 range

    # Convert to PIL Image
    refined_mask = Image.fromarray(mask_array, mode="L")
    return refined_mask

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