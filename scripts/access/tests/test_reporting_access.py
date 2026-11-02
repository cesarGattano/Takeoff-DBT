import io

import pytest
from psycopg2 import errors, sql
from psycopg2.extensions import connection

REPORTER_ALLOWED_TABLES = [
    "dim_canal",
    "dim_date",
    "dim_produit",
    "dim_statut_commande",
    "fact_commandes",
    "fact_visites",
    "fact_retours",
]
REPORTER_DIM_CLIENT_ALLOWED_COLS = [
    "client_id",
    "ville",
    "code_postal",
    "pays",
    "segment",
    "date_inscription",
    "actif",
]
REPORTER_DIM_CLIENT_DENIED_COLS = [
    "nom",
    "prenom",
    "nom_complet",
    "email",
    "date_naissance",
    "age",
]
REPORTER_DENIED_TABLES = [
    "raw_clients",
    "raw_produits",
    "raw_commandes",
    "raw_lignes_commande",
    "raw_visites",
    "raw_retours",
    "stg_clients",
    "stg_produits",
    "stg_commandes",
    "stg_lignes_commande",
    "stg_visites",
    "stg_retours",
]

# Target: fact_commandes where SELECT is granted
# Security tip: WHERE false = 0 lines touched even with bad configuration.
DENIED_STATEMENTS = {
    "insert": "INSERT INTO public.fact_commandes SELECT * FROM public.fact_commandes WHERE false",
    "update": "UPDATE public.fact_commandes SET montant_total = montant_total WHERE false",
    "delete": "DELETE FROM public.fact_commandes WHERE false",
    "truncate": "TRUNCATE public.fact_commandes",
    "alter": "ALTER TABLE public.fact_commandes ADD COLUMN test_col int",
    "drop": "DROP TABLE public.fact_commandes",
    "create_table": "CREATE TABLE public.test_reporting (id int)",
    "create_schema": "CREATE SCHEMA test_reporting",
    "copy_to_file": "COPY public.fact_commandes TO '/tmp/fact_commandes.csv'",
    "copy_to_program": "COPY public.fact_commandes TO PROGRAM 'id'",
    "copy_from_file": "COPY public.fact_commandes FROM '/tmp/fact_commandes.csv'",
    "read_server_file": "SELECT pg_read_file('/etc/passwd')",
    "set_role_admin": "SET ROLE postgres",
}


def assert_denied(conn: connection, query):
    """Explicit assertion that a query is denied for the reporter
    role. Raises an error if the query succeeds.

    conn (connection): A psycopg2 connection object.
    query (str | sql.Composable): The SQL query to execute."""
    with conn.cursor() as cur:
        with pytest.raises(errors.InsufficientPrivilege):
            cur.execute(query)


@pytest.mark.parametrize("table", REPORTER_ALLOWED_TABLES)
def test_select_allowed_tables(reporter_conn: connection, table: str):
    """Test SELECT on the allowed columns for reporter.

    Args:
        reporter_conn (connection): A psycopg2 connection object for the reporter role.
        table (str): The name of the table to query.
    """
    query = sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier("public", table))
    with reporter_conn.cursor() as cur:
        cur.execute(query)
        res = cur.fetchone()
        assert res is not None, f"Query returned no results for table {table}"
        assert res[0] >= 0


def test_select_dim_client_allowed_columns(reporter_conn: connection):
    """Test SELECT on the allowed columns for reporter in dim_client.

    Args:
        reporter_conn (connection): A psycopg2 connection object for the reporter role.
    """
    query = sql.SQL("SELECT {} FROM public.dim_client").format(
        sql.SQL(", ").join(map(sql.Identifier, REPORTER_DIM_CLIENT_ALLOWED_COLS))
    )
    with reporter_conn.cursor() as cur:
        cur.execute(query)


def test_join_facts_with_dim_client(reporter_conn: connection):
    """Test JOIN between fact_commandes and dim_client for reporter.

    Args:
        reporter_conn (connection): A psycopg2 connection object for the reporter role.
    """
    with reporter_conn.cursor() as cur:
        cur.execute("""
            SELECT f.commande_id, c.segment, c.ville
            FROM public.fact_commandes f
            JOIN public.dim_client c USING (client_id)
        """)


def test_copy_to_stdout_allowed_on_readable_table(reporter_conn: connection):
    """Test COPY to stdout from fact_commandes for reporter.

    Args:
        reporter_conn (connection): A psycopg2 connection object for the reporter role.
    """
    with reporter_conn.cursor() as cur:
        # Tip: copy_expert = to submit a COPY table FROM STDIN / COPY table TO STDOUT
        cur.copy_expert("COPY public.fact_commandes TO STDOUT", io.StringIO())


@pytest.mark.parametrize("col", REPORTER_DIM_CLIENT_DENIED_COLS)
def test_select_dim_client_denied_columns(reporter_conn: connection, col: str):
    """Test SELECT on the denied columns for reporter in dim_client.

    Args:
        reporter_conn (connection): A psycopg2 connection object for the reporter role.
        col (str): The name of the column to query.
    """
    assert_denied(
        reporter_conn,
        sql.SQL("SELECT {} FROM public.dim_client").format(sql.Identifier(col)),
    )


