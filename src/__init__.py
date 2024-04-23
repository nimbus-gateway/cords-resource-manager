from apifairy import APIFairy
from flask import Flask, json
from flask_marshmallow import Marshmallow
from config import settings

# -------------
# Configuration
# -------------

# Create the instances of the Flask extensions in the global scope,
# but without any arguments passed in. These instances are not
# attached to the Flask application at this point.
apifairy = APIFairy()
ma = Marshmallow()


# ----------------------------
# Application Factory Function
# ----------------------------

def create_app():
    # Create the Flask application
    app = Flask(__name__)

    # Configure the API documentation
    app.config['APIFAIRY_TITLE'] = 'CORDS ML Model Management API'
    app.config['APIFAIRY_VERSION'] = '0.1'
    app.config['APIFAIRY_UI'] = 'elements'

    initialize_extensions(app)
    register_blueprints(app)
    return app


# ----------------
# Helper Functions
# ----------------

def initialize_extensions(app):
    # Since the application instance is now created, pass it to each Flask
    # extension instance to bind it to the Flask application instance (app)
    apifairy.init_app(app)
    ma.init_app(app)


def register_blueprints(app):
    # Import the blueprints
    from src.services.routes import api


    # Since the application instance is now created, register each Blueprint
    # with the Flask application instance (app)
    app.register_blueprint(api, url_prefix='/api')
