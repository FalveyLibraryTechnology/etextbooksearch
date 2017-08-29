import csv
import os
import re
import requests
from lxml import html
from xlrd import open_workbook  # Excel files

from utils import comma, findISBNs, findExcelISBNs, sortUnique
from ProgressBar import ProgressBar

def solrURL(isbn):
    return 'http://hermes.library.villanova.edu:8082/solr/biblio/select?fl=callnumber-raw,title&wt=csv&q=isbn:"%s"' % isbn

def getClassName(classCode):
    parts = classCode.split(' ')
    if len(parts) < 2:
        return 'n/a'
    url = 'https://novasis.villanova.edu/pls/bannerprd/bvckctlg.p_display_courses?term_in=201820&one_subj=%s&sel_subj=&sel_crse_strt=%s&sel_crse_end=%s&sel_levl=&sel_schd=&sel_coll=&sel_divs=&sel_dept=&sel_attr=' % (parts[0], parts[1], parts[1])
    response = requests.get(url)
    tree = html.fromstring(response.content)
    titleEl = tree.xpath('//td[@class="nttitle"][2]')[0]
    return titleEl.text

bookstore = sortUnique(findExcelISBNs('Fall BookList 7-25-2017 (Library).xlsx', 'BookstoreFiles'))
catalog = sortUnique(findISBNs('solrISBNs12Jul2017.txt', 'CatalogFiles'))

classMap = {}
print ('- Making class map...')
with open('class-list.csv', 'r') as classList:
    for line in classList:
        parts = line.strip().split(',')
        classMap[parts[0]] = []
        for i in range(1, len(parts)):
            classMap[parts[0]].append(parts[i].split('---'))

print ('\nComparing %s books to a catalog of %s...' % (comma(len(bookstore)), comma(len(catalog))))
cindex = 0
with open('callnumbers.csv', 'w') as writeFile:
    writeFile.write('notes,professor,class,class name,call number,title,isbn\n')
    bar = ProgressBar(len(bookstore))
    for bisbn in bookstore:
        while cindex < len(catalog) and bisbn > catalog[cindex]:
            cindex += 1
        if cindex < len(catalog) and bisbn == catalog[cindex]:
            response = requests.get(solrURL(bisbn))
            data = response.text.split('\n')
            for i in range(len(classMap[bisbn])):
                writeFile.write(',%s,%s,"%s",%s,%s\n' % (
                    classMap[bisbn][i][1], # Teacher
                    classMap[bisbn][i][0], # Class code
                    getClassName(classMap[bisbn][i][0]), # Class name
                    data[1], # Call number and title
                    bisbn    # ISBN
                ))
        bar.progress()
    bar.finish()
