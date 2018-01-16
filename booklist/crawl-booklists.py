import json
import requests
import time
from lxml import html

def getHTML(url):
    # print (url)
    response = requests.get(url.replace("&amp;", "&"))
    return html.fromstring(response.content)

filename = "2018_0_spring"
classes = json.load(open("%s.json" % filename, "r"))

polite_delay = 3

for index in range(0, len(classes)):
    section = classes[index]
    print (index, len(classes), section["code"])
    classes[index]["books"] = []
    tree = getHTML(classes[index]["booklist"])
    isbns = [x.text_content()[6:] for x in tree.xpath("//span[contains(@id,'materialISBN')]")] # document.querySelectorAll("#materialISBN")
    prices = [x.text for x in tree.xpath("//div[@class='material-group-table']//tr[2]/td[8]")] # .print_background:nth-child(2) td.right_border
    types = [x.text.strip() for x in tree.xpath("//div[@class='material-group-table']//tr[2]/td[2]")] # .print_background:nth-child(2) td.right_border
    sum = 0
    lowest = 99999
    highest = 0
    for i in range(len(isbns)):
        price = float(prices[i][1:])
        if price < lowest:
            lowest = price
        if price > highest:
            highest = price
        classes[index]["books"].append({
            "isbn": isbns[i],
            "price": price,
            "type": types[i],
        })
        sum += price
    classes[index]["lowest"] = lowest
    classes[index]["highest"] = highest
    classes[index]["sum"] = sum
    time.sleep (polite_delay)

json.dump(classes, open("%s-with-books.json" % filename, "w"), indent=4)
