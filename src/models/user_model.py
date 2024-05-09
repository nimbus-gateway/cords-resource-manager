import secrets
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash
from src import ma
from marshmallow import Schema, fields, validate
from tinydb import TinyDB, Query
import hashlib
import json
import logging

logging.basicConfig(level=logging.DEBUG)  

class NewUserSchema(ma.Schema):
    """Schema defining the attributes when creating a new user."""
    email = fields.Email(
        required=True, 
        validate=validate.Length(min=4), 
        description="Email address of the user.",
        error_messages={"required": "Email is required."}
    )
    password= fields.String(
        required=True, 
        validate=validate.Length(min=4), 
        description="Password of the user.",
        error_messages={"required": "Email is required."}
    )
    first_name = fields.String(
        required=True, 
        validate=validate.Length(min=1), 
        description="First name of the user.",
        error_messages={"required": "First name is required."}
    )
    last_name = fields.String(
        required=True, 
        validate=validate.Length(min=1), 
        description="Last name of the user.",
        error_messages={"required": "Last name is required."}
    )
    role = fields.String(
        required=True, 
        validate=validate.Length(min=1), 
        description="Role of the user in the platform.",
        error_messages={"required": "Role is required."}
    )

class UserSchema(ma.Schema):
    """Schema defining the attributes of a user."""
    id = ma.Integer()
    email = ma.String()


class TokenSchema(ma.Schema):
    """Schema defining the attributes of a token."""
    token = ma.String()


class User():
    def __init__(self, db_path='src/db/db.json'):
        """Create a new User object."""
        self.db = TinyDB(db_path)
        self.User = Query()
        self.email = None
        self.password = None
        self.first_name = None
        self.last_name = None
        self.role = None
        self.auth_token = None
        self.auth_token_expiration = None
        self.password_hashed = None

    def is_password_correct(self, email: str, password_plaintext: str):

        user = self.get_user(email)
        return check_password_hash(user['password'], password_plaintext)

    def set_password(self, password_plaintext: str):
        self.password_hashed = self._generate_password_hash(password_plaintext)


    def add_user(self, email, password, first_name, last_name, role):
        """
        Add a new user to the database.
        :param email: Email address of the user.
        :param password: Password of the user.
        """

        password = self._generate_password_hash(password)
        document = {'email': email, 'password': password, 'first_name': first_name, 'last_name': last_name, 'role': role }
        user_id = self._create_hashed_id(document)
        document['user_id'] = user_id
        document['timestamp'] = str(datetime.now().isoformat())

        response_document = dict(document)
        document['auth_token'] = ""
        document['auth_token_expiration'] = ""

        if self.db.insert(document):
                return response_document
        else:
            return False

    def get_user(self, email):
        """
        Retrieve a user by its ID.
        :param user_id: The ID of the model to retrieve.
        """
    
        user = self.db.search(self.User.email == email)
        if user:
            self.email = user[0]['email']
            self.password = user[0]['password']
            self.first_name = user[0]['first_name']
            self.last_name = user[0]['last_name']
            self.role = user[0]['role']
            self.auth_token = user[0]['auth_token']
            if user[0]['auth_token_expiration'] != "":
                self.auth_token_expiration = datetime.fromisoformat(user[0]['auth_token_expiration'])
            else:
                self.auth_token_expiration = None
            return user[0]
        else:
            return False

        

    @staticmethod
    def _generate_password_hash(password_plaintext):
        return generate_password_hash(password_plaintext)

    def generate_auth_token(self):
        self.auth_token = secrets.token_urlsafe()
        self.auth_token_expiration = datetime.utcnow() + timedelta(minutes=60)

        try:
            self.db.update({'auth_token' : self.auth_token, 'auth_token_expiration': self.auth_token_expiration.isoformat()}, 
                           self.User.email == self.email )
            return self.auth_token
        except Exception as e:
            logging.error(e.__repr__())
            return False

    def verify_auth_token(self, auth_token):
        user = self.db.search(self.User.auth_token == auth_token)
        if len(user) == 0:
            return False
        user = user[0]
        # user = User.query.filter_by(auth_token=auth_token).first()
        if user['auth_token_expiration'] != "":
            auth_token_expiry = datetime.fromisoformat(user['auth_token_expiration'])
            if user and auth_token_expiry > datetime.utcnow():
                return True
        else:
            return False
        

    def revoke_auth_token(self):
        self.auth_token_expiration = datetime.utcnow()

    # def __repr__(self):
    #     return f'<User: {self.email}>'
    
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