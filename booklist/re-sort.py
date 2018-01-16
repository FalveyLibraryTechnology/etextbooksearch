import json

filename = "2018_0_spring-with-books.json"

classes = json.load(open(filename, "r"))

classes.sort(key=lambda c: c["code"], reverse=False)
classes.sort(key=lambda c: c["lowest"] * c["students"], reverse=True)
# classes.sort(key=lambda c: c["students"] if c["sum"] > 0 else -1, reverse=True)

json.dump(classes, open(filename, "w"), sort_keys=True, indent=4)
