from rm_background import rm_background
from file_handler import multiple_images
from cartoonize_image import cartoonize

extensions = ['jpg', 'png']
multiple_images('input', 'cartoonize_input', extensions, rm_background)
multiple_images('cartoonize_input', 'output', extensions, cartoonize)