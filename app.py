from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret_key"


@app.route("/")
def home():
    return redirect("/login")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                (name, email, password, "member")
            )
            conn.commit()
        except:
            cursor.close()
            conn.close()
            return "Email already exists"

        cursor.close()
        conn.close()
        return redirect("/login")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
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
        else:
            return "Invalid credentials"

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if session.get("role") == "admin":
        cursor.execute("""
            SELECT tasks.id, tasks.project_id, tasks.title, tasks.description,
                   tasks.due_date, tasks.priority, tasks.status,
                   projects.name AS project_name,
                   users.name AS assigned_user
            FROM tasks
            JOIN projects ON tasks.project_id = projects.id
            JOIN users ON tasks.assigned_to = users.id
            ORDER BY tasks.due_date ASC
        """)
    else:
        cursor.execute("""
            SELECT tasks.id, tasks.project_id, tasks.title, tasks.description,
                   tasks.due_date, tasks.priority, tasks.status,
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


@app.route("/create_project", methods=["GET", "POST"])
def create_project():
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied: Only admin can create projects"

    if request.method == "POST":
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

    return render_template("create_project.html")


@app.route("/create_task", methods=["GET", "POST"])
def create_task():
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied: Only admin can create tasks"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        due_date = request.form["due_date"]
        priority = request.form["priority"]
        project_id = request.form["project_id"]
        assigned_to = request.form["assigned_to"]

        cursor.execute(
            """
            INSERT INTO tasks 
            (title, description, due_date, priority, project_id, assigned_to)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (title, description, due_date, priority, project_id, assigned_to)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/dashboard")

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

    allowed_status = ["To Do", "In Progress", "Done"]
    if status not in allowed_status:
        return "Invalid status"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status=%s WHERE id=%s", (status, task_id))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/dashboard")


@app.route("/edit_task/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied: Only admin can edit tasks"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]

        cursor.execute(
            "UPDATE tasks SET title=%s, description=%s WHERE id=%s",
            (title, description, task_id)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/dashboard")

    cursor.execute("SELECT * FROM tasks WHERE id=%s", (task_id,))
    task = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("edit_task.html", task=task)


@app.route("/edit_project/<int:project_id>", methods=["GET", "POST"])
def edit_project(project_id):
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied: Only admin can edit projects"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]

        cursor.execute(
            "UPDATE projects SET name=%s, description=%s WHERE id=%s",
            (name, description, project_id)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/dashboard")

    cursor.execute("SELECT * FROM projects WHERE id=%s", (project_id,))
    project = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("edit_project.html", project=project)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)