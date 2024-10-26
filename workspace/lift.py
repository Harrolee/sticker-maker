from PIL import Image, ImageOps, ImageFilter
import numpy as np

def lift(input_path, output_path):
    # Load the image
    image = Image.open(input_path).convert("RGBA")
    
    # 1. Identify subject (assuming subject is non-transparent part)
    mask = image.split()[3]  # Get alpha channel
    bbox = mask.getbbox()
    
    if bbox:
        # 2. Move the subject into the center of the image
        subject = image.crop(bbox)
        new_size = max(subject.size)
        new_image = Image.new("RGBA", (new_size, new_size), (0, 0, 0, 0))
        
        paste_x = (new_size - subject.width) // 2
        paste_y = (new_size - subject.height) // 2
        new_image.paste(subject, (paste_x, paste_y), subject)
        
        # 3. Save image
        new_image.save(output_path)
    else:
        # If no subject found, save the original image
        image.save(output_path)

lift('workspace/input/1.png', 'workspace/output/1.png')