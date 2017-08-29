import os
import io
import csv
import json
import urllib.parse

from utils import mapHashPath

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
                'description': '%s<br/><b>%s</b>' % (row[0], msg),
                'edition': row[1],
                'msg': msg
            }
            if len(row) > 6:
                map[row[0]]['worldcatHref'] = row[6]
    return map

items = {}
items.update(formatForAC('have-underdrm.csv', 'Reserved in Course Reserves'))
items.update(formatForAC('have-drmfree.csv', 'Ebook Available'))
# Faculty books
doNotHave = {}
doNotHave.update(formatForAC('do-not-have.csv', 'Available for ebook purchase'))
# Add Class and teacher information
with open('class-list.csv', 'r') as classList:
    for line in classList:
        parts = line.strip().split(',')
        if parts[0] in items:
            items[parts[0]]['classes'] = []
            for i in range(1, len(parts)):
                p = parts[i].split('---')
                items[parts[0]]['classes'].append('%s (%s)' % (p[0], p[1].title()))
        elif parts[0] in doNotHave:
            doNotHave[parts[0]]['classes'] = []
            for i in range(1, len(parts)):
                p = parts[i].split('---')
                doNotHave[parts[0]]['classes'].append('%s (%s)' % (p[0], p[1].title()))
        else:
            # TODO SAD CLASSES

final = {'items': items, 'faculty': doNotHave}
# Map related ISBNs
with open(mapHashPath(), 'r') as source:
    keys = list(items.keys())
    print (len(keys))
    keys.extend(doNotHave.keys())
    print (len(keys))
    reader = csv.reader(source, delimiter=',')
    map = []
    for i, row in enumerate(reader):
        matches = [isbn for isbn in row if isbn in keys]
        if matches:
            map.append({
                'editions': row,
                'matches': matches
            })
    final.update({'isbnmap': map})

with open('autocomplete.json', 'w') as out:
    json.dump(final, out)
