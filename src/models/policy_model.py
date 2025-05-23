
from tinydb import TinyDB, Query, table
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
import os
import uuid

logging.basicConfig(level=logging.DEBUG)  

class PolicyPayload(ma.Schema):
    """Schema defining a policy linked to a resource."""
    resource_id =  fields.String(
            required=True, 
            validate=validate.Length(min=1), 
            description="A unqiue identification of the resource"
    )
    policy_type = fields.String(
        required=True,
        validate=validate.Length(min=1), 
        description="Type of the policy either: EVALUATION_TIME, DURATION, N_TIME, PURPOSE, ROLE"
    )

    policy_metadata = fields.Dict(
        required=True,
        validate=validate.Length(min=1), 
        description="Policy type specific constraints and metadata"
    )



policies ={
    "access": []
}



class PolicyModel():
    def __init__(self, db_path='src/db/db.json'):
        """
        Initialize the connection to the database.
        :param db_path: Path to the TinyDB database file.
        """
        
        self.db = TinyDB(db_path)
        self.policies = self.db.table("policies")
        self.Model = Query()
        
        try:
             self.PURPOSE= self._load_json('policies/PURPOSE.json')
             self.ROLE = self._load_json('policies/ROLE.json')
             self.EVALUATION_TIME = self._load_json('policies/EVALUATION_TIME.json')
             self.N_TIMES = self._load_json('policies/N_TIMES.json')
             self.FL_SECURE_AGGREGATION = self._load_json('policies/FL_SECURE_AGGREGATION.json')
             self.FL_PARTICIPANT_REPUTATION = self._load_json('policies/FL_PARTICIPANT_REPUTATION.json')
             self.FL_PARTICIPANT_CPU = self._load_json('policies/FL_PARTICIPANT_CPU.json')
             self.FL_PARTICIPANT_GEO = self._load_json('policies/FL_PARTICIPANT_GEO.json')
             self.FL_LOCAL_MODEL_PERFORMANCE = self._load_json('policies/FL_LOCAL_MODEL_PERFORMANCE.json')
             self.FL_INCENTIVE_REWARD = self._load_json('policies/FL_INCENTIVE_REWARD.json')
        except Exception as e:
             logging.error("One or more policy templates missing")
             raise e

    # def get_policy_template(self, type):
    #     return False

    def add_policy(self, resource_id, policy_type, metadata):
        """
        Add a new policy and link to a resource.
        :param resource_id: A unqiue identification of the resource.
        :param policy_type: Type of the policy either: DURATION, N-TIME, PURPOSE, ROLE.
        :param metadata: Policy type specific constraints and metadata.
        """
        document = {'resource_id': resource_id, 'policy_type': policy_type, 'policy_metadata': metadata}
        policy_id = self._create_hashed_id(document)
        document['doc_type'] = 'policy'
        document['policy_id'] = policy_id
        document['timestamp'] = str(datetime.now().isoformat())


        result = self.policies.insert(document)
        if result:
            logging.debug(f"Policy added successfully: {document}")
            return document
        else:
            logging.error("Failed to add policy")
            return False
        
    def get_policy(self, resource_id):
        """
        Retrieve policies linked to a resource.
        :param resource_id: ID of the resource.
        """
        Policy = Query()
        policies = self.policies.search(Policy.resource_id == resource_id)
        logging.debug(f"Policies retrieved for resource_id {resource_id}: {policies}")
        if policies:
            return policies
        else:
            logging.warning(f"No policies found for resource_id {resource_id}")
            return False
        
    def remove_policy(self, policy_id):
        """
        Remove a policy linked to a resource.
        :param policy_id: ID of the policy.
        :return: True if the policy was removed, False otherwise.
        """
        Policy = Query()
        result = self.policies.remove(Policy.policy_id == policy_id)
        if result:
            return True
        else:
            return False
        
    def _load_json(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file at path {file_path} does not exist.")
        
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
        
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
    
    def formalize_policies(self, resource_id):
        logging.debug("========== Formalizing the policies =============")
        Policy = Query()
        policies = self.policies.search(Policy.resource_id == resource_id)
        permissions = []
        fL_permissions = []
        print(policies)
        if policies:
            for policy in policies:
                if policy['policy_type'] == 'EVALUATION_TIME':
                    template = self.EVALUATION_TIME
                    template["@id"] = str("https://w3id.org/idsa/autogen/permission/{0}-{1}".format(resource_id, 'EVALUATION_TIME'))
                    template['ids:constraint'][0]['ids:rightOperand']['@value'] = str(policy['policy_metadata']['AFTER'])
                    template['ids:constraint'][1]['ids:rightOperand']['@value'] = str(policy['policy_metadata']['BEFORE'])
                    template['ids:constraint'][0]['@id'] = str('https://w3id.org/idsa/autogen/constraint/{0}'.format(uuid.uuid4()))
                    template['ids:constraint'][1]['@id'] = str('https://w3id.org/idsa/autogen/constraint/{0}'.format(uuid.uuid4()))
                    permissions.append(template)

                if policy['policy_type'] == 'N-TIMES' or policy['policy_type'] == 'N_TIMES':
                    template = self.N_TIMES
                    template["@id"] = str("https://w3id.org/idsa/autogen/permission/{0}-{1}".format(resource_id, 'N-TIMES'))
                    template['ids:constraint'][0]['ids:rightOperand']['@value'] = str(policy['policy_metadata']['TIMES'])
                    template['ids:constraint'][0]['ids:pipEndpoint']['@id'] = str(policy['policy_metadata']['PIPENDPOINT'])
                    template['ids:constraint'][0]['@id'] = str('https://w3id.org/idsa/autogen/constraint/{0}'.format(uuid.uuid4()))
                    permissions.append(template)

                if policy['policy_type'] == 'PURPOSE':
                    template = self.PURPOSE
                    template["@id"] = str("https://w3id.org/idsa/autogen/permission/{0}-{1}".format(resource_id, 'PURPOSE'))
                    template['ids:constraint'][0]['ids:rightOperandReference']['@id'] = str(policy['policy_metadata']['PURPOSE'])
                    template['ids:constraint'][0]['ids:pipEndpoint']['@id'] = str(policy['policy_metadata']['PIPENDPOINT'])
                    template['ids:constraint'][0]['@id'] = str('https://w3id.org/idsa/autogen/constraint/{0}'.format(uuid.uuid4()))
                    permissions.append(template)

                if policy['policy_type'] == 'ROLE':
                    template = self.ROLE
                    template["@id"] = str("https://w3id.org/idsa/autogen/permission/{0}-{1}".format(resource_id, 'ROLE'))
                    template['ids:constraint'][0]['ids:rightOperandReference']['@id'] = str(policy['policy_metadata']['ROLE'])
                    template['ids:constraint'][0]['ids:pipEndpoint']['@id'] = str(policy['policy_metadata']['PIPENDPOINT'])
                    template['ids:constraint'][0]['@id'] = str('https://w3id.org/idsa/autogen/constraint/{0}'.format(uuid.uuid4()))
                    permissions.append(template)

                if policy['policy_type'] == 'FL_SECURE_AGGREGATION':
                    template = self.ROLE
                    template["@id"] = str("https://w3id.org/idsa/autogen/permission/{0}-{1}".format(resource_id, 'FL_SECURE_AGGREGATION'))
                    template['ids:constraint'][0]['ids:rightOperandReference']['@id'] = str(policy['policy_metadata']['AGGREGATION_ALGORITHM'])
                    template['ids:constraint'][0]['ids:pipEndpoint']['@id'] = str(policy['policy_metadata']['PIPENDPOINT'])
                    template['ids:constraint'][0]['@id'] = str('https://w3id.org/idsa/autogen/constraint/{0}'.format(uuid.uuid4()))
                    fL_permissions.append(template)

                if policy['policy_type'] == 'FL_PARTICIPANT_REPUTATION':
                    template = self.ROLE
                    template["@id"] = str("https://w3id.org/idsa/autogen/permission/{0}-{1}".format(resource_id, 'FL_PARTICIPANT_REPUTATION'))
                    template['ids:constraint'][0]['ids:rightOperandReference']['@id'] = str(policy['policy_metadata']['MIN_PARTICIPANT_REPUTATION'])
                    template['ids:constraint'][0]['ids:pipEndpoint']['@id'] = str(policy['policy_metadata']['PIPENDPOINT'])
                    template['ids:constraint'][0]['@id'] = str('https://w3id.org/idsa/autogen/constraint/{0}'.format(uuid.uuid4()))
                    fL_permissions.append(template)

                if policy['policy_type'] == 'FL_PARTICIPANT_CPU':
                    template = self.ROLE
                    template["@id"] = str("https://w3id.org/idsa/autogen/permission/{0}-{1}".format(resource_id, 'FL_PARTICIPANT_CPU'))
                    template['ids:constraint'][0]['ids:rightOperandReference']['@id'] = str(policy['policy_metadata']['FL_PARTICIPANT_CPU'])
                    template['ids:constraint'][0]['ids:pipEndpoint']['@id'] = str(policy['policy_metadata']['PIPENDPOINT'])
                    template['ids:constraint'][0]['@id'] = str('https://w3id.org/idsa/autogen/constraint/{0}'.format(uuid.uuid4()))
                    fL_permissions.append(template)

                if policy['policy_type'] == 'FL_LOCAL_MODEL_EVALUATION':
                    template = self.ROLE
                    template["ids:action"][0]["@id"] = str("fl:aggregate")
                    template["@id"] = str("https://w3id.org/idsa/autogen/permission/{0}-{1}".format(resource_id, 'FL_LOCAL_MODEL_EVALUATION'))
                    template['ids:constraint'][0]['ids:leftOperand']['@id'] = str(policy['policy_metadata']['FL_ModelEvaluation_SpecifiedBy'])
                    template['ids:constraint'][0]['ids:rightOperandReference']['@id'] = str(policy['policy_metadata']['FL_ModelEvaluation_HasValue'])
                    template['ids:constraint'][0]['ids:operator']['@id'] = str(policy['policy_metadata']['FL_Contraint_Operator'])
                    template['ids:constraint'][0]['ids:pipEndpoint']['@id'] = str(policy['policy_metadata']['PIPENDPOINT'])
                    template['ids:constraint'][0]['@id'] = str('https://w3id.org/idsa/autogen/constraint/{0}'.format(uuid.uuid4()))
                    fL_permissions.append(template)


        return permissions, fL_permissions        



    
    # def update_model(self, model_id, name, version, description, ml_flow_model_path):
    #     """
    #     Update a new model to the database.
    #     :param model_id: Id of the model.
    #     :param name: Name of the model.
    #     :param version: Version of the model.
    #     :param description: A short description of the model.
    #     :ml_flow_model_path description: MLFlow Model Path as recorded in Path variable of MLFlow
    #     """

    #     Model = Query()
    
    #     if self.db.update({'name': name, 'version': version, 'description': description, 
    #                        'ml_flow_model_path': ml_flow_model_path, 'timestamp': str(datetime.now().isoformat())}, Model.model_id ==model_id):
    #         return self.get_model(model_id)
    #     else:
    #         return False