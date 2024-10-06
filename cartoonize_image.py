import torch
from diffusers import StableDiffusionInstructPix2PixPipeline
from diffusers.utils import load_image

# model_id = "instruction-tuning-sd/cartoonizer"
# pipeline = StableDiffusionInstructPix2PixPipeline.from_pretrained(
#     model_id, torch_dtype=torch.float16, use_auth_token=True
# ).to("mps")

# image_path = "https://hf.co/datasets/diffusers/diffusers-images-docs/resolve/main/mountain.png"
# image = load_image(image_path)

# image = pipeline("Cartoonize the following image", image=image).images[0]
# image.save("image.png")

model_id = "instruction-tuning-sd/cartoonizer"
pipeline = StableDiffusionInstructPix2PixPipeline.from_pretrained(
    model_id, torch_dtype=torch.float16, use_auth_token=True
).to("mps")

def cartoonize(input_path, output_path):

    image = load_image(input_path)
    image = pipeline("Cartoonize the following image", image=image).images[0]
    image.save(output_path)


# from pathlib import Path

# def multiple_images(input_dir, output_dir):
#     extensions = ['jpg', 'png']
#     for e in extensions:
#         _cartoonize_images(input_dir, output_dir, e)

# def _cartoonize_images(input_dir, output_dir, extension):
#     image_files = [f for f in Path(input_dir).glob(f'*.{extension}')]
#     for file in image_files:
#         input_path = str(file)
#         output_path = str(f'{output_dir}/{file.stem}.{extension}')

#         image = load_image(input_path)
#         image = pipeline("Cartoonize the following image", image=image).images[0]
#         image.save(output_path)
#         # with open(input_path, 'rb') as i:
#             # with open(output_path, 'wb') as o:
#             #     input = i.read()
#             #     output = remove(input, session=session)
#             #     o.write(output)