import os
import secrets
import random
import datetime
import re

from cs50 import SQL
from flask import (
    Flask,
    redirect,
    render_template,
    jsonify,
    request,
    session,
    flash

)
from flask_session import Session
from flask_mail import Mail, Message

from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from flask_socketio import SocketIO, send
from helpers import apology, login_required, admin_required
from dotenv import find_dotenv, load_dotenv


dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

my_secret_email = os.getenv("my_secret_email")
my_secret_pass = os.getenv("my_secret_pass")


app = Flask(__name__)

current_username = ""
current_password = ""
current_email= ""
current_verification_code = {}

app.config['MAIL_SERVER'] = 'smtp.office365.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = my_secret_email
app.config['MAIL_PASSWORD'] = my_secret_pass
app.config['MAIL_DEFAULT_SENDER'] = my_secret_email

mail = Mail(app)

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

# In your Flask route
@app.route("/members", methods=["GET", "POST"])
@login_required
def members():
    if request.method == "POST":
        clicked_name = request.form.get("member_name")
        print(f"Clicked Name: {clicked_name}")

        # Get the number of days absent and the specific days with month
        absent_info = datadb.execute("""
            SELECT COUNT(*) as days_absent, GROUP_CONCAT(month || ' ' || day) as absent_days
            FROM attendance
            WHERE people_id = (SELECT id FROM people WHERE name = ?) AND present = 'False'
        """, clicked_name)[0]

        # Convert the comma-separated absent_days into a list of dictionaries
        # Each dictionary contains 'month' and 'day'
        absent_days = [
            {'month': day.split(' ')[0], 'day': day.split(' ')[1]}
            for day in absent_info['absent_days'].split(',')
        ] if absent_info['absent_days'] else []

        # Render the template with the detailed note
        return render_template("members_detail.html", name=clicked_name, days_absent=absent_info['days_absent'], absent_days=absent_days)

    # For the initial GET request, retrieve the list of members
    rows = datadb.execute("SELECT * FROM people")
    return render_template("members.html", rows=rows)


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        # Ensure old password, new password, and confirmation are submitted
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        # Query database for user's current hashed password
        user_id = session["user_id"]
        current_hashed_password = db.execute("SELECT hash FROM users WHERE id = ?", user_id)[0]["hash"]

        if not check_password_hash(current_hashed_password, old_password):
            return apology("Invalid old password", 403)

        if new_password != confirmation:
            return apology("New password and confirmation do not match", 403)

        new_hashed_password = generate_password_hash(new_password)
        db.execute("UPDATE users SET hash = ? WHERE id = ?", new_hashed_password, user_id)
        print("password changed for id:",user_id)

        # Redirect user to home page with a success message
        flash("Password changed successfully!", "success")
        return redirect("/")
    
    return render_template("change_password.html")




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



def send_registration_email(email, code):
    subject = "Congratulations on Registering with Student Attendance!"

    body = f"""
        <<p>Dear User,</p>
        <p>Thank you for choosing our Student Attendance System!</p>
        <p>We're delighted that you have registered with us. Your presence in our community is highly valued. Our system is designed to make attendance tracking efficient and user-friendly.</p>
        <p>If you have any questions or need assistance, please don't hesitate to reach out to us at <a href="mailto:05baivab@gmail.com">05baivab@gmail.com</a>. We're here to support you.</p>
        <p>Once again, thank you for registering with us. We look forward to providing you with a seamless attendance experience.</p>
        <p>Best regards,<br>Student Attendance Team</p>

    """

    message = Message(subject, recipients=[email], html=body)

    try:
        mail.send(message)
        print("Registration email sent successfully")
    except Exception as e:
        print(f"Error sending registration email: {e}")
        return apology(f"Error: {e}")



def send_verification_email(email, code):  #*Works well
    subject = "Email Verification Code"
    
    # HTML-formatted body with a larger and copyable verification code
    body = f"""
        <p>Dear User,</p>
        <p>Thank you for registering to our Attendance System! Your verification code is:</p>
        <p style="font-size: 18px; font-weight: bold; background-color: #f4f4f4; padding: 10px; border-radius: 5px; user-select: all;">{code}</p>
        <p>Please enter this code on the website to complete the registration process.</p>
        <p>Best regards,<br>Student Attendance</p>
    """

    message = Message(subject, recipients=[email], html=body)

    try:
        mail.send(message)
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")
        return apology(f"Error: {e}")

def verification_code():
    global current_verification_code
    current_verification_code = str(random.randint(100000, 999999))
    return 



@app.route("/verification", methods=["GET", "POST"])
def verification(): 
    #
    send_verification_email(current_email,current_verification_code)
    
    if request.method == "POST":
        code = request.form.get("verification_code")
        print("code recived is: ",code)
        print("code:",code, "  verification_code: ",current_verification_code)
        if str(code).strip() == str(current_verification_code).strip():
    
            print("All went good!")
            hash = generate_password_hash(current_password)

            try:
                new_user = db.execute(
                    "INSERT INTO users (username, hash, email) VALUES(?, ?, ?)", current_username, hash, current_email
                )
            except:
                return apology("Username Already Exists")
            session["user_id"] = new_user
            send_registration_email(current_email,current_verification_code)
            return redirect("/")
        
        return render_template("register.html")
    else: 
        return render_template("verification.html")


@app.route("/register", methods=["GET", "POST"]) 
def register():
    """Register user"""
    global current_username
    global current_password
    global current_email

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        email = request.form.get("email")

        # Check if the email is in a valid format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return apology("Invalid email format. Please provide a valid email address.")

        # Check if the email already exists in the database
        existing_user = db.execute("SELECT * FROM users WHERE email = ?", email)
        if existing_user:
            return apology("Email already exists. Please use a different email.")

        # Checking if the values are acceptable
        if not username:
            return apology("Username Error")
        if not password:
            return apology("Password Error")
        if not confirmation:
            return apology("Confirmation Error")

        if password != confirmation:
            return apology("Password and Confirmation DO NOT MATCH")
        
        current_username = username
        current_password = password
        current_email = email
        verification_code()
        return redirect("/verification")

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
    socketio.run(app, host="0.0.0.0",debug=True)
