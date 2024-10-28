from PIL import Image

def _enlarge_image(image):
    original_size = max(image.size)
    new_size = int(original_size * 1.2)  # Increase size by 20%
    
    # Create a new image with the increased size
    new_image = Image.new("RGBA", (new_size, new_size), (0, 0, 0, 0))
    return new_image, new_size

def lift(input_path, output_path):
    image = Image.open(input_path).convert("RGBA")
    
    # Identify subject (assuming subject is non-transparent part)
    mask = image.split()[3]  # Get alpha channel
    bbox = mask.getbbox()
    
    if bbox:
        subject = image.crop(bbox)
        new_image, new_size = _enlarge_image(subject)

        # Paste the subject into the center of the new image
        paste_x = (new_size - subject.width) // 2
        paste_y = (new_size - subject.height) // 2
        new_image.paste(subject, (paste_x, paste_y), subject)
        
        new_image.save(output_path)
    else:
        # If no subject found, save the original image
        print('could not find subject of image')
        image.save(output_path)
    return output_path

# Example usage
lift('workspace/input/atWork.png', 'workspace/output/lifted_atWork_bigger.png')
