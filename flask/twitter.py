from flask import Flask, request, render_template, jsonify, make_response
from flask_mail import Mail, Message
from bson.objectid import ObjectId
import datetime, random, smtplib
from pymongo import MongoClient


client = MongoClient()
db = client.twitter
twiu = db.users

app = Flask(__name__)
mail = Mail(app)


@app.route('/adduser', methods = ['GET','POST'])
def addUser():
	pass

@app.route('/login', methods = ['GET','POST'])
def login():
	pass
@app.route('/logout', methods = ['GET','POST'])
def logout():
	pass

@app.route('/verify', methods = ['GET','POST'])
def verify():
	pass

@app.route('/additem', methods = ['GET','POST'])
def addItem():
	pass

@app.route('/item/<id>', methods = ['GET'])
def getPost(id):
	pass

@app.route('/search', methods = ['GET','POST'])
def search():
	pass

if __name__ == "__main__":
#	app.debug = True
	app.run(host='0.0.0.0',port=80)