def test_select_star_dim_client_denied(reporter_conn: connection):
    """Test SELECT * in dim_clietn for reporter.

    Args:
        reporter_conn (connection): A psycopg2 connection object for the reporter role.
    """
    assert_denied(reporter_conn, "SELECT * FROM public.dim_client")


@pytest.mark.parametrize("table", REPORTER_DENIED_TABLES)
def test_select_denied_tables(reporter_conn: connection, table: str):
    """Test SELECT in denied tables for reporter.

    Args:
        reporter_conn (connection): A psycopg2 connection object for the reporter role.
        table (str): The name of the table to query.
    """
    assert_denied(
        reporter_conn,
        sql.SQL("SELECT * FROM {}").format(sql.Identifier("public", table)),
    )


@pytest.mark.parametrize(
    "query", DENIED_STATEMENTS.values(), ids=DENIED_STATEMENTS.keys()
)
def test_all_denied_statements(reporter_conn: connection, query: str):
    """Test multiple statement denied for reporter.

    Args:
        reporter_conn (connection): A psycopg2 connection object for the reporter role.
        query (str): The SQL query to test.
    """
    assert_denied(reporter_conn, query)


# Test de niveau supérieur


def test_deny_by_default_read(admin_conn: connection, reporter_name: str):
    """Test that the reporter role can only SELECT the whitelisted tables
    at the table level. Cover all non-system schemas (e.g. also monitoring).

    Args:
        admin_conn (connection): A psycopg2 connection object for the superuser.
        reporter_name (str): The name of the reporter role.
    """
    with admin_conn.cursor() as cur:
        # pg_class -> infos sur les objets relationnels (tables, vues, etc...)
        # pg_namespace -> infos sur les schémas
        # pg_class.relkind: r = table, v = view, m = materialized view, p = partitioned table
        cur.execute(
            """
            SELECT n.nspname || '.' || c.relname
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind IN ('r', 'v', 'm', 'p')
              AND n.nspname NOT IN ('pg_catalog', 'information_schema')
              AND n.nspname NOT LIKE 'pg\\_toast%%'
              AND has_table_privilege(%s::name, c.oid, 'SELECT')
        """,
            (reporter_name,),
        )
        readable = {row[0] for row in cur.fetchall()}
    assert readable == {f"public.{t}" for t in REPORTER_ALLOWED_TABLES}


def test_no_write_privilege_anywhere(admin_conn: connection, reporter_name: str):
    """Test that the reporter role has no write privileges on any tables
    at the table level. Cover all non-system schemas (e.g. also monitoring).

    Args:
        admin_conn (connection): A psycopg2 connection object for the superuser.
        reporter_name (str): The name of the reporter role.
    """
    with admin_conn.cursor() as cur:
        cur.execute(
            """
            SELECT n.nspname || '.' || c.relname, p
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            CROSS JOIN unnest(ARRAY['INSERT','UPDATE','DELETE','TRUNCATE',
                                    'REFERENCES','TRIGGER']) AS p
            WHERE c.relkind IN ('r', 'v', 'm', 'p')
              AND n.nspname NOT IN ('pg_catalog', 'information_schema')
              AND n.nspname NOT LIKE 'pg\\_toast%%'
              AND has_table_privilege(%s::name, c.oid, p)
        """,
            (reporter_name,),
        )
        assert cur.fetchall() == []


def test_role_attributes(admin_conn: connection, reporter_name: str):
    """Test the reporter role attributes.

    Args:
        admin_conn (connection): A psycopg2 connection object for the superuser.
        reporter_name (str): The name of the reporter role."""
    with admin_conn.cursor() as cur:
        cur.execute(
            """
            SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication,
                   rolbypassrls, rolcanlogin, rolconnlimit
            FROM pg_roles WHERE rolname = %s
        """,
            (reporter_name,),
        )
        row = cur.fetchone()
    assert row == (False, False, False, False, False, True, 5)


def test_group_role_cannot_login(admin_conn: connection, reporting_group_name: str):
    """Test that the reporting group role cannot login.

    Args:
        admin_conn (connection): A psycopg2 connection object for the superuser.
        reporting_group_name (str): The name of the reporting group.
    """
    with admin_conn.cursor() as cur:
        cur.execute(
            "SELECT rolcanlogin FROM pg_roles WHERE rolname = %s",
            (reporting_group_name,),
        )
        assert cur.fetchone() == (False,)


def test_only_member_of_reporting(admin_conn: connection, reporter_name: str):
    """Test that the reporter role is only a member of the reporting group.

    Args:
        admin_conn (connection): A psycopg2 connection object for the superuser.
        reporter_name (str): The name of the reporter role.
    """
    with admin_conn.cursor() as cur:
        cur.execute(
            """
            SELECT r.rolname
            FROM pg_auth_members m
            JOIN pg_roles r ON r.oid = m.roleid
            JOIN pg_roles u ON u.oid = m.member
            WHERE u.rolname = %s
        """,
            (reporter_name,),
        )
        assert {row[0] for row in cur.fetchall()} == {"reporting"}
