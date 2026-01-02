#type: ignore

from flask import Flask,request,jsonify, Response
from main import setup, add_note, get_note, delete_note
from typing import Optional, Tuple
from functools import wraps


#--------------
#Flask App Creation
#----------------

app = Flask(__name__)


#----------
#Wrapper Functions
#-----------

def handle_response(key: str = None):
    """
    Decorator for Flsk endpoints.

    -Handles erros returned from main.py functions.
    -Wraps successful responses in a consistent JSON structure.

    Args:
        key (str): Optional key to use in the JSON response for successful data.
    """
    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            result = func(*args, **kwargs)
            
            #If this is for our Delete, Setup, or Add Endpoints...
            if len(result) == 2:

                #For Delete., Setup..., Add....
               
                
                    if result[0]:
                        return jsonify({"success": result[0]})
                    else:
                        return jsonify({"success": result[0],"error":result[1]}), 500
            
            #This is for our get
            elif len(result) == 3:
                
                if key:

                    if result[0]:
                        return jsonify({"success": result[0],"notes":result[2]})
                    else:
                        return jsonify({"success": result[0],"error":result[1]}), 404

                else:
                    return jsonify({"success": result[0],"error":result[1]}), 500

        return wrapper
    return decorator



        


#----------
#Route Functions
#-----------

#Function to handle the setup Route, used by the POST HTML type.
@app.route("/setup", methods=["POST"])
@handle_response()
def setup_endpoint() -> Tuple[Response,Optional[int]]:
    """
    POST /setup
    Calls setup() in main.py

    Request JSON:
    {
        "bucket": "<bucket name>"
    }

    Returns:
        (Response,Optional[int]):
            - Response: jsonified response with "success" and "error" fields.  
            - Optional[int]: If not successful, error code.
    """    

    #Get the data.
    data = request.get_json()

    #We need our bucket name for setup. If  we don't have a bucket name, or we don't get data...
    if not data or if "bucket" not in data:
        return False,"bucket is a required field."
    
    return setup(data["bucket"])
    
    

#Function to handle the posting of notes, through the notes route and the POST HTML type.
@app.route("/notes", methods = ["POST"])
@handle_response()
def add_note_endpoint() -> Tuple(Response,Optional[int]):
    """
    POST /notes
    Calls add_note() in main.py

    Request JSON:
    {
        "title": "<note title>",
        "content": "<note content>"
    }

    Returns:
        (Response,Optional[int]):
            - Response: jsonified response with "success" and "error" fields.  
            - Optional[int]: If not successful, error code.
    """    

    data = request.get_json()

    if not data or "title" not in data, or "content" not in data:
        return False,"title and content fields are required."

    title = data["title"]
    content = data["content"]

    return add_note(title,content)

#Function to handle the getting of notes, through the notes route and the GET HTML type.
@app.route("/notes",methods=["GET"])
@handle_response("notes")
def get_note_endpoint() -> Tuple[Response,Optional[int]]:
    """
    GET /notes:?
    Calls get_note() in main.py

    Query Parameters:
        id (optional): If provided, returns the note with this id. Must be positive
            and exist in the cloud storage.

    Returns:
        (Response,Optional[int]):
            - Response: jsonified response with "success" and "error" fields if failed, "success"
                and "notes" field for success. 
            - Optional[int]: If not successful, error code.
    """    

    note_id = request.args.get("id")
    return get_note(note_id)

#Function to handle the deletion of notes, through the notes route and the GET HTML type.
@app.route("/notes",methods=["DELETE"])
@handle_response("id")
def delete_note_endpoint() -> Tuple[Response,Optional[int]]:
    """
    DELETE /notes:?
    Calls delete_note() in main.py

    Query Parameters:
        id: Required. Positive integer id of note to delete. Must exist in the cloud storage.

    Returns:
        (Response,Optional[int]):
            - Response: jsonified response with "success" and "error" fields if failed, "success"
                and "notes" field for success. 
            - Optional[int]: If not successful, error code.
    """  
    idx = request.args.get("id")
    if not idx:
        return False, "id was not included."
    
    return delete_note(idx)



#---------------
# Conditional Execution
#---------------

if __name__ == "__main__":
    app.run(debug=True)

    
    



