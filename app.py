from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secret_key")


@app.route("/")
def home():
    return "App is LIVE 🚀"   # ✅ TEMP TEST (important)


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
            return "Database connection failed ❌"

        cursor = conn.cursor(dictionary=True)

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

        tasks = cursor.fetchall()

        total_tasks = len(tasks)

        cursor.close()
        conn.close()

        return render_template(
            "dashboard.html",
            tasks=tasks,
            total_tasks=total_tasks
        )

    except Exception as e:
        return f"Dashboard error: {e}"


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# 🚀 REQUIRED FOR RAILWAY
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)