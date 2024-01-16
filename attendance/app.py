import os
import secrets
from cs50 import SQL
from flask import (
    Flask,
    redirect,
    render_template,
    jsonify,
    request,
    session,

)
from flask_session import Session

from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from flask_socketio import SocketIO, send
from helpers import apology, login_required, admin_required
import datetime

# Configure application
app = Flask(__name__)

current_username = ""

# Configure session to use filesystem (instead of signed cookies)
app.config["SECRET_KEY"] = secrets.token_hex(32)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

socketio = SocketIO(app, cors_allowed_origins="*")

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///users.db")
datadb = SQL("sqlite:///data.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/attendance")
@login_required
def attendance():
    date_dict = {}

    # Define the number of days for each month
    days_in_month = {
        "Jan": 31,
        "Feb": None,  # Will be determined based on leap year
        "Mar": 31,
        "Apr": 30,
        "May": 31,
        "Jun": 30,
        "Jul": 31,
        "Aug": 31,
        "Sep": 30,
        "Oct": 31,
        "Nov": 30,
        "Dec": 31,
    }

    months = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]

    current_year = datetime.datetime.now().year

    if (current_year % 4 == 0 and current_year % 100 != 0) or (current_year % 400 == 0):
        days_in_month["Feb"] = 29  # Leap year
    else:
        days_in_month["Feb"] = 28

    for month in months:
        last_day = days_in_month[month]

        # dictionary for the month
        month_dict = {}

        # iterate through days from 1 to the last day of the month
        for day in range(1, last_day + 1):
            # dictionary for each day
            day_dict = {}
            month_dict[str(day)] = day_dict

        # Add the month's dictionary to the main date_dict
        date_dict[month] = month_dict

    return render_template("attendance.html", date_dict=date_dict)


@app.route("/members", methods=["GET", "POST"])
@login_required
def members():
    if request.method == "POST":
        clicked_name = request.form.get("member_name")
        print(f"Clicked Name: {clicked_name}")
        return apology("TODO")

    rows = datadb.execute("SELECT * FROM people")
    return render_template("members.html", rows=rows)


@app.route("/live_chat")
@login_required
def chat():
    user_id = session["user_id"]
    username = db.execute("SELECT username FROM users WHERE id = ?", user_id)[0][
        "username"
    ]

    return render_template("chat.html", username=username)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        current_username = request.form.get("username")

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # checking if the values are acceptable
        if not username:
            return apology("Username Error")
        if not password:
            return apology("Password Error")
        if not confirmation:
            return apology("Confirmation Error")

        if password != confirmation:
            return apology("Password and Confirmation DO NOT MATCH")

        # saving it as a hashed pass in db
        hash = generate_password_hash(password)

        try:
            new_user = db.execute(
                "INSERT INTO users (username,hash) VALUES(?,?)", username, hash
            )
        except:
            return apology("Username Already Exists")
        current_username = username
        session["user_id"] = new_user
        return redirect("/")

    else:
        return render_template("register.html")


@socketio.on("message")
def handle_message(message):
    user_id = session["user_id"]
    if message != "User connected!":
        send(message, broadcast=True)

        db.execute(
            "INSERT INTO messages (user_id, message,time) VALUES (?,?,?)",
            user_id,
            message,
            datetime.now(),
        )


global_starting_date = 8
global_ending_date = global_starting_date
global_dates = []
months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]
days_in_month = {
    "Jan": 31,
    "Feb": 29,
    "Mar": 31,
    "Apr": 30,
    "May": 31,
    "Jun": 30,
    "Jul": 31,
    "Aug": 31,
    "Sep": 30,
    "Oct": 31,
    "Nov": 30,
    "Dec": 31,
}
current_month = months[0]
month_over = False


from flask import render_template

@app.route("/week", methods=["GET", "POST"])
@login_required
def week():
    names = datadb.execute("SELECT name FROM people")
    global_ending_date = global_starting_date + 7
    global_dates = [str(i) for i in range(global_starting_date, global_ending_date)]
    month = current_month

    # Fetch attendance information for each person within the date range
    attendance_data = {}
    for name in names:
        attendance_data[name['name']] = []
        for date in global_dates:
            present = datadb.execute("""
                SELECT present FROM attendance
                WHERE people_id = (SELECT id FROM people WHERE name = ?)
                AND month = ?
                AND day = ?
            """, name['name'], current_month, date)
            #! remember in here when sendind the data, "True" means they were absent on that day, and "False" is they were present
            attendance_data[name['name']].append(bool(present) and present[0]['present'] == 'False')

    if request.method == "GET":
        #print(attendance_data)
        return render_template(
            "week.html",
            names=names,
            dates=global_dates,
            month=month,
            length=global_ending_date - global_starting_date,
            attendance_data=attendance_data
        )




@app.route("/next_week", methods=["GET"])
@login_required
def next_week():

    print("Next week requested")
    global global_starting_date, current_month, month_over, months

    if (month_over):
        print("Month is over")
        month_over = False
        current_index = months.index(current_month)
        current_month = months[(current_index + 1) % len(months)]
        global_starting_date = -6

    if (global_starting_date + 14 > days_in_month[current_month]):
        global_starting_date = days_in_month[current_month] - 6
        month_over = True

    else:
        global_starting_date = global_starting_date + 7

    return redirect("/week")


@app.route("/previous_week", methods=["GET"])
@login_required
def previous_week():
    global global_starting_date, current_month, month_over, months

    print("Previous week requested")

    if (global_starting_date - 7 < 1):
        current_index = months.index(current_month)
        current_month = months[current_index - 1]
        global_starting_date = days_in_month[current_month] - 6
        month_over = False
    else:
        global_starting_date = global_starting_date - 7

    return redirect("/week")


@app.route("/process_date", methods=["POST"])
@login_required
@admin_required
def process_date():
    data = request.get_json()

    print("Received data:", data)  # uncomment it to use it filter the data, and store it if its
    #Received data: {'name': 'Baivab Dutta', 'day': 'Monday', 'date': '36', 'month': 'Jan', 'checked': False}

    # In my database, day = date. Mispelled.
    sql_command = '''
        INSERT OR REPLACE INTO attendance(people_id, present, month, day)
        VALUES(
            (SELECT people.id FROM people WHERE people.name='{name}'),
            '{checked}',
            '{month}',
            '{date}'
        );
    '''.format(name=data['name'], month=data['month'], date=data['date'], checked=data['checked'])

    datadb.execute(sql_command,)
    print("Database Updated")

    response = {"message": "Data received successfully"}
    return jsonify(response)


if __name__ == "__main__":

    socketio.run(app, host="0.0.0.0")
