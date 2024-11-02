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
    print('sending request to remove-bg on replicate')
    output = replicate.run(
        "lucataco/remove-bg:95fcc2a26d3899cd6c2691c900465aaeff466285a65c14638cc5f36f34befaf1",
        input=input
    )
    return output

if __name__ == "__main__":
    single_lucataco_rm_background("workspace/rm_bg_input/cartoonized_border_atWork_15.png", "workspace/output/_lucataco.png")