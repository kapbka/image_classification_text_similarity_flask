from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import requests
import subprocess
import json


app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.IRGDB
users = db["Users"]


def user_exists(username):
    return users.find({"Username": username}).count() != 0


def verify_pw(username, password):
    if not user_exists(username):
        return False

    hashed_pw = users.find({
        "Username": username
    })[0]["Password"]

    return bcrypt.hashpw(password.encode('utf8'), hashed_pw) == hashed_pw


def generate_return_dict(status, msg):
    return {
        "status": status,
        "msg": msg
    }


def verify_creds(username, password):
    if not user_exists(username):
        return generate_return_dict(301, 'Invalid Username'), True

    correct_pw = verify_pw(username, password)
    if not correct_pw:
        return generate_return_dict(302, 'Invalid Password'), True

    return None, False


def count_tokens(username):
    tokens = users.find({
        "Username": username
    })[0]["Tokens"]

    return tokens


class Register(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data['username']
        password = posted_data['password']

        if user_exists(username):
            ret_json = {
                'status': 301,
                'msg': 'Invalid username'
            }
            return jsonify(ret_json)

        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        users.insert_one({
            "Username": username,
            "Password": hashed_pw,
            "Tokens": 4
        })

        ret_json = {
            "status": 200,
            "msg": "You have successfully signed up for the API"
        }

        return jsonify(ret_json)


class Classify(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data['username']
        password = posted_data['password']
        url = posted_data['url']

        ret_json, error = verify_creds(username, password)
        if error:
            return jsonify(ret_json)

        num_tokens = count_tokens(username)
        if num_tokens <= 0:
            return jsonify(generate_return_dict(303, 'Not Enough Tokens'))

        r = requests.get(url)
        ret_json = {}
        with open("temp.jpg", "wb") as f:
            f.write(r.content)
            proc = subprocess.Popen('python classify_image.py --model_dir=. --image_file=./temp.jpg', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            proc.communicate()[0]
            proc.wait()
            with open("text.txt") as g:
                ret_json = json.load(g)

        users.update({
            "Username": username
        }, {
            "$set": {
                "Tokens": num_tokens - 1
            }
        })

        return ret_json


class Refill(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data['username']
        password = posted_data['admin_pw']
        refill_amount = posted_data['refill']

        if not user_exists(username):
            return jsonify(generate_return_dict(301, 'Invalid Username'))

        correct_pw = "abc123"
        if password != correct_pw:
            return jsonify(generate_return_dict(304, 'Invalid Admin Password'))

        current_tokens = count_tokens(username)
        users.update({
            "Username": username
        }, {
            "$set": {
                "Tokens": refill_amount + current_tokens
            }
        })

        return jsonify(generate_return_dict(200, 'Refilled Successfully'))


api.add_resource(Register, '/register')
api.add_resource(Classify, '/classify')
api.add_resource(Refill, '/refill')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
