import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import binary_dilation, gaussian_filter, binary_erosion
import random
import cv2
from scipy import ndimage
from pathlib import Path

def detect_border_angle(mask, point, radius=40):
    """
    Detect the angle of the border using a larger area and principal component analysis.
    Uses multiple sampling radii to get a more stable angle estimate.
    """
    y, x = point
    h, w = mask.shape
    
    # Collect border points at multiple scales
    border_points = []
    for r in [radius//2, radius, radius*1.5]:  # Sample at different scales
        r = int(r)
        y_min, y_max = max(0, y-r), min(h, y+r)
        x_min, x_max = max(0, x-r), min(w, x+r)
        
        # Get the border region
        region = mask[y_min:y_max, x_min:x_max]
        edge = binary_dilation(region) ^ binary_erosion(region)
        
        # Get edge points
        local_points = np.where(edge > 0)
        for ly, lx in zip(local_points[0], local_points[1]):
            border_points.append([lx + x_min - x, ly + y_min - y])  # Center around the point
    
    if len(border_points) < 3:
        return 0
    
    # Convert to numpy array
    points = np.array(border_points)
    
    # Calculate covariance matrix
    mean = np.mean(points, axis=0)
    centered_points = points - mean
    cov = np.cov(centered_points.T)
    
    # Get principal direction
    eigenvalues, eigenvectors = np.linalg.eigh(cov)
    principal_direction = eigenvectors[:, 1]  # Largest eigenvalue's vector
    
    # Calculate angle
    angle = np.degrees(np.arctan2(principal_direction[1], principal_direction[0]))
    
    # Make sure the angle is oriented outward from the mask
    # Sample points slightly inside and outside the mask
    test_dist = 5
    in_point = (int(y - test_dist * np.sin(np.radians(angle))), 
                int(x - test_dist * np.cos(np.radians(angle))))
    out_point = (int(y + test_dist * np.sin(np.radians(angle))), 
                int(x + test_dist * np.cos(np.radians(angle))))
    
    # Check if we need to flip the angle
    if (0 <= in_point[0] < h and 0 <= in_point[1] < w and 
        0 <= out_point[0] < h and 0 <= out_point[1] < w):
        if mask[in_point] > mask[out_point]:
            angle += 180
    
    # Normalize angle to -180 to 180 range
    angle = (angle + 180) % 360 - 180
    
    return angle

def create_bump_kernel(base_size=7, elongation=1.5):
    """Create an elliptical kernel for bump-like growth."""
    size = base_size + random.randint(-1, 1)
    kernel = np.zeros((int(size * elongation), size))
    center_y, center_x = kernel.shape[0] // 2, kernel.shape[1] // 2
    y, x = np.ogrid[-center_y:kernel.shape[0]-center_y, -center_x:kernel.shape[1]-center_x]
    
    # Create elliptical mask
    mask = (x*x)/(center_x*center_x) + (y*y)/(center_y*center_y) <= 1
    kernel[mask] = 1
    
    # Add slight randomness to edges
    kernel = gaussian_filter(kernel, sigma=0.3)
    return kernel > 0.5

def calculate_text_size(text, font):
    """Calculate the required size for the text."""
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def fit_text_to_tab(tab_width, tab_height, text, font_path, margin=10):
    """Find largest font size that fits in available space."""
    available_w = tab_width - 2 * margin
    available_h = tab_height - 2 * margin

    for size in range(48, 12, -2):  # Try 48 down to 12
        font = ImageFont.truetype(str(font_path), size)
        bbox = font.getbbox(text)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        if text_w <= available_w and text_h <= available_h:
            return font, size

    # Fallback to minimum size - truncate text if still too long
    min_font = ImageFont.truetype(str(font_path), 12)
    bbox = min_font.getbbox(text)
    text_w = bbox[2] - bbox[0]

    # If text still doesn't fit at minimum size, truncate with ellipsis
    if text_w > available_w:
        while len(text) > 3:
            text = text[:-1]
            bbox = min_font.getbbox(text + "...")
            if bbox[2] - bbox[0] <= available_w:
                return min_font, 12, text + "..."
        return min_font, 12, "..."

    return min_font, 12

def grow_bump_tab(mask, start_point, angle, text_width, text_height, image_size, margin=10):
    """Grow a bump-like tab with controlled size based on text dimensions and image size."""
    h, w = mask.shape
    img_w, img_h = image_size
    result = mask.copy()
    current = np.zeros_like(mask)

    # Calculate minimum tab dimensions - at least 15% of image width, 8% of height
    min_width = max(text_width + 2 * margin, int(img_w * 0.15))
    min_height = max(text_height + 2 * margin, int(img_h * 0.08))
    
    # Initialize with small elliptical shape
    y, x = start_point
    kernel = create_bump_kernel(5, elongation=1.2)
    y_indices, x_indices = np.where(kernel)
    for dy, dx in zip(y_indices - kernel.shape[0]//2, x_indices - kernel.shape[1]//2):
        ny, nx = y + dy, x + dx
        if 0 <= ny < h and 0 <= nx < w:
            current[ny, nx] = 1
    
    # Calculate growth direction
    angle_rad = np.radians(angle)
    direction = np.array([np.cos(angle_rad), np.sin(angle_rad)])

    # Grow the tab until it reaches minimum size
    max_iterations = 100  # Allow enough iterations to reach minimum size
    for i in range(max_iterations):
        # Create elongated kernel - larger kernels for faster growth
        kernel_size = 9 + (i // 3)
        kernel = create_bump_kernel(kernel_size, elongation=1.5)

        # Apply dilation
        new_growth = binary_dilation(current, kernel)

        # Add directional bias - more aggressive shift for faster growth
        shift = 3 + (i // 2) + random.randint(-1, 1)
        dy = int(direction[1] * shift)
        dx = int(direction[0] * shift)

        shifted = np.zeros_like(new_growth)

        # Calculate valid slices for shifting
        src_slice_y = slice(max(0, -dy), min(h, h - dy))
        src_slice_x = slice(max(0, -dx), min(w, w - dx))
        dst_slice_y = slice(max(0, dy), min(h, h + dy))
        dst_slice_x = slice(max(0, dx), min(w, w + dx))

        shifted[dst_slice_y, dst_slice_x] = new_growth[src_slice_y, src_slice_x]

        # Add minimal noise to edges for organic look
        edge = binary_dilation(shifted) ^ shifted
        noise = np.random.random(edge.shape) > 0.85
        shifted = shifted | (edge & noise)

        current = shifted
        result = result | current

        # Check if tab is big enough
        tab_only = result & ~mask
        tab_coords = np.where(tab_only)
        if len(tab_coords[0]) > 0:
            tab_h = max(tab_coords[0]) - min(tab_coords[0])
            tab_w = max(tab_coords[1]) - min(tab_coords[1])
            if tab_w >= min_width and tab_h >= min_height:
                break

    return result

def create_organic_tab(input_path, output_path, tab_text: str = "kmlmk"):
    """Create an image with a bump-like tab."""
    # Load image
    image = Image.open(input_path).convert('RGBA')
    image_array = np.array(image)
    image_size = (image.width, image.height)

    # Font path for TrueType font
    font_path = Path(__file__).parent / "fonts" / "Inter-Bold.ttf"

    # Create mask from alpha channel
    alpha_mask = (image_array[:, :, 3] > 0).astype(np.uint8)

    edge = alpha_mask - binary_erosion(alpha_mask)
    edge_points = list(zip(*np.where(edge > 0)))

    if not edge_points:
        return None

    # Try to find a good starting point by sampling multiple points
    best_point = None
    most_stable_angle = float('inf')

    # Sample several random points
    samples = random.sample(edge_points, min(10, len(edge_points)))
    for point in samples:
        # Check angle stability at different scales
        angles = []
        for radius in [30, 40, 50]:
            angle = detect_border_angle(alpha_mask, point, radius)
            angles.append(angle)

        # Calculate angle variance
        angle_variance = np.var(angles)
        if angle_variance < most_stable_angle:
            most_stable_angle = angle_variance
            best_point = point

    start_point = best_point or random.choice(edge_points)
    border_angle = detect_border_angle(alpha_mask, start_point)

    # Calculate initial text size using a medium font size for tab growth calculation
    initial_font = ImageFont.truetype(str(font_path), 24)
    text_width, text_height = calculate_text_size(tab_text, initial_font)

    # Grow tab with minimum size based on image dimensions
    tab_mask = grow_bump_tab(alpha_mask, start_point, border_angle, text_width, text_height, image_size)
    new_tab_only = tab_mask & ~alpha_mask

    # Create result image
    result = image.copy()
    result_array = np.array(result)

    # Set tab color (light blue with higher opacity)
    tab_color = np.array([173, 216, 230, 230], dtype=np.uint8)  # Increased opacity

    # Apply tab color
    for c in range(4):
        result_array[:, :, c] = np.where(new_tab_only, tab_color[c], result_array[:, :, c])

    # Convert back to PIL Image
    result = Image.fromarray(result_array)

    # Add text
    if tab_text:
        # Calculate actual tab dimensions
        tab_points = np.where(new_tab_only)
        if len(tab_points[0]) > 0:
            actual_tab_height = max(tab_points[0]) - min(tab_points[0])
            actual_tab_width = max(tab_points[1]) - min(tab_points[1])

            # Fit text to the actual tab size
            fit_result = fit_text_to_tab(actual_tab_width, actual_tab_height, tab_text, font_path)
            if len(fit_result) == 3:
                font, font_size, tab_text = fit_result  # Text was truncated
            else:
                font, font_size = fit_result

            # Recalculate text size with fitted font
            text_width, text_height = calculate_text_size(tab_text, font)

            text_y = int(np.mean(tab_points[0]))
            text_x = int(np.mean(tab_points[1]))

            # Create text image with padding
            padding = 10
            text_img = Image.new('RGBA', (text_width + padding*2, text_height + padding*2), (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_img)
            text_draw.text((padding, padding), tab_text, fill='white', font=font)

            # When rotating text, use the negative of the border angle
            # This will align text more naturally with the overall border
            rotated_text = text_img.rotate(-border_angle, expand=True, resample=Image.BICUBIC)

            # Position text in center of tab
            paste_x = text_x - rotated_text.width // 2
            paste_y = text_y - rotated_text.height // 2

            # Paste text
            result.paste(rotated_text, (paste_x, paste_y), rotated_text)

    result.save(output_path)
    return output_path