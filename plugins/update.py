import os
import re
from sys import argv

current_version = argv[1]
updatefile = open("update", "r")

def die(*args):
    for arg in args:
        print(arg)
    updatefile.close()
    os.remove("./update")
    exit(0)

update_content = updatefile.read()
version = re.findall(r"version_number=\"([\d.]+)\"", update_content)[0]
if current_version == version:
    die("already on the lastest version")
with open("animefetch.py", "w+") as file:
    file.write(update_content)
print("updated the program")
die(f"{current_version} -> {version}")