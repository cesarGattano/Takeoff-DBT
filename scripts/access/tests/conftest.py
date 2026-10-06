import os

import psycopg2
import pytest
from dotenv import load_dotenv
from collections.abc import Generator

load_dotenv()  # remonte l'arborescence jusqu'au .env


def connect(
    user: str, password: str, dbname: str | None = None
) -> psycopg2.extensions.connection:
    """Connects to a database **dbname** (if provided) using
    the provided **user** and **password**. If **dbname** is
    not provided, it defaults to the value of the environment
    variable POSTGRES_DB.

    Args:
        user (str): The username for the database connection.
        password (str): The password for the database connection.
        dbname (str | None, optional): The name of the database to connect to. Defaults to None.

    Returns:
        psycopg2.extensions.connection: A database connection object.
    """
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.environ["LOCAL_DB_PORT"],
        dbname=dbname or os.environ["POSTGRES_DB"],
        user=user,
        password=password,
        connect_timeout=5,
    )


@pytest.fixture(scope="session")
def reporter_name() -> str:
    """Name of a reporting user from the environment variables.

    Returns:
        str: The reporting user's name."""
    return os.environ["REPORTING_USER"]


@pytest.fixture(scope="session")
def reporting_group_name() -> str:
    """Name of a reporting group from the environment variables.

    Returns:
        str: The reporting group's name."""
    return os.environ["REPORTING_GROUP"]


@pytest.fixture(scope="session")
def admin_conn() -> Generator[psycopg2.extensions.connection, None, None]:
    """Superuser connection.

    Yields:
        Generator[psycopg2.extensions.connection, None, None]:
            A generator yielding a superuser database connection object.
    """
    conn = connect(os.environ["POSTGRES_USER"], os.environ["POSTGRES_PASSWORD"])
    yield conn
    conn.close()


@pytest.fixture
def reporter_conn(
    reporter_name,
) -> Generator[psycopg2.extensions.connection, None, None]:
    """Reporting user connection. Systematic rollback: if a test
    succeeds by error in writing, nothing would be validated.

    Yields:
        Generator[psycopg2.extensions.connection, None, None]:
            A generator yielding a reporter connection object."""
    conn = connect(reporter_name, os.environ["REPORTING_PASSWORD"])
    yield conn
    conn.rollback()
    conn.close()
