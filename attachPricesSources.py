import os
import io
import sys
import re
import string
import requests
from xlrd import open_workbook  # Excel files

from utils import comma, mapHashPath

def getPrices(filename, path, saveClasses = False):
    isbnPattern1 = re.compile(r'978(?:-?\d){10}')
    isbnPattern2 = re.compile(r'[A-Za-z]((?:-?\d){10})\D')
    isbnPattern3 = re.compile(r'[A-zA-Z]((?:-?\d){9}X)')
    isbnPattern4 = re.compile(r'a(\d{10})\D')
    priceDecPattern = re.compile(r'^[\$ ]*(?P<price>\d{2,4}\.\d{1,2})$')
    priceWholePattern = re.compile(r'^[\$ ]*(?P<price>\d{2,4})$')

    classList = []
    nextISBN = ''

    isbns = []
    print ('- %s... (opening Excel file)' % filename)
    with open_workbook(os.path.join(path, filename)) as book:
        # Determine price column
        # print ('  finding price column...')
        priceCol = -1
        rowRange = 200
        matchMax = 50 # Minimum match (prices should be saturated)
        for s in range(book.nsheets):
            sheet = book.sheet_by_index(s)
            for col in range(sheet.ncols):
                cvalues = sheet.col_values(col, 0, rowRange) # first x rows for sample
                matches = 0
                for i in range(len(cvalues)):
                    cvalue = str(cvalues[i])
                    m = priceDecPattern.match(cvalue)
                    prize = 1
                    if m: # extra credit for decimal numbers
                        prize = 2
                    else:
                        m = priceWholePattern.match(cvalue)
                    if m:
                        np = float(m.group('price'))
                        if np > 1900 and np <= 2018: # Exclude dates
                            m = False
                    if m:
                        matches += prize
                if matches > matchMax:
                    priceCol = col
                    matchMax = matches
        if priceCol > -1:
            print ('  price column: %s' % 'A B C D E F G H I J K L M N O P Q R S T U V W X Y Z AAABACADAEAFAGAHAIAJAKALAMANAOAPAQARASATAUAVAWAXAYAZ'[priceCol*2:priceCol*2+2], matchMax)
        else:
            print ('  no price column')
        #
        rowTotal = 0
        for s in range(book.nsheets):
            rowTotal += book.sheet_by_index(s).nrows
        print ('  parsing %s rows...' % comma(rowTotal))
        # bar = ProgressBar(rowTotal, label='  ')
        for s in range(book.nsheets):
            sheet = book.sheet_by_index(s)
            for row in range(sheet.nrows):
                risbns = []
                rvalues = sheet.row_values(row)
                risbns.extend([isbnPattern1.findall(str(cell))[0] for cell in rvalues if isbnPattern1.search(str(cell))])
                risbns.extend([isbnPattern2.findall(str(cell))[0] for cell in rvalues if isbnPattern2.search(str(cell))])
                risbns.extend([isbnPattern3.findall(str(cell))[0] for cell in rvalues if isbnPattern3.search(str(cell))])
                risbns.extend([isbnPattern4.findall(str(cell))[0] for cell in rvalues if isbnPattern4.search(str(cell))])
                if len(risbns) > 0:
                    if saveClasses and nextISBN:
                        # print (nextISBN)
                        classList.append(nextISBN)
                        nextISBN = risbns[0].split('.')[0]
                    for i in range(len(risbns)):
                        if priceCol >= 0:
                            risbns[i] += ',%s,%s,%u' % (rvalues[priceCol], filename, row + 1)
                        else:
                            risbns[i] += ',,%s,%u' % (filename, row + 1)
                elif saveClasses and not rvalues[3]:
                    nextISBN += ',%s---%s' % (rvalues[1].strip(), rvalues[4])
                isbns.extend(risbns)
                # bar.progress()
    stripped = []
    trans = str.maketrans('','','-')
    for y in isbns:
        stripped.append(y.translate(trans))
    stripped = list(set(stripped))
    # bar.finish('found: %s' % comma(len(stripped)))
    if saveClasses:
        print('> saving class list')
        with open('class-list.csv', "w") as outFile:
            outFile.write("%s" % '\n'.join(classList[1:]))
    return stripped

def runFileComparison(filename):
    print ('Comparing to %s...' % filename)
    classList = {}
    with open('class-list.csv', "r") as listcsv:
        with open(mapHashPath(), "r") as map:
            mapLines = map.readlines()
            for row in listcsv:
                isbn = row[:13]
                classes = row[13:]
                classList[isbn] = classes
                # Compare to all editions
                for set in mapLines:
                    if isbn == set[:13]:
                        alts = set[14:].strip(',\n').split(',')
                        for alt in alts:
                            classList[alt] = classes
    with open(filename, "r") as dnhFile:
        dnhLines = dnhFile.readlines()
        dnhCount = len(dnhLines)
        priceRows = []
        row = 0 # ISBNs are sorted in both files, so we don't need to start from the beginning each time
        isbn = dnhLines[row][:13]
        isbnPattern = '^' + isbn
        if isbn in classList:
            dnhLines[row] += classList[isbn]
        for p in range(len(priceList)):
            if re.search(isbnPattern, priceList[p]):
                priceRows.append(re.sub(isbnPattern, priceList[p], dnhLines[row]))
                row += 1
                if row >= dnhCount:
                    break
                isbn = dnhLines[row][:13]
                isbnPattern = '^' + isbn
                if isbn in classList:
                    dnhLines[row] += classList[isbn]
        for i in range(row, dnhCount):
            priceRows.append(dnhLines[i])
        with open('%s-prices.csv' % filename.split('.')[0], "w") as outFile:
            outFile.write("%s" % ''.join(priceRows))

priceList = []
if os.path.exists('hashes/prices.txt'):
    print ('Loaded from prices.txt')
    with open('hashes/prices.txt', "r") as priceFile:
        priceList = sorted([row.strip() for row in priceFile])
else:
    # priceList = getPrices('Springer_eBook_list_20170710_165150.xlsx', 'PublisherFiles')
    # exit(0)
    priceList = getPrices('Fall BookList 7-25-2017 (Library).xlsx', 'BookstoreFiles', saveClasses = True)
    for file in os.listdir('PublisherFiles'):
        priceList.extend(getPrices(file, 'PublisherFiles'))
    priceList = sorted(priceList)
    with open('hashes/prices.txt', "w") as priceFile:
        priceFile.write("%s" % '\n'.join(priceList))

runFileComparison('do-not-have.csv')
runFileComparison('have-drmfree.csv')
runFileComparison('have-underdrm.csv')
