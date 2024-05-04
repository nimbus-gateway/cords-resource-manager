from flask import Blueprint
from src.controllers.ml_model_controller import ml_models
from src.controllers.ds_connector_controller import ds_connector
from src.controllers.ds_resource_controller import ds_resource
from src.controllers.user_controller import users_blueprint

# main blueprint to be registered with application
api = Blueprint('api', __name__)

# register user with api blueprint
api.register_blueprint(ml_models, url_prefix="/ml_models")
api.register_blueprint(ds_connector, url_prefix="/dataspace_connector")
api.register_blueprint(ds_resource, url_prefix="/dataspace_resource")
api.register_blueprint(users_blueprint, url_prefix="/users")

