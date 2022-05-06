from flask import (
    Blueprint, flash, redirect, render_template, request, url_for, session
)
import requests

from bookcase.auth import login_required
from bookcase.db import get_db

bp = Blueprint('bookcase', __name__)
GOOGLE_API = ""  # enter your google books api


@bp.context_processor
@login_required
def inject_books():
    """return the number of books from the database that the user has read

    Returns:
        dict: length of books
    """
    db = get_db()
    books = db.execute(
        "SELECT * FROM reads"
        " WHERE user_id=(?)",
        (session['user_id'],)
    ).fetchall()
    return {'bookCount': len(books)}


@bp.route('/')
@login_required
def index():
    """index page of the bookcase app

    Returns:
        Any: Renders index template from the template folder with the given context
    """
    db = get_db()
    comments = db.execute(
        "SELECT comment, username, book.title, user.id"
        " FROM comments"
        " INNER JOIN user, book"
        " ON user.id=comments.user_id"
        " AND book.id=comments.book_id"
        " ORDER BY comments.id DESC"
        " LIMIT 3").fetchall()
    most_books = db.execute(
        "SELECT title, author, COUNT(book_id) as cnt"
        " FROM book"
        " INNER JOIN reads"
        " ON book.id=reads.book_id"
        " GROUP BY (title)"
        " ORDER BY COUNT(book_id) DESC"
        " LIMIT 10").fetchall()
    return render_template('site/index.html', comments=comments, mostBooks=most_books)


@bp.route('/profile/<string:id>')
@login_required
def profile(id):
    """Profile page of the users

    Args:
        id (str): user id

    Returns:
        Any: Renders profile template from the template folder with the given context
    """
    db = get_db()

    # return the last book that user has read
    last_book = db.execute(
        "SELECT book.title"
        " FROM book"
        " INNER JOIN reads"
        " ON book.id=reads.book_id"
        " WHERE reads.user_id=(?)"
        " ORDER BY book.id DESC LIMIT 1",
        (id,)).fetchone()

    # return user from the database by given id
    user = db.execute(
        "SELECT * FROM user WHERE id=(?)", (id,)).fetchone()

    return render_template('site/profile.html', user=user, last_book=last_book)


@bp.route('/search', methods=('GET', 'POST'))
@login_required
def search():
    """Search books by Google Books API and tries to add to database if it not exist in the database

    Returns:
        Any: Renders search template from the template folder with the given context
    """
    if request.method == 'GET':
        db = get_db()

        # title of the book provided by user
        query = request.args.get('search', '')

        # ensure title was submitted
        if not query:
            return redirect(url_for('index'))

        # Google Books API url with the query that provided by user
        search_url = "https://www.googleapis.com/books/v1/volumes?q=" + \
            query + "&maxResults=40&" + GOOGLE_API

        # return json data of the search from Google Books API
        json_book = requests.get(search_url).json()

        # initialize a empty list for the books in the json data
        books = []

        # add all the books in the json data to the books list
        for item in json_book['items']:
            try:
                bookimg = item['volumeInfo']['imageLinks']['thumbnail']
            except KeyError:
                bookimg = url_for(
                    'static', filename='images/no_cover_thumb.gif')

            try:
                bookrate = item['volumeInfo']['averageRating']
            except KeyError:
                bookrate = 0

            try:
                bookid = item['id']
            except KeyError:
                bookid = ""

            try:
                bookpages = item['volumeInfo']['pageCount']
            except KeyError:
                bookpages = 0

            try:
                bookauthor = item['volumeInfo']['authors'][0]
            except KeyError:
                bookauthor = ""

            try:
                booktitle = item['volumeInfo']['title']
            except KeyError:
                booktitle = ""

            try:
                bookdesc = item['volumeInfo']['description']
            except KeyError:
                bookdesc = ""

            try:
                if item['volumeInfo']['industryIdentifiers'][0]['type']:
                    bookisbn = item['volumeInfo'][
                        'industryIdentifiers'][0]['identifier']
                elif item['volumeInfo']['industryIdentifiers'][1]['type']:
                    bookisbn = item['volumeInfo'][
                        'industryIdentifiers'][1]['identifier']
            except KeyError:
                bookisbn = ""

            # create a dictionary of a book with the provided variables
            book = {
                "BookAuthor": bookauthor,
                "BookID": bookid,
                "BookTitle": booktitle,
                "BookDesc": bookdesc,
                "BookIsbn": bookisbn,
                "BookImg": bookimg,
                "BookRate": bookrate,
                "BookPages": bookpages,
            }

            # add the created book dictionary to the books list
            books.append(book)

        # insert all the books into database from the books list
        for book in books:
            try:
                db.execute(
                    "INSERT INTO book"
                    " (bookid, img, isbn, title, author, page, rate, desc)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (book['BookID'], book['BookImg'], book['BookIsbn'], book['BookTitle'],
                     book['BookAuthor'], book['BookPages'], book['BookRate'], book['BookDesc'])
                )
                db.commit()
            except db.IntegrityError:
                pass
        return render_template('site/search.html', books=books)
    return render_template('site/search.html')


