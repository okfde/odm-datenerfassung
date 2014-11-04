#Search Bing for 'data' using their API (https://datamarket.azure.com/dataset/5BA839F1-12CE-4CCE-BF57-A49D98D29A44).
#To get going you need to sign up for that APU and grab your API key, managed under https://datamarket.azure.com/account/keys
import sys
#TODO delete CSV output
import unicodecsv

import metautils
from dbsettings import settings

from pyBingSearchAPI.bing_search_api import BingSearchAPI 

#TODO: Filetypes from metautils!

def find_data(city_id, site, filetypes=[ft.lower() for ft in metautils.allfiletypes]):
    site = site.replace('http://', '')
    query = ' OR '.join(['ext:%s' % f for f in filetypes])
    query = 'domain:%s AND (%s)' % (site, query)

    my_key = sys.argv[2]
    bing = BingSearchAPI(my_key)
    
    skipper= 0
    firstUrl = ""
    
    results = []
    
    urls = []
    
    count = 0
    
    print 'Query (can be used on bing.com): ' + query
    
    while True:
        params = {'$format': 'json',
                  '$top': 50,
                  '$skip': skipper}

        results_raw = bing.search('web',query,params).json() # requests 1.0+
                    
        newresults = results_raw['d']['results'][0]['Web']
        
        if len(newresults) == 0:
            break;

        if newresults[0]['Url'] == firstUrl:
            print "Breaking after " + str(count) + " pages"
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
    fileout = sys.argv[1]
    metautils.setsettings(settings)
    
    cur = metautils.getDBCursor(settings)
    
    #Get cities to search
    cur.execute('SELECT city_shortname, url FROM cities WHERE binged = %s', (True,))
    bres = cur.fetchall()
    
    urls = []
    for row in bres:
        print "Searching " + row[1]
        urls.extend(find_data(row[0], row[1]))
        #TODO: Get current set from DB
        #Compare sets and write out statistics, incl. what wasn't found this time
        #Spot testing of whether that stuff has really gone
        #Add new data to DB
    
    #TODO: Delete CSV output
    fields = ('Stadt_URL', 'URL_Datei', 'URL_Text', 'Beschreibung', 'Format', 'geo', 'URL_Dateiname')
    writer = unicodecsv.DictWriter(open(fileout, "wb"), fields)
    writer.writeheader()
    print "Writing " + str(len(urls)) + "urls"
    for url in urls:
        writer.writerow(url)

if __name__ == '__main__':
    main()
