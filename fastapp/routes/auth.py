from fasthtml.common import *
from fastapp.services.db import DbClient
from starlette.responses import JSONResponse, RedirectResponse
from dataclasses import dataclass

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

        # Add OAuth buttons if enabled
        if auth_config.is_oauth_enabled:
            oauth_buttons = Div(
                H3("Or login with:", cls="text-center mb-3"),
                Div(
                    A("Login with Google", 
                      href="/auth/google",
                      cls="btn btn-light w-100 mb-2"),
                    A("Login with GitHub",
                      href="/auth/github", 
                      cls="btn btn-dark w-100"),
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
        
        # Debug logging
        print(f"Login attempt for user: {username}")
        print(f"Current users in DB: {DbClient._users}")
        
        # Check if user exists and password is correct
        user = db_client.get_user_by_username(username)
        
        if user and user.get('password') == password:  # In production, use proper password hashing!
            # Set user in session
            print(f"Login successful for user: {username}")
            session['user_id'] = username
            return RedirectResponse('/', status_code=303)
        else:
            # Debug logging
            print(f"Login failed for user: {username}")
            if not user:
                print(f"User not found: {username}")
            elif user.get('password') != password:
                print(f"Password mismatch for user: {username}")
            
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
        
        # Create user
        db_client.create_user(username, password)  # In production, hash the password!
        
        # Set user in session
        session['user_id'] = username
        
        return RedirectResponse('/', status_code=303)
    
    @rt("/logout")
    def get(session):
        if 'user_id' in session:
            del session['user_id']
        return RedirectResponse('/login', status_code=303)

    if app.state.auth_config.is_oauth_enabled:
        @rt("/auth/google")
        def get_google_auth(request):
            client = request.app.state.google_client
            redirect_uri = redir_url(request, "/auth_redirect", scheme='http')
            auth_url = client.get_auth_url(redirect_uri, state='google')
            return RedirectResponse(auth_url)

        @rt("/auth/github")
        def get_github_auth(request):
            client = request.app.state.github_client
            redirect_uri = redir_url(request, "/auth_redirect", scheme='http')
            auth_url = client.get_auth_url(redirect_uri, state='github')
            return RedirectResponse(auth_url) 