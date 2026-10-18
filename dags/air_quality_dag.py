"""
### Hanoi Air Quality Pipeline

Chạy hằng ngày, xử lý dữ liệu của **ngày hôm trước**:

1. `extract`: lấy dữ liệu từ Open-Meteo API, lưu Parquet vào MinIO
2. `load`: nạp Parquet từ MinIO vào PostgreSQL (schema `raw`)
3. `dbt_build`: chạy model (staging, marts) và kiểm thử chất lượng dữ liệu

Mọi bước đều idempotent: chạy lại cho cùng một ngày không sinh dữ liệu trùng.
"""

from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

# Hai hàm này nằm trong /opt/airflow/scripts (đã có trong PYTHONPATH).
# Cả hai có tham số tên `ds`: Airflow tự truyền ngày chạy (YYYY-MM-DD) vào đó.
from extract import extract
from load import load

DBT_DIR = "/opt/airflow/dbt_project"

default_args = {
    "owner": "data-eng",
    "retries": 2,                                # lỗi thì thử lại tối đa 2 lần
    "retry_delay": timedelta(minutes=5),         # mỗi lần cách nhau 5 phút
    "execution_timeout": timedelta(minutes=20),  # một task chạy quá 20 phút thì coi là lỗi
}

with DAG(
    dag_id="hanoi_air_quality",
    description="ELT: Open-Meteo -> MinIO -> PostgreSQL -> dbt",
    doc_md=__doc__,
    start_date=pendulum.datetime(2026, 10, 1, tz="UTC"),
    schedule="@daily",         # 00:00 UTC mỗi ngày = 07:00 giờ Hà Nội
    catchup=False,             # không tự chạy bù; dùng backfill khi cần
    max_active_runs=1,         # tránh hai lần chạy cùng ghi vào database một lúc
    default_args=default_args,
    tags=["portfolio", "air-quality"],
) as dag:

    t_extract = PythonOperator(
        task_id="extract",
        python_callable=extract,   # không cần op_args: Airflow tự điền `ds`
    )

    t_load = PythonOperator(
        task_id="load",
        python_callable=load,
    )

    # `dbt build` = chạy seed, model và test theo đúng thứ tự phụ thuộc.
    t_dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"cd {DBT_DIR} && dbt build --profiles-dir .",
    )

    t_extract >> t_load >> t_dbt_build
