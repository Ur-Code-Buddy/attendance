from flask import redirect, render_template, session, jsonify
from functools import wraps
from cs50 import SQL
import secrets





# Rest of the code remains unchanged
def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        # Check if the current user is an admin
        if not is_admin():
            # If not, then do this

            print(f"Permission Denied, User: {session.get('user_id')} tried to access it")
            response = {"message": "Not Accepted,not an ADMIN"}
            return jsonify(response)


        #if admin, proceed
        return func(*args, **kwargs)

    return decorated_view


def is_admin():
    #checking the id from the idsession flask
    user_id = session.get("user_id")

    #checking if the "is_admin" for the user
    user = SQL("sqlite:///users.db").execute("SELECT is_admin FROM users WHERE id = ?", user_id)

    # if user exists and is admin
    return user and user[0]["is_admin"] == 'TRUE'
