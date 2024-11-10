from app.make_sticker.config import StickerConfig


def remove_background(input_path, output_path, config: StickerConfig):
    if config.is_local == 'true':
        return _gatis(input_path, output_path)
    else:
        return _rm_background_replicate(input_path, output_path, config)

def _gatis(input_path, output_path, session=None):
    from rembg import remove, new_session
    with open(input_path, 'rb') as i:
        with open(output_path, 'wb') as o:
            input = i.read()
            output = remove(input, session=session) if session else remove(input)
            o.write(output)
    return output_path

def single_lucataco_rm_background(input_path, output_path, config):
    output = _lucataco(input_path, config=config)
    with open(output_path, 'wb') as o:
        o.write(output.read())
    return output_path

def _rm_background_replicate(input_path, output_path, config):
    output = _lucataco(input_path, config)
    with open(output_path, 'wb') as o:
        o.write(output.read())
    return output_path

def _lucataco(input_path, config: StickerConfig):
    from replicate.client import Client
    client = Client(api_token=config.replicate_token)
    image = open(input_path, "rb");
    input = {
        "image": image
    }
    print('sending request to remove-bg on replicate')
    output = client.run(
        f"lucataco/remove-bg:{config.replicate_rm_background_model_hash}",
        input=input
    )
    return output

if __name__ == "__main__":
    single_lucataco_rm_background("workspace/rm_bg_input/cartoonized_border_atWork_15.png", "workspace/output/_lucataco.png")