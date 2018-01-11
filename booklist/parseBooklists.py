import json
import requests
from lxml import html

def getHTML(url):
    # print (url)
    response = requests.get(url.replace("&amp;", "&"))
    return html.fromstring(response.content)

filename = "Spring2018"
classes = json.load(open("%s.json" % filename, "r"))

for index in range(43, len(classes)):
    section = classes[index]
    print (index, section["name"])
    classes[index]["books"] = []
    tree = getHTML(classes[index]["booklist"])
    isbns = [x.text_content()[6:] for x in tree.xpath("//span[contains(@id,'materialISBN')]")] # document.querySelectorAll("#materialISBN")
    prices = [x.text for x in tree.xpath("//div[@class='material-group-table']//tr[2]/td[8]")] # .print_background:nth-child(2) td.right_border
    types = [x.text.strip() for x in tree.xpath("//div[@class='material-group-table']//tr[2]/td[2]")] # .print_background:nth-child(2) td.right_border
    sum = 0
    for i in range(len(isbns)):
        price = float(prices[i][1:])
        classes[index]["books"].append({
            "isbn": isbns[i],
            "price": price,
            "type": types[i],
        })
        sum += price
    classes[index]["sum"] = sum
    classes[index]["savings"] = sum * section["students"]
    print ("\t$%s * %s = $%.2f" % (("%.2f" % classes[index]["sum"]).rjust(7), str(section["students"]).zfill(3), classes[index]["savings"]))

json.dump(classes, open("%s-with-prices.json" % filename, "w"), indent=4)
