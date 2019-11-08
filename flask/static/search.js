var userName = readCookie('user');

function readCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}

function singleSearch(){
    document.getElementById("result").innerHTML = "";
    document.getElementById("result2").innerHTML = "";
	var it  = document.getElementById("pid").value;
	if (it === ''){
		document.getElementById("result").innerHTML = 'Please enter ID'
	}
	else{
		var request = new XMLHttpRequest();
		request.onreadystatechange = function(){
			if(this.readyState == 4 && this.status == 200||this.readyState == 4 && this.status == 500){
				var results = JSON.parse(request.responseText);
				if(results.status === "OK")
					document.getElementById("result").innerHTML = postChange(results.item) +"<br>"
				if(results.status === "error")
					document.getElementById("result").innerHTML = results.error
			}
		}
		request.open("GET", "/item/"+it,true);
		request.send();
	}
}

function multiSearch(){
    document.getElementById("result").innerHTML = "";
    document.getElementById("result2").innerHTML = "";
	var json = {};
	var t = document.getElementById("time").value;
	var l = document.getElementById("num").value;
	var q = document.getElementById("q").value;
	var u = document.getElementById("uname").value;
	if (t!=""){
		json.timestamp = parseInt(t);
	}
	if (l!=""){
		json.limit = parseInt(l);
	}
	if (q!=""){
		json.q = q;
	}
	if (u!=""){
		json.username = u;
	}
	if (userName != null && document.getElementById("following") != null){
        json.following = document.getElementById("following").checked;
	}
	else{
		json.following = false
	}
	var request = new XMLHttpRequest();
	request.onreadystatechange = function(){
		if(this.readyState == 4 && this.status == 200||this.readyState == 4 && this.status == 500){
			var results = JSON.parse(request.responseText);
			if(results.status === "OK"){
				var res = "";
				if (results.items.length == 0){
					document.getElementById("result").innerHTML = 'No items found'
				}
				else{
					for (var i = 0; i < results.items.length; i++){
						res += postChange(results.items[i]) +"<br><br>";
					}
					document.getElementById("result").innerHTML = res;
				}
			}
			if(results.status === "error")
				document.getElementById("result").innerHTML = results.error;
		}
	}
	request.open("POST", "/search",true);
	request.setRequestHeader("Content-Type","application/json");
	request.send(JSON.stringify(json));
}

function postChange(i){
	var ans = "";
	ans += i.id + ", Posted by "+i.username+" at "+i.timestamp+"<br>Contents<br>";
	ans += i.content+"<br>";
	ans += "Likes:" + i.property.likes + " Retweets: " + i.retweeted 
	return ans;
}

function userSearch(){
    document.getElementById("result").innerHTML = "";
    document.getElementById("result2").innerHTML = "";
	var it  = document.getElementById("uid").value;
	if (it === ''){
		document.getElementById("result").innerHTML = 'Please enter ID';
	}
	else{
		var request = new XMLHttpRequest();
		request.onreadystatechange = function(){
			if(this.readyState == 4 && this.status == 200||this.readyState == 4 && this.status == 500){
				var results = JSON.parse(request.responseText);
				if(results.status === "OK")
					document.getElementById("result").innerHTML = userChange(it,results.user)+"<br>"
				if(results.status === "error")
					document.getElementById("result").innerHTML = results.error
			}
		}
		request.open("GET", "/user/"+it,true);
		request.send();
	}
}

function userChange(uid,u){
	var ans = "";
	ans += "User: "+uid+"<br>";
	ans += "Email: "+u.email+"<br>";
	ans += "Followers: "+u.followers+" users<br>";
    ans += "Following: "+u.following+" users<br><br>";
    ans += '<button onclick="userFollows(\''+uid+'\')">Get Follows</button><br>';
    ans += '<button onclick="userFollowing(\''+uid+'\')">Get Followers</button><br>';
    ans += '<button onclick="userPosts(\''+uid+'\')">Get Posts</button><br>';
    ans += 'Limit:<input type="number" min="1" max="200" name="limit" id="usnum"><br><br>';
    if (userName != null) {
        ans += '<button onclick="followUser(\''+uid+'\',\'true\')">Follow</button><br>';
        ans += '<button onclick="followUser(\''+uid+'\',\'false\')">Unfollow</button><br>';
    }
	return ans;
}

