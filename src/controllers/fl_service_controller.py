from flask import request, Response, json, Blueprint, jsonify, abort
from src.models.fl_service import FLService, FLServiceSchema, FLServiceSchemaResponse, MLSemanticSchema
from src.models.error_model import ErrorReponseSchema
from apifairy import body, other_responses, response, authenticate
from cords_semantics.semantics import MlSemanticManager
from cords_semantics.mlflow import convert_tags_to_dictionary, extract_mlflow_semantics
from src import basic_auth, token_auth
import mlflow
import logging
from config import settings



logging.basicConfig(level=logging.DEBUG)  


# user controller blueprint to be registered with api blueprint
fl_services= Blueprint("fl_services", __name__, template_folder='templates')
fl_service_schema = FLServiceSchema()
fl_service_response_schema = FLServiceSchemaResponse()
error_response_schema = ErrorReponseSchema()
ml_semantic_schema = MLSemanticSchema()
fl_service = FLService()


@fl_services.route('/add', methods = ["POST"])
@authenticate(token_auth)
@response(fl_service_response_schema, 201)
@other_responses({400: error_response_schema})
@body(fl_service_schema)
def add_service(kwargs):
    """Add a new FL service entry"""
    print(kwargs)
    try:
        data = request.get_json()
        if not data:
            error = {"status": "failed", "message": "Error Occurred", "error": "No data provided"}
            return error, 400

        # Extract required fields
        name = data.get('name')
        description = data.get('description')
        fl_session = data.get('fl_session')
        fl_participants = data.get('fl_participants')
        fl_aggregation = data.get('fl_aggregation')
        fl_communication = data.get('fl_communication')
        fl_security_privacy = data.get('fl_security_privacy')
        fl_training = data.get('fl_training')

        # Check for missing required fields
        required_fields = [name, description, fl_session, fl_participants, 
                           fl_aggregation, fl_communication, fl_security_privacy, fl_training]
        
        if not all(required_fields):
            error = {"status": "failed", "message": "Error Occurred", "error": "Missing required fields"}
            return error, 400

        # Call the service function to add the FL service
        resp = fl_service.add_fl_service(
            name, description, 
            fl_session, fl_participants, fl_aggregation, 
            fl_communication, fl_security_privacy, fl_training
        )

        # If successful, return the response
        if resp:
            return resp, 201
        else:
            error = {"status": "failed", "message": "Error Occurred", "error": "Database insert failed"}
            return error, 400

    except Exception as e:
        logging.error(str(e))
        error = {"status": "failed", "message": "Error Occurred", "error": str(e)}
        return error, 500


# @ml_models.route('/get_model/<string:model_id>', methods = ["GET"])
# @response(MLModelSchemaResponse)
# @other_responses({404: 'Entry not found'})
# @authenticate(token_auth)
# def get_model(model_id):
#     """Return a ML Model Entry"""

#     model_response = new_model.get_model(model_id)

#     if model_response:
#         print(model_response)
#         return model_response[0]
#     else:
#         abort(404)
        



# @ml_models.route('/update_model/<string:model_id>', methods=['PUT'])
# @body(ml_model_schema)
# @authenticate(token_auth)
# @response(ml_model_response_schema)
# @other_responses({404: 'Entry not found'})
# def update_model(kwargs, model_id):
#     """Update a ML Model Entry"""
#     try:
#         data = request.get_json()
#         if not data:
#             error = {"status": "failed", "message": "Error Occured", "error": "No data provided"}
#             return error, 400

#         name = data.get('name')
#         version = data.get('version')
#         description = data.get('description')
#         ml_flow_model_path = data.get('ml_flow_model_path')

        
#         if not all([name, version, description, ml_flow_model_path]):
#             error = {"status": "failed", "message": "Error Occured", "error": "Missing data"}
#             return error, 400
#         #model_id = kwargs['model_id']
#         model_response = new_model.update_model(model_id, name, version, description, ml_flow_model_path)
 
#         if model_response:
#             return model_response[0]
#         else:
#             abort(404)
    
#     except Exception as e:
#         logging.error(str(e))
#         error = {"status": "failed", "message": "Error Occured", "error":  str(e)}
#         return error, 500
    

# @ml_models.route('/generate_semantics/<string:model_id>', methods = ["GET"])
# @response(ml_semantic_schema)
# @authenticate(token_auth)
# def generate_semantics(model_id):
#     """Generate semantic description"""
#     try:
#         mlflow.set_tracking_uri(settings.MLFLOW_URI)
#         semantic_manager = MlSemanticManager('data/cordsml.rdf')
        
#         ml_flow_run_id = new_model.get_mlflow_run_id(model_id)
#         logging.info("run id retrieved :%s", ml_flow_run_id)
#         mflow_tags = extract_mlflow_semantics(ml_flow_run_id)
#         logging.info("tags extracted from mlflow: %s", str(mflow_tags))

#         mlflow_semantics_dictionary = convert_tags_to_dictionary(mflow_tags)
#         logging.info("semantic in a dictionary: %s ", str(mlflow_semantics_dictionary))

#         semantic_graph = semantic_manager.create_model_semantics(mlflow_semantics_dictionary)
#         jsonld_output = semantic_manager.convert_to_json_ld()

#         # jsonld_output = json.loads(jsonld_output_string)
#         print(jsonld_output)
#         resp = {"model_id": model_id, "semantics": jsonld_output}
 
#         return resp
    
#     except Exception as e:
#         error = {"status": "failed", "message": "Error Occured", "error":  str(e)}
#         logging.error(e)
#         return error, 500