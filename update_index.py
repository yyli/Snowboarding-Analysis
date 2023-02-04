#!/usr/bin/env python3
import glob
import re
import urllib.parse
from pathlib import Path
import chevron

MARKDOWN_TEMPLATE = """
# Snowboarding Analysis Files

{{#folders}}
  - {{name}}
    {{#folders}}
    - {{name}}
    {{#files}}
        - [{{name}}]({{path}})
    {{/files}}
    {{/folders}}
{{/folders}}
"""

def get_all_files():
    results = glob.glob("**/**.html", recursive=True)
    return results

def parse_html(file):
    with open(file, "r") as f:
        contents = f.read()
        title_var = re.findall('<meta name="__notebook_title_name__" content="(.*)">', contents)
        contents = contents.replace("analyze", title_var)
        contents = contents.replace("Make this Notebook Trusted to load map: File -> Trust Notebook", "")

        if len(title_var) != 1:
            raise RuntimeError(f"Couldn't extract title for {file}")
        
        title_var = title_var[0]

    with open(file, "w") as f:
        f.write(contents)

    return title_var

def update_readme(files_with_title):
    mustache_json = {"folders": {}}
    for f_w_t in files_with_title:
        file = f_w_t["file"]
        title = f_w_t["title"]
        parts = Path(file).parts
        if len(parts) > 3:
            raise RuntimeError("Can't nest files more than 2 folders")

        num_parts = len(parts)
        local = mustache_json["folders"]
        for idx, p in enumerate(parts[:-1]):
            if idx == num_parts - 2:
                if p not in local:
                    local[p] = []
                local[p].append({
                    "name": title,
                    "path": urllib.parse.quote(file)
                })
            else:
                if p not in local:
                    local[p] = {}
                
                local = local[p]

    folders = []
    for k,v in mustache_json["folders"].items():
        ffolders = []
        for kk, vv in v.items():
            ffolders.append({
                "name": kk,
                "files": sorted(vv, key=lambda x: x["name"])
            }) 
        v = ffolders

        folders.append({
            "name": k,
            "folders": v
        })
    mustache_json["folders"] = folders

    from pprint import pprint
    pprint(mustache_json)

    with open('README.md', 'w') as f:
        f.write(chevron.render(MARKDOWN_TEMPLATE, mustache_json))

def main():
    files = get_all_files()
    files_with_title = []
    for file in files:
        print(f"Parsing {file}")
        title_var = parse_html(file)
        files_with_title.append({
            "title": title_var, 
            "file": file
        })

    update_readme(files_with_title)

if __name__ == "__main__":
    main()
