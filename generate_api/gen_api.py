import sys
import os
import re
from bs4 import BeautifulSoup
import requests
import jinja2
from pprint import pprint
import keyword
from pathlib import Path
from time import sleep

res = requests.get("https://help.pyramidanalytics.com/Content/Root/developer/reference/APIs/REST%20API/objects.htm")
doc = BeautifulSoup(res.text, features="html.parser")
tbl = doc.find("table", {"class": "fxlist"})
classes = [x.get("href").replace("definitions/","").replace(".htm","") for x in tbl.find_all("a")]
base_url = "https://help.pyramidanalytics.com/Content/Root/developer/reference/APIs/REST%20API/definitions/{classname}.htm"


res = requests.get("https://help.pyramidanalytics.com/Content/Root/developer/reference/APIs/REST%20API/enums.htm")
doc = BeautifulSoup(res.text, features="html.parser")
tbl = doc.find("table", {"class": "fxlist"})
enum_classes = [x.get("href").replace("definitions/","").replace(".htm","") for x in tbl.find_all("a")]



methods = dict(
    auth = "https://help.pyramidanalytics.com/Content/Root/developer/reference/APIs/REST%20API/API2/auth.htm",
    access = "https://help.pyramidanalytics.com/Content/Root/developer/reference/APIs/REST%20API/API2/access.htm",
    content = "https://help.pyramidanalytics.com/Content/Root/developer/reference/APIs/REST%20API/API2/content.htm",
    query = "https://help.pyramidanalytics.com/Content/Root/developer/reference/APIs/REST%20API/API2/query.htm",
    dataSources = "https://help.pyramidanalytics.com/Content/Root/developer/reference/APIs/REST%20API/API2/dataSources.htm",
    tasks = "https://help.pyramidanalytics.com/Content/Root/developer/reference/APIs/REST%20API/API2/tasks.htm",
    notification = "https://help.pyramidanalytics.com/Content/Root/developer/reference/APIs/REST%20API/API2/notification.htm"
)



tpl = '''
@dataclass
class {{ classname }}(DataClassJsonMixin):
    """ 
    generated from {{ url }}
    """
    {% for attr in classattrs -%}
    {{ attr.Name }}: {{ attr.PythonType }} = {{ attr.Default }} # Format:"{{ attr.Format}}" Descr:"{{ attr.Description}}"
    {% endfor %}

'''

tpl_enum = '''
class {{ classname }}(IntEnum):#
    """ 
    generated from  {{ url }}
    """
    {% for attr in classattrs -%}
    {{ attr.Name }} = {{ attr.Value }}
    {% endfor %}

'''

tpl_method = '''
def {{ methodname }}({{ inputtype }}) -> {{ response_type }}:
    """
    Description:
        {{description}}
    Input:
        {% for k,v in in_attrs.items() -%}
        {{ k }}: {{ v }}
        {% endfor %}

    Output:
        {% for k,v in out_attrs.items() -%}
        {{ k }}: {{ v }}
        {% endfor %}

    generated from {{ url }}
    """
    method_url = "{{method_url}}"


'''

env = jinja2.Environment()



def gen_enum():
    with open("api_gen/enum.py", "w") as out:
        t = env.from_string(tpl_enum)
        out.write("from enum import IntEnum\n\n")
        for classname in enum_classes:
            print(f"processing enum: {classname}")

            url = base_url.format(classname=classname)
            
            soup = None
            cachename = "cache/{}.htm".format(classname)
            if os.path.exists(cachename):
                with open(cachename, "r") as f:
                    soup = BeautifulSoup(f.read(), features="html.parser")
            else:
                attrs_html = requests.get(url)
                soup = BeautifulSoup(attrs_html.text, features="html.parser")
                with open(cachename, "w") as f:
                    f.write(attrs_html.text)

            api_tbl = soup.find("table", {"class" : "apiCode"})

            header = [x.text.strip() for x in api_tbl.select("tr th p")]
            attrs = []
            for row in api_tbl.select("tr")[1:]:
                attr = dict(zip(header,[a.text.strip() for a in row.select("td")]))
                #if attrs["Type"] == "string": attrs["Type"] = "str"
                attr_type = attr.get("Type", "unknown")
                name = attr["Enumerated Name"]
                if name in keyword.kwlist:
                    name = name + "_"
                name = attr["Name"] = name

                attrs.append(attr)
            if classname in ("QueryResultMessageExtraData", ):
                # skip problematic classes for now
                continue
            out.write(t.render(classname=classname, classattrs=attrs, url=url))

