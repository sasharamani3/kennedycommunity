## Kennedy Community
## Created by Sasha Ramani, MPP 2018

##To dos:

#-host
#-email everyone



from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from flask_session import Session
from functools import wraps

import sqlite3

from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
import time

from helpers import login_required, phoneProvided, linkedinProvided, facebookProvided, rundbquery

import smtplib
import ssl

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import datetime
import pytz

import random

# Configure application
application = app = Flask(__name__)
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080,debug=True)


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response



@app.route("/")
def index():
    """Welcome Page"""
    return render_template("index.html")



@app.route("/about", methods=["GET", "POST"])
def about():
    """About Page"""
    return render_template("about.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # See if the user exists at all
        query = "Select Count(*) from innodb.alumni where email = %(email)s"
        params = {}
        params['email'] = request.form.get("email").lower()
        dbreturn = rundbquery(query, params)

        for row in dbreturn:
            if (row[0] == 0):
                session.clear()
                print("User does not exist")
                return render_template("badlogin.html")



        # Nowe can assume that the user exists
        query = "Select id, email, password FROM innodb.alumni WHERE email = %(email)s"
        params = {}
        params['email'] = request.form.get("email").lower()
        dbreturn = rundbquery(query, params)

        for row in dbreturn:
            print(row)
            if check_password_hash(row[2], request.form.get("password")):
                session["user_id"] = row[0]
                return render_template("goodlogin.html")

            else:
                session.clear()
                return render_template("badlogin.html")


    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")



@app.route("/logout", methods=["GET", "POST"])
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()
    return render_template("logout.html")



@app.route("/changepw", methods=["GET", "POST"])
def changepw():
    """Change Password"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Verify correct original credentials
        query = "Select idusers, email, password FROM innodb.alumni WHERE email = %(email)s"
        params = {}
        params['email'] = request.form.get("email").lower()
        dbreturn = rundbquery(query, params)

        for row in dbreturn:
            if not check_password_hash(row[2], request.form.get("password")):
                return render_template("badlogin.html")
            else:

                # Update user's password
                query = "UPDATE innodb.alumni SET password = %(password)s WHERE email = %(email)s"
                params = {}
                params['password'] = generate_password_hash(request.form.get("password"))
                params['email'] = request.form.get("email").lower()
                dbreturn2 = rundbquery(query, params)


                # Now log the user in
                query = "Select idusers FROM users WHERE email = %(email)s"
                params['email'] = request.form.get("email").lower()
                dbreturn3 = rundbquery(query, params)

                for row3 in dbreturn3:
                    session["user_id"] = row[0]

                # Redirect user to home page
                return redirect("/")

    else:   # User reached route via GET (as by clicking a link or via redirect)
        return render_template("changepw.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register a new account"""

    if request.method == "GET":
       return render_template("register.html")


    if request.method == "POST":
        print('Submitted form')

        # STEP 1: ADD TO THE DATABASE
        query = 'INSERT INTO innodb.alumni (fullname, shortname, program, gradyear, jointordualdegree, email, phone, phoneprovided, linkedin, linkedinprovided, facebook, facebookprovided, othersocial, ama, active, password)'
        query = query + 'VALUES (%(fullname)s, %(shortname)s, %(program)s, %(gradyear)s, %(jointordualdegree)s, %(email)s, %(phone)s, %(phoneprovided)s, %(linkedin)s, %(linkedinprovided)s, %(facebook)s, %(facebookprovided)s, %(othersocial)s, %(ama)s, %(active)s, %(password)s)'

        defaultpass = ''.join(random.choice('0123456789ABCDEF') for i in range(8))

        params = {}
        params['fullname'] = request.form.get('fullname')
        params['shortname'] = request.form.get('shortname')
        params['program'] = request.form.get('program')
        params['gradyear'] = request.form.get('gradyear')
        params['jointordualdegree'] = request.form.get('jointordualdegree')
        params['email'] = request.form.get('email')
        params['phone'] = request.form.get('phone')
        params['phoneprovided'] = 1 - (request.form.get('phone') == "")
        params['linkedin'] = request.form.get('linkedin')
        params['linkedinprovided'] = 1 - (request.form.get('linkedin') == "")
        params['facebook'] = request.form.get('facebook')
        params['facebookprovided'] = 1 - (request.form.get('facebook') == "")
        params['othersocial'] = request.form.get('othersocial')
        params['ama'] = request.form.get('ama')
        params['active'] = 1
        params['password'] = generate_password_hash(defaultpass)

        dbreturn = rundbquery(query, params)

        sendWelcomeEmail(params['shortname'], params['email'], request.form.get('harvardemail'), params['password'], params)

        return redirect(url_for('registered'))



def sendWelcomeEmail(shortname, email, harvardemail, defaultpassword, params):
    # me == my email address
    # you == recipient's email address

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Kennedy Community | Welcome!"

    me = 'kennedycommunityapp@gmail.com'
    you = [harvardemail]

    msg['From'] = 'Kennedy Community Bot'
    msg['To'] = ", ".join(you)

    # Create the body of the message (a plain-text and an HTML version).
    text = "Hi " + shortname.title() +", welcome to Kenendy Community!"

    html = '<html><head></head>'
    html = html + '<body><h2>Welcome!</h2><p></p>'
    html = html + 'Hi ' + shortname.title() + ', welcome to Kennedy Community! Your account registration is complete.</p>'
    html = html + '<p></p>Your account email address is <b>' + email + '</b> and your password is <b>' + defaultpassword + '</b>. Please log in and change your password.'
    html = html + '<p></p>This is the only time that your Harvard email will be used by the site: we only do this to verify that you are, in fact, a Harvard student or graduate.'
    html = html + '<p></p>Please do not reply to me, as I am only a bot. My creator is Sasha Ramani, who is accessible at sasha.ramani@gmail.com. You can, of course, find his profile and contact information - as well as that of 300+ HKS grads - on Kennedy Community.'
    html = html + '<p></p>Love, <br> Kennedy Community Bot<br>'
    html = html + '<p></p>================================<p>PS. The  account information that I have for you is:</p>'
    html = html + getEmailBodyOfProfile(params)
    html = html + '</body></html>'

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # Send the message via local SMTP server.
    s = smtplib.SMTP('smtp.gmail.com:587')
    s.ehlo()
    s.starttls()

    username = 'kennedycommunityapp@gmail.com'
    password = 'Freedom55!?'
    s.login(username,password)

    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.
    s.sendmail(me, you, msg.as_string())
    s.quit()



@app.route("/registered", methods=["GET", "POST"])
def registered():
    if request.method == "GET":
        return render_template("registered.html")


def getEmailBodyOfProfile(params):
    html = ''
    html = html + '<p><b>Full Name: </b> ' + params['fullname'] + '</p>'
    html = html + '<p><b>Given Name: </b> ' + params['shortname'] + '</p>'
    html = html + '<p><b>HKS Program: </b> ' + params['program'] + '</p>'
    html = html + '<p><b>HKS Grad Year: </b> ' + params['gradyear'] + '</p>'
    html = html + '<p><b>Joint/Dual Degree: </b> ' + params['jointordualdegree'] + '</p>'
    html = html + '<p><b>Personal email: </b> ' + params['email'] + '</p>'
    html = html + '<p><b>Phone number: </b> ' + params['phone'] + '</p>'
    html = html + '<p><b>LinkedIn: </b> ' + params['linkedin'] + '</p>'
    html = html + '<p><b>Facebook: </b> ' + params['facebook'] + '</p>'
    html = html + '<p><b>Other Social Media: </b> ' + params['othersocial'] + '</p>'
    html = html + '<p><b>Ask me about: </b> ' + params['ama'] + '</p>'
    return (html)


@app.route("/editprofile", methods=["GET", "POST"])
@login_required
def editProfile():

    if request.method == "GET":

        query = "SELECT fullname, shortname, program, gradyear, jointordualdegree, email, phone, linkedin, facebook, othersocial, ama FROM innodb.alumni WHERE id = %(id)s"
        params = {}
        params['id'] = session.get("user_id")

        db = rundbquery(query, params)
        for row in db:
            fullname = row[0]
            shortname = row[1]
            program = row[2]
            gradyear = row[3]
            jointordualdegree = row[4]
            email = row[5]
            phone = row[6]
            linkedin = row[7]
            facebook = row[8]
            othersocial = row[9]
            ama = row[10]

        return render_template("editprofile.html", fullname=fullname, shortname=shortname, program=program, gradyear=gradyear, jointordualdegree=jointordualdegree, email=email, phone=phone, linkedin=linkedin, facebook=facebook, othersocial=othersocial, ama=ama)


    if request.method == "POST":
        print('Edited Profile')

        # STEP 1: ADD TO THE DATABASE
        query = 'UPDATE innodb.alumni SET '
        query = query + 'fullname = %(fullname)s, shortname = %(shortname)s, program = %(program)s, gradyear = %(gradyear)s, jointordualdegree = %(jointordualdegree)s, '
        query = query + 'email = %(email)s, phone = %(phone)s, phoneprovided = %(phoneprovided)s, linkedin = %(linkedin)s, linkedinprovided = %(linkedinprovided)s, facebook = %(facebook)s, facebookprovided = %(facebookprovided)s, othersocial = %(othersocial)s, ama = %(ama)s '
        query = query + 'WHERE id = %(id)s'

        params = {}
        params['fullname'] = request.form.get('fullname')
        params['shortname'] = request.form.get('shortname')
        params['program'] = request.form.get('program')
        params['gradyear'] = request.form.get('gradyear')
        params['jointordualdegree'] = request.form.get('jointordualdegree')
        params['email'] = request.form.get('email')
        params['phone'] = request.form.get('phone')
        params['phoneprovided'] = 1 - (request.form.get('phone') == "")
        params['linkedin'] = request.form.get('linkedin')
        params['linkedinprovided'] = 1 - (request.form.get('linkedin') == "")
        params['facebook'] = request.form.get('facebook')
        params['facebookprovided'] = 1 - (request.form.get('facebook') == "")
        params['othersocial'] = request.form.get('othersocial')
        params['ama'] = request.form.get('ama')
        params['id'] = session.get("user_id")

        dbreturn = rundbquery(query, params)

        sendUpdatedProfile(params['shortname'], params['email'], params)

        return redirect(url_for('editedprofile'))


def sendUpdatedProfile(shortname, email, params):
    # me == my email address
    # you == recipient's email address

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Kennedy Community | Profile Update"

    me = 'kennedycommunityapp@gmail.com'
    you = [email]

    msg['From'] = 'Kennedy Community Bot'
    msg['To'] = ", ".join(you)

    # Create the body of the message (a plain-text and an HTML version).
    text = "Hi " + shortname.title() +", we've received your updated profile"

    html = '<html><head></head>'
    html = html + '<body><h2>Confirmation: Updated Profile</h2><p></p>'
    html = html + 'Hi ' + shortname.title() + ', your profile has been successfully updated.'
    html = html + '<p></p>Please direct any replies to Sasha Ramani at sasha.ramani@gmail.com'
    html = html + '<p></p>Love, <br> Kennedy Community Bot<br>'
    html = html + '<p></p>================================<p>PS. The  account information that I have for you is:</p>'
    html = html + getEmailBodyOfProfile(params)
    html = html + '</body></html>'

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # Send the message via local SMTP server.
    s = smtplib.SMTP('smtp.gmail.com:587')
    s.ehlo()
    s.starttls()

    username = 'kennedycommunityapp@gmail.com'
    password = 'Freedom55!?'
    s.login(username,password)

    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.
    s.sendmail(me, you, msg.as_string())
    s.quit()



@app.route("/editedprofile", methods=["GET", "POST"])
def editedprofile():
    if request.method == "GET":
        return render_template("editedprofile.html")


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    if request.method == "GET":
        return render_template("search.html")

    if request.method == "POST":
        q = request.form.get('q')
        print('query: '+ q)
        return viewsearch(q, 1)


@app.route("/scrollsearch")
@login_required
def scrollsearch():
    if request.method == "GET":
        q = request.args.get('q')
        startat = request.args.get('startat')
        return viewsearch(q, startat)


@app.route("/viewsearch")
@login_required
def viewsearch(q, startat):
    query = "SELECT Count(*) FROM innodb.alumni WHERE active = 1 AND (fullname LIKE %(q)s OR program LIKE %(q)s OR jointordualdegree LIKE %(q)s OR email LIKE %(q)s OR phone LIKE %(q)s OR othersocial LIKE %(q)s OR ama LIKE %(q)s) LIMIT 20"
    params = {}
    params['q'] = '%' + q + '%'
    params['startat'] = startat
    if params['startat'] == 'All' or params['startat'] is None:
        params['startat'] = 0
    else:
        params['startat'] = max(1,int(params['startat']))-1

    for row in rundbquery(query, params):
        counttotal = row[0]

    query = "SELECT id, fullname, program, gradyear, jointordualdegree, email, phone, linkedin, facebook FROM innodb.alumni WHERE active = 1 AND (fullname LIKE %(q)s OR program LIKE %(q)s OR jointordualdegree LIKE %(q)s OR email LIKE %(q)s OR phone LIKE %(q)s OR othersocial LIKE %(q)s OR ama LIKE %(q)s) LIMIT 20 OFFSET %(startat)s"
    db = rundbquery(query, params)

    phone_status = phoneProvided()
    linkedin_status = linkedinProvided()
    facebook_status = facebookProvided()

    allstudents = []
    for row in db:
        currentstudent = {}
        currentstudent['id'] = row[0]
        currentstudent['fullname'] = row[1]
        currentstudent['program'] = row[2]
        currentstudent['gradyear'] = row[3]
        currentstudent['jointordualdegree'] = row[4]
        currentstudent['email'] = row[5]

        if phone_status == 1:
            currentstudent['phone'] = row[6]
        else:
            currentstudent['phone'] = 'Hidden'

        if linkedin_status == 1:
            currentstudent['linkedin'] = row[7]
        else:
            currentstudent['linkedin'] = 'Hidden'

        if facebook_status == 1:
            currentstudent['facebook'] = row[8]
        else:
            currentstudent['facebook'] = 'Hidden'

        allstudents.append(currentstudent)


    endat = min(counttotal, int(params['startat']) + 20)
    desc = '#' + str(params['startat']+1) + ' to ' + str(endat) + ' of ' + str(counttotal)
    desc = desc + " for query '" + q + "'"

    return render_template("viewsearch.html", students=allstudents, desc=desc, start=params['startat'], end=endat, q=q)



@app.route("/viewlist")
@login_required
def viewlist():
    query = "SELECT id, fullname, program, gradyear, jointordualdegree, email, phone, linkedin, facebook FROM innodb.alumni WHERE active = 1 ORDER BY id LIMIT 20 OFFSET %(startat)s"
    params = {}
    params['startat'] = request.args.get("startat")

    if params['startat'] == 'All' or params['startat'] is None:
        params['startat'] = 0
    else:
        params['startat'] = max(1,int(params['startat']))-1

    db = rundbquery(query, params)

    phone_status = phoneProvided()
    linkedin_status = linkedinProvided()
    facebook_status = facebookProvided()


    allstudents = []
    for row in db:
        currentstudent = {}
        currentstudent['id'] = row[0]
        currentstudent['fullname'] = row[1]
        currentstudent['program'] = row[2]
        currentstudent['gradyear'] = row[3]
        currentstudent['jointordualdegree'] = row[4]
        currentstudent['email'] = row[5]

        if phone_status == 1:
            currentstudent['phone'] = row[6]
        else:
            currentstudent['phone'] = 'Hidden'

        if linkedin_status == 1:
            currentstudent['linkedin'] = row[7]
        else:
            currentstudent['linkedin'] = 'Hidden'

        if facebook_status == 1:
            currentstudent['facebook'] = row[8]
        else:
            currentstudent['facebook'] = 'Hidden'

        allstudents.append(currentstudent)

    endat = min(getDBsize(), int(params['startat']) + 20)
    desc = '#' + str(params['startat']+1) + ' to ' + str(endat) + ' of ' + str(getDBsize())

    return render_template("viewlist.html", students=allstudents, desc=desc, start=params['startat'], end=endat)



@app.route("/getEmail")
@login_required
def getEmail():
    """Look up data for id"""
    if not request.args.get("id"):
        raise RuntimeError("id not found")

    query = "SELECT email FROM innodb.alumni WHERE id=%(id)s"
    params = {}
    params['id'] = request.args.get("id")
    db = rundbquery(query, params)

    for row in db:
        print(row[0])
        return jsonify(row[0])



@app.route("/getPhone")
@login_required
def getPhone():
    print ('Started with id: ' + request.args.get("id"))
    """Look up data for id"""
    if not request.args.get("id"):
        raise RuntimeError("id not found")

    if phoneProvided() == 0:
        print('Did not provide')
        return jsonify(0)

    query = "SELECT phone FROM innodb.alumni WHERE id=%(id)s AND active=1"
    params = {}
    params['id'] = request.args.get("id")
    db = rundbquery(query, params)

    for row in db:
        return jsonify(row[0])


@app.route("/getLinkedin")
@login_required
def getLinkedin():
    print ('Started with id: ' + request.args.get("id"))
    """Look up data for id"""
    if not request.args.get("id"):
        raise RuntimeError("id not found")

    if linkedinProvided() == 0:
        print('Did not provide')
        return jsonify(0)

    query = "SELECT linkedin FROM innodb.alumni WHERE id=%(id)s AND active=1"
    params = {}
    params['id'] = request.args.get("id")
    db = rundbquery(query, params)

    for row in db:
        return jsonify(row[0])



@app.route("/getFacebook")
@login_required
def getFacebook():
    print ('Started with id: ' + request.args.get("id"))
    """Look up data for id"""
    if not request.args.get("id"):
        raise RuntimeError("id not found")

    if facebookProvided() == 0:
        print('Did not provide')
        return jsonify(0)

    query = "SELECT facebook FROM innodb.alumni WHERE id=%(id)s AND active=1"
    params = {}
    params['id'] = request.args.get("id")
    db = rundbquery(query, params)

    for row in db:
        return jsonify(row[0])



@app.route("/viewprofile", methods=["GET"])
@login_required
def viewProfile():

    if request.method == "GET":

        query = "SELECT fullname, shortname, program, gradyear, jointordualdegree, email, phone, linkedin, facebook, othersocial, ama FROM innodb.alumni WHERE id = %(id)s"
        params = {}
        params['id'] = request.args.get('id')

        phone_status = phoneProvided()
        linkedin_status = linkedinProvided()
        facebook_status = facebookProvided()

        db = rundbquery(query, params)
        for row in db:
            fullname = row[0]
            shortname = row[1]
            program = row[2]
            gradyear = row[3]
            jointordualdegree = row[4]
            email = row[5]

            if phone_status == 1:
                phone = row[6]
            else:
                phone = 'Hidden'

            if linkedin_status == 1:
                linkedin = row[7]
            else:
                linkedin = 'Hidden'

            if facebook_status == 1:
                facebook = row[8]
            else:
                facebook = 'Hidden'

            othersocial = row[9]
            ama = row[10]

    return render_template("viewprofile.html", fullname=fullname, shortname=shortname, program=program, gradyear=gradyear, jointordualdegree=jointordualdegree, email=email, phone=phone, linkedin=linkedin, facebook=facebook, othersocial=othersocial, ama=ama)



def getDBsize():
    query = "Select Count(*) from innodb.alumni where active=1"
    params = ""

    for row in rundbquery(query, params):
        return row[0]