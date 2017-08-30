import io
import os
import re
import sys
import string
import requests
from checksumdir import dirhash # folder md5
from xlrd import open_workbook  # Excel files

from ProgressBar import ProgressBar

def comma(num):
    return '{:,}'.format(num)
def sortUnique(arr):
    return sorted(list(set(filter(None, arr))))

def findISBNs (filename, path):
    isbnPattern1 = re.compile(r'978(?:-?\d){10}')
    isbnPattern2 = re.compile(r'[A-Za-z]((?:-?\d){10})\D')
    isbnPattern3 = re.compile(r'[A-zA-Z]((?:-?\d){9}X)')
    isbnPattern4 = re.compile(r'a(\d{10})\D')

    isbns = []
    bytes = 0
    byteTotal = os.path.getsize(os.path.join(path, filename))
    bar = ProgressBar(byteTotal, label='- ' + filename + ' ')
    with io.open(os.path.join(path, filename), "r", encoding="ascii", errors="surrogateescape") as isbn_lines:
        for line in isbn_lines:
            isbns.extend(isbnPattern1.findall(line))
            isbns.extend(isbnPattern2.findall(line))
            isbns.extend(isbnPattern3.findall(line))
            isbns.extend(isbnPattern4.findall(line))

            bytes += len(line)
            bar.progress(bytes)
    stripped = []
    trans = str.maketrans('','','-')
    for y in isbns:
        stripped.append(y.translate(trans))
    stripped = sortUnique(stripped)
    bar.finish('found: %s' % comma(len(stripped)))
    return stripped

def findExcelISBNs (filename, path):
    isbnPattern1 = re.compile(r'978(?:-?\d){10}')
    isbnPattern2 = re.compile(r'[A-Za-z]((?:-?\d){10})\D')
    isbnPattern3 = re.compile(r'[A-zA-Z]((?:-?\d){9}X)')
    isbnPattern4 = re.compile(r'a(\d{10})\D')

    print ('- Opening %s... (Excel)' % filename)
    with open_workbook(os.path.join(path, filename)) as book:
        rowTotal = 0
        for s in range(book.nsheets):
            rowTotal += book.sheet_by_index(s).nrows
        bar = ProgressBar(rowTotal, label='  ')

        isbns = []
        for s in range(book.nsheets):
            sheet = book.sheet_by_index(s)
            for row in range(sheet.nrows):
                rvalues = sheet.row_values(row)
                for cell in rvalues:
                    isbns.extend(isbnPattern1.findall(str(cell)))
                    isbns.extend(isbnPattern2.findall(str(cell)))
                    isbns.extend(isbnPattern3.findall(str(cell)))
                    isbns.extend(isbnPattern4.findall(str(cell)))
                bar.progress()
    stripped = []
    trans = str.maketrans('','','-')
    for y in isbns:
        stripped.append(y.translate(trans))
    stripped = sortUnique(stripped)
    bar.finish('found: %s' % comma(len(stripped)))
    return stripped

def expandedHashPath():
    return 'hashes/expanded-%s.txt' % dirhash('BookstoreFiles', 'md5')
def mapHashPath():
    return 'hashes/map-%s.csv' % dirhash('BookstoreFiles', 'md5')

def expandCourseISBNs (bookstoreJSON, worldcatAI):
    courseISBNs = [str(book['isbn']) for book in bookstoreJSON] # Add the base so that when we get overlimit messages, we have something useful
    xCourseISBNs = courseISBNs[:]
    bar = ProgressBar(len(courseISBNs), label='> Downloading editions for %s ISBNs ' % comma(len(courseISBNs)))
    xMap = [];
    for isbn in courseISBNs:
        url = 'http://xisbn.worldcat.org/webservices/xid/isbn/'+isbn+'?method=getEditions&fl=isbn&format=txt&ai='+worldcatAI
        response = requests.get(url)
        risbns = response.text.split('\n')
        xCourseISBNs.extend(risbns)
        xMap.append(','.join(risbns))
        bar.progress()
    bar.finish()
    xCourseISBNs = sortUnique(xCourseISBNs)
    with open(expandedHashPath(), "w") as outfile:
        outfile.write("%s" % '\n'.join(xCourseISBNs))
    with open(mapHashPath(), "w") as outfile:
        outfile.write("%s" % '\n'.join(xMap))
    print ('- saved (%s)' % dirhash('BookstoreFiles', 'md5'))
    return xCourseISBNs
