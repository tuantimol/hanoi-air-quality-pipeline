SELECT
    a.observed_at,
    a.pm25,
    a.pm10,
    a.no2,
    a.o3,
    a.aqi,
    w.temperature_c,
    w.humidity_pct,
    w.wind_kmh,
    w.precipitation_mm
FROM {{ ref('stg_air_quality') }} AS a
LEFT JOIN{{ ref('stg_weather') }} AS w ON a.observed_at = w.observed_at

