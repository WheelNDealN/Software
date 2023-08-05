import time         #All my imports for the project.
import sqlite3 as sql
import pyotp
import logging
import hashlib 
from flask import (Flask, g, redirect, render_template, request, session, url_for, render_template)
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import update

application = Flask(__name__, template_folder='template')           #This is my sql setup giving access to the flask application.
application.secret_key = 'supersecret'
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
application.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///Products.db"
db = SQLAlchemy(application)
con = sql.connect('Userdata.db', check_same_thread=False, timeout=10)
cur = con.cursor()

logging.basicConfig(filename = 'app.txt',level=logging.DEBUG,filemode='w')          #this is where i set up the logging for my code.
logger = logging.getLogger(__name__)
handler = logging.FileHandler('app.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class Items(db.Model):          #here i have the items database for new product requests.
    ID = db.Column(db.Integer, primary_key=True)
    Device = db.Column(db.Text)
    def __repr__(self):
        return '<device %r>' %self.Device

class Userdb(db.Model):         #This is my Database for each new request where TID is the primary key.
    TID = db.Column(db.Integer, primary_key=True)
    Product = db.Column(db.String(64), index=True, default = "Product")
    Email_Address = db.Column(db.String(25), default = "Email Address")
    Date = db.Column(db.String, default = datetime.utcnow)
    def __repr__(self):
        return '<Product %r>' %self.Date

ChangeID=0      #these two variables i needed to be set to a default value
GobEmail = ""

#all next few functions are where i refactored my code.
def getlength():        #This function was to reduce repeating code when trying to find the next available id number to assign.
    try:
        ordered = Userdb.query.order_by(Userdb.TID.desc())
        return ordered[0].TID
    except:
        return -1

def getlengthItems():       #Same as getting the getlength however for the new products that can be created.
    try:
        ordered = Items.query.order_by(Items.ID.desc())
        return ordered[0].ID
    except:
        return -1

def getuserlen():       #refactored function for getting the length of my Users, this is useful for the primary key going up when a user is added.
  ordered = """SELECT ID FROM UserInfo ORDER BY ID DESC;"""
  cur.execute(ordered)
  Ans = cur.fetchall()
  Ans = Ans[0][0]
  return Ans

def getauth():      #this is for the 2factor authentification, getting the token used on the app to check for the correct code
    try:
        authuser=f"SELECT Authkey from UserInfo WHERE ID='{session['user_id']}'"
        statement = fetch(authuser)
        statement = ''.join(statement)
        return statement
    except:
        return 0

def create_user(addemail,addpassword,addadmin):     #This function was to clean up the code as the Statement variable is long
    IDtoAdd = int(getuserlen()+1)
    user=addemail
    passw=addpassword
    admin=addadmin
    cur.execute("INSERT INTO UserInfo (ID,Email,Admin,Password) VALUES (?,?,?,?)",(IDtoAdd,addemail,admin,passw))
    con.commit()

def Add_2fa(secret,id):         #This function addd the secret auth key google to the user data base 
    Secret = secret
    ID=id
    sql = "UPDATE UserInfo SET AuthKey = '%s' WHERE ID = '%s'"% (Secret,ID)
    cur.execute(sql)
    con.commit()

def setchangeid(ID):            #These two functions where used when i had to select the index of the Product database for modifing
    global ChangeID
    ChangeID = ID

def getchangeid():              #mentioned above ^^^^
    return ChangeID

def hashpass(passw):                    #This function hashes the password which i used a few times for refactoring code
    salt = ("diD_h12$j")
    passw += salt
    hashed = hashlib.md5(passw.encode())  
    hashed = hashed.hexdigest()
    return hashed

def fetch(Query):               #This is me refactoring SQLite as this sequence of code had to be ran many times and this made my code look nicer and stopped repetition
    try:
        statement = Query
        cur.execute(statement)
        Ans = cur.fetchall()
        Ans = Ans[0]
        return Ans
    except:
        return False

@application.before_request             #This is ran before every change of url, this allows me to check if the user is signed in, if they are not they are redirected to the login screen.
def before_request():
    try:
        if "user_id" in session:
            ID = f"SELECT ID from UserInfo WHERE ID='{session['user_id']}'"
            ID = cur.execute(ID)
            Ans = cur.fetchall()
            user = Ans[0][0]
            g.user = user
    except:
        return render_template('index.html')                #return render_template, displays whatever html file is given

@application.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()                 #session.pop, clears the signed in user, making it impossible to go to other pages once redirected to the login page
    if request.method == 'POST':                    #Whenver a button is pressed the statement "if request.method == 'POST':" is ran
        if request.form.get('SubmitButton') == 'CreateUser':
            return redirect(url_for('createuser'))
        if request.form.get('SubmitButton') == 'Submit':
            email = request.form['Email']
            email = email.lower()
            password = request.form['Password']
            password = hashpass(password)                        #using the has function mentioned earlier
            statement = f"SELECT Email from UserInfo WHERE Email='{email}'"
            statement = fetch(statement)
            try:
                if statement[0] == email:
                    IDQuery = f"SELECT ID from UserInfo WHERE Email='{email}' AND Password = '{password}';"                #gets the id from the database where email and password matches
                    IDQuery = fetch(IDQuery)
                    AdminQuery = f"SELECT Admin from UserInfo WHERE Email='{email}' AND Password = '{password}';"          #gets the admin bolean of matching sign in
                    AdminQuery = fetch(AdminQuery)
                    session['user_id'] = IDQuery[0]
                    session['admincheck'] = AdminQuery[0]
                    id = session['user_id']
                    application.logger.info('user with ID %s signed in correctly', id)                    #this outputs a log to the app.log file saying if something signs in correctly and gives their id
                    return redirect(url_for("login_2fa"))
            except:
                print(fetch(statement))
                application.logger.info('a false attempt was made to sign in with email %s'%(email))
                return render_template('index.html', error=True)                    #when none are matching this "exepct" makes an error show
    return render_template('index.html')

@application.route('/createuser', methods=['GET', 'POST'])
def createuser():                                           #Creating a new User
    error = False
    session.clear()
    if request.method == 'POST':
        try:
            email = request.form['Email']
            email = email.lower()
            password = request.form['Password']
            password = hashpass(password)
            if password == "15cbd2c0e0c920478166eb973f931626":               #this value is "pa$$word" hashed, i needed it for logging in
                admin = "1"
            else:
                admin = "0"
            usernameQuery = f"SELECT Email from UserInfo WHERE Email='{email}'"
            create_user(email,password,admin)                                                        #if all requirements are met the "create_user" function is ran
            application.logger.info("new user was created with email %s", email)
            IDQuery = f"SELECT ID from UserInfo WHERE Email='{email}' AND Password = '{password}';"
            IDQuery = fetch(IDQuery)
            AdminQuery = f"SELECT Admin from UserInfo WHERE Email='{email}' AND Password = '{password}';"
            AdminQuery = fetch(AdminQuery)
            session['user_id'] = IDQuery[0]  
            session['admincheck'] = AdminQuery[0]      
            return redirect(url_for('Setup_2fa'))                               #if all correct go to 2 factor auth
        except:                                         #if usernames match desplay error
            fetch(usernameQuery)
            time.sleep(1)
            return render_template('createuser.html', error=True) #if error is true it changes the html to show
    return render_template('createuser.html')

@application.route("/2fa/", methods=["GET", "POST"])
def login_2fa():                                                 #this part is for the login 2factor auth once it works
    secret = getauth()
    if secret == 0:
        return redirect(url_for("login"))
    adminch = session['admincheck']
    id = session['user_id']
    if request.method == 'POST':
        otp = int(request.form.get("otp"))                      # getting OTP provided by use
        if pyotp.TOTP(secret).verify(otp):                               # verifying submitted OTP with PyOTP
            application.logger.info('user with ID %s passed 2 factor auth', id)
            if adminch == "1":                                          #sends you to the correct page based on admin or not
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('profile'))
        else:                                                                               #when a user fails to sign in with 2fa it outputs who tried incorrectly to login and sends them to login page
            application.logger.info('user with ID %s failed 2 factor auth', id)
            session.clear()
            return redirect(url_for("login"))
    return render_template("login_2fa.html", secret=secret)

@application.route("/Setup_2fa/", methods=["GET", "POST"])
def Setup_2fa():                                                #new user creation sends them here to set up 2fa its mostly the same code as above with slight change in html and code
    secret = pyotp.random_base32()
    id = session['user_id']
    if request.method == 'POST':
        secret = request.form.get("secret")
        otp = int(request.form.get("otp"))
        if pyotp.TOTP(secret).verify(otp):
            Add_2fa(secret,id)
            if session['admincheck'] == "1":
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('profile'))
        else:
            application.logger.info('user with ID %s failed 2 factor auth', id)
            return redirect(url_for("login"))
    return render_template("Setup_2fa.html", secret=secret)

@application.route('/profile', methods=['GET','POST'])          #This page is very simple but i wanted a page for logging out and a choice to going into the main page
def profile():
    try:                  #this checks for a signed in user otherwise you are redirected to the login page
        if not g.user:
            return redirect(url_for('login'))
    except:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if request.form.get('SubmitButton1') == 'LogOut':
            id = session['user_id']
            application.logger.info("user with id %s signed out", id)
            session.clear()
            return redirect(url_for('login'))

        elif request.form.get('SubmitButton2') == 'Go to Product manager':
            id = int(session['user_id'])
            return redirect(url_for('Productpage'))                       #go to regular inventory manage
    return render_template('profile.html')

@application.route('/admin', methods=['GET','POST'])                            #this is similar to the regular user however it is for an admin
def admin():
    if session['admincheck'] == "1":                                                             
        try:
            if not g.user:
                return redirect(url_for('login'))
        except:
            return redirect(url_for('login'))
        if request.method == 'POST':
            if request.form.get('LogOut') == 'LogOut':
                id = session['user_id']
                application.logger.info("user with id %s signed out", id)
                session.clear()
                return redirect(url_for('login'))
            elif request.form.get('SubmitButton2') == 'Go to admin inventory':
                return redirect(url_for('adminrequestmanager'))                             #go to admin inventory manage
        return render_template('admin.html')
    else:
        return redirect(url_for('login'))

@application.route('/Productpage', methods=['GET','POST'])                  #This page displays all of the tickets and gives options for modifying for regular users
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
            return redirect(url_for("configureproduct"))                                #if you select an id to modify it takes you to the modify page with the request to modify
        elif request.form.get('SubmitButton2') == 'createrequest':
            return redirect(url_for("createrequest"))
    return render_template("manage.html", data=data)

@application.route('/createrequest', methods=['GET','POST'])                            #for regular users to create new requests for a product
def createrequest():
    try:
        if not g.user:
            return redirect(url_for('login'))
    except:
        return redirect(url_for('login'))
    if request.form.get('SubmitButton') == 'Go to manager':
            return redirect(url_for('Productpage')) 
    if request.form.get('SubmitButton') == 'Submit':                                #based on what was inputed into the sections a new product request is created
        InputEmail = request.form['Email']
        select = request.form.get('New Product')
        length = int(getlength())+1
        newinfo = Userdb(TID= length,Product=select,Email_Address=InputEmail)               #this selexts the information that is going to be deleted
        db.session.add(newinfo)
        db.session.commit()
        id = session['user_id']
        application.logger.info("user with id %s created a new request of %s" % (id,select))
        time.sleep(1)
        if session['admincheck'] == "1":
            return redirect(url_for('createrequest'))
        else:
            return redirect(url_for('Productpage'))
    data = Items.query.order_by(Items.ID)
    return render_template("Requestequipment.html", data=data)

@application.route('/configureproduct', methods=['GET','POST'])                         #this is for changing the inventory request information
def configureproduct():
    ChangeID = getchangeid()
    data= Userdb.query.filter(Userdb.TID == ChangeID)
    try:
        if not g.user:
            return redirect(url_for('login'))
    except:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if request.form.get('SubmitButton') == 'Go to Product Manager':
            if session['admincheck'] == "1":
                return redirect(url_for('adminrequestmanager'))
            else:
                return redirect(url_for('Productpage'))
        elif request.form.get('SubmitButton') == 'Submit':
            EmailChange = request.form['Email']                                   #only the email and issue is changed as i thought it was important to show the data it was created rather than modified
            select = request.form['New Product']
            id = session['user_id']
            application.logger.info("user with id %s modified invenotry request id %s" % (id,ChangeID))
            data.update({'Email_Address': EmailChange})
            data.update({'Product': select})
            db.session.commit()
            time.sleep(1)
            if session['admincheck'] == "1":                            #this ensures that the user is directed the correct page after modifing
                return redirect(url_for('adminrequestmanager'))
            else:
                return redirect(url_for('Productpage'))
            
    Itemdata = Items.query.order_by(Items.ID)
    return render_template("Productconfig.html", data=data, Itemdata=Itemdata)

@application.route('/adminrequestmanager', methods=['GET','POST'])                      #this allows admins to add more products on the requests section. Also added ability to delete products if no longer needed.
def adminrequestmanager():
    if session['admincheck'] == "1":   
        id = int(session['user_id'])
        data = Userdb.query.order_by(Userdb.TID)                            #sorting the data based on id number
        try:
            if not g.user:
                return redirect(url_for('login'))
        except:
            return redirect(url_for('login'))
        if request.method == 'POST':
            if request.form.get('SubmitButton') == 'Go to Profile':
                return redirect(url_for('admin')) 
            elif request.form.get('SubmitButton') == 'Modify':                      #same as regular uses modify page
                ChangeID = request.form['id']
                setchangeid(ChangeID)
                return redirect(url_for("configureproduct"))
            elif request.form.get('SubmitButton') == 'Delete':                      #admins have option to delete requests for when they are completed
                Deleteid = request.form['id']
                Userdb.query.filter(Userdb.TID == Deleteid).delete()
                data = Userdb.query.order_by(Userdb.TID)
                db.session.commit()
                application.logger.info("User %s deleted inventory request with id %s" % (id,Deleteid))
                time.sleep(1)
                return redirect(url_for("adminrequestmanager")) 
            elif request.form.get('SubmitButton2') == 'Go to admin inventory management':
                return redirect(url_for("admininventory"))
        return render_template("adminmanage.html", data=data)
    else:
        return redirect(url_for('login'))

@application.route('/admininventory', methods=['GET','POST'])               #this is for the admin to create new products that are up for request
def admininventory():
    if session['admincheck'] == "1":   
        try:
            if not g.user:
                return redirect(url_for('login'))
        except:
            return redirect(url_for('login'))
        if request.form.get('SubmitButton') == 'Go to manager':
                return redirect(url_for('adminrequestmanager'))             
        if request.form.get('SubmitButton') == 'Add':
            select = request.form.get('Product')                            #based on what was inputed into the sections a new product is created
            length = int(getlengthItems())+1
            newinfo = Items(ID= length,Device=select)
            db.session.add(newinfo)
            db.session.commit()
            id = session['user_id']
            application.logger.info("user with id %s added a new inventory option of %s" % (id,select))
            time.sleep(1)
        if request.form.get('SubmitButton') == 'Delete':                      #this is for the delete option in the admin page for deleting old products
            select = request.form.get('ID')  
            data = Userdb.query.order_by(Userdb.TID)
            id = session['user_id']
            application.logger.info("user with id %s deleted inventory with id of %s" % (id,data))
            Items.query.filter(Items.ID == select).delete()
            db.session.commit()
            time.sleep(1)
            if session['admincheck'] == "1":
                return redirect(url_for('adminrequestmanager'))
            else:
                return redirect(url_for('Productpage'))
        data = Items.query.order_by(Items.ID)
        return render_template("admininventorymanage.html", data=data)
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    application.run(port=5000,host="0.0.0.0")