function userFollows(uid) {
    document.getElementById("result2").innerHTML = "";
    var lim="";
    var l = document.getElementById("usnum").value;
    if (l!=""){
		lim = "?limit="+parseInt(l);
	}
    var request = new XMLHttpRequest();
	request.onreadystatechange = function(){
		if(this.readyState == 4 && this.status == 200||this.readyState == 4 && this.status == 500){
			var results = JSON.parse(request.responseText);
			if(results.status === "OK"){
                var res = "";
                var ulist = results.users;
                if (ulist.length > 0){
                    res = "Followed by: <br>"
                    for (let i = 0; i < ulist.length; i++) {
                        res += ulist[i]+"<br>";
                    }
                }
                else{
                    res = "No followers."
                }
                document.getElementById("result2").innerHTML = res;
			}
			if(results.status === "error")
				document.getElementById("result2").innerHTML = results.error;
		}
    }
    request.open("GET", "/user/"+uid+"/followers"+lim,true);
	request.send();
}
function userFollowing(uid) {
    document.getElementById("result2").innerHTML = "";
    var lim="";
    var l = document.getElementById("usnum").value;
    if (l!=""){
		lim = "?limit="+parseInt(l);
	}
    var request = new XMLHttpRequest();
	request.onreadystatechange = function(){
		if(this.readyState == 4 && this.status == 200||this.readyState == 4 && this.status == 500){
			var results = JSON.parse(request.responseText);
			if(results.status === "OK"){
                var res = "";
                var ulist = results.users;
                if (ulist.length > 0){
                    res = "Following: <br>"
                    for (let i = 0; i < ulist.length; i++) {
                        res += ulist[i]+"<br>";
                    }
                }
                else{
                    res = "Not following anyone."
                }
                document.getElementById("result2").innerHTML = res;
			}
			if(results.status === "error")
				document.getElementById("result2").innerHTML = results.error;
		}
    }
    request.open("GET", "/user/"+uid+"/following"+lim,true);
	request.send();
}

function userPosts(uid) {
    document.getElementById("result2").innerHTML = "";
    var lim="";
    var l = document.getElementById("usnum").value;
    if (l!=""){
		lim = "?limit="+parseInt(l);
	}
    var request = new XMLHttpRequest();
	request.onreadystatechange = function(){
		if(this.readyState == 4 && this.status == 200||this.readyState == 4 && this.status == 500){
			var results = JSON.parse(request.responseText);
			if(results.status === "OK"){
                var res = "";
                var res = "";
                var ilist = results.items;
                if (ilist.length > 0){
                    res = "PostID: <br>"
                    for (let i = 0; i < ilist.length; i++) {
                        res += ilist[i]+"<br>";
                    }
                }
                else{
                    res = "No Posts."
                }
                document.getElementById("result2").innerHTML = res;
			}
			if(results.status === "error")
				document.getElementById("result2").innerHTML = results.error;
		}
    }
    request.open("GET", "/user/"+uid+"/posts"+lim,true);
	request.send();
}

function followUser(uid,bool) {
    document.getElementById("result2").innerHTML = "";
    var json = {};
    json.username = uid;
	if (bool == 'true'){
        json.follow = true;
	}
	else{
		json.follow = false;
	}
	var request = new XMLHttpRequest();
	request.onreadystatechange = function(){
		if(this.readyState == 4 && this.status == 200||this.readyState == 4 && this.status == 500){
			var results = JSON.parse(request.responseText);
			if(results.status === "OK"){
				if (bool == 'true'){
					document.getElementById("result2").innerHTML = 'You followed this user';
				}
				else{
					document.getElementById("result2").innerHTML = 'You unfollowed this user';
				}
			}
			if(results.status === "error")
				document.getElementById("result2").innerHTML = results.error;
		}
    }
	request.open("POST", "/follow",true);
	request.setRequestHeader("Content-Type","application/json");
	request.send(JSON.stringify(json));
}