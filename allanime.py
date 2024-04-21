import json
import requests


class AllAnime:
    def __init__(self):
        #variables*
        self.agent="Mozilla/5.0 (Windows NT 6.1; Win64; rv:109.0) Gecko/20100101 Firefox/109.0"
        self.allanime_api = "https://api.allanime.day"
        self.allanime_base="https://allanime.to"
        self.mode = "sub"
        self.quality = "best"
        self.download_dir = "."
        self.histfile = "ani-hsts"
        self.skip = False
        
        # other
        self.endpoint = requests.get(self.allanime_base + "/getVersion").json()["episodeIframeHead"]
        
        self.internalLinks = [
            "Luf-mp4",
            "Sak",
            # "Yt-mp4",
            "Default",
            "S-mp4",
            "Ak"
        ]
        
        # queries
        self.popular_query = """
            query(
                    $type: VaildPopularTypeEnumType!
                    $size: Int!
                    $page: Int
                    $dateRange: Int
                ) {
                queryPopular(
                    type: $type
                    size: $size
                    dateRange: $dateRange
                    page: $page
                ) {
                    total
                    recommendations {
                        anyCard {
                            _id
                            name
                            thumbnail
                            englishName
                            slugTime
                        }
                    }
                }
            }
        """
        self.searchQuery = """
            query(
                $search: SearchInput
                $limit: Int
                $page: Int
                $translationType: VaildTranslationTypeEnumType
                $countryOrigin: VaildCountryOriginEnumType
            ) {
                shows(
                    search: $search
                    limit: $limit
                    page: $page
                    translationType: $translationType
                    countryOrigin: $countryOrigin
                ) {
                    pageInfo {
                        total
                    }
                    edges {
                        _id
                        name
                        thumbnail
                        englishName
                        slugTime
                    }
                }
            }
        """
        self.details_query = """
            query ($_id: String!) {
                show(
                    _id: $_id
                ) {
                    thumbnail
                    description
                    type
                    season
                    score
                    genres
                    status
                    studios
                }
            }
        """
        self.episodes_query = """
            query ($_id: String!) {
                show(
                    _id: $_id
                ) {
                    _id
                    availableEpisodesDetail
                }
            }
        """
        self.streams_query = """
            query(
                $showId: String!,
                $translationType: VaildTranslationTypeEnumType!,
                $episodeString: String!
            ) {
                episode(
                    showId: $showId
                    translationType: $translationType
                    episodeString: $episodeString
                ) {
                    sourceUrls
                }
            }
        """
    
    
    def decrypt(self, provider_id) -> str:
        decrypted = ''
        for hex_value in [provider_id[i:i+2] for i in range(0, len(provider_id), 2)]:
            dec = int(hex_value, 16)
            xor = dec ^ 56
            oct_value = oct(xor)[2:].zfill(3)
            decrypted += chr(int(oct_value, 8))
        return decrypted
    
    def isInternal(self, link:str) -> bool:
        return link in self.internalLinks
    
    def get_popular(self, page:int):
        resp = requests.get(
            f"{self.allanime_api}/api",
            params={
                "variables": json.dumps({
                    "type": "anime",
                    "size": 26,
                    "dateRange": 7,
                    "page": page
                }),
                "query": self.popular_query
            },
            headers={
                "Referer": self.allanime_base,
                "User-Agent": self.agent
            }
        )
        
        return resp.json()["data"]["queryPopular"]["recommendations"]
    
    def get_latest_update(self, page: int):
        resp = requests.get(
            f"{self.allanime_api}/api",
            params={
                "variables": json.dumps({
                    "search": {
                        "allowAdult": False,
                        "allowUnknown": False,
                    },
                    "limit": 26,
                    "page": page,
                    "translationType": self.mode,
                    "countryOrigin": "ALL"
                }),
                "query": self.searchQuery
            },
            headers={
                "Referer": self.allanime_base,
                "User-Agent": self.agent
            }
        )
        
        return resp.json()["data"]["shows"]["edges"]
    
    def get_search(self, page: int, query: str):
        resp = requests.get(
            f"{self.allanime_api}/api",
            params={
                "variables": json.dumps({
                    "search": {
                        "query": query,
                        "allowAdult": False,
                        "allowUnknown": False,
                    },
                    "limit": 26,
                    "page": page,
                    "translationType": self.mode,
                    "countryOrigin": "ALL"
                }),
                "query": self.searchQuery
            },
            headers={
                "Referer": self.allanime_base,
                "User-Agent": self.agent
            }
        )
        
        return resp.json()["data"]["shows"]["edges"]
    
    def get_anime_details(self, anime_id: str):
        resp = requests.get(
            f"{self.allanime_api}/api",
            params={
                "variables": json.dumps({
                    "_id": anime_id
                }),
                "query": self.details_query
            },
            headers={
                "Referer": self.allanime_base,
                "User-Agent": self.agent
            }
        )
        
        return resp.json()["data"]["show"]
    
    def get_episodes_list(self, anime_id: str):
        resp = requests.get(
            f"{self.allanime_api}/api",
            params={
                "variables": json.dumps({
                    "_id": anime_id
                }),
                "query": self.episodes_query
            },
            headers={
                "Referer": self.allanime_base,
                "User-Agent": self.agent
            }
        )
        
        return resp.json()["data"]["show"]["availableEpisodesDetail"][self.mode]
    
    def get_episode_streams(self, anime_id: str, episode_num: int) -> list:
        resp = requests.get(
            f"{self.allanime_api}/api",
            params={
                "variables": json.dumps({
                    "showId": anime_id,
                    "translationType": self.mode,
                    "episodeString": f"{episode_num}"
                }),
                "query": self.streams_query
            },
            headers={
                "Referer": self.allanime_base,
                "User-Agent": self.agent
            }
        )
        
        return resp.json()["data"]["episode"]["sourceUrls"]
    
    def get_video_from_url(self, url: str, name: str) -> dict:
        decryptedUrl = self.decrypt(url.replace("--", ""))
        print(decryptedUrl)
        resp = requests.get(self.endpoint + decryptedUrl.replace("/clock?", "/clock.json?"))
        if resp.status_code!= 200:
            return None
        links = resp.json()["links"]
        return links
    
    def get_video_list(self, anime_id: str, episode_num: int):
        episode_streams = self.get_episode_streams(anime_id, episode_num)
        video_list = []
        for stream in episode_streams:
            if self.isInternal(stream["sourceName"]):
                print(f"{stream['sourceName']} is internal")
                links = self.get_video_from_url(stream["sourceUrl"], stream["sourceName"])
                print(links)
                video_list.append(links)
        
        return video_list
    


