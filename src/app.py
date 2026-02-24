#type: ignore

from flask import Flask,request,jsonify, Response
from main import setup, add_note, get_note, delete_note, health_check
from typing import Optional, Tuple
from functools import wraps
import os
from main import ErrorCode


#----------------
# Error Code Mapping
#-----------------
ERROR_MAP = {
    ErrorCode.INVALID_INPUT:        (400, "Invalid input provided"),
    ErrorCode.NOT_FOUND:            (404, "Requested resource not found"),
    ErrorCode.PERMISSION_DENIED:    (403, "Permission denied"),
    ErrorCode.SERVER_ERROR:         (500, "Internal server error"),
    ErrorCode.NOT_FOUND_USE_LOCAL:  (200, "Using local data as fallback (remote not found)"),
    ErrorCode.PERMISSION_DENIED_USE_LOCAL: (200, "Using local data as fallback (permission denied)"),
    ErrorCode.SERVER_ERROR_USE_LOCAL: (200, "Using local data as fallback (server error)"),
    ErrorCode.SETUP_REQUIRED: (403, "Setup must be run first.")
}



#--------------
#Flask App Creation
#----------------

app = Flask(__name__)
API_key = os.getenv("API_KEY", "default_key")


#----------
#Wrapper Functions
#-----------


def handle_response(key: str = None):
    """
    Decorator for Flask endpoints.

    -Handles errors returned from main.py functions.
    -Wraps successful responses in a consistent JSON structure.

    Args:
        key (str): Optional key to use in the JSON response for successful data.
    """
    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            result = func(*args, **kwargs)

            def map_error(err):
                if isinstance(err,ErrorCode):
                    code, msg = ERROR_MAP.get(err, (500, "unknown error"))
                    return code, msg
                return (500, str(err))
            
            #If this is for our Delete, Setup, or Add Endpoints...
            if len(result) == 2:

                #For Delete., Setup..., Add....
               
                
                if result[0]:
                    return jsonify({"success": result[0],"message":"Operation was successful."})
                else:
                    code,err = map_error(result[1])

                    #The result was technically a success, but we want to show it anyway.
                    if result[1] in [ErrorCode.NOT_FOUND_USE_LOCAL,ErrorCode.PERMISSION_DENIED_USE_LOCAL,ErrorCode.SERVER_ERROR_USE_LOCAL]:
                        return  jsonify({"success": True,"message":err}), code
                    
                    return jsonify({"success": result[0],"error":err}), code
            
            #This is for our get
            elif len(result) == 3:
                
                if key:


                    if result[0]:
                        return jsonify({"success": result[0],"notes":result[2]})
                    
                    else:
                        code, err = map_error(result[1])

                        #The result was technically a success, but we want to show it anyway.
                        if result[1] in [ErrorCode.NOT_FOUND_USE_LOCAL,ErrorCode.PERMISSION_DENIED_USE_LOCAL,ErrorCode.SERVER_ERROR_USE_LOCAL]:
                            return  jsonify({"success": True,"message":err}), code
                        
                        return jsonify({"success": result[0],"error":err}), code
        
            return jsonify({"success": False,"error":"Unknown error"}), 500

        return wrapper
    return decorator

def require_api_key(func):
    """
    Decorator for Flask endpoints.

    -Handles checking of API key.
    -Wraps successful responses in a consistent JSON structure.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-KEY")

        if key != API_key:
            return jsonify({"success": False,"error":"Unauthorized"}), 401
        
        return func(*args,**kwargs)
    return wrapper
    
        
    

        


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
    if not data or "bucket" not in data:
        return False,"bucket is a required field."
    
    return setup(data["bucket"])
    
#Simple method for checking health of the server.
# Not protected by API key, nor the handle_response() wrapper since it's just a health check.
@app.route("/health", methods=["GET"])
def health_check_endpoint() -> Tuple[Response,Optional[int]]:
    """
    GET /health
    Simple health check endpoint.

    Returns:
        (Response,Optional[int]):
            - Response: jsonified response with "success" and "error" fields.  
            - Optional[int]: If not successful, error code.
    """

    ok, msg = health_check()
    if ok:
        return jsonify({"success": True,"message":msg}), 200
    else:
        return jsonify({"success": True,"error":msg}), 200

#Function to handle the posting of notes, through the notes route and the POST HTML type.
@app.route("/notes", methods = ["POST"])
@require_api_key
@handle_response()
def add_note_endpoint() -> tuple(Response,Optional[int]):
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

    if not data or "title" not in data or "content" not in data:
        return False,"title and content fields are required."

    title = data["title"]
    content = data["content"]

    
    return add_note(title,content)

#Function to handle the getting of notes, through the notes route and the GET HTML type.
@app.route("/notes",methods=["GET"])
@require_api_key
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
@require_api_key
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

    
    



