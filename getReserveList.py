import csv
import json
import os
import re
import requests
from checksumdir import dirhash # folder md5
from lxml import html
from xlrd import open_workbook  # Excel files

from utils import comma, findISBNs, findExcelISBNs, mapHashPath, sortUnique
from ProgressBar import ProgressBar

def solrURL(isbn):
    return 'http://hermes.library.villanova.edu:8082/solr/biblio/select?fl=callnumber-raw&wt=csv&q=isbn:"%s"' % isbn

def getClassName(classCode):
    parts = classCode.split(' ')
    if len(parts) < 2:
        return 'n/a'
    url = 'https://novasis.villanova.edu/pls/bannerprd/bvckctlg.p_display_courses?term_in=201820&one_subj=%s&sel_subj=&sel_crse_strt=%s&sel_crse_end=%s&sel_levl=&sel_schd=&sel_coll=&sel_divs=&sel_dept=&sel_attr=' % (parts[0], parts[1], parts[1])
    response = requests.get(url)
    tree = html.fromstring(response.content)
    titleEl = tree.xpath('//td[@class="nttitle"][2]')[0]
    return titleEl.text

# Load exploded print books we have
catalog = []
if not os.path.exists("reports/have-print-exact.csv"):
    print ("Run findEtextbooks.py first.")
    exit (0)
else:
    with open('reports/have-print-exact.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            catalog.append(row[0]) # isbn
    catalog = sortUnique(catalog)
    print ('= Loaded catalog ISBNs from file (%s)' % comma(len(catalog)))

# Bookstore JSON
bookstoreJSON = []
for file in os.listdir("BookstoreFiles"):
    with open(os.path.join("BookstoreFiles", file), 'r') as jsonFile:
        bookstoreJSON.extend(json.load(jsonFile))

print ('\nComparing %s books to a catalog of %s...' % (comma(len(bookstore)), comma(len(catalog))))
cindex = 0
with open('reserve-list.csv', 'w') as writeFile:
    writeFile.write('notes,isbn,call number,professor,class,class name,title\n')
    bar = ProgressBar(len(catalog))
    for isbn in catalog:
        response = requests.get(solrURL(isbn))
        data = response.text.split('\n')
        for book in bookstoreJSON:
            if book['isbn'] == isbn:
                for course in book['classes']:
                    writeFile.write(',%s,"%s",%s,"%s","%s","%s"\n' % (
                        isbn,   # ISBN
                        data[1], # Call number
                        course['prof'], # Professor
                        course['code'], # Class code
                        getClassName(course['code']), # Class name
                        book['title']  # Title
                    ))
                break
        bar.progress()
    bar.finish()
