from fastcore.parallel import threaded
from contextlib import asynccontextmanager
import uuid
from io import BytesIO
from dotenv import dotenv_values
from fasthtml.common import *
# from fasthtml.oauth import GoogleAppClient, GitHubAppClient, redir_url
from PIL import Image, ImageOps
# from auth_config import AuthConfig
from fastapp.make_sticker.config import StickerConfig
from fastapp.services.db import DbClient
from fastapp.services.storefront import StickerPublisher, StorefrontProduct
from fastapp.ui_components import accordion
from fastapp.make_sticker.main import stickerize
from dataclasses import dataclass
from fastapp.db.models import Sticker, User
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select


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
    app.state.db_client = DbClient()
    app.state.config = StickerConfig()
    yield
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
def complete_login(email: str, session, app: FastHTML):
    user_id, name = app.state.db_client.find_user_by_email(email)
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
def get(auth):
    if not auth: return RedirectResponse('/login', 303)
    
    return Titled("Create Sticker",
        Div(
            Grid(
                H1("Sticker Creator"),
                A("View Your Stickers", href="/dashboard", cls="button")
            ),
            image_upload()
        )
    )

def image_upload(): 
    return Article(
        H2('Step 1: Upload an image'),
        Form(hx_post="stickerize", hx_target="#main_content", 
             hx_encoding="multipart/form-data", 
             hx_trigger="submit",
             hx_indicator="#loading-spinner")(
            Input(type='text', id='sticker_name', name='sticker_name', accept='text/*'),
            Input(type='file', id='image_input', name='image_input', accept='image/*'),
            Button("Stickerize Image", type="submit"), 
        ),
        Div(
            Div("Processing image...", cls="spinner-text"),
            cls="spinner-container",
            id="loading-spinner",
            style="display:none"
        ),
        id="main_content"
    )

def processing_preview(basename: str, sticker_name: str, sticker_url):
    """Shows a loading state while checking if processing is complete"""
    if os.path.exists(sticker_url):
        return Article(
            H2('Step 2: Post to Storefront', id="narrator"),
            Form(hx_post="post-to-storefront", hx_target="#narrator")(
                Button("Post", type="submit"), 
            ),
            Figure(
                Img(src=sticker_url, alt="stickerized image"), 
                id="displayed-image"
            ), 
            id="main_content"
        )
    else:
        return Article(
            Div(
                f"Creating {sticker_name} sticker...",
                id="processing-status",
                hx_get=f"/process-status/{basename}",
                hx_trigger="every 3s",
                hx_target="#main_content"
            ),
            id="main_content"
        )

@rt('/stickerize')
async def post(sticker_name: str, image_input: UploadFile, session):
    basename = str(uuid.uuid4())[:4]
    bytes = await image_input.read()
    img = Image.open(BytesIO(bytes))
    img.thumbnail((1024, 1024))
    img = ImageOps.exif_transpose(img)
    input_path = f"{app.state.config.workspace_dir}/input/{basename}.png"
    img.save(input_path)
    process_image(basename, sticker_name, app.state.config)
    output_path = f"{app.state.config.workspace_dir}/output/{basename}.png"
    session['sticker_url'] = output_path
    session['sticker_name'] = sticker_name
    return processing_preview(basename, sticker_name, output_path)

@rt('/process-status/{basename}')
def get_process_status(basename: str, session):
    """Endpoint to check processing status"""
    return processing_preview(basename, session['sticker_name'], session['sticker_url'])

@threaded
def process_image(basename: str, sticker_name: str, config):
    """Process image in background thread"""
    stickerize(f"{basename}.png", sticker_name, config)

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

@rt("/dashboard")
def get(auth, app: FastHTML):
    if not auth: return RedirectResponse('/login', 303)
    
    # Get database connection from app state
    db_client = app.state.db_client
    
    # Get user's stickers
    with Session(db_client.engine) as session:
        user_stickers = session.execute(
            select(Sticker).where(Sticker.creator == auth)
        ).scalars().all()
    
    return Titled(
        f"Your Stickers",
        Div(
            H2("Your Stickers"),
            A("Create New Sticker", href="/", cls="button"),
            Div(
                H3("Drafts"),
                Ul(*[sticker_to_li(s) for s in user_stickers if not s.storefront_product_id]),
                H3("Published"),
                Ul(*[sticker_to_li(s) for s in user_stickers if s.storefront_product_id]),
                id="sticker-list"
            )
        )
    )

def sticker_to_li(sticker: Sticker):
    """Convert a Sticker model to a list item for display"""
    edit = AX('Edit', f'/sticker/{sticker.sticker_id}', 'sticker-editor')
    preview = AX('Preview', f'/preview/{sticker.sticker_id}', 'preview-area')
    status = "published" if sticker.storefront_product_id else "draft"
    return Li(
        f"{sticker.name}",
        Div(edit, ' | ', preview),
        cls=f"sticker-{status}"
    )

@rt("/create-sticker") 
def post(text: str, name: str, auth, app: FastHTML):
    if not auth: return RedirectResponse('/login', 303)
    
    db_client = app.state.db_client
    
    # Create new sticker
    with Session(db_client.engine) as session:
        new_sticker = Sticker(
            name=name,
            creator=auth,
            storefront_product_id=None  # Will be set when published
        )
        session.add(new_sticker)
        session.commit()
        sticker_id = new_sticker.sticker_id
    
    return (
        Div(f"Sticker '{name}' saved!", id="notifications"),
        # Your existing preview generation code...
    )

serve()