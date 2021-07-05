from flask import Flask, jsonify, request
from flask_restful import Api, Resource

from pymongo import MongoClient


app = Flask(__name__)
api = Api(app)

client = MongoClient('mongodb://db:27017')  ## default port 27017
db = client.ANewDB
user_num = db['user_num']
user_num.insert_one({
    'num_of_users': 0
})


class Visit(Resource):
    def get(self):
        prev_num = user_num.find({})[0]['num_of_users']
        new_num = prev_num + 1
        user_num.update({}, {"$set":{"num_of_users":new_num}})
        return str("Hello user " + str(new_num))


class Operation:
    def __init__(self, name):
        self.name = name

    def check_posted_data(self, posted_data):
        if self.name in ['add', 'subtract', 'multiply']:
            if 'x' not in posted_data or 'y' not in posted_data:
                return 301  # missing parameter
            else:
                return 200
        elif self.name == 'divide':
            if 'x' not in posted_data or 'y' not in posted_data:
                return 301  # missing parameter
            elif posted_data['y'] == 0:
                return 302  # 0 division
            else:
                return 200

    def make_operation(self):
        # if I am here then the Resource was requested using the method POST
        # 1. get posted data
        posted_data = request.get_json()

        # 1a verify validity of posted data
        status_code = self.check_posted_data(posted_data)
        if status_code != 200:
            ret_json = {
                'Message': 'An error occurred',
                'Status Code': status_code
            }
            return jsonify(ret_json)

        x = posted_data['x']
        y = posted_data['y']
        x = int(x)
        y = int(y)

        # 2. make an operation over the posted data
        if self.name == 'add':
            ret = x + y
        elif self.name == 'subtract':
            ret = x - y
        elif self.name == 'multiply':
            ret = x * y
        elif self.name == 'divide':
            ret = x / y
        else:
            raise ValueError('Unknown operation!')

        ret_map = {
            'Res': ret,
            'Status Code': 200
        }
        return jsonify(ret_map)


class Add(Resource):
    def post(self):
        return Operation('add').make_operation()


class Subtract(Resource):
    def post(self):
        return Operation('subtract').make_operation()


class Multiply(Resource):
    def post(self):
        return Operation('multiply').make_operation()


class Divide(Resource):
    def post(self):
        return Operation('divide').make_operation()


api.add_resource(Add, '/add')
api.add_resource(Subtract, '/subtract')
api.add_resource(Multiply, '/multiply')
api.add_resource(Divide, '/divide')
api.add_resource(Visit, '/hello')


@app.route('/')
def hello_world():
    return "Hello World!"


@app.route('/hithere')
def hi_there():
    return "Hi there"


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
