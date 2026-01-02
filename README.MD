What I learned:

-Flask
    | Acts as the *bridge* between Python code and HTTP.
    | Msotly used for experimentation, or lightweight to medium projects.
    |Uses "Routes" to determine which Python function to invoke.
    |For the note app, one example is /notes, / is the default.
    |You can use request.method in your functions to determine the HTTP type of command.
    (GET -> Get something)
    (POST -> Send something)
    (PATCH -> Partially Update)
    (DELETE -> Delete something)
    (UPDATE -> Fully update something.)

-Syntax
    | Use a *decorator* (@) to specify what HTTP types and the route the function handles.

    Ex: @app.route("/path",methods =[...])
    def function_name():
        return response

    
    /path -> endpoint
    methods=[...] -> Your HTTP methods to respond to. (GET, POST, etc...)
    function_name -> function to handle those types of requests
    return can be text, JSON, or HTML. (Hyper-***text*** markup langauge.)

    | Provides a "request" object to do requests on. requests.method to check method, request.args to get the arguments, requests.get_JSON() to get the JSON from a POST

    | Responses are usually JSON. 
    {status:"ok", "data":...}
    {status:"error","message":...}
    
-app
    |app is usually the handle for a Flask instance/object.
    This represents the web application.
    |All routes, config, and server behaviour are attached.

    | Flask(__name__) -> "reception desk" object.
      app.route(...) -> Tells the desk "This url triggers this function."

      app.run() -> Opens the desk to start recieving visitors.

    | Holds all routes I define. Handles incoming requests, calls appropriate pyhon function, configure debug mode, ports, templates, middleware, etc.

    | @app.route("/notes") is a better representation of:

        def notes(): ...
        app.add_url_rule("/notes", view_func=notes)
    
    | You can use jsonify to pass back things that are dictionaries.
    | Json headers are case sensitive. Be careful!

-Main
    | Usually does more complex logic, while you let the app/Flask object handle the Communication.
    
-Dataclasses
    | Mini classes that just hold data. Come from the dataclasses module. Usually good to avoid globals.
    | Learned about this, but completely forgot.

-Buckets
    | Apparently people usually only use one bucket per environment, so bucket-switching is not needed here?

-Wrappers
    | Functions are objects in Python
    | Wrappers are functions that call other functions, and can do extra work before, or after.
    def wrapper(func):
        def inner(*args, **kwargs)
            print("Running the function...")
            result = func(*args,**kwargs)
            print("Running after the function...")
            return result
        return inner
    | This can be used for exceptions, or modification before or after a function.

If I could do this again:

    I would be able to format things a bit better, I think. There is a lot of repetion in the handle functions.
    I would be able to handle a bit more complex JSON.