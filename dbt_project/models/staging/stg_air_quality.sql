WITH 

source AS (
    SELECT * FROM {{ source('raw','air_quality') }}
),

typed AS (
    SELECT
        "time"::timestamp           		AS observed_at,
        pm2_5::float                   		AS pm25,
        pm10::float                  		AS pm10,
        nitrogen_dioxide::float     	        AS no2,
        ozone::float                		AS o3,
        us_aqi::int                 		AS aqi,
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
    pm25,
    pm10,
    no2,
    o3,
    aqi,
    ingested_date
FROM deduped
WHERE 	rn = 1
  	AND pm25 IS NOT NULL
