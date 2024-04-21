import json
import os
import re
import subprocess
import sys
import time
import requests
from dotenv import load_dotenv

import aniskip

download = False
agent="Mozilla/5.0 (Windows NT 6.1; Win64; rv:109.0) Gecko/20100101 Firefox/109.0"
allanime_base="https://allanime.to"
allanime_api="https://api.allanime.day"
mode = "sub"
quality = "best"
download_dir = "."
version_number="0.1.3"
histfile = "ani-hsts"
skip = False

load_dotenv()

def die(out:str) -> None:
    print(out)
    exit(0)

def help_info():
    print("""
    Usage:
    """ + sys.argv[0] + """ [options] [query]
    """ + sys.argv[0] + """ [query] [options]
    """ + sys.argv[0] + """ [options] [query] [options]

    Options:
      -c, --continue
        Continue watching from history
      -d, --download
        Download the video instead of playing it
      -D, --delete
        Delete history
      -s, --syncplay
        Use Syncplay to watch with friends
      -S, --select-nth
        Select nth entry
      -q, --quality
        Specify the video quality
      -v, --vlc
        Use VLC to play the video
      -V, --version
        Show the version of the script
      -h, --help
        Show this help message and exit
      -e, --episode, -r, --range
        Specify the number of episodes to watch
      --dub
        Play dubbed version
      --rofi
        Use rofi instead of fzf for the interactive menu
      -U, --update
        Update the script
    Some example usages:
      """ + sys.argv[0] + """ -q 720p banana fish
      """ + sys.argv[0] + """ -d -e 2 cyberpunk edgerunners
      """ + sys.argv[0] + """ --vlc cyberpunk edgerunners -q 1080p -e 4
      """ + sys.argv[0] + """ blue lock -e 5-6
      """ + sys.argv[0] + """ -e \"5 6\" blue lock
    \n" "${0##*/}" "${0##*/}" "${0##*/}" "${0##*/}" "${0##*/}" "${0##*/}" "${0##*/}" "${0##*/}""")
    exit(0)

def version_info() -> None:
    print(sys.argv[0] + "\n" f"{version_number}")
    exit(0)
    
def update() -> None:
    print("checking for updates")
    req = requests.get("https://raw.githubusercontent.com/SwirX/aniwatch-cli/master/animefetch.py")
    if not req:
        die("couldn't check for updates")
        return
    with open("update", "w+") as update:
        update.write(req.text)
    os.system(f"python update.py {version_number}")
    exit(0)

def dl_aniskip(force=False):
    if os.path.isfile("aniskip.py") and os.path.isfile(f"{os.getenv("APPDATA")}/mpv/scripts/skip.lua") and not force:
        print("Not downloaded. The files already exist.")
        return
    if force:
        print("[FORCED DOWNLOAD]")
    print("downloading ani-skip.py and skip.lua")
    aniskip = requests.get("https://raw.githubusercontent.com/SwirX/aniwatch-cli/master/aniskip.py").text
    skip = requests.get("https://raw.githubusercontent.com/SwirX/aniwatch-cli/master/skip.lua").text
    if aniskip == "" and skip == "":
        die("couldn't get the files")
    with open("aniskip.py", "w+") as aniskipfile:
        aniskipfile.write(aniskip)
    with open(f'{os.getenv("APPDATA")}/mpv/scripts/skip.lua', "w+") as skipfile:
        skipfile.write(skip)
    
def provider_init(resp, regex):
    match = re.search(regex, resp)
    if match:
        provider_id = match.group(1)
        return provider_id
    return None

def decrypt_allanime(provider_id) -> str:
    decrypted = ''
    for hex_value in [provider_id[i:i+2] for i in range(0, len(provider_id), 2)]:
        dec = int(hex_value, 16)
        xor = dec ^ 56
        oct_value = oct(xor)[2:].zfill(3)
        decrypted += chr(int(oct_value, 8))
    return decrypted

def search_anime(query) -> list:
    search_gql = '''
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
            edges {
                _id
                malId
                aniListId
                name
                availableEpisodes
                banner
                thumbnail
                episodeCount
                rating
                score
                status
                genres
                tags
                __typename
            }
        }
    }
    '''
    resp = requests.get(
        f"{allanime_api}/api",
        params={
            "variables": json.dumps({
                "search": {
                    "allowAdult": False,
                    "allowUnknown": False,
                    "query": query
                },
                "limit": 40,
                "page": 1,
                "translationType": mode,
                "countryOrigin": "ALL"
            }),
            "query": search_gql
        },
        headers={
            "Referer": allanime_base,
            "User-Agent": agent
        }
    ).json()
    die(resp)
    anime_list = []
    if "data" in resp and "shows" in resp["data"]:
        for edge in resp["data"]["shows"]["edges"]:
            animeid = edge["_id"]
            animename = edge["name"]
            availables_episodes = edge["availableEpisodes"]
            anime_list.append({"id": animeid, "name": animename, "availableEpisodes": availables_episodes})
        
    return anime_list

def episodes_list(id) -> list:
    episodes_list_gql = '''
        query ($showId: String!) {
            show(
                _id: $showId
            ) {
                _id
                availableEpisodesDetail
            }
        }
    '''

    # Assuming `allanime_api`, `agent`, `allanime_base`, and `id` are defined elsewhere in your code
    payload = {
        "variables": {
            "showId": id
        },
        "query": episodes_list_gql
    }

    headers = {
        "User-Agent": agent,
        "Referer": allanime_base,
    }

    resp = requests.post(f"{allanime_api}/api", json=payload, headers=headers)

    # print(resp.text)

    resp = resp.json()
    
    if "data" in resp and "show" in resp["data"]:
        available_episodes = resp["data"]["show"]["availableEpisodesDetail"]
        episodes = sorted([int(ep) for ep in available_episodes[mode]])
    
    return episodes

