from pathlib import Path
from dotenv import dotenv_values


class DbConfig():
    def __init__(self):
        config = dotenv_values(dotenv_path="_db.env")

        # db
        self.db_user = config["DB_USER"]
        self.db_name = config["DB_NAME"]
        self.db_pass = config["DB_PASS"]
        self.db_connection_string = f"postgresql+psycopg2://{self.db_user}:{self.db_pass}@localhost:5432/{self.db_name}"
