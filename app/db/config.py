from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.sql import text
import pg8000
from dotenv import dotenv_values


class DbConfig():
    def __init__(self):
        config = dotenv_values(dotenv_path="_db.env")
        self.is_local = config["IS_LOCAL"]
        if self.is_local == 'true':
            breakpoint()
            self.db_user = 'postgres'
            self.db_name = 'postgres'
            self.db_pass = 'postgres'
            self.db_host = 'localhost'
            self.db_connection_string = f"postgresql+psycopg2://{self.db_user}:{self.db_pass}@{self.db_host}:5432/{self.db_name}"
            self.engine = create_engine(self.db_connection_string)
        else:
            self.db_user = config["DB_USER"]
            self.db_name = config["DB_NAME"]
            self.db_pass = config["DB_PASS"]
            self.instance_connection_name = config["INSTANCE_CONNECTION_NAME"]
            self.engine, self.connector = self.cloud_sql_connect_with_connector()



    def cloud_sql_connect_with_connector(self) -> Engine:
        """
        Initializes a connection pool for a Cloud SQL instance of Postgres.

        Uses the Cloud SQL Python Connector package.
        """

        # initialize Cloud SQL Python Connector object
        connector = Connector(refresh_strategy="lazy")

        def getconn() -> pg8000.dbapi.Connection:
            conn: pg8000.dbapi.Connection = connector.connect(
                self.instance_connection_name,
                "pg8000",
                user=self.db_user,
                password=self.db_pass,
                db=self.db_name,
            )
            return conn

        pool = create_engine(
            "postgresql+pg8000://",
            creator=getconn,
        )
        return pool, connector