def test():
    a = AllAnime()
    print(a.get_video_list("vDTSJHSpYnrkZnAvG", 1))
    # AllAnime().get_video_from_url("175948514e4c4f57175b54575b5307515c050f5c0a0c0f0b0f0c0e590a0c0b5b0a0c0a010e5a0e0b0e0a0e5e0e0f0b0d0a010f080e5e0e0a0e0b0e010f0d0a010f080c0a0d0a0d0d0c5b0c5d0d0d0f0e0d5e0e000f0c0e5c0d5b0e000c0f0f080c090a010f0d0f0b0e0c0a010b0f0a0c0a590a0c0f0d0f0a0f0c0e0b0e0f0e5a0e0b0f0c0c5e0e0a0a0c0b5b0a0c0c0a0f0c0e010f0e0e0c0e010f5d0a0c0a590a0c0e0a0e0f0f0a0e0b0a0c0b5b0a0c0b0c0b0e0b0c0b0a0a5a0b0e0b0a0a5a0b0c0b0f0d0a0b0c0b0c0b5b0b0f0b0e0b5b0b0e0b0e0a000b0e0b0e0b0e0d5b0a0c0a590a0c0f0a0f0c0e0f0e000f0d0e590e0f0f0a0e5e0e010e000d0a0f5e0f0e0e0b0a0c0b5b0a0c0f0d0f0b0e0c0a0c0a590a0c0e5c0e0b0f5e0a0c0b5b0a0c0e0b0f0e0a5a0a010e5a0e0b0e0a0e5e0e0f0b0d0a010f080e5e0e0a0e0b0e010f0d0a010f080c0a0d0a0d0d0c5b0c5d0d0d0f0e0d5e0e000f0c0e5c0d5b0e000c0f0f080c090a010f0d0f0b0e0c0a010b0f0a0c0f5a", "Luf-mp4")

test()