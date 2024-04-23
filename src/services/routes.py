from flask import Blueprint
from src.controllers.ml_model_controller import ml_models

# main blueprint to be registered with application
api = Blueprint('api', __name__)

# register user with api blueprint
api.register_blueprint(ml_models, url_prefix="/ml_models")

