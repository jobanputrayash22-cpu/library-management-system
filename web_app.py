from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import date

app = Flask(__name__)
DB = "library_web.db"


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = db()
    con.execute("""
        CREATE TABLE IF NOT EXISTS books(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            available INTEGER NOT NULL
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS members(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS issues(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            member_id INTEGER NOT NULL,
            issue_date TEXT NOT NULL,
            return_date TEXT,
            status TEXT NOT NULL
        )
    """)
    con.commit()
    con.close()


init_db()

HTML = """
<!doctype html>
<html>
<head>
    <title>Library Management System</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body{font-family:Arial;margin:0;background:#f4f6f8;color:#222}
        header{background:#243447;color:white;padding:25px;text-align:center}
        header h1{margin:0 0 8px}
        .container{max-width:1100px;margin:25px auto;padding:0 15px}
        .card{background:white;padding:20px;margin-bottom:20px;border-radius:8px;box-shadow:0 2px 8px #ddd}
        h2{margin-top:0;color:#243447}
        input,select{padding:9px;margin:4px;border:1px solid #ccc;border-radius:4px}
        button{padding:9px 15px;border:0;border-radius:4px;background:#243447;color:white;cursor:pointer}
        button:hover{background:#162331}
        .danger{background:#b23b3b}
        .success{background:#2e7d32}
        table{width:100%;border-collapse:collapse;margin-top:15px}
        th,td{padding:10px;border-bottom:1px solid #ddd;text-align:left}
        th{background:#eef1f4}
        .row{display:flex;flex-wrap:wrap;align-items:center;gap:5px}
        .msg{padding:10px;background:#fff3cd;border-radius:5px;margin-bottom:15px}
        a{color:#243447}
    </style>
</head>
<body>
<header>
    <h1>📚 Library Management System</h1>
    <div>Books • Members • Issue / Return • Records</div>
</header>

<div class="container">
{% if message %}
<div class="msg">{{ message }}</div>
{% endif %}

<div class="card">
<h2>Book Management</h2>
<form method="post" action="/add-book" class="row">
<input name="name" placeholder="Book Name" required>
<input name="author" placeholder="Author" required>
<input name="category" placeholder="Category" required>
<input name="quantity" type="number" min="1" placeholder="Quantity" required>
<button>Add Book</button>
</form>

<form method="get" class="row" style="margin-top:10px">
<input name="book_search" value="{{ book_search }}" placeholder="Search book / author / category">
<button>Search</button>
<a href="/">Show All</a>
</form>

<table>
<tr><th>ID</th><th>Book</th><th>Author</th><th>Category</th><th>Quantity</th><th>Available</th><th>Action</th></tr>
{% for b in books %}
<tr>
<td>{{b.id}}</td><td>{{b.name}}</td><td>{{b.author}}</td><td>{{b.category}}</td>
<td>{{b.quantity}}</td><td>{{b.available}}</td>
<td><a href="/delete-book/{{b.id}}">Delete</a></td>
</tr>
{% endfor %}
</table>
</div>

<div class="card">
<h2>Member Management</h2>
<form method="post" action="/add-member" class="row">
<input name="name" placeholder="Name" required>
<input name="phone" placeholder="Phone" required>
<input name="email" type="email" placeholder="Email" required>
<button>Add Member</button>
</form>

<table>
<tr><th>ID</th><th>Name</th><th>Phone</th><th>Email</th><th>Action</th></tr>
{% for m in members %}
<tr>
<td>{{m.id}}</td><td>{{m.name}}</td><td>{{m.phone}}</td><td>{{m.email}}</td>
<td><a href="/delete-member/{{m.id}}">Delete</a></td>
</tr>
{% endfor %}
</table>
</div>

<div class="card">
<h2>Issue / Return</h2>
<form method="post" action="/issue" class="row">
<input name="book_id" type="number" placeholder="Book ID" required>
<input name="member_id" type="number" placeholder="Member ID" required>
<button class="success">Issue Book</button>
</form>

<form method="post" action="/return" class="row" style="margin-top:10px">
<input name="issue_id" type="number" placeholder="Issue ID" required>
<button>Return Book</button>
</form>
</div>

<div class="card">
<h2>Issue / Return Records</h2>
<table>
<tr><th>Issue ID</th><th>Book</th><th>Member</th><th>Issue Date</th><th>Return Date</th><th>Status</th></tr>
{% for i in issues %}
<tr>
<td>{{i.id}}</td><td>{{i.book}}</td><td>{{i.member}}</td>
<td>{{i.issue_date}}</td><td>{{i.return_date or '-'}}</td><td>{{i.status}}</td>
</tr>
{% endfor %}
</table>
</div>
</div>
</body>
</html>
"""


