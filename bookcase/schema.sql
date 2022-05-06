DROP TABLE IF EXISTS user;

DROP TABLE IF EXISTS book;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    job TEXT NOT NULL,
    fav_author TEXT,
    password TEXT NOT NULL
);

CREATE TABLE book (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bookid TEXT UNIQUE NOT NULL,
    isbn TEXT NOT NULL,
    author TEXT NOT NULL,
    title TEXT NOT NULL,
    rate REAL NOT NULL,
    page INTEGER NOT NULL,
    desc TEXT NOT NULL,
    img TEXT NOT NULL
);

CREATE TABLE reads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    book_id INTEGER,
    timestamp TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(user_id) REFERENCES user(id),
    FOREIGN KEY(book_id) REFERENCES book(id)
);

CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    book_id INTEGER,
    comment TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES user(id),
    FOREIGN KEY(book_id) REFERENCES book(id)
);

