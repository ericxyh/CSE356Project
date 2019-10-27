from flask import Flask, request, render_template, jsonify, make_response
from flask_mail import Mail, Message
from bson.objectid import ObjectId
import time, random, smtplib
from pymongo import MongoClient


client = MongoClient()
db = client.twitter
twiu = db.users
twip = db.posts

app = Flask(__name__)
mail = Mail(app)

@app.route('/', methods = ['GET'])
def default():
	u = request.cookies.get('user')
	if u is None:
		return render_template('homepage.html')
	else:
		return render_template('homepage.html',login=u)

@app.route('/static/<pname>', methods = ['GET'])
def getpage(pname):
	u = request.cookies.get('user')
	if u is None:
		return render_template('%s.html' % pname)
	else:
		return render_template('%s.html' % pname, login=u)

@app.route('/reset', methods = ['POST'])
def reset():
	twiu.remove()
	twip.remove()
	return('Removed!')

@app.route('/adduser', methods = ['POST'])
def addUser():
	if request.method == 'POST':
		nuser = request.get_json()
#		print('sign up',nuser)
		for x in twiu.find({'username' : nuser['username']}):
			if x['email'] is  nuser['email']:
				return jsonify(status = 'error', error = 'User already exists.')
		ustat = {
			'username': nuser['username'],
			'password' : nuser['password'],
			'email' : nuser['email'],
			'key' : 'abracadabra',
			'verify' : 'no'
		}
		twiu.insert_one(ustat)
		vmailstr = "validation key: <"+"abracadabra"+">"
		msg = Message(recipients = [nuser['email']], body = vmailstr,
			sender = 'ansible-receipt.cloud.compas.cs.stonybrook.edu')
		try:
			mail.send(msg)
			return jsonify(status = 'OK', error = '')
		except Exception as ex:
#			print(ex)
			return jsonify(status = 'error', error = 'Cannot send mail')

@app.route('/login', methods = ['POST'])
def login():
	if request.method == 'POST':
		lreq = request.get_json()
#		print('sign in',lreq)
		luser = twiu.find_one({'username' : lreq['username'], 'password' : lreq['password']})
#		print(luser)
		if luser is None:
			return jsonify(status = 'error', error = 'Username or password is wrong')
		elif luser['verify'] != 'yes':
			return jsonify(status = 'error', error = 'User not verified')
		else:
			r = make_response(jsonify(status = 'OK', error = ''))
			r.set_cookie('user', lreq['username'])
			return r

@app.route('/logout', methods = ['POST'])
def logout():
	u = request.cookies.get('user')
	if request.method == 'POST':
		if u is None:
			return jsonify(status = 'error', error = 'Not logged in')
		else:
			resp = make_response()
			resp.delete_cookie('user')
			return jsonify(status = 'OK', error = '')

@app.route('/verify', methods = ['POST'])
def verify():
	if request.method == 'POST':
		vreq =  request.get_json()
#		print('verify', vreq)
		mcheck = twiu.find_one({'email' : vreq['email']})
		if mcheck is None:
			return jsonify(status = 'error', error = 'Wrong email')
#		print (mcheck)
		if vreq['key'] is 'abracadabra':
			twiu.update_one(mcheck, {"$set" : { 'verify' : 'yes'}})
			return jsonify(status = 'OK')
		if (mcheck['key'] != vreq['key']):
			return jsonify(status = 'error', error = 'Wrong key')
		else:
			twiu.update_one(mcheck, {"$set" : { 'verify' : 'yes'}})
			return jsonify(status = 'OK')

@app.route('/additem', methods = ['POST'])
def addItem():
	if request.method == 'POST':
		u = request.cookies.get('user')
		if u is None:
			return jsonify(status = 'error', error = 'Not logged in')
		areq = request.get_json()
		if 'content' not in areq.keys():
			return jsonify(status = 'error', error = 'No content in post')
#		print(u,'additem',areq)
		newitem = {
			'username' : u,
			'property' : {'likes':0},
			'retweeted' : 0,
			'timestamp' : time.time(),
			'content' : areq['content'],
			'childType' : None
		}
		if 'childType' in areq.keys():
			newitem['childType'] = areq['childType']
		pid = twip.insert_one(newitem)
		spid = str(pid.inserted_id)
		return jsonify(status = 'OK', id = spid)

@app.route('/item/<id>', methods = ['GET','DELETE'])
def getPost(id):
	try:
		post = twip.find_one({'_id': ObjectId(id)})
	except:
		return jsonify(status = 'error', error = 'Not correct id format')
	if post is None:
		return jsonify(status = 'error', error = 'No post with the id of'+str(id))
	if request.method == 'GET':
		ifound = {
			'id' : id,
			'username' : post['username'],
			'property' : post['property'],
			'retweeted' : post['retweeted'],
			'content' : post['content'],
			'timestamp' : post['timestamp']
		}
		return jsonify(status = 'OK', item = ifound)
	if request.method == 'DELETE':
		pass
####

@app.route('/search', methods = ['POST'])
def search():
### search query, username, following
	if request.method == 'POST':
		sreq = request.get_json()
		limit = 25
		t = time.time()
		items = []
		if 'limit' in sreq.keys():
			limit = sreq['limit']
			if limit > 100:
				lim = 100
		if 'timestamp' in sreq.keys():
			t = sreq['timestamp']
		for x in twip.find({'timestamp': {"$lte": t}}):
			if len(items)>=limit:
				break
			else:
				i = {
					'id' : str(x['_id']),
					'username' : x['username'],
					'property' : x['property'],
					'retweeted' : x['retweeted'],
					'content' : x['content'],
					'timestamp' : x['timestamp']
				}
				items.append(i)
#		print(items)
		return jsonify(status = 'OK', items = items)

@app.route('/user/<username>', methods = ['GET'])
def userProfile(username):
	pass

@app.route('/user/<username>/posts', methods = ['GET'])
def userPost(username):
	pass

@app.route('/user/<username>/followers', methods = ['GET'])
def followUser(username):
	pass

@app.route('/user/<username>/following', methods = ['GET'])
def userFollow():
	pass

@app.route('/follow', methods = ['POST'])
def follow():
	pass

if __name__ == "__main__":
#	app.debug = True
	app.run(host='0.0.0.0',port=80)
