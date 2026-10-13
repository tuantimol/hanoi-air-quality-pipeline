# Hanoi Air Quality Pipeline
## File Structer:
hanoi-air-quality-pipeline/
├── docker-compose.yml
├── Dockerfile.airflow
├── .env
├── dags/
│   └── air_quality_dag.py
├── scripts/
│   ├── extract.py
│   └── load.py
├── dbt_project/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
│       ├── staging/
│       └── marts/
└── README.md
