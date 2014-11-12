import unicodecsv as csv
import sys

def simplifyurl(url):
    return u'/'.join(url.split('/')[3:])

if (len(sys.argv)<3):
    print 'Usage: cleanDuplicates filetoclean.csv outputfile.csv [supportingitemsfulllist.csv]'
    exit()

lowestulmparents = ('/metadaten/', '/single/')

csvoutfile = open(sys.argv[2], 'wb')
citywriter = csv.writer(csvoutfile, delimiter=',')
cities = dict()

with open(sys.argv[1], 'rb') as csvfile:
    cityreader = csv.reader(csvfile, delimiter=',')
    #Skip headings
    headings = next(cityreader, None)
    #Write headings
    citywriter.writerow(headings)

    #Divide up data into cities to reduce searching
    for row in cityreader:
        cityurl = row[0]
        if cityurl not in cities:
            cities[cityurl] = dict()
            
csvfile.close()
    
with open(sys.argv[1], 'rb') as csvfile:
    cityreader = csv.reader(csvfile, delimiter=',')
    #Skip headings
    headings = next(cityreader, None)
    
    for inrow in cityreader:
        try:
            cityurl = inrow[0]
            searchurl = inrow[1]
            parenturl = inrow[6]
        except:
            print u'Data format error: ' + u', '.join(inrow) + u'\nStopping.'
        found = False

        print "Searching for " + searchurl

        if searchurl in cities[cityurl]:
            #Prioritize records with all data
            #In general this shouldn't happen, as the file is downloaded
            #after the link is found
            if ((('ermittelt' in cities[cityurl][searchurl][6]) and ('ermittelt' not in parenturl)) or 
            #Ulm special handling to prevent using links from summary pages
            ((cityurl == 'ulm.de') and any(x in parenturl for x in lowestulmparents))):
                cities[cityurl][searchurl] = inrow
                print "Replacing row"
            else:
                print "Row is already there: duplicate"
        else:
            print "Appending as unique entry"
            cities[cityurl][searchurl] = inrow

findparentsource = False

if (len(sys.argv)>3):
    findparentsource = True
    parentsfile = sys.argv[3]

missinglinks = {}

for city in cities.values():
    for outputrow in city.values():
        try:
            if 'ermittelt' in outputrow[6] and findparentsource:
                #These links always have http etc. in them, the stored links from the A elements may not
                missinglink = simplifyurl(outputrow[1])
                print 'Will search for link component: ' + missinglink + ' in entire items file'
                missinglinks[missinglink] = {}
                missinglinks[missinglink]['actualurl'] = outputrow[1]
                missinglinks[missinglink]['parenturl'] = 'Nicht gefunden'
                missinglinks[missinglink]['parenttitle'] = 'Nicht gefunden'
        except:
            print outputrow

if findparentsource and len(missinglinks) > 0:
    #Unfortunately it won't work if the URL arguments get rearranged :(
    #If it becomes a problem we should parse the URLs
    with open(sys.argv[3], 'rb') as csvfile:
        parentreader = csv.reader(csvfile, delimiter=',')
        #Skip headings
        headings = next(parentreader, None)

        count = 0
        
        for inrow in parentreader:
            count += 1
            if count % 100 == 0:
                print str(count) + ' rows read'
            try:
                if 'ermittelt' not in inrow[6]:
                    linkurl = inrow[1] #URL of link found. May or may not contain http
                    potentialparent = inrow[6]
                    for mlkey in missinglinks.keys():
                        if mlkey in linkurl:
                            print 'Found a parent: ' + potentialparent + ' for ' + mlkey
                            missinglinks[mlkey]['actualurl'] = inrow[2]
                            missinglinks[mlkey]['parenturl'] = inrow[6]
                            missinglinks[mlkey]['parenttitle'] = inrow[7]
            except:
                print inrow
                
for city in cities.values():
    for outputrow in city.values():
        try:
            if 'ermittelt' in outputrow[6] and findparentsource:
                urlkey = simplifyurl(outputrow[1])
                outputrow[2] = missinglinks[urlkey]['actualurl']
                outputrow[6] = missinglinks[urlkey]['parenturl']
                outputrow[7] = missinglinks[urlkey]['parenttitle']
        except:
            print outputrow
        citywriter.writerow(outputrow)

csvfile.close();
csvoutfile.close();
