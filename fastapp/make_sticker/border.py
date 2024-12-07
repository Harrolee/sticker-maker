from enum import Enum
import numpy as np
from scipy.ndimage import binary_dilation, gaussian_filter
from PIL import Image
import cv2  # Added for better edge smoothing

class EdgeRoughness(Enum):
    MEGACOARSE = 13
    COARSE = 11
    MID = 9
    SMOOTH = 3
      

def create_solid_border(input_path, output_path, roughness: EdgeRoughness, width=15, color=(0, 0, 0), ):
    """Create a solid border with smooth edges but solid color."""
    # Open and convert image to RGBA
    image = Image.open(input_path).convert("RGBA")
    image_array = np.array(image)
    
    # Get alpha channel
    alpha_channel = image_array[:, :, 3]
    
    # Method 1: Multi-step smoothing
    # First create binary mask with high threshold
    binary_mask = (alpha_channel >= 250).astype(np.uint8)
    
    # Apply slight gaussian blur then re-threshold to smooth edges
    # sigma = 0.9
    # smoothed = gaussian_filter(binary_mask.astype(float), sigma=sigma)
    # binary_mask = (smoothed > 0.5).astype(np.uint8)
    
# looked pretty good!
    # Method 2: Morphological operations
    kernel = np.ones((roughness.value,roughness.value), np.uint8)
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)
    
    # Method 3: Distance transform approach
    # dist = cv2.distanceTransform(binary_mask, cv2.DIST_L2, 3)
    # binary_mask = (dist > 0).astype(np.uint8)
    
    # Create dilated mask for border (using the smoothed base mask)
    dilated_mask = binary_dilation(binary_mask, iterations=width)
    
    # Create border mask
    border_mask = dilated_mask.astype(np.uint8) - binary_mask
    
    # Create result array
    result = np.zeros_like(image_array)
    
    # Fill border areas with solid color
    for i in range(3):
        result[:, :, i] = np.where(border_mask == 1, color[i], 0)
    result[:, :, 3] = border_mask * 255  # Solid alpha for border
    
    # Copy original image where it exists
    mask_3d = np.stack([binary_mask] * 4, axis=-1)
    result = np.where(mask_3d, image_array, result)
    
    # Convert back to PIL and save
    result_image = Image.fromarray(result)
    result_image.save(output_path)
    return output_path

if __name__ == "__main__":
    border_color = (0, 0, 0)  # Black border
    create_solid_border(
        "workspace/border_input/border_improve.png",
        "workspace/output/bordered-border_improve.png",
        width=15,
        color=border_color
    )