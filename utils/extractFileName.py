import unicodecsv as csv
import sys

csvoutfile = open(sys.argv[3], 'wb')
citywriter = csv.writer(csvoutfile, delimiter=',')

with open(sys.argv[1], 'rb') as csvfile:
    cityreader = csv.reader(csvfile, delimiter=',')
    #Skip headings
    headings = next(cityreader, None)
    #Write headings
    citywriter.writerow(headings)
    
    for inrow in cityreader:
        url = inrow[1]
        k = url.rfind("/")
        tcolumn = int(sys.argv[2])
        filename = inrow[1].split('/')[-1]
        if (len(inrow) - 1) < tcolumn:
          inrow.append(filename)
        else:
          inrow[tcolumn] = filename
        citywriter.writerow(inrow)

csvfile.close();
csvoutfile.close();
