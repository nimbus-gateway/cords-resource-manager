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
    



## the function from the below line will deal with the Connectors
import base64
import urllib3
import requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@ds_connector.route('/fetch_self_description', methods=["GET"])
def fetch_self_description():
    """Fetch self-description from an external API"""
    try:
        # Define the URL and credentials
        self_description_url = "https://localhost:8090/api/selfDescription/"
        username = "apiUser"
        password = "password"

        # Encode the credentials for Basic Auth
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        # Set up headers
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
        }

        # Disable warnings for self-signed certificates (development only)
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Make the GET request with SSL verification disabled
        response = requests.get(self_description_url, headers=headers, verify=False)

        # Check if the response is successful
        if response.status_code != 200:
            error_message = f"Failed to fetch self-description: {response.reason}"
            logging.error(error_message)
            return jsonify({"status": "failed", "message": error_message}), response.status_code

        # Return the JSON response
        return jsonify(response.json()), 200

    except Exception as e:
        error_message = f"Error fetching self-description: {str(e)}"
        logging.error(error_message)
        return jsonify({"status": "failed", "message": error_message}), 500

@ds_connector.route('/post_offered_resource', methods=["POST"])
def post_offered_resource():
    """Post offered resource to an external API"""
    try:
        # Define the URL and credentials
        offered_resource_url = "https://localhost:8090/api/offeredResource/"
        username = "apiUser"
        password = "password"

        # Encode the credentials for Basic Auth
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        # Get the JSON payload from the request
        data = request.get_json()
        if not data:
            error_message = "No data provided in the request"
            logging.error(error_message)
            return jsonify({"status": "failed", "message": error_message}), 400

        # Extract catalog attribute from the payload
        catalog = data.get("catalog")
        if not catalog:
            error_message = "Catalog attribute is missing in the request payload"
            logging.error(error_message)
            return jsonify({"status": "failed", "message": error_message}), 400

        # Set up headers
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
            "catalog": catalog,  # Add catalog as a header
        }

        payload = data.get("resource_description")

        # Make the POST request with SSL verification disabled
        response = requests.post(offered_resource_url, headers=headers, json=payload, verify=False)

        # Check if the response is successful
        if response.status_code != 200:
            error_message = f"Failed to post offered resource: {response.reason}"
            logging.error(error_message)
            return jsonify({"status": "failed", "message": error_message}), response.status_code

        # Return the JSON response
        return jsonify(response.json()), 200

    except Exception as e:
        error_message = f"Error posting offered resource: {str(e)}"
        logging.error(error_message)
        return jsonify({"status": "failed", "message": error_message}), 500


@ds_connector.route('/update_broker', methods=["POST"])
def update_broker():
    """Update broker by sending a POST request to the proxy"""
    try:
        # Define the URL and credentials
        broker_update_url = "https://localhost:8184/proxy"
        username = "idsUser"
        password = "password"

        # Encode the credentials for Basic Auth
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        # Define the payload
        payload = {
            "multipart": "form",
            "Forward-To": "https://broker-reverseproxy/infrastructure",
            "messageType": "ConnectorUpdateMessage"
        }

        # Set up headers
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
        }

        # Make the POST request with SSL verification disabled
        response = requests.post(broker_update_url, headers=headers, json=payload, verify=False)

        # Check if the response is successful
        if response.status_code != 200:
            error_message = f"Failed to update broker: {response.reason}"
            logging.error(error_message)
            return jsonify({"status": "failed", "message": error_message}), response.status_code

        # Return the JSON response
        
        return jsonify({"status": "success", "message": "Broker updated successfully"}), 200

    except Exception as e:
        error_message = f"Error updating broker: {str(e)}"
        logging.error(error_message)
        return jsonify({"status": "failed", "message": error_message}), 500
    

@ds_connector.route('/resource_description_request', methods=["POST"])
def resource_description_request():
    """Send a resource description request to an external API"""
    try:
        # Define the URL and credentials
        description_request_url = "https://localhost:8184/proxy"
        username = "idsUser"
        password = "password"

        # Encode the credentials for Basic Auth
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        # Get the JSON payload from the request
        data = request.get_json()
        if not data:
            error_message = "No data provided in the request"
            logging.error(error_message)
            return jsonify({"status": "failed", "message": error_message}), 400

        # Extract requestedElement from the payload
        requested_element = data.get("requestedElement")
        if not requested_element:
            error_message = "requestedElement attribute is missing in the request payload"
            logging.error(error_message)
            return jsonify({"status": "failed", "message": error_message}), 400

        # Define the payload to send
        payload = {
            "multipart": "form",
            "Forward-To": "https://ecc-provider:8889/data",
            "messageType": "DescriptionRequestMessage",
            "requestedElement": requested_element
        }

        # Set up headers
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
        }

        # Make the POST request with SSL verification disabled
        response = requests.post(description_request_url, headers=headers, json=payload, verify=False)

        # Check if the response is successful
        if response.status_code != 200:
            error_message = f"Failed to send resource description request: {response.reason}"
            logging.error(error_message)
            return jsonify({"status": "failed", "message": error_message}), response.status_code

        # Return the JSON response
        return jsonify(response.json()), 200

    except Exception as e:
        error_message = f"Error sending resource description request: {str(e)}"
        logging.error(error_message)
        return jsonify({"status": "failed", "message": error_message}), 500
    


