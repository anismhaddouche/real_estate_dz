import json

import psycopg
from gql import gql
from prefect import task

create_table_rental = """
    CREATE TABLE if not exists rental(
        id SERIAL PRIMARY KEY,
        title TEXT ,
        description TEXT ,
        show_analytics BOOLEAN ,
        created_at TIMESTAMP ,
        is_from_store BOOLEAN,
        like_count INTEGER ,
        status TEXT ,
        price bigint ,
        price_preview bigint ,
        price_unit TEXT ,
        price_type TEXT ,
        exchange_type TEXT,
        small_description JSONB,
        category_name TEXT ,
        city_id INT ,
        city_name TEXT ,
        region_id TEXT ,
        region_name TEXT ,
        media_url TEXT,
        store_id INT ,
        store_name TEXT ,
        store_image_url TEXT,
        user_id INT 
    );
"""


@task
def connect_to_database(db_params: dict):
    """
    Connect to the PostgreSQL database
    """
    try:
        conn = psycopg.connect(
            host=db_params["host"],
            port=db_params["port"],
            dbname=db_params["dbname"],
            user=db_params["user"],
            password=db_params["password"],
            autocommit=True,
        )
        return conn
    except psycopg.Error as e:
        print("Error where connecting the the database:", e)
        return None


def transform_annonce_data(raw_data: dict) -> dict:
    """
    Transforme raw data to a format compatible with the created table
    """
    transformed_data = {
        "id": raw_data["id"],
        "title": raw_data["title"] if raw_data["title"] else None,
        "description": raw_data["description"] if raw_data["description"] else None,
        "show_analytics": raw_data["showAnalytics"]
        if raw_data["showAnalytics"]
        else None,
        "created_at": raw_data["createdAt"] if raw_data["createdAt"] else None,
        "is_from_store": raw_data["isFromStore"] if raw_data["isFromStore"] else None,
        "like_count": raw_data["likeCount"] if raw_data["likeCount"] else None,
        "status": raw_data["status"] if raw_data["status"] else None,
        "price": raw_data["price"] if raw_data["price"] else None,
        "price_preview": raw_data["pricePreview"] if raw_data["pricePreview"] else None,
        "price_unit": raw_data["priceUnit"] if raw_data["priceUnit"] else None,
        "price_type": raw_data["priceType"] if raw_data["priceType"] else None,
        "exchange_type": raw_data["exchangeType"] if raw_data["exchangeType"] else None,
        "small_description": json.dumps(raw_data["smallDescription"])
        if raw_data["smallDescription"]
        else None,  # area is on the small_description key
        "category_name": raw_data["category"]["name"] if raw_data["category"] else None,
        "city_id": raw_data["cities"][0]["id"] if raw_data["cities"] else None,
        "city_name": raw_data["cities"][0]["name"] if raw_data["cities"] else None,
        "region_id": raw_data["cities"][0]["region"]["id"]
        if raw_data["cities"]
        else None,
        "region_name": raw_data["cities"][0]["region"]["name"]
        if raw_data["cities"]
        else None,
        "media_url": ([url["mediaUrl"] for url in raw_data["medias"]])
        if raw_data["medias"]
        else None,
        "store_id": raw_data["store"]["id"] if raw_data["store"] else None,
        "store_name": raw_data["store"]["name"] if raw_data["store"] else None,
        "store_image_url": raw_data["store"]["imageUrl"] if raw_data["store"] else None,
        "user_id": raw_data["user"]["id"] if raw_data["user"] else None,
    }
    return transformed_data


def ingest_announce(conn, transformed_annonce_data: dict) -> None:
    """
    Insert a transformed annonce into the table
    """
    ingest_announce_sql = f""" INSERT INTO rental(
        id, title,
        description, show_analytics, created_at, is_from_store,
        like_count, status, price, price_preview, price_unit, price_type, exchange_type,
        small_description, category_name, city_id, city_name, region_id,
        region_name, media_url, store_id, store_name,
        store_image_url, user_id
    ) VALUES (
        %(id)s, %(title)s, %(description)s, %(show_analytics)s, %(created_at)s, %(is_from_store)s,
        %(like_count)s, %(status)s, %(price)s, %(price_preview)s,
        %(price_unit)s, %(price_type)s, %(exchange_type)s, %(small_description)s,
        %(category_name)s, %(city_id)s, %(city_name)s, %(region_id)s,
        %(region_name)s,  %(media_url)s, %(store_id)s, %(store_name)s,
        %(store_image_url)s, %(user_id)s
    );
"""
    with conn.cursor() as curr:
        try:
            curr.execute(ingest_announce_sql, transformed_annonce_data)
        except psycopg.Error as e:
            print(f"Error: {e} in annonce id={transformed_annonce_data['id']}")


def load_query(path):
    with open(path) as f:
        return gql(f.read())
