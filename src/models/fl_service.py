
from tinydb import TinyDB, Query,table
from tinydb.table import Document
from src import ma
import re
import hashlib
import json
from datetime import datetime
from marshmallow import Schema, fields, validate
from cords_semantics.semantics import FlSemanticManager
from cords_semantics.mlflow import convert_tags_to_dictionary, extract_mlflow_semantics
import mlflow
import logging
from config import settings

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s'
)


class MLSemanticSchema(ma.Schema):
    """Schema defining the semantics of a registeed ML Model."""
    model_id =  fields.String(
            required=True, 
            validate=validate.Length(min=1), 
            description="A unqiue identification for the model generated by the API"
    )
    semantics = fields.Dict(
        required=True,
         description="A unqiue identification for the model generated by the API"
    )

class FLServiceSchemaResponse(ma.Schema):
    """Schema defining the attributes after creating new model entry."""
    fl_service_id = fields.String(
            required=True, 
            validate=validate.Length(min=1), 
            description="A unqiue identification for the fl service generated by the API"
    )
    name = fields.String(
            required=True, 
            validate=validate.Length(min=1), 
            description="A name of the federated learning service"
    )
    description = fields.String(
            required=True, 
            validate=validate.Length(min=1), 
            description="Description of the FL service",
    )
        # FL Session
    fl_session = fields.Nested(
        Schema.from_dict({
            "session_id": fields.String(required=True, description="Unique identifier for an FL session"),
            "session_start_time": fields.String(required=True, description="Timestamp when FL session started"),
            "session_end_time": fields.String(required=True, description="Timestamp when FL session ended"),
            "num_min_clients": fields.Integer(required=True, description="Minimum number of clients required"),
            "num_max_clients": fields.Integer(required=True, description="Maximum number of clients allowed"),
            "participation_ratio": fields.Float(required=True, description="Ratio of selected clients per training round")
        }),
        required=True,
        description="Details of the federated learning session"
    )

    # FL Aggregation
    fl_aggregation = fields.Nested(
        Schema.from_dict({
            "aggregation_method": fields.String(required=True, description="Type of aggregation (FedAvg, FedProx, FedSGD)"),
            "aggregation_frequency": fields.Integer(required=True, description="Number of training rounds before aggregation")
        }),
        required=True,
        description="Defines how client model updates are aggregated"
    )

    # FL Communication
    fl_communication = fields.Nested(
        Schema.from_dict({
            "communication_protocol": fields.String(required=True, description="Protocol used for updates (MQTT, gRPC, WebSockets)"),
            "secure_aggregation_enabled": fields.Boolean(required=True, description="Whether secure aggregation is applied (Yes/No)")
        }),
        required=True,
        description="Defines how model updates are exchanged"
    )

    # FL Security & Privacy
    fl_security = fields.Nested(
        Schema.from_dict({
            "differential_privacy_enabled": fields.Boolean(required=True, description="Whether differential privacy is applied (Yes/No)"),
            "encryption_method": fields.String(required=True, description="Encryption method used for secure FL communication")
        }),
        required=True,
        description="Ensures data privacy and security in FL"
    )

    # FL Training
    fl_training = fields.Nested(
        Schema.from_dict({
            "training_rounds": fields.Integer(required=True, description="Number of training rounds in FL session"),
            "local_epochs": fields.Integer(required=True, description="Number of local training epochs per client"),
            "loss_function": fields.String(required=True, description="Loss function used in model training")
        }),
        required=True,
        description="Defines all training-related metadata"
    )
    timestamp = fields.String(
            required=True, 
            validate=validate.Length(min=1), 
            description="Time stamp when the fl service was added",
    )


