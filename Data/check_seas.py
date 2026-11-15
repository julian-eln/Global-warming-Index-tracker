import urllib.request, re
def get(u):
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=10).read().decode("utf-8", "ignore")
for u in ["https://teamseas.org/", "https://teamseas.org/assets/js/page.js?v=2.1",
          "https://teamseas.org/assets/js/scripts.js?v=2.1"]:
    t = get(u)
    for m in re.finditer(r".{0,200}(liveCounter|live-counter|countUp|3[0-9],?[0-9]{3},?[0-9]{3}).{0,200}", t):
        print(f"--- {u}\n{m.group(0).strip()}\n")
