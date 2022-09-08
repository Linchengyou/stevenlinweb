import pathlib
import json
from config import app_config_path


class Config:
    def __init__(self):
        self.config_file_path = app_config_path  # config檔路徑
        self.config_file = pathlib.Path(self.config_file_path)  # config檔路徑物件
        self.config = None

    def get_config(self):
        if self.config_file.is_file():
            self.config = json.loads(self.config_file.read_text(encoding='utf-8'), encoding='utf-8')
            return self.config

    def update_config(self, config):
        with open(self.config_file_path, 'w') as f:
            json.dump(config, f, indent=2)
