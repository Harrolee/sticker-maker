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

if __name__ == "__main__":
    # export the REPLICATE_API_TOKEN for this to work
    cartoonize_replicate("workspace/cartoonize_input/border_atWork_15.png", "workspace/output/cartoonized_border_atWork_15.png")