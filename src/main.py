

from typing import Optional, Tuple
from dataclasses import dataclass, field
from json import loads, dumps, load, dump, JSONDecodeError
from google.cloud import storage
from google.cloud.storage import Blob
from google.api_core import exceptions as gcs_ex
from pathlib import Path
from os import getenv
from enum import Enum
from dotenv import load_dotenv


#-----------
# Dataclass and State
#------------

class ErrorCode(Enum):
    INVALID_INPUT = 1
    NOT_FOUND = 2
    PERMISSION_DENIED = 3
    SERVER_ERROR = 4
    NOT_FOUND_USE_LOCAL = 5
    PERMISSION_DENIED_USE_LOCAL = 6
    SERVER_ERROR_USE_LOCAL = 7
    SETUP_REQUIRED = 8


#Dataclass for storing instances of variables. A full class isn't quite needed here. (Maybe in the future.)
@dataclass
class StorageState:
    client: Optional[storage.Client] = None
    bucket_name: Optional[str] = None
    bucket: Optional[storage.Bucket] = None
    blob_name: Optional[str] = "notes.json"
    blob_r:Optional[Blob] = None
    id_count: int = 0
    old_ids:list[int] = field(default_factory=list)
    source:str =  "online"

state = StorageState()

load_dotenv()
LOCAL_FILE:str = getenv("LOCAL") or "local_notes.json"


#-----------
# Try/except Wrapper
#-----------

def catch_errors_2(func):
    """Handle try/except in a function. Assumes A tuple of 2 returned.

    Args:
        func (function): name of the function to wrap. Usually automatic with the @ syntax.
    """
    def catch(*args, **kwargs):
        try:
            return func(*args,**kwargs)
        except Exception as e:
            
            return (False, str(e))
    return catch

def catch_errors_3(func):
    """Wrapper that handles try/except in functions using the specified Tuple schema. Assumes 2 things in tuple.

    Args:
        func (function): name of the function to wrap. Usually automatic with the @ syntax.
    """
    def catch(*args, **kwargs):
        try:
            return func(*args,**kwargs)
        except Exception as e:
            
            return (False, str(e),None)
    return catch

#---------
# Setup functions
#----------


def setup(bucket_n:Optional[str]) -> Tuple[bool, Optional[ErrorCode]]:
    """Set up storage and state object

    Args:
        bucket_n (str): Bucket name. Must be a non-empty string.

    Returns:
        Tuple[bool, Optional[str]]:
            - bool: True if setup was success without errors. False if not. 
            - str: Error Message if bool is False. None if True
    """

    #Make sure we have bucket name.
    if bucket_n is None:
        return (False,ErrorCode.INVALID_INPUT)
    
    #Check the bucket name.
    ok, err = check_string(bucket_n)
    if not ok:
        return (False, ErrorCode.INVALID_INPUT)
    
    #Set up our stuff
    try:
        #Get the client
        state.client = storage.Client(project=" project-2-483120")

        #Set the state of our client
        state.bucket_name = bucket_n

        #Attach our bucket to the client.
        state.bucket = state.client.bucket(state.bucket_name)

        #Attach our blob
        state.blob_r = state.bucket.blob(state.blob_name)

        #Ensure the file exists.
        if not state.blob_r.exists():
            state.blob_r.upload_from_string("{}")

    except gcs_ex.NotFound as e:
    # Bucket does not exist.
        state.client = None
        state.bucket = None
        state.blob_r = None
        state.source = "offline"
        setup_ensure_meta()
        return (False, ErrorCode.NOT_FOUND_USE_LOCAL)
    
    except gcs_ex.Forbidden as e:
        #Permission or billing
        state.client = None
        state.bucket = None
        state.blob_r = None
        state.source = "offline"
        setup_ensure_meta()
        return (False, ErrorCode.PERMISSION_DENIED_USE_LOCAL)


    except Exception as e:

        #Return to our default state
        state.client = None
        state.bucket_name = ""
        state.bucket = None
        state.blob_r = None
        state.source = "offline"
        setup_ensure_meta()
        return (False,ErrorCode.SERVER_ERROR_USE_LOCAL)
    
    state.source = "online"
    setup_ensure_meta()
    return (True,None)

#----------
# Main Note functions
#----------

#A special case. Will never return False. If it *did*, then you wouldn't even get the False because you couldn't connect to server.
# This is for the health check endpoint, which is not protected by the API key or the handle_response wrapper, since it's just a health check.
#
def health_check() -> Tuple[bool, str]:
    """Check the health of the storage.

    Returns:
        Tuple[bool, Optional[str]]:
            - bool: True if setup was success without errors. False if not. 
            - str: Error Message if bool is False. Confirmation message if bool is True.
    """
    if state.source == "offline" and not Path(LOCAL_FILE).exists():
        return (False,"Server is responding. Setup has not been ran.")
        
    if state.source == "online" and (state.blob_r is None or state.bucket is None):
        return (False,"Server is responding. Setup has not been run yet.")
    
    
    return (True,"Server is responding. Setup has been ran.")


