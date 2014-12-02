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

#Create step. Failures are OK if the city already exists
dict_cur.execute("SELECT city_shortname FROM cities")

for rec in dict_cur.fetchall():
    dataset_dict = {}
    dataset_dict['name'] = rec['city_shortname']
    dataset_dict['id'] = rec['city_shortname']
    data_string = urllib.quote(json.dumps(dataset_dict))
    request = urllib2.Request(url +'/api/3/action/organization_create')
    request.add_header('Authorization', apikey)
    response = urllib2.urlopen(request, data_string)
    response_dict = json.loads(response.read())
    pprint.pprint(rec['city_shortname'] + ": " + str(response_dict['success']))

#Update step. We always want to be able to update.
keys = ['city_shortname', 'city_fullname']
extras = ['city_type', 'open_data_portal', 'api_get', 'api_post', 'api_link', 'api_post_content', 'latitude', 'longitude', 'contact_email', 'contact_person', 'url', 'ris_url']
query = 'SELECT '
keys.extend(extras)
for key in keys:
    query += key + ','
query = query[0:len(query)-1]
query = query + ' FROM cities'
dict_cur.execute(query)
for rec in dict_cur.fetchall():
    dataset_dict = {}
    dataset_dict['id'] = rec['city_shortname']
    dataset_dict['name'] = rec['city_shortname']
    dataset_dict['title'] = rec['city_fullname']
    dataset_dict['extras'] = []
    for key in extras:
        dataset_dict['extras'].append({'key': key, 'value': rec[key]})
    data_string = urllib.quote(json.dumps(dataset_dict))
    request = urllib2.Request(url +'/api/3/action/organization_create')
    request.add_header('Authorization', apikey)
    response = urllib2.urlopen(request, data_string)
    response_dict = json.loads(response.read())
    pprint.pprint(rec['city_shortname'] + ": " + str(response_dict['success']))
    assert(response_dict['success'] == True)

