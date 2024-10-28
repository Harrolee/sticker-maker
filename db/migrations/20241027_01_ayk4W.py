from yoyo import step

# SQL for creating tables
create_user_table = """
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    credits INTEGER DEFAULT 0
);
"""

create_sticker_table = """
CREATE TABLE stickers (
    sticker_id SERIAL PRIMARY KEY,
    gumroad_product_id VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    sales INTEGER DEFAULT 0,
    creator INTEGER NOT NULL,
    FOREIGN KEY (creator) REFERENCES users(user_id)
);
"""

create_collection_table = """
CREATE TABLE collections (
    collection_id SERIAL PRIMARY KEY,
    gumroad_product_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    sticker_ids INTEGER[] NOT NULL,
    sales INTEGER DEFAULT 0,
    creator INTEGER NOT NULL,
    FOREIGN KEY (creator) REFERENCES users(user_id)
);
"""

# SQL for dropping tables
drop_user_table = "DROP TABLE IF EXISTS user;"
drop_sticker_table = "DROP TABLE IF EXISTS sticker;"
drop_collection_table = "DROP TABLE IF EXISTS collection;"

# Define migration steps
steps = [
    step(create_user_table, drop_user_table),
    step(create_sticker_table, drop_sticker_table),
    step(create_collection_table, drop_collection_table),
]
