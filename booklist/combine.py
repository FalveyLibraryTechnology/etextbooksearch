import json

filename = "2018_0_spring"

source = json.load(open("%s.json" % filename, "r"))
classes = json.load(open(filename, "r"))

for i in range(len(classes)):
    print (classes[i]["code"], source[i]["code"])
    if classes[i]["code"] != source[i]["code"]:
        print ("panic")
        exit()
    classes[i]["prof_email"] = source[i]["prof_email"]
    classes[i]["prof_name"] = source[i]["prof_name"]

json.dump(classes, open("%s-by-class.json" % filename, "w"), indent=4)
