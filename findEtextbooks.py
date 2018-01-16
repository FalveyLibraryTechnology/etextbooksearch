import datetime
import json
import os
import re
import requests
import string
from checksumdir import dirhash # folder md5
from xlrd import open_workbook  # Excel files

from src.utils import *
from src.ProgressBar import ProgressBar

currentPeriod = "2018_0_spring" # 1 for fall, 0 for spring
print ("\nCURRENT PERIOD: %s\n" % currentPeriod)

worldcatAI = 'falveylibrary'

pubFilePath = "PublisherFiles"   # DRM free available books
storeFilePath = "BookstoreFiles" # Course requirements
catFilePath = "CatalogFiles"     # What we have

def getISBNsFromFolder(foldername, prefix=''):
    isbns = []
    if os.path.exists(foldername):
        print ('\n%s/' % foldername)
        hash = dirhash(foldername, 'md5')
        hashFile = 'hashes/%s-%s.txt' % (prefix, hash)
        print ('= %s' % hash)
        if not os.path.exists(hashFile):
            for file in os.listdir(foldername):
                ext = file[-4:].lower()
                if ext == '.xls' or ext == 'xlsx':
                    isbns = isbns + (findExcelISBNs(file, foldername)) # EXCEL
                else:
                    isbns = isbns + (findISBNs(file, foldername))
            isbns = sortUnique(isbns)
            with open(hashFile, "w") as hashFile:
                hashFile.write("%s" % '\n'.join(isbns))
            return isbns
        else:
            with open(hashFile, "r") as hashw:
                isbns = [isbn.strip() for isbn in hashw]
                print ('= Loaded %s from file (%s)' % (foldername, comma(len(isbns))))
                return isbns
    else:
        print ('\nNo %s' % foldername)
        return []

def getCallnumber(isbn):
    response = requests.get('http://hermes.library.villanova.edu:8082/solr/biblio/select?fl=callnumber-raw&wt=csv&q=isbn:"%s"' % isbn)
    data = response.text.split("\n")
    if not data[1]:
        return "N/A"
    return data[1] # Call number

def getMetadata (matchingISBNs, outFileName, exact=False, addClasses=True, addCallnumber=False, addFull=False):
    global bookstoreISBNs, bookstoreJSON, isbn_class_map

    with open ("%s.csv" % outFileName, "w") as csvfile:
        if len(matchingISBNs) == 0:
            csvfile.write("nothing")
            return
        if addCallnumber:
            csvfile.write("CALL NUMBER,")
        fields = 'isbn,year,ed,title,author,lang,url,publisher,form,city'
        csvfile.write(fields.upper())
        if addClasses:
            csvfile.write(",CLASS CODE,ATTENDEES,PROFESSOR NAME")
            if addFull:
                csvfile.write(",PROF FULL NAME,PROF EMAIL")
            csvfile.write(",...")
        csvfile.write("\n")
        bar = ProgressBar(len(matchingISBNs), label='%s: %u ' % (outFileName, len(matchingISBNs)))
        for isbn in matchingISBNs:
            urlz = 'http://xisbn.worldcat.org/webservices/xid/isbn/'+isbn+'?method=getMetadata&fl='+fields+'&format=csv&ai='+worldcatAI
            response = requests.get(urlz)
            row = response.text.strip()
            if not str(response.text)[:1] == '9':
                if not isbn in bookstoreISBNs:
                    row = "%s,,,,,,,,," % isbn
                else:
                    for book in bookstoreJSON:
                        if book["isbn"] == isbn:
                            row = '%s,,,"%s",,,,,,' % (isbn, book["title"])
                            break
            if addClasses:
                if addFull:
                    if isbn in full_name_map:
                        row += full_name_map[isbn]
                    elif isbn in isbn_class_map:
                        row += isbn_class_map[isbn]
                elif isbn in isbn_class_map:
                    row += isbn_class_map[isbn]
            if addCallnumber:
                csvfile.write('"%s",' % getCallnumber(isbn))
            csvfile.write("%s\n" % str(row).strip())
            bar.progress()
        if exact:
            bar.finish("%.3f%%" % (100 * len(matchingISBNs) / len(bookstoreISBNs)))
        else:
            bar.finish("%.3f%%" % (100 * len(matchingISBNs) / len(xCourseISBNs)))

# Expanded ISBNs
print ('BookstoreFiles/')
# Bookstore JSON
bookstoreISBNs = []
bookstoreJSON = []
for file in os.listdir(storeFilePath):
    with open(os.path.join(storeFilePath, file), 'r') as jsonFile:
        bookstoreJSON.extend(json.load(jsonFile))
