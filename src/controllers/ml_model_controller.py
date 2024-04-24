from flask import request, Response, json, Blueprint, jsonify, abort
from src.models.ml_model import MlModel, MLModelSchema, ErrorReponseSchema, MLModelSchemaResponse, MLSemanticSchema
from apifairy import body, other_responses, response
from cords_semantics.semantics import MlSemanticManager
from cords_semantics.mlflow import convert_tags_to_dictionary, extract_mlflow_semantics
import logging
from config import settings
import mlflow


logging.basicConfig(level=logging.DEBUG)  


# user controller blueprint to be registered with api blueprint
ml_models = Blueprint("ml_models", __name__, template_folder='templates')
ml_model_schema = MLModelSchema()
ml_model_response_schema = MLModelSchemaResponse()
error_response_schema = ErrorReponseSchema()
ml_semantic_schema = MLSemanticSchema()
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
        ml_flow_model_path = data.get('ml_flow_model_path')
        
        if not all([name, version, description, ml_flow_model_path]):
            error = {"status": "failed", "message": "Error Occured", "error": "Missing data"}
            return error, 400

        resp = new_model.add_model(name, version, description, ml_flow_model_path)
        if resp:
            return resp, 201
        else:
            error = {"status": "failed", "message": "Error Occured", "error": "Data Base Insert Failed"}
            return error, 400


    except Exception as e:
        error = {"status": "failed", "message": "Error Occured", "error":  str(e)}
        return error, 500


@ml_models.route('/get_model/<string:model_id>', methods = ["GET"])
@response(ml_model_response_schema)
@other_responses({404: 'Entry not found'})
def get_model(model_id):
    """Return a ML Model Entry"""

    model_response = new_model.get_model(model_id)

    if model_response:
        return model_response[0]
    else:
        abort(404)
        



@ml_models.route('/update_model/<string:model_id>', methods=['PUT'])
@body(ml_model_schema)
@response(ml_model_response_schema)
@other_responses({404: 'Entry not found'})
def update_model(kwargs, model_id):
    """Update a ML Model Entry"""
    try:
        data = request.get_json()
        if not data:
            error = {"status": "failed", "message": "Error Occured", "error": "No data provided"}
            return error, 400

        name = data.get('name')
        version = data.get('version')
        description = data.get('description')
        ml_flow_model_path = data.get('ml_flow_model_path')

        
        if not all([name, version, description, ml_flow_model_path]):
            error = {"status": "failed", "message": "Error Occured", "error": "Missing data"}
            return error, 400
        #model_id = kwargs['model_id']
        model_response = new_model.update_model(model_id, name, version, description, ml_flow_model_path)
 
        if model_response:
            return model_response[0]
        else:
            abort(404)
    
    except Exception as e:
        error = {"status": "failed", "message": "Error Occured", "error":  str(e)}
        return error, 500
    

@ml_models.route('/generate_semantics/<string:model_id>', methods = ["GET"])
@response(ml_semantic_schema)
def generate_semantics(model_id):
    """Getting semantic description"""
    try:
        mlflow.set_tracking_uri(settings.MLFLOW_URI)
        semantic_manager = MlSemanticManager('data/cordsml.rdf')
        
        ml_flow_run_id = new_model.get_mlflow_run_id(model_id)
        logging.info("run id retrieved :%s", ml_flow_run_id)
        mflow_tags = extract_mlflow_semantics(ml_flow_run_id)
        logging.info("tags extracted from mlflow: %s", str(mflow_tags))

        mlflow_semantics_dictionary = convert_tags_to_dictionary(mflow_tags)
        logging.info("semantic in a dictionary: ", mlflow_semantics_dictionary)

        semantic_graph = semantic_manager.create_model_semantics(mlflow_semantics_dictionary)
        jsonld_output_string = semantic_graph.serialize(format='json-ld')

        jsonld_output = json.loads(jsonld_output_string)

        response = {"model_id": model_id, "semantics": jsonld_output}
 
        return response
    
    except Exception as e:
        error = {"status": "failed", "message": "Error Occured", "error":  str(e)}
        return error, 500