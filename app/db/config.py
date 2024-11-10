from pathlib import Path
from dotenv import dotenv_values


class DbConfig():
    def __init__(self):
        config = dotenv_values(dotenv_path="_db.env")

        if config["IS_LOCAL"] == 'true':
            self.db_user = 'postgres'
            self.db_name = 'postgres'
            self.db_pass = 'postgres'
            self.db_host = 'localhost'
        else:
            self.db_user = config["DB_USER"]
            self.db_name = config["DB_NAME"]
            self.db_pass = config["DB_PASS"]
            self.db_host = config["DB_HOST"]

        self.db_connection_string = f"postgresql+psycopg2://{self.db_user}:{self.db_pass}@{self.db_host}:5432/{self.db_name}"
