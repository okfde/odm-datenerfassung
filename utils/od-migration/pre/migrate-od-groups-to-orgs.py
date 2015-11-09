# -*- coding: utf-8 -*-
import urllib2
import urllib
import json
import pprint
import os

#This script is a one time operation to create organisations based on groups from offenedaten.de

def setdata(dictobj, id, title, desc, api_link, city_type, latitude, longitude, open_data_portal, url, image_url):
    dictobj['name'] = id
    dictobj['id'] = id
    dictobj['title'] = title
    dictobj['description'] = desc
    dictobj['extras'] = []
    dictobj['extras'].append({'key': 'api_link', 'value': api_link})
    dictobj['extras'].append({'key': 'city_type', 'value': city_type})
    dictobj['extras'].append({'key': 'latitude', 'value': latitude})
    dictobj['extras'].append({'key': 'longitude', 'value': longitude})
    dictobj['extras'].append({'key': 'open_data_portal', 'value': open_data_portal})
    dictobj['extras'].append({'key': 'url', 'value': url})
    dictobj['image_url'] = image_url

mogdy = {}
maxplank = {}
sonder = {}
mittenwalde = {}
paderborn = {}
okfde = {}
codingdavinci = {}
ubleipzig = {}

setdata(mogdy, "mogdy", "MOGDy München", "Im Rahmen des Munich Open Government Day wurden verschiedene Datensätze der Landeshauptstadt München durch das Statistische Amt als Open Data freigegeben und bereitgestellt. Die Mehrheit entstammt der Datenbank des Statistikamtes (ZIMAS).", None, None, 48.1375, 11.575833333333, None, "http://www.muenchen.de/rathaus/Stadtverwaltung/Direktorium/IT-Beauftragte/Projekt-E--und-Open-Government/MOGDy.html", "http://www.muenchen.de/rathaus/.imaging/stk/lhm/image300/dms/Home/Stadtverwaltung/Direktorium/IT-Beauftragte/Teaser/mogdy_teaser/document/mogdy_teaser.jpg")
setdata(maxplank, "mpiwg", "Max-Planck-Instituts für Wissenschaftsgeschichte", "Auswahl von historischen Quellen aus der Sammlung des Max-Planck-Instituts für Wissenschaftsgeschichte Berlin.", None, None, 52.445277777778, 13.277777777778, None, "https://www.mpiwg-berlin.mpg.de/de/ressourcen/index.html", "https://www.mpiwg-berlin.mpg.de/de/images/logo.png")
setdata(sonder, "apps4deutschland", "Apps4Deutschland", "Diese Organization enthält besondere Datensätze, die im Rahmen des Apps4Deutschland-Wettbewerbs freigegeben wurden.", None, None, 52.53121, 13.40565, None, "http://apps4deutschland.de/", "http://apps4deutschland.de/wp-content/themes/apps4d/img/logo.png")
setdata(mittenwalde, "mittenwalde", "Stadt Mittenwalde", "Open Data der Stadt Mittenwalde", None,"Stadt", 52.266666666667, 13.533333333333, None, "http://www.mittenwalde.de", "http://mittenwalde.de/ris/wappen.jpg")
setdata(paderborn, "paderborn", "Stadt Paderborn", "Informationen bezüglich Paderborn, NRW.", None, "Stadt", 51.719444444444, 8.7572222222222, None, "http://www.paderborn.de/", "http://upload.wikimedia.org/wikipedia/commons/thumb/1/19/DEU_Paderborn_COA.svg/200px-DEU_Paderborn_COA.svg.png")
setdata(okfde, "okf-de", "Open Knowledge Foundation Deutschland", "Die Open Knowledge Foundation Deutschland ist ein gemeinnütziger Verein, der sich für offenes Wissen, offene Daten, Transparenz und Beteiligung einsetzt.", None, None, 52.5169347, 13.4251999, None, "http://www.okfn.de", "http://okfn.de/static/images/logo_black.png")
setdata(codingdavinci, "codingdavinci", "Coding da Vinci", "Coding da Vinci ist der erste Kultur-Hackathon (Entwicklertag) in Deutschland, der Entwickler/innen, Designer/innen und Gamer/innen zusammenbringt, um in Kooperation mit Kultureinrichtungen aus offenen Daten und eigener Kreativität neue Anwendungen, mobile Apps, Spiele und Visualisierungen umzusetzen.\n\nZiel von Coding da Vinci ist nicht nur das Etablieren und Vernetzen einer technikaffinen und kulturbegeisterten Community, sondern insbesondere das kreative Ausschöpfen der technischen Möglichkeiten, die in unserem digitalen Kulturerbe stecken. Wir setzen uns für die freie Verfügbarkeit und Nutzbarkeit von Kulturdaten ein und stellen sicher, dass sie kreativen Menschen als Rohmaterial für ihre Ideen zur Verfügung stehen.", None, None, 52.5167596, 13.4250505, None, "http://okfn.de/projekte/codingdavinci/", "http://okfn.de/static/images/projects/codingdavinci_square.jpg")
setdata(ubleipzig, "ubleipzig", "Universitätsbibliothek Leipzig", None, None, None, 51.332455104722, 12.368229031667, None, "https://www.ub.uni-leipzig.de", "https://www.ub.uni-leipzig.de/static/ubl-gradient.png")

#Alter this if e.g. things went wrong with only one import
#orgs_to_add = (mogdy, maxplank, sonder, mittenwalde, paderborn)
orgs_to_add = (okfde, codingdavinci, ubleipzig)

for org in orgs_to_add:
    data_string = urllib.quote(json.dumps(org))
    url = os.environ['CKANURL']
    apikey = os.environ['CKANAPIKEY']
    request = urllib2.Request(url +'/api/3/action/organization_create')
    request.add_header('Authorization', apikey)
    response = urllib2.urlopen(request, data_string)
    response_dict = json.loads(response.read())
    pprint.pprint(org['title'] + ": " + str(response_dict['success']))
    assert(response_dict['success'] == True)