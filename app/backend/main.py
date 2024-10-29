from backend.rm_background import single_lucataco_rm_background
from backend.file_handler import multiple_images
from backend.cartoonize_image import  cartoonize_replicate
from backend.lift import lift
from backend.border import border
from backend.tab import tab
from dotenv import load_dotenv
load_dotenv()

work_dir = 'workspace'

# filename = 'raw_atwork.png'

def stickerize(filename):
    path = single_lucataco_rm_background(work_dir + '/input' + '/' + filename, work_dir + '/cartoonize_input' + '/' + filename)
    path = cartoonize_replicate(path, work_dir + '/rm_background_input' + '/' + filename)
    path = single_lucataco_rm_background(path, work_dir + '/lift_input'+ '/' + filename)
    path = lift(path, work_dir + '/border_input'+ '/' + filename)
    path = border(path, work_dir + '/tab_input'+ '/' + filename)
    path = tab(path, work_dir + '/cartoonize_input'+ '/' + filename) # should I cartoonize the whole thing at the end, 
    print(path)
    return path

# extensions = ['jpg', 'png']
# multiple_images(work_dir + '/input', work_dir + '/cartoonize_input', extensions, rm_background)  
# multiple_images(work_dir + '/cartoonize_input', work_dir + '/rm_background_input', extensions, cartoonize) # cartoonize the subject
# multiple_images(work_dir + '/rm_background_input', work_dir + '/lift_input', extensions, rm_background) # convert background to alpha
# multiple_images(work_dir + '/lift_input', work_dir + '/border_input', extensions, lift) # center the image
# multiple_images(work_dir + '/border_input', work_dir + '/cartoonize_input', extensions, border) # create a border
# multiple_images(work_dir + '/tab_input', work_dir + '/cartoonize_input', extensions, tab) # add a name tab to the border
# # any border post-processing steps here
