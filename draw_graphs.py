import json
import os

from src.graphs import horizontal_graph

bars = []
for file in os.scandir("hashes/reports/"):
    with open("hashes/reports/%s" % file.name) as json_report:
        parts = file.name.split("_")
        stats = json.load(json_report)
        bars.append({
            "title": "%s %s" % (parts[2][:-5].title(), parts[0]),
            "total": stats["bookstore"]["total-books"],
            "sections": [
                [stats["print"]["exact-matches"], stats["print"]["expanded-matches"]],
                [stats["ebooks"]["exact-matches"], stats["ebooks"]["expanded-matches"]],
            ],
            "labels": ["print", "ebooks"],
        })

horizontal_graph("bookstore_bars.png", bars, key=["Extended Matches", "Exact Matches"])
