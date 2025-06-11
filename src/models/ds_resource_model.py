
from tinydb import TinyDB, Query, table
from tinydb.table import Document
from src import ma
import re
import hashlib
import json
from datetime import datetime
from marshmallow import Schema, fields, validate
from src.connectors.true_connector import TrueConnector
from config import settings
import logging
import websockets
import os
import asyncio
import threading
import zipfile

from src.models.ml_model import MlModel
from src.models.fl_service import FLService

model = MlModel()
fl_service = FLService()


class DataSpaceResourceSchemaResponse(ma.Schema):
    """Schema a Data Space Connector."""
    connector_id = fields.String(
        required=True, 
        validate=validate.Length(min=1), 
        description="Identifier for the connector under which the resource is added.",
        error_messages={"required": "Connector ID is required."}
    )
    asset_id = fields.String(
        required=True, 
        validate=validate.Length(min=1),
        description="Identifier for the data asset that needed to be shared as a resource. For eg: ML Model ID.",
        error_messages={"required": "Asset ID is required."}
    )
    type = fields.String(
        missing='model', 
        description="Type of the resource, default is 'model'.",
        validate=validate.Length(min=1)
    )
    resource_id = fields.String(
        required=True,
        description="Unique identification for the resource genearted at the API.",
        validate=validate.Length(min=1)
    )
    timestamp = fields.String(
        required=True,
        description="Time stamp when the connector is added.",
    )


class DataSpaceResourceSchema(ma.Schema):
    """Schema a Data Space Connector."""
    connector_id = fields.String(
        required=True, 
        validate=validate.Length(min=1), 
        description="Identifier for the connector under which the resource is added.",
        error_messages={"required": "Connector ID is required."}
    )
    asset_id = fields.String(
        required=True, 
        validate=validate.Length(min=1),
        description="Identifier for the data asset that needed to be shared as a resource. For eg: ML Model ID.",
        error_messages={"required": "Asset ID is required."}
    )
    type = fields.String(
        missing='model', 
        description="Type of the resource, default is 'model'.",
        validate=validate.Length(min=1)
    )


class DataSpaceResourceDescriptionSchema(ma.Schema):
    """Schema a Data Space Connector."""
    resource_id = fields.String(
        required=True, 
        validate=validate.Length(min=1), 
        description="Unique identification for the resource",
        error_messages={"required": "Resource is required."}
    )
    connector = fields.String(
        required=True, 
        validate=validate.Length(min=1),
        description="IDSA Connector name that the resource description is compatible with",
        error_messages={"required": "Connector name is required."}
    )
    resource_description = fields.Dict(
        required=True, 
        description="IDS Resource Description",
        validate=validate.Length(min=1)
    )


class ResourceRegistrationPayloadSchema(ma.Schema):
    """Schema of the payload for registering a data resource."""
    title = fields.String(
        required=True, 
        validate=validate.Length(min=1), 
        description="Title for the data resource",
        error_messages={"required": "Resource is required."}
    )
    description = fields.String(
        required=True, 
        validate=validate.Length(min=1),
        description="Description of the data resource",
        error_messages={"required": "Connector name is required."}
    )
    keywords = fields.List(
        cls_or_instance = fields.Str(),
        required=True, 
        description="Keywords for describing the data resource",
        validate=validate.Length(min=1)
    )
    catalog_id = fields.String(
        required=True, 
        validate=validate.Length(min=1),
        description="ID of the resource catalog",
        error_messages={"required": "Catalog id is required."}
    )

class ArtifactDownloadResponse(ma.Schema):
    """Schema a Data Space Connector."""
    artifact_id = fields.String(
        required=True, 
        description="Identification of the artifact."
    )
    transfer_status = fields.String(
        required=True, 
        description="Status of the artifact transfer process"
    )
    message = fields.String(
        required=True, 
        description="Additonal info on artifact download process."
    )

# Helper function to zip artifiacts
def zip_folder(folder_path, output_path):
    # Create a ZipFile object in write mode
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through the directory structure
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                # Create the full path to the file
                file_path = os.path.join(root, file)
                # Write the file to the zip file, preserving its folder structure
                zipf.write(file_path, os.path.relpath(file_path, os.path.dirname(folder_path)))


# Helper function to run asyncio coroutines in the background
def start_async_task(loop, coro):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(coro)
    

async def send_file(websocket, filename, save_as, chunk_size=512*512):  # 1MB chunks
    with open(filename, 'rb') as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            # Send each chunk as a separate WebSocket message
            data_to_send = {"filename": save_as, "content": list(chunk)}
            await websocket.send(json.dumps(data_to_send))
        # Send a final message to indicate the end of the file
        await websocket.send(json.dumps({"filename": save_as, "end": True}))

async def client(filename, save_as, sink_ip, port):
    # Establish a WebSocket connection to the specified address
    async with websockets.connect('ws://{0}:{1}'.format(sink_ip, port)) as websocket:
        # Call the send_file function to send the specified file
        await send_file(websocket, filename, save_as, 1024)

