from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt


app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.BankDB
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


class Register(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data['username']
        password = posted_data['password']

        if user_exists(username):
            return jsonify(generate_return_dict(301, 'Invalid username'))

        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        users.insert_one({
            "Username": username,
            "Password": hashed_pw,
            "Own": 0,
            "Debt": 0
        })

        return jsonify(generate_return_dict(200, 'You have successfully signed up for the API'))


def cash_with_user(username):
    return users.find({
        "Username": username
    })[0]["Own"]


def debt_with_user(username):
    return users.find({
        "Username": username
    })[0]["Debt"]


def update_account(username, balance):
    users.update({
        "Username": username
    }, {
        "$set": {
            "Own": balance
        }
    })


def update_debt(username, balance):
    users.update({
        "Username": username
    }, {
        "$set": {
            "Debt": balance
        }
    })


class Add(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data['username']
        password = posted_data['password']
        amount = posted_data['amount']

        ret_json, err = verify_creds(username, password)
        if err:
            return jsonify(ret_json)

        if amount <= 0:
            return jsonify(generate_return_dict(304, 'The money amount entered must be >= 0'))

        cash = cash_with_user(username)

        # 1$ commission for a transaction
        amount -= 1
        bank_cash = cash_with_user("BANK")
        update_account("BANK", bank_cash + 1)

        update_account(username, cash+amount)

        return jsonify(generate_return_dict(200, "Amount added successfully to the account"))


class Transfer(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data['username']
        password = posted_data['password']
        to = posted_data['to']
        amount = posted_data['amount']

        ret_json, err = verify_creds(username, password)
        if err:
            return jsonify(ret_json)

        cash = cash_with_user(username)
        if cash <= 0:
            return jsonify(generate_return_dict(304, 'You are out of money, please add or take a loan'))

        if not user_exists(to):
            return jsonify(generate_return_dict(301, 'Receiver username is invalid'))

        if cash - amount < 0:
            return jsonify(generate_return_dict(306, 'Not enough money for a transfer'))

        cash_from = cash
        cash_to = cash_with_user(to)
        bank_cash = cash_with_user('BANK')

        # 1$ commission for a transaction
        update_account("BANK", bank_cash + 1)
        update_account(to, cash_to + amount - 1)
        update_account(username, cash_from - amount)

        return jsonify(generate_return_dict(200, "Amount added successfully to the account"))


class Balance(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data['username']
        password = posted_data['password']

        ret_json, err = verify_creds(username, password)
        if err:
            return jsonify(ret_json)

        ret_json = users.find({
            "Username": username
        }, {
            "Password": 0,  # exclide these 2 fields from the result
            "_id": 0
        })[0]

        return jsonify(ret_json)


class TakeLoan(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data['username']
        password = posted_data['password']
        amount = posted_data['amount']

        ret_json, err = verify_creds(username, password)
        if err:
            return jsonify(ret_json)

        cash = cash_with_user(username)
        if cash < amount:
            return jsonify(generate_return_dict(303, "Not enough cash in your account"))

        debt = debt_with_user(username)
        update_account(username, cash + amount)
        update_debt(username, debt + amount)

        return jsonify(generate_return_dict(200, "Loan added to your account"))


class PayLoan(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data['username']
        password = posted_data['password']
        amount = posted_data['amount']

        ret_json, err = verify_creds(username, password)
        if err:
            return jsonify(ret_json)

        cash = cash_with_user(username)
        debt = debt_with_user(username)

        update_account(username, cash - amount)
        update_debt(username, debt - amount)

        return jsonify(generate_return_dict(200, "You have successfully paid your loan"))


api.add_resource(Register, '/register')
api.add_resource(Add, '/add')
api.add_resource(Transfer, '/transfer')
api.add_resource(Balance, '/balance')
api.add_resource(TakeLoan, '/takeloan')
api.add_resource(PayLoan, '/payloan')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
