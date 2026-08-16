from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3

app = Flask(__name__, static_folder="static", static_url_path="/static")

app.secret_key = "online-feedback-secret-key"

DATABASE = "database.db"


# =========================
# DATABASE INITIALIZATION
# =========================

def init_db():

    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS Feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            rating INTEGER NOT NULL,
            comments TEXT NOT NULL,
            date_submitted TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# =========================
# HOME PAGE
# =========================

@app.route("/")
def home():

    return render_template("index.html")


# =========================
# SUBMIT FEEDBACK
# =========================

@app.route("/submit-feedback", methods=["POST"])
def submit_feedback():

    name = request.form.get("name")
    email = request.form.get("email")
    rating = request.form.get("rating")
    comments = request.form.get("comments")

    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        INSERT INTO Feedback
        (name, email, rating, comments)
        VALUES (?, ?, ?, ?)
    """, (name, email, rating, comments))

    conn.commit()
    conn.close()

    return render_template("success.html")


# =========================
# ADMIN LOGIN
# =========================

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin123":

            session["admin_logged_in"] = True

            return redirect(url_for("admin_dashboard"))

        return render_template(
            "admin_login.html",
            error="Invalid username or password"
        )

    return render_template("admin_login.html")


# =========================
# ADMIN DASHBOARD
# =========================

@app.route("/admin-dashboard")
def admin_dashboard():

    # Protect dashboard
    if not session.get("admin_logged_in"):

        return redirect(url_for("admin_login"))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()


    # =========================
    # SEARCH AND FILTER
    # =========================

    search = request.args.get("search", "")
    rating_filter = request.args.get("rating", "")

    query = """
        SELECT *
        FROM Feedback
        WHERE 1=1
    """

    params = []


    # Search name, email or comments
    if search:

        query += """
            AND (
                name LIKE ?
                OR email LIKE ?
                OR comments LIKE ?
            )
        """

        search_value = "%" + search + "%"

        params.extend([
            search_value,
            search_value,
            search_value
        ])


    # Filter by rating
    if rating_filter:

        query += " AND rating = ?"

        params.append(rating_filter)


    # Latest feedback first
    query += " ORDER BY date_submitted DESC"


    cursor.execute(query, params)

    feedbacks = cursor.fetchall()


    # =========================
    # TOTAL FEEDBACK
    # =========================

    cursor.execute("""
        SELECT COUNT(*)
        FROM Feedback
    """)

    total_feedback = cursor.fetchone()[0]


    # =========================
    # AVERAGE RATING
    # =========================

    cursor.execute("""
        SELECT AVG(rating)
        FROM Feedback
    """)

    average_rating = cursor.fetchone()[0]


    # =========================
    # FIVE STAR FEEDBACK
    # =========================

    cursor.execute("""
        SELECT COUNT(*)
        FROM Feedback
        WHERE rating = 5
    """)

    five_star_feedback = cursor.fetchone()[0]


    conn.close()


    # Handle empty database
    if average_rating is None:

        average_rating = 0

    else:

        average_rating = round(average_rating, 2)


    return render_template(
        "admin.html",
        feedbacks=feedbacks,
        total_feedback=total_feedback,
        average_rating=average_rating,
        five_star_feedback=five_star_feedback
    )


# =========================
# DELETE FEEDBACK
# =========================

@app.route("/delete-feedback/<int:feedback_id>", methods=["POST"])
def delete_feedback(feedback_id):

    # Protect delete function
    if not session.get("admin_logged_in"):

        return redirect(url_for("admin_login"))


    conn = sqlite3.connect(DATABASE)

    conn.execute(
        "DELETE FROM Feedback WHERE id = ?",
        (feedback_id,)
    )

    conn.commit()
    conn.close()


    return redirect(url_for("admin_dashboard"))


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.pop("admin_logged_in", None)

    return redirect(url_for("admin_login"))


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":

    init_db()

    app.run(debug=True)