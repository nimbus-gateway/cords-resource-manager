
from tinydb import TinyDB, Query
from src import ma
import re
import hashlib
import json
from datetime import datetime
from marshmallow import Schema, fields

class ErrorReponseSchema(ma.Schema):
    """Schema defining the attributes when creating a new model entry."""
    status = ma.String(required=True)
    message = ma.String(required=True)
    error = ma.String(required=True)

class MLSemanticSchema(ma.Schema):
    """Schema defining the sematnic of a registeed ML Model."""
    model_id = ma.String(required=True)
    semantics = ma.List(fields.Dict(), required=True)

class MLModelSchemaResponse(ma.Schema):
    """Schema defining the attributes after creating new model entry."""
    model_id = ma.String(required=True)
    name = ma.String(required=True)
    version = ma.String(required=True)
    description = ma.String(required=True)
    ml_flow_model_path = ma.String(required=True)
    timestamp = ma.String(required=True)

class MLModelSchema(ma.Schema):
    """Schema defining the attributes when creating a new model entry."""
    name = ma.String(required=True)
    version = ma.String(required=True)
    description = ma.String(required=True)
    ml_flow_model_path = ma.String(required=True)

class MlModel():
    def __init__(self, db_path='src/db/db.json'):
        """
        Initialize the connection to the database.
        :param db_path: Path to the TinyDB database file.
        """
        self.db = TinyDB(db_path)
        self.Model = Query()

    def add_model(self, name, version, description, ml_flow_model_path):
        """
        Add a new model to the database.
        :param name: Name of the model.
        :param version: Version of the model.
        :param description: A short description of the model.
        :ml_flow_model_path description: MLFlow Model Path as recorded in Path variable of MLFlow
        """
        document = {'name': name, 'version': version, 'description': description, 'ml_flow_model_path': ml_flow_model_path}
        model_id = self._create_hashed_id(document)
        document['model_id'] = model_id
        document['timestamp'] = str(datetime.now().isoformat())

        if self._validate_mlflow_input(document['ml_flow_model_path']):
            if self.db.insert(document):
                return document
            else:
                return False
        else:
            raise ValueError("Invalid ml_flow_model_path")
    
    def update_model(self, model_id, name, version, description, ml_flow_model_path):
        """
        Update a new model to the database.
        :param model_id: Id of the model.
        :param name: Name of the model.
        :param version: Version of the model.
        :param description: A short description of the model.
        :ml_flow_model_path description: MLFlow Model Path as recorded in Path variable of MLFlow
        """

        Model = Query()
    
        if self.db.update({'name': name, 'version': version, 'description': description, 
                           'ml_flow_model_path': ml_flow_model_path, 'timestamp': str(datetime.now().isoformat())}, Model.model_id ==model_id):
            return self.get_model(model_id)
        else:
            return False

    def get_model(self, model_id):
        """
        Retrieve a model by its ID.
        :param model_id: The ID of the model to retrieve.
        """
        Model = Query()
        model = self.db.search(Model.model_id == model_id)
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
