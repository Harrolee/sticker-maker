from rm_background import rm_background
from backend.file_handler import multiple_images
from cartoonize_image import cartoonize
from lift import lift
from border import border
from tab import tab
from dotenv import load_dotenv
load_dotenv()

work_dir = 'workspace'

extensions = ['jpg', 'png']
multiple_images(work_dir + '/input', work_dir + '/cartoonize_input', extensions, rm_background)  
multiple_images(work_dir + '/cartoonize_input', work_dir + '/rm_background_input', extensions, cartoonize) # cartoonize the subject
multiple_images(work_dir + '/rm_background_input', work_dir + '/lift_input', extensions, rm_background) # convert background to alpha
multiple_images(work_dir + '/lift_input', work_dir + '/border_input', extensions, lift) # center the image
multiple_images(work_dir + '/border_input', work_dir + '/cartoonize_input', extensions, border) # create a border
multiple_images(work_dir + '/tab_input', work_dir + '/cartoonize_input', extensions, tab) # add a name tab to the border
# any border post-processing steps here
