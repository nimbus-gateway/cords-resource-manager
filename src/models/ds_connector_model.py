
from tinydb import TinyDB, Query
from src import ma
import re
import hashlib
import json
from datetime import datetime
from marshmallow import Schema, fields, validate


class ErrorReponseSchema(ma.Schema):
    """Schema defining the attributes when creating a new model entry."""
    status = ma.String(required=True)
    message = ma.String(required=True)
    error = ma.String(required=True)

class ConnectorGetSchema(ma.Schema):
    """Schema defing a connector get payload"""
    id = fields.String(
        required=True,
        validate=validate.Length(min=1),
        description="Unique identifier for the connector.",
        error_messages={"required": "ID is required."}
    )


class DataSpaceConnectorSchemaResponse(ma.Schema):
    """Schema a Data Space Connector."""
    id = fields.String(
        required=True,
        validate=validate.Length(min=1),
        description="Unique identifier for the connector.",
        error_messages={"required": "ID is required."}
    )
    name = fields.String(
        required=True,
        validate=validate.Length(min=1),
        description="Name of the connector.",
        error_messages={"required": "Name is required."}
    )
    type = fields.String(
        required=True,
        validate=validate.Length(min=1),
        description="Type of the connector, describing its purpose or functionality.",
        error_messages={"required": "Type is required."}
    )
    description = fields.String(
        required=True,
        validate=validate.Length(min=1),
        description="A short description of the connector, outlining its main features or role.",
        error_messages={"required": "Description is required."}
    )
    public_key = fields.String(
        required=True,
        validate=validate.Length(min=1),
        description="Public key associated with the connector, used for secure communications.",
        error_messages={"required": "Public key is required."}
    )
    access_url = fields.Url(
        required=True,
        description="Access URL for the connector, providing the primary point of interface.",
        error_messages={"required": "Access URL is required."}
    )
    reverse_proxy_url = fields.Url(
        required=True,
        description="URL of the reverse proxy associated with the connector, used to manage and route traffic.",
    )
    timestamp = fields.String(
        required=True,
        description="Time stamp when the connector is added.",
    )


class DataSpaceConnectorSchema(ma.Schema):
    """Schema a Data Space Connector."""
    id = fields.String(
        required=True,
        validate=validate.Length(min=1),
        description="Unique identifier for the connector.",
        error_messages={"required": "ID is required."}
    )
    name = fields.String(
        required=True,
        validate=validate.Length(min=1),
        description="Name of the connector.",
        error_messages={"required": "Name is required."}
    )
    type = fields.String(
        required=True,
        validate=validate.Length(min=1),
        description="Type of the connector, describing its purpose or functionality.",
        error_messages={"required": "Type is required."}
    )
    description = fields.String(
        required=True,
        validate=validate.Length(min=1),
        description="A short description of the connector, outlining its main features or role.",
        error_messages={"required": "Description is required."}
    )
    public_key = fields.String(
        required=True,
        validate=validate.Length(min=1),
        description="Public key associated with the connector, used for secure communications.",
        error_messages={"required": "Public key is required."}
    )
    access_url = fields.Url(
        required=True,
        description="Access URL for the connector, providing the primary point of interface.",
        error_messages={"required": "Access URL is required."}
    )
    reverse_proxy_url = fields.Url(
        required=True,
        description="URL of the reverse proxy associated with the connector, used to manage and route traffic.",
        error_messages={"required": "Reverse proxy URL is required."}
    )



class DataSpaceConnector():

    def __init__(self, db_path='src/db/db.json'):
        """
        Initialize the connection to the database.
        :param db_path: Path to the TinyDB database file.
        """
        self.db = TinyDB(db_path)

    def add_connector(self, id, name, type, description, public_key, access_url, reverseProxyUrl):
        """
        Add a new data space connector to the database with specified attributes.
        
        :param id: Identifier for the connector.
        :param name: Name of the connector.
        :param type: Type of the connector.
        :param description: A short description of the connector.
        :param public_key: Public key associated with the connector.
        :param access_url: Access URL for the connector.
        :param reverseProxyUrl: URL of the reverse proxy associated with the connector.
        
        :return: Returns the connector document if successfully inserted, otherwise returns False.
        """
        document = {
            'id': id,
            'name': name,
            'type': type,
            'description': description,
            'public_key': public_key,
            'access_url': access_url,
            'reverse_proxy_url': reverseProxyUrl,
            'timestamp': str(datetime.now().isoformat())
        }
        
        ConnectorQuery = Query()
        found = self.db.search(ConnectorQuery.id == id)
        if found:
            # If the ID already exists, return an error message
            return False, 409

        if self.db.insert(document):
                return document, 201
        else:
            return False, 500
        

    def get_connector(self, id):
        """
        Retrieve a connector by its ID.
        
        :param id: Identifier for the connector.
        :return: Connector document or None if not found.
        """
        ConnectorQuery = Query()
        result = self.db.search(ConnectorQuery.id == id)
        if result:
            return result[0]
        else:
            return None

    def update_connector(self, id, **updates):
        """
        Update an existing connector's details based on the provided updates.
        
        :param id: Identifier for the connector.
        :param updates: A dictionary of attributes to update.
        :return: Updated document or False if the update failed.
        """
        ConnectorQuery = Query()
        found = self.db.search(ConnectorQuery.id == id)
        if not found:
            return False, 404

        updated_count = self.db.update(updates, ConnectorQuery.id == id)
        if updated_count > 0:
            return self.get_connector(id)
        else:
            return False, 500
    
