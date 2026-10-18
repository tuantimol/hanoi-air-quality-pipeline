WITH 

source AS (
    SELECT * FROM {{ source('raw', 'weather') }}
),

typed AS (
    SELECT
        "time"::timestamp                   		AS observed_at,
        temperature_2m::float               		AS temperature_c,
        relative_humidity_2m::float         		AS humidity_pct,
        wind_speed_10m::float               		AS wind_kmh,
        precipitation::float                		AS precipitation_mm,
        ingested_date,
        loaded_at
    FROM source
),

deduped AS (
    SELECT
        *,
        row_number() over (
            partition by observed_at
            ORDER BY loaded_at DESC, ingested_date DESC
        ) AS rn
    FROM typed
)

SELECT
    observed_at,
    temperature_c,
    humidity_pct,
    wind_kmh,
    precipitation_mm,
    ingested_date
FROM deduped
WHERE rn = 1