@ds_connector.route('/contract_request_message', methods=["POST"])
def contract_request_message():
    """Send a contract request message to an external API"""
    try:
        # Define the URL and credentials
        contract_request_url = "https://localhost:8184/proxy"
        username = "idsUser"
        password = "password"

        # Encode the credentials for Basic Auth
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        # Get the JSON payload from the request
        data = request.get_json()
        if not data:
            error_message = "No data provided in the request"
            logging.error(error_message)
            return jsonify({"status": "failed", "message": error_message}), 400

        # Extract required fields from the payload
        contract_artifact = data.get("contract_artifact")
        contract_id = data.get("contract_id")
        contract_permission = data.get("contract_permission")
        contract_provider = data.get("contract_provider")

        # Validate required fields
        if not all([contract_artifact, contract_id, contract_permission, contract_provider]):
            error_message = "Missing required fields in the request payload"
            logging.error(error_message)
            return jsonify({"status": "failed", "message": error_message}), 400

        # Build the payload
        payload = {
            "multipart": "form",
            "Forward-To": "https://ecc-provider:8889/data",
            "messageType": "ContractRequestMessage",
            "requestedElement": contract_artifact,
            "payload": {
                "@context": {
                    "ids": "https://w3id.org/idsa/core/",
                    "idsc": "https://w3id.org/idsa/code/"
                },
                "@type": "ids:ContractRequest",
                "@id": contract_id,
                "ids:permission": contract_permission if isinstance(contract_permission, list) else [contract_permission],
                "ids:provider": {
                    "@id": contract_provider
                },
                "ids:obligation": [],
                "ids:prohibition": [],
                "ids:consumer": {
                    "@id": "http://w3id.org/engrd/connector/consumer"
                }
            }
        }

        # Set up headers
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
        }

        # Make the POST request with SSL verification disabled
        response = requests.post(contract_request_url, headers=headers, json=payload, verify=False)

        # Check if the response is successful
        if response.status_code != 200:
            error_message = f"Failed to send contract request message: {response.reason}"
            logging.error(error_message)
            return jsonify({"status": "failed", "message": error_message}), response.status_code

        # Return the JSON response
        return jsonify(response.json()), 200

    except Exception as e:
        error_message = f"Error sending contract request message: {str(e)}"
        logging.error(error_message)
        return jsonify({"status": "failed", "message": error_message}), 500
    


@ds_connector.route('/contract_agreement_message', methods=["POST"])
def contract_agreement_message():
    """Send a contract agreement message to an external API"""
    try:
        contract_agreement_url = "https://localhost:8184/proxy"
        username = "idsUser"
        password = "password"

        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        data = request.get_json()
        if not data:
            error_message = "No data provided in the request"
            logging.error(error_message)
            return jsonify({"status": "failed", "message": error_message}), 400


        contract_artifact = data.get("contract_artifact")
        contract_agreement = data.get("contract_agreement")

        if not all([contract_artifact, contract_agreement]):
            error_message = "Missing required fields in the request payload"
            logging.error(error_message)
            return jsonify({"status": "failed", "message": error_message}), 400

        payload = {
            "multipart": "form",
            "Forward-To": "https://ecc-provider:8889/data",
            "messageType": "ContractAgreementMessage",
            "requestedArtifact": contract_artifact,
            "payload": contract_agreement
        }

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "text/plain",
        }
        
        logging.info("Contract agreement payload: %s", payload)

        response = requests.post(contract_agreement_url, headers=headers, json=payload, verify=False)

        if response.status_code != 200:
            error_message = f"Failed to send contract agreement message: {response.reason}"
            logging.error(error_message)
            return jsonify({"status": "failed", "message": error_message}), response.status_code

        # Try to return JSON if possible, otherwise return raw text
        try:
            return jsonify(response.json()), 200
        except ValueError:
            return Response(response.text, status=200, mimetype=response.headers.get('Content-Type', 'text/plain'))

    except Exception as e:
        error_message = f"Error sending contract agreement message: {str(e)}"
        logging.error(error_message)
        return jsonify({"status": "failed", "message": error_message}), 500
    


@ds_connector.route('/artifact_request_message', methods=["POST"])
def artifact_request_message():
    """Send an artifact request message to an external API"""
    try:
        artifact_request_url = "https://localhost:8184/proxy"
        username = "idsUser"
        password = "password"

        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        data = request.get_json()
        if not data:
            error_message = "No data provided in the request"
            logging.error(error_message)
            return jsonify({"status": "failed", "message": error_message}), 400


        contract_artifact = data.get("contract_artifact")
        transfer_contract = data.get("transfer_contract")
        payload = data.get("payload", "")

        if not all([contract_artifact, transfer_contract]):
            error_message = "Missing required fields in the request payload"
            logging.error(error_message)
            return jsonify({"status": "failed", "message": error_message}), 400

        payload = {
            "multipart": "form",
            "Forward-To": "https://ecc-provider:8889/data",
            "messageType": "ArtifactRequestMessage",
            "requestedArtifact": contract_artifact,
            "transferContract": transfer_contract,
            "payload": payload
        }

        logging.info("Artifact request payload: %s", payload)

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
        }

        response = requests.post(artifact_request_url, headers=headers, json=payload, verify=False)

        if response.status_code != 200:
            error_message = f"Failed to send artifact request message: {response.reason}"
            logging.error(error_message)
            return jsonify({"status": "failed", "message": error_message}), response.status_code

        try:
            return jsonify(response.json()), 200
        except ValueError:
            return Response(response.text, status=200, mimetype=response.headers.get('Content-Type', 'text/plain'))

    except Exception as e:
        error_message = f"Error sending artifact request message: {str(e)}"
        logging.error(error_message)
        return jsonify({"status": "failed", "message": error_message}), 500