# adds the user's comment to the database
@bp.route('/comment', methods=['POST'])
@login_required
def comment():
    db = get_db()

    # get user's comment
    comment = request.form['comment']
    id = int(request.form['bookid'])
    bookid = request.form['gid']
    wordLen = len(comment.split())
    comment2 = db.execute(
        "SELECT comment"
        " FROM comments"
        " WHERE comments.user_id=(?)"
        " AND comments.book_id=(?)",
        (session['user_id'], id)
    ).fetchall()
    if wordLen < 20:
        flash("The comment is too short!", category='error')
    elif wordLen > 100:
        flash("The comment is too long!", category='error')
    elif len(comment2) == 0:
        db.execute(
            "INSERT INTO comments"
            " (user_id, book_id, comment)"
            " VALUES (?, ?, ?)",
            (session['user_id'], id, comment)
        )
        db.commit()
    else:
        flash("You have already a comment on this book!", category='error')
    if request.method == 'POST':
        return redirect(url_for('bookcase.details', id=bookid))


@bp.route('/details/<string:id>', methods=('GET', 'POST'))
@login_required
def details(id):
    db = get_db()
    book = db.execute("SELECT * FROM book WHERE bookid=(?)",
                      (id,)).fetchall()[0]
    comments = db.execute(
        "SELECT comment, user.username"
        " FROM comments"
        " INNER JOIN book"
        " ON comments.book_id=book.id"
        " INNER JOIN user"
        " ON comments.user_id=user.id"
        " WHERE book.bookid=(?)",
        (id,)
    ).fetchall()

    added = False

    if request.method == 'POST':

        # return user id and book id from reads table if user has read and return empty list if did not read
        info = db.execute("SELECT user_id, book_id FROM reads WHERE user_id=(?) AND book_id=(?)",
                          (session['user_id'], book['id'])).fetchall()

        # if user did not read the book
        if len(info) == 0:

            # insert the informations about the user has read this book
            db.execute("INSERT INTO reads (user_id, book_id) VALUES (?, ?)",
                       (session['user_id'], book['id']))

            # inform user about success of adding the book to its library
            flash(
                f"{book['title']} has added into your library successfully", category='success')
            added = True
            db.commit()
        else:
            db.execute("DELETE FROM reads WHERE user_id=(?) AND book_id=(?)",
                       (session['user_id'], book['id']))
            flash(
                f"{book['title']} has deleted from your library successfully", category='error')

            db.commit()
        return render_template('site/details.html', book=book, added=added)
    info = db.execute("SELECT user_id, book_id"
                      " FROM reads"
                      " WHERE user_id=(?)"
                      " AND book_id=(?)",
                      (session['user_id'], book['id'])
                      ).fetchall()
    if len(info) != 0:
        added = True
    return render_template('site/details.html', book=book, added=added, comments=comments)


@bp.route('/books')
@login_required
def my_books():
    """shows a list that the user has read

    Returns:
        Any: Renders books template from the templatefolder with the given context
    """
    db = get_db()
    books = db.execute(
        "SELECT book.title, reads.timestamp, book.bookid, book.img"
        " FROM book"
        " INNER JOIN reads"
        " ON book.id=reads.book_id"
        " WHERE reads.user_id=(?)",
        (session['user_id'],)
    ).fetchall()
    return render_template('site/books.html', books=books)


@bp.app_errorhandler(404)
def page_not_found(e):
    """Direct user to 404 error page if the requested page is not exist

    Args:
        e (Any): error message

    Returns:
        Any: Renders 404 template from the template folder
    """
    return render_template('site/404.html')
