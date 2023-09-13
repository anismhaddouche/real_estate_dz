from datetime import datetime
from pathlib import Path

import psycopg
from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport
from prefect import flow, get_run_logger, task

from utils import (connect_to_database, create_table_rental, ingest_announce,
                   load_query, transform_annonce_data)

db_params = {
    "dbname": "realestate",
    "user": "postgres",
    "password": "example",
    "host": "localhost",
    "port": "5432",
}


@task(name="Prepare database")
def prep_db(db_params: dict, sql_request: str):
    """
    Create a database and table if not exists
    """
    logger = get_run_logger()
    with psycopg.connect(
        f"host={db_params['host']} port={db_params['port']} user={db_params['user']} password={db_params['password']}",
        autocommit=True,
    ) as conn:
        res = conn.execute(
            f"SELECT 1 FROM pg_database WHERE datname='{db_params['dbname']}'"
        )
        if len(res.fetchall()) == 0:
            logger.info(f"Creating the db {db_params['dbname']}")
            conn.execute(f"create database {db_params['dbname']};")
        with psycopg.connect(
            f"host={db_params['host']} port={db_params['port']} dbname={db_params['dbname']}  user={db_params['user']} password={db_params['password']}",
            autocommit=True,
        ) as conn:
            conn.execute(sql_request)


@task(name="fetch new data")
def fetch_new_data(conn, url: str, query, operationName, lastPage, last_date) -> None:
    """
    Fetch data into the database
    """
    logger = get_run_logger()
    logger.info(f"The Timestamp of the most recent annouce in the table is {last_date}")
    transport = AIOHTTPTransport(url=url)
    client = Client(transport=transport, fetch_schema_from_transport=False)
    for i in range(lastPage):
        result = client.execute(
            query,
            operation_name=operationName,
            variable_values={
                "mediaSize": "LARGE",
                "q": None,
                "filter": {
                    "categorySlug": "immobilier-location",
                    "origin": None,
                    "hasPrice": True,
                    "fields": [],
                    "page": i,
                    "count": 1000,
                },
            },
        )
        data_page = result["search"]["announcements"]["data"]
        recent_date_page = datetime.strptime(
            data_page[0]["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        if recent_date_page > last_date:
            for j in range(len(data_page)):
                recent_date_annonce = datetime.strptime(
                    data_page[j]["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ"
                )
                if recent_date_annonce > last_date:
                    logger.info(
                        f"Fetching page{i} announce {j} created at {recent_date_annonce}"
                    )
                    ingest_announce(conn, transform_annonce_data(data_page[j]))
            del data_page
        else:
            break


@task(name="fetch all data")
def fetch_all_data(conn, url: str, query, operationName, lastPage):
    """
    fetching all data in the website and save it in a parquet file
    """
    logger = get_run_logger()
    logger.info(f"Fetching all data till the page {lastPage}")
    transport = AIOHTTPTransport(url=url)
    client = Client(transport=transport, fetch_schema_from_transport=False)
    for i in range(lastPage + 1):
        logger.info(f" Fetching page {i}/{lastPage}")
        result = client.execute(
            query,
            operation_name=operationName,
            variable_values={
                "mediaSize": "LARGE",
                "q": None,
                "filter": {
                    "categorySlug": "immobilier-location",
                    "origin": None,
                    "hasPrice": True,
                    "fields": [],
                    "page": i,
                    "count": 1000,
                },
            },
        )
        data_page = result["search"]["announcements"]["data"]
        for data_announce in data_page:
            ingest_announce(conn, transform_annonce_data(data_announce))
    return None


@flow(name="fetch data")
def fetch_data(url: str, query_path: Path, query_last_page_path: Path, db_params: dict):
    """
    Main flow for getting date (all fo only fetch)
    """
    prep_db(db_params, create_table_rental)
    conn = connect_to_database(db_params)
    logger = get_run_logger()
    transport = AIOHTTPTransport(url=url)
    client = Client(transport=transport, fetch_schema_from_transport=False)
    operationName = "SearchQueryWithoutFilters"
    query_last_page = load_query(query_last_page_path)
    result_last_page = client.execute(
        query_last_page,
        operation_name=operationName,
        variable_values={
            "mediaSize": "LARGE",
            "q": None,
            "filter": {
                "categorySlug": "immobilier-location",
                "origin": None,
                "hasPrice": True,
                "fields": [],
                "page": 1,
                "count": 1000,
            },
        },
    )
    query = load_query(query_path)
    lastPage = result_last_page["search"]["announcements"]["paginatorInfo"]["lastPage"]
    try:
        cursor = conn.cursor()
        select_query = (
            "SELECT created_at FROM rental ORDER BY created_at DESC LIMIT 1 ;"
        )
        cursor.execute(select_query)
        last_date = cursor.fetchone()
    except conn.Error as e:
        logger.info("Error executing query:", e)

    if last_date is None:
        fetch_all_data(conn, url, query, operationName, lastPage)
    else:
        last_date = last_date[0]
        fetch_new_data(conn, url, query, operationName, lastPage, last_date)
    conn.close()
    return None


if __name__ == "__main__":
    # test
    url = "https://api.ouedkniss.com/graphql"
    query_path = Path("config/datas.graphql")
    query_last_page_path = Path("config/pagination.graphql")
    fetch_data(url, query_path, query_last_page_path, db_params)
