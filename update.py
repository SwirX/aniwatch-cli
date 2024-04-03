import os
import re
from sys import argv

current_version = argv[1]

with open("update", "r") as updatefile:
    update_content = updatefile.read()
    version = re.findall(r"version_number=\"([\d.]+)\"", update_content)[0]
    if current_version == version:
        print("already on the lastest version")
        exit(0)
    with open("animefetch.py", "w+") as file:
        file.write(update_content)
    print("updated the program")
    print(f"{current_version} -> {version}")
    exit(0)