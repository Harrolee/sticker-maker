### Run Migrations

#### Prerequisites
- Python 3.9+
- Database connection details (either local or GCP Cloud SQL)
- Required environment variables:
  ```
  DB_USER=your_db_user
  DB_PASS=your_db_password
  DB_NAME=your_db_name
  INSTANCE_CONNECTION_NAME=project:region:instance  # Only for GCP Cloud SQL
  ```

#### Local Development
1. Install dependencies:
   ```bash
   pip install alembic sqlalchemy psycopg2-binary
   ```

2. Navigate to the database directory:
   ```bash
   cd fastapp/db
   ```

3. Run migrations:
   ```bash
   alembic upgrade head
   ```

#### GCP Cloud SQL
1. Install dependencies:
   ```bash
   pip install alembic sqlalchemy cloud-sql-python-connector pg8000
   ```

2. Set up Cloud SQL Auth Proxy (recommended for secure access):
   ```bash
   # Download and install Cloud SQL Auth Proxy
   curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.1/cloud-sql-proxy.linux.amd64
   chmod +x cloud-sql-proxy

   # Start the proxy
   ./cloud-sql-proxy INSTANCE_CONNECTION_NAME

   # ./cloud-sql-proxy sticker-maker-439910:us-central1:sticker-maker-db
   ```

3. Navigate to the database directory:
   ```bash
   cd fastapp/db
   ```

4. Run migrations:
   ```bash
   alembic upgrade head
   ```

#### Creating New Migrations
1. Make changes to the models in `fastapp/db/models.py`
2. Generate a new migration:
   ```bash
   alembic revision --autogenerate -m "Description of changes"
   ```
3. Review the generated migration in `fastapp/db/migrations/versions/`
4. Apply the migration using `alembic upgrade head`

#### Rolling Back Migrations
To revert the most recent migration:
```bash
alembic downgrade -1
```


#### To revert to a specific migration:
```bash
alembic downgrade <migration_id>
```