from tinydb import TinyDB, Query, table
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

# class PIPPayload(ma.Schema):
#     """Schema defining a policy linked to a resource."""
#     resource_id =  fields.String(
#             required=True, 
#             validate=validate.Length(min=1), 
#             description="A unqiue identification of the resource"
#     )
#     policy_type = fields.String(
#         required=True,
#         validate=validate.Length(min=1), 
#         description="Type of the policy either: EVALUATION_TIME, DURATION, N_TIME, PURPOSE, ROLE"
#     )

#     policy_metadata = fields.Dict(
#         required=True,
#         validate=validate.Length(min=1), 
#         description="Policy type specific constraints and metadata"
#     )





class PIPModel():
    def __init__(self, db_path='src/db/db.json'):
        """
        Initialize the connection to the database.
        :param db_path: Path to the TinyDB database file.
        """
        
        self.db = TinyDB(db_path)

    # adding a access count

    def get_access_count(self, consumer_uri, targetUri):

        PIP = Query()

        resource_id = targetUri.split('/')[-1]
        logging.info("Access for the resource ID: {0}".format(resource_id))

        
        policy_docs = self.db.search((PIP.resource_id == resource_id) & (PIP.doc_type == 'policy'))

        if len(policy_docs) == 0:
            raise ValueError("No policy available for given resource")

        for policy in policy_docs:
            if policy['policy_type'] == 'N_TIMES':
                policy_count = policy['policy_metadata']['TIMES']
                break
            else:
                policy_count = 0

        access_count_doc = self.db.search((PIP.resource_id == resource_id) & (PIP.doc_type == 'pip') & (PIP.consumer_uri == consumer_uri))
        if len(access_count_doc) == 0:
            unique_id = max(self.db.all(), key=lambda x: x.doc_id).doc_id + 1 if self.db.all() else 1
            document = {'doc_type': 'pip', 'consumer_uri': consumer_uri, 'resource_id': resource_id, 'access_count': policy_count-1, 'doc_id': unique_id}
            status = self.db.insert(table.Document(document, doc_id = unique_id))
            logging.info("Updating the access record status {0}".format(str(status)))
            logging.info(str(document))
            return policy_count
            
        else:
            access_count = int(access_count_doc[0]['access_count'])
            document = {'doc_type': 'pip', 'consumer_uri': consumer_uri, 'resource_id': resource_id, 'access_count': access_count-1}
            status = self.db.update(document, (PIP.resource_id == resource_id) & (PIP.doc_type == 'pip') & (PIP.consumer_uri == consumer_uri))
            logging.info("Updating the access record status {0}".format(str(status)))
            logging.info(str(document))
            return access_count



    