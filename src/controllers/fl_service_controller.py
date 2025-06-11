from flask import request, Response, json, Blueprint, jsonify, abort
from src.models.fl_service import FLService, FLServiceSchema, FLServiceSchemaResponse, MLSemanticSchema
from src.models.error_model import ErrorReponseSchema
from apifairy import body, other_responses, response, authenticate
from cords_semantics.semantics import FlSemanticManager
from cords_semantics.mlflow import convert_tags_to_dictionary, extract_mlflow_semantics
from src import basic_auth, token_auth
import logging
from config import settings



# Configure logging with file name, function name, and line number
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s'
)


# user controller blueprint to be registered with api blueprint
fl_services= Blueprint("fl_services", __name__, template_folder='templates')
fl_service_schema = FLServiceSchema()
fl_service_response_schema = FLServiceSchemaResponse()
error_response_schema = ErrorReponseSchema()
ml_semantic_schema = MLSemanticSchema()
fl_service = FLService()


@fl_services.route('/add', methods = ["POST"])
# @authenticate(token_auth)
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
        fl_aggregation = data.get('fl_aggregation')
        fl_communication = data.get('fl_communication')
        fl_security = data.get('fl_security')
        fl_training = data.get('fl_training')

        # Check for missing required fields
        required_fields = [name, description, fl_session,  
                           fl_aggregation, fl_communication, fl_security, fl_training]
        
        print("required fields")
        print(required_fields)
        
        if not all(required_fields):
            error = {"status": "failed", "message": "Error Occurred", "error": "Missing required fields"}
            return error, 400

        # Call the service function to add the FL service
        resp = fl_service.add_fl_service(
            name, description, 
            fl_session, fl_aggregation, 
            fl_communication, fl_security, fl_training
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


@fl_services.route('/get/<string:fl_service_id>', methods=["GET"])
# @authenticate(token_auth)
@response(fl_service_response_schema, 200)
@other_responses({404: error_response_schema})
def get_service(fl_service_id):
    """Retrieve an FL service entry by its ID"""
    try:
        service = fl_service.get_fl_service(fl_service_id)

        if service:
            return service[0], 200
        else:
            error = {"status": "failed", "message": "FL Service not found", "error": f"Service ID {fl_service_id} not found"}
            return error, 404

    except Exception as e:
        logging.error(str(e))
        error = {"status": "failed", "message": "Error Occurred", "error": str(e)}
        return error, 500
    
@fl_services.route('/list', methods=["GET"])
def list_services():
    """List all available FL services"""
    try:
        services = fl_service.get_all_services()

        if services:
            return jsonify(services), 200
        else:
            return {"status": "success", "message": "No FL services available"}, 200

    except Exception as e:
        logging.error(str(e))
        error = {"status": "failed", "message": "Error Occurred", "error": str(e)}
        return error, 500


@fl_services.route('/update/<string:fl_service_id>', methods=["PUT"])
#@authenticate(token_auth)
@response(fl_service_response_schema, 200)
@other_responses({400: error_response_schema, 404: error_response_schema})
@body(fl_service_schema)
def update_service(fl_service_id, kwargs):
    """Update an existing FL service entry"""
    try:
        data = request.get_json()
        if not data:
            error = {"status": "failed", "message": "Error Occurred", "error": "No data provided"}
            return error, 400

        # Extract updated fields
        name = data.get('name')
        description = data.get('description')
        fl_session = data.get('fl_session')
        fl_aggregation = data.get('fl_aggregation')
        fl_communication = data.get('fl_communication')
        fl_security_privacy = data.get('fl_security_privacy')
        fl_training = data.get('fl_training')

        # Validate required fields
        required_fields = [name, description, fl_session,  
                           fl_aggregation, fl_communication, fl_security_privacy, fl_training]

        if not all(required_fields):
            error = {"status": "failed", "message": "Error Occurred", "error": "Missing required fields"}
            return error, 400

        # Call the service function to update the FL service
        resp = fl_service.update_fl_session(
            fl_service_id, name, description
        )

        # If update was successful, return updated service details
        if resp:
            return resp, 200
        else:
            error = {"status": "failed", "message": "FL Service not found", "error": f"Service ID {fl_service_id} not found"}
            return error, 404

    except Exception as e:
        logging.error(str(e))
        error = {"status": "failed", "message": "Error Occurred", "error": str(e)}
        return error, 500

@fl_services.route('/generate_semantics/<string:fl_service_id>', methods = ["GET"])
# @response(ml_semantic_schema)
# @authenticate(token_auth)
def generate_semantics(fl_service_id):
    """Generate semantic description"""
    try:
        fl_semantic_manager = FlSemanticManager('data/cords_federated_learning.rdf')

        service = fl_service.get_fl_service(fl_service_id)[0]
        

        tags = convert_json_to_cords_format(service)
        logging.info(tags)
        semantics_dictionary = convert_tags_to_dictionary([tags])
        logging.info(semantics_dictionary)
        semantics = fl_semantic_manager.create_fl_semantics(semantics_dictionary)
        logging.info(semantics)
        return semantics, 200


    except Exception as e:
        error = {"status": "failed", "message": "Error Occured", "error":  str(e)}
        logging.error(e)
        return error, 500


@fl_services.route('/update_published_status/<string:fl_service_id>', methods=["POST"])
# @authenticate(token_auth)
@other_responses({400: error_response_schema, 404: error_response_schema})
def update_published_status(fl_service_id):
    """Update the published status of an FL service"""
    try:
        published = True

        # Call the service function to update the published status
        resp = fl_service.update_published_status(fl_service_id, published)

        if resp:
            return {"status": "success", "message": f"Published status updated for service ID {fl_service_id}"}, 200
        else:
            error = {"status": "failed", "message": "FL Service not found", "error": f"Service ID {fl_service_id} not found"}
            return error, 404

    except Exception as e:
        logging.error(str(e))
        error = {"status": "failed", "message": "Error Occurred", "error": str(e)}
        return error, 500


@fl_services.route('/remove/<string:fl_service_id>', methods=["DELETE"])
# @authenticate(token_auth)
@other_responses({404: error_response_schema})
def remove_service(fl_service_id):
    """Remove an FL service entry by its ID"""
    try:
        # Call the service function to remove the FL service
        result = fl_service.remove_fl_service(fl_service_id)

        if result:
            return {"status": "success", "message": f"FL service with ID {fl_service_id} removed successfully."}, 200
        else:
            error = {"status": "failed", "message": "FL Service not found", "error": f"Service ID {fl_service_id} not found"}
            return error, 404

    except Exception as e:
        logging.error(str(e))
        error = {"status": "failed", "message": "Error Occurred", "error": str(e)}
        return error, 500

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



def convert_json_to_cords_format(input_json):
    mapping = {
        "fl_session": "cords.FLSession",
        "fl_aggregation": "cords.FLAggregation",
        "fl_communication": "cords.FLCommunication",
        "fl_security": "cords.FLSecurity",
        "fl_training": "cords.FLTraining"
    }
    
    key_mapping = {
        "session_id": "sessionID",
        "session_start_time": "sessionStartTime",
        "session_end_time": "sessionEndTime",
        "num_min_clients": "numMinClients",
        "num_max_clients": "numMaxClients",
        "participation_ratio": "participationRatio",
        "aggregation_method": "aggregationAlgorithm",
        "aggregation_frequency": "aggregationFrequency",
        "communication_protocol": "communicationProtocol",
        "secure_aggregation_enabled": "secureAggregationEnabled",
        "differential_privacy_enabled": "differentialPrivacyEnabled",
        "encryption_method": "encryptionMethod",
        "training_rounds": "trainingRounds",
        "local_epochs": "localEpochs",
        "loss_function": "lossFunction"
    }
    
    transformed_data = {}
    
    for key, value in input_json.items():
        if key in mapping:  # Handle nested structures
            prefix = mapping[key]
            for sub_key, sub_value in value.items():
                if sub_key in key_mapping:
                    transformed_data[f"{prefix}.{key_mapping[sub_key]}"] = sub_value
        
    return transformed_data


