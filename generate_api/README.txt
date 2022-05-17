Create python python modules from the REST documentation online

# create venv
$ python -m venv venv

# install requirements
$ ./venv/bin/pip install -r requirements.txt

# download api html docs and save in local "cache" dir
# output is written to "api_gen"
$ ./venv/bin/python gen_api.py