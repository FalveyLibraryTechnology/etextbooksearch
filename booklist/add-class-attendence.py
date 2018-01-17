import json
import os

term = "2018_0_spring"

source = json.load(open("%s.json" % term, "r"))

storeFilePath = "../BookstoreFiles/"
bookstoreJSON = []
for file in os.listdir(storeFilePath):
    with open(os.path.join(storeFilePath, file), 'r') as jsonFile:
        bookstoreJSON.extend(json.load(jsonFile))

isbn_map = {}
full_name_map = {}
for book in bookstoreJSON:
    isbn_map[book["isbn"]] = ""
    full_name_map[book["isbn"]] = ""
    sum = 0
    for c in book["classes"]:
        parts = c["code"].split(" ")
        code = "%s %s - %s" % (parts[0], parts[1], parts[2])
        found = False
        for course in source:
            if code == course["code"]:
                found = True
                isbn_map[book["isbn"]] += ',"%s",%d,"%s"' % (c["code"], course["students"], c["prof"])
                full_name_map[book["isbn"]] += ',"%s",%d,"%s","%s"' % (c["code"], course["students"], course["prof_name"], course["prof_email"])
                sum += course["students"]
                break
        if not found:
            print (code)
    # sum of students, code, enrollment, full name, email
    full_name_map[book["isbn"]] = ",%d%s" % (sum, full_name_map[book["isbn"]])

json.dump(isbn_map, open("%s-isbn-map.json" % term, "w"), indent=4)
json.dump(full_name_map, open("%s-full-name-map.json" % term, "w"), indent=4)
