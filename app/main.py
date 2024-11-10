import os
import sys

def print_debug_info():
    print("=== Python Environment Debug Info ===")
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"Directory Contents: {os.listdir('.')}")
    print(f"Parent Directory Contents: {os.listdir('..')}")
    print("Python Path:")
    for path in sys.path:
        print(f"  - {path}")
    print("Environment Variables:")
    for key, value in os.environ.items():
        if 'PYTHON' in key:
            print(f"  {key}: {value}")
    print("================================")

# Add this at the top of your main.py, before the imports
print_debug_info()

from contextlib import asynccontextmanager
import uuid
from io import BytesIO
from dotenv import dotenv_values
from fasthtml.common import *
# from fasthtml.oauth import GoogleAppClient, GitHubAppClient, redir_url
from PIL import Image, ImageOps

from .make_sticker.config import StickerConfig
# from auth_config import AuthConfig
from services.db import DbClient
from .services.storefront import StickerPublisher, StorefrontProduct
from ui_components import accordion
from .make_sticker.main import stickerize


# auth_config = AuthConfig()
# google_client = GoogleAppClient(
#     client_id=auth_config.google_client_id,
#     client_secret=auth_config.google_client_secret
# )
# github_client = GitHubAppClient(
#     client_id=auth_config.github_client_id,
#     client_secret=auth_config.github_client_secret
# )
auth_callback_path = "/auth_redirect"

def before(req, session):
    auth = req.scope['auth'] = session.get('user_id', None)
    if not auth: return RedirectResponse('/login', status_code=303)
bware = Beforeware(before, skip=['/login', auth_callback_path, '/create-account', '/complete-login'])

@asynccontextmanager
async def lifespan(app: FastHTML):
    # Set up globally accessible singleton objects like db connection pool here
    config = dotenv_values(dotenv_path=".env")
    app.state.db_client = DbClient(config)
    app.state.config = StickerConfig(config)
    yield
    # Clean up globally accessible singleton objects here
    app.state.db_client.close()

app,rt = fast_app(before=bware, lifespan=lifespan)

@app.get('/login')
def login(request):
    # redir = redir_url(request,auth_callback_path)
    return P(
        Form(hx_get="complete-login", hx_target="#root", hx_encoding="multipart/form-data", hx_trigger="submit")
             (
                Input(type='text', id='email', placeholder="email here", accept='text/*'),
                Button("Login", type="submit"), 
             ),
        Form(hx_get="create-account", hx_target="#root", hx_encoding="multipart/form-data", hx_trigger="submit")
        (
            Input(type='text', id='name', placeholder="name here", accept='text/*'),
            Input(type='text', id='email', placeholder="email here", accept='text/*'),
            Button("Create Account", type="submit"), 
        ),
        # A('(Busted) Login with Github', href=github_client.login_link(redir)),
        # A('(Busted) Login with Google', href=google_client.login_link(redir)),
        id="root"
    )    

@app.get('/create-account')
def create_account(name: str, email: str, session, app: FastHTML):
    user_id = app.state.db_client.create_user(name, email)
    if user_id == None:
        return P(f"Error creating account")
    session['user_id'] = user_id
    session['user_name'] = name
    return JSONResponse(
        content={},
        status_code=200,
        headers={"HX-Redirect": "/"}
    )

@app.get('/complete-login')
def complete_login(email: str, session):
    user_id, name = app.state.db_client.find_user_info_by_email(email)
    if user_id == None:
        return P(f"Could not find a user account with email {email}")
    session['user_id'] = user_id
    session['user_name'] = name
    return JSONResponse(
        content={},
        status_code=200,
        headers={"HX-Redirect": "/"}
    )

# @app.get(auth_callback_path)
# def auth_redirect(code:str, request, session):
#     redir = redir_url(request, auth_callback_path, scheme='http')
#     user_info = github_client.retr_info(code, redir)
#     user_id = user_info[github_client.id_key] # get their ID
#     session['user_id'] = user_id # save ID in the session
#     # user_in_db(user_id)
#     return RedirectResponse('/', status_code=303)

@app.get('/logout')
def logout(session):
    session.pop('user_id', None)
    return RedirectResponse('/login', status_code=303)

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
async def post(sticker_name: str, image_input: UploadFile, session):
    # show a loading spinner until the process is complete
    bytes = await image_input.read()
    img = Image.open(BytesIO(bytes))
    img.thumbnail((1024, 1024))
    img = ImageOps.exif_transpose(img)
    basename = str(uuid.uuid4())[:4]
    fname = f"workspace/input/{basename}-temp.png"
    img.save(fname)
    
    output_path = stickerize(f"{basename}-temp.png", sticker_name, app.state.config)

    session['sticker_url'] = output_path
    session['sticker_name'] = sticker_name
    return Article(
            H2('Step 2: Post to Storefront', id="narrator"),
            Form(hx_post="post-to-storefront", hx_target="#narrator")(
                Button("Post", type="submit"), 
            ),
            Figure(
                Img(src=output_path, alt="stickerized image"), 
                id="displayed-image"), 
            id="main_content"
        )


@rt('/post-to-storefront')
async def post(session):
    storefront_product = StorefrontProduct(
        title=session['sticker_name'], 
        description=f"Custom made {session['sticker_name']} sticker, made by {session['user_name']}", 
        redirect_url="http://www.localhost:5001",
        image_url=session['sticker_url'],
        price=400
    )
    publisher = StickerPublisher(app.state.config)
    storefront_product_id, product_url = publisher.publish_sticker(storefront_product)
    app.state.db_client.save_sticker(storefront_product_id, storefront_product.title, session['user_id'])
    # should also save the image to s3
    return A(f"Here's a link to your sticker: {storefront_product.title}", href=product_url, id="narrator")


# def collection():
#     return Article(
#             H2('Step 3: Add to a collection'),
#             Form(hx_post="add-to-collection", hx_target="#main_content")(
#                 Select(style="width: auto", id="attr1st")(
#                     Option("Nucklehead", value="Nucklehead", selected=True), Option("Fumblebees", value="Fumblebees")
#                 ),
#                 Button("Add", type="submit"), 
#             ),
#             Figure(
#                 Img(src=img, alt="stickerized image"), 
#                 id="displayed-image"), 
#             id="main_content"
#         )

# @rt('/add-to-collection')
# async def post(collection_name: str):
#     col = "flex flex-col"
#     bnset = "shadow-[inset_0_2px_4px_rgba(255,255,255,0.1),0_4px_8px_rgba(0,0,0,0.5)]"
#     return Article(
#         accordion(id="uhhhh", question=collection_name, answer="put pictures here",
#                   question_cls="text-black s-body",
#         answer_cls="s-body text-black/80 col-span-full",
#         container_cls=f"{col} justify-between bg-soft-blue rounded-[1.25rem] {bnset}"),
#         id="main_content"
#     )



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