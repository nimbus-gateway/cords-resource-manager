from src import ma
from marshmallow import Schema, fields, validate


class ErrorReponseSchema(ma.Schema):
    """Schema of an error message of the CORDS ML Manager API"""
    status = ma.String(required=True)
    message = ma.String(required=True)
    error = ma.String(required=True)