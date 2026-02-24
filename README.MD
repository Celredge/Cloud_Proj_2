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

    There is a .env.example file with the push that will help you if you get confused. You can modify the path in the .env LOCAL variable to point somewhere else if you need a json that is not local to your file structure. The Program should create the file for you if it is not present.

    Run the server.
    python app.py

    Note: You *must* use the setup endpoint at least once validly. It is what sets up paths for file. Bucket is the name of the cloud bucket to connect to. If it can't be found, it falls back to local storage.
    If you are unsure if you have run setup, then running the "health" endpoint will confirm.

    
    
    Invoke-RestMethod -Uri http://127.0.0.1:5000/setup -Method POST -ContentType "application/json" -Body (@{ bucket = "my-notes-bucket" } | ConvertTo-Json)



    Example Requests (Powershell):
    Invoke-RestMethod -Uri http://127.0.0.1:5000/notes -Method GET -Headers @{ "X-API-KEY" = "your_secret_key" }
    Invoke-RestMethod -Uri http://127.0.0.1:5000/notes -Method POST -Headers @{ "X-API-KEY" = "your_secret_key" } -Body '{"title":"Hello","content":"World"}' -ContentType "application/json"


## Containerization

    Everything is included to create a container using docker, including the dockerfile. Use the following commands in the root directory of the API. (That is, where requirements.txt and this README are.)
    

    Example Commands (Powershell):

    docker build -t notes:api:taghere . 
    docker run -p 5000:5000 --env-file src/.env notes-api:taghere

    It should be noted you need Docker installed, as well as have followed the directions for creating a .env file, which is used here. The .env from your local environment will be carried over.






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
    + dumps and loads as well as dump and load are different from each other in json. dumps takes a Python object, and makes it into a JSON string. loads takes a JSON string and makes it a python object. Use with things like Blobs. dump and load are for working *directly* with files, and not objects like Blobs. download_as_text() returns a *JSON STRING* not a Python, one, which is why we have to use it.

    ###Persistence
    + Try to have 'One source of Truth' for everything. It makes it a lot easier. One in, one out. 

