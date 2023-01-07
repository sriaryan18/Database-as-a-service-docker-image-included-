from flask import Flask,jsonify,request
from flask_restful import Api,Resource
from pymongo import MongoClient
from cryptography.fernet import Fernet


app=Flask(__name__)
api=Api(app)

client=MongoClient('mongodb://db_as_a_service-db-1')
client.drop_database('newColl')
coll=client['newColl']
db=coll['data']

key = Fernet.generate_key()
 
 
fernet = Fernet(key)

def check_username_available(userName):
	c=db.count_documents({"username":userName})
	if(c==0): 
		return True
	return False
	
def validateCredential(data):
	if(check_username_available(data['username'])==False):

		password=db.find({"username":data['username']})
		# p1=decrypt_password(doc[0]['password'])
		# p2=decrypt_password(data['password'])
		# return p1==p2
		# password=decrypt_password(password)
		# print(password[0]['password'])
		if(password[0]['password']==data['password']):
			return True

	return False

def get_remaining_tokens(uName,password):
	return db.find({"username":uName})[0]['tokens']

def encrypt_password(password):
	return fernet.encrypt(password.encode())

def decrypt_password(password):
	print(password)
	return fernet.decrypt(password).decode()


class Register(Resource):

	def __init__(self):
		pass

	def post(self):
		data=request.get_json()
		uName=data['username']
		password=data['password']
		# password=encrypt_password(password)
		if(check_username_available(uName)==False):
			retJson={
				"Code":301,
				"Message":"UserName already exist {}".format(password)
			}
			return jsonify(retJson)
		data_dict={"username":uName,
		"password":password,
		"tokens":10,
		"sentences":""}
		db.insert_one(data_dict)
		retJson={"Code":300,
		"Message":"Hey {} your registration is successful".format(uName)}
		return jsonify(retJson)


class Store(Resource):

	def post(self):
		data=request.get_json()
		uName=data['username']
		password=data['password']
		sentence=data['sentence']
		# password=encrypt_password(password)
		check={'username':uName,"password":password}
		print(password)
		if(validateCredential(check)==0):
			retJson={
			"Code": 302,
			"Message":"Unmatched username and password"
			}
			return jsonify(retJson)
		rem_token=get_remaining_tokens(uName,password)
		if(rem_token<=0):
			retJson={"Code":303,
			"Message":"Out of token"}
			return jsonify(retJson)
		rem_token-=1
		db.update_one({"username":uName},{"$set":{"sentences":sentence}},upsert=True)
		db.update_one({"username":uName},{"$set":{'tokens':rem_token}})
		retJson={"Code":300,
		"Message":"OK, number of tokens remaining is {}".format(rem_token)}
		return jsonify(retJson)


class Read(Resource):
	def get(self):
		data=request.get_json()
		uName=data['username']
		password=data['password']
		check={'username':uName,"password":password}
		if(validateCredential(check)==0):
			retJson={
			"Code": 302,
			"Message":"Unmatched username and password"
			}
			return jsonify(retJson)
		rem_token=get_remaining_tokens(uName,password)
		if(rem_token<=0):
			retJson={"Code":303,
			"Message":"Out of token"}
			return jsonify(retJson)
		rem_token-=1
		sentence=db.find({"username":uName})[0]['sentences']
		db.update_one({"username":uName},{"$set":{'tokens':rem_token}})
		retJson={"Code":300,
		"Message":"OK",
		"sentence":sentence}
		return jsonify(retJson)



api.add_resource(Register,'/register')
api.add_resource(Store,'/store')
api.add_resource(Read,'/read')
@app.route('/')
def hello():
	return "Hey"



if __name__ == '__main__':
	app.run(debug=True,host='0.0.0.0')