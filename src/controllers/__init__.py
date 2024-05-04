from flask import request, Response, json, Blueprint, jsonify, abort
from apifairy import body, other_responses, response, authenticate
import logging
from config import settings
from werkzeug.exceptions import Forbidden, Unauthorized
from src import basic_auth, token_auth
from src.models.user_model import User, NewUserSchema, UserSchema

@basic_auth.verify_password
def verify_password(email, password):
    user = User()
    user_data = user.get_user(email)
    if user_data is None:
        return None

    if user.is_password_correct(email, password):
        return user


@basic_auth.error_handler
def basic_auth_error(status=401):
    error = (Forbidden if status == 403 else Unauthorized)()
    return {
        'code': error.code,
        'message': error.name,
        'description': error.description,
    }, error.code, {'WWW-Authenticate': 'Form'}



@token_auth.verify_token
def verify_token(auth_token):
    user = User()
    return user.verify_auth_token(auth_token)


@token_auth.error_handler
def token_auth_error(status=401):
    error = (Forbidden if status == 403 else Unauthorized)()
    return {
        'code': error.code,
        'message': error.name,
        'description': error.description,
    }, error.code