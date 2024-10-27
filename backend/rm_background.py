from pathlib import Path

def _gatis(input_path, output_path, session=None):
    from rembg import remove, new_session
    with open(input_path, 'rb') as i:
        with open(output_path, 'wb') as o:
            input = i.read()
            output = remove(input, session=session) if session else remove(input)
            o.write(output)

def single_lucataco_rm_background(input_path, output_path):
    output = _lucataco(input_path)
    with open(output_path, 'wb') as o:
        o.write(output.read())
    return output_path

def _lucataco(input_path):
    import replicate
    image = open(input_path, "rb");
    input = {
        "image": image
    }
    output = replicate.run(
        "lucataco/remove-bg:95fcc2a26d3899cd6c2691c900465aaeff466285a65c14638cc5f36f34befaf1",
        input=input
    )
    return output
    
    

def single_image(input_path, output_path):
    with open(input_path, 'rb') as i:
        with open(output_path, 'wb') as o:
            input = i.read()
            output = remove(input)
            o.write(output)

def multiple_images(input_dir, output_dir):
    session = new_session()
    extensions = ['jpg', 'png']
    for e in extensions:
        _multiple_files(input_dir, output_dir, e, session)


def _multiple_files(input_dir, output_dir, extension, session):
    image_files = [f for f in Path(input_dir).glob(f'*.{extension}')]
    for file in image_files:
        input_path = str(file)
        output_path = str(f'{output_dir}/{file.stem}.{extension}')

        with open(input_path, 'rb') as i:
            with open(output_path, 'wb') as o:
                input = i.read()
                output = remove(input, session=session)
                o.write(output)


# single_image('input/atWork.png', 'output/atWork.png')
# multiple_images('input', 'output')

if __name__ == "__main__":
    single_lucataco_rm_background("workspace/rm_bg_input/cartoonized_border_atWork_15.png", "workspace/output/_lucataco.png")