from dotenv import dotenv_values
import os

class AuthConfig():
    def __init__(self):
        secrets = dotenv_values(dotenv_path=".env")
        self.auth_mode = os.getenv('AUTH_MODE', 'dev')  # 'dev' or 'prod'

        # OAuth configs only loaded in prod mode
        if self.auth_mode == 'prod':
            self.google_oauth_api_key = secrets.get('GOOGLE_OAUTH_API_KEY')
            self.google_client_id = secrets.get("CLIENT_ID")
            self.google_client_secret = secrets.get("CLIENT_SECRET")

            self.github_client_id = secrets.get('GITHUB_CLIENT_ID')
            self.github_client_secret = secrets.get('GITHUB_CLIENT_SECRET')

            # Auth0 configuration
            self.auth0_domain = secrets.get('AUTH0_DOMAIN')
            self.auth0_client_id = secrets.get('AUTH0_CLIENT_ID')
            self.auth0_client_secret = secrets.get('AUTH0_CLIENT_SECRET')

            # Validate required OAuth configs in prod mode
            missing = []
            for key in ['GOOGLE_OAUTH_API_KEY', 'CLIENT_ID', 'CLIENT_SECRET',
                       'GITHUB_CLIENT_ID', 'GITHUB_CLIENT_SECRET']:
                if not secrets.get(key):
                    missing.append(key)
            if missing:
                raise ValueError(f"Missing required OAuth configs in prod mode: {', '.join(missing)}")

    @property
    def is_oauth_enabled(self):
        return self.auth_mode == 'prod'

    @property
    def is_auth0_enabled(self):
        """Check if Auth0 is configured and enabled."""
        if self.auth_mode != 'prod':
            return False
        return all([
            getattr(self, 'auth0_domain', None),
            getattr(self, 'auth0_client_id', None),
            getattr(self, 'auth0_client_secret', None)
        ])
