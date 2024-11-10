from pathlib import Path
from dotenv import dotenv_values


class StickerConfig():
    def __init__(self):
        config = dotenv_values(dotenv_path="make_sticker/_sticker.env")
        self.workspace_dir = 'workspace'

        self.is_local = config["IS_LOCAL"]

        # replicate
        self.replicate_token = config['REPLICATE_API_TOKEN']
        self.replicate_cartoonize_model_hash = config['REPLICATE_CARTOONIZE_MODEL_HASH']
        self.replicate_rm_background_model_hash = config['REPLICATE_RM_BACKGROUND_MODEL_HASH']
        
        # email
        self.sender_email = config["SENDER_EMAIL"]
        self.sender_email_password = config["SENDER_EMAIL_PASSWORD"]
        self.supplier_email = config["SUPPLIER_EMAIL"]
        self.support_email = config["SUPPORT_EMAIL"]

        # storefront
        self.sell_app_storefront_name = config["SELL_APP_STOREFRONT_NAME"]
        self.sell_app_token = config["SELL_APP_TOKEN"]

        self.dirs = ['border_input', 'cartoonize_input','lift_input','rm_background_input','tab_input', 'output' ]
        self.init_dirs()

    def init_dirs(self):
        for dir in self.dirs:
            Path(f'{self.workspace_dir}/{dir}').mkdir(exist_ok=True,parents=True)
