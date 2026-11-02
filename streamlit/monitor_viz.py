import streamlit as st
import psycopg2
import os
import pandas as pd


def get_recent_healthchecks(dsn: str, sli_name: str, limit: int = 20) -> list[bool]:
    """Retrieve the recent healthcheck results for a given SLI from the database.

    Args:
        dsn (str): The database connection string.
            Example: "dbname=test user=postgres password=secret host=localhost port=5432"
        sli_name (str): The name of the service level indicator.
        limit (int, optional): The number of recent healthcheck results to retrieve.
            Defaults to 20.
    Returns:
        list[bool]: A list of boolean values representing the recent healthcheck results.
            True indicates a successful healthcheck, while False indicates a failed healthcheck.
    """
    query = """
        SELECT success
        FROM sli_measurements
        WHERE sli_name = %s
        ORDER BY measured_at DESC
        LIMIT %s;
    """
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute(query, (sli_name, limit))
    results = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return results


@st.fragment(run_every="60s")
def render_db_health(dsn: str, sli_name: str, limit: int = 20):
    """Display the health status of a given SLI in a Streamlit app.

    Args:
        dsn (str): The database connection string.
            Example: "dbname=test user=postgres password=secret host=localhost port=5432"
        sli_name (str): The name of the service level indicator.
        limit (int, optional): The number of recent healthcheck results to display.
            Defaults to 20.
    """
    recent_checks = get_recent_healthchecks(dsn, sli_name, limit)
    current = recent_checks[-1] if recent_checks else False
    uptime_pct = 100 * sum(recent_checks) / len(recent_checks) if recent_checks else 0

    col1, col2 = st.columns([1, 3])
    with col1:
        if current:
            st.success("🟢 UP")
        else:
            st.error("🔴 DOWN")
    with col2:
        st.metric("Disponibilité (dernières mesures)", f"{uptime_pct:.1f}%")


def get_latency_percentiles(dsn: str, sli_name: str, window: str = "1 hour") -> dict:
    """Retrieves the latency percentiles for a given SLI from the database and
    for a given time window ending now().

    Args:
        dsn (str): The database connection string.
            Example: "dbname=test user=postgres password=secret host=localhost port=5432"
        sli_name (str): The name of the service level indicator.
        window (str, optional): Time window for calculating percentiles. Defaults to "1 hour".

    Returns:
        dict: A dictionary containing the 50th, 95th, and 99th percentiles of latency measurements,
            as well as the number of measurements in the specified time window.
            Example: {"p50": 120.5, "p95": 250.0, "p99": 400.0, "n": 100}
    """
    # Use native function of postgres to calculate percentiles directly in the database for efficiency
    # percentile_cont is a continuous percentile function that interpolates between values if necessary
    # percentile_disc is a discrete percentile function that returns the nearest value in the dataset
    query = """
        SELECT
            percentile_cont(0.50) WITHIN GROUP (ORDER BY value_numeric) AS p50,
            percentile_cont(0.95) WITHIN GROUP (ORDER BY value_numeric) AS p95,
            percentile_cont(0.99) WITHIN GROUP (ORDER BY value_numeric) AS p99,
            count(*) AS nb_mesures
        FROM sli_measurements
        WHERE sli_name = %s
          AND measured_at >= now() - %s::interval
          AND success = true;
    """
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute(query, (sli_name, window))
    res = cur.fetchone()
    p50, p95, p99, n = res if res else (None, None, None, 0)
    cur.close()
    conn.close()
    return {"p50": p50, "p95": p95, "p99": p99, "n": n}


@st.fragment(run_every="300s")
def render_latency_sli(dsn: str, sli_name: str, label: str):
    """Display the latency percentiles for a given SLI in a Streamlit app.

    Args:
        dsn (str): The database connection string.
            Example: "dbname=test user=postgres password=secret host=localhost port=5432"
        sli_name (str): The name of the service level indicator.
        label (str): The label for the latency metrics.
    """
    stats = get_latency_percentiles(dsn, sli_name)
    col1, col2, col3 = st.columns(3)
    col1.metric(f"{label} — p50", f"{stats['p50']:.1f} ms" if stats["p50"] else "N/A")
    col2.metric(f"{label} — p95", f"{stats['p95']:.1f} ms" if stats["p95"] else "N/A")
    col3.metric(f"{label} — p99", f"{stats['p99']:.1f} ms" if stats["p99"] else "N/A")
    st.caption(f"Basé sur {stats['n']} mesures (dernière heure)")


def get_latency_timeseries(
    dsn: str, sli_name: str, window: str = "1 hour"
) -> pd.DataFrame:
    """
    Retrieve latency timeseries data for a given SLI from the database and
    for a given time window ending now().

    Args:
        dsn (str): The database connection string.
            Example: "dbname=test user=postgres password=secret host=localhost port=5432"
        sli_name (str): The name of the service level indicator.
        window (str, optional): The time window for the timeseries data.
            Defaults to "1 hour".

    Returns:
        pd.DataFrame: The timeseries data.
    """
    query = """
        SELECT measured_at, value_numeric
        FROM sli_measurements
        WHERE sli_name = %s AND measured_at >= now() - %s::interval AND success = true
        ORDER BY measured_at;
    """
    conn = psycopg2.connect(dsn)
    df = pd.read_sql(query, conn, params=(sli_name, window))
    conn.close()
    return df


@st.fragment(run_every="30s")
def render_latency_timeseries(dsn: str, sli_name: str, label: str):
    """Display the latency timeseries for a given SLI in a Streamlit app.

    Args:
        dsn (str): The database connection string.
            Example: "dbname=test user=postgres password=secret host=localhost port=5432"
        sli_name (str): The name of the service level indicator.
        label (str): The label for the latency metrics.
    """
    df = get_latency_timeseries(dsn, sli_name)
    st.line_chart(df.set_index("measured_at"))


if __name__ == "__main__":
    # Load database connection strings from environment variables
    try:
        dsn_monitoring = (
            f"dbname={os.environ['MONITORING_DB']} "
            f"user={os.environ['MONITORING_USER']} "
            f"password={os.environ['MONITORING_PASSWORD']} "
            f"host=localhost port={os.environ['LOCAL_DB_PORT']}"
        )
    except KeyError as e:
        print(f"Environment variable {e} not set. Please check your .env file.")
        exit(1)

    # Streamlit app
    st.title("Monitoring Dashboard")

    render_db_health(dsn_monitoring, "db_health")

    render_latency_sli(
        dsn_monitoring,
        "fact_commandes_latency",
        "Latence: commandes",
    )
    render_latency_timeseries(
        dsn_monitoring,
        "fact_commandes_latency",
        "Latence: commandes",
    )

    render_latency_sli(
        dsn_monitoring,
        "fact_visites_latency",
        "Latence: visites",
    )
    render_latency_timeseries(
        dsn_monitoring,
        "fact_visites_latency",
        "Latence: visites",
    )


# Pour aller plus loin:
# 1) Mise en place d'une architecture "collecteur" et "visualiseur" pour la
#   surveillance de la base de données. Solution open-source: Prometheus + Grafana.
#   Grafana à mettre en place dans ce script pour la partie visualiseur.
