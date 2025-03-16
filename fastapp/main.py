from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fasthtml.common import *
from fastapp.make_sticker.config import StickerConfig
from fastapp.services.db import DbClient
from fastapp.routes.auth import setup_auth_routes
from fastapp.routes.stickers import setup_sticker_routes
from fastapp.routes.dashboard import setup_dashboard_routes
import os

# Load .env file if it exists
if os.path.exists(".env"):
    load_dotenv()

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

# Set up routes
setup_auth_routes(app)
setup_sticker_routes(app, rt)
setup_dashboard_routes(app, rt)

# @app.get(auth_callback_path)
# def auth_redirect(code:str, request, session):
#     redir = redir_url(request, auth_callback_path, scheme='http')
#     user_info = github_client.retr_info(code, redir)
#     user_id = user_info[github_client.id_key] # get their ID
#     session['user_id'] = user_id # save ID in the session
#     # user_in_db(user_id)
#     return RedirectResponse('/', status_code=303)

serve()

# The following commented code is kept for reference but not used
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

# def collection_accordion():
#     """UI components can be styled and reused.
#     UI libraries can be installed using `pip`."""
#     # accs = [accordion(id=id, question=q, answer=a,
#     #     question_cls="text-black s-body", answer_cls=a_cls, container_cls=c_cls)
#     #     for id,(q,a) in enumerate(qas)]
#     return accordion()

# def sticker_preview(g):
#     grid_cls = "box col-xs-12 col-sm-6 col-md-4 col-lg-3"
#     image_path = f"{g.folder}/{g.id}.png"
#     if os.path.exists(image_path):
#         return Div(Card(
#                        Img(src=image_path, alt="Card image", cls="card-img-top"),
#                        Div(P(B("Prompt: "), g.prompt, cls="card-text"),cls="card-body"),
#                    ), id=f'gen-{g.id}', cls=grid_cls)
#     return Div(f"Generating gen {g.id} with prompt {g.prompt}", 
#             id=f'gen-{g.id}', hx_get=f"/gens/{g.id}", 
#             hx_trigger="every 2s", hx_swap="outerHTML", cls=grid_cls)