import io
import os
import sys
from datetime import date, timedelta

import boto3
import pandas as pd
import requests
from botocore.exceptions import ClientError

LAT, LON = 21.0285, 105.8542 
BUCKET = "raw-data"
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")

DATASETS = {
    "air_quality": (
        "https://air-quality-api.open-meteo.com/v1/air-quality",
        "pm10,pm2_5,nitrogen_dioxide,ozone,us_aqi",
    ),
    "weather": (
        "https://api.open-meteo.com/v1/forecast",
        "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
    ),
}


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=os.environ["MINIO_ROOT_USER"],
        aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
        region_name="us-east-1",
    )


def ensure_bucket(s3) -> None:
    try:
        s3.head_bucket(Bucket=BUCKET)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("404", "NoSuchBucket", "NotFound"):
            s3.create_bucket(Bucket=BUCKET)
            print(f"Created bucket: {BUCKET}")
        else:
            raise


def fetch_hourly(url: str, hourly_vars: str, ds: str) -> pd.DataFrame:
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": hourly_vars,
        "start_date": ds,
        "end_date": ds,
        "timezone": "Asia/Bangkok",
    }
    resp = requests.get(url, params=params, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text}")
    data = resp.json()
    if "hourly" not in data:
        raise RuntimeError(f"Response has no 'hourly' field: {data}")
    df = pd.DataFrame(data["hourly"])
    if df.empty:
        raise RuntimeError(f"No data returned for {ds}")
    return df


def save_parquet(s3, df: pd.DataFrame, name: str, ds: str) -> str:
    buf = io.BytesIO()
    df.to_parquet(buf, index=False)
    key = f"{name}/date={ds}/data.parquet"
    s3.put_object(Bucket=BUCKET, Key=key, Body=buf.getvalue())
    return key


def extract(ds: str) -> None:
    s3 = get_s3_client()
    ensure_bucket(s3)
    for name, (url, hourly_vars) in DATASETS.items():
        df = fetch_hourly(url, hourly_vars, ds)
        key = save_parquet(s3, df, name, ds)
        print(f"Saved {len(df)} rows -> s3://{BUCKET}/{key}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = (date.today() - timedelta(days=1)).isoformat()
    extract(target)