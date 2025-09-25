# from logging.config import fileConfig

# from sqlalchemy import engine_from_config
# from sqlalchemy import pool

# from alembic import context
# from src.app.core.db.database import Base
# # Also ensure your new model is imported so Base can see it
# from src.app.models.call_logs import CallLog

# import os
# from dotenv import load_dotenv
# load_dotenv()
# config.set_main_option('sqlalchemy.url', os.getenv('POSTGRES_URI'))

# # this is the Alembic Config object, which provides
# # access to the values within the .ini file in use.
# config = context.config

# # Interpret the config file for Python logging.
# # This line sets up loggers basically.
# if config.config_file_name is not None:
#     fileConfig(config.config_file_name)

# # add your model's MetaData object here
# # for 'autogenerate' support
# # from myapp import mymodel
# # target_metadata = mymodel.Base.metadata
# target_metadata = Base.metadata

# # other values from the config, defined by the needs of env.py,
# # can be acquired:
# # my_important_option = config.get_main_option("my_important_option")
# # ... etc.


# def run_migrations_offline() -> None:
#     """Run migrations in 'offline' mode.

#     This configures the context with just a URL
#     and not an Engine, though an Engine is acceptable
#     here as well.  By skipping the Engine creation
#     we don't even need a DBAPI to be available.

#     Calls to context.execute() here emit the given string to the
#     script output.

#     """
#     url = config.get_main_option("sqlalchemy.url")
#     context.configure(
#         url=url,
#         target_metadata=target_metadata,
#         literal_binds=True,
#         dialect_opts={"paramstyle": "named"},
#     )

#     with context.begin_transaction():
#         context.run_migrations()


# def run_migrations_online() -> None:
#     """Run migrations in 'online' mode.

#     In this scenario we need to create an Engine
#     and associate a connection with the context.

#     """
#     connectable = engine_from_config(
#         config.get_section(config.config_ini_section, {}),
#         prefix="sqlalchemy.",
#         poolclass=pool.NullPool,
#     )

#     with connectable.connect() as connection:
#         context.configure(
#             connection=connection, target_metadata=target_metadata
#         )

#         with context.begin_transaction():
#             context.run_migrations()


# if context.is_offline_mode():
#     run_migrations_offline()
# else:
#     run_migrations_online()

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from dotenv import load_dotenv
import src.app.models as models


from alembic import context

# --- Fix for module import errors ---
# Add the 'src' directory to the Python path
# This ensures that Alembic can find your application's modules, like 'app.core.db.database'
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# --- Load Environment Variables ---
# Load variables from the .env file in your src directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'src', '.env'))

# --- Alembic Config object ---
# This provides access to the values within the .ini file in use.
config = context.config

# --- Set the database URL from environment variables ---
# This is the crucial step to ensure Alembic connects to the correct database
# It overrides the sqlalchemy.url from your alembic.ini file
postgres_uri = os.getenv('POSTGRES_URI')
if postgres_uri:
    config.set_main_option('sqlalchemy.url', postgres_uri)
else:
    raise ValueError("POSTGRES_URI is not set in the environment or .env file.")

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Import all your models here ---
# This is how autogenerate discovers your tables.
# For autogenerate to work, Base.metadata must be populated with all your table models.
from src.app.core.db.database import Base
from src.app.models.user import User  # Import other models
from src.app.models.agent_profile import AgentProfile # Import other models
from src.app.models.connections import Connection # Import other models
from src.app.models.call_logs import CallLog # Your new model is here

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