bookstoreISBNs = [x['isbn'] for x in bookstoreJSON]

expandedHashFile = expandedHashPath()
print ('= %s' % expandedHashFile)
if not os.path.exists(expandedHashFile):
    xCourseISBNs = expandCourseISBNs(bookstoreJSON, worldcatAI)
else:
    with open(expandedHashFile, "r") as courseFile:
        xCourseISBNs = [book.strip() for book in courseFile]
    print ('> Editions loaded from file (%s)' % comma(len(xCourseISBNs)))

pubISBNs = getISBNsFromFolder(pubFilePath, prefix='pub')

catISBNs = getISBNsFromFolder(catFilePath, prefix='cat')

print ("\n= Load class data...\n")
isbn_class_map = json.load(open("booklist/%s-isbn-map.json" % currentPeriod, "r"))
full_name_map = json.load(open("booklist/%s-full-name-map.json" % currentPeriod, "r"))

# match the files
#   needToBuy in pubFile but not cat
#   printBooks in cat but not pubfile
#   ebookMatches in pubfile and cat
bar = ProgressBar(
    len(xCourseISBNs),
    label='Looking for %s ISBNs in a pool of %s ' % (
        comma(len(xCourseISBNs)),
        comma(len(pubISBNs) + len(catISBNs))
    )
)


ebookMatches = []
exactEbooks = []
printBooks = []
exactPrint = []
needToBuy = []
noMatch = []
catIndex = 0
pubIndex = 0
for isbn in xCourseISBNs:
    bar.progress()
    while catIndex < len(catISBNs) and isbn > catISBNs[catIndex]:
        catIndex += 1
    while pubIndex < len(pubISBNs) and isbn > pubISBNs[pubIndex]:
        pubIndex += 1
    inCatalog = catIndex < len(catISBNs) and isbn == catISBNs[catIndex]
    inBookstoreList = isbn in bookstoreISBNs
    if pubIndex < len(pubISBNs) and isbn == pubISBNs[pubIndex]:
        if inCatalog:
            if inBookstoreList:
                exactEbooks.append(isbn)
            ebookMatches.append(isbn)
        elif inBookstoreList:
            needToBuy.append(isbn)
    elif inCatalog:
        if inBookstoreList:
            exactPrint.append(isbn)
        printBooks.append(isbn)
    elif inBookstoreList:
        noMatch.append(isbn)

bar.finish()
'''
for isbn in needToBuy:
    print (isbn, isbn in isbn_class_map)
'''
print ("\nSaving Report for posterity...")
if not os.path.exists("hashes/reports/"):
    os.mkdir("hashes/reports/")
if os.path.exists("hashes/reports/%s.json" % currentPeriod):
    currentPeriod += datetime.datetime.now().strftime("_%y_%m_%d")
with open ("hashes/reports/%s.json" % currentPeriod, "w") as hashreport:
    report = {
        "bookstore": {
            "total-books": len(bookstoreJSON),
            "expanded": len(xCourseISBNs),
        },
        "ebooks": {
            "exact-matches": len(exactEbooks),
            "expanded-matches": len(ebookMatches),
        },
        "hashes": {
            "catalog": "hashes/cat-%s.txt" % dirhash("CatalogFiles", "md5"),
            "expanded": expandedHashPath(),
            "map": mapHashPath(),
            "publishers": "hashes/pub-%s.txt" % dirhash("PublisherFiles", "md5"),
        },
        "no-matches": noMatch,
        "print": {
            "exact-matches": len(exactPrint),
            "expanded-matches": len(printBooks),
        },
    }
    json.dump(report, hashreport, sort_keys=True, indent=4)

print ("\nPrinting results...")
if not os.path.exists("reports/"):
    os.mkdir("reports/")
getMetadata (ebookMatches, "reports/have-ebooks", addFull=True)                  # have and open access
getMetadata (exactEbooks, "reports/have-ebooks-exact", exact=True, addFull=True) # exact class ebookMatches for above
getMetadata (printBooks, "reports/have-print", addCallnumber=True)                     # have and not open access: physical books, CASA catalog, restricted ebooks
getMetadata (exactPrint, "reports/have-print-exact", exact=True, addCallnumber=True)   # exact class ebookMatches for above
getMetadata (needToBuy, "reports/ebooks-available-for-purchase", exact=True) # don't have
getMetadata (noMatch, "reports/dont-have-no-ebook", exact=True)    # don't have no ebook
getMetadata (bookstoreISBNs, "reports/bookstore-list-reformatted", exact=True)    # don't have no ebook
# print ('no matches: %s (%.3f%%)\n' % (comma(len(noMatch)), 100 * len(noMatch) / len(bookstoreISBNs)))
