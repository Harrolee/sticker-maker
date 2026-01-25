from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import bcrypt
import os

class DbClient():
    def __init__(self):
        self.is_local = os.environ.get('IS_LOCAL', 'false').lower() == 'true'
        self._setup_connection()
        self.queries = self.Queries()

    def _setup_connection(self):
        if self.is_local:
            print("Setting up local database connection...")
            self.db_user = 'postgres'
            self.db_name = 'postgres'
            self.db_pass = 'postgres'
            self.db_host = 'db' if os.environ.get('DOCKER_ENV') else 'localhost'
            self.engine = create_engine(
                f"postgresql+psycopg2://{self.db_user}:{self.db_pass}@{self.db_host}:5432/{self.db_name}"
            )
            print("Local database connection established")
        else:
            print("Setting up Neon database connection...")
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                raise ValueError("DATABASE_URL environment variable is required for production")
            self.engine = create_engine(database_url)
            print("Neon database connection established")

    def close(self):
        pass  # Connection pooling handled by SQLAlchemy

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    class Queries():
        def create_user(self, name, email):
            return text(
                """
                INSERT INTO users (name, email, credits)
                VALUES (:name, :email, 0)
                RETURNING user_id
                """
            ).bindparams(name=name, email=email)

        def save_sticker(self, storefront_product_id, sticker_name, creator_id):
            return text(
                """
                INSERT INTO stickers (storefront_product_id, name, sales, creator)
                VALUES (:product_id, :name, 0, :creator_id)
                """
            ).bindparams(
                product_id=storefront_product_id,
                name=sticker_name,
                creator_id=creator_id
            )

    def db_connection(self):
        with self.engine.connect() as conn:
            stmt = text("select * from postgres")
            print(conn.execute(stmt).fetchall())

    def get_user_by_username(self, username):
        """Get a user by username from the database"""
        from fastapp.db.models import User
        try:
            with Session(self.engine) as session:
                user = session.query(User).filter(User.username == username).first()
                if user:
                    return {
                        'user_id': user.user_id,
                        'username': user.username,
                        'password_hash': user.password_hash,
                        'name': user.name,
                        'email': user.email
                    }
                return None
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None

    def get_user_by_auth0_id(self, auth0_id: str):
        """Get a user by their Auth0 ID (sub field)"""
        from fastapp.db.models import User
        try:
            with Session(self.engine) as session:
                user = session.query(User).filter(User.auth0_id == auth0_id).first()
                if user:
                    return {
                        'user_id': user.user_id,
                        'username': user.username,
                        'name': user.name,
                        'email': user.email,
                        'auth0_id': user.auth0_id
                    }
                return None
        except Exception as e:
            print(f"Error getting user by Auth0 ID: {e}")
            return None

    def get_or_create_auth0_user(self, auth0_id: str, email: str, name: str = None):
        """Get or create a user based on Auth0 authentication.

        If a user with the given auth0_id exists, return them.
        If not, create a new user with the Auth0 info.

        Args:
            auth0_id: The Auth0 'sub' field (unique identifier)
            email: The user's email from Auth0
            name: The user's name from Auth0 (optional)

        Returns:
            dict with user info or None on error
        """
        from fastapp.db.models import User
        try:
            with Session(self.engine) as session:
                # First check if user exists by auth0_id
                user = session.query(User).filter(User.auth0_id == auth0_id).first()
                if user:
                    return {
                        'user_id': user.user_id,
                        'username': user.username,
                        'name': user.name,
                        'email': user.email,
                        'auth0_id': user.auth0_id
                    }

                # Check if user exists by email (might have registered via other method)
                user = session.query(User).filter(User.email == email).first()
                if user:
                    # Link the Auth0 ID to the existing user
                    user.auth0_id = auth0_id
                    if name and not user.name:
                        user.name = name
                    session.commit()
                    return {
                        'user_id': user.user_id,
                        'username': user.username,
                        'name': user.name,
                        'email': user.email,
                        'auth0_id': user.auth0_id
                    }

                # Create new user
                display_name = name or email.split('@')[0]
                new_user = User(
                    username=None,  # Auth0 users don't have a username initially
                    password_hash=None,  # Auth0 users don't have a local password
                    name=display_name,
                    email=email,
                    auth0_id=auth0_id
                )
                session.add(new_user)
                session.commit()
                print(f"Created new Auth0 user: {email}")
                return {
                    'user_id': new_user.user_id,
                    'username': new_user.username,
                    'name': new_user.name,
                    'email': new_user.email,
                    'auth0_id': new_user.auth0_id
                }
        except Exception as e:
            print(f"Error getting/creating Auth0 user: {e}")
            return None

    def create_user(self, username, password):
        """Create a new user in the database with hashed password"""
        from fastapp.db.models import User
        try:
            # Hash the password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            with Session(self.engine) as session:
                new_user = User(
                    username=username,
                    password_hash=password_hash,
                    name=username,  # Use username as name for now
                    email=f"{username}@placeholder.local"  # Placeholder email
                )
                session.add(new_user)
                session.commit()
                print(f"Created user: {username}")
                return {
                    'user_id': new_user.user_id,
                    'username': new_user.username
                }
        except Exception as e:
            print(f"Error creating user: {e}")
            return None

    def verify_password(self, username, password):
        """Verify a user's password"""
        user = self.get_user_by_username(username)
        if not user or not user.get('password_hash'):
            return False
        return bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8'))

    def all_users(self) -> int | None:
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT * FROM users"))
                results = result.all()
            return results
        except Exception as e:
                    print(f"Error getting users: {e}")

    def find_user_by_email(self, email) -> tuple | None:
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT user_id, name FROM users WHERE email = :email"), {"email": email})
                print("about to unpack")
                user_id, name = result.first()
            return user_id, name
        except Exception as e:
                    print(f"Error getting user info: {e}")

    def save_sticker(self, storefront_product_id, sticker_name, creator_id):
        try:
            with self.engine.connect() as conn:
                with conn.begin():
                    conn.execute(self.queries.save_sticker(storefront_product_id, sticker_name, creator_id))
        except Exception as e:
                    print(f"Error saving sticker: {e}")

if __name__ == "__main__":
    with DbClient() as client:
        # client.create_user('dojacat', 'd@kitty.com')
        print(client.all_users())
