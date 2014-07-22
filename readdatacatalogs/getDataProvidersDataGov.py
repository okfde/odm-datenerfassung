import sys
import json
import codecs

with open(sys.argv[1], 'rb') as jsonfile:
    text = jsonfile.read()
    data = json.loads(text)   

    portals = []   
    authors = []
    maintainers = []
    tags = []
 
    for item in data:
        if ('metadata_original_portal' in item['extras'] and item['extras']['metadata_original_portal'] != None and item['extras']['metadata_original_portal'] not in portals):
            portals.append(item['extras']['metadata_original_portal'])
        if ('maintainer' in item and item['maintainer'] != None and item['maintainer'] not in maintainers):
            maintainers.append(item['maintainer'])
        if ('author' in item and item['author'] != None and item['author'] not in authors):
            authors.append(item['author'])
        if ('tags' in item and len(item['tags']) != 0):
            for tag in item['tags']:
                if (tag not in tags):
                   tags.append(tag)

jsonfile.close()

outfile = codecs.open('portals.txt', 'wb', 'utf-8')
for portal in portals:
    outfile.write(portal + u'\n')
outfile.close()

outfile = codecs.open('authors.txt', 'wb', 'utf-8')
for author in authors:
    outfile.write(author + u'\n')
outfile.close()

outfile = codecs.open('maintainers.txt', 'wb', 'utf-8')
for maintainer in maintainers:
    outfile.write(maintainer + u'\n')
outfile.close()

outfile = codecs.open('tags.txt', 'wb', 'utf-8')
for tag in tags:
    outfile.write(tag + u'\n')
outfile.close()
