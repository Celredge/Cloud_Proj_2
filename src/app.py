#type: ignore

from flask import Flask,request,jsonify, Response
from main import setup, add_note, get_note, delete_note
from typing import Optional, Tuple

#--------------
#Flask App Creation
#----------------

app = Flask(__name__)

#----------
#Route Functions
#-----------

#Function to handle the setup Route, used by the POST HTML type.
@app.route("/setup", methods=["POST"])
def setup_endpoint() -> Tuple[Response,Optional[int]]:
    """Endpoint Method using the /setup endpoint and POST as it's HTML type. Used to setup the bucket and other things before the API can work.

    Returns:
        (Response,int): The Jsonified Dictionary Response, and an Error Code, if any.
    """

    #Get the data.
    data = request.get_json()

    #We need our bucket name for setup. If  we don't have a bucket name, or we don't get data...
    if not data or "bucket" not in data:
        return jsonify({"success": False,"error":"Bucket name not provided"}), 400
    
    #Get the bucket name, and call setup() in main.py
    bucket_name = data["bucket"]
    success, error = setup(bucket_name)

    #If it was not successful, then send the error to the client.
    if not success:
        return jsonify({"success":False,"error":error}), 500
    
    #Successful. Indicate it was to the client.
    return jsonify({"success":True,"bucket":bucket_name})

#Function to handle the posting of notes, through the notes route and the POST HTML type.
@app.route("/notes", methods = ["POST"])
def add_note_endpoint() -> Tuple(Response,Optional[int]):
    """Endpoint Method of using the /notes endpoint and POST as it's HTML type. Used to Post a note using the API. Must use the setup function above before working.

    Returns:
        (Response,int): Jsonified response of success, and an error code, if any.
    """

    #Request the data
    data = request.get_json()

    #If we don't get any data, send the error back to Client.
    if not data:
        return jsonify({"success": False,"error":"Payload not provided."}), 400
    
    #Get the Title and the Content of the Note from the JSON, since it's a dictionary.
    # / Note: Case sensitive in JSON. Be careful.
    title = data.get("title")
    content = data.get("content")

    #Execute add_note() function in main.
    success, error = add_note(title,content)

    if not success:
         return jsonify({"success":False,"error":error}), 500
    
    return jsonify({"success":True})

#Function to handle the getting of notes, through the notes route and the GET HTML type.
@app.route("/notes",methods=["GET"])
def get_note_endpoint() -> Tuple[Response,Optional[int]]:
    """Endpoint Method of using the /notes endpoint and GET as it's HTML type. Used to get a note/notes using the API. Must use the setup function above before working. Gets all  notes if the id in the json is missing,
    or a specific one if the id is there.

    Returns:
        (Response,int): The response containing the Notes/Note gotten, and an error code if necessary.
    """
    #We must determine which version of the function to invoke.
    if "id" not in request.args.keys() or len(request.args) == 0:

        #Get all notes in the function.
        succ, err, dat = get_note()

        #See if succeeded and handle errors.
        if not succ:
            return jsonify({"success": False,"error": err}), 500
        
        #Successful. Let's send it off.
        return jsonify({"success": True,"notes":dat})
    
    #If we must get a specific id...
    else:
        #Get the specific note from the id.
        idf = request.args.get("id")
        succ, err, dat = get_note(idf)

        #See if succeeded and handle errors.
        if not succ:
            return jsonify({"success": False,"error":err}) , 404
        
        #Successful, let's send it off.
        return jsonify({"success": True,"notes":dat})

#Function to handle the deletion of notes, through the notes route and the GET HTML type.
@app.route("/notes",methods=["DELETE"])
def delete_note_endpoint() -> Tuple[Response,Optional[int]]:
    """Endpoint Method of using the /notes endpoint and DELETE as it's HTML type. Used to delete a note/notes using the API. Must use the setup function above before working. 

    Returns:
        (Response,int): The response containing the Notes/Note gotten, and an error code if necessary.
    """
    

    
    #We must determine which version of the function to invoke.
    if "id" not in request.args.keys():

        #We need the id. No dice.
        return jsonify({"success": False,"error":"id was not included."}) , 404
    
    #Get the id and use the function
    idx = request.args.get("id")

    #Use the function
    succ, err = delete_note(idx)

    #Not successful. Send a message.
    if not succ:
        return jsonify({"success": False,"error":err}) , 500
    
    #Successful. Report the success.
    return jsonify({"success":True,"id":idx})



#---------------
# Conditional Execution
#---------------

if __name__ == "__main__":
    app.run(debug=True)

    
    



