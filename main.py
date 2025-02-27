from functools import total_ordering
import requests
from peewee import *
from datetime import datetime
import html
import time
import random
import math
import re
db = SqliteDatabase("db/cve.sqlite")

class CVE_DB(Model):
    id = IntegerField()
    full_name = CharField(max_length=1024)
    description = CharField(max_length=200)
    language = CharField(max_length=255)
    url = CharField(max_length=1024)
    created_at = CharField(max_length=128)
    cve = CharField(max_length=64)

    class Meta:
        database = db

db.connect()
db.create_tables([CVE_DB])

def init_file():
    newline = "# Github CVE Monitor\n\n> Automatic monitor github cve using Github Actions \n\n Last generated : {}\n\n| CVE | Name | Description | Language | Date |\n|---|---|---|---|\n".format(datetime.now())
    with open('docs/README.md','w') as f:
        f.write(newline) 
    f.close()

def write_file(new_contents):
    with open('docs/README.md','a') as f:
        f.write(new_contents)
    f.close()

def get_info(year):
    try:
        api = "https://api.github.com/search/repositories?q=CVE-{}&sort=updated&page=3&per_page=500".format(year)
        # API
        req = requests.get(api).json()
        items = req["items"]
        return items
    except Exception as e:
        print("An error occurred in the network request", e)
        return None


def db_match(items):
    r_list = []
    regex = r"[Cc][Vv][Ee][-_]\d{4}[-_]\d{4,7}"
    cve = ''
    for item in items:
        id = item["id"]
        if CVE_DB.select().where(CVE_DB.id == id).count() != 0:
            continue
        full_name = html.escape(item["full_name"])
        description = item["description"]
        if description == "" or description == None:
            description = 'no description'
        else:
            description = html.escape(description.strip())
        language = item["language"]
        if language == "" or language == None:
            language = 'no language'
        else:
            language = html.escape(language.strip())
        url = item["html_url"]
### EXTRACT CVE 
        matches = re.finditer(regex, url, re.MULTILINE)
        for matchNum, match in enumerate(matches, start=1):
            cve = match.group()
        if not cve:
            matches = re.finditer(regex, description, re.MULTILINE)
            cve = "CVE Not Found"
            for matchNum, match in enumerate(matches, start=1):
                cve = match.group()
### 
        created_at = item["created_at"]
        r_list.append({
            "id": id,
            "full_name": full_name,
            "description": description,
            "language": language,
            "url": url,
            "created_at": created_at,
            "cve": cve.replace('_','-')
        })
        CVE_DB.create(id=id,
                      full_name=full_name,
                      description=description,
                      language=language,
                      url=url,
                      created_at=created_at,
                      cve=cve.upper().replace('_','-'))

    return sorted(r_list, key=lambda e: e.__getitem__('created_at'))

def main():
    year = datetime.now().year
    sorted_list = []
    for i in range(year, 1999, -1):
        item = get_info(i)
        if item is None or len(item) == 0:
            continue
        print("Year : {} : raw data obtained {} articles".format(i, len(item)))
        sorted = db_match(item)
        if len(sorted) != 0:
            print("Year {} : update {} articles".format(i, len(sorted)))
            sorted_list.extend(sorted)
        count = random.randint(3, 15)
        time.sleep(count)
    cur = db.cursor()
    cur.execute("SELECT * FROM CVE_DB ORDER BY cve DESC;")
    result = cur.fetchall()
    for row in result:
    #    if row[4].startswith('20'):
        Publish_Date=row[4]
    #    else:
    #        Publish_Date=""    
    #        print("(!) Not a date")    
        Description = row[2].replace('|','-')
        if row[5].upper() == "CVE NOT FOUND":
            newline = "| " + row[5].upper() + " | [" + row[1] + "](" + row[3] + ") | " + Description + " | " + Publish_Date + "|\n"
        else:
            newline = "| [" + row[5].upper() + "](https://www.cve.org/CVERecord?id=" + row[5].upper() + ") | [" + row[1] + "](" + row[3] + ") | " + Description + " | " + Publish_Date + "|\n"
        write_file(newline)

    # Statistics
    
    ## TODO HERE WILL COME THE CODE FOR STATISTICS 
        
if __name__ == "__main__":
    init_file()
    main()
