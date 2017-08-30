import os
import io

from utils import expandCourseISBNs, findExcelISBNs, sortUnique
from ProgressBar import ProgressBar

worldcatAI = 'falveylibrary'
storeFilePath = "BookstoreFiles"

courseISBNs = []
if os.path.exists(storeFilePath):
    print ('BookstoreFiles/')
    bookstoreJSON = []
    for file in os.listdir(storeFilePath):
        with open(os.path.join(storeFilePath, file), 'r') as jsonFile:
            bookstoreJSON.extend(json.load(jsonFile))
    expandCourseISBNs(bookstoreJSON, worldcatAI)
else:
    print ('No BookstoreFiles')
