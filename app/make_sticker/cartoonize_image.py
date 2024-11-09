from make_sticker.config import StickerConfig

def cartoonize(input_path, output_path, config: StickerConfig):
    if config.is_local == 'true':
        return "workspace/rm_background_input/local_run.png"#_cartoonize_local(input_path, output_path)
    else:
        return _cartoonize_replicate(input_path, output_path, config)

def _cartoonize_local(input_path, output_path):
    import torch
    from diffusers import StableDiffusionInstructPix2PixPipeline
    from diffusers.utils import load_image

    model_id = "instruction-tuning-sd/cartoonizer"
    pipeline = StableDiffusionInstructPix2PixPipeline.from_pretrained(
        model_id, torch_dtype=torch.float16
    ).to("mps")
    print(f"image path is {input_path}")
    image = load_image(input_path)
    image = pipeline("Cartoonize the following image", image=image).images[0]
    image.save(output_path)

def _cartoonize_replicate(input_path, output_path, config):
    output = _sayak_cartoonizer(input_path, config)
    with open(output_path, 'wb') as o:
        o.write(output.read())
    return output_path

def _sayak_cartoonizer(input_path, config: StickerConfig):
    from replicate.client import Client
    client = Client(api_token=config.replicate_token)
    image = open(input_path, "rb");
    input = {
        "image": image
    }
    print('sending request to cartoonizer on replicate')
    output = client.run(
        f"harrolee/cartoonizer:{config.replicate_cartoonize_model_hash}",
        input=input
    )
    return output[0]

# if __name__ == "__main__":
#     # export the REPLICATE_API_TOKEN for this to work
#     _cartoonize_replicate("workspace/cartoonize_input/border_atWork_15.png", "workspace/output/cartoonized_border_atWork_15.png")