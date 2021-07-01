""""
Registration of a user with 0 tokens
Each user gets 10 tokens
Store a sentence on our database for one token
Retrieve his stored sentence on our database for 1 token

"""
from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
from bcrypt import hashpw, gensalt


app = Flask(__name__)
api = Api(app)

client = MongoClient('mongodb://db:27017')  ## default port 27017
db = client.SentencesDatabase
users = db['Users']


class Register(Resource):
    def post(self):
        # 1. get posted data by the user
        posted_data = request.get_json()

        # 2. Access posted data
        username = posted_data['username']
        password = posted_data['password']

        # 3. generate hashed password = hash(password + salt)
        hashed_pw = hashpw(password.encode('utf8'), gensalt())

        # 4. write username and hashed_pw to our DB
        users.insert_one({
            'Username': username,
            'Password': hashed_pw,
            'Sentence': '',
            'Tokens': 6
        })

        # 5. return the result to the user
        ret_json = {
            'status': 200,
            'msg': 'You successfully signed up for the API'
        }

        return jsonify(ret_json)


def verify_pw(username, password):
    hashed_pw = users.find({
        'Username': username
    })[0]['Password']

    return hashed_pw(password.encode('utf8'), hashed_pw) == hashed_pw


def count_tokens(username):
    tokens =users.find({
        'Username': username
    })[0]['Tokens']

    return tokens


class Store(Resource):
    def post(self):
        # 1. get posted data by the user
        posted_data = request.get_json()

        # 2. read the data
        username = posted_data['username']
        password = posted_data['password']
        sentence = posted_data['sentence']

        # 3. verify the username pw match
        correct_pw = verify_pw(username, password)

        if not correct_pw:
            ret_json = {
                'status': 302
            }
            return jsonify(ret_json)

        # 4. verify user has enough tokens
        num_tokens = count_tokens(username)

        if num_tokens <= 0:
            ret_json = {
                'status': 301
            }
            return jsonify(ret_json)

        # 5. store the sentence, take one token away and return 200 OK
        users.update({
            'Username': username
            }, {
                '$set': {
                    "Sentence": sentence,
                    "Tokens": num_tokens - 1
                }
            }
        )

        ret_json = {
            'status': 200,
            'msg': 'Sentence saved successfully'
        }
        return jsonify(ret_json)


class Get(Resource):
    def post(self):
        # 1. get posted data by the user
        posted_data = request.get_json()

        # 2. read the data
        username = posted_data['username']
        password = posted_data['password']

        # 3. verify the username pw match
        correct_pw = verify_pw(username, password)

        if not correct_pw:
            ret_json = {
                'status': 302
            }
            return jsonify(ret_json)

        # 4. verify user has enough tokens
        num_tokens = count_tokens(username)

        if num_tokens <= 0:
            ret_json = {
                'status': 301
            }
            return jsonify(ret_json)

        # 5. make the user pay
        users.update({
            'Username': username
            }, {
                '$set': {
                    "Tokens": num_tokens - 1
                }
            }
        )

        # return the sentence to the user
        sentence = users.find({
            'Username': username
        })[0]['Sentence']

        ret_json = {
            'status': 200,
            'sentence': sentence
        }

        return ret_json


api.add_resource(Register, '/register')
api.add_resource(Store, '/store')
api.add_resource(Get, '/get')


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000)