class DataSpaceResource():

    def __init__(self, db_path='src/db/db.json'):
        """
        Initialize the connection to the database.
        :param db_path: Path to the TinyDB database file.
        """
        self.db = TinyDB(db_path)
        self.resource = self.db.table("resource")

    def create_resource(self, connector_id, asset_id, _type='model'):
        """
        Add a new resource to a specific data space connector in the database with a hash for data integrity.
        
        :param connector_id: Identifier for the connector under which the resource is added.
        :param asset_id: Identifier for the data asset that needed to be shared as a resource. For eg: ML Model ID.
        :param type: Type of the resource (default is 'model').
        
        :return: Returns the resource document with a hash and timestamp if successfully inserted, otherwise returns False.
        """
        # Create timestamp for the creation moment
        timestamp = str(datetime.now().isoformat())
        
        # Prepare the document
        document = {
            'connector_id': connector_id,
            'asset_id': asset_id,
            'type': _type,
            'timestamp': timestamp,
            'doc_type': 'resource',
        }
        
        # Convert document to string and encode it to generate a hash
        document_string = str(document).encode('utf-8')
        hash_digest = hashlib.sha256(document_string).hexdigest()

        # Add hash to the document
        document['resource_id'] = hash_digest

        # Insert the new resource into the database
        logging.info("Adding the resource : {0}".format(str(document)))
        if self.resource.insert(document):
            return document, 201
        else:
            return False, 500
        
    def get_resource(self, resource_id):
        """
        Retrieve a resource by its hash (resource_id).

        :param resource_id: The hash identifier of the resource.
        :return: Resource document if found, otherwise None.
        """
        ResourceQuery = Query()
        result = self.resource.search(ResourceQuery.resource_id == resource_id)
        if result:
            return result[0]
        else:
            return None

    def update_resource(self, resource_id, **updates):
        """
        Update details of an existing resource.

        :param resource_id: The hash identifier of the resource to update.
        :param updates: Keyword arguments representing the fields to update.
        :return: Updated resource document or False if update fails.
        """
        ResourceQuery = Query()
        found = self.resource.search(ResourceQuery.resource_id == resource_id)
        if not found:
            return False, 404

        # Update the resource in the database
        updated_count = self.db.update(updates, ResourceQuery.resource_id == resource_id)
        if updated_count > 0:
            # Recalculate hash if the document changes
            updated_document = self.db.get(ResourceQuery.resource_id == resource_id)
            updated_document_string = str(updated_document).encode('utf-8')
            new_hash = hashlib.sha256(updated_document_string).hexdigest()
            self.resource.update({'resource_id': new_hash}, ResourceQuery.resource_id == resource_id)
            return self.resource.get(ResourceQuery.resource_id == new_hash), 200
        else:
            return False, 500
        
    def create_resource_description(self, resource_id, title, description, keywords=[], connector='trueconnector'):
        """
        Generates or retrieves an IDSA-compatible description for a specific resource based on the provided resource ID,
        title, description, and optionally keywords. The description generation can also be influenced by the specified
        connector, which adjusts the output based on the characteristics or requirements of the connector.

        :param resource_id: The unique identifier for the resource for which the description is to be generated.
                            This ID should uniquely specify a resource in the database.
        :param title: The title of the resource, providing a succinct and informative name.
        :param description: A text description of the resource, detailing its purpose and main features.
        :param keywords: Optional. A list of strings that help in tagging and categorizing the resource. Defaults to an empty list.
        :param connector: Optional. The name of the connector used to tailor the resource description.
                        Defaults to 'trueconnector' if not specified. This parameter allows the description
                        to be adjusted based on specific characteristics or requirements of the connector.

        :return: A JSON object containing the detailed description of the resource. The content of the description
                might vary depending on the connector specified.
        """
    
        ResourceQuery = Query()
    
        found = self.resource.search(ResourceQuery.resource_id == resource_id)

        if found:
            response = {
                "resource_id": resource_id,
                "connector": connector,
                "resource_description": ""
            }

            asset_id = found[0]['asset_id']
            type_of_the_asset = found[0]['type'] 

            if type_of_the_asset == 'model':
                logging.debug("Generating the semantics for model %s", asset_id)
                semantics = model.generate_semantics(asset_id)
            
            elif type_of_the_asset == 'fl_service':
                logging.debug("Generating the semantics for fl service %s", asset_id)
                semantics = fl_service.generate_semantics(asset_id)
            
            
            if semantics:

                if connector == "trueconnector":
                    try:
                        true_connector = TrueConnector()
                        response['resource_description'] = true_connector.create_resource_description(resource_id, type_of_the_asset, title, description, keywords, semantics)
                        return response, 200
                    except Exception as e:
                        logging.error("Resource descriptopn creation failed %s", str(e))
                        return False, 500
                    
            else:
                logging.error("Sematic Creation Returned False")
                return False, 500
            
        else:
            logging.error("Invalid Resource ID")
            return False, 500


    def download_resource(self, resource_id, sink_ip, port):
        
        filename = "artifacts/{0}.zip".format(resource_id)
        save_as = "{0}.zip".format(resource_id)

        ResourceQuery = Query()
    
        found = self.resource.search(ResourceQuery.resource_id == resource_id)

        if found:
            print(found)
            resource_type = found[0]['type']
            if resource_type == 'model':
                model_id = found[0]['asset_id']
                _model = model.get_model(model_id)[0]
                ml_flow_model_path = _model['ml_flow_model_path']

                path_list = ml_flow_model_path.split('/')

                path = settings.MLFLOW_ARTIFACT_PATH + '/' + path_list[1] + '/' + path_list[2] + '/artifacts'

                zip_folder(path, filename)

                loop = asyncio.new_event_loop()
                download_thread = threading.Thread(target=start_async_task, args=(loop, client(filename, save_as, sink_ip, port)))
                download_thread.start()
                
                
                return True, 200

            return False, 500
        else:
            logging.error("Resource Preperation Failed")
            return False, 500

        






