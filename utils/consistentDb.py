import psycopg2

import metautils

print 'Finding cities with data...'
cities = metautils.getCitiesWithData()
print cities

print '\nRemoving search machine data that has been found with own crawler...'
for city in cities:
    cur = metautils.getDBCursor(dictCursor = True)
    
    #Get all Google and Bing data to see if the files have also been found by crawling (and in the future, data catalogs)
    cur.execute('SELECT source, url FROM data WHERE city LIKE %s AND source = %s OR source = %s', (city,'b','g'))
    gbres = cur.fetchall()
    cur.execute('SELECT filelist FROM data WHERE city LIKE %s AND source = %s OR source = %s AND array_length(filelist,1)>0', (city,'c','d'))
    allfiles = [t[0].split('/')[-1].lower() for t in [f for f in [res['filelist'] for res in cur.fetchall()]]]
    for result in gbres:
        if result['url'].split('/')[-1].lower() in allfiles:
            print 'Excluding ' + result['url'] + ' from results (source: ' + result['source'] + ').'
            cur.execute('UPDATE data SET accepted = %s, checked = %s WHERE url LIKE %s', (False, True, result['url']))
    metautils.dbCommit()

print '\nRemoving cities with no data that are not part of the original database...'
cur = metautils.getDBCursor()
cur.execute('DELETE FROM cities WHERE city_shortname IN (SELECT cities.city_shortname FROM cities LEFT JOIN data ON data.city = cities.city_shortname WHERE data.city IS NULL AND cities.city_type IS NULL)')
metautils.dbCommit()

print '\nRemoving search machine and crawl data that is from the data catalog...'
cur = metautils.getDBCursor(dictCursor = True)
#Get all portals
cur.execute('SELECT city_shortname, open_data_portal, odp_alias FROM cities WHERE catalog_read = %s', (True,))
citieswithportals = cur.fetchall()

for result in citieswithportals:
    cur = metautils.getDBCursor(dictCursor = True)
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
        
