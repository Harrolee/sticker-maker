import os

class AuthConfig():
    def __init__(self):
        self.auth_mode = os.getenv('AUTH_MODE', 'dev')  # 'dev' or 'prod'

        # Auth0 configuration (primary auth method in prod)
        if self.auth_mode == 'prod':
            self.auth0_domain = os.getenv('AUTH0_DOMAIN')
            self.auth0_client_id = os.getenv('AUTH0_CLIENT_ID')
            self.auth0_client_secret = os.getenv('AUTH0_CLIENT_SECRET')

            # Validate Auth0 configs in prod mode
            missing = []
            for key in ['AUTH0_DOMAIN', 'AUTH0_CLIENT_ID', 'AUTH0_CLIENT_SECRET']:
                if not os.getenv(key):
                    missing.append(key)
            if missing:
                raise ValueError(f"Missing required Auth0 configs in prod mode: {', '.join(missing)}")

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
