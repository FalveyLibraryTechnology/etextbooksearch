import csv
import json
import os
import re
import requests
from checksumdir import dirhash # folder md5
from lxml import html
from xlrd import open_workbook  # Excel files

from src.utils import comma, findISBNs, sortUnique
from src.ProgressBar import ProgressBar

def solrURL(isbn):
    return 'http://hermes.library.villanova.edu:8082/solr/biblio/select?fl=callnumber-raw&wt=csv&q=isbn:"%s"' % isbn

classNameCache = {}
def getClassName(classCode):
    parts = classCode.split(" ")
    if len(parts) < 2:
        print ("INVALID CLASSCODE: %s" % classCode)
        return classCode
    codeHash = "%s%s" % (parts[0], parts[1])
    if codeHash in classNameCache:
        return classNameCache[codeHash]
    if len(parts) < 2:
        return "n/a"
    url = "https://novasis.villanova.edu/pls/bannerprd/bwckctlg.p_disp_course_detail?cat_term_in=201830&subj_code_in=%s&crse_numb_in=%s" % (parts[0], parts[1])
    response = requests.get(url)
    tree = html.fromstring(response.content)
    try:
        titleEl = tree.xpath('//td[@class="nttitle"]')[0]
        title = titleEl.text.split(" - ", maxsplit=1)[1]
        # print (title)
        classNameCache[codeHash] = title
    except:
        print ("MISSING CLASS TITLE: %s" % classCode)
        print (url)
        return classCode
    return title

# Bookstore JSON
print ("= Loading book data from BookstoreFiles/"
bookstoreJSON = []
for file in os.listdir("BookstoreFiles"):
    with open(os.path.join("BookstoreFiles", file), "r") as jsonFile:
        bookstoreJSON.extend(json.load(jsonFile))

# Load exploded print books we have
exactPrint = []
if not os.path.exists("reports/have-print-exact.csv"):
    if not os.path.exists("CatalogFiles"):
        print ("x Load ISBNs into CatalogFiles/ to generate this report.")
        exit (0)
    print ("= Using CatalogFiles and bookstoreJSON to make have-print-exact.")
    catalogISBNs = []
    for file in os.listdir("CatalogFiles"):
        catalogISBNs.extend(findISBNs(file, "CatalogFiles"))
    bookstoreISBNs = [x["isbn"] for x in bookstoreJSON]
    bar = ProgressBar(len(bookstoreISBNs))
    for isbn in bookstoreISBNs:
        if isbn in catalogISBNs:
            exactPrint.append(isbn)
        bar.progress()
    with open("reports/have-print-exact.csv", "w") as outfile:
        outfile.write("\n".join(exactPrint))
    bar.finish()
else:
    with open("reports/have-print-exact.csv", newline="") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            exactPrint.append(row[0]) # isbn
    exactPrint = sortUnique(exactPrint)
    print ("= Loaded exactPrint ISBNs from file (%s)" % comma(len(exactPrint)))

print ("\nFinding %s exact print matches in %s items of bookstore class data..." % (comma(len(exactPrint)), comma(len(bookstoreJSON))))
cindex = 0
with open("reserve-list.csv", "w") as writeFile:
    writeFile.write("notes,isbn,call number,title,professor,class,class name\n")
    bar = ProgressBar(len(exactPrint))
    for isbn in exactPrint:
        response = requests.get(solrURL(isbn))
        data = response.text.split("\n")
        if not data[1]:
            print ("No callnumber for %s" % isbn)
            continue
        for book in bookstoreJSON:
            if book["isbn"] == isbn:
                for course in book["classes"]:
                    writeFile.write(',%s,"%s","%s",%s,"%s","%s"\n' % (
                        isbn,   # ISBN
                        data[1], # Call number
                        book["title"],  # Title
                        course["prof"], # Professor
                        course["code"], # Class code
                        getClassName(course["code"]), # Class name
                    ))
                break
        bar.progress()
    bar.finish()
