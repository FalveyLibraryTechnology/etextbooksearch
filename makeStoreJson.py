import json
import os
import re
from xlrd import open_workbook  # Excel files

from ProgressBar import ProgressBar

author_col = 0
title_col = 1
isbn_col = 6

code_col = 0
prof_col = 2

def comma(num):
    return '{:,}'.format(num)

# TODO: ADD PRICES
def newBookObj(row):
    return {
        'title': row[title_col].strip(),
        'isbn': row[isbn_col].strip(),
        'classes': []
    }

for file in os.listdir('VillanovaStoreFiles'):
    print ('opening %s' % file)
    with open_workbook(os.path.join('VillanovaStoreFiles', file)) as book:
        classList = []
        bookObj = {}

        isbnPattern1 = re.compile(r'978(?:-?\d){10}')
        isbnPattern2 = re.compile(r'[A-Za-z]((?:-?\d){10})\D')
        isbnPattern3 = re.compile(r'[A-zA-Z]((?:-?\d){9}X)')
        isbnPattern4 = re.compile(r'a(\d{10})\D')

        rowTotal = 0
        #for s in range(book.nsheets):
        rowTotal += book.sheet_by_index(0).nrows
        bar = ProgressBar(rowTotal, label='parsing %s rows' % comma(rowTotal))
        #for s in range(book.nsheets):
        sheet = book.sheet_by_index(0)
        start_row = 7
        books = []
        classes = []
        for row in range(start_row, sheet.nrows):
            rvalues = sheet.row_values(row)
            # Classes before books
            if rvalues[prof_col]:
                if len(classes) > 0:
                    for bookObj in books:
                        bookObj["classes"] = classes[:]
                        classList.append(bookObj)
                    books = []
                    classes = []
                classes.append({
                    'code': rvalues[code_col].strip(),
                    'prof': rvalues[prof_col].strip(),
                })
            else:
                books.append(newBookObj(rvalues))

            '''
            # Books before classes
            risbns = []
            risbns.extend([isbnPattern1.findall(str(cell))[0] for cell in rvalues if isbnPattern1.search(str(cell))])
            risbns.extend([isbnPattern2.findall(str(cell))[0] for cell in rvalues if isbnPattern2.search(str(cell))])
            risbns.extend([isbnPattern3.findall(str(cell))[0] for cell in rvalues if isbnPattern3.search(str(cell))])
            risbns.extend([isbnPattern4.findall(str(cell))[0] for cell in rvalues if isbnPattern4.search(str(cell))])
            if len(risbns) > 0:
                if bookObj:
                    # print (bookObj)
                    classList.append(bookObj)
                bookObj = newBookObj(rvalues)
            elif not rvalues[title_col] and bookObj:
                bookObj['classes'].append({
                    'code': rvalues[code_col].strip(),
                    'prof': rvalues[prof_col]
                })
            '''
            bar.progress()
        bar.finish()

        # Consolidate
        isbn_index = {}
        newClassList = []
        for index in range(len(classList)):
            bookObj = classList[index]
            if bookObj["isbn"] in isbn_index:
                newClassList[isbn_index[bookObj["isbn"]]]["classes"].extend(bookObj["classes"])
            else:
                isbn_index[bookObj["isbn"]] = len(newClassList)
                newClassList.append(bookObj)
        classList = newClassList[:]

        print('> saving store list')
        with open('BookstoreFiles/%s.json' % file, "w") as outFile:
            json.dump(classList, outFile, separators=(',', ':'))
