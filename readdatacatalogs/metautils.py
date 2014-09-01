# -*- coding: utf-8 -*-
def getgroupofelements(target, item):
    if target in item:
        returnstring = arraytocsv(item[target])
    return returnstring
    
def arraytocsv(arrayvalue):
    returnstring = ''
    for part in arrayvalue:
        returnstring += part + ','
        #Get rid of last commas
    returnstring = returnstring[0:len(returnstring)-1]
    return returnstring
    
def setofvaluesascsv(arrayvalue, keyvalue):
    simplearray = setofvaluesasarray(arrayvalue, keyvalue)
    return arraytocsv(simplearray)
    
def setofvaluesasarray(arrayvalue, keyvalue):
    simplearray = []
    for item in arrayvalue:
        simplearray.append(item[keyvalue])
    return simplearray
    
def setBlankCategories(row):
    row[u'Veröffentlichende Stelle'] = ''
    row[u'Arbeitsmarkt'] = ''
    row[u'Bevölkerung'] = ''
    row[u'Bildung und Wissenschaft'] = ''
    row[u'Haushalt und Steuern'] = ''
    row[u'Stadtentwicklung und Bebauung'] = ''
    row[u'Wohnen und Immobilien'] = ''
    row[u'Sozialleistungen'] = ''
    row[u'Öffentl. Sicherheit'] = ''
    row[u'Gesundheit'] = ''
    row[u'Kunst und Kultur'] = ''
    row[u'Land- und Forstwirtschaft'] = ''
    row[u'Sport und Freizeit'] = ''
    row[u'Umwelt'] = ''
    row[u'Transport und Verkehr'] = ''
    row[u'Energie, Ver- und Entsorgung'] = ''
    row[u'Politik und Wahlen'] = ''
    row[u'Gesetze und Justiz'] = ''
    row[u'Wirtschaft und Wirtschaftsförderung'] = ''
    row[u'Tourismus'] = ''
    row[u'Verbraucher'] = ''
    row[u'Sonstiges'] = ''
    row[u'Noch nicht kategorisiert'] = 'x'
    
    return row

def govDataLongToODM(group):
    group = group.strip()
    if group == u'Bevölkerung' or group == u'Bildung und Wissenschaft' or group == u'Gesundheit' or group == u'Transport und Verkehr' or group == u'Politik und Wahlen' or group == u'Gesetze und Justiz':
        return [group]
    elif group == u'Wirtschaft und Arbeit':
        return [u'Arbeitsmarkt', u'Wirtschaft und Wirtschaftsförderung']
    elif group == u'Öffentliche Verwaltung, Haushalt und Steuern':
        return [u'Haushalt und Steuern', u'Sonstiges']
    elif group == u'Infrastruktur, Bauen und Wohnen':
        return [u'Wohnen und Immobilien', u'Stadtentwicklung und Bebauung']
    elif group == u'Infrastruktur, Bauen und Wohnen' or group == u'Geographie, Geologie und Geobasisdaten':
        return [u'Stadtentwicklung und Bebauung']
    elif group == u'Soziales':
        return [u'Sozialleistungen']
    elif group == u'Kultur, Freizeit, Sport und Tourismus':
        return [u'Kunst und Kultur', u'Sport und Freizeit', u'Tourismus']
    elif group == u'Umwelt und Klima':
        return [u'Umwelt']
    elif group == u'Verbraucherschutz':
        return [u'Verbraucher(-schutz)']
    else:
        return []

def extractFormat(filestring):
    return "PASS"
    
#Sometimes things deep in the JSON are interpreted as a string
def dequotejson(stringvalue):
    cleanvalue = stringvalue.replace('\\', '')
    cleanvalue = cleanvalue[1:len(cleanvalue)-1]
    return cleanvalue

def getTargetColumns():
    return [u'Quelle', u'Stadt', u'URL PARENT', u'Dateibezeichnung', u'URL Datei', u'Format', u'Beschreibung', u'Zeitlicher Bezug', u'Lizenz', u'Kosten', u'Veröffentlichende Stelle', u'Arbeitsmarkt', u'Bevölkerung', u'Bildung und Wissenschaft', u'Haushalt und Steuern', u'Stadtentwicklung und Bebauung', u'Wohnen und Immobilien', u'Sozialleistungen', u'Öffentl. Sicherheit', u'Gesundheit', u'Kunst und Kultur', u'Land- und Forstwirtschaft', u'Sport und Freizeit', u'Umwelt', u'Transport und Verkehr', u'Energie, Ver- und Entsorgung', u'Politik und Wahlen', u'Gesetze und Justiz', u'Wirtschaft und Wirtschaftsförderung', u'Tourismus', u'Verbraucher', u'Sonstiges', u'Noch nicht kategorisiert']
            