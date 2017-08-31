import json
import os
import re
from xlrd import open_workbook  # Excel files

from ProgressBar import ProgressBar
from utils import comma

# TODO: ADD PRICES
def newBookObj(row):
    return {
        'title': row[3],
        'isbn': row[11],
        'classes': []
    }

for file in os.listdir('VillanovaStoreFiles'):
    with open_workbook(os.path.join('VillanovaStoreFiles', file)) as book:
        classList = []
        bookObj = {}

        isbnPattern1 = re.compile(r'978(?:-?\d){10}')
        isbnPattern2 = re.compile(r'[A-Za-z]((?:-?\d){10})\D')
        isbnPattern3 = re.compile(r'[A-zA-Z]((?:-?\d){9}X)')
        isbnPattern4 = re.compile(r'a(\d{10})\D')

        rowTotal = 0
        for s in range(book.nsheets):
            rowTotal += book.sheet_by_index(s).nrows
        bar = ProgressBar(rowTotal, label='parsing %s rows' % comma(rowTotal))
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
                    if bookObj:
                        # print (bookObj)
                        classList.append(bookObj)
                    bookObj = newBookObj(rvalues)
                elif not rvalues[3] and bookObj:
                    bookObj['classes'].append({
                        'code': rvalues[1].strip(),
                        'prof': rvalues[4]
                    })
                bar.progress()
        bar.finish()
        print('> saving store list')
        with open('BookstoreFiles/%s.json' % file, "w") as outFile:
            json.dump(classList, outFile, separators=(',', ':'))
