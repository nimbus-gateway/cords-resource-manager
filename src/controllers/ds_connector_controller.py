from flask import request, Response, json, Blueprint, jsonify, abort
from src.models.ds_connector_model import DataSpaceConnector, DataSpaceConnectorSchema, DataSpaceConnectorSchemaResponse, ConnectorGetSchema
from src.models.error_model import ErrorReponseSchema
from apifairy import body, other_responses, response, authenticate
from src.connectors.true_connector import TrueConnector
import logging
from config import settings
from src import basic_auth, token_auth
from src.models.ds_resource_model import DataSpaceResource, ResourceRegistrationPayloadSchema

logging.basicConfig(level=logging.DEBUG)  

# user controller blueprint to be registered with api blueprint
ds_connector = Blueprint("dataspace_connector", __name__, template_folder='templates')
ds_connector_model = DataSpaceConnector()
ds_resource_model = DataSpaceResource()


@ds_connector.route('/add_connector', methods = ["POST"])
@response(DataSpaceConnectorSchemaResponse)
@other_responses({409: (ErrorReponseSchema, 'Id already exists')})
@authenticate(token_auth)
@body(DataSpaceConnectorSchema)
def add_connector(kwargs):
    """Add a new data space connector instance"""
    logging.debug("Argument Recieved at /add_connector %s", str(kwargs))
    try:
        data = request.get_json()
        if not data:
            error = {"status": "failed", "message": "Error Occured", "error": "No data provided"}
            return error, 400

        # Extract data using kwargs-like unpacking
        _id = data.get('id')
        name = data.get('name')
        _type = data.get('type')
        description = data.get('description')
        public_key = data.get('public_key')
        access_url = data.get('access_url')
        reverse_proxy_url = data.get('reverse_proxy_url')
        
        resp = ds_connector_model.add_connector(_id, name, _type, description, public_key, access_url, reverse_proxy_url)
        
        print(resp)
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


@ds_connector.route('/get_connector', methods = ["GET"])
@response(DataSpaceConnectorSchemaResponse)
@body(ConnectorGetSchema)
@authenticate(token_auth)
@other_responses({404: 'Entry not found'})
def get_connector(kwargs):
    """Get connector information"""
    data = request.get_json()
    _id = data['id']
    logging.info("Getting the connector %s", _id)
    resp = ds_connector_model.get_connector(_id)

    print(resp)
    if resp:
        return resp
    else:
        error = {"status": "failed", "message": "Error Occured", "error": "Connector not found"}
        logging.error("Error Occured %s", error)
        return error, 404
        #error, 409
        
        

@ds_connector.route('/register_resource/<resource_id>', methods=["POST"])
@authenticate(token_auth)
@body(ResourceRegistrationPayloadSchema)
def create_resource_description(kwargs, resource_id):
    """Register a resource using IDS information model"""
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
        catalog_id = data.get('catalog_id')

        if not all([title, description, keywords]):
            error = {"status": "failed", "message": "Error Occured", "error": "Missing data"}
            logging.error("Resource descriptopn creation failed %s", str(error))
            return error, 400

        resource_description = ds_resource_model.create_resource_description(resource_id, title, description, keywords)

        if resource_description:
            description = resource_description[0]
            logging.debug("Resource description for the resource id %s", str(description))

            if description['connector'] == 'trueconnector':
        
                true_connector = TrueConnector()
                resp = true_connector.register_resource(description['resource_description'], catalog_id)

                if resp:
                    return resp, 200
            

        error = {"status": "failed", "message": "Resource not found", "error": "Issue during description creation"}
        logging.error("Resource descriptopn creation failed %s", str(error))
        return jsonify(error), 404
        
    except Exception as e:
        error = {"status": "failed", "message": "Error occurred", "error": str(e)}
        logging.error("Error occurred %s", error)
        return jsonify(error), 500