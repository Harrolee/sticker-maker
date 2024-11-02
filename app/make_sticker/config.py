from pathlib import Path
from dotenv import dotenv_values, load_dotenv

config = dotenv_values()
class AppConfig():
    def __init__(self):
        self.workspace_dir = 'workspace'

        self.is_local = config["IS_LOCAL"]

        # replicate
        self.replicate_token = config['REPLICATE_API_TOKEN']
        self.replicate_model_hash = config['REPLICATE_MODEL_HASH']
        
        # email
        self.sender_email = config["SENDER_EMAIL"]
        self.sender_email_password = config["SENDER_EMAIL_PASSWORD"]
        self.supplier_email = config["SUPPLIER_EMAIL"]
        self.support_email = config["SUPPORT_EMAIL"]

        self.dirs = ['border_input', 'cartoonize_input','lift_input','rm_background_input','tab_input' ]
        self.init_dirs()

    def init_dirs(self):
        for dir in self.dirs:
            Path(f'{self.workspace_dir}/{dir}').mkdir(exist_ok=True,parents=True)
