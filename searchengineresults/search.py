#Search Bing for 'data' using their API (https://datamarket.azure.com/dataset/5BA839F1-12CE-4CCE-BF57-A49D98D29A44).
#To get going you need to sign up for that APU and grab your API key, managed under https://datamarket.azure.com/account/keys
import sys

import metautils
from dbsettings import settings

from pyBingSearchAPI.bing_search_api import BingSearchAPI 

def find_data(city_id, site, filetypes=[ft.lower() for ft in metautils.allfiletypes]):
    site = site.replace('http://', '')
    query = ' OR '.join(['ext:%s' % f for f in filetypes])
    query = 'domain:%s AND (%s)' % (site, query)

    my_key = sys.argv[1]
    bing = BingSearchAPI(my_key)
    
    skipper= 0
    firstUrl = ""
    
    results = []
    
    urls = []
    
    count = 0
    
    #print 'Query (can be used on bing.com): ' + query
    
    while True:
        params = {'$format': 'json',
                  '$top': 50,
                  '$skip': skipper}

        results_raw = bing.search('web',query,params).json() # requests 1.0+
                    
        newresults = results_raw['d']['results'][0]['Web']
        
        if len(newresults) == 0:
            break;

        if newresults[0]['Url'] == firstUrl:
            #print "Breaking after " + str(count) + " pages"
            break;
        
        #Once repetitions 
        firstUrl = newresults[0]['Url']
        results.extend(newresults)

        skipper += 50
        count += 1

    urls = [{
        'Stadt_URL': city_id,
        'URL_Datei': l['Url'],
        'URL_Text': l['Title'],
        'Beschreibung': l['Description'],
        'Format': l['Url'].split('.')[-1].upper(),
        'URL_Dateiname': l['Url'].split('/')[-1]
    } for l in results]

    for l in urls:
        l['geo'] = metautils.isgeo(l['Format'])

    return urls


def main():
    metautils.setsettings(settings)
    
    cur = metautils.getDBCursor(settings)
    
    #Get cities to search
    cur.execute('SELECT city_shortname, url FROM cities WHERE binged = %s', (True,))
    bres = cur.fetchall()
    
    print 'domain:incommon:new:binglost'
    
    for row in bres:
        citydata = find_data(row[0], row[1])
        citydict = {}
        for result in citydata:
            citydict[result['URL_Datei']] = result
        bingset = set(citydict.keys())
        allset = set(citydict.keys())
        cur = metautils.getDBCursor(settings)
        cur.execute('SELECT url FROM data WHERE source=%s AND city=%s', ('b', row[0]))
        dbset = set()
        for dbres in cur.fetchall():
            dbset.add(dbres[0])
            allset.add(dbres[0])
        #Analysis
        intersection = dbset.intersection(bingset)
        dbnot = allset.difference(dbset)
        bingnot = allset.difference(bingset)

        records = []
        for urlkey in dbnot:
            therow = citydict[urlkey]
            #In this case, we can safely assign it directly
            therow['URL'] = therow['URL_Datei']
            #Likewise, there cannot be any filenames
            therow['filenames'] = []
            metautils.convert_crawl_row(therow, 'b')
            records.append(therow)
            
        print row[1] + ':' + str(len(intersection)) + ':' + str(len(dbnot)) + ':' + str(len(bingnot))
        #Write to DB  
        metautils.addCrawlDataToDB(records) #Checked and accepted are both false by default

if __name__ == '__main__':
    main()
