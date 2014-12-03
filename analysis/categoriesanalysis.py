import psycopg2, unicodecsv

import metautils

from dbsettings import settings

metautils.setsettings(settings)

csvfile = open('categoriesanalysis.csv', 'wb')
csvwriter = unicodecsv.writer(csvfile)

cur = metautils.getDBCursor(settings, dictCursor = True)
cur.execute('select distinct unnest(categories) as cat from data')
categories = []
for catrow in cur.fetchall():
    categories.append(catrow['cat'])

csvwriter.writerow(categories)

genresults = []
for cat in categories:
    cur.execute('select count(url) as res from data where categories@>ARRAY[%s] and accepted = %s', (cat, True))
    genresults.append(cur.fetchall()[0]['res'])

csvwriter.writerow(genresults)

indcities = ('bremen', 'hamburg', 'berlin', 'badenwuerttemberg')

for city in indcities:
    citrow = [city]
    csvwriter.writerow(citrow)
    citresults = []
    for cat in categories:
        cur.execute('select count(url) as res from data where city like %s and categories@>ARRAY[%s] and accepted = %s', (city, cat, True))
        citresults.append(cur.fetchall()[0]['res'])

    csvwriter.writerow(citresults)
