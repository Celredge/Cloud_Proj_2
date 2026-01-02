from typing import Optional, Tuple
from dataclasses import dataclass, field
from json import loads, dumps
from google.cloud import storage
from google.cloud.storage import Blob



#-----------
# Dataclass and State
#------------


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

state = StorageState()


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


def setup(bucket_n:Optional[str]) -> Tuple[bool, Optional[str]]:
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
        return (False,"No bucket name provided.")
    
    #Check the bucket name.
    ok, err = check_string(bucket_n)
    if not ok:
        return (False, str(err))
    
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

    except Exception as e:

        #Return to our default state
        state.client = None
        state.bucket_name = ""
        state.bucket = None
        state.blob_r = None

        return (False,str(e))
    
    return (True,None)

#----------
# Main Note functions
#----------


@catch_errors_2
def add_note(title:str,content:str) -> Tuple[bool,Optional[str]]:
    """Add a note to the clould storage JSON

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
        return (False,str(err))
    
    #Check Content
    ok, err = check_string(content)
    if not ok:
        return (False,str(err))

    
    #Check to see if setup was called.
    if state.client is None or state.blob_r is None:
        return (False, "Setup hasn't run yet.")
    
    else:
            #Get the notes.
            notes = loads(state.blob_r.download_as_text())

            #Get the id
            note_id = generate_id()

            #Modify the notes we have downloaded.
            notes[str(note_id)] = {"title":title,"content":content}

            #Upload
            state.blob_r.upload_from_string(dumps(notes))
        

        
    return (True,None)

@catch_errors_3
def get_note(id:Optional[str] = None) -> Tuple[bool,Optional[str],Optional[dict]]:
    """Get note/notes from cloud storage and serves them.

    Args:
        id (Optional[str]): ID of the note in string form. If not provided, will get all notes. Id must be positive.

    Returns:
        Tuple[bool,Optional[str],Optional[dict]]:
            - bool: True if setup was success without errors. False if not. 
            - str: Error Message if bool is False. None if True
            - dict: The notes id in string form: the notes retrieved
    """

    #Make sure setup has run
    if state.client is None or state.blob_r is None:
        return (False, "Setup hasn't run yet.", None)
    
    #Get the json data
    notes = loads(state.blob_r.download_as_text())

    #If no id, return the entire notes
    if id is None:
        return (True,None,notes)
    
    #Check the id to make sure it's good.
    ok, err = check_int_positive(int(id))
    if not ok:
        return(False,str(err),None)
    
    entry = notes.get(id,None)

    #If the entry doesn't exist...
    if entry is None:
        return (False,"Id does not exist.",None)

    return (True,None,{str(id): entry})

@catch_errors_2
def delete_note(id:Optional[str]) -> Tuple[bool,Optional[str]]:
    """Delete a note by id.

    Args:
        id (Optional[str]): ID of the note in string form. Id must be positive and exist in the cloud storage.

    Returns:
        Tuple[bool,Optional[str]]:
            - bool: True if setup was success without errors. False if not. 
            - str: Error Message if bool is False. None if True

    """
    #If no id, none of the below matters. So we check it.
    if id is None:
        return (False, "No id provided.")
    
    #Check to see if id is valid number.
    ok,err = check_int_positive(int(id))
    if not ok:
        return (False,str(err))
    
    #Make sure setup has run
    if state.client is None or state.blob_r is None:
        return (False, "Setup hasn't run yet.")
    
    #Get the json data
    notes = loads(state.blob_r.download_as_text())


    #Make sure that the id exists.
    note = notes.get(id,None)

    #If we didn't find it...
    if note is None:
        return (False,"Id does not exist.")
    
    #Add the deleted id to our free ids list.
    state.old_ids.append(int(id))

    #Delete the entry.
    del notes[str(id)]

    #Update the Cloud Storage.
    state.blob_r.upload_from_string(dumps(notes))

    return (True,None)


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

#----------------
# Verification Functions
#----------------


def check_int_positive(*args:Optional[int]) -> Tuple[bool,Optional[str]]:
    """Check if an integer is valid for id.

    Args:
        prospect (Optional[int]): The integer to check. 

    Returns:
        Tuple[bool,Optional[str]]:
            - bool: True if setup was success without errors. False if not. 
            - str: Error Message if bool is False. None if True
    """

    if len(args) == 0:
        return (False,"Argument 0 is not provided.")

    for idx, i in enumerate(args):
        
        #Check that they are strings.
        if not isinstance(i,int):
            return (False,f"Argument {idx} is not an integer.")
        
        #Check that they are not negative.
        if i < 0:
            return (False,f"Argument {idx} is negative.")
        
    
    return (True,None)

def check_string(*args:Optional[str]) -> Tuple[bool,Optional[str]]:
    """Check strings for validity and non-empty.

    Args:
        prospect (Optional[str]): String to check.

    Returns:
        Tuple[bool,Optional[str]]:
            - bool: True if setup was success without errors. False if not. 
            - str: Error Message if bool is False. None if True 
    """
    if len(args) == 0:
        return (False,"Argument 0 is not provided.")


    for idx, s in enumerate(args):

        #Check that they are strings.
        if not isinstance(s,str):
            return (False,f"Argument {idx} is not a string.")
        
        #Check that they are not empty.
        if len(s.strip()) == 0:
            return (False, f"Argument {idx} is empty.")

    
    #Checks out.
    return (True,None)



