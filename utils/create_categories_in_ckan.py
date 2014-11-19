# -*- coding: utf-8 -*-
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

categories = [
{"name": u"Noch nicht kategorisiert"},

{"name": u"Wirtschaft und Arbeit", 
"image": "https://raw.githubusercontent.com/fraunhoferfokus/govdata-theme/master/src/main/webapp/images/categories/wirtschaft_arbeit.png"},

{"name": u"Soziales",
"image": "https://raw.githubusercontent.com/fraunhoferfokus/govdata-theme/master/src/main/webapp/images/categories/soziales.png"},

{"name": u"Infrastruktur, Bauen und Wohnen",
"image": "https://raw.githubusercontent.com/fraunhoferfokus/govdata-theme/master/src/main/webapp/images/categories/infrastruktur_bauen_wohnen.png"},

{"name": u"Bildung und Wissenschaft",
"image": "https://raw.githubusercontent.com/fraunhoferfokus/govdata-theme/master/src/main/webapp/images/categories/bildung_wissenschaft.png"},

{"name": u"Gesundheit",
"image": "https://raw.githubusercontent.com/fraunhoferfokus/govdata-theme/master/src/main/webapp/images/categories/gesundheit.png"},

{"name": u"Öffentliche Verwaltung, Haushalt und Steuern",
"image": "https://raw.githubusercontent.com/fraunhoferfokus/govdata-theme/master/src/main/webapp/images/categories/verwaltung.png"},

{"name": u"Gesetze und Justiz",
"image": "https://raw.githubusercontent.com/fraunhoferfokus/govdata-theme/master/src/main/webapp/images/categories/gesetze_justiz.png"},

{"name": u"Transport und Verkehr",
"image": "https://raw.githubusercontent.com/fraunhoferfokus/govdata-theme/master/src/main/webapp/images/categories/transport_verkehr.png"},

{"name": u"Geographie, Geologie und Geobasisdaten",
"image": "https://raw.githubusercontent.com/fraunhoferfokus/govdata-theme/master/src/main/webapp/images/categories/geo.png"},

{"name": u"Verbraucherschutz",
"image": "https://raw.githubusercontent.com/fraunhoferfokus/govdata-theme/master/src/main/webapp/images/categories/verbraucher.png"},

{"name": u"Bevölkerung",
"image": "https://raw.githubusercontent.com/fraunhoferfokus/govdata-theme/master/src/main/webapp/images/categories/bevoelkerung.png"},

{"name": u"Umwelt und Klima",
"image": "https://raw.githubusercontent.com/fraunhoferfokus/govdata-theme/master/src/main/webapp/images/categories/umwelt_klima.png"},

{"name": u"Politik und Wahlen",
"image": "https://raw.githubusercontent.com/fraunhoferfokus/govdata-theme/master/src/main/webapp/images/categories/politik_wahlen.png"},

{"name": u"Kultur, Freizeit, Sport, Tourismus",
"image": "https://raw.githubusercontent.com/fraunhoferfokus/govdata-theme/master/src/main/webapp/images/categories/kultur_freizeit_sport_tourismus.png"}
]

for cat in categories:
    dataset_dict = {}
    dataset_dict['name'] = metautils.force_alphanumeric_short(cat['name'])
    dataset_dict['title'] = cat['name']
    dataset_dict['image_url'] = cat['image'] if 'image' in cat else None
    data_string = urllib.quote(json.dumps(dataset_dict))
    request = urllib2.Request(url +'/api/3/action/group_create')
    request.add_header('Authorization', apikey)
    response = urllib2.urlopen(request, data_string)
    response_dict = json.loads(response.read())
    created_grp = response_dict['result']
    pprint.pprint(created_grp)


