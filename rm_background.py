from pathlib import Path
from rembg import remove, new_session

def rm_background(input_path, output_path, session=None):
    with open(input_path, 'rb') as i:
            with open(output_path, 'wb') as o:
                input = i.read()
                output = remove(input, session=session) if session else remove(input)
                o.write(output)

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