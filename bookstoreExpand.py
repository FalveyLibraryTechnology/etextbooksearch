import os
import io

from utils import expandCourseISBNs, findExcelISBNs, sortUnique
from ProgressBar import ProgressBar

worldcatAI = 'falveylibrary'
storeFilePath = "BookstoreFiles"

courseISBNs = []
if os.path.exists(storeFilePath):
    print ('BookstoreFiles/')
    for storeFile in os.listdir(storeFilePath):
        courseISBNs = courseISBNs + (findExcelISBNs(storeFile,storeFilePath))
    expandCourseISBNs(courseISBNs, worldcatAI)
else:
    print ('No BookstoreFiles')
    exit(0)
