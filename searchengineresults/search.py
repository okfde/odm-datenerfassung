#TODO: Make work with imported bing module
#TODO: Download index and strip links
import sys
import unicodecsv

from census.bing_search_api import BingSearchAPI 

def find_data(site, filetypes=('csv', 'xls', 'xlsx', 'json', 'shp', 'kml', 'kmz', 'rdf', 'zip')):
    query = ' OR '.join(['ext:%s' % f for f in filetypes])
    query = 'domain:%s AND (%s)' % (site, query)

    my_key = sys.argv[2]
    bing = BingSearchAPI(my_key)
    
    skipper= 0
    firstUrl = ""
    
    results = []
    
    urls = []
    
    count = 0
    
    while True:
        params = {'$format': 'json',
                  '$top': 50,
                  '$skip': skipper}
        #TODO: I was only able to get this to work by modifying the module; how can we make it generic and submit a pull request?
        print(query)
    
        results_raw = bing.search('web',query,params).json() # requests 1.0+
        newresults = results_raw['d']['results']
        
        if len(newresults) == 0:
            break;
        
        if newresults[0]['Url'] == firstUrl:
            print "Breaking after " + str(count) + "pages"
            break;
        
        #Once repetitions 
        firstUrl = newresults[0]['Url']
        results.extend(newresults)

        skipper += 50
        count += 1

    urls = [{
        'Stadt': site,
        'URL': l['Url'],
        'Title': l['Title'],
        'Description': l['Description'],
        'Format': l['Url'].split('.')[-1].upper()
        'URL_Dateiname': l['Url'].split('/')[-1]
    } for l in results]
    
    return urls


def main():
    fileout = sys.argv[1]
    
    with open('sites.csv', 'rb') as csvfile:
        cityreader = unicodecsv.reader(csvfile, delimiter=',')
        headings = next(cityreader, None)
        
        urls = []
        for row in cityreader:
            print "Searching " + row[6]
            urls.extend(find_data(row[6]))
    
    fields = ('Stadt', 'URL', 'Title', 'Description', 'Format')
    writer = unicodecsv.DictWriter(open(fileout, "wb"), fields)
    writer.writeheader()
    print "Writing " + str(len(urls)) + "urls"
    for url in urls:
        writer.writerow(url)

if __name__ == '__main__':
    main()
