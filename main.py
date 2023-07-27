#All my imports
from distutils.log import error
from flask import Flask, render_template, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import update
import time
import sqlite3 as sql
from flask import (Flask, g, redirect, render_template, request, session, url_for)
import re

#This is set up for databases and for the flask server
application = Flask(__name__, template_folder='template')
application.secret_key = 'supersecret'
application.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///tickets.db"
db = SQLAlchemy(application)
con = sql.connect('UserInfo.db', check_same_thread=False, timeout=10)
cur = con.cursor()

ChangeID=0

#refactored function for getting the length of my Users, this is useful for the primary key going up when a user is added
def getuserlen():
  ordered = """SELECT ID FROM UserInfo ORDER BY ID DESC;"""
  cur.execute(ordered)
  Ans = cur.fetchall()
  Ans = Ans[0][0]
  return Ans

#This function was to clean up the code as the Statement variable is long
def create_user(addusername,addpassword,addadmin):
    IDtoAdd = int(getuserlen()+1)
    user=addusername
    passw=addpassword
    admin=addadmin
    cur.execute("INSERT INTO UserInfo (ID,Username,Password,Admin) VALUES (?,?,?,?)",(IDtoAdd,user,passw,admin) )
    con.commit()

#These two functions where used when i had to select the index of the ticket database for modifing
def setchangeid(ID):
    global ChangeID
    ChangeID = ID

def getchangeid():
    return ChangeID

#This is me refactoring SQLite as this sequence of code had to be ran many times and this made my code look nicer and stopped repetition
def fetch(Query):
    try:
        statement = Query
        cur.execute(statement)
        Ans = cur.fetchall()
        Ans = Ans[0]
        return Ans
    except:
        return False

#This is ran before every change of url, this allows me to check if the user is signed in, if they are not they are redirected to the login screen.
@application.before_request
def before_request():
    try:
        if "user_id" in session:
            ID = f"SELECT ID from UserInfo WHERE ID='{session['user_id']}'"
            ID = cur.execute(ID)
            Ans = cur.fetchall()
            user = Ans[0][0]
            g.user = user
    except:
        return render_template('index.html')

@application.route('/login', methods=['GET', 'POST'])
def login():
    #session.pop, clears the signed in user, making it impossible to go to other pages once redirected to the login page
    session.pop('user_id', None)

    #Whenver a button is pressed the statement "if request.method == 'POST':" is ran
    if request.method == 'POST':
        if request.form.get('SubmitButton') == 'CreateUser':
            print("clicked")
            return redirect(url_for('createuser'))
            
        if request.form.get('SubmitButton') == 'Submit':
            username = request.form['Username']
            password = request.form['Password']
            statement = f"SELECT Username from UserInfo WHERE Username='{username}' AND Password = '{password}';"
            statement = fetch(statement)

            #this try method checks for matching usernames and signs them in if they are matching
            try:
                if statement[0] == username:
                    IDQuery = f"SELECT ID from UserInfo WHERE Username='{username}' AND Password = '{password}';"
                    IDQuery = fetch(IDQuery)
                    AdminQuery = f"SELECT Admin from UserInfo WHERE Username='{username}' AND Password = '{password}';"
                    AdminQuery = fetch(AdminQuery)
                    session['user_id'] = IDQuery[0]  
                    session['admincheck'] = AdminQuery[0]

                    #checking for admin and directing to the correct url
                    if session['admincheck'] == "1":
                        return redirect(url_for("admin"))

                    else:
                        return redirect(url_for('profile'))
            
            #when none are matching this "exepct" makes an error show
            except:
                print(fetch(statement))
                return render_template('index.html', error=True)

    return render_template('index.html')


#Creating a new User
@application.route('/createuser', methods=['GET', 'POST'])
def createuser():
    error = False
    session.clear()
    if request.method == 'POST':
        session.pop('user_id', None)
        username = request.form['Username']
        password = request.form['Password']

        #this is checking if the username has characters upper or lower case A-Z and numbers 0-9, if any other are detected and error is given
        if (bool(re.match('^[a-zA-Z0-9]*$',username))==False):
            return render_template('createuser.html', Format=True)

        #to create an admin a check for the passowrd being "pa$$word", ideally kept a secret but for ease of use ive displayed the rule on the page
        else:
            if password == "pa$$word":
                admin = "1"

            else:
                admin = "0"

            usernameQuery = f"SELECT Username from UserInfo WHERE Username='{username}'"

            #if all requirements are met the "create_user" function is ran
            try:
                create_user(username,password,admin)
                #whenever i add delay to the webpage i am showing the user a message, or creating a fake a buffer to make it feel as though something is happening
                time.sleep(1)
                return redirect(url_for('login'))
            
            #if usernames match desplay error
            except:
                fetch(usernameQuery)
                time.sleep(1)
                return render_template('createuser.html', error=True)
        
    return render_template('createuser.html')

#This page is very simple but i wanted a page for logging out and a choice to going into the main page
@application.route('/profile', methods=['GET','POST'])
def profile():

    #this checks for a signed in user otherwise you are redirected to the login page
    try:
        if not g.user:
            return redirect(url_for('login'))
    except:
        return redirect(url_for('login'))

    if request.method == 'POST':

        if request.form.get('SubmitButton1') == 'LogOut':
            session.clear()
            return redirect(url_for('login'))

        elif request.form.get('SubmitButton2') == 'Go to ticket manager':
            return redirect(url_for('ticketmanager'))                       

    return render_template('profile.html')

#this is similar to the regular user however it is for an admin
@application.route('/admin', methods=['GET','POST'])
def admin():                                                              

    try:
        if not g.user:
            return redirect(url_for('login'))
    except:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if request.form.get('LogOut') == 'LogOut':
            session.clear()
            return redirect(url_for('login'))
            
        elif request.form.get('SubmitButton2') == 'Go to admin ticket manager':
            return redirect(url_for('adminticketmanager'))

    return render_template('admin.html')

if __name__ == '__main__':
    application.run(port=8069,host="0.0.0.0")
