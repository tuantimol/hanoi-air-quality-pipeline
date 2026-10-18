SELECT
    observed_at::date                       				AS observation_date,
    count(*)                                				AS hours_observed,
    round(avg(pm25)::numeric, 1)            				AS avg_pm25,
    max(pm25)                               				AS max_pm25,
    round(avg(aqi)::numeric, 0)             				AS avg_aqi,
    round(avg(temperature_c)::numeric, 1)   				AS avg_temp_c,
    round(avg(humidity_pct)::numeric, 0)    				AS avg_humidity_pct,
    CASE
        WHEN avg(aqi) IS NULL THEN NULL
        WHEN avg(aqi) <= 50  THEN 'Tốt'
        WHEN avg(aqi) <= 100 THEN 'Trung bình'
        WHEN avg(aqi) <= 150 THEN 'Không tốt cho nhóm nhạy cảm'
        WHEN avg(aqi) <= 200 THEN 'Xấu'
        WHEN avg(aqi) <= 300 THEN 'Rất xấu'
        ELSE 'Nguy hại'
    END                                     				AS aqi_category
FROM {{ ref('fct_hourly_air_weather') }}
GROUP BY  1

