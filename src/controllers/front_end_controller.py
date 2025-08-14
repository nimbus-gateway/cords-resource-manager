from flask import request, Response, json, Blueprint, jsonify, abort
from apifairy import body, other_responses, response, authenticate
from cords_semantics.semantics import FlSemanticManager
from cords_semantics.mlflow import convert_tags_to_dictionary, extract_mlflow_semantics
from src import basic_auth, token_auth
import mlflow
import logging
from config import settings
from src.models.fl_service import FLService
from src.models.ds_resource_model import DataSpaceResource



# Configure logging with file name, function name, and line number
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s'
)


# user controller blueprint to be registered with api blueprint
front_end= Blueprint("front_end", __name__, template_folder='templates')
fl_service = FLService()
ds_resource_model = DataSpaceResource()

@front_end.route('/add_fl_service', methods = ["POST"])
def add_service():
    """Add a new FL service entry"""
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
        fl_client = data.get('fl_client')
        connector_id = data.get('connector_id')

        # Check for missing required fields
        required_fields = [name, description, fl_session,  
                           fl_aggregation, fl_communication, fl_security, fl_training, connector_id, fl_client]
        
        print("required fields")
        print(required_fields)
        
        if not all(required_fields):
            error = {"status": "failed", "message": "Error Occurred", "error": "Missing required fields"}
            return error, 400

        # Call the service function to add the FL service
        resp = fl_service.add_fl_service(
            name, description, 
            fl_session, fl_aggregation, 
            fl_communication, fl_security, fl_training, fl_client
        )


        # If successful, return the response
        if resp:

            fl_service_id = resp["fl_service_id"]
            # Call the function to create a resource in the connector
            resource_response = ds_resource_model.create_resource(connector_id, fl_service_id, "fl_service")

            if resource_response[0]:
                # If resource creation is successful, return the response
                resp["resource_id"] = resource_response[0]["resource_id"]
                resp["status"] = "success"
                resp["message"] = "FL service and resource created successfully"
                resp["error"] = None
                resp["fl_service_id"] = fl_service_id
                resp["fl_client"] = fl_client
                resp["connector_id"] = connector_id

                return resp, 201
            else:
                # If resource creation fails, return an error response
                error = {"status": "failed", "message": "Error Occurred", "error": "Resource creation failed"}
                logging.error("Resource creation failed %s", str(error))
                return jsonify(error), 404
        else:
            error = {"status": "failed", "message": "Error Occurred", "error": "Database insert failed"}
            return error, 400

    except Exception as e:
        logging.error(str(e))
        error = {"status": "failed", "message": "Error Occurred", "error": str(e)}
        return error, 500
    




@front_end.route('/list_service_summary', methods=["GET"])
def list_services():
    """List all available FL services"""
    try:
        fl_service = FLService()
        services = fl_service.get_service_summary()

        if services:
            return jsonify(services), 200
        else:
            return {"status": "success", "message": "No FL services available"}, 200

    except Exception as e:
        logging.error(str(e))
        error = {"status": "failed", "message": "Error Occurred", "error": str(e)}
        return error, 500
