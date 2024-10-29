from dotenv import dotenv_values
from pathlib import Path

class AppConfig():
    def __init__(self):
        self.workspace_dir = 'workspace'
        self.dirs = ['border_input', 'cartoonize_input','lift_input','rm_background_input','tab_input' ]
        self.init_dirs()

    def init_dirs(self):
        for dir in self.dirs:
            Path(f'{self.workspace_dir}/{dir}').mkdir(exist_ok=True,parents=True)
