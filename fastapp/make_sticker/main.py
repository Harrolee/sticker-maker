from fastapp.make_sticker.rm_background import remove_background
from fastapp.make_sticker.cartoonize_image import cartoonize
from fastapp.make_sticker.lift import lift
from fastapp.make_sticker.border import create_solid_border, EdgeRoughness
from fastapp.make_sticker.tab import tab

work_dir = 'fastapp/workspace'

def stickerize(filename, tab_text, config):
    path = remove_background(work_dir + '/input' + '/' + filename, work_dir + '/cartoonize_input' + '/' + filename, config)
    path = cartoonize(path, work_dir + '/rm_background_input' + '/' + filename, config)
    path = remove_background(path, work_dir + '/lift_input'+ '/' + filename, config)
    path = lift(path, work_dir + '/border_input'+ '/' + filename)
    path = create_solid_border(path, work_dir + '/tab_input'+ '/' + filename, roughness=EdgeRoughness.MID,width=2, color=(0,0,0))
    path = create_solid_border(path, work_dir + '/tab_input'+ '/' + filename, roughness=EdgeRoughness.MID, width=5, color=(173, 216, 230))
    path = tab(path, work_dir + '/output'+ '/' + filename, tab_text=tab_text) # should I cartoonize the whole thing at the end, 
    # path = tab("fastapp/workspace/tab_input/broke_case.png", work_dir + '/output'+ '/' + filename, tab_text="lee apple")
    print(path)
    return path