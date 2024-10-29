

# model_id = "instruction-tuning-sd/cartoonizer"
# pipeline = StableDiffusionInstructPix2PixPipeline.from_pretrained(
#     model_id, torch_dtype=torch.float16, use_auth_token=True
# ).to("mps")

# image_path = "https://hf.co/datasets/diffusers/diffusers-images-docs/resolve/main/mountain.png"
# image = load_image(image_path)

# image = pipeline("Cartoonize the following image", image=image).images[0]
# image.save("image.png")


def cartoonize_local(input_path, output_path):
    import torch
    from diffusers import StableDiffusionInstructPix2PixPipeline
    from diffusers.utils import load_image

    model_id = "instruction-tuning-sd/cartoonizer"
    pipeline = StableDiffusionInstructPix2PixPipeline.from_pretrained(
        model_id, torch_dtype=torch.float16
    ).to("mps")

    image = load_image(input_path)
    image = pipeline("Cartoonize the following image", image=image).images[0]
    image.save(output_path)



def cartoonize_replicate(input_path, output_path):
    output = _sayak_cartoonizer(input_path)
    with open(output_path, 'wb') as o:
        o.write(output.read())
    return output_path

def _sayak_cartoonizer(input_path):
    import replicate
    image = open(input_path, "rb");
    input = {
        "image": image
    }
    print('sending request to cartoonizer on replicate')
    output = replicate.run(
        "harrolee/cartoonizer:b4b9bb25b0aefaa73cf6780d3801896fc12a0dae64d177790f842c183b18cecb",
        input=input
    )
    return output[0]

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

if __name__ == "__main__":
    # export the REPLICATE_API_TOKEN for this to work
    cartoonize_replicate("workspace/cartoonize_input/border_atWork_15.png", "workspace/output/cartoonized_border_atWork_15.png")