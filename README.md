# Bookcase

Bookcase is a flask based web application which uses SQLite, Bootstrap and Google Books API. Users that have registered have the able to keep a list of the books they have read. Users can also search for books, see its information and comment on any book.

## Installing
    $ git clone https://github.com/fmbxnary/flask-bookcase.git
    
##### Note
    You may need to enter your Google Books Api key:
        bookcase.py > GOOGLE_API
        
## Requirements
    $ cd venv/bin/activate
    $ pip install -r requirements.txt
    
## Environment
#### For Mac
    $ flask init-db
    $ export FLASK_APP=bookcase
    $ export FLASK_DEBUG=1
    
#### For Windows
    $ flask init-db
    $ set FLASK_APP=bookcase
    $ set FLASK_DEBUG=1
    
## Running
    $ flask run
      * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
