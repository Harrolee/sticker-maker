from dotenv import dotenv_values

class AuthConfig():
    def __init__(self):
        secrets = dotenv_values(dotenv_path=".env")
       
        self.google_oauth_api_key = secrets['GOOGLE_OAUTH_API_KEY']
        self.google_client_id = secrets["CLIENT_ID"]
        self.google_client_secret = secrets["CLIENT_SECRET"]
        
        self.github_client_id = secrets['GITHUB_CLIENT_ID']
        self.github_client_secret = secrets['GITHUB_CLIENT_SECRET']