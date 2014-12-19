# -*- coding: utf-8 -*-
import re
import itertools
from lxml import html
import metautils
from dbsettings import settings


portalname = u'opendata.bayern.de'

category_to_odm_map = {
    u'Öffentliche Verwaltung, Haushalt und Steuern'  : [u'Öffentliche Verwaltung, Haushalt und Steuern'],
    'Bildung und Wissenschaft'                       : [u'Bildung und Wissenschaft'],
    'Verkehr'                                        : [u'Transport und Verkehr'],
    'Handwerk, Gewerbe, Industrie und Landwirtschaft': [u'Wirtschaft und Arbeit'],
    'Klima, Umwelt und Natur '                       : [u'Umwelt und Klima'],
    'Politik, Medien und Gesellschaft'               : [u'Politik und Wahlen'],
    'Menschen, Familie und Soziales'                 : [u'Soziales', u'Bevölkerung'],
    'Freizeit, Kultur und Tourismus'                 : [u'Kultur, Freizeit, Sport, Tourismus'],
    u'Wohnen, Grundstück und Flächennutzung'         : [u'Infrastruktur, Bauen und Wohnen']}


def search_results_urls(n):
    url = 'http://opendata.bayern.de/daten/list,' + str(n) + ',.html'
    page = html.parse(url)
    return page.xpath('//ul[@class="search-results"]//li/h3/a/@href')


def catalog_entry_urls():
    n = 0  # start of catalog entry nr, shows 10 at a time
    srl = search_results_urls(n)
    urls = []
    while srl:
        urls.extend(srl)
        n += 10
        srl = search_results_urls(n)
    urls = map(lambda u: {'url': 'http://opendata.bayern.de' + u}, urls)
    return urls


def fetch(d):
    page = html.parse(d['url'])
    subhead = page.xpath('//p[@class="sub-head"]')[0].text
    tables = page.xpath('//table')
    beschreibung = tables[0].xpath('.//td')
    kontakt = tables[1].xpath('.//td')
    bedingungen = tables[2].xpath('.//td')

    d['title'] = page.xpath('//h1')[1].text
    d['filelist'] = beschreibung[0].xpath('./a/@href')
    d['description'] = beschreibung[1].text
    cats = map(lambda x: x.text, beschreibung[2].xpath('.//span'))
    d['categories'] = filter(None, cats)

    if kontakt:
        d['publisher'] = kontakt[0].text
    else:
        d['publisher'] = re.findall('"([^"]*)"', subhead)[0]

    d['nutzungsbedingungen'] = bedingungen[0].text
    if len(bedingungen) > 1:
        d['lizenzhinweise'] = bedingungen[1].text
    d['temporalextent'] = subhead[-10:len(subhead)]  # last ten chars
    return d


def get_license(lizenztext, nutzungsbedingungen):
    if lizenztext and "Creative Commons Namensnennung 3.0 Deutschland Lizenz" in lizenztext:
        return "CC-BY 3.0"
    elif lizenztext and "Lizenz CC0" in lizenztext:
        return "CC0-1.0"
    elif nutzungsbedingungen == 'Die Weiterverwendung der Daten ist frei.':
        return "other-open"
    else:
        return "other-closed"


def import_data(d):
    d['originating_portal'] = portalname
    d['city'] = 'bayern'
    d['source'] = 'd'
    d['costs'] = None
    d['spatial'] = False
    d['formats'] = []
    d['metadata'] = ''
    d['metadata_xml'] = None
    d['categories'] = list(itertools.chain(* map(lambda c: category_to_odm_map[c], d['categories'])))
    d['open'] = d['nutzungsbedingungen'] == \
                'Die Weiterverwendung der Daten ist frei.'
    d['licenseshort'] = get_license(d['lizenzhinweise'], d['nutzungsbedingungen'])
    return d


def bayern():
    ds = catalog_entry_urls()
    ds = map(fetch, ds)
    ds = map(import_data, ds)

    metautils.setsettings(settings)
    metautils.addSimpleDataToDB(ds,
                                portalname,
                                checked=True,
                                accepted=True,
                                remove_data=True)
    return ds

bayern()
