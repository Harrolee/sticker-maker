from rm_background import rm_background
from file_handler import multiple_images
from cartoonize_image import cartoonize
from lift import lift


work_dir = 'workspace'

extensions = ['jpg', 'png']
multiple_images(work_dir + '/input', work_dir + '/cartoonize_input', extensions, rm_background)
# multiple_images(work_dir + '/cartoonize_input', work_dir + '/output', extensions, cartoonize)
# multiple_images(work_dir + '/cartoonize_input', work_dir + '/lift_input', extensions, lift)
