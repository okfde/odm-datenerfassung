DELETE FROM cities WHERE city_shortname IN
(SELECT cities.city_shortname
FROM cities
LEFT JOIN data ON data.city = cities.city_shortname
WHERE data.city IS NULL AND cities.city_type IS NULL)