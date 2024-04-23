from flask import request, Response, json, Blueprint, jsonify, abort
from src.models.ml_model import MlModel, MLModelSchema, ErrorReponseSchema, MLModelSchemaResponse
from apifairy import body, other_responses, response
# from src import bcrypt, db
# from datetime import datetime
# import jwt
# import os

# user controller blueprint to be registered with api blueprint
ml_models = Blueprint("ml_models", __name__, template_folder='templates')
ml_model_schema = MLModelSchema()
ml_model_response_schema = MLModelSchemaResponse()
error_response_schema = ErrorReponseSchema()
new_model = MlModel()


@ml_models.route('/add_model', methods = ["POST"])
@response(ml_model_response_schema, 201)
@other_responses({400: error_response_schema})
@body(ml_model_schema)
def add_model(kwargs):
    """Add a new ml model entry"""
    print(kwargs)
    try:
        data = request.get_json()
        if not data:
            error = {"status": "failed", "message": "Error Occured", "error": "No data provided"}
            return error, 400

        name = data.get('name')
        version = data.get('version')
        description = data.get('description')
        semantics = data.get('semantics')
        
        if not all([name, version, description, semantics]):
            error = {"status": "failed", "message": "Error Occured", "error": "Missing data"}
            return error, 400

        model_id = new_model.add_model(name, version, description, semantics)
        resp = kwargs
        resp['model_id'] = str(model_id)


        return resp, 201
    


    except Exception as e:
        error = {"status": "failed", "message": "Error Occured", "error":  str(e)}
        return error, 500


@ml_models.route('/get_model/<string:model_id>', methods = ["GET"])
@response(ml_model_response_schema)
@other_responses({404: 'Entry not found'})
def get_model(model_id):
    """Return a ML Model Entry"""

    model_response = new_model.get_model(model_id)

    if model_response == "Model not found.":
        abort(404)
    else:
        model_response['model_id'] = model_id
        return model_response
