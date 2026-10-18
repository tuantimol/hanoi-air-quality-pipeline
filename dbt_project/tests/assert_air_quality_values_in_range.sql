SELECT
    observed_at,
    pm25,
    aqi
FROM {{ ref('stg_air_quality') }}
WHERE pm25 < 0
   OR pm25 > 1000
   OR aqi < 0
   OR aqi > 500