def page(message="", book_search=""):
    con = db()

    if book_search:
        books = con.execute("""
            SELECT * FROM books
            WHERE name LIKE ? OR author LIKE ? OR category LIKE ?
            ORDER BY id DESC
        """, (f"%{book_search}%", f"%{book_search}%", f"%{book_search}%")).fetchall()
    else:
        books = con.execute("SELECT * FROM books ORDER BY id DESC").fetchall()

    members = con.execute("SELECT * FROM members ORDER BY id DESC").fetchall()

    issues = con.execute("""
        SELECT issues.*, books.name AS book, members.name AS member
        FROM issues
        JOIN books ON issues.book_id = books.id
        JOIN members ON issues.member_id = members.id
        ORDER BY issues.id DESC
    """).fetchall()

    con.close()

    return render_template_string(
        HTML,
        books=books,
        members=members,
        issues=issues,
        message=message,
        book_search=book_search
    )


@app.route("/")
def home():
    return page(book_search=request.args.get("book_search", ""))


@app.post("/add-book")
def add_book():
    try:
        name = request.form["name"].strip()
        author = request.form["author"].strip()
        category = request.form["category"].strip()
        quantity = int(request.form["quantity"])

        if not name or not author or not category or quantity <= 0:
            return page("Please enter valid book details.")

        con = db()
        con.execute(
            "INSERT INTO books(name,author,category,quantity,available) VALUES(?,?,?,?,?)",
            (name, author, category, quantity, quantity)
        )
        con.commit()
        con.close()
        return redirect("/")
    except Exception:
        return page("Invalid book details.")


@app.post("/add-member")
def add_member():
    try:
        name = request.form["name"].strip()
        phone = request.form["phone"].strip()
        email = request.form["email"].strip()

        if not name or not phone or not email:
            return page("Please enter all member details.")

        con = db()
        con.execute(
            "INSERT INTO members(name,phone,email) VALUES(?,?,?)",
            (name, phone, email)
        )
        con.commit()
        con.close()
        return redirect("/")
    except Exception:
        return page("Invalid member details.")


@app.get("/delete-book/<int:book_id>")
def delete_book(book_id):
    con = db()
    active = con.execute(
        "SELECT COUNT(*) FROM issues WHERE book_id=? AND status='Issued'",
        (book_id,)
    ).fetchone()[0]

    if active:
        con.close()
        return page("Cannot delete a book that is currently issued.")

    con.execute("DELETE FROM books WHERE id=?", (book_id,))
    con.commit()
    con.close()
    return redirect("/")


@app.get("/delete-member/<int:member_id>")
def delete_member(member_id):
    con = db()
    active = con.execute(
        "SELECT COUNT(*) FROM issues WHERE member_id=? AND status='Issued'",
        (member_id,)
    ).fetchone()[0]

    if active:
        con.close()
        return page("Cannot delete a member with an active issue.")

    con.execute("DELETE FROM members WHERE id=?", (member_id,))
    con.commit()
    con.close()
    return redirect("/")


@app.post("/issue")
def issue():
    try:
        book_id = int(request.form["book_id"])
        member_id = int(request.form["member_id"])

        con = db()
        book = con.execute(
            "SELECT available FROM books WHERE id=?", (book_id,)
        ).fetchone()
        member = con.execute(
            "SELECT id FROM members WHERE id=?", (member_id,)
        ).fetchone()

        if not book:
            con.close()
            return page("Book ID not found.")
        if not member:
            con.close()
            return page("Member ID not found.")
        if book["available"] <= 0:
            con.close()
            return page("Book is not available.")

        con.execute("""
            INSERT INTO issues(book_id,member_id,issue_date,status)
            VALUES(?,?,?,?)
        """, (book_id, member_id, str(date.today()), "Issued"))

        con.execute(
            "UPDATE books SET available=available-1 WHERE id=?",
            (book_id,)
        )
        con.commit()
        con.close()
        return redirect("/")
    except Exception:
        return page("Invalid issue request.")


@app.post("/return")
def return_book():
    try:
        issue_id = int(request.form["issue_id"])
        con = db()

        record = con.execute(
            "SELECT book_id,status FROM issues WHERE id=?",
            (issue_id,)
        ).fetchone()

        if not record:
            con.close()
            return page("Issue ID not found.")

        if record["status"] == "Returned":
            con.close()
            return page("This book is already returned.")

        con.execute("""
            UPDATE issues
            SET return_date=?, status='Returned'
            WHERE id=?
        """, (str(date.today()), issue_id))

        con.execute(
            "UPDATE books SET available=available+1 WHERE id=?",
            (record["book_id"],)
        )

        con.commit()
        con.close()
        return redirect("/")
    except Exception:
        return page("Invalid return request.")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
