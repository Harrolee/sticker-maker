import uuid
from io import BytesIO
from fasthtml.common import *
from pathlib import Path
from PIL import Image, ImageOps
from ui_components import accordion
from backend.main import stickerize
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
    return Title('Image Upload Demo'), Main(image_upload(), cls='container', id='root')

def image_upload(): 
    return Article(
        H2('Step 1: Upload an image'),
        Form(hx_post="stickerize", hx_target="#main_content", 
                hx_encoding="multipart/form-data", hx_trigger="submit")(
            Input(type='text', id='sticker_name', accept='text/*'),
            Input(type='file', id='image_input', accept='image/*'),
            Button("Stickerize Image", type="submit"), 
        ),
        id="main_content"
    )

# @rt('/upload-image')
# async def post(imageup: UploadFile):
#     bytes = await imageup.read()
#     img = Image.open(BytesIO(bytes))
#     img.thumbnail((1024, 1024))
#     img = ImageOps.exif_transpose(img) # Fix image rotation based on exif metadata
#     fname = f"workspace/input/temp.png"
#     img.save(fname)
#     return Article(
#             H2('Step 2: Name your sticker'),
#             Form(hx_post="stickerize", hx_target="#main_content")(
#                 Input(type='text', id='sticker_name', accept='text/*'),
#                 Button("Stickerize Image", type="submit"), 
#             ),
#             Figure(
#                 Img(src=fname, alt="preview image"), 
#                 id="displayed-image"), 
#             id="main_content"
#         )

# add the ability to stickerize it

@rt('/stickerize')
async def post(sticker_name: str, image_input: UploadFile):
    # show a loading spinner until the process is complete
    bytes = await image_input.read()
    img = Image.open(BytesIO(bytes))
    img.thumbnail((1024, 1024))
    img = ImageOps.exif_transpose(img)
    basename = str(uuid.uuid4())[:4]
    fname = f"workspace/input/{basename}-temp.png"
    img.save(fname)
    
    output_path = stickerize(f"{basename}-temp.png")
    
    # call stickerizer, somehow make it save the sticker with this name: sticker_name

    print(sticker_name)
    return Article(
            H2('Step 2: Post to GumRoad', id="narrator"),
            Form(hx_post="post-to-gumroad", hx_target="#narrator")(
                Button("Post", type="submit"), 
            ),
            Figure(
                Img(src=output_path, alt="stickerized image"), 
                id="displayed-image"), 
            id="main_content"
        )


@rt('/post-to-gumroad')
async def post():
    # create product on gumroad
    # store product id in database
    # show the product id to user
    # show the user a link to the product on Gumroad

    return A("Sticker name here", href="https://www.google.com", id="narrator")
        # Article(
            # H2('Here\'s your link', href="https://www.google.com", id="narrator"),
        #     Figure(
        #         Img(src=img, alt="stickerized image"), 
        #         id="displayed-image"), 
        #     id="main_content"
        # )


def collection():
    return Article(
            H2('Step 3: Add to a collection'),
            Form(hx_post="add-to-collection", hx_target="#main_content")(
                Select(style="width: auto", id="attr1st")(
                    Option("Nucklehead", value="Nucklehead", selected=True), Option("Fumblebees", value="Fumblebees")
                ),
                Button("Add", type="submit"), 
            ),
            Figure(
                Img(src=img, alt="stickerized image"), 
                id="displayed-image"), 
            id="main_content"
        )

@rt('/add-to-collection')
async def post(collection_name: str):
    col = "flex flex-col"
    bnset = "shadow-[inset_0_2px_4px_rgba(255,255,255,0.1),0_4px_8px_rgba(0,0,0,0.5)]"
    return Article(
        accordion(id="uhhhh", question=collection_name, answer="put pictures here",
                  question_cls="text-black s-body",
        answer_cls="s-body text-black/80 col-span-full",
        container_cls=f"{col} justify-between bg-soft-blue rounded-[1.25rem] {bnset}"),
        id="main_content"
    )



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



def collection_accordion():
    """UI components can be styled and reused.
    UI libraries can be installed using `pip`."""
    # accs = [accordion(id=id, question=q, answer=a,
    #     question_cls="text-black s-body", answer_cls=a_cls, container_cls=c_cls)
    #     for id,(q,a) in enumerate(qas)]
    return accordion()