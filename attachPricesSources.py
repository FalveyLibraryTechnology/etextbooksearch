import json
import os
import re
import requests
import string
from xlrd import open_workbook  # Excel files

from utils import comma, mapHashPath

def getPrices(filename, path):
    isbnPattern1 = re.compile(r'978(?:-?\d){10}')
    isbnPattern2 = re.compile(r'[A-Za-z]((?:-?\d){10})\D')
    isbnPattern3 = re.compile(r'[A-zA-Z]((?:-?\d){9}X)')
    isbnPattern4 = re.compile(r'a(\d{10})\D')
    priceDecPattern = re.compile(r'^[\$ ]*(?P<price>\d{2,4}\.\d{1,2})$')
    priceWholePattern = re.compile(r'^[\$ ]*(?P<price>\d{2,4})$')

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
            charPairs = 'A B C D E F G H I J K L M N O P Q R S T U V W X Y Z AAABACADAEAFAGAHAIAJAKALAMANAOAPAQARASATAUAVAWAXAYAZ'
            print ('  price column: %s' % charPairs[priceCol*2:priceCol*2+2])
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
                    for i in range(len(risbns)):
                        price = ''
                        if priceCol > -1:
                            price = rvalues[priceCol]
                        risbns[i] += ',%s,%s' % (price, filename)
                isbns.extend(risbns)
                # bar.progress()
    stripped = []
    trans = str.maketrans('','','-')
    for y in isbns:
        stripped.append(y.translate(trans))
    stripped = list(set(stripped))
    return stripped

def runFileComparison(filename):
    print ('Comparing to %s...' % filename)
    classList = {}
    # Bookstore JSON
    bookstoreJSON = []
    for file in os.listdir('BookstoreFiles'):
        with open(os.path.join('BookstoreFiles', file), 'r') as jsonFile:
            bookstoreJSON.extend(json.load(jsonFile))
    with open(mapHashPath(), "r") as map:
        mapJSON = json.load(map)
        for book in bookstoreJSON:
            if len(book['classes']) == 0:
                continue
            classList[book['isbn']] = book['classes']
            # Compare to all editions
            for isbn in mapJSON:
                if book['isbn'] == isbn:
                    for alt in mapJSON[isbn]:
                        classList[alt] = book['classes']
    with open(filename, "r") as matchFile:
        matchLines = [l.strip() for l in matchFile.readlines()] # fix new line problems
        priceRows = []
        row = 0 # ISBNs are sorted in both files, so we don't need to start from the beginning each time
        for match in matchLines:
            isbn = match[:13]
            if isbn in classList:
                match += ',%s' % ','.join(['%s---%s' % (c['code'], c['prof']) for c in classList[isbn]])
            isbnPattern = '^' + isbn
            while row < len(priceList) and not re.search(isbnPattern, priceList[row]):
                row += 1
            if row >= len(priceList):
                break
            priceRows.append(re.sub(isbnPattern, priceList[row], match))
        with open('%s-prices.csv' % filename.split('.')[0], "w") as outFile:
            outFile.write("isbn,price,source,metdata?,classes...\n")
            outFile.write("%s" % '\n'.join(priceRows))

priceList = []
if os.path.exists('hashes/prices.txt'):
    print ('Loaded from prices.txt')
    with open('hashes/prices.txt', "r") as priceFile:
        priceList = sorted([row.strip() for row in priceFile])
else:
    print ('- BookstoreFiles/')
    for file in os.listdir('BookstoreFiles'):
        print ('  %s' % file)
        with open(os.path.join('BookstoreFiles', file)) as jsonfile:
            bjson = json.load(jsonfile)
            for book in bjson:
                if 'price' in book:
                    priceList.append('%s,%s,%s' % (book['isbn'], book['price'], file))
        print ('  %s prices found' % comma(len(priceList)))
    for file in os.listdir('PublisherFiles'):
        priceList.extend(getPrices(file, 'PublisherFiles'))
    priceList = sorted(priceList)
    with open('hashes/prices.txt', "w") as priceFile:
        priceFile.write("%s" % '\n'.join(priceList))

runFileComparison('do-not-have.csv')
runFileComparison('have-drmfree.csv')
runFileComparison('have-underdrm.csv')
