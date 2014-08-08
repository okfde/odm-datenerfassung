import unicodecsv as csv
import sys

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
        cityurl = inrow[0]
        searchurl = inrow[1]
        found = False

        print "Searching for " + searchurl

        #Prioritize records with all data
        #In general this shouldn't happen, as the file is downloaded
        #after the link is found
        if searchurl in cities[cityurl]:
            if ('ermittelt' in cities[cityurl][searchurl][6]) and ('ermittelt' not in inrow[6]):
                cities[cityurl][searchurl] = inrow
                print "Replacing row"
            else:
                print "Row is already there: duplicate"
        else:
            print "Appending as unique entry"
            cities[cityurl][searchurl] = inrow

for city in cities.values():
    for outputrow in city.values():
        citywriter.writerow(outputrow)

csvfile.close();
csvoutfile.close();
