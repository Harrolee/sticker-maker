from fasthtml.common import *
from fastapp.services.db import DbClient
from starlette.responses import JSONResponse, RedirectResponse
from dataclasses import dataclass

def build_redirect_uri(request, path: str) -> str:
    """Build a full redirect URI from the request and path."""
    # Use X-Forwarded headers if behind a proxy (like Cloud Run)
    proto = request.headers.get('x-forwarded-proto', request.url.scheme)
    host = request.headers.get('x-forwarded-host', request.url.netloc)
    return f"{proto}://{host}{path}"

@dataclass
class LoginForm:
    username: str
    password: str

@dataclass
class CreateAccountForm:
    username: str
    password: str
    confirm_password: str

def setup_auth_routes(app):
    rt = app.route

    @rt("/login")
    def get(request):
        auth_config = request.app.state.auth_config

        login_form = Form(
            Div(
                H1("Login", cls="text-center mb-4"),
                cls="form-header"
            ),
            Div(
                Input(id="username", name="username", placeholder="Username", required=True),
                cls="form-group mb-3"
            ),
            Div(
                Input(id="password", name="password", type="password", placeholder="Password", required=True),
                cls="form-group mb-3"
            ),
            Div(
                Button("Login", type="submit", cls="btn-primary w-100"),
                cls="form-actions mb-3"
            ),
            Div(
                A("Create Account", href="/create-account", cls="text-center d-block"),
                cls="text-center"
            ),
            action="/complete-login",
            method="post",
            cls="login-form p-4"
        )

        # Build OAuth buttons if Auth0 is enabled
        oauth_buttons_list = []

        if auth_config.is_auth0_enabled:
            oauth_buttons_list.append(
                A("Login with Auth0",
                  href="/auth/auth0",
                  cls="btn btn-info w-100")
            )

        if oauth_buttons_list:
            oauth_buttons = Div(
                H3("Or login with:", cls="text-center mb-3"),
                Div(
                    *oauth_buttons_list,
                    cls="oauth-buttons"
                ),
                cls="mt-4"
            )
            login_form = Div(login_form, oauth_buttons)

        return Titled("Login", login_form)

    @rt("/create-account")
    def get():
        create_account_form = Form(
            Div(
                Input(id="username", name="username", placeholder="Username", required=True),
                cls="form-group"
            ),
            Div(
                Input(id="password", name="password", type="password", placeholder="Password", required=True),
                cls="form-group"
            ),
            Div(
                Input(id="confirm_password", name="confirm_password", type="password", placeholder="Confirm Password", required=True),
                cls="form-group"
            ),
            Div(
                Button("Create Account", type="submit"),
                A("Back to Login", href="/login", cls="ml-2"),
                cls="form-actions"
            ),
            action="/complete-account-creation",
            method="post"
        )

        return Titled("Create Account", create_account_form)

    @rt("/complete-login")
    def post(username: str, password: str, session, request):
        # Get database client from app state
        db_client = request.app.state.db_client

        # Check if user exists and password is correct
        if db_client.verify_password(username, password):
            print(f"Login successful for user: {username}")
            session['user_id'] = username
            return RedirectResponse('/', status_code=303)
        else:
            print(f"Login failed for user: {username}")

            # Return to login page with error
            error_form = Form(
                Div("Invalid username or password", cls="error-message"),
                Div(
                    Input(id="username", name="username", placeholder="Username", required=True, value=username),
                    cls="form-group"
                ),
                Div(
                    Input(id="password", name="password", type="password", placeholder="Password", required=True),
                    cls="form-group"
                ),
                Div(
                    Button("Login", type="submit"),
                    A("Create Account", href="/create-account", cls="ml-2"),
                    cls="form-actions"
                ),
                action="/complete-login",
                method="post"
            )

            return Titled("Login", error_form)

    @rt("/complete-account-creation")
    def post(username: str, password: str, confirm_password: str, session, request):
        # Get database client from app state
        db_client = request.app.state.db_client

        # Check if passwords match
        if password != confirm_password:
            error_form = Form(
                Div("Passwords do not match", cls="error-message"),
                Div(
                    Input(id="username", name="username", placeholder="Username", required=True, value=username),
                    cls="form-group"
                ),
                Div(
                    Input(id="password", name="password", type="password", placeholder="Password", required=True),
                    cls="form-group"
                ),
                Div(
                    Input(id="confirm_password", name="confirm_password", type="password", placeholder="Confirm Password", required=True),
                    cls="form-group"
                ),
                Div(
                    Button("Create Account", type="submit"),
                    A("Back to Login", href="/login", cls="ml-2"),
                    cls="form-actions"
                ),
                action="/complete-account-creation",
                method="post"
            )

            return Titled("Create Account", error_form)

        # Check if user already exists
        existing_user = db_client.get_user_by_username(username)
        if existing_user:
            error_form = Form(
                Div("Username already exists", cls="error-message"),
                Div(
                    Input(id="username", name="username", placeholder="Username", required=True),
                    cls="form-group"
                ),
                Div(
                    Input(id="password", name="password", type="password", placeholder="Password", required=True),
                    cls="form-group"
                ),
                Div(
                    Input(id="confirm_password", name="confirm_password", type="password", placeholder="Confirm Password", required=True),
                    cls="form-group"
                ),
                Div(
                    Button("Create Account", type="submit"),
                    A("Back to Login", href="/login", cls="ml-2"),
                    cls="form-actions"
                ),
                action="/complete-account-creation",
                method="post"
            )

            return Titled("Create Account", error_form)

        # Create user (password is hashed in create_user)
        result = db_client.create_user(username, password)

        if not result:
            error_form = Form(
                Div("Failed to create account. Please try again.", cls="error-message"),
                Div(
                    Input(id="username", name="username", placeholder="Username", required=True),
                    cls="form-group"
                ),
                Div(
                    Input(id="password", name="password", type="password", placeholder="Password", required=True),
                    cls="form-group"
                ),
                Div(
                    Input(id="confirm_password", name="confirm_password", type="password", placeholder="Confirm Password", required=True),
                    cls="form-group"
                ),
                Div(
                    Button("Create Account", type="submit"),
                    A("Back to Login", href="/login", cls="ml-2"),
                    cls="form-actions"
                ),
                action="/complete-account-creation",
                method="post"
            )
            return Titled("Create Account", error_form)

        # Set user in session
        session['user_id'] = username

        return RedirectResponse('/', status_code=303)

    @rt("/logout")
    def get(session):
        if 'user_id' in session:
            del session['user_id']
        return RedirectResponse('/login', status_code=303)

    if app.state.auth_config.is_auth0_enabled:
        @rt("/auth/auth0")
        def get_auth0_auth(request):
            client = request.app.state.auth0_client
            redirect_uri = build_redirect_uri(request, "/auth_redirect")
            auth_url = client.get_auth_url(redirect_uri, state='auth0')
            return RedirectResponse(auth_url)
