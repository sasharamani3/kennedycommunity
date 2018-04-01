import random
import pymysql
import pymysql.cursors

from helpers import rundbquery
from application import getDBsize
from werkzeug.security import generate_password_hash

import smtplib
import ssl

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def sendWelcomeEmail(shortname, email, defaultpassword):
    # me == my email address
    # you == recipient's email address

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Kennedy Community | Welcome!"

    me = 'kennedycommunityapp@gmail.com'
    you = [email]

    msg['From'] = 'Kennedy Community Bot'
    msg['To'] = ", ".join(you)

    # Create the body of the message (a plain-text and an HTML version).
    text = "Hi " + shortname.title() +", welcome to Kenendy Community!"

    html = '<html><head></head>'
    html = html + '<body><h2>Welcome to Kennedy Community!</h2><p></p>'
    html = html + 'Hi ' + shortname.title() + ', welcome to Kennedy Community! Your account registration is complete.</p>'
    html = html + '<p></p>Your login is <b>' + email + '</b> and your password is <b>' + defaultpassword + '</b>. Please log in at <a href="www.kennedycommunity.com">kennedycommunity.com</a> and change your password.'
    html = html + '<p></p>The goal of this site is to promote our community by sharing personal contact information and social media information. The community is restricted to HKS students and graduates.'
    html = html + '<p></p>This site will be buggy at first, so please be patient as we work out any issues.'
    html = html + '<p></p>Please do not reply to me, as I am only a bot. My creator is Sasha Ramani, who is accessible at sasha.ramani@gmail.com. You can, of course, find his profile and contact information - as well as that of 300+ HKS grads - on <a href="www.kennedycommunity.com">Kennedy Community</a>.'
    html = html + '<p></p>Love, <br> Kennedy Community Bot<br>'
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


def assignDefaultPWtoEveryone():
    for currentuser in range(267, getDBsize()+1):
        pw = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
        hash = generate_password_hash(pw)

        print('User ' + str(currentuser) + ' gets default pw ' + str(pw))

        query = "Update innodb.alumni set defaultpass = %(pw)s, password = %(hash)s where id = %(id)s"
        params = {}
        params['pw'] = pw
        params['hash'] = hash
        params['id'] = currentuser
        rundbquery(query,params)



for currentuser in range(267,getDBsize()+1):
    query = "select id, shortname, email, defaultpass from innodb.alumni where id = %(id)s"
    params = {}
    params['id'] = currentuser
    db = rundbquery(query,params)

    for row in db:
        sendWelcomeEmail(row[1], row[2], row[3])
        print('Sent email to ID ' + str(row[0]) + ': ' + row[1] + ' at ' + row[2])

