from fasthtml.common import *
from starlette.responses import RedirectResponse


def build_redirect_uri(request, path: str) -> str:
    """Build a full redirect URI from the request and path."""
    proto = request.headers.get('x-forwarded-proto', request.url.scheme)
    host = request.headers.get('x-forwarded-host', request.url.netloc)
    return f"{proto}://{host}{path}"


def setup_auth_routes(app):
    rt = app.route

    @rt("/login")
    def get(request):
        login_page = Div(
            H1("Welcome", cls="text-center mb-4"),
            P("Sign in to access your stickers", cls="text-center mb-4"),
            A("Sign in with Auth0",
              href="/auth/auth0",
              cls="btn btn-primary w-100"),
            cls="login-container p-4",
            style="max-width: 400px; margin: 100px auto;"
        )
        return Titled("Login", login_page)

    @rt("/logout")
    def get(session):
        if 'user_id' in session:
            del session['user_id']
        return RedirectResponse('/login', status_code=303)

    @rt("/auth/auth0")
    def get_auth0_auth(request):
        client = request.app.state.auth0_client
        redirect_uri = build_redirect_uri(request, "/auth_redirect")
        auth_url = client.get_auth_url(redirect_uri, state='auth0')
        return RedirectResponse(auth_url)
