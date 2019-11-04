from flask import Flask, request, render_template, jsonify, make_response
from flask_mail import Mail, Message
from bson.objectid import ObjectId
import time, random, smtplib
from pymongo import MongoClient, TEXT


client = MongoClient("localhost:27017")
db = client.twitter
twiu = db.users
twip = db.posts
twip.create_index([('content', TEXT)])

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

@app.route('/reset', methods = ['GET','POST'])
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
			'verify' : 'no',
			'followers' : [],
			'following' : []
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
		u = request.cookies.get('user')
		if u is None:
			return jsonify(status = 'error', error = 'Not logged in')
		if post['username'] is not u:
			return jsonify(status = 'error', error = "Can't delete other people's post")
		else:
			re = make_response()
			try:
				twip.delete_one({"_id":ObjectId(id)})
				re.status_code = 200
				return re
			except:
				re.status_code = 208
				return re

@app.route('/search', methods = ['POST'])
def search():
### search query, username, following
	if request.method == 'POST':
		sreq = request.get_json()
		search = {}
		lim = 25
		if 'limit' in sreq.keys():
			limit = sreq['limit']
			if limit > 100:
				lim = 100
		t = time.time()
		if 'timestamp' in sreq.keys():
			t = sreq['timestamp']
		search['timestamp'] = {"$lte": t}
		if 'q' in sreq.keys() and sreq['q'] != '':
			search['$text'] = {"$search": sreq['q']}
		users = []
		if 'username' in sreq.keys():
			users.append(sreq['username'])
		u = request.cookies.get('user')
		if u is not None and ('following' not in sreq.keys() or sreq['following']):
			suser = twiu.find_one({'username' : u})
			users.extend(suser['following'])
		if len(users)>0:
			search['username'] = {'$in': users}
		items = []
		for x in twip.find(search).limit(lim):
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
	user = twiu.find_one({'username': username})
	if user is None:
		return jsonify(status = 'error', error = 'No user with the name of '+username)
	userinfo = {
		'email' : user['email'],
		'followers' : len(user['followers']),
		'following' : len(user['following'])
	}
	return jsonify(status = 'OK', user = userinfo)

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
