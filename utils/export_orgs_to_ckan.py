import urllib2
import urllib
import json
import pprint

import metautils

from dbsettings import settings

metautils.setsettings(settings)

#This is a one time operation to create organisations based on the originating portal in ODM DB
#Run prior to importing data

#Change these as appropriate
url = ''
apikey = ''

dict_cur = metautils.getDBCursor(settings, dictCursor = True)
dict_cur.execute("SELECT distinct originating_portal FROM data")

for rec in dict_cur.fetchall():
    dataset_dict = {}
    dataset_dict['id'] = rec['originating_portal']
    dataset_dict['name'] = rec['originating_portal'].replace('.', '-').replace('/', '').replace(':', '').lower()
    data_string = urllib.quote(json.dumps(dataset_dict))
    request = urllib2.Request(url +'/api/3/action/organization_create')
    request.add_header('Authorization', apikey)
    response = urllib2.urlopen(request, data_string)
    response_dict = json.loads(response.read())
    created_org = response_dict['result']
    pprint.pprint(created_org)


