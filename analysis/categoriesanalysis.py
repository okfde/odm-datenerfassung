import psycopg2, unicodecsv

import metautils

from dbsettings import settings

metautils.setsettings(settings)

csvfile = open('categoriesanalysis.csv', 'wb')
csvwriter = unicodecsv.writer(csvfile)

cur = metautils.getDBCursor(settings, dictCursor = True)
cur.execute('select distinct unnest(categories) as cat from data')
headings = ['city', 'source/total', 'open']
categories = []
for catrow in cur.fetchall():
    categories.append(catrow['cat'])
rowtowrite = headings
rowtowrite.extend(categories)
csvwriter.writerow(rowtowrite)
'''
genresults = []
for cat in categories:
    cur.execute('select count(url) as res from data where categories@>ARRAY[%s] and accepted = %s', (cat, True))
    genresults.append(cur.fetchall()[0]['res'])

csvwriter.writerow(genresults)
'''
sources = ('m', 'd', 'c', 'b', 'g')
'''
for source in sources:
    sourcerow = ['Source: ' + source]
    csvwriter.writerow(sourcerow)
    
    srcresults = []
    for cat in categories:
        cur.execute('select count(url) as res from data where categories@>ARRAY[%s] and accepted = %s and source = %s', (cat, True, source))
        srcresults.append(cur.fetchall()[0]['res'])
        
    csvwriter.writerow(srcresults)

indcities = ('bremen', 'hamburg', 'berlin', 'badenwuerttemberg', 'rheinlandpfalz')
'''
cur = metautils.getDBCursor(settings, dictCursor = True)
cur.execute('select distinct city from data where accepted = %s order by city', (True,))
indcities = []
for citrow in cur.fetchall():
    indcities.append(citrow['city'])

for city in indcities:
    cur.execute('select count(url) as res from data where city like %s and accepted = %s', (city, True))
    total = (cur.fetchall()[0]['res'])
    heading = [city, total]
    csvwriter.writerow(heading)
    for source in sources:
	for opentype in [True, False, None]:    
	    citresults = [city, source, str(opentype)]
	    #Percent results don't make that much sense to me
	    #percentres = [city, source, str(opentype), 'percent']
	    for cat in categories:
                cur.execute('select count(url) as res from data where city like %s and categories@>ARRAY[%s] and source = %s and open is %s and accepted = %s', (city, cat, source, opentype, True))
                result = cur.fetchall()[0]['res']
	        citresults.append(result)
	        #percentres.append(str((result/total)*100))
            csvwriter.writerow(citresults)
            #csvwriter.writerow(percentres)
csvfile.close()
