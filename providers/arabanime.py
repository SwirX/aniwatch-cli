import requests
import base64
import json
import bs4
import lxml

class ArabAnime:
    def __init__(self):
        self.agent = "Mozilla/5.0 (Windows NT 6.1; Win64; rv:109.0) Gecko/20100101 Firefox/109.0"
        self.baseurl = "https://www.arabanime.net"
        self.lang = "ar"
        
    def get_popular(self, page:int = 1):
        url = self.baseurl + "/api?page=" + str(page)
        req = requests.get(url)
        encoded_data = req.json()["Shows"]
        decoded_data = []
        for encoded in encoded_data:
            decoded_data.append(json.loads(base64.b64decode(encoded).decode()))
        return decoded_data
    
    def search(self, query:str, page:int = 1):
        body = {
            "searchq": query,
        }
        req = requests.post(f"{self.baseurl}/searchq", data=body)
        soup = bs4.BeautifulSoup(req.content, "html.parser")
        soup_results = soup.select("div.show")
        results = []
        for result in soup_results:
            data = {
                "url": result.select_one("a").get("href"),
                "title": result.select_one("h3").text,
                "thumbnail_url": result.select_one("img").get("src"),
            }
            results.append(data)
        return results
    
    def get_anime_details(self, url:str ):
        req = requests.get(url)
        soup = bs4.BeautifulSoup(req.content, "html.parser")
        data = json.loads(base64.b64decode(soup.select_one("div#data").text).decode())
        s = data["show"][0]
        res = {
            "id": s["anime_id"],
            "url": url,
            "title": s["anime_name"],
            "score": s["anime_score"],
            "status": s["anime_status"],
            "type": s["anime_type"],
            "release_date": s["anime_release_date"],
            "description": s["anime_description"],
            "genres": [a for a in s["anime_genres"].split(", ")],
            "cover": s["anime_cover_image_url"],
            "slug": s["anime_slug"],
            "episodes_count": s["show_episode_count"],
        }
        return res
    
    def video_list(self, url:str ):
        req = requests.get(url)
        soup = bs4.BeautifulSoup(req.content, "html.parser")
        data = json.loads(base64.b64decode(soup.select_one("div#datawatch").text).decode())
        server = base64.b64decode(data["ep_info"][0]["stream_servers"][0]).decode()
        del req, soup
        req = requests.get(server)
        soup = bs4.BeautifulSoup(req.content, "html.parser")
        opts = []
        for opt in soup.select("option"):
            res = {
                "name": opt.text,
                "link": base64.b64decode(opt.get("data-src")).decode()
            }
            opts.append(res)
            
        print(opts)    
    
def test():
    a = ArabAnime()
    # a.search("One Punch Man")
    # print(a.get_anime_details("https://www.arabanime.net/show-2054/one-punch-man"))
    a.video_list("https://www.arabanime.net/watch-2054/one-punch-man/1")

test()