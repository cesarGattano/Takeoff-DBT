import os
import psycopg2
import time
from dotenv import load_dotenv
from dataclasses import dataclass

# Load environment variables from .env file
load_dotenv()


# A class with __init__, __repr__, and __eq__ methods automatically generated
@dataclass
class LatencyResult:
    table: str
    """Database table name"""
    duration_ms: float
    """Duration of the request in milliseconds"""
    row_count: int
    """Number of rows returned by the query"""
    success: bool
    """Indicates if the query was successful"""
    error: str | None = None
    """Error message if the query failed, None otherwise"""


# Simple requests to check the health of the database and the fact tables
FACT_TABLE_QUERIES = {
    "fact_commandes": "SELECT commande_id FROM fact_commandes "
    "ORDER BY commande_id DESC LIMIT 100;",
    "fact_visites": "SELECT visite_id FROM fact_visites "
    "ORDER BY visite_id DESC LIMIT 100;",
}
# Note: "SELECT *" potentially biases the metric of the latency if the amount
# of data is too large. It is better to select a specific column and limit the
# number of rows.


# Service level indicators (SLI) functions
# -----
def check_db_health(dsn: str, timeout: int = 3) -> bool:
    """Check the postgreSQL database connection via psycopg2.

    Args:
        dsn (str): The database connection string.
            Example: "dbname=test user=postgres password=secret host=localhost port=5432"
        timeout (int, optional): The connection timeout in seconds. Defaults to 3.

    Returns:
        bool: True if the database is healthy, False otherwise.
    """
    try:
        conn = psycopg2.connect(dsn, connect_timeout=timeout)
        conn.close()
        return True
    except psycopg2.OperationalError:
        return False


def measure_query_latency(
    dsn: str, table: str, query: str, timeout: int = 3
) -> LatencyResult:
    """Check a **query** latency for a given **table** via psycopg2
    and time.

    Args:
        dsn (str): The database connection string.
            Example: "dbname=test user=postgres password=secret host=localhost port=5432"
        table (str): The name of the table to query.
        query (str): The SQL query to execute.
        timeout (int, optional): The timeout for the query in seconds. Defaults to 3.

    Returns:
        LatencyResult: Results of the query latency measurement.
    """
    try:
        conn = psycopg2.connect(dsn, connect_timeout=timeout)
        conn.set_session(readonly=True, autocommit=True)
        # Will never leave a transaction open and will never write to the database.
        # Important because we are measuring latency and not modifying the database.
        cur = conn.cursor()

        start = time.perf_counter()
        cur.execute(query)
        rows = cur.fetchall()
        duration_ms = (time.perf_counter() - start) * 1000
        # 1) fetchall is included in the latency measurement in order
        # to have the SLI metric closer to the real user experience.
        # 2) perf_counter is used instead of time.time() because it has a higher
        # resolution and is not affected by system clock updates.

        cur.close()
        conn.close()
        return LatencyResult(
            table=table, duration_ms=duration_ms, row_count=len(rows), success=True
        )

    except psycopg2.Error as e:
        return LatencyResult(
            table=table, duration_ms=-1, row_count=0, success=False, error=str(e)
        )


def collect_all_latencies(dsn: str) -> list[LatencyResult]:
    """Collect the latency of all fact tables via psycopg2.

    Args:
        dsn (str): The database connection string.
            Example: "dbname=test user=postgres password=secret host=localhost port=5432"

    Returns:
        list[LatencyResult]: A list of LatencyResult objects for each fact table query.
    """
    return [
        measure_query_latency(dsn, table, query)
        for table, query in FACT_TABLE_QUERIES.items()
    ]


# Storing measurments in database
# -----
def write_measurement(
    dsn: str,
    sli_name: str,
    value: float | bool,
    success: bool,
    error: str | None = None,
):
    """Write a measurement to the monitoring database.

    Args:
        dsn (str): The database connection string.
            Example: "dbname=test user=postgres password=secret host=localhost port=5432"
        sli_name (str): The name of the service level indicator.
        value (float | bool): The value of the SLI measurement.
        success (bool): Whether the measurement was successful.
        error (str | None, optional): The error message if the measurement failed.
            Defaults to None.
    """
    conn = psycopg2.connect(dsn)
    conn.set_session(readonly=False, autocommit=True)
    cur = conn.cursor()
    cur.execute(f"""
        INSERT INTO sli_measurements (sli_name, value_numeric, value_boolean, success, error_message)
        VALUES (
            '{sli_name}',
            {value if isinstance(value, float) else 'NULL'},
            {value if isinstance(value, bool) else 'NULL'},
            {success},
            '{error}')
        """)
    cur.close()
    conn.close()


if __name__ == "__main__":
    # Load database connection strings from environment variables
    try:
        dsn_dw = (
            f"dbname={os.environ['POSTGRES_DB']} "
            f"user={os.environ['POSTGRES_USER']} "
            f"password={os.environ['POSTGRES_PASSWORD']} "
            f"host=localhost port={os.environ['LOCAL_DB_PORT']}"
        )
        dsn_monitoring = (
            f"dbname={os.environ['MONITORING_DB']} "
            f"user={os.environ['MONITORING_USER']} "
            f"password={os.environ['MONITORING_PASSWORD']} "
            f"host=localhost port={os.environ['LOCAL_DB_PORT']}"
        )
    except KeyError as e:
        print(f"Environment variable {e} not set. Please check your .env file.")
        exit(1)

    # Loop of monitoring checks
    try:
        iter = 0
        while True:
            if check_db_health(dsn_dw):
                print("Database is healthy.")
                write_measurement(dsn_monitoring, "db_health", True, True)
            else:
                print("Database is down!")
                write_measurement(
                    dsn_monitoring,
                    "db_health",
                    False,
                    False,
                    "Database connection failed.",
                )

            latencies = collect_all_latencies(dsn_dw)
            for latency in latencies:
                if latency.success:
                    print(
                        f"Table: {latency.table}, Duration: {latency.duration_ms:.2f} ms, "
                        f"Row count: {latency.row_count}"
                    )
                    write_measurement(
                        dsn_monitoring,
                        f"{latency.table}_latency",
                        latency.duration_ms,
                        True,
                    )
                else:
                    print(
                        f"Table: {latency.table}, Query failed with error: {latency.error}"
                    )
                    write_measurement(
                        dsn_monitoring,
                        f"{latency.table}_latency",
                        latency.duration_ms,
                        False,
                        latency.error,
                    )

            print(f"Monitoring cycle {iter} complete. Waiting for the next cycle...")
            time.sleep(60)  # Check every 60 seconds
            iter += 1
    except KeyboardInterrupt:
        print("Monitoring stopped by user.")
    except Exception as e:
        print(f"An error occurred: {e}")


# Pour aller plus loin:
# 1) Mise en place d'une architecture "collecteur" et "visualiseur" pour la
#   surveillance de la base de données. Solution open-source: Prometheus + Grafana.
#   Prometheus à mettre en place dans ce script pour la partie collecteur.