def get_sources_url(id, ep):
    episode_embed_gql = '''
            query ($showId: String!, $translationType: VaildTranslationTypeEnumType!, $episodeString: String!) {
                episode(
                    showId: $showId
                    translationType: $translationType
                    episodeString: $episodeString
                ) {
                    episodeString
                    sourceUrls
                    title
                }
            }
    '''

    payload = {
        "query": episode_embed_gql,
        "variables": {
            "showId": id,
            "translationType": mode,
            "episodeString": ep
        }
    }

    headers = {
        "User-Agent": agent
    }

    resp = requests.post(f"{allanime_api}/api", json=payload, headers=headers)

    resp = resp.json()
    
    
    sources = {}
    if "data" in resp and "episode" in resp["data"]:
        for episode in resp["data"]["episode"]["sourceUrls"]:
            url = episode["sourceUrl"]
            if episode["sourceUrl"].startswith("--"):
                url = url.replace("--", "")
                url = decrypt_allanime(url)
                url = url.replace("clock", "clock.json")
                url = f"https://embed.ssbcontent.site{url}"
                sources[episode["sourceName"]] = {
                    "url": url,
                    "priority": episode["priority"],
                }
    
    if not sources:
        die("Episode not released!")
        
    return sources

def fetch_links(sources: dict) -> list:
    links = []
    for source in sources:
        source = sources[source]
        try:
            resp = requests.get(source["url"]).json()
            if "links" in resp:
                for entry in resp["links"]:
                    link = entry["link"]
                    if "anicdnstream" in link or "vipanicdn" in link or "dropbox" in link:
                        links.append(link)
                        if "src" in entry:
                            links.append(entry["src"])
        except:
            continue
    return links

def generate_cmd(link:str, anime:dict, ep:int, skip_opts:str) -> str:
    executable = "\"C:\\Program Files\\mpv\\mpv.exe\""
    if anime["availableEpisodes"][mode] >= 1000 and len(ep) < 4:
        ep = "0"*(4-len(ep))+ep
    elif anime["availableEpisodes"][mode] >= 100 and len(ep) < 3:
        ep = "0"*(3-len(ep))+ep
    elif anime["availableEpisodes"][mode] >= 10 and len(ep) < 2:
        ep = "0"*(2-len(ep))+ep
            
    title = f"{anime["name"].replace(" ", ".")}.E{ep}"
    
    cmd = f'{executable} {link} --title="{title}" -fs {skip_opts}'
    return cmd

def play(anime, ep):
    try:
        sources = get_sources_url(anime["id"], ep)
    except:
        timeout = 5
        print("no response when fetching sources")
        print(f"waiting {timeout}s before retrying")
        time.sleep(timeout)
        sources = get_sources_url(anime["id"], ep)
    print("Loading Sources")
    links_list = fetch_links(sources)
    for link in links_list:
        if "anicdnstream" in link:
            print("anicdnstream loaded")
        elif "dropbox" in link:
            print("dropbox loaded")
        elif "vipanicdn" in link:
            print("vipanicdn loaded")
    
    link = links_list[0]
    skip_options = ""
    if skip:
        skip_options = aniskip.build_flags(title, ep)
    cmd = generate_cmd(link, anime, ep, skip_options)
    print(cmd)
    subprocess.Popen(cmd, shell=True)
    
def download() -> None:
    raise NotImplementedError("Still no downloads for now")

if __name__ == "__main__":
    query = ""
    for i in range(len(sys.argv)):
        arg = sys.argv[i]
        if arg in ["-d", "--download", "--dl"]:
            download = True
        elif arg in ["-s", "--skip"]:
            skip = True
        elif arg in ["-e", "-ep", "--episode"]:
            ep = sys.argv[i+1]
        elif arg in ["-u", "--update", "-us", "--us", "-usf", "--usf"]:
            if "sf" in arg:
                dl_aniskip(True)
            elif "s" in arg:
                dl_aniskip()
            update()
        elif arg == "--dub":
            mode = "dub"
        else:
            if i != 0:
                if "-" not in arg[i-1]:
                    query += arg
    os.system("clear")
    print(query)
    if query == "":
        query = input("\33[2K\r\033[1;36mSearch anime: \033[0m")
    query = query.replace(" ", "+")
    anime_list = search_anime(query)
    if len(anime_list) == 0:
        die("No results found!")
    os.system("clear")
    print("Select anime:")
    for i in range(1, len(anime_list)+1):
        print(f"{i}. {anime_list[i-1]["name"]}")
    result = input()
    if not result:
        exit(1)
    result = int(result) - 1
    anime = anime_list[result]
    title = anime["name"]
    allanime_title = title.split('(')[0].translate(str.maketrans('', '', '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'))
    ep_list = episodes_list(anime["id"])
    os.system("clear")
    print("Select episode:")
    for ep in ep_list:
        print(ep)
    result = input()
    if not result:
        exit(1)
    play(anime, result)
    
    
    while True:
        c = input()
        if c == "n":
            result = str(int(result) + 1)
            if int(result) > anime["availableEpisodes"][mode]:
                print("This was the last episode")
                print("exiting")
            play(anime, result)
        elif c == "p":
            result = str(int(result) - 1)
            if result == "0":
                print("This is the first episode")
            play(anime, result)
        elif c == "q":
            print("exiting")
            exit(0)
    