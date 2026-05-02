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


@app.route("/health")
def health():
    return "App is running 🚀"


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        try:
            name = request.form["name"]
            email = request.form["email"]
            password = generate_password_hash(request.form["password"])

            conn = get_db_connection()
            if conn is None:
                return "Database connection failed"

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
                return "Database connection failed"

            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()

            cursor.close()
            conn.close()

            if user and check_password_hash(user["password"], password):
                session["user_id"] = user["id"]
                session["name"] = user["name"]
                session["role"] = user["role"]
                return redirect("/dashboard")

            return "Invalid credentials"

        except Exception as e:
            return f"Login error: {e}"

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    try:
        conn = get_db_connection()
        if conn is None:
            return "Database connection failed"

        cursor = conn.cursor(dictionary=True)

        if session.get("role") == "admin":
            cursor.execute("""
                SELECT 
                    tasks.id,
                    tasks.project_id,
                    tasks.title,
                    tasks.description,
                    tasks.due_date,
                    tasks.priority,
                    tasks.status,
                    projects.name AS project_name,
                    users.name AS assigned_user
                FROM tasks
                JOIN projects ON tasks.project_id = projects.id
                JOIN users ON tasks.assigned_to = users.id
                ORDER BY tasks.due_date ASC
            """)
        else:
            cursor.execute("""
                SELECT 
                    tasks.id,
                    tasks.project_id,
                    tasks.title,
                    tasks.description,
                    tasks.due_date,
                    tasks.priority,
                    tasks.status,
                    projects.name AS project_name,
                    users.name AS assigned_user
                FROM tasks
                JOIN projects ON tasks.project_id = projects.id
                JOIN users ON tasks.assigned_to = users.id
                WHERE tasks.assigned_to = %s
                ORDER BY tasks.due_date ASC
            """, (session["user_id"],))

        tasks = cursor.fetchall()

        total_tasks = len(tasks)
        todo_tasks = sum(1 for task in tasks if task["status"] == "To Do")
        progress_tasks = sum(1 for task in tasks if task["status"] == "In Progress")
        done_tasks = sum(1 for task in tasks if task["status"] == "Done")

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

    except Exception as e:
        return f"Dashboard error: {e}"


@app.route("/create_project", methods=["GET", "POST"])
def create_project():
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied"

    if request.method == "POST":
        try:
            name = request.form["name"]
            description = request.form["description"]

            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO projects (name, description, created_by) VALUES (%s, %s, %s)",
                (name, description, session["user_id"])
            )

            conn.commit()
            cursor.close()
            conn.close()

            return redirect("/dashboard")

        except Exception as e:
            return f"Error: {e}"

    return render_template("create_project.html")


@app.route("/create_task", methods=["GET", "POST"])
def create_task():
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        try:
            title = request.form["title"]
            description = request.form["description"]
            due_date = request.form["due_date"]
            priority = request.form["priority"]
            project_id = request.form["project_id"]
            assigned_to = request.form["assigned_to"]

            cursor.execute("""
                INSERT INTO tasks 
                (title, description, due_date, priority, project_id, assigned_to)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (title, description, due_date, priority, project_id, assigned_to))

            conn.commit()
            cursor.close()
            conn.close()

            return redirect("/dashboard")

        except Exception as e:
            return f"Error: {e}"

    cursor.execute("SELECT * FROM projects")
    projects = cursor.fetchall()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("create_task.html", projects=projects, users=users)


@app.route("/update_status/<int:task_id>/<status>")
def update_status(task_id, status):
    if "user_id" not in session:
        return redirect("/login")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE tasks SET status=%s WHERE id=%s",
            (status, task_id)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/dashboard")

    except Exception as e:
        return f"Error: {e}"


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# 🚀 IMPORTANT FOR RAILWAY
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)