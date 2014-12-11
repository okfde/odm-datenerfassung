import psycopg2, unicodecsv

import metautils

from dbsettings import settings

metautils.setsettings(settings)

csvfile = open('export.csv', 'wb')
csvwriter = unicodecsv.writer(csvfile)

cur = metautils.getDBCursor(settings, dictCursor = True)
cur.execute('select distinct unnest(categories) as cat from data')
columns = ['city', 'source', 'formats', 'license']
categories = []
for catrow in cur.fetchall():
    categories.append(catrow['cat'])
    
columns.extend(categories)

csvwriter.writerow(columns)

cur.execute('select city, source, formats, licenseshort, categories from data where accepted = %s', (True,))
for res in cur.fetchall():
    row = [res['city'], res['source'], metautils.arraytocsv(res['formats']), res['licenseshort']]
    for el in categories:
        if el in res['categories']:
            row.append('x')
        else:
            row.append('')
    
    csvwriter.writerow(row)

csvfile.close()
