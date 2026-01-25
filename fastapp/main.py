from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fasthtml.common import *
from fastapp.make_sticker.config import StickerConfig
from fastapp.services.db import DbClient
from fastapp.routes.auth import setup_auth_routes
from fastapp.routes.stickers import setup_sticker_routes
from fastapp.routes.dashboard import setup_dashboard_routes
from fastapp.routes.admin import setup_admin_routes
from fastapp.auth_config import AuthConfig
import os

# Load .env file if it exists
if os.path.exists(".env"):
    load_dotenv()

def create_app():
    # Initialize configuration
    auth_config = AuthConfig()

    # Add custom styling
    punk_styles = Style("""
        :root {
            --primary: #ff3c3c;
            --bg-color: #1a1a1a;
            --text-color: #f4f4f4;
            --accent: #ffd700;
            --secondary-bg: #2a2a2a;
            --font-headers: 'Permanent Marker', cursive;
            --font-body: 'Roboto', sans-serif;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: var(--font-body);
            background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23242424' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: var(--font-headers);
            color: var(--accent);
            text-transform: uppercase;
            letter-spacing: 2px;
            text-shadow: 2px 2px 0px rgba(0,0,0,0.3);
        }

        .button {
            background-color: var(--primary);
            color: var(--text-color);
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            text-transform: uppercase;
            font-weight: bold;
            letter-spacing: 1px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }

        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 8px rgba(0,0,0,0.3);
            background-color: #ff5252;
        }

        ul {
            background-color: var(--secondary-bg);
            border-radius: 8px;
            padding: 20px;
            box-shadow: inset 0 0 10px rgba(0,0,0,0.3);
        }

        li {
            border-bottom: 1px solid #333;
            padding: 12px;
            transition: all 0.3s ease;
        }

        li:hover {
            background-color: rgba(255,255,255,0.05);
            transform: translateX(5px);
        }

        .sticker-published {
            border-left: 4px solid var(--accent);
        }

        .sticker-draft {
            border-left: 4px solid var(--primary);
        }

        .processing-status {
            color: var(--accent);
            font-style: italic;
        }

        .error-status {
            color: var(--primary);
        }

        .ready-status {
            color: #4CAF50;
        }

        .storefront-link {
            color: var(--accent);
            text-decoration: none;
            font-weight: bold;
        }

        .storefront-link:hover {
            text-decoration: underline;
        }
    """)

    google_fonts = Link(
        rel="stylesheet",
        href="https://fonts.googleapis.com/css2?family=Permanent+Marker&family=Roboto:wght@400;700&display=swap"
    )

    # Initialize Auth0 client
    auth0_client = None

    if auth_config.is_auth0_enabled:
        from fastapp.services.oauth import Auth0AppClient
        auth0_client = Auth0AppClient(
            client_id=auth_config.auth0_client_id,
            client_secret=auth_config.auth0_client_secret,
            domain=auth_config.auth0_domain
        )

    auth_callback_path = "/auth_redirect"

    def before(req, session):
        auth = req.scope['auth'] = session.get('user_id', None)
        if not auth: return RedirectResponse('/login', status_code=303)

    # Skip auth for login-related paths
    skip_auth_paths = ['/login', auth_callback_path, '/create-account', '/complete-login', '/complete-account-creation']
    if auth_config.is_auth0_enabled:
        skip_auth_paths.append('/auth/auth0')

    bware = Beforeware(before, skip=skip_auth_paths)

    @asynccontextmanager
    async def lifespan(app: FastHTML):
        # Initialize all state during startup
        app.state.db_client = DbClient()
        app.state.config = StickerConfig()
        app.state.auth_config = auth_config
        app.state.auth0_client = auth0_client

        # Setup all routes after state is initialized
        setup_auth_routes(app)
        setup_sticker_routes(app, app.route)
        setup_dashboard_routes(app, app.route)
        setup_admin_routes(app, app.route)

        if auth_config.is_auth0_enabled:
            @app.get(auth_callback_path)
            def auth_redirect(code: str, state: str, request, session):
                redir = redir_url(request, auth_callback_path, scheme='http')
                db_client = request.app.state.db_client

                if state != 'auth0':
                    return RedirectResponse('/login?error=invalid_provider', status_code=303)

                client = request.app.state.auth0_client
                if not client:
                    return RedirectResponse('/login?error=auth0_not_configured', status_code=303)

                try:
                    user_info = client.retr_info(code, redir)
                    auth0_id = user_info.get('sub')
                    email = user_info.get('email')
                    name = user_info.get('name') or user_info.get('nickname')

                    if not auth0_id or not email:
                        print(f"Auth0 missing required info: sub={auth0_id}, email={email}")
                        return RedirectResponse('/login?error=missing_user_info', status_code=303)

                    # Get or create user in database
                    user = db_client.get_or_create_auth0_user(auth0_id, email, name)
                    if not user:
                        return RedirectResponse('/login?error=user_creation_failed', status_code=303)

                    # Use the database user_id for the session
                    session['user_id'] = user['user_id']
                except Exception as e:
                    print(f"Auth0 callback error: {e}")
                    return RedirectResponse('/login?error=auth0_error', status_code=303)

                return RedirectResponse('/', status_code=303)

        try:
            yield
        finally:
            # Cleanup during shutdown
            if hasattr(app.state, 'db_client'):
                app.state.db_client.close()

    # Create the application with lifecycle management
    app, _ = fast_app(
        before=bware,
        lifespan=lifespan,
        hdrs=(google_fonts, punk_styles)
    )
    return app

# Create and serve the application
app = create_app()
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
