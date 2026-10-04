import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date


# ---------------- DATABASE ----------------

con = sqlite3.connect("library.db")
cur = con.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS books(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    author TEXT,
    category TEXT,
    quantity INTEGER,
    available INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS members(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    email TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS issues(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER,
    member_id INTEGER,
    issue_date TEXT,
    return_date TEXT,
    status TEXT
)
""")

con.commit()


# ---------------- FUNCTIONS ----------------

def add_book():
    name = book_name.get().strip()
    author = book_author.get().strip()
    category = book_category.get().strip()
    quantity = book_quantity.get().strip()

    if not name or not author or not category or not quantity:
        messagebox.showerror("Error", "Please fill all fields")
        return

    try:
        quantity = int(quantity)

        if quantity <= 0:
            raise ValueError

        cur.execute("""
        INSERT INTO books(name, author, category, quantity, available)
        VALUES(?,?,?,?,?)
        """, (name, author, category, quantity, quantity))

        con.commit()

        book_name.delete(0, tk.END)
        book_author.delete(0, tk.END)
        book_category.delete(0, tk.END)
        book_quantity.delete(0, tk.END)

        show_books()
        messagebox.showinfo("Success", "Book added successfully")

    except ValueError:
        messagebox.showerror("Error", "Quantity must be a valid number")


def show_books():
    for row in book_table.get_children():
        book_table.delete(row)

    rows = cur.execute("SELECT * FROM books").fetchall()

    for row in rows:
        book_table.insert("", tk.END, values=row)


def delete_book():
    selected = book_table.selection()

    if not selected:
        messagebox.showwarning("Warning", "Select a book first")
        return

    book_id = book_table.item(selected[0])["values"][0]

    active = cur.execute(
        "SELECT COUNT(*) FROM issues WHERE book_id=? AND status='Issued'",
        (book_id,)
    ).fetchone()[0]

    if active:
        messagebox.showerror("Error", "This book is currently issued")
        return

    cur.execute("DELETE FROM books WHERE id=?", (book_id,))
    con.commit()

    show_books()


def add_member():
    name = member_name.get().strip()
    phone = member_phone.get().strip()
    email = member_email.get().strip()

    if not name or not phone or not email:
        messagebox.showerror("Error", "Please fill all fields")
        return

    cur.execute("""
    INSERT INTO members(name, phone, email)
    VALUES(?,?,?)
    """, (name, phone, email))

    con.commit()

    member_name.delete(0, tk.END)
    member_phone.delete(0, tk.END)
    member_email.delete(0, tk.END)

    show_members()

    messagebox.showinfo("Success", "Member added successfully")


def show_members():
    for row in member_table.get_children():
        member_table.delete(row)

    rows = cur.execute("SELECT * FROM members").fetchall()

    for row in rows:
        member_table.insert("", tk.END, values=row)


def delete_member():
    selected = member_table.selection()

    if not selected:
        messagebox.showwarning("Warning", "Select a member first")
        return

    member_id = member_table.item(selected[0])["values"][0]

    active = cur.execute(
        "SELECT COUNT(*) FROM issues WHERE member_id=? AND status='Issued'",
        (member_id,)
    ).fetchone()[0]

    if active:
        messagebox.showerror(
            "Error",
            "This member has an issued book"
        )
        return

    cur.execute(
        "DELETE FROM members WHERE id=?",
        (member_id,)
    )

    con.commit()
    show_members()


def issue_book():
    try:
        book_id = int(issue_book_id.get())
        member_id = int(issue_member_id.get())

        book = cur.execute(
            "SELECT available FROM books WHERE id=?",
            (book_id,)
        ).fetchone()

        member = cur.execute(
            "SELECT id FROM members WHERE id=?",
            (member_id,)
        ).fetchone()

        if book is None:
            messagebox.showerror("Error", "Book ID not found")
            return

        if member is None:
            messagebox.showerror("Error", "Member ID not found")
            return

        if book[0] <= 0:
            messagebox.showerror("Error", "Book is not available")
            return

        cur.execute("""
        INSERT INTO issues(book_id, member_id, issue_date, status)
        VALUES(?,?,?,?)
        """, (
            book_id,
            member_id,
            str(date.today()),
            "Issued"
        ))

        cur.execute("""
        UPDATE books
        SET available = available - 1
        WHERE id=?
        """, (book_id,))

        con.commit()

        issue_book_id.delete(0, tk.END)
        issue_member_id.delete(0, tk.END)

        show_books()
        show_issues()

        messagebox.showinfo("Success", "Book issued successfully")

    except ValueError:
        messagebox.showerror(
            "Error",
            "Enter valid Book ID and Member ID"
        )


def return_book():
    try:
        issue_id = int(return_issue_id.get())

        record = cur.execute("""
        SELECT book_id, status
        FROM issues
        WHERE id=?
        """, (issue_id,)).fetchone()

        if record is None:
            messagebox.showerror("Error", "Issue record not found")
            return

        if record[1] == "Returned":
            messagebox.showerror("Error", "Book already returned")
            return

        cur.execute("""
        UPDATE issues
        SET return_date=?, status=?
        WHERE id=?
        """, (
            str(date.today()),
            "Returned",
            issue_id
        ))

        cur.execute("""
        UPDATE books
        SET available = available + 1
        WHERE id=?
        """, (record[0],))

        con.commit()

        return_issue_id.delete(0, tk.END)

        show_books()
        show_issues()

        messagebox.showinfo(
            "Success",
            "Book returned successfully"
        )

    except ValueError:
        messagebox.showerror(
            "Error",
            "Enter a valid Issue ID"
        )


def show_issues():
    for row in issue_table.get_children():
        issue_table.delete(row)

    rows = cur.execute("""
    SELECT issues.id,
           books.name,
           members.name,
           issues.issue_date,
           issues.return_date,
           issues.status
    FROM issues
    JOIN books ON issues.book_id = books.id
    JOIN members ON issues.member_id = members.id
    ORDER BY issues.id DESC
    """).fetchall()

    for row in rows:
        issue_table.insert("", tk.END, values=row)


# ---------------- WINDOW ----------------

root = tk.Tk()
root.title("Library Management System")
root.geometry("1000x650")
root.minsize(900, 600)


# ---------------- STYLE ----------------

style = ttk.Style()

style.configure(
    "Title.TLabel",
    font=("Arial", 24, "bold")
)

style.configure(
    "Heading.TLabel",
    font=("Arial", 14, "bold")
)

style.configure(
    "TButton",
    font=("Arial", 10),
    padding=6
)

style.configure(
    "Treeview",
    rowheight=28,
    font=("Arial", 10)
)

style.configure(
    "Treeview.Heading",
    font=("Arial", 10, "bold")
)


# ---------------- HEADER ----------------

header = tk.Frame(root, pady=15)

header.pack(fill="x")

tk.Label(
    header,
    text="📚 Library Management System",
    font=("Arial", 24, "bold")
).pack()

tk.Label(
    header,
    text="Manage books, members and issue / return records",
    font=("Arial", 10)
).pack(pady=3)


# ---------------- TABS ----------------

tabs = ttk.Notebook(root)

tabs.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=5
)


books_tab = ttk.Frame(tabs)
members_tab = ttk.Frame(tabs)
issue_tab = ttk.Frame(tabs)
records_tab = ttk.Frame(tabs)

tabs.add(books_tab, text="  Books  ")
tabs.add(members_tab, text="  Members  ")
tabs.add(issue_tab, text="  Issue / Return  ")
tabs.add(records_tab, text="  Records  ")


# =========================================================
# BOOK TAB
# =========================================================

book_form = ttk.LabelFrame(
    books_tab,
    text="Add New Book",
    padding=15
)

book_form.pack(
    fill="x",
    padx=15,
    pady=15
)


tk.Label(book_form, text="Book Name").grid(
    row=0, column=0, padx=5, pady=5
)

book_name = ttk.Entry(book_form, width=22)

book_name.grid(
    row=0, column=1, padx=5, pady=5
)


tk.Label(book_form, text="Author").grid(
    row=0, column=2, padx=5
)

book_author = ttk.Entry(
    book_form,
    width=22
)

book_author.grid(
    row=0, column=3, padx=5
)


tk.Label(book_form, text="Category").grid(
    row=1, column=0, padx=5, pady=5
)

book_category = ttk.Entry(
    book_form,
    width=22
)

book_category.grid(
    row=1, column=1, padx=5
)


tk.Label(book_form, text="Quantity").grid(
    row=1, column=2, padx=5
)

book_quantity = ttk.Entry(
    book_form,
    width=22
)

book_quantity.grid(
    row=1, column=3, padx=5
)


ttk.Button(
    book_form,
    text="Add Book",
    command=add_book
).grid(
    row=0,
    column=4,
    rowspan=2,
    padx=20
)


# Book table

book_table = ttk.Treeview(
    books_tab,
    columns=(
        "id",
        "name",
        "author",
        "category",
        "quantity",
        "available"
    ),
    show="headings"
)

for col, text, width in [
    ("id", "ID", 60),
    ("name", "Book Name", 230),
    ("author", "Author", 180),
    ("category", "Category", 150),
    ("quantity", "Quantity", 100),
    ("available", "Available", 100)
]:

    book_table.heading(col, text=text)
    book_table.column(col, width=width)


book_table.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=5
)


ttk.Button(
    books_tab,
    text="Delete Selected Book",
    command=delete_book
).pack(pady=10)


# =========================================================
# MEMBER TAB
# =========================================================

member_form = ttk.LabelFrame(
    members_tab,
    text="Add New Member",
    padding=15
)

member_form.pack(
    fill="x",
    padx=15,
    pady=15
)


tk.Label(member_form, text="Name").grid(
    row=0, column=0, padx=5
)

member_name = ttk.Entry(
    member_form,
    width=25
)

member_name.grid(
    row=0, column=1, padx=5
)


tk.Label(member_form, text="Phone").grid(
    row=0, column=2, padx=5
)

member_phone = ttk.Entry(
    member_form,
    width=20
)

member_phone.grid(
    row=0, column=3, padx=5
)


tk.Label(member_form, text="Email").grid(
    row=0, column=4, padx=5
)

member_email = ttk.Entry(
    member_form,
    width=25
)

member_email.grid(
    row=0, column=5, padx=5
)


ttk.Button(
    member_form,
    text="Add Member",
    command=add_member
).grid(
    row=0,
    column=6,
    padx=15
)


member_table = ttk.Treeview(
    members_tab,
    columns=("id", "name", "phone", "email"),
    show="headings"
)

for col, text, width in [
    ("id", "ID", 70),
    ("name", "Name", 250),
    ("phone", "Phone", 180),
    ("email", "Email", 300)
]:

    member_table.heading(col, text=text)
    member_table.column(col, width=width)


member_table.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=10
)


ttk.Button(
    members_tab,
    text="Delete Selected Member",
    command=delete_member
).pack(pady=10)


# =========================================================
# ISSUE / RETURN TAB
# =========================================================

issue_title = tk.Label(
    issue_tab,
    text="Issue or Return a Book",
    font=("Arial", 18, "bold")
)

issue_title.pack(pady=25)


issue_form = ttk.LabelFrame(
    issue_tab,
    text="Issue Book",
    padding=20
)

issue_form.pack(
    padx=100,
    fill="x"
)


tk.Label(
    issue_form,
    text="Book ID"
).grid(
    row=0, column=0, padx=10
)

issue_book_id = ttk.Entry(
    issue_form,
    width=15
)

issue_book_id.grid(
    row=0, column=1,
    padx=10
)


tk.Label(
    issue_form,
    text="Member ID"
).grid(
    row=0, column=2,
    padx=10
)

issue_member_id = ttk.Entry(
    issue_form,
    width=15
)

issue_member_id.grid(
    row=0, column=3,
    padx=10
)


ttk.Button(
    issue_form,
    text="Issue Book",
    command=issue_book
).grid(
    row=0, column=4,
    padx=20
)


return_form = ttk.LabelFrame(
    issue_tab,
    text="Return Book",
    padding=20
)

return_form.pack(
    padx=100,
    fill="x",
    pady=25
)


tk.Label(
    return_form,
    text="Issue ID"
).grid(
    row=0, column=0, padx=10
)

return_issue_id = ttk.Entry(
    return_form,
    width=15
)

return_issue_id.grid(
    row=0, column=1,
    padx=10
)


ttk.Button(
    return_form,
    text="Return Book",
    command=return_book
).grid(
    row=0,
    column=2,
    padx=20
)


tk.Label(
    issue_tab,
    text="Use the Book ID and Member ID from the Books and Members tabs.",
    font=("Arial", 10)
).pack(pady=15)


# =========================================================
# RECORDS TAB
# =========================================================

tk.Label(
    records_tab,
    text="Issue / Return Records",
    font=("Arial", 18, "bold")
).pack(pady=20)


issue_table = ttk.Treeview(
    records_tab,
    columns=(
        "id",
        "book",
        "member",
        "issue_date",
        "return_date",
        "status"
    ),
    show="headings"
)

for col, text, width in [
    ("id", "Issue ID", 80),
    ("book", "Book", 220),
    ("member", "Member", 200),
    ("issue_date", "Issue Date", 120),
    ("return_date", "Return Date", 120),
    ("status", "Status", 100)
]:

    issue_table.heading(col, text=text)
    issue_table.column(col, width=width)


issue_table.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=10
)


ttk.Button(
    records_tab,
    text="Refresh Records",
    command=show_issues
).pack(pady=10)


# ---------------- LOAD DATA ----------------

show_books()
show_members()
show_issues()


# ---------------- RUN ----------------

root.mainloop()