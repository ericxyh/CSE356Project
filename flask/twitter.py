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

@app.route('/', methods = ['GET','POST'])
def default():
	return('Welcome!')

@app.route('/adduser', methods = ['GET','POST'])
def addUser():
	if request.method == 'POST':
		nuser = request.get_json()
		for x in twiu.find({'username' : nuser['username']}):
			if x['email'] is  nuser['email']:
				return jsonify(status = 'ERROR', error = 'User already exists.')
		ustat = {
			'username': nuser['username'],
			'password' : nuser['password'],
			'email' : nuser['email'],
			'key' : 'abracadabra'
		}
		twiu.insert_one(ustat)
		vmailstr = "validation key: <"+"abracadabra"+">"
		msg = Message(recipients = [nuser['email']], body = vmailstr,
			sender = 'ansible-receipt.cloud.compas.cs.stonybrook.edu')
		try:
			mail.send(msg)
			return jsonify(status = 'OK', error = '')
		except Exception as ex:
			print(ex)
			return jsonify(status = 'ERROR', error = 'Cannot send mail')

@app.route('/login', methods = ['GET','POST'])
def login():
	if request.method == 'POST':
		lreq = request.get_json()
		luser =  w2u.find_one({'user' : lreq['username'], 'password' : lreq['password']})
		if luser is None:
			return jsonify(status = 'ERROR', error = 'User does not exist')
		elif luser['verify'] != 'yes':
			return jsonify(status = 'ERROR', error = 'User not verified')
		else:
			r = make_response(jsonify(status = 'OK', error = ''))
			r.set_cookie('user', lreq['username'])
			return r

@app.route('/logout', methods = ['GET','POST'])
def logout():
	u = request.cookies.get('user')
	if u is None:
		return jsonify(status = 'ERROR', error = 'Not logged in')
	else:
		resp = make_response()
		resp.set_cookie('user','',expires=0)
		return jsonify(status = 'OK', error = '')

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