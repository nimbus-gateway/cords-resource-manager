from flask import request, Response, json, Blueprint, jsonify, abort
from apifairy import body, other_responses, response, authenticate
from src import basic_auth, token_auth
import logging
from config import settings
from src.models.policy_model import PolicyModel, PolicyPayload

logging.basicConfig(level=logging.DEBUG)  


# policy controller blueprint to be registered with api blueprint
policy_blueprint = Blueprint("policy_model", __name__, template_folder='templates')
new_policy = PolicyModel()
# ml_model_schema = MLModelSchema()
# ml_model_response_schema = MLModelSchemaResponse()
# error_response_schema = ErrorReponseSchema()
# ml_semantic_schema = MLSemanticSchema()
# new_model = MlModel()


# @response(ml_model_response_schema, 201)
# @other_responses({400: error_response_schema})
# @body(ml_model_schema)



@policy_blueprint.route('/add_policy', methods = ["POST"])
@authenticate(token_auth)
@body(PolicyPayload)
def add_policy(kwargs):
    """Add a new policy and link it to a resource"""
    print(kwargs)
    try:
        data = request.get_json()
        if not data:
            error = {"status": "failed", "message": "Error Occured", "error": "No data provided"}
            return error, 400

        resource_id = data.get('resource_id')
        policy_type = data.get('policy_type')
        policy_metadata = data.get('policy_metadata')
        
        if not all([resource_id, policy_type, policy_metadata]):
            error = {"status": "failed", "message": "Error Occured", "error": "Missing data"}
            return error, 400

        resp = new_policy.add_policy(resource_id, policy_type, policy_metadata)
        if resp:
            return resp, 201
        else:
            error = {"status": "failed", "message": "Error Occured", "error": "Database Insert Failed"}
            return error, 400


    except Exception as e:
        error = {"status": "failed", "message": "Error Occured", "error":  str(e)}
        return error, 500


@policy_blueprint.route('/get_policies/<string:resource_id>', methods = ["GET"])
# @response(MLModelSchemaResponse)
# @other_responses({404: 'Entry not found'})
@authenticate(token_auth)
def get_policy(resource_id):
    """Return list of policies linked to the resource"""

    policy_response = new_policy.get_policy(resource_id)

    if policy_response:
        print(policy_response)
        return policy_response
    else:
        abort(404)
        