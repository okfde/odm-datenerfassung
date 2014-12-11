import urllib
import unicodecsv as csv
import sys

def printlist ( array ):
    for item in array:
        print item
    return
    
def processfile(url):
    csvreader = csv.reader(url)
    firstrowdone = False
    results = {}
    urlcolumn = 4

    for row in csvreader:
        if not firstrowdone:
            firstrowdone = True
            continue
        filename = row[urlcolumn].strip()
        if removeparameters:
            filename = filename.split('?')[0]
        filename = filename.strip()
        if filename not in results:
            print 'Adding ' + filename + ' to results.'
            results[filename] = row
        elif filename in results:
            print 'Warning: ' + filename + ' already in results. Not adding.'
        else:
            print 'Warning: not data: ' + filename
            
    return results

#Key for the sheet with 'final' results, although they are still allowed to include overlaps...
vkey = '1dRTL0fuXYxHDx6R7uW6l6ys1_Hw3s4yYFZD_3TjP2Fk'
#Key for the sheet with lists of files from data catalogs
kkey = '1tkKGeQqlx9YTLlwGiGhkYEG-kswTkQlSp7Kcj6J0Eh4'
removeparameters = False

googleurl = urllib.urlopen('https://docs.google.com/spreadsheets/d/' + '1AdzjwLPuSXQg3Wg7DB1F-syuCGddPoy6ay6NfbVjWws' + '/export?single=true&gid=' + '879531375' + '&format=csv')
bingurl = urllib.urlopen('https://docs.google.com/spreadsheets/d/' + '1AdzjwLPuSXQg3Wg7DB1F-syuCGddPoy6ay6NfbVjWws' + '/export?single=true&gid=' + '1164735504' + '&format=csv')

print 'Downloading and reading Google results'
googleresults = processfile(googleurl)
print 'Downloading and reading Bing results'
bingresults = processfile(bingurl)

alldata = []
alldata.append(googleresults)
alldata.append(bingresults)

uniquelist = []

for dataset in alldata:
    for filename in dataset.keys():
        if filename not in uniquelist:
            uniquelist.append(filename)
            
total = len(uniquelist)
gfound = len(googleresults)
bfound = len(bingresults)

print 'There are ' + str(total) + ' unique entries based on filename'
print 'Google found ' + str(gfound) + ' of those'
print 'Bing found ' + str(bfound) + ' of those'

print 'For pasting: '
print str(total) + '\t' + str(gfound) + '\t' + str(bfound)

gset = set(googleresults.keys())
bset = set(bingresults.keys())
allset = set(uniquelist)

intersection = gset.intersection(bset)
print 'Intersection of Google and Bing: ' + str(len(intersection))
printlist(intersection)
