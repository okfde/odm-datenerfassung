import psycopg2

import metautils

cities = metautils.getCitiesWithData()

for city in cities:
    cur = metautils.getDBCursor()
    
    #Start by accepting everything that has been checked
    cur.execute('UPDATE data SET accepted = TRUE WHERE city LIKE %s AND checked = TRUE', (city,))
    metautils.dbCommit()
    
    cur = metautils.getDBCursor(dictCursor = True)
    
    #Get all Google and Bing data to see if the files have also been found by crawling (and in the future, data catalogs)
    cur.execute('SELECT source, url FROM data WHERE city LIKE %s AND source = %s OR source = %s', (city,'b','g'))
    gbres = cur.fetchall()
    cur.execute('SELECT filelist FROM data WHERE city LIKE %s AND source = %s OR source = %s AND array_length(filelist,1)>0', (city,'c','d'))
    allfiles = [t[0].split('/')[-1].lower() for t in [f for f in [res['filelist'] for res in cur.fetchall()]]]
    for result in gbres:
        if result['url'].split('/')[-1].lower() in allfiles:
            print 'Excluding ' + result['url'] + ' from results (source: ' + result['source'] + ').'
            cur.execute('UPDATE data SET accepted = FALSE WHERE url LIKE %s', (result['url'],))
    metautils.dbCommit()
    
    #Now that we've done that, test all c/b/g results to see if they contain a data portal url or alias, and exclude accordingly
    #for each city:
        #get portals
        #get all (still) accepted data for c/b/g
        #for each row
            #select url
            #if url contains any of the portals, set accepted=false
        #commit
        
    
        
