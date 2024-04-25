import requests
import json
import sys
import re
import os

def clean_string(s:str) -> str:
    # print("cleaning string " + s)
    s = s.replace("%20", " ")
    c = re.sub(r'[^\x20-\x7E]', ' ', s)
    c = re.sub(r'\s+', ' ', c)
    # print("cleaning returned: " + c)
    return c

def download(filetype):
    exit(1)

def build_options(skiptype:str, skip_metadata:dict) -> list:
    # print("getting the skip times")
    start, end = 0, 0
    results = skip_metadata["results"]
    # print(results)
    for result in results:
        # print("looping through", result)
        if result["skip_type"] == skiptype:
            # print("same skiptype")
            start = result["interval"]["start_time"]
            end = result["interval"]["end_time"]
            # print(f"got start and end times of {skiptype} {start}, {end}")
    return [start, end]

def fetch_mal_id(term: str) -> int:
    # print("fetching the mal id")
    query = term.replace(" ", "%20")
    params = {
        'type': "anime",
        "keyword": query,
    }
    
    response = requests.get("https://myanimelist.net/search/prefix.json", params=params)
    metadata = json.loads(response.text.replace("\\", ""))
    # print("got a response")

    name = clean_string(query)
    id = None
    for result in metadata["categories"][0]["items"]:
        if result["name"] == name:
            id = result["id"]
    
    return id

def build_flags(title: str, ep:int) -> str:
    # print("building flags")
    roaming=  os.getenv("APPDATA")
    lua_script = f"{roaming}/mpv/scripts/skip.lua"
    agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    
    if not os.path.isfile(lua_script):
        print("'skip.lua' script not found!")
        print("downloading it")
        download("lua")
    
    mal_id = fetch_mal_id(title)
    skip_md = {}
    try:
        headers = {
            'User-Agent': agent,
        }
        params = {
            'types': [
                'op',
                'ed',
            ],
        }
        response = requests.get(
            f'https://api.aniskip.com/v1/skip-times/{mal_id}/{ep}',
            params=params,
            headers=headers,
            timeout=(5, None),
        )
        skip_md = response.json()
        # print(skip_md)
        try:
            tmp = skip_md["found"]
        except KeyError as e:
            print(f"Skip times not found!\n{e}")
            return
    except Exception as e:
        print(f"an error occured while fetching skip times: {e}")
    
    op = build_options("op", skip_md)
    ed = build_options("ed", skip_md)
    
    op_opts = f"skip-op_start={op[0]},skip-op_end={op[1]}"
    ed_opts = f"skip-ed_start={ed[0]},skip-ed_end={ed[1]}"
    
    skip_flag = f"--script-opts={op_opts},{ed_opts} '--script={os.path.abspath(lua_script).replace("\\", "/")}'"
    return skip_flag

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} [\"title\"] [ep]")
        sys.exit(0)
    
    skip_flag = build_flags(sys.argv[1], sys.argv[2])
    if skip_flag:
        print(skip_flag)
    

