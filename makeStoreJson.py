import json
import os
import re
from xlrd import open_workbook  # Excel files

from ProgressBar import ProgressBar

def comma(num):
    return '{:,}'.format(num)

author_col = 0
title_col = 2
isbn_col = 8 # 6
buy_new_col = 12
buy_used_col = 13
rent_new_col = 14
rent_used_col = 15

code_col = 0
prof_col = 3 # 2

is_book_col = title_col

# TODO: ADD PRICES
def newBookObj(row):
    prices = {}
    if row[buy_new_col]:
        prices["buy_new"] = row[buy_new_col]
    if row[buy_used_col]:
        prices["buy_used"] = row[buy_used_col]
    if row[rent_new_col]:
        prices["rent_new"] = row[rent_new_col]
    if row[rent_used_col]:
        prices["rent_used"] = row[rent_used_col]
    return {
        'title': row[title_col].strip(),
        'isbn': row[isbn_col].strip(),
        'prices': prices,
        'classes': []
    }

for file in os.listdir('VillanovaStoreFiles'):
    print ('opening %s' % file)
    with open_workbook(os.path.join('VillanovaStoreFiles', file)) as book:
        classList = []
        bookObj = {}

        rowTotal = 0
        #for s in range(book.nsheets):
        rowTotal += book.sheet_by_index(0).nrows
        bar = ProgressBar(rowTotal, label='parsing %s rows' % comma(rowTotal))
        #for s in range(book.nsheets):
        sheet = book.sheet_by_index(0)
        books = []
        classes = []
        for row in range(8, sheet.nrows): # start row
            rvalues = sheet.row_values(row)

            '''
            # By Course
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

            # By Author
            if rvalues[is_book_col]:
                if bookObj:
                    # print (bookObj)
                    classList.append(bookObj)
                bookObj = newBookObj(rvalues)
            elif not rvalues[is_book_col] and bookObj:
                bookObj['classes'].append({
                    'code': rvalues[code_col].strip(),
                    'prof': rvalues[prof_col]
                })

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
