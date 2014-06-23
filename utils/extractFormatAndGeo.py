import unicodecsv as csv
import sys

csvoutfile = open(sys.argv[4], 'wb')
citywriter = csv.writer(csvoutfile, delimiter=',')

filetypes = ('.CSV', '.XLS', '.XLSX', '.JSON', '.GEOJSON', '.GML', '.GPX', '.GJSON', '.TIFF', '.SHP', '.KML', '.KMZ', '.WMS', '.WFS', '.RDF', '.ZIP')
geofiletypes = ('.GEOJSON', '.GML', '.GPX', '.GJSON', '.TIFF', '.SHP', '.KML', '.KMZ', '.WMS', '.WFS')

with open(sys.argv[1], 'rb') as csvfile:
    cityreader = csv.reader(csvfile, delimiter=',')
    #Skip headings
    headings = next(cityreader, None)
    #Write headings
    citywriter.writerow(headings)
    
    for inrow in cityreader:
        url = inrow[1]
        tcolumn = int(sys.argv[2])
        geocolumn = int(sys.argv[3])
        format = ''
        geo = ''
        for ext in filetypes:
            if ext in url.upper():
                format = ext[1:len(ext)]               
                if ext in geofiletypes:
                    geo = 'x'     
        if (len(inrow) - 1) < tcolumn:
            inrow.append(format)
        else:
            inrow[tcolumn] = format
        if (len(inrow) - 1) < geocolumn:
            inrow.append(geo)
        else:
            inrow[geocolumn] = geo

        citywriter.writerow(inrow)

csvfile.close();
csvoutfile.close();
