
from tinydb import TinyDB, Query,table
from tinydb.table import Document
from src import ma
import re
import hashlib
import json
from datetime import datetime
from marshmallow import Schema, fields, validate
from cords_semantics.semantics import MlSemanticManager
from cords_semantics.mlflow import convert_tags_to_dictionary, extract_mlflow_semantics
import mlflow
import logging
from config import settings

logging.basicConfig(level=logging.DEBUG)  

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
            "session_end_time": fields.String(required=True, description="Timestamp when FL session ended")
        }),
        required=True,
        description="Details of the federated learning session"
    )

    # FL Participants
    fl_participants = fields.Nested(
        Schema.from_dict({
            "num_min_clients": fields.Integer(required=True, description="Minimum number of clients required"),
            "num_max_clients": fields.Integer(required=True, description="Maximum number of clients allowed"),
            "participation_ratio": fields.Float(required=True, description="Ratio of selected clients per training round")
        }),
        required=True,
        description="Details about the clients participating in the FL session"
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
    fl_security_privacy = fields.Nested(
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
            "session_end_time": fields.String(required=True, description="Timestamp when FL session ended")
        }),
        required=True,
        description="Details of the federated learning session"
    )

    # FL Participants
    fl_participants = fields.Nested(
        Schema.from_dict({
            "num_min_clients": fields.Integer(required=True, description="Minimum number of clients required"),
            "num_max_clients": fields.Integer(required=True, description="Maximum number of clients allowed"),
            "participation_ratio": fields.Float(required=True, description="Ratio of selected clients per training round")
        }),
        required=True,
        description="Details about the clients participating in the FL session"
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
    fl_security_privacy = fields.Nested(
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
        self.Model = Query()

    def add_fl_service(self, name, description, fl_session, fl_participants, 
                       fl_aggregation, fl_communication, fl_security_privacy, fl_training):
        """
        Add a new FL service entry to the database.
        
        :param name: Name of the FL service.
        :param description: A short description of the FL service.
        :param fl_session: Dictionary containing session details.
        :param fl_participants: Dictionary containing participant details.
        :param fl_aggregation: Dictionary defining the aggregation method.
        :param fl_communication: Dictionary defining the communication protocol.
        :param fl_security_privacy: Dictionary specifying security and privacy measures.
        :param fl_training: Dictionary containing training-related metadata.
        :return: The inserted document if successful, False otherwise.
        """

        # Generate a unique ID for the new FL service entry
        unique_id = max(self.db.all(), key=lambda x: x.doc_id).doc_id + 1 if self.db.all() else 1
        document = {
            "name": name,
            "description": description,
            "fl_session": fl_session,
            "fl_participants": fl_participants,
            "fl_aggregation": fl_aggregation,
            "fl_communication": fl_communication,
            "fl_security_privacy": fl_security_privacy,
            "fl_training": fl_training,
            "doc_id": unique_id,
            "timestamp": str(datetime.now().isoformat())
        }

        # Generate a unique model ID based on document content
        model_id = self._create_hashed_id(document)
        document["model_id"] = model_id

        # Validate the MLFlow model path before insertion
        
        logging.info(f"Adding the FL service: {document}")
        logging.info(f"Unique ID: {unique_id}")

        # Insert the document into the database
        if self.db.insert(table.Document(document, doc_id=unique_id)):
            return document
        else:
            logging.error("Failed to insert the FL service entry.")
            return False
        
    
    def update_fl_sessoion(self, fl_service_id, name, description, ml_flow_model_path):
        """
        Update a new model to the database.
        :param model_id: Id of the model.
        :param name: Name of the model.
        :param version: Version of the model.
        :param description: A short description of the model.
        :ml_flow_model_path description: MLFlow Model Path as recorded in Path variable of MLFlow
        """

        Model = Query()
    
        if self.db.update({'name': name, 'description': description, 
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
        model = self.db.search(Model.fl_service_id == fl_service_id)
        if model:
            return model
        else:
            return False

    def query_models(self, search_criteria):
        """
        Query models based on a search criteria.
        :param search_criteria: A dictionary with field values to search for.
        """
        results = self.db.search(self.Model.matches(search_criteria))
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
        
    def generate_semantics(self, model_id):
        try:
            mlflow.set_tracking_uri(settings.MLFLOW_URI)
            semantic_manager = MlSemanticManager('data/cordsml.rdf')
            
            ml_flow_run_id = self.get_mlflow_run_id(model_id)
            logging.info("run id retrieved :%s", ml_flow_run_id)
            mflow_tags = extract_mlflow_semantics(ml_flow_run_id)
            logging.info("tags extracted from mlflow: %s", str(mflow_tags))

            mlflow_semantics_dictionary = convert_tags_to_dictionary(mflow_tags)
            logging.info("semantic in a dictionary: %s ", str(mlflow_semantics_dictionary))

            semantic_graph = semantic_manager.create_model_semantics(mlflow_semantics_dictionary)
            jsonld_output = semantic_manager.convert_to_json_ld()

            jsonld_output = jsonld_output

            return jsonld_output

        except Exception as e:
            logging.error("Error Occured During Semantic Generation %s",str(e))
            return False
        
 