class FLServiceSchema(Schema):
    """Schema defining the attributes when creating a new FL service entry."""
    
    # Basic FL Service Info
    name = fields.String(
        required=True,
        validate=validate.Length(min=1),
        description="A name of the federated learning service",
        error_messages={"required": "Service name is required."}
    )
    
    description = fields.String(
        required=True,
        validate=validate.Length(min=1),
        description="Description of the FL learning service going to initiate",
        error_messages={"required": "Description is required."}
    )
    
    # FL Session
    fl_session = fields.Nested(
        Schema.from_dict({
            "session_id": fields.String(required=True, description="Unique identifier for an FL session"),
            "session_start_time": fields.String(required=True, description="Timestamp when FL session started"),
            "session_end_time": fields.String(required=True, description="Timestamp when FL session ended"),
            "num_min_clients": fields.Integer(required=True, description="Minimum number of clients required"),
            "num_max_clients": fields.Integer(required=True, description="Maximum number of clients allowed"),
            "participation_ratio": fields.Float(required=True, description="Ratio of selected clients per training round")
        }),
        required=True,
        description="Details of the federated learning session"
    )

    # FL Aggregation
    fl_aggregation = fields.Nested(
        Schema.from_dict({
            "aggregation_method": fields.String(required=True, description="Type of aggregation (FedAvg, FedProx, FedSGD)"),
            "aggregation_frequency": fields.Integer(required=True, description="Number of training rounds before aggregation")
        }),
        required=True,
        description="Defines how client model updates are aggregated"
    )

    # FL Communication
    fl_communication = fields.Nested(
        Schema.from_dict({
            "communication_protocol": fields.String(required=True, description="Protocol used for updates (MQTT, gRPC, WebSockets)"),
            "secure_aggregation_enabled": fields.Boolean(required=True, description="Whether secure aggregation is applied (Yes/No)")
        }),
        required=True,
        description="Defines how model updates are exchanged"
    )

    # FL Security & Privacy
    fl_security = fields.Nested(
        Schema.from_dict({
            "differential_privacy_enabled": fields.Boolean(required=True, description="Whether differential privacy is applied (Yes/No)"),
            "encryption_method": fields.String(required=True, description="Encryption method used for secure FL communication")
        }),
        required=True,
        description="Ensures data privacy and security in FL"
    )

    # FL Training
    fl_training = fields.Nested(
        Schema.from_dict({
            "training_rounds": fields.Integer(required=True, description="Number of training rounds in FL session"),
            "local_epochs": fields.Integer(required=True, description="Number of local training epochs per client"),
            "loss_function": fields.String(required=True, description="Loss function used in model training")
        }),
        required=True,
        description="Defines all training-related metadata"
    )


