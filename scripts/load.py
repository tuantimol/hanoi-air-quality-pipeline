import io
import os
import sys
from datetime import date, datetime, timedelta, timezone

import boto3
import pandas as pd
from botocore.exceptions import ClientError
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

BUCKET = "raw-data"
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
TABLES = ["air_quality", "weather"]


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=os.environ["MINIO_ROOT_USER"],
        aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
        region_name="us-east-1",
    )


def get_engine():
    url = URL.create(
        "postgresql+psycopg2",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        port=5432,
        database=os.environ["POSTGRES_DB"],
    )
    return create_engine(url)


def read_parquet_from_lake(s3, name: str, ds: str) -> pd.DataFrame:
    key = f"{name}/date={ds}/data.parquet"
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=key)
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            raise FileNotFoundError(
                f"Không thấy s3://{BUCKET}/{key}. Hãy chạy extract.py cho ngày {ds} trước."
            ) from e
        raise
    return pd.read_parquet(io.BytesIO(obj["Body"].read()))


def load_table(conn, df: pd.DataFrame, name: str, ds: str) -> None:
    ds_date = date.fromisoformat(ds)

    df = df.copy()
    df["ingested_date"] = ds_date                      
    df["loaded_at"] = datetime.now(timezone.utc)      

    table_exists = conn.execute(
        text("SELECT to_regclass(:t)"), {"t": f"raw.{name}"}
    ).scalar()
    if table_exists:
        conn.execute(
            text(f"DELETE FROM raw.{name} WHERE ingested_date = :d"), {"d": ds_date}
        )
    df.to_sql(name, conn, schema="raw", if_exists="append", index=False)


def load(ds: str) -> None:
    s3 = get_s3_client()
    engine = get_engine()

    frames = {name: read_parquet_from_lake(s3, name, ds) for name in TABLES}

    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
        for name, df in frames.items():
            load_table(conn, df, name, ds)
            print(f"Loaded {len(df)} rows -> raw.{name} (ingested_date={ds})")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else (date.today() - timedelta(days=1)).isoformat()
    load(target)
