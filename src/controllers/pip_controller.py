from flask import request, Response, json, Blueprint, jsonify, abort
from apifairy import body, other_responses, response, authenticate
from src import basic_auth, token_auth
import logging
import traceback
from config import settings
from src.models.pip_model import PIPModel

logging.basicConfig(level=logging.DEBUG)  


# policy controller blueprint to be registered with api blueprint
pip_blueprint = Blueprint("pip_model", __name__, template_folder='templates')
pip_model = PIPModel()



@pip_blueprint.route('/access/', methods = ["GET"])
def access():
    """Get the number of access time by the resource"""
    try:
        resource_id = request.args.get('targetUri')
        consumer_uri = request.args.get('consumerUri')


        if not all([resource_id, consumer_uri]):
            error = {"status": "failed", "message": "Error Occured", "error": "Missing data"}
            return error, 400


        count = pip_model.get_access_count(consumer_uri, resource_id)

        return str(count), 200, {'Content-Type': 'text/plain'}
        


    except Exception as e:
        error = {"status": "failed", "message": "Error Occured", "error":  str(e)}
        logging.error(str(e))
        stack_trace = traceback.format_exc()
        logging.error("An exception occurred:\n%s", stack_trace)
        return error, 500
    

@pip_blueprint.route('/purpose/', methods = ["GET"])
def purpose():
    """Get the number of access time by the resource"""
    try:
        resource_id = request.args.get('targetUri')
        consumer_uri = request.args.get('consumerUri')


        if not all([resource_id, consumer_uri]):
            error = {"status": "failed", "message": "Error Occured", "error": "Missing data"}
            return error, 400


        count = "Marketing"

        return str(count), 200, {'Content-Type': 'text/plain'}
        


    except Exception as e:
        error = {"status": "failed", "message": "Error Occured", "error":  str(e)}
        logging.error(str(e))
        stack_trace = traceback.format_exc()
        logging.error("An exception occurred:\n%s", stack_trace)
        return error, 500
    

@pip_blueprint.route('/role/', methods = ["GET"])
def role():
    """Get the number of access time by the resource"""
    try:
        resource_id = request.args.get('targetUri')
        consumer_uri = request.args.get('consumerUri')


        if not all([resource_id, consumer_uri]):
            error = {"status": "failed", "message": "Error Occured", "error": "Missing data"}
            return error, 400


        role = "User"

        return str(role), 200, {'Content-Type': 'text/plain'}
        


    except Exception as e:
        error = {"status": "failed", "message": "Error Occured", "error":  str(e)}
        logging.error(str(e))
        stack_trace = traceback.format_exc()
        logging.error("An exception occurred:\n%s", stack_trace)
        return error, 500