@catch_errors_2
def add_note(title:str,content:str) -> Tuple[bool,Optional[ErrorCode]]:
    """Add a note to the cloud storage JSON

    Args:
        title (str): Title of the note. Must be non-empty string.
        content (str): Content of the note. Must be a non-empty string.

    Returns:
        Tuple[bool,Optional[str]]:
            - bool: True if setup was success without errors. False if not. 
            - str: Error Message if bool is False. None if True
    """

    #Check title
    ok,err = check_string(title)
    if not ok:
        print("Adding note failed with invalid title string.")
        return (False,ErrorCode.INVALID_INPUT)
    
    #Check Content
    ok, err = check_string(content)
    
    if not ok:
        print("Adding note failed with invalid content string.")
        return (False,ErrorCode.INVALID_INPUT)

    #Check our sources to ensure setup has ran
    if state.source == "offline" and not Path(LOCAL_FILE).exists():
        return (False,ErrorCode.SETUP_REQUIRED)
        
    if state.source == "online" and (state.blob_r is None or state.bucket is None):
        return (False,ErrorCode.SETUP_REQUIRED)
    

    notes = load_notes() or {}

    id = generate_id()

    notes[str(id)] = {"title":title,"content":content}
    persist(notes)
    return (True,None)

@catch_errors_3
def get_note(id:Optional[str] = None) -> Tuple[bool,Optional[ErrorCode],Optional[dict]]:
    """Get note/notes from cloud storage and serves them.

    Args:
        id (Optional[str]): ID of the note in string form. If not provided, will get all notes. Id must be positive.

    Returns:
        Tuple[bool,Optional[str],Optional[dict]]:
            - bool: True if setup was success without errors. False if not. 
            - str: Error Message if bool is False. None if True
            - dict: The notes id in string form: the notes retrieved
    """

    #Discriminate between sources
    if state.source == "offline" and not Path(LOCAL_FILE).exists():
            return (False,ErrorCode.SETUP_REQUIRED,None)
        
    if state.source == "online" and (state.blob_r is None or state.bucket is None):
        return (False,ErrorCode.SETUP_REQUIRED,None)
    
    notes = load_notes()
    
    if id is None:
        print("Getting all notes successful.")
        return(True,None,hide_meta(notes))
    
    if parse_id(id) != None:
        return (False,ErrorCode.INVALID_INPUT,None)
    
    entry = notes.get(id,None)

    if entry is None:
        print("Getting note with Id failed because Id does not exist.")
        return (False,ErrorCode.NOT_FOUND,None)
    
    print("Getting Note with Id Successful.")
    return(True,None,entry)
        

@catch_errors_2
def delete_note(id:Optional[str]) -> Tuple[bool,Optional[ErrorCode]]:
    """Delete a note by id.

    Args:
        id (Optional[str]): ID of the note in string form. Id must be positive and exist in the cloud storage.

    Returns:
        Tuple[bool,Optional[str]]:
            - bool: True if setup was success without errors. False if not. 
            - str: Error Message if bool is False. None if True

    """
    #If no id, none of the below matters. So we check it.
    
    if state.source == "offline" and not Path(LOCAL_FILE).exists():
        return (False,ErrorCode.SETUP_REQUIRED)
        
    if state.source == "online" and (state.blob_r is None or state.bucket is None):
        return (False,ErrorCode.SETUP_REQUIRED)
    

    if id is None:
        print("Delete note failed because Id was not provided.")
        return (False, ErrorCode.INVALID_INPUT)
    
    #Check to see if id is valid number.
    if parse_id(id) != None:
        return (False,ErrorCode.INVALID_INPUT)
    
    #Discriminate between Sources
    notes = load_notes() or {}

    note = notes.get(id,None)

    if note is None:
        print("Id not found in JSON. Continuing...")
        return (True, None)
    
    state.old_ids.append(int(id))
    del notes[id]


    persist(notes)
    print("Deleting Note Successful.")
    return(True,None)

#-----------
#Helper Functions
#-----------

def generate_id() -> int:
    """Generate an id.

    Returns:
        int: The Id which has been chosen.
    """
    #Check to see if there are any pre-used ids.
    if len(state.old_ids) != 0:

        back = state.old_ids[0]
        del state.old_ids[0]
        
        return back
    
    #No pre-used ids. Generate new.
    else:
        
        back = state.id_count
        
        state.id_count += 1

        return back

