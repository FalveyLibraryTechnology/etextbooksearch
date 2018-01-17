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

worldcat_cache = {}
if os.path.exists("hashes/worldcat.json"):
    worldcat_cache = json.load(open("hashes/worldcat.json", "r"))
def getWorldCatData(isbn, fields):
    global worldcat_cache
    worldcatAI = 'falveylibrary'

    if isbn in worldcat_cache:
        return worldcat_cache[isbn]
    print ("no cache", isbn)
    urlz = 'http://xisbn.worldcat.org/webservices/xid/isbn/'+isbn+'?method=getMetadata&fl='+fields+'&format=csv&ai='+worldcatAI
    response = requests.get(urlz)
    ret = response.text.strip()
    worldcat_cache[isbn] = ret
    return ret

callnumber_cache = {}
if os.path.exists("hashes/callnumbers.json"):
    callnumber_cache = json.load(open("hashes/callnumbers.json", "r"))
def getCallnumber(isbn):
    global callnumber_cache

    if isbn in callnumber_cache:
        return callnumber_cache[isbn]
    response = requests.get('http://hermes.library.villanova.edu:8082/solr/biblio/select?fl=callnumber-raw&wt=csv&q=isbn:"%s"' % isbn)
    data = response.text.split("\n")
    if not data[1]:
        callnumber_cache[isbn] = "n/a"
        return "n/a"
    callnumber_cache[isbn] = data[1]
    return data[1] # Call number

def getMetadata (matchingISBNs, outFileName, exact=False, addCallnumber=False, addPrices=False, match=[]):
    global bookstore_isbn_map, bookstoreJSON, full_name_map

    with open ("%s.csv" % outFileName, "w") as csvfile:
        if len(matchingISBNs) == 0:
            csvfile.write("nothing")
            return
        if addCallnumber:
            csvfile.write("CALL NUMBER,")
        for pair in match:
            col, list = pair
            print (col)
            csvfile.write("%s," % col.upper())
        fields = "isbn,year,ed,title,author,lang,url,publisher,form,city"
        csvfile.write(fields.upper())
        if addPrices:
            csvfile.write(",PRICE BUY NEW,PRICE RENT NEW")
        csvfile.write(",TOTAL ENROLLMENT,CLASS CODE,ATTENDEES,PROFESSOR NAME,PROFESSOR EMAIL,...\n")

        bar = ProgressBar(len(matchingISBNs), label='%s: %u ' % (outFileName, len(matchingISBNs)))
        for isbn in matchingISBNs:
            row = ""
            if addCallnumber:
                row += '"%s",' % getCallnumber(isbn)
            for pair in match:
                col, list = pair
                if isbn in list:
                    row += "Yes,"
                else:
                    row += ","
            # Fields
            data = getWorldCatData(isbn, fields)
            if not str(data)[:1] == '9':
                if not isbn in bookstore_isbn_map:
                    row += "%s,,,,,,,,," % isbn
                else:
                    book = bookstoreJSON[bookstore_isbn_map[isbn]]
                    row += '%s,,,"%s",,,,,,' % (isbn, book["title"])
            else:
                row += data
            if addPrices:
                prices = bookstoreJSON[bookstore_isbn_map[isbn]]["prices"]
                if "buy_new" in prices:
                    row += ",%.2f" % prices["buy_new"]
                elif "buy_used" in prices:
                    row += ",%.2f (used)" % prices["buy_rent"]
                else:
                    row += ","
                if "rent_new" in prices:
                    row += ",%.2f" % prices["rent_new"]
                elif "rent_used" in prices:
                    row += ",%.2f (used)" % prices["rent_used"]
                else:
                    row += ","
            if isbn in full_name_map:
                row += full_name_map[isbn]
            csvfile.write("%s\n" % row)
            bar.progress()
        if exact:
            bar.finish("%.3f%%" % (100 * len(matchingISBNs) / len(bookstoreISBNs)))
        else:
            bar.finish() # "%.3f%%" % (100 * len(matchingISBNs) / len(xCourseISBNs)))

# Expanded ISBNs
print ('BookstoreFiles/')
# Bookstore JSON
bookstoreISBNs = []
bookstoreJSON = []
bookstore_isbn_map = {}
for file in os.listdir(storeFilePath):
    with open(os.path.join(storeFilePath, file), 'r') as jsonFile:
        bookstoreJSON.extend(json.load(jsonFile))
for i in range(len(bookstoreJSON)):
    book = bookstoreJSON[i]
    bookstoreISBNs.append(book["isbn"])
    bookstore_isbn_map[book["isbn"]] = i

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
getMetadata (ebookMatches, "reports/have-ebooks")                  # have and open access
getMetadata (exactEbooks, "reports/have-ebooks-exact", exact=True) # exact class ebookMatches for above
getMetadata (printBooks, "reports/have-print", addCallnumber=True)                     # have and not open access: physical books, CASA catalog, restricted ebooks
getMetadata (exactPrint, "reports/have-print-exact", exact=True, addCallnumber=True)   # exact class ebookMatches for above
getMetadata (needToBuy, "reports/ebooks-available-for-purchase", exact=True) # don't have
getMetadata (noMatch, "reports/dont-have-no-ebook", exact=True)    # don't have no ebook

print ("\nGenerate difference report...")
oldname = "Archive/Spring 18 BookList by Course 12-17-17.xlsx.json"
oldisbns = []
oldjson = json.load(open(oldname, "r"))
for i in range(len(oldjson)):
    book = oldjson[i]
    if not book["isbn"]:
        continue
    isbn = int(book["isbn"])
    oldisbns.append(isbn)

newisbns = [int(x) for x in bookstoreISBNs if x]

oldisbns.sort()
newisbns.sort()

removed = []
added = []

oldindex = 0
newindex = 0
while oldindex < len(oldisbns) and newindex < len(newisbns):
    if newisbns[newindex] < oldisbns[oldindex]:
        added.append(newisbns[newindex])
        newindex += 1
    elif newisbns[newindex] > oldisbns[oldindex]:
        removed.append(oldisbns[oldindex])
        oldindex += 1
    else:
        oldindex += 1
        newindex += 1
removed.extend(oldisbns[oldindex:])
added.extend(newisbns[newindex:])

removed = [str(x) for x in removed]
added = [str(x) for x in added]

getMetadata(removed, "reports/bookstore-removed", exact=True, addCallnumber=True)
getMetadata(added, "reports/bookstore-added", exact=True, addCallnumber=True)

getMetadata (bookstoreISBNs, "reports/bookstore-list-reformatted", exact=True, addPrices=True, match=[("Added",added),("Ebook Available",needToBuy)])

json.dump(worldcat_cache, open("hashes/worldcat.json", "w"))
json.dump(callnumber_cache, open("hashes/callnumbers.json", "w"))
