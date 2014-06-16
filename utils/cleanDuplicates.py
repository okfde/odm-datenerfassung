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
            cities[cityurl] = []
            
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

        for outrow in cities[cityurl]:
            outurl = outrow[1]
            if searchurl == outurl:
                print "Row is already there: duplicate"
                found = True
                break
        if not found:
            print "Appending as unique entry"
            cities[cityurl].append(inrow)

for city in cities.values():
    for outputrow in city:
        citywriter.writerow(outputrow)

csvfile.close();
csvoutfile.close();