def load_notes_local() -> dict:
    """Load the local notes and return the JSON

    Returns:
        Optional[dict]:
            dict - A dictionary indicative of the local json data. None if file doesn't exist.
    
    """
    file_path = Path(LOCAL_FILE)

    Path(LOCAL_FILE).touch(exist_ok=True)
    
    try:
        with open(file_path,"r",encoding ="utf-8") as f:
            return load(f)
    except (JSONDecodeError,FileNotFoundError):
        #If file is corrupted, start fresh
        return {}
        
    
def save_notes_local(notes:dict):
    """Save the notes into JSON

    Args:
        dict:
            dict - The dictionary to make into JSON and save.

    """
    with open(LOCAL_FILE,"w",encoding="utf-8") as f:

        dump(notes, f, indent=2)

def load_notes()-> dict:
    """Load Notes for both types.

    Returns:
        dict: Data that was loaded from the JSON.
    """

    # Fail early if setup was never run
    if state.source == "online" and (state.blob_r is None or state.bucket is None):
        raise RuntimeError("Storage not initialized. Please run setup first.")


    if state.source == "offline":
        return load_notes_local() or {}
    elif state.blob_r != None and state.source == "online":
        try:
            return loads(state.blob_r.download_as_text())
        except JSONDecodeError:
            return {}
    
    return {}

def save_notes(notes:dict):
    """Save Notes for both types.

    Args:
        notes (dict): Data that is to be stored in the JSON.
    """

    if state.source == "offline":
        return save_notes_local(notes)
    elif state.blob_r != None and state.source == "online":
        state.blob_r.upload_from_string(dumps(notes))

def setup_ensure_meta():
    """Ensure metadata is in the JSON. Add it if missing.
    """
    if state.source == "offline" and LOCAL_FILE:
        Path(LOCAL_FILE).touch(exist_ok=True)
    

    notes = load_notes()

    if '_meta' not in notes:
        notes["_meta"] = {"id_count":0,"old_ids":[]}
        save_notes(notes)
    else:
        #id_count

        metas = notes.get("_meta",None)
        if metas is not None:
            state.id_count = metas.get("id_count",0)
            state.old_ids = metas.get("old_ids",[])

def persist(notes:dict):
    """Writes current data to meta and notes.
    """
    notes['_meta'] = {"id_count":state.id_count,"old_ids":state.old_ids}
    save_notes(notes)

def hide_meta(notes:dict) -> dict:
    """Hides meta from getting all notes.

    Args:
        notes (dict): Dictionary storing the notes and meta.

    Returns:
        dict: Argument dictionary without meta.
    """
    true = {}

    for k,v in notes.items():

        if k != "_meta":

            true[k] = v
    return true
       
#----------------
# Verification Functions
#----------------

def parse_id(id_val: Optional[str]) -> Optional[ErrorCode]:
    """Use check_int_positive and other checks to make sure an id is valid.

    Args:
        id_val (Optional[str]): Number to check in str form.

    Returns:
        Optional[ErrorCode]: None if successful, ErrorCode type if unsuccessful.
    """

    if id_val is None:
        return ErrorCode.INVALID_INPUT
    
    try:
        i = int(id_val)
    except (ValueError,TypeError):
        return ErrorCode.INVALID_INPUT
    
    ok, _ = check_int_positive(i)
    if not ok:
        return ErrorCode.INVALID_INPUT
    
    return None

def check_int_positive(*args:Optional[int]) -> Tuple[bool,Optional[ErrorCode]]:
    """Check if an integer is valid for id.

    Args:
        prospect (Optional[int]): The integer to check. 

    Returns:
        Tuple[bool,Optional[str]]:
            - bool: True if setup was success without errors. False if not. 
            - str: Error Message if bool is False. None if True
    """

    if len(args) == 0:
        return (False,ErrorCode.INVALID_INPUT)

    for idx, i in enumerate(args):
        
        #Check that they are strings.
        if not isinstance(i,int):
            return (False,ErrorCode.INVALID_INPUT)
        
        #Check that they are not negative.
        if i < 0:
            return (False,ErrorCode.INVALID_INPUT)
        
    
    return (True,None)

def check_string(*args:Optional[str]) -> Tuple[bool,Optional[ErrorCode]]:
    """Check strings for validity and non-empty.

    Args:
        prospect (Optional[str]): String to check.

    Returns:
        Tuple[bool,Optional[str]]:
            - bool: True if setup was success without errors. False if not. 
            - str: Error Message if bool is False. None if True 
    """
    if len(args) == 0:
        return (False,ErrorCode.INVALID_INPUT)


    for idx, s in enumerate(args):

        #Check that they are strings.
        if not isinstance(s,str):
            return (False,ErrorCode.INVALID_INPUT)
        
        #Check that they are not empty.
        if len(s.strip()) == 0:
            return (False, ErrorCode.INVALID_INPUT)

    
    #Checks out.
    return (True,None)



