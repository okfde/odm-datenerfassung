import ckanapi
import unicodecsv as csv
import sys

ckaninstance = ckanapi.RemoteCKAN('https://offenedaten.de', user_agent='ckanapiexample/1.0 (+http://okfn.de)')
groups = ckaninstance.action.group_show(id='berlin')

csvoutfile = open(sys.argv[1], 'wb')
datawriter = csv.writer(csvoutfile, delimiter=',')

columns = [ 'title', 'name', 'notes', 'author', 'author_email', 'owner_org', 'url', 'capacity', 'private', 'maintainer', 'maintainer_email', 'state', 'version', 'license_id', 'revision_id', 'type', 'id']

row = []
for column in columns:
    row.append(column);

datawriter.writerow(row)

for package in groups['packages']:
    row = []
    for column in columns:
        row.append(package[column])
    datawriter.writerow(row)

csvoutfile.close();

