from PIL import Image, ImageOps, ImageFilter

def create_mask(image: Image, threshold):
    mask = Image.new("L", image.size, 0)  # Start with a black mask
    pixels = image.load()
    mask_pixels = mask.load()
    # Loop through all the pixels to create a mask where the person is
    # TODO: iterate on this so that pixels are only replaced if a 3x3 kernel of applicable pixels is available
    # kernel = [[]]
    # copy the pixels into a numpy array and run a kernel over that
    # data = numpy.asarray(image)
    for y in range(image.size[1]):
        for x in range(image.size[0]):
            r, g, b, a = pixels[x, y]
            if r > threshold or g > threshold or b > threshold:
                mask_pixels[x, y] = 255  # Person area is white in the mask
    return mask

def border(input_path, output_path, border_size = 10, border_color = ()):
    image = Image.open(input_path).convert("RGBA")

    black_threshold = 33
    mask = create_mask(image, black_threshold)
    # dilate mask
    dilated_mask = mask.filter(ImageFilter.MaxFilter(size=11))
    
    border_image = Image.new("RGBA", image.size, border_color + (255,))
    border_inside = Image.composite(border_image, image, dilated_mask)
    result = Image.composite(image, border_inside, mask)

    result.save(output_path)


if __name__ == "__main__":
    border_color = (173, 216, 230)
    border("output/atWork.jpg", "output/border_atWork.png", border_color=border_color)