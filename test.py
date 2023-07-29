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

class Userdb(db.Model):
    TID = db.Column(db.Integer, primary_key=True)
    Issue = db.Column(db.String(64), index=True, default = "Issue")
    Email_Address = db.Column(db.String(25), default = "Email Address")
    Date = db.Column(db.String, default = datetime.utcnow)

    def __repr__(self):
        return '<Issue %r>' %self.Date
    