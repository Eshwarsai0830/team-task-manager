from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secret_key")


@app.route("/")
def home():
    return redirect("/login")


@app.route("/create_tables")
def create_tables():
    conn = get_db_connection()
    if conn is None:
        return "Database connection failed ❌"

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'member'
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            name TEXT,
            description TEXT,
            created_by INTEGER
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT,
            description TEXT,
            due_date DATE,
            priority TEXT,
            status TEXT DEFAULT 'To Do',
            project_id INTEGER,
            assigned_to INTEGER
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()

    return "Tables created successfully ✅"


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        try:
            name = request.form["name"]
            email = request.form["email"]
            password = generate_password_hash(request.form["password"])

            conn = get_db_connection()
            if conn is None:
                return "Database connection failed ❌"

            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                (name, email, password, "member")
            )
            conn.commit()

            cursor.close()
            conn.close()
            return redirect("/login")

        except Exception as e:
            return f"Signup error: {e}"

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            email = request.form["email"]
            password = request.form["password"]

            conn = get_db_connection()
            if conn is None:
                return "Database connection failed ❌"

            cursor = conn.cursor()

            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()

            cursor.close()
            conn.close()

            if user and check_password_hash(user[3], password):
                session["user_id"] = user[0]
                session["name"] = user[1]
                session["role"] = user[4]
                return redirect("/dashboard")

            return "Invalid credentials"

        except Exception as e:
            return f"Login error: {e}"

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    if conn is None:
        return "Database connection failed ❌"

    cursor = conn.cursor()

    if session.get("role") == "admin":
        cursor.execute("""
            SELECT tasks.id, tasks.project_id, tasks.title, tasks.description,
                   tasks.due_date, tasks.priority, tasks.status,
                   projects.name, users.name
            FROM tasks
            JOIN projects ON tasks.project_id = projects.id
            JOIN users ON tasks.assigned_to = users.id
            ORDER BY tasks.due_date ASC
        """)
    else:
        cursor.execute("""
            SELECT tasks.id, tasks.project_id, tasks.title, tasks.description,
                   tasks.due_date, tasks.priority, tasks.status,
                   projects.name, users.name
            FROM tasks
            JOIN projects ON tasks.project_id = projects.id
            JOIN users ON tasks.assigned_to = users.id
            WHERE tasks.assigned_to = %s
            ORDER BY tasks.due_date ASC
        """, (session["user_id"],))

    rows = cursor.fetchall()

    tasks = []
    for row in rows:
        tasks.append({
            "id": row[0],
            "project_id": row[1],
            "title": row[2],
            "description": row[3],
            "due_date": row[4],
            "priority": row[5],
            "status": row[6],
            "project_name": row[7],
            "assigned_user": row[8]
        })

    total_tasks = len(tasks)
    todo_tasks = sum(1 for t in tasks if t["status"] == "To Do")
    progress_tasks = sum(1 for t in tasks if t["status"] == "In Progress")
    done_tasks = sum(1 for t in tasks if t["status"] == "Done")

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        tasks=tasks,
        today=datetime.today().date(),
        role=session.get("role"),
        total_tasks=total_tasks,
        todo_tasks=todo_tasks,
        progress_tasks=progress_tasks,
        done_tasks=done_tasks
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)