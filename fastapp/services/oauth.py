from abc import ABC, abstractmethod
import requests
from urllib.parse import urlencode

class OAuthClient(ABC):
    @abstractmethod
    def get_auth_url(self, redirect_uri: str, state: str = None) -> str:
        pass

    @abstractmethod
    def retr_info(self, code: str, redirect_uri: str) -> dict:
        pass

class GoogleAppClient(OAuthClient):
    auth_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
    token_endpoint = "https://oauth2.googleapis.com/token"
    userinfo_endpoint = "https://www.googleapis.com/oauth2/v2/userinfo"
    scope = "openid email profile"
    id_key = "id"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    def get_auth_url(self, redirect_uri: str, state: str = None) -> str:
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': self.scope,
        }
        if state:
            params['state'] = state
        return f"{self.auth_endpoint}?{urlencode(params)}"

    def retr_info(self, code: str, redirect_uri: str) -> dict:
        # Exchange code for token
        token_response = requests.post(
            self.token_endpoint,
            data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
        ).json()

        # Use token to get user info
        user_info = requests.get(
            self.userinfo_endpoint,
            headers={'Authorization': f"Bearer {token_response['access_token']}"}
        ).json()

        return user_info

class GitHubAppClient(OAuthClient):
    auth_endpoint = "https://github.com/login/oauth/authorize"
    token_endpoint = "https://github.com/login/oauth/access_token"
    userinfo_endpoint = "https://api.github.com/user"
    scope = "read:user user:email"
    id_key = "id"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    def get_auth_url(self, redirect_uri: str, state: str = None) -> str:
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'scope': self.scope,
        }
        if state:
            params['state'] = state
        return f"{self.auth_endpoint}?{urlencode(params)}"

    def retr_info(self, code: str, redirect_uri: str) -> dict:
        # Exchange code for token
        headers = {'Accept': 'application/json'}
        token_response = requests.post(
            self.token_endpoint,
            data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'redirect_uri': redirect_uri
            },
            headers=headers
        ).json()

        # Use token to get user info
        user_info = requests.get(
            self.userinfo_endpoint,
            headers={
                'Authorization': f"Bearer {token_response['access_token']}",
                'Accept': 'application/json'
            }
        ).json()

        return user_info


class Auth0AppClient(OAuthClient):
    """Auth0 OAuth client for authentication.

    Auth0 uses OpenID Connect, so we get user info from the /userinfo endpoint.
    The 'sub' field contains the unique user identifier.
    """
    scope = "openid profile email"
    id_key = "sub"  # Auth0 uses 'sub' (subject) as the unique identifier

    def __init__(self, client_id: str, client_secret: str, domain: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.domain = domain
        # Auth0 endpoints are based on the domain
        self.auth_endpoint = f"https://{domain}/authorize"
        self.token_endpoint = f"https://{domain}/oauth/token"
        self.userinfo_endpoint = f"https://{domain}/userinfo"

    def get_auth_url(self, redirect_uri: str, state: str = None) -> str:
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': self.scope,
            'audience': f"https://{self.domain}/userinfo",
        }
        if state:
            params['state'] = state
        return f"{self.auth_endpoint}?{urlencode(params)}"

    def retr_info(self, code: str, redirect_uri: str) -> dict:
        # Exchange code for token
        token_response = requests.post(
            self.token_endpoint,
            json={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            },
            headers={'Content-Type': 'application/json'}
        ).json()

        if 'error' in token_response:
            raise Exception(f"Auth0 token error: {token_response.get('error_description', token_response['error'])}")

        # Use token to get user info
        user_info = requests.get(
            self.userinfo_endpoint,
            headers={'Authorization': f"Bearer {token_response['access_token']}"}
        ).json()

        return user_info
