from flask import request, Response, json, Blueprint, jsonify, abort
from apifairy import body, other_responses, response, authenticate
import logging
from config import settings
from werkzeug.exceptions import Forbidden, Unauthorized
from src import basic_auth, token_auth
from src.models.user_model import User, NewUserSchema, UserSchema

logging.basicConfig(level=logging.DEBUG)  

# user controller blueprint to be registered with api blueprint
users_blueprint = Blueprint("users", __name__, template_folder='templates')




@users_blueprint.route('/register', methods=['POST'])
@body(NewUserSchema)
# @response(UserSchema, 201)
def register(kwargs):
    """Create a new user"""
    print(kwargs)

    try:
        data = request.get_json()
        if not data:
            error = {"status": "failed", "message": "Error Occured", "error": "No data provided"}
            return error, 400

        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        role = data.get('role')

        new_user = User()
        print(new_user)
        resp = new_user.add_user(email, password, first_name, last_name, role)
        if resp:
            return resp, 201
        else:
            error = {"status": "failed", "message": "Error Occured", "error": "Data Base Insert Failed"}
            return error, 400


    except Exception as e:
        error = {"status": "failed", "message": "Error Occured", "error":  str(e)}
        return error, 500

    


@users_blueprint.route('/get-auth-token', methods=['POST'])
@authenticate(basic_auth)
# @response(token_schema)
# @other_responses({401: 'Invalid username or password'})
def get_auth_token():
    """Get authentication token"""
    user = basic_auth.current_user()
    token = user.generate_auth_token()

    return dict(token=token)