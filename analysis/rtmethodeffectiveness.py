import urllib
import unicodecsv as csv
import sys

def printlist ( array ):
    for item in array:
        print item
    return
    
def iscorrectdata ( cell ):
    scell = cell.strip()
    if (scell != 'Daten') and (scell != 'Geodaten'):
        return False
    else:
        return True

#Unfortunately, some special handling is needed per city
#But not this much. Will optimize once a new city comes.
cityname = sys.argv[1]
#Key for the sheet with 'final' results, although they are still allowed to include overlaps...
vkey = '1dRTL0fuXYxHDx6R7uW6l6ys1_Hw3s4yYFZD_3TjP2Fk'
#Key for the sheet with lists of files from data catalogs
kkey = '1tkKGeQqlx9YTLlwGiGhkYEG-kswTkQlSp7Kcj6J0Eh4'
removeparameters = False
nocatalog = False

if cityname == 'rostock':
    ggid = '336231741'
    kgid = '1862363954'
elif cityname == 'ulm':
    ggid = '1992341045'
    kgid = '1085553358'
elif cityname == 'koeln':
    ggid = '2110295467'
    kgid = '1846551467'
    removeparameters = True
elif cityname == 'bonn':
    ggid = '1093780796'
    kgid = '596265031'
elif cityname == 'moers':
    ggid = '988368152'
    kgid = '1743221268'
elif cityname == 'berlin':
    ggid = '588106105'
    kgid = '1978531407'
elif cityname == 'stuttgart':
    ggid = '51929456'
    nocatalog = True
elif cityname == 'muenchen':
    ggid = '1289667874'
    nocatalog = True

googlebingcrawlcsvurl = urllib.urlopen('https://docs.google.com/spreadsheets/d/' + vkey + '/export?single=true&gid=' + ggid + '&format=csv')
if not nocatalog:
    catalogcsvurl = urllib.urlopen('https://docs.google.com/spreadsheets/d/' + kkey + '/export?single=true&gid=' + kgid + '&format=csv')

print 'Downloading and reading Google and Bing and Crawl results'
csvreader = csv.reader(googlebingcrawlcsvurl)
firstRow = True
googleresults = []
bingresults = []
crawlresults = []
for row in csvreader:
    #print row
    if (firstRow):
        firstRow = False
        print 'Skipping header...'
        continue
    filename = urllib.unquote(row[4].split('/')[-1])
    if removeparameters:
        filename = filename.split('?')[0]
    filename = filename.strip()
    source = row[0].strip()
    if source == 'g':
        if filename not in googleresults:
            print 'Adding ' + filename + ' to Google results.'
            googleresults.append(filename)
        else:
            print 'Warning: ' + filename + ' already in Google results. Not adding.'
    elif source == 'b':
        if filename not in bingresults:
            print 'Adding ' + filename + ' to Bing results.'
            bingresults.append(filename)
        else:
            print 'Warning: ' + filename + ' already in Bing results. Not adding.'
    elif source == 'c':
        if filename not in crawlresults:
            print 'Adding ' + filename + ' to Crawl results.'
            crawlresults.append(filename)
        else:
            print 'Warning: ' + filename + ' already in Crawl results. Not adding.'
    else:
        print 'Not a valid entry type: ' + row[0]
        
print 'Downloading and reading Catalog results'
catalogresults = []
if not nocatalog:

    csvreader = csv.reader(catalogcsvurl)

    for row in csvreader:
        #Handle wms results specially; they don't appear in the other sources
        if 'wms' in row[0]:
            filename = urllib.unquote(row[0].split('/')[-2])
        else:
            filename = urllib.unquote(row[0].split('/')[-1])
        if filename not in catalogresults:
            print 'Adding ' + filename + ' to Catalog results.'
            catalogresults.append(filename)
        else:
            print 'Warning: ' + filename + ' already in Catalog results. Not adding.'

alldata = []
alldata.append(googleresults)
alldata.append(bingresults)
alldata.append(crawlresults)
alldata.append(catalogresults)

uniquelist = []

for dataset in alldata:
    for filename in dataset:
        if filename not in uniquelist:
            uniquelist.append(filename)
            
total = len(uniquelist)
gfound = len(googleresults)
bfound = len(bingresults)
cfound = len(crawlresults)
kfound = len(catalogresults)

print 'There are ' + str(total) + ' unique entries based on filename'
print 'Google found ' + str(gfound) + ' of those'
print 'Bing found ' + str(bfound) + ' of those'
print 'Crawler found ' + str(cfound) + ' of those'
print 'Catalog \'found\' ' + str(kfound) + ' of those'

print 'For pasting: '
print str(total) + '\t' + str(gfound) + '\t' + str(bfound) + '\t' + str(cfound) + '\t' + str(kfound)

gset = set(googleresults)
bset = set(bingresults)
cset = set(crawlresults)
kset = set(catalogresults)
allset = set(uniquelist)

intersection = gset.intersection(bset)
print 'Intersection of Google and Bing: ' + str(len(intersection))
printlist(intersection)
intersection = gset.intersection(cset)
print 'Intersection of Google and Crawler: ' + str(len(intersection))
printlist(intersection)
intersection = gset.intersection(kset)
print 'Intersection of Google and Catalog: ' + str(len(intersection))
printlist(intersection)
intersection = bset.intersection(cset)
print 'Intersection of Bing and Crawler: ' + str(len(intersection))
printlist(intersection)
intersection = bset.intersection(kset)
print 'Intersection of Bing and Catalog: ' + str(len(intersection))
printlist(intersection)
intersection = cset.intersection(kset)
print 'Intersection of Crawler and Catalog: ' + str(len(intersection))
printlist(intersection)
difference = allset.difference(kset)
print 'What the catalog doesn\'t contain (' + str(len(difference)) + '):'
printlist(difference)

