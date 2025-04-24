from flask import request, Response, json, Blueprint, jsonify, abort
from src.models.ds_resource_model import DataSpaceResource, DataSpaceResourceSchema, DataSpaceResourceSchemaResponse, DataSpaceResourceDescriptionSchema, ArtifactDownloadResponse
from src.models.error_model import ErrorReponseSchema
from apifairy import body, other_responses, response, authenticate
import logging
from config import settings
from src import basic_auth, token_auth
import websockets
import os
import asyncio
import threading

logging.basicConfig(level=logging.DEBUG)  

# user controller blueprint to be registered with api blueprint
ds_resource = Blueprint("dataspace_resource", __name__, template_folder='templates')
ds_resource_model = DataSpaceResource()



@ds_resource.route('/create_resource', methods = ["POST"])
#@authenticate(token_auth)
@response(DataSpaceResourceSchemaResponse)
@body(DataSpaceResourceSchema)
def create_resource(kwargs):
    """Create a resource to be shared in IDS"""
    logging.debug("Argument Recieved at /create_resource %s", str())
    try:
        data = request.get_json()
        if not data:
            error = {"status": "failed", "message": "Error Occured", "error": "No data provided"}
            return error, 400

        # Extract data using kwargs-like unpacking
        connector_id = data.get('connector_id')
        asset_id = data.get('asset_id')
        _type = data.get('type')
        
        resp = ds_resource_model.create_resource(connector_id, asset_id, _type)
        
        if resp[0]:
            return resp[0], 201
        else:
            if resp[1] == 409:
                
                error = {"status": "failed", "message": "Error Occured", "error": "Id already exists"}
                logging.error("Error Occured %s", error)
                return error, 409
                #error, 409
            else:
                error = {"status": "failed", "message": "Error Occured", "error": "Data base insert failed"}
                logging.error("Error Occured %s", error)
                return error, 500
            
    except Exception as e:
        error = {"status": "failed", "message": "Error Occured", "error":  str(e)}
        logging.error("Error Occured %s", error)
        return error, 500
    
@ds_resource.route('/get_resource/<resource_id>', methods=["GET"])
#@authenticate(token_auth)
@response(DataSpaceResourceSchemaResponse)
def get_resource(resource_id):
    """Retrieve a resource by its unique hash identifier (resource_id)"""
    logging.debug("Fetching resource with ID %s", resource_id)
    try:
        resource = ds_resource_model.get_resource(resource_id)

        print(resource)
        if resource:
            return resource, 200
        else:
            error = {"status": "failed", "message": "Resource not found", "error": "No resource matches the provided ID"}
            logging.error("Resource not found %s", error)
            return jsonify(error), 404

    except Exception as e:
        error = {"status": "failed", "message": "Error occurred", "error": str(e)}
        logging.error("Error occurred %s", error)
        return jsonify(error), 500
    
    
@ds_resource.route('/create_resource_description/<resource_id>', methods=["POST"])
#@authenticate(token_auth)
@response(DataSpaceResourceDescriptionSchema)
def create_resource_description(resource_id):
    """Create a resource description using IDS information model"""
    logging.debug("Fetching resource with ID %s", resource_id)
        
    try:
        data = request.get_json()
        if not data:
            error = {"status": "failed", "message": "Error Occured", "error": "No data provided"}
            return error, 400

        # Extract data using kwargs-like unpacking
        title = data.get('title')
        description = data.get('description')
        keywords = data.get('keywords')

        if not all([title, description, keywords]):
            error = {"status": "failed", "message": "Error Occured", "error": "Missing data"}
            logging.error("Resource descriptopn creation failed %s", str(error))
            return error, 400

        resource_description = ds_resource_model.create_resource_description(resource_id, title, description, keywords)
        logging.debug("Resource description for the resource id %s", str(resource_description))

        if resource_description[0]:
            return resource_description[0], 200
        else:
            error = {"status": "failed", "message": "Error at true connector. See the server log", "error": "Issue during description creation"}
            logging.error("Resource descriptopn creation failed %s", str(error))
            return jsonify(error), 404
        
    except Exception as e:
        error = {"status": "failed", "message": "Error occurred", "error": str(e)}
        logging.error("Error occurred %s", error)
        return jsonify(error), 500


@ds_resource.route('/download_resource/<resource_id>', methods=["POST"])
@response(ArtifactDownloadResponse)
@authenticate(token_auth)
def download_resource(resource_id):
    """Start sending the artifact/resource over a web socket to the consumer"""
    # Start the WebSocket server in a new thread to not block the Flask server

    data = request.get_json()
    if not data:
        error = {"status": "failed", "message": "Error Occured", "error": "No data provided"}
        return error, 400

    # Extract data using kwargs-like unpacking
    consumer_ip = data.get('consumer_ip')
    consumer_port = data.get('consumer_port')
   
    status = ds_resource_model.download_resource(resource_id, consumer_ip, consumer_port)
    resp = {"artifact_id": resource_id, "transfer_status": str(status), "message": "WebSocket server started for file download"}
    logging.debug(resp)
    return resp


@ds_resource.route('/initiate_download', methods=["POST"])
@response(ArtifactDownloadResponse)
def initiate_download():
    """Endpoint for IDSA Data App to init downloading"""
    # Start the WebSocket server in a new thread to not block the Flask server

    data = request.get_json()
    if not data:
        error = {"status": "failed", "message": "Error Occured", "error": "No data provided"}
        return error, 400

    # Extract data using kwargs-like unpacking
    artifact_id = data.get('artifact_id')
    consumer_ip = data.get('consumer_ip')
    consumer_port = data.get('consumer_port')

    try:
        resource_id = artifact_id.split('/')[-1]

    except Exception as e:
        error = {"status": "failed", "message": "Invalid Artifact ID", "error": str(e)}
        logging.error("Error occurred %s", error)
        return jsonify(error), 500
   
    status = ds_resource_model.download_resource(resource_id, consumer_ip, consumer_port)
    resp = {"artifact_id": resource_id, "transfer_status": str(status), "message": "WebSocket server started for file download"}
    logging.debug(resp)
    return resp

