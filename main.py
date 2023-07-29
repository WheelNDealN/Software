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
application.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///Products.db"
db = SQLAlchemy(application)
con = sql.connect('Userdata.db', check_same_thread=False, timeout=10)
cur = con.cursor()

class Items(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    Device = db.Column(db.Text)

    def __repr__(self):
        return '<device %r>' %self.Device

#This is my Ticket Database, with all the limitations and format options
class Userdb(db.Model):
    TID = db.Column(db.Integer, primary_key=True)
    Product = db.Column(db.String(64), index=True, default = "Product")
    Email_Address = db.Column(db.String(25), default = "Email Address")
    Date = db.Column(db.String, default = datetime.utcnow)

    def __repr__(self):
        return '<Product %r>' %self.Date

ChangeID=0

#Same as getting the Users length this one is for the tickets, allowing me to add one to the ID when a new one is created
def getlength():
    try:
        ordered = Userdb.query.order_by(Userdb.TID.desc())
        return ordered[0].TID
    except:
        return -1

#refactored function for getting the length of my Users, this is useful for the primary key going up when a user is added
def getuserlen():
  ordered = """SELECT ID FROM UserInfo ORDER BY ID DESC;"""
  cur.execute(ordered)
  Ans = cur.fetchall()
  Ans = Ans[0][0]
  return Ans

#This function was to clean up the code as the Statement variable is long
def create_user(addemail,addpassword,addadmin):
    IDtoAdd = int(getuserlen()+1)
    user=addemail
    passw=addpassword
    admin=addadmin
    cur.execute("INSERT INTO UserInfo (ID,Email,Password,Admin) VALUES (?,?,?,?)",(IDtoAdd,addemail,passw,admin) )
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
            email = request.form['Email']
            email = email.lower()
            password = request.form['Password']
            print(email)
            print(password)
            statement = f"SELECT Email from UserInfo WHERE Email='{email}'"
            statement = fetch(statement)
            print(statement)

            #this try method checks for matching usernames and signs them in if they are matching
            try:
                if statement[0] == email:
                    IDQuery = f"SELECT ID from UserInfo WHERE Email='{email}' AND Password = '{password}';"
                    IDQuery = fetch(IDQuery)
                    AdminQuery = f"SELECT Admin from UserInfo WHERE Email='{email}' AND Password = '{password}';"
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
        email = request.form['Email']
        email = email.lower()
        password = request.form['Password']
        if password == "pa$$word":
            admin = "1"

        else:
            admin = "0"

        usernameQuery = f"SELECT Email from UserInfo WHERE Email='{email}'"

        #if all requirements are met the "create_user" function is ran
        try:
            create_user(email,password,admin)
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

        elif request.form.get('SubmitButton2') == 'Go to Product manager':
            return redirect(url_for('Productpage'))                       

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
            
        elif request.form.get('SubmitButton2') == 'Go to admin inventory':
            return redirect(url_for('Productpage'))

    return render_template('admin.html')

 
#This page displays all of the tickets and gives options for modifying for regular users
@application.route('/Productpage', methods=['GET','POST'])
def Productpage():
    data = Userdb.query.order_by(Userdb.TID)
    try:
        if not g.user:
            return redirect(url_for('login'))
    except:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if request.form.get('SubmitButton') == 'Go to Profile':
            if session['admincheck'] == "1":
                return redirect(url_for("admin"))
            else:
                return redirect(url_for('profile'))

        elif request.form.get('SubmitButton') == 'Modify':
            ChangeID = request.form['id']
            setchangeid(ChangeID)

            return redirect(url_for("configureticket"))
            
        elif request.form.get('SubmitButton') == 'CreateTicket':
            return redirect(url_for("createticket"))
        
    return render_template("manage.html", data=data)

#this is the same as the ticket manager however with adding option of deleting the ticket from the ticket database
@application.route('/productmanager', methods=['GET','POST'])
def productmanager():
    data = Userdb.query.order_by(Userdb.TID)
    try:
        if not g.user:
            return redirect(url_for('login'))
    except:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if request.form.get('SubmitButton') == 'Go to Profile':
            if session['admincheck'] == "1":
                return redirect(url_for("admin"))
            else:
                return redirect(url_for('profile'))
            
        elif request.form.get('SubmitButton') == 'Modify':
            ChangeID = request.form['id']
            setchangeid(ChangeID)
            return redirect(url_for("configureticket"))

        elif request.form.get('SubmitButton') == 'CreateTicket':
            return redirect(url_for("createticket"))
        
    return render_template("manage.html", data=data)

@application.route('/createticket', methods=['GET','POST'])
def createticket():
    try:
        if not g.user:
            
            return redirect(url_for('login'))
            
    except:
        return redirect(url_for('login'))

    if request.form.get('SubmitButton') == 'Go to Ticket Manager':
            return redirect(url_for('productmanager')) 

    #based on what was inputed into the sections a new ticket is created
    if request.form.get('SubmitButton') == 'Submit':
        InputEmail = request.form['Email']
        InputProduct = request.form['Issue']
        length = int(getlength())+1
        newinfo = Userdb(TID= length,Product=InputProduct,Email_Address=InputEmail)
        db.session.add(newinfo)
        db.session.commit()
        time.sleep(1)

        if session['admincheck'] == "1":
            return redirect(url_for('adminticketmanager'))

        else:
            return redirect(url_for('productmanager'))
    data = Items.query.order_by(Items.ID)
    return render_template("Requestequipment.html", data=data)

if __name__ == '__main__':
    application.run(port=8069,host="0.0.0.0")
