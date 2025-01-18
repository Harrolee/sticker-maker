from pathlib import Path
import os

class StickerConfig():
    def __init__(self):
        self.workspace_dir = 'fastapp/workspace'
        
        # Basic settings
        self.is_local = os.environ.get('IS_LOCAL', 'false').lower() == 'true'
        
        # API tokens
        self.replicate_token = os.environ.get('REPLICATE_API_TOKEN')
        self.replicate_cartoonize_model_hash = os.environ.get('REPLICATE_CARTOONIZE_MODEL_HASH')
        self.replicate_rm_background_model_hash = os.environ.get('REPLICATE_RM_BACKGROUND_MODEL_HASH')
        self.sell_app_token = os.environ.get('SELL_APP_TOKEN')
        self.sell_app_storefront_name = os.environ.get('SELL_APP_STOREFRONT_NAME')
        
        # Email settings
        self.sender_email = os.environ.get('SENDER_EMAIL')
        self.sender_email_password = os.environ.get('SENDER_EMAIL_PASSWORD')
        self.supplier_email = os.environ.get('SUPPLIER_EMAIL')
        self.support_email = os.environ.get('SUPPORT_EMAIL')

        # Initialize workspace directories
        self.dirs = ['border_input', 'cartoonize_input', 'lift_input', 
                    'rm_background_input', 'tab_input', 'output', 'input']
        self._init_dirs()

    def _init_dirs(self):
        for dir in self.dirs:
            Path(f'{self.workspace_dir}/{dir}').mkdir(exist_ok=True, parents=True)
