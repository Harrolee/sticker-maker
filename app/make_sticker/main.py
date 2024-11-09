from make_sticker.rm_background import remove_background
from make_sticker.cartoonize_image import cartoonize
from make_sticker.lift import lift
from make_sticker.border import border
from make_sticker.tab import tab
from make_sticker.config import StickerConfig

config = StickerConfig()

work_dir = 'workspace'

def stickerize(filename, tab_text):

    path = remove_background(work_dir + '/input' + '/' + filename, work_dir + '/cartoonize_input' + '/' + filename, config)
    path = cartoonize(path, work_dir + '/rm_background_input' + '/' + filename, config)
    path = remove_background(path, work_dir + '/lift_input'+ '/' + filename, config)
    path = lift(path, work_dir + '/border_input'+ '/' + filename)
    path = border(path, work_dir + '/tab_input'+ '/' + filename, border_size=3, border_color=(0,0,0))
    path = border(path, work_dir + '/tab_input'+ '/' + filename)
    path = tab(path, work_dir + '/cartoonize_input'+ '/' + filename, tab_text=tab_text) # should I cartoonize the whole thing at the end, 
    print(path)
    return path

def _test_stickerize(filename, tab_text):
    from lift import lift
    from border import border
    from tab import tab

    path = 'workspace/lift_input/2b69d-temp.png'
    path = lift(path, work_dir + '/border_input'+ '/' + filename)
    path = border(path, work_dir + '/tab_input'+ '/' + filename, border_color=(173, 216, 230))
    path = tab(path, work_dir + '/cartoonize_input'+ '/' + filename, tab_text=tab_text) # should I cartoonize the whole thing at the end?
    print(path)
    return path


if __name__ == "__main__":
    _test_stickerize('2b69d-temp.png', 'do over')