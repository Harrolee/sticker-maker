import json
from dotenv import dotenv_values

class AuthConfig():
    def __init__(self):
        secrets = dotenv_values(dotenv_path="_auth.env")
        try:
            with open("client_secret_376442012597-ehpirc0b6k472k140mntul76t8a0jgc0.apps.googleusercontent.com.json", 'r') as f:
                auth_config = json.load(f)
        except RuntimeError as error:
            raise LookupError(f"could not open client_secret json, Error: {error}")
        
        self.google_oauth_api_key = secrets['GOOGLE_OAUTH_API_KEY']
        self.google_client_id = auth_config["web"]["client_id"]
        self.google_client_secret = auth_config["web"]["client_secret"]
        
        self.github_client_id = secrets['GITHUB_CLIENT_ID']
        self.github_client_secret = secrets['GITHUB_CLIENT_SECRET']