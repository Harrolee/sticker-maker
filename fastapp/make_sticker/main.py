import shutil
from fastapp.make_sticker.rm_background import remove_background
from fastapp.make_sticker.cartoonize_image import cartoonize
from fastapp.make_sticker.lift import lift
from fastapp.make_sticker.border import create_solid_border, EdgeRoughness
from fastapp.make_sticker.tab import create_organic_tab
from fastapp.make_sticker.filters import FILTER_STYLES, apply_artistic_filter

work_dir = 'fastapp/workspace'

# Available styles for the stylization step
AVAILABLE_STYLES = ['cartoonize', 'filter', 'filter_bold', 'filter_soft', 'filter_comic']
DEFAULT_STYLE = 'cartoonize'


def stickerize(filename, tab_text, config, style: str = None):
    """
    Main sticker creation pipeline.

    Args:
        filename: Input filename
        tab_text: Text to display on the sticker tab
        config: Sticker configuration
        style: Stylization method - 'cartoonize' (AI, default), 'filter',
               'filter_bold', 'filter_soft', or 'filter_comic' (non-AI options)

    Returns:
        Path to the final sticker image
    """
    # Default to cartoonize for backwards compatibility
    if style is None:
        style = DEFAULT_STYLE

    # Validate style
    if style not in AVAILABLE_STYLES:
        print(f"Warning: Unknown style '{style}', falling back to '{DEFAULT_STYLE}'")
        style = DEFAULT_STYLE

    # Step 1: Remove background from input
    path = remove_background(
        work_dir + '/input' + '/' + filename,
        work_dir + '/cartoonize_input' + '/' + filename,
        config
    )

    # Step 2: Apply stylization (AI cartoonize or non-AI filter)
    if style == 'cartoonize':
        # Use AI-based cartoonizer (Replicate model)
        path = cartoonize(path, work_dir + '/rm_background_input' + '/' + filename, config)
    else:
        # Use non-AI filter
        filter_func = FILTER_STYLES.get(style, apply_artistic_filter)
        path = filter_func(path, work_dir + '/rm_background_input' + '/' + filename, config)

    # Step 3: Remove background again (after stylization)
    path = remove_background(path, work_dir + '/lift_input' + '/' + filename, config)

    # Step 4: Lift/enlarge
    path = lift(path, work_dir + '/border_input' + '/' + filename)

    # Step 5: Add borders
    path = create_solid_border(
        path,
        work_dir + '/tab_input' + '/' + filename,
        roughness=EdgeRoughness.MID,
        width=2,
        color=(0, 0, 0)
    )
    bordered_path = create_solid_border(
        path,
        work_dir + '/tab_input' + '/' + filename,
        roughness=EdgeRoughness.MID,
        width=5,
        color=(173, 216, 230)
    )

    # Step 6: Add organic tab with text
    output_path = work_dir + '/output' + '/' + filename
    result_path = create_organic_tab(bordered_path, output_path, tab_text=tab_text)

    # Handle case where tab creation fails (e.g., no edge points found)
    if result_path is None:
        print(f"Warning: Could not create tab for {filename}, saving without tab")
        shutil.copy(bordered_path, output_path)
        return output_path

    print(result_path)
    return result_path


def get_available_styles() -> list:
    """
    Return list of available styles for UI display.

    Returns:
        List of dicts with 'value' and 'label' keys
    """
    return [
        {'value': 'cartoonize', 'label': 'AI Cartoonize (Replicate)'},
        {'value': 'filter', 'label': 'Artistic Filter (No AI)'},
        {'value': 'filter_bold', 'label': 'Bold & Vibrant (No AI)'},
        {'value': 'filter_soft', 'label': 'Soft & Pastel (No AI)'},
        {'value': 'filter_comic', 'label': 'Comic Book (No AI)'},
    ]