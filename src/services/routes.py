from flask import Blueprint
from src.controllers.ml_model_controller import ml_models
from src.controllers.fl_service_controller import fl_services
from src.controllers.ds_connector_controller import ds_connector
from src.controllers.ds_resource_controller import ds_resource
from src.controllers.user_controller import users_blueprint
from src.controllers.policy_controller import policy_blueprint
from src.controllers.pip_controller import pip_blueprint
from src.controllers.front_end_controller import front_end
from flask_cors import CORS

# main blueprint to be registered with application
api = Blueprint('api', __name__)

# register user with api blueprint
api.register_blueprint(fl_services, url_prefix="/fl_services")
api.register_blueprint(ml_models, url_prefix="/ml_models")
api.register_blueprint(ds_connector, url_prefix="/dataspace_connector")
api.register_blueprint(ds_resource, url_prefix="/dataspace_resource")
api.register_blueprint(users_blueprint, url_prefix="/users")
api.register_blueprint(policy_blueprint, url_prefix="/policy")
api.register_blueprint(pip_blueprint, url_prefix="/pip")
api.register_blueprint(front_end, url_prefix="/front_end")





# Apply CORS to all routes under the 'api' blueprint:
CORS(api, resources={r"/*": {"origins": "http://localhost:8082"}})



