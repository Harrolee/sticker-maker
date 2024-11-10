from app.make_sticker.rm_background import remove_background
from app.make_sticker.cartoonize_image import cartoonize
from app.make_sticker.lift import lift
from app.make_sticker.border import border
from app.make_sticker.tab import tab

work_dir = 'app/workspace'

def stickerize(filename, tab_text, config):

    path = remove_background(work_dir + '/input' + '/' + filename, work_dir + '/cartoonize_input' + '/' + filename, config)
    path = cartoonize(path, work_dir + '/rm_background_input' + '/' + filename, config)
    path = remove_background(path, work_dir + '/lift_input'+ '/' + filename, config)
    path = lift(path, work_dir + '/border_input'+ '/' + filename)
    path = border(path, work_dir + '/tab_input'+ '/' + filename, border_size=3, border_color=(0,0,0))
    path = border(path, work_dir + '/tab_input'+ '/' + filename)
    path = tab(path, work_dir + '/output'+ '/' + filename, tab_text=tab_text) # should I cartoonize the whole thing at the end, 
    print(path)
    return path