class FLService():
    def __init__(self, db_path='src/db/db.json'):
        """
        Initialize the connection to the database.
        :param db_path: Path to the TinyDB database file.
        """
        self.db = TinyDB(db_path)
        self.fl_services = self.db.table("fl_services")
        self.Model = Query()

    def add_fl_service(self, name, description, fl_session,
                       fl_aggregation, fl_communication, fl_security_privacy, fl_training):
        """
        Add a new FL service entry to the database.
        
        :param name: Name of the FL service.
        :param description: A short description of the FL service.
        :param fl_session: Dictionary containing session details.
        :param fl_aggregation: Dictionary defining the aggregation method.
        :param fl_communication: Dictionary defining the communication protocol.
        :param fl_security_privacy: Dictionary specifying security and privacy measures.
        :param fl_training: Dictionary containing training-related metadata.
        :return: The inserted document if successful, False otherwise.
        """

        # Generate a unique ID for the new FL service entry
        document = {
            "name": name,
            "description": description,
            "fl_session": fl_session,
            "fl_aggregation": fl_aggregation,
            "fl_communication": fl_communication,
            "fl_security": fl_security_privacy,
            "fl_training": fl_training,
            "doc_type": "fl_service",
            "timestamp": str(datetime.now().isoformat())
        }

        # Generate a unique model ID based on document content
        fl_service_id = self._create_hashed_id(document)
        document["fl_service_id"] = fl_service_id

        # Validate the MLFlow model path before insertion
        
        logging.info(f"Adding the FL service: {document}")

        # Insert the document into the database
        if self.fl_services.insert(document):
            return document
        else:
            logging.error("Failed to insert the FL service entry.")
            return False
        
    
    def update_fl_session(self, fl_service_id, name, description, ml_flow_model_path):
        """
        Update a new model to the database.
        :param model_id: Id of the model.
        :param name: Name of the model.
        :param version: Version of the model.
        :param description: A short description of the model.
        :ml_flow_model_path description: MLFlow Model Path as recorded in Path variable of MLFlow
        """

        Model = Query()
    
        if self.fl_services.update({'name': name, 'description': description, 
                           'ml_flow_model_path': ml_flow_model_path, 'timestamp': str(datetime.now().isoformat())}, Model.fl_service_id ==fl_service_id):
            return self.get_model(fl_service_id)
        else:
            return False

    def get_fl_service(self, fl_service_id):
        """
        Retrieve a model by its ID.
        :param model_id: The ID of the model to retrieve.
        """
        Model = Query()
        model = self.fl_services.search(Model.fl_service_id == fl_service_id)
        if model:
            return model
        else:
            return False
        

    def get_all_services(self):
        """
        Retrieve all documents in the table 'fl_services'.
        """
        logging.info("Retrieving all FL services from the database.")
        services = self.fl_services.all()
        return services if services else []

    def get_service_summary(self):
        """
        Retrieve all documents from fl_services, resources, and policies tables joined by asset_id and resource_id.
        """
        logging.info("Retrieving service summary by joining fl_services, resources, and policies tables.")
        Model = Query()
        services = self.fl_services.all()
        resources = self.db.table("resource").all()
        policies = self.db.table("policies").all()

        logging.debug(f"Retrieved {len(services)} services, {len(resources)} resources, and {len(policies)} policies from the database.")

        # Create a dictionary of resources indexed by asset_id for quick lookup
        resources_by_asset_id = {resource["asset_id"]: resource for resource in resources if "asset_id" in resource}
        logging.debug(f"Created resources lookup dictionary with {len(resources_by_asset_id)} entries.")

        # Create a dictionary of policies indexed by resource_id for quick lookup
        policies_by_resource_id = {}
        for policy in policies:
            resource_id = policy.get("resource_id")
            if resource_id:
                if resource_id not in policies_by_resource_id:
                    policies_by_resource_id[resource_id] = []
                policies_by_resource_id[resource_id].append(policy)
        logging.debug(f"Created policies lookup dictionary with {len(policies_by_resource_id)} entries.")

        # Join services with resources and policies
        joined_data = []
        for service in services:
            asset_id = service.get("fl_service_id")
            if asset_id and asset_id in resources_by_asset_id:
                resource = resources_by_asset_id[asset_id]
                resource_id = resource.get("resource_id")
                joined_entry = {**service, **resource}
                joined_entry["policies"] = policies_by_resource_id.get(resource_id, [])
                joined_data.append(joined_entry)
                logging.debug(f"Joined service with asset_id {asset_id} to corresponding resource and policies.")
            else:
                if asset_id:
                    logging.warning(f"No matching resource found for service with asset_id {asset_id}.")
                else:
                    logging.warning("Service does not have an asset_id.")

        logging.info(f"Returning {len(joined_data)} joined entries.")
        return joined_data if joined_data else []
        

    def query_models(self, search_criteria):
        """
        Query models based on a search criteria.
        :param search_criteria: A dictionary with field values to search for.
        """
        results = self.fl_services.search(self.Model.matches(search_criteria))
        return results if results else "No models found matching the criteria."
    
    def get_mlflow_run_id(self, model_id):
        """
        Get the MLFlow Run ID of an artifact corresponding to a registered Model.
        :param model_id: The ID of the model.
        """
        model = self.get_model(model_id)[0]
        
        if model:
            artifact_path = model['ml_flow_model_path']
            run_id = artifact_path.split('/')[2]
            return run_id
        
        else:
            return False

    def _create_hashed_id(self, document):
        # Serialize the document data to JSON format
        # Ensure consistent ordering by sorting keys
        doc_string = json.dumps(document, sort_keys=True)
        
        # Get current timestamp as a string
        timestamp = datetime.now().isoformat()
        
        # Create a hash object
        hash_obj = hashlib.sha256()
        
        # Update the hash object with the document string and timestamp
        hash_obj.update(doc_string.encode('utf-8'))
        hash_obj.update(timestamp.encode('utf-8'))
        
        # Return the hexadecimal digest of the hash
        return hash_obj.hexdigest()
    
    def _validate_mlflow_input(self, input_string):
        # Define the regex pattern
        pattern = r"^mlflow-artifacts:/\d+/[a-zA-Z0-9]+/artifacts/[a-zA-Z0-9_\-]+$"

        # Compile the regex pattern for efficiency if used repeatedly
        regex = re.compile(pattern)

        # Use the fullmatch method to check if the entire string conforms to the pattern
        if regex.fullmatch(input_string):
            return True
        else:
            return False
        
    def generate_semantics(self, fl_service_id):
        """Generate semantic description"""

        fl_semantic_manager = FlSemanticManager('data/cords_federated_learning.rdf')

        service = self.get_fl_service(fl_service_id)[0]
        
        tags = self.__convert_json_to_cords_format(service)
        logging.info(tags)
        semantics_dictionary = convert_tags_to_dictionary([tags])
        logging.info(semantics_dictionary)
        semantics = fl_semantic_manager.create_fl_semantics(semantics_dictionary)
        logging.info(semantics)
        return semantics



        
    def __convert_json_to_cords_format(self, input_json):
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
 
