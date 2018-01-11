import json

filename = "Spring2018-with-prices.json"

classes = json.load(open(filename, "r"))

classes.sort(key=lambda c: c["students"] if c["sum"] > 0 else -1, reverse=True)

json.dump(classes, open(filename, "w"), sort_keys=True, indent=4)
