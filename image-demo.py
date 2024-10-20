from io import BytesIO
from fasthtml.common import *
from pathlib import Path
from PIL import Image, ImageOps

pages = {"main_page": "main_page"}

app,rt = fast_app()
# gridlink = Link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/flexboxgrid/6.3.1/flexboxgrid.min.css", type="text/css")
# app = FastHTML(hdrs=(picolink, gridlink))


collections_path = Path('collections')

@rt('/collections/{id}')
def get(): return collection(1)


def collection(id):
    collection_path = collections_path / str(id)
    return Div(*[Img(src=path) for path in collection_path.glob('*')])

# Main page
@rt('/')
def get():
    # add = Form(Group(upl, inp, Button("Sticker!")), hx_post="/upload-img", target_id='displayed-image', hx_swap="outerHTML")
    # sticker_containers = [sticker_preview(g) for g in gens(limit=10)] # Start with last 10
    # gen_list = Div(*sticker_containers[::-1], id='gen-list', cls="row") # flexbox container: class = row
    return Title('Image Upload Demo'), Main(H1('Image Upload'), image_upload(), cls='container')

def image_upload(): 
    return Article(
        H2('Step 1: Upload an Image'),
        Form(hx_encoding='multipart/form-data', hx_post="/upload-image", hx_target="#displayed-image")(
            Input(type='file', id='imageup', accept='image/*'),
            Button("Upload", type="submit", cls='secondary'),
        ),
        Figure(id='displayed-image')
    )

@rt('/upload-image')
async def post(imageup: UploadFile):
    bytes = await imageup.read()
    img = Image.open(BytesIO(bytes))
    img.thumbnail((1024, 1024))
    img = ImageOps.exif_transpose(img) # Fix image rotation based on exif metadata
    fname = f"workspace/input/temp.png"
    img.save(fname)
    return (Figure(
                Img(src=fname, alt="preview image"), id="displayed-image"), 
                Form(hx_post="stickerize", hx_target="#displayed-image")(
                    Input(type='text', id='sticker_name', accept='text/*'),
                    Button("Stickerize Image", type="submit"), 
                )
            )

# add the ability to stickerize it

@rt('/stickerize')
async def post(sticker_name: str):
    fname = f"collections/1/test2.png"
    img = Image.open(fname)
    # call stickerizer, somehow make it save the sticker with this name: sticker_name
    sticker_path = fname
    return Figure(Img(src=sticker_path, alt="stickerized image"), id="displayed-image")





# add to a collection?
# sql database of sticker collections
# a collection page:
    # named cards on a page
        # when clicked, the cards accordion into available stickers


serve()



# Show the image (if available) and prompt for a generation
def sticker_preview(g):
    grid_cls = "box col-xs-12 col-sm-6 col-md-4 col-lg-3"
    image_path = f"{g.folder}/{g.id}.png"
    if os.path.exists(image_path):
        return Div(Card(
                       Img(src=image_path, alt="Card image", cls="card-img-top"),
                       Div(P(B("Prompt: "), g.prompt, cls="card-text"),cls="card-body"),
                   ), id=f'gen-{g.id}', cls=grid_cls)
    return Div(f"Generating gen {g.id} with prompt {g.prompt}", 
            id=f'gen-{g.id}', hx_get=f"/gens/{g.id}", 
            hx_trigger="every 2s", hx_swap="outerHTML", cls=grid_cls)
