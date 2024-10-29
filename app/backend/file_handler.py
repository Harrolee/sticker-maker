from pathlib import Path

def multiple_images(input_dir, output_dir, extensions, processor):
    for e in extensions:
        _multiple_images(input_dir, output_dir, e, processor)

def _multiple_images(input_dir, output_dir, extension, processor):
    image_files = [f for f in Path(input_dir).glob(f'*.{extension}')]
    for file in image_files:
        input_path = str(file)
        output_path = str(f'{output_dir}/{file.stem}.{extension}')

        processor(input_path, output_path)