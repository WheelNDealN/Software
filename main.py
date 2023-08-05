#All my import
import time
import sqlite3 as sql
import pyotp
import logging
import hashlib 
from flask import (Flask, g, redirect, render_template, request, session, url_for, render_template)
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import update


#This is set up for databases and for the flask server
application = Flask(__name__, template_folder='template')
application.secret_key = 'supersecret'
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
application.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///Products.db"
db = SQLAlchemy(application)
con = sql.connect('Userdata.db', check_same_thread=False, timeout=10)
cur = con.cursor()
logging.basicConfig(filename = 'app.txt',level=logging.DEBUG,filemode='w')
logger = logging.getLogger(__name__)
handler = logging.FileHandler('app.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


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
GobEmail = ""

#Same as getting the Users length this one is for the tickets, allowing me to add one to the ID when a new one is created
def getlength():
    try:
        ordered = Userdb.query.order_by(Userdb.TID.desc())
        return ordered[0].TID
    except:
        return -1

#Same as getting the Users length this one is for the tickets, allowing me to add one to the ID when a new one is created
def getlengthItems():
    try:
        ordered = Items.query.order_by(Items.ID.desc())
        return ordered[0].ID
    except:
        return -1

#refactored function for getting the length of my Users, this is useful for the primary key going up when a user is added
def getuserlen():
  ordered = """SELECT ID FROM UserInfo ORDER BY ID DESC;"""
  cur.execute(ordered)
  Ans = cur.fetchall()
  Ans = Ans[0][0]
  return Ans

def getauth():
    try:
        authuser=f"SELECT Authkey from UserInfo WHERE ID='{session['user_id']}'"
        statement = fetch(authuser)
        statement = ''.join(statement)
        return statement
    except:
        return 0

#This function was to clean up the code as the Statement variable is long
def create_user(addemail,addpassword,addadmin):
    IDtoAdd = int(getuserlen()+1)
    user=addemail
    passw=addpassword
    admin=addadmin
    cur.execute("INSERT INTO UserInfo (ID,Email,Admin,Password) VALUES (?,?,?,?)",(IDtoAdd,addemail,admin,passw))
    con.commit()

def Add_2fa(secret,id):
    Secret = secret
    ID=id
    sql = "UPDATE UserInfo SET AuthKey = '%s' WHERE ID = '%s'"% (Secret,ID)
    cur.execute(sql)
    con.commit()

#These two functions where used when i had to select the index of the Produc database for modifing
def setchangeid(ID):
    global ChangeID
    ChangeID = ID

def getchangeid():
    return ChangeID

def hashpass(passw):
    salt = ("diD_h12$j")
    passw += salt
    hashed = hashlib.md5(passw.encode())  
    hashed = hashed.hexdigest()
    return hashed

#
#
#test application and then deploy the code
#one workflow with two jobs
#add logging
#admin has to create an admin account
#
#


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
    session.clear()
    #session.pop, clears the signed in user, making it impossible to go to other pages once redirected to the login page

    #Whenver a button is pressed the statement "if request.method == 'POST':" is ran
    if request.method == 'POST':
        if request.form.get('SubmitButton') == 'CreateUser':
            return redirect(url_for('createuser'))
            
        if request.form.get('SubmitButton') == 'Submit':
            email = request.form['Email']
            email = email.lower()
            password = request.form['Password']
            password = hashpass(password)
            statement = f"SELECT Email from UserInfo WHERE Email='{email}'"
            statement = fetch(statement)

            #this try method checks for matching usernames and signs them in if they are matching
            try:
                if statement[0] == email:
                    IDQuery = f"SELECT ID from UserInfo WHERE Email='{email}' AND Password = '{password}';"
                    IDQuery = fetch(IDQuery)
                    AdminQuery = f"SELECT Admin from UserInfo WHERE Email='{email}' AND Password = '{password}';"
                    AdminQuery = fetch(AdminQuery)
                    session['user_id'] = IDQuery[0]  
                    session['admincheck'] = AdminQuery[0]      
                    id = session['user_id']
                    application.logger.info('user with ID %s signed in correctly', id)
                    return redirect(url_for("login_2fa"))
                       
            #when none are matching this "exepct" makes an error show
            except:
                print(fetch(statement))
                application.logger.info('a false attempt was made to sign in with email %s'%(email))
                return render_template('index.html', error=True)         

    return render_template('index.html')

@application.route("/2fa/", methods=["GET", "POST"])
def login_2fa():
    secret = getauth()
    if secret == 0:
        return redirect(url_for("login"))
    adminch = session['admincheck']
    id = session['user_id']
    if request.method == 'POST':
        # getting secret key used by user

        # getting OTP provided by user
        otp = int(request.form.get("otp"))

        # verifying submitted OTP with PyOTP
        if pyotp.TOTP(secret).verify(otp):
            application.logger.info('user with ID %s passed 2 factor auth', id)
            if adminch == "1":
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('profile'))
        else:
            application.logger.info('user with ID %s failed 2 factor auth', id)
            session.clear()
            return redirect(url_for("login"))
    return render_template("login_2fa.html", secret=secret)

@application.route("/Setup_2fa/", methods=["GET", "POST"])
def Setup_2fa():
    secret = pyotp.random_base32()
    id = session['user_id']
    if request.method == 'POST':
        secret = request.form.get("secret")
        # getting secret key used by user
        
        # getting OTP provided by user
        otp = int(request.form.get("otp"))
        # verifying submitted OTP with PyOTP
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

#Creating a new User
@application.route('/createuser', methods=['GET', 'POST'])
def createuser():
    error = False
    session.clear()
    if request.method == 'POST':
        email = request.form['Email']
        email = email.lower()
        password = request.form['Password']
        password = hashpass(password)
        if password == "15cbd2c0e0c920478166eb973f931626":
            admin = "1"
        else:
            admin = "0"
        usernameQuery = f"SELECT Email from UserInfo WHERE Email='{email}'"
        #if all requirements are met the "create_user" function is ran
        create_user(email,password,admin)
        application.logger.info("new user was created with email %s", email)
        #whenever i add delay to the webpage i am showing the user a message, or creating a fake a buffer to make it feel as though something is happening
        IDQuery = f"SELECT ID from UserInfo WHERE Email='{email}' AND Password = '{password}';"
        IDQuery = fetch(IDQuery)
        AdminQuery = f"SELECT Admin from UserInfo WHERE Email='{email}' AND Password = '{password}';"
        AdminQuery = fetch(AdminQuery)
        session['user_id'] = IDQuery[0]  
        session['admincheck'] = AdminQuery[0]      
        return redirect(url_for('Setup_2fa'))
            
        #if usernames match desplay error
        #except:
        #    fetch(usernameQuery)
        #    time.sleep(1)
        #    return render_template('createuser.html', error=True)
        
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
            id = session['user_id']
            application.logger.info("user with id %s signed out", id)
            session.clear()
            return redirect(url_for('login'))

        elif request.form.get('SubmitButton2') == 'Go to Product manager':
            id = int(session['user_id'])
            return redirect(url_for('Productpage'))                       

    return render_template('profile.html')

#this is similar to the regular user however it is for an admin
@application.route('/admin', methods=['GET','POST'])
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
                return redirect(url_for('adminrequestmanager'))
        
        return render_template('admin.html')
    else:
        application.logger.info("User %i deleted inventory request with id %s ",id,Deleteid)
        return redirect(url_for('login'))

 
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

            return redirect(url_for("configureproduct"))
            
        elif request.form.get('SubmitButton2') == 'createrequest':
            return redirect(url_for("createrequest"))
        
    return render_template("manage.html", data=data)

#this allows admins to add more products on the requests section. Also added ability to delete products if no longer needed.
@application.route('/adminrequestmanager', methods=['GET','POST'])
def adminrequestmanager():
    if session['admincheck'] == "1":   
        id = int(session['user_id'])
        data = Userdb.query.order_by(Userdb.TID)
        try:
            if not g.user:
                return redirect(url_for('login'))
        except:
            return redirect(url_for('login'))

        if request.method == 'POST':

            if request.form.get('SubmitButton') == 'Go to Profile':
                return redirect(url_for('admin')) 

            elif request.form.get('SubmitButton') == 'Modify':
                ChangeID = request.form['id']
                setchangeid(ChangeID)

                return redirect(url_for("configureproduct"))
                    
            elif request.form.get('SubmitButton') == 'Delete':
                Deleteid = request.form['id']
                Userdb.query.filter(Userdb.TID == Deleteid).delete()
                data = Userdb.query.order_by(Userdb.TID)
                db.session.commit()
                Deleted = str(request.form['id'])
                application.logger.info("User %s deleted inventory request with id %s" % (id,Deleted))
                time.sleep(1)
                return redirect(url_for("adminrequestmanager")) 

            elif request.form.get('SubmitButton2') == 'Go to admin inventory management':
                return redirect(url_for("admininventory"))
            
        return render_template("adminmanage.html", data=data)
    else:
        return redirect(url_for('login'))

@application.route('/createrequest', methods=['GET','POST'])
def createrequest():
    try:
        if not g.user:
            return redirect(url_for('login'))
            
    except:
        return redirect(url_for('login'))

    if request.form.get('SubmitButton') == 'Go to manager':
            return redirect(url_for('Productpage')) 

    #based on what was inputed into the sections a new product request is created
    if request.form.get('SubmitButton') == 'Submit':
        InputEmail = request.form['Email']
        select = request.form.get('New Product')
        length = int(getlength())+1
        newinfo = Userdb(TID= length,Product=select,Email_Address=InputEmail)
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

@application.route('/admininventory', methods=['GET','POST'])
def admininventory():
    if session['admincheck'] == "1":   
        try:
            if not g.user:
                return redirect(url_for('login'))
        except:
            return redirect(url_for('login'))

        if request.form.get('SubmitButton') == 'Go to manager':
                return redirect(url_for('adminrequestmanager')) 

        #based on what was inputed into the sections a new product is created
        if request.form.get('SubmitButton') == 'Add':
            select = request.form.get('Product')
            length = int(getlengthItems())+1
            newinfo = Items(ID= length,Device=select)
            db.session.add(newinfo)
            db.session.commit()
            id = session['user_id']
            application.logger.info("user with id %s added a new inventory option of %s" % (id,select))
            time.sleep(1)

        if request.form.get('SubmitButton') == 'Delete':
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
    

#this is for changing the ticket information that i thought was important
@application.route('/configureproduct', methods=['GET','POST'])
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
            #only the email and issue is changed as i thought it was important to show the data it was created rather than modified
            EmailChange = request.form['Email']
            select = request.form['New Product']
            id = session['user_id']
            application.logger.info("user with id %s modified invenotry request id %s" % (id,ChangeID))
            data.update({'Email_Address': EmailChange})
            data.update({'Product': select})
            db.session.commit()
            time.sleep(1)
            #this ensures that the user is directed the correct page after modifing
            if session['admincheck'] == "1":
                return redirect(url_for('adminrequestmanager'))
            else:
                return redirect(url_for('Productpage'))
            
    Itemdata = Items.query.order_by(Items.ID)
    return render_template("Productconfig.html", data=data, Itemdata=Itemdata)

if __name__ == '__main__':
    application.run(port=5000,host="0.0.0.0")