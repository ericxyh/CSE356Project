from flask import Flask, request, render_template, jsonify, make_response, send_file, Response
from flask_mail import Mail, Message
from bson.objectid import ObjectId
import time, random, smtplib, uuid, pymongo
from pymongo import MongoClient
from cassandra.cluster import Cluster

MAILADD = 'bigone.cloud.compas.cs.stonybrook.edu'

client = MongoClient("localhost:27017")
db = client.twitter
twiu = db.users
twip = db.posts
twip.create_index([('content', pymongo.TEXT)])

app = Flask(__name__)
mail = Mail(app)

#app.config['CASSANDRA_HOSTS'] = ['127.0.0.1']
#app.config['CASSANDRA_KEYSPACE'] = "twitter"
#cdb = CQLAlchemy(app)
cluster = Cluster(['127.0.0.1'])
session = cluster.connect('twitter')
mediaget = session.prepare("SELECT file FROM media WHERE id=?")
mediaset = session.prepare("INSERT INTO media (id, user, file,time, post) VALUES (?,?,?,?,'')")
mediapostget = session.prepare("SELECT user,post FROM media WHERE id=?")
mediapostset = session.prepare("UPDATE media SET post = ? WHERE id = ?")
mediadelete = session.prepare("DELETE FROM media WHERE id = ?")

@app.route('/', methods = ['GET'])
def default():
	u = request.cookies.get('user')
	if u is None:
		return render_template('homepage.html')
	else:
		return render_template('homepage.html',login=u)

@app.route('/stat/<pname>', methods = ['GET'])
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
	session.execute("TRUNCATE media")
	return('Removed!')

@app.route('/adduser', methods = ['POST'])
def addUser():
	if request.method == 'POST':
		nuser = request.get_json()
#		print('sign up',nuser)
		for x in twiu.find({'username' : nuser['username']}):
			if x['email'] is nuser['email']:
				return jsonify(status = 'error', error = 'User already exists.'),500
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
			sender = MAILADD)
		try:
			mail.send(msg)
			return jsonify(status = 'OK', error = ''),200
		except Exception as ex:
			print(ex)
			return jsonify(status = 'error', error = 'Cannot send mail'),500

@app.route('/login', methods = ['POST'])
def login():
	if request.method == 'POST':
		lreq = request.get_json()
#		print('sign in',lreq)
		luser = twiu.find_one({'username' : lreq['username'], 'password' : lreq['password']})
#		print(luser)
		if luser is None:
			return jsonify(status = 'error', error = 'Username or password is wrong'),500
		elif luser['verify'] != 'yes':
			return jsonify(status = 'error', error = 'User not verified'),500
		else:
			r = make_response(jsonify(status = 'OK', error = ''))
			r.set_cookie('user', lreq['username'])
			return r,200

@app.route('/logout', methods = ['POST'])
def logout():
	u = request.cookies.get('user')
	if request.method == 'POST':
		if u is None:
			return jsonify(status = 'error', error = 'Not logged in'),500
		else:
			resp = make_response()
			resp.delete_cookie('user')
			return jsonify(status = 'OK', error = ''),200

@app.route('/verify', methods = ['POST'])
def verify():
	if request.method == 'POST':
		vreq =  request.get_json()
#		print('verify', vreq)
		mcheck = twiu.find_one({'email' : vreq['email']})
		if mcheck is None:
			return jsonify(status = 'error', error = 'Wrong email'),500
#		print (mcheck)
		if vreq['key'] is 'abracadabra':
			twiu.update_one(mcheck, {"$set" : { 'verify' : 'yes'}})
			return jsonify(status = 'OK'),200
		if (mcheck['key'] != vreq['key']):
			return jsonify(status = 'error', error = 'Wrong key'),500
		else:
			twiu.update_one(mcheck, {"$set" : { 'verify' : 'yes'}})
			return jsonify(status = 'OK'),200

@app.route('/additem', methods = ['POST'])
def addItem():
	if request.method == 'POST':
		u = request.cookies.get('user')
		if u is None:
			return jsonify(status = 'error', error = 'Not logged in'),500
		areq = request.get_json()
		if 'content' not in areq.keys():
			return jsonify(status = 'error', error = 'No content in post'),500
#		print(u,'additem',areq)
		newitem = {
			'username' : u,
			'property' : {'likes':0,'list':[]},
			'retweeted' : 0,
			'timestamp' : time.time(),
			'content' : areq['content'],
			'childType' : None,
			'parent' : None,
			'media' : []
		}
		if ('childType' in areq.keys()) ^ ('parent' in areq.keys()):
			return jsonify(status = 'error', error = 'Must have both parent and child info'),500
		elif 'childType' in areq.keys() and 'parent' in areq.keys():
			paid = areq['parent']
			newitem['childType'] = areq['childType']
			newitem['parent'] = paid
			if areq['childType'] == 'retweet':
				try:
					papost = twip.find_one({'_id': ObjectId(paid)})
				except:
					return jsonify(status = 'error', error = 'Not correct parent id format'),500
				if papost is None:
					return jsonify(status = 'error', error = 'No parent post with the id of '+str(paid)),500
				twip.update_one({'_id': ObjectId(paid)}, {"$set" : {"retweeted" : papost['retweeted']+1}})
		if 'media' in areq.keys():
			newitem['media'] = areq['media']
		pid = twip.insert_one(newitem)
		spid = str(pid.inserted_id)
		if 'media' in areq.keys():
			for i in areq['media']:
				uid = uuid.UUID(i)
				row = session.execute(mediapostget,[uid])
				f = row.one()
				if f is None:
					return jsonify(status = 'error', error = 'No media with the id of '+str(i)),500
				elif f.user != u:
					return jsonify(status = 'error', error = 'Media with the id of '+str(i)+' not uploaded by current user'),500
				elif f.post != '':
					return jsonify(status = 'error', error = 'Media with the id of '+str(i)+' used in another post'),500
				else:
					session.execute(mediapostset,[spid,uid])
		return jsonify(status = 'OK', id = spid)

@app.route('/item/<id>', methods = ['GET','DELETE'])
def getPost(id):
	try:
		post = twip.find_one({'_id': ObjectId(id)})
	except:
		return jsonify(status = 'error', error = 'Not correct id format'),500
	if post is None:
		return jsonify(status = 'error', error = 'No post with the id of '+str(id)),500
	if request.method == 'GET':
		ifound = {
			'id' : id,
			'username' : post['username'],
			'property' : {'likes': post['property']['likes']},
			'retweeted' : post['retweeted'],
			'content' : post['content'],
			'timestamp' : post['timestamp'],
			'childType' : post['childType'],
			'parent' : post['parent'],
			'media' : post['media']
		}
		return jsonify(status = 'OK', item = ifound)
	if request.method == 'DELETE':
#delete media
		u = request.cookies.get('user')
		if u is None:
			return 306
		if post['username'] != u:
			return 307
		else:
			m = post['media']
			for n in m:
				session.execute(mediadelete,[uuid(n)])
			try:
				twip.delete_one({"_id":ObjectId(id)})
				return 200
			except:
				return 308

@app.route('/search', methods = ['POST'])
def search():
### rank, parent, reply, hasMedia
#search results not ordered by timestamp, newest first
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
		if u is not None and 'following' in sreq.keys() and sreq['following']:
			suser = twiu.find_one({'username' : u})
			if suser:
				users.extend(suser['following'])
			search['username'] = {'$in': users}
		else:
			if len(users)>0:
				search['username'] = {'$in': users}
		#sort & rank
		#
		items = []
		for x in twip.find(search).limit(lim).sort('timestamp', pymongo.DESCENDING):
			i = {
				'id' : str(x['_id']),
				'username' : x['username'],
				'property' : {'likes' :x['property']['likes']},
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
	user = twiu.find_one({'username': username})
	if user is None:
		return jsonify(status = 'error', error = 'No user with the name of '+username)
	lim = 50
	if request.args.get('limit') is not None:
		lim = request.args.get('limit', type = int)
		if lim > 200:
			lim = 200
	upost = twip.find({'username':username}).limit(lim)
	ans=[]
	for u in upost:
		ans.append(str(u['_id']))
	return jsonify(status = 'OK', items = ans)

@app.route('/user/<username>/followers', methods = ['GET'])
def followsUser(username):
	user = twiu.find_one({'username': username})
	if user is None:
		return jsonify(status = 'error', error = 'No user with the name of '+username),500
	lim = 50
	if request.args.get('limit') is not None:
		lim = int(request.args.get('limit'))
		if lim > 200:
			lim = 200
	ans = user['followers'][:lim]
	return jsonify(status = 'OK', users = ans),200

@app.route('/user/<username>/following', methods = ['GET'])
def userFollow(username):
	user = twiu.find_one({'username': username})
	if user is None:
		return jsonify(status = 'error', error = 'No user with the name of '+username),500
	lim = 50
	if request.args.get('limit') is not None:
		lim = request.args.get('limit', type = int)
		if lim > 200:
			lim = 200
	ans = user['following'][:lim]
	return jsonify(status = 'OK', users = ans),200

@app.route('/follow', methods = ['POST'])
def follow():
	u = request.cookies.get('user')
	if u is None:
		return jsonify(status = 'error', error = 'Not logged in'),500
	freq = request.get_json()
	print(u,freq)
	if 'username' not in freq.keys() or 'follow' not in freq.keys():
		return jsonify(status = 'error', error = 'Need username and whether to follow or not'),500
	fu = freq['username']
	if u == fu:
		return jsonify(status = 'error', error = "Can't follow/unfollow oneself"),500
	luser = twiu.find_one({'username': u})
	fuser = twiu.find_one({'username': fu})
	if luser is None or fuser is None:
		return jsonify(status = 'error', error = 'User does not exist'),500
	lf = luser['following']
	ff = fuser['followers']
	if fu in lf:
		if freq['follow']:
			return jsonify(status = 'error', error = 'Already following the user'),500
		else:
			twiu.update_one({'username' : u}, {"$pull" : { 'following' : fu}})
			twiu.update_one({'username' : fu}, {"$pull" : { 'followers' : u}})
#			print(twiu.find_one({'username': u}))
#			print(twiu.find_one({'username': fu}))
			return jsonify(status = 'OK'),200
	else:
		if freq['follow']:
			twiu.update_one({'username' : u}, {"$push" : { 'following' : fu}})
			twiu.update_one({'username' : fu}, {"$push" : { 'followers' : u}})
#			print(twiu.find_one({'username': u}))
#			print(twiu.find_one({'username': fu}))
			return jsonify(status = 'OK'),200
		else:
			return jsonify(status = 'error', error = "Can't unfollow user you aren't following"),500

@app.route('/item/<id>/like', methods = ['POST'])
def likepost(id):
	u = request.cookies.get('user')
	lreq = request.get_json()
	if u is None:
		return jsonify(status = 'error', error = 'Not logged in'),500
	if 'like' not in lreq:
		return jsonify(status = 'error', error = 'No boolean availble'),500
	try:
		post = twip.find_one({'_id': ObjectId(id)})
	except:
		return jsonify(status = 'error', error = 'Not correct id format'),500
	if post is None:
		return jsonify(status = 'error', error = 'No post with the id of'+str(id)),500
	llist = post['property']['list']
	print(id,u in llist,lreq['like'],u)
	if u in llist:
		if lreq['like']:
			return jsonify(status = 'error', error = 'Already liked this post'),500
		else:
			print('pull')
			twip.update_one({'_id': ObjectId(id)}, {"$pull" : { 'property.list' : u}})
			twip.update_one({'_id': ObjectId(id)}, {"$set" : { 'property.likes' : post['property']['likes']-1}})
			return jsonify(status = 'OK'),200
	else:
		if lreq['like']:
			print('push')
			twip.update_one({'_id': ObjectId(id)}, {"$push" : { 'property.list' : u}})
			twip.update_one({'_id': ObjectId(id)}, {"$set" : { 'property.likes' : post['property']['likes']+1}})
			return jsonify(status = 'OK'),200
		else:
			return jsonify(status = 'error', error = "Can't unlike post you isn't liking"),500
	return jsonify(status = 'OK')


@app.route('/addmedia', methods = ['POST'])
def addmedia():
	u = request.cookies.get('user')
	if u is None:
		return jsonify(status = 'error', error = 'Not logged in'),500
	f = request.files.to_dict()
	if 'content' not in f:
		return jsonify(status = 'error', error = 'No media file'),500
	f = f['content'].read()
	id = uuid.uuid1()
	a = session.execute(mediaset, [id, u, f,time.time()])
	return jsonify(status = 'OK', id = id.hex)
# user?

@app.route('/media/<id>', methods = ['GET'])
def getmedia(id):
	uid = uuid.UUID(id)
	row = session.execute(mediaget,[uid])
	f = row.one()
	if f is None:
		return 460
	f=f.file
	return Response(f, mimetype='multipart/form-data'),200

if __name__ == "__main__":
#	app.debug = True
	app.run(host='0.0.0.0',port=80,threaded=True)


#delete unrelated medias