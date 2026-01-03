#Project 2: Authentication

##Overview
Project 2 is a polished version of the Project 1 API. It supports adding, retrieving, and deleting notes.
Supports Offline and Online .json persistent storage.

###Features

    + Retrieve All Notes, or note by Id using /notes GET and id argument in the JSON.
    + Delete a Note by Id using /notes DELETE and id argument in the JSON.
    + Add a Note by using /notes and POST.
    + Offline/Online Modes, Automatic fallback to local if cloud bucket cannot be found.
    + Configurable Local JSON file for offline use through .env
    + Persistence in Offline or Online functions in Notes, Note Id using metaJSON.
    + API key authentication handling through JSON and .env

## Getting Started

    First, install the prerequisites from requirements.txt
    '''powershell
    pip install -r requirements.txt

    Create a .env file if you do not have it yet. Set it with 2 things.
    API_KEY=your_secret_key
    LOCAL=local_notes.json (Or whatever json file in the folder that you wish to use as local storage.)

    Run the server.
    python app.py

    Example Requests:
    Invoke-RestMethod -Uri http://127.0.0.1:5000/notes -Method GET -Headers @{ "X-API-KEY" = "your_secret_key" }
    Invoke-RestMethod -Uri http://127.0.0.1:5000/notes -Method POST -Headers @{ "X-API-KEY" = "your_secret_key" } -Body '{"title":"Hello","content":"World"}' -ContentType "application/json"



## What I learned

    ###Wrappers
    
    + An outermost function must exist if the wrapper takes additional arguments (like key).
    + The innermost function actually calls your func passed in, and does the logic. 
    + The innermost function doesn't need the key because of *closure*. Python keeps outer variables alive for nested functions. (Think of it kind of like global.)
    + Think of it like a Russian nesting doll. Outer holds the key, middle knows which function to execute, innermost actually runs.
    + You can write local helper functions in wrappers! Don't forget this.

    ###Authentication
    + This project uses an API Key. The request is only taken if the given key and the secret one stored in .env are the same.
    + Didn't use HTML. While it's a bit more standard, it's not too great for programmatic access, as well as need session management, and more moving parts like hashing, sessions, etc.
    + API Keys is optimal because this *is* an API, not a website.

    ###JSON
    + dumps and loads as well as dump and load are different from each other in json. dumps takesw a Python object, and makes it into a JSON string. loads takes a JSON string and makes it a python object. Use with things like Blobs. dump and load are for working *directly* with files, and not objects like Blobs. download_as_text() returns a *JSON STRING* not a Python, one, which is why we have to use it.

    ###Persistence
    + Try to have 'One source of Truth' for everything. It makes it a lot easier. One in, one out. 

