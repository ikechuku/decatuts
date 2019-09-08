import os
import datetime

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)


# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///decatuts.db")


@app.route("/")
def index():
    """Render Index Page"""
    return render_template("index.html")


@app.route("/students", methods=["GET", "POST"])
@login_required
def students():
    # User reached route via GET
    if request.method == "GET":
        user=session['user_id']
        row = db.execute("SELECT * FROM schedule WHERE user_id = :user", user=user)

        return render_template("students.html", subjects = row)

    # User reached route via POST (as by submitting a form via POST)
    elif request.method == "POST":
        subject = request.form.get("subject")
        tutor_gender = request.form.get("tutor_gender")
        address = request.form.get("address")

        print(subject, tutor_gender, address)
        row = db.execute("INSERT INTO students (user_id, subject, tutor_gender, address) VALUES (:user_id, :subject, :tutor_gender, :address)", user_id=session['user_id'], subject=subject,tutor_gender=tutor_gender,address=address)

        return redirect("/schedule")  



@app.route("/schedule", methods=["GET", "POST"])
@login_required
def schedule():
    # User reached route via GET
    if request.method == "GET":
        subjects = db.execute("SELECT DISTINCT subject FROM tutors")
        return render_template("schedule.html", subjects=subjects)

    # User reached route via POST (as by submitting a form via POST)
    elif request.method == "POST":       
       #get and space out the days of week
        ll = request.form.getlist("check-box")
        y = " "   #
        for i in ll:
            y+=i+" "
        days_of_week= " ".join(str(x) for x in ll)

        # start_date = request.form.get("start_date")
        duration = int(request.form.get("duration"))
        hours_per_day = int(request.form.get("hours_per_day"))
        gender = request.form.get("gender")
        subject = request.form.get("subject")
        total = 1500 * hours_per_day * duration

        print("total", total)
        print("days_of_week", days_of_week)
        # print("start_date" ,start_date)
        print("duration" ,duration)
        print("hours_per_day", hours_per_day)
        print("gender" ,gender)
        print("subject", subject)


        row = db.execute("INSERT INTO schedule ( user_id, days_of_week, duration, hours_per_day, total, tutor_gender, subject) VALUES ( :user_id, :days_of_week, :duration, :hours_per_day, :total, :gender, :subject)",user_id=session['user_id'], days_of_week=days_of_week,duration=duration, hours_per_day=hours_per_day, total=total, gender=gender, subject=subject)

        print(row)
        return redirect(url_for('confirmation', subject=request.form.get("subject")))
        # return render_template("/confirmation", subject=request.form.get("subject"))  


@app.route("/confirmation", methods=["GET", "POST"])
@login_required
def confirmation():
    # User reached route via GET
    if request.method == "GET":
        rows = db.execute("SELECT * FROM tutors WHERE subject = :subject", subject=request.args.get('subject', None))
        summary = db.execute("SELECT days_of_week, hours_per_day, total, subject FROM (SELECT * FROM schedule WHERE user_id = :id) WHERE id = (SELECT MAX(id) FROM schedule)", id = session['user_id'])
        return render_template("confirmation.html", subjects=rows, summary=summary)

    # User reached route via POST (as by submitting a form via POST)
    elif request.method == "POST":
       
        tutor = request.form.get("tutor")

        row = db.execute("INSERT INTO schedule (tutor_name) VALUES ( :tutor) into schedule WHERE id = SELECT id FROM (SELECT * FROM schedule WHERE user_id = id) WHERE id = (SELECT MAX(id) FROM schedule)",id=session["user_id"] tutor=tutor)

        print(row)
        return redirect("/confirmation")  


@app.route("/check", methods=["GET"])
def check():
    
    """Return true if email available, else false, in JSON format"""

    email =  request.args.get("email")
    rows = db.execute("SELECT 1 FROM users WHERE email = :email", email=email)
    if len(rows) > 0:
        return jsonify(False)

    return jsonify(True)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure email was submitted
        if not request.form.get("email"):
            return apology("must provide email", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for email
        rows = db.execute("SELECT * FROM users WHERE email = :email",
                          email=request.form.get("email"))
        print(rows);

        # Ensure email exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("incorrect email and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]
        session['email'] = rows[0]['email']
        session['firstname'] = rows[0]['lastname']
        # Redirect user to home page
        return redirect("/students")

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
        # get all input values and store in python variables
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        phone = request.form.get("phone")
        reference = request.form.get("selected")
    
        if not email or email == "":
            return apology("must provide email", 400)

        rows = db.execute("SELECT * FROM users WHERE email = :email", email=email)
        print("^^^^^the rows",len(rows))
        
        if len(rows)>0:
            print("Passwords not provided")
            return apology("User already exists", 400)
         # Ensure password was submitted
        elif not password :
            print("Passwords not provided")

            return apology("must provide password", 400)

        if password!=confirmation:  
            print("Passwords do not match", 400)
            return apology("Passwords do not match", 400)
        
        hashed_pwd = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        # Insert into the  database
        db.execute("INSERT INTO users (firstname, lastname, email, phone, reference, hash)  VALUES (:firstname, :lastname, :email, :phone, :reference, :hash)", firstname=firstname, lastname=lastname,  email=email, phone=phone, reference=reference, hash=hashed_pwd)
        return redirect("/login")      

    else:
        return render_template("register.html")


@app.route("/tutors", methods=["GET", "POST"])
def tutor():
    """Register user"""
    if request.method == "POST":
        # get all input values and store in python variables
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        name = request.form.get("name")
        phone = request.form.get("phone")
        day = request.form.get("selected")

        print(email, password, confirmation, name, day)
        if not email or email == "":
            return apology("must provide email", 400)

        rows = db.execute("SELECT * FROM users WHERE email = :email", email=email)
        # print("^^^^^the rows",len(rows))
        
        if len(rows)>0:
            return apology("User already exists", 400)

         # Ensure password was submitted
        elif not password :
            return apology("must provide password", 400)

        if password!=confirmation:
            return apology("Passwords do not match", 400)
        
        hashed_pwd = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        # Insert into the  database
        db.execute("INSERT INTO tutors (name, email, phone, day, hash)  VALUES (:name, :email, :phone, :day, :hash)", name=name, email=email, phone=phone, day=day, hash=hashed_pwd)
        return redirect("/")      

    else:
        return render_template("tutors.html")



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
