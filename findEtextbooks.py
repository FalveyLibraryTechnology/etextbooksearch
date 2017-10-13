import json
import os
import re
import requests
import string
from checksumdir import dirhash # folder md5
from xlrd import open_workbook  # Excel files

from utils import *
from ProgressBar import ProgressBar

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

def getMetadata (matchingISBNs, outFileName):
    with open (outFileName, "w") as csvfile:
        if len(matchingISBNs) == 0:
            csvfile.write("nothing")
            return
        fields = 'isbn,year,ed,title,author,lang,url,publisher,form,city'
        for isbn in matchingISBNs:
            urlz = 'http://xisbn.worldcat.org/webservices/xid/isbn/'+isbn+'?method=getMetadata&fl='+fields+'&format=csv&ai='+worldcatAI
            response = requests.get(urlz)
            if not str(response.text)[:1] == '9':
                csvfile.write("%s\n" % isbn)
            else:
                csvfile.write("%s\n" % str(response.text).strip())

# Expanded ISBNs
print ('BookstoreFiles/')
expandedHashFile = expandedHashPath()
print ('= %s' % expandedHashFile)
if not os.path.exists(expandedHashFile):
    # Bookstore JSON
    bookstoreJSON = []
    for file in os.listdir(storeFilePath):
        with open(os.path.join(storeFilePath, file), 'r') as jsonFile:
            bookstoreJSON.extend(json.load(jsonFile))
    xCourseISBNs = expandCourseISBNs(bookstoreJSON, worldcatAI)
else:
    with open(expandedHashFile, "r") as courseFile:
        xCourseISBNs = [book.strip() for book in courseFile]
    print ('> Editions loaded from file (%s)' % comma(len(xCourseISBNs)))

pubISBNs = getISBNsFromFolder(pubFilePath, prefix='pub')

catISBNs = getISBNsFromFolder(catFilePath, prefix='cat')

# match the files
# needToBuy in pubFile but not cat, notDRMfree in cat but not pubfile, matches in pubfile and cat
matches = []
notDRMfree = []
needToBuy = []
noMatch = 0
bar = ProgressBar(
    len(xCourseISBNs),
    label='Looking for %s ISBNs in a pool of %s ' % (
        comma(len(xCourseISBNs)),
        comma(len(pubISBNs) + len(catISBNs))
    )
)

catIndex = 0
pubIndex = 0
for x in xCourseISBNs:
    bar.progress()
    while catIndex < len(catISBNs) and x > catISBNs[catIndex]:
        catIndex += 1
    while pubIndex < len(pubISBNs) and x > pubISBNs[pubIndex]:
        pubIndex += 1
    inCats = catIndex < len(catISBNs) and x == catISBNs[catIndex]
    if pubIndex < len(pubISBNs) and x == pubISBNs[pubIndex]:
        if inCats:
            matches.append(x)
        else:
            needToBuy.append(x)
    elif inCats:
        notDRMfree.append(x)
    else:
        noMatch = noMatch + 1

bar.finish('no match: %s\n' % comma(noMatch))

getMetadata (matches, "have-ebooks.csv")     # have and open access
print ('have-ebooks: %u' % len(matches))
getMetadata (needToBuy, "available-ebooks.csv")    # don't have
print ('available-ebooks: %u' % len(needToBuy))
getMetadata (notDRMfree, "have-print.csv") # have and not open access: physical books, CASA catalog, restricted ebooks
print ('have-print: %u' % len(notDRMfree))

