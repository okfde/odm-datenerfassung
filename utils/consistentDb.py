import psycopg2

import metautils

from dbsettings import settings

metautils.setsettings(settings)

print '\nMarking all Bonn Google data as rejected (needs to be changed if Google searches are ever resumed!'
cur = metautils.getDBCursor(settings, dictCursor = True)
cur.execute('update data set accepted = %s where city = %s and source = %s', (False,'bonn','g'))
metautils.dbCommit()

print '\nResetting open...'
cur = metautils.getDBCursor(settings, dictCursor = True)
cur.execute('select url, licenseshort from data')
for ores in cur.fetchall():
    if ores['licenseshort'].strip() == '':
        license = 'nicht bekannt'
        open = None
    else:
        open = metautils.isopen(ores['licenseshort'].strip())
        license = ores['licenseshort'].strip()
    cur.execute('update data set licenseshort = %s, open = %s where url = %s', (license, open, ores['url']))
metautils.dbCommit()

print 'Finding cities with data...'
cities = metautils.getCitiesWithData()
print cities

print '\nRemoving search machine data that has been found with own crawler...'
for city in cities:
    cur = metautils.getDBCursor(settings, dictCursor = True)
    
    #Get all Google and Bing data to see if the files have also been found by crawling
    cur.execute('SELECT source, url FROM data WHERE city LIKE %s AND (source = %s OR source = %s) AND accepted = %s', (city,'b','g', True))
    gbres = cur.fetchall()
    cur.execute('SELECT filelist FROM data WHERE city LIKE %s AND source = %s OR source = %s AND array_length(filelist,1)>0', (city,'c','d'))
    allfiles = [t[0].split('/')[-1].lower() for t in [f for f in [res['filelist'] for res in cur.fetchall()]]]
    for result in gbres:
        if result['url'].split('/')[-1].lower() in allfiles:
            print 'Excluding ' + result['url'] + ' from results (source: ' + result['source'] + ').'
            cur.execute('UPDATE data SET accepted = %s, checked = %s WHERE url LIKE %s', (False, True, result['url']))
    metautils.dbCommit()

print '\nRemoving cities with no data that are not part of the original database...'
cur = metautils.getDBCursor(settings)
cur.execute('DELETE FROM cities WHERE city_shortname IN (SELECT cities.city_shortname FROM cities LEFT JOIN data ON data.city = cities.city_shortname WHERE data.city IS NULL AND cities.city_type IS NULL)')
metautils.dbCommit()

print '\nRemoving search machine and crawl data that is from the data catalog...'
cur = metautils.getDBCursor(settings, dictCursor = True)
#Get all portals
cur.execute('SELECT city_shortname, open_data_portal, odp_alias FROM cities WHERE catalog_read = %s', (True,))
citieswithportals = cur.fetchall()

for result in citieswithportals:
    cur = metautils.getDBCursor(settings, dictCursor = True)
    city = result['city_shortname']
    print city
    cur.execute('SELECT url FROM data WHERE city LIKE %s AND source = %s OR source = %s OR source = %s AND accepted = %s', (city,'b','g','c',True))
    citydata = cur.fetchall()
    #Now that we've done that, test all c/b/g results to see if they contain a data portal url or alias, and exclude accordingly
    completeportals = []
    if result['odp_alias'] != None:
        completeportals.extend(result['odp_alias'])
        completeportals.append(result['open_data_portal'])
    else:
        print result['open_data_portal']
        completeportals = (result['open_data_portal'],)
    print completeportals
    completeportalssimplified = []
    for portal in completeportals:
        if 'http://' in portal:
            completeportalssimplified.append(portal[7:len(portal)].strip())
            print 'Excluding ' + portal[7:len(portal)].strip() + ' from ' + city
        else:
            completeportalssimplified.append(portal.strip())
            print 'Excluding ' + portal.strip() + ' from ' + city
    for entry in citydata:
        if any(x in entry['url'] for x in completeportalssimplified):
            print 'Excluding ' + entry['url'] + ' from ' + city + ' results'
            cur.execute('UPDATE data SET accepted = %s, checked = %s WHERE url LIKE %s', (False, True, entry['url']))
    metautils.dbCommit()
    
print '\nChecking if all cities with data have coordinates...'
metautils.updateCitiesWithLatLong()

print '\nTransferring old categories...'
metautils.convertOldCategories()

print '\nRemoving unknown categories...'
metautils.removeUnknownCategories()
        