def gen_object():
    with open("api_gen/objects.py", "w") as out:
        t = env.from_string(tpl)
        python_types = {
            "string" : "str",
            "integer" : "int",
            "boolean" : "bool",
            "object"  : "dict"

        }

        for classname in classes:
            print(f"processing object: {classname}")
            url = base_url.format(classname=classname)
            
            soup = None
            cachename = "cache/{}.htm".format(classname)
            if os.path.exists(cachename):
                with open(cachename, "r") as f:
                    soup = BeautifulSoup(f.read(), features="html.parser")
            else:
                attrs_html = requests.get(url)
                soup = BeautifulSoup(attrs_html.text, features="html.parser")
                with open(cachename, "w") as f:
                    f.write(attrs_html.text)
            
            api_tbl = soup.find("table", {"class" : "apiCode"})

            header = [x.text.strip() for x in api_tbl.select("tr th p")]
            #print(header)
            attrs = []
            for row in api_tbl.select("tr")[1:]:
                attr = dict(zip(header,[a.text.strip() for a in row.select("td")]))
                #if attrs["Type"] == "string": attrs["Type"] = "str"
                attr_type = attr.get("Type", "unknown")
                attr["Default"] = "None"

                if m:= re.search("(\w+)\s*\[\s*\]", attr_type):
                    attr_type="List[{}]".format(m.group(1))

                if attr.get("Required") == "Y":
                    attr["PythonType"] = python_types.get(attr_type,attr_type)
                else:
                    attr["PythonType"] = "Optional[{}]".format(python_types.get(attr_type,attr_type))
                descr = attr.get("Description","").lower()
                if re.search("default:false", descr):
                    attr["Default"] = "False"
                elif re.search("default:true", descr):
                    attr["Default"] = "True"

                attrs.append(attr)
            
            #pprint(attrs)
            out.write(t.render(classname=classname, classattrs=attrs, url=url))
            


def gen_methods():
    #from playwright.sync_api import sync_playwright
    #playwright = sync_playwright().start()
    #browser = playwright.chromium.launch()
    #page = browser.new_page()

    t = env.from_string(tpl_method)

    for groupname, url in methods.items():
        res = requests.get(methods[groupname])
        doc = BeautifulSoup(res.text, features="html.parser")
        tbl = doc.find("table", {"class": "fxlist"})
        definitions = [x.get("href").replace("definitions/","").replace(".htm","") for x in tbl.find_all("a")]
        with open(f"api_gen/{groupname}.py", "w") as out:
            for methodname in definitions:
                print(f"processing method: {methodname}")
                cachename = "cache/method/{}.htm".format(methodname)
                p = Path(cachename).parent
                if not p.exists():
                    p.mkdir()
                url = f"https://help.pyramidanalytics.com/Content/Root/developer/reference/APIs/REST%20API/API2/{methodname}.htm"
                soup = None
                if os.path.exists(cachename):
                    with open(cachename, "r") as f:
                        soup = BeautifulSoup(f.read(), features="html.parser")
                else:
                    #print(url)
                    res = requests.get(url)
                    content = res.text
                    #print(res.status_code)
                    soup = BeautifulSoup(content, features="html.parser")
                    with open(cachename, "w") as f:
                        f.write(soup.prettify())

                method_url = soup.find("div", {"class": "apiCode"}).text.strip()
                description = soup.find("h1").text.strip()
                details = [x.text.strip() for x in soup.select("li")]
                spec = dict([(n.text.strip(), n) for n in soup.select("h5")])
                inputs = []
                if "Input Parameters" in spec:
                    input_header = spec["Input Parameters"]
                    in_nodes = []
                    node = input_header.find_next_sibling("div")
                    #import ipdb;ipdb.set_trace()
                    while 1:
                        if not node:
                            break
                        if node.name == "h5": break
                        if node.attrs.get("style") == "clear:left":
                            node = node.find_next_sibling()
                            continue
                        if "apihead" in node.attrs.get("class",{}) or "apidetail" in node.attrs.get("class",{}):
                            in_nodes.append(node.text.strip())
                        else:
                            break
                        node = node.find_next_sibling()
                    it = iter(in_nodes)
                    in_attrs = dict(zip(it, it))

                if "Output Response" in spec:
                    header = spec["Output Response"]
                    out_nodes = []
                    node = header.find_next_sibling("div")
                    #import ipdb;ipdb.set_trace()
                    while 1:
                        if not node:
                            break
                        if node.name == "h5": break
                        if node.attrs.get("style") == "clear:left":
                            node = node.find_next_sibling()
                            continue
                        if "apihead" in node.attrs.get("class",{}) or "apidetail" in node.attrs.get("class",{}):
                            out_nodes.append(node.text.strip())
                        else:
                            break
                        node = node.find_next_sibling()
                    it = iter(out_nodes)
                    out_attrs = dict(zip(it, it))

                response_type = out_attrs.get("Response Type")
                if not response_type:
                    response_type = out_attrs.get("Response List Type", "None")
                    if m:= re.search("(\w+)\s*\[\s*\]", response_type):
                        response_type = "List[{}]".format(m.group(1))

                out.write(t.render(
                        methodname=methodname.split("/")[-1], 
                        url=url, method_url=method_url,
                        description=description,
                        in_attrs=in_attrs,
                        out_attrs=out_attrs,
                        response_type=response_type
                        ))




def main():
    output_dir = Path("api_gen")
    if not output_dir.exists():
        output_dir.mkdir()

    cache_dir = Path("cache")
    if not cache_dir.exists():
        cache_dir.mkdir()
        (cache_dir / Path("method")).mkdir()
        
    gen_enum()
    gen_object()
    gen_methods()

if __name__ == '__main__':
    main()