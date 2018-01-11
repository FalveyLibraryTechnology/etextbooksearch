import os
import io
import csv
import json
import urllib.parse

from src.utils import mapHashPath
from src.ProgressBar import ProgressBar

# Load Bookstore
storeJSON = {}
for file in os.listdir('BookstoreFiles'):
    with open(os.path.join('BookstoreFiles', file)) as jf:
        j = json.load(jf)
        for book in j:
            book['classes'] = ['%s (%s)' % (c['code'], c['prof'].capitalize()) for c in book['classes']]
            storeJSON[str(book['isbn'])] = book

def formatForAC(filename, msg):
    map = {}
    with open(filename, 'r') as source:
        reader = csv.reader(source, delimiter=',')
        for i, row in enumerate(reader):
            # isbn,year,ed,title,author,lang,url,publisher,form,city
            #    0    1  2     3      4    5   6         7    8    9
            if len(row) < 4:
                continue
            map[row[0]] = {
                'value': row[0],
                'label': row[3],
                'edition': row[1],
                'author': (row[4][:47] + '...') if len(row[4]) > 50 else row[4],
                'msg': msg
            }
            if len(row) > 6:
                map[row[0]]['worldcatHref'] = row[6]
    return map

items = {}

# Books in the library
# Separate by direct matching with store item
reserves = formatForAC('reports/have-print.csv', 'Reserved in Course Reserves')
for isbn in reserves:
    if not isbn in storeJSON:
        reserves[isbn]['msg'] = '%s Edition In Library Collection' % reserves[isbn]['edition']
items.update(reserves)

ebooks = formatForAC('reports/have-ebooks.csv', 'Correct Edition Available as eBook')
for isbn in ebooks:
    if not isbn in storeJSON:
        ebooks[isbn]['msg'] = '%s Edition eBook Available' % ebooks[isbn]['edition']
items.update(ebooks)

doNotHave = {}
doNotHave.update(formatForAC('reports/ebooks-available-for-purchase.csv', 'Available for ebook purchase'))
# Add Class and teacher information
# Massage descriptions
def addClassInfo(dict):
    for isbn in dict:
        if len(dict[isbn]['author']) > 0:
            dict[isbn]['description'] = '<i>%s</i><br/>%s<br/><b>%s</b>' % (dict[isbn]['author'], dict[isbn]['value'], dict[isbn]['msg'])
        else:
            dict[isbn]['description'] = '%s<br/><b>%s</b>' % (dict[isbn]['value'], dict[isbn]['msg'])
        del dict[isbn]['author']
        del dict[isbn]['edition']
        del dict[isbn]['msg']
        if isbn in storeJSON:
            dict[isbn]['classes'] = storeJSON[isbn]['classes']
        else:
            for key in mapJson:
                if isbn in mapJson[key]:
                    dict[isbn]['classes'] = storeJSON[key]['classes']
    return dict

with open(mapHashPath()) as jf:
    mapJson = json.load(jf)
    items = addClassInfo(items)
    doNotHave = addClassInfo(doNotHave)

final = {'items': items, 'faculty': doNotHave}

# Map related ISBNs
keys = list(items.keys())
print (len(keys))
keys.extend(doNotHave.keys())
print (len(keys))

map = []
for isbn in mapJson:
    matches = [x for x in mapJson[isbn] if x in keys]
    if matches:
        map.append({
            'editions': mapJson[isbn],
            'matches': matches
        })
final.update({'isbnmap': map})

with open('autocomplete.json', 'w') as out:
    json.dump(final, out, separators=(',', ':'))
