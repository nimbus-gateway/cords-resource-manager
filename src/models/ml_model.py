
from tinydb import TinyDB, Query
from src import ma

class ErrorReponseSchema(ma.Schema):
    """Schema defining the attributes when creating a new model entry."""
    status = ma.String(required=True)
    message = ma.String(required=True)
    error = ma.String(required=True)



class MLModelSchemaResponse(ma.Schema):
    """Schema defining the attributes after creating new model entry."""
    model_id = ma.String(required=True)
    name = ma.String(required=True)
    version = ma.String(required=True)
    description = ma.String(required=True)
    semantics = ma.String(required=True)

class MLModelSchema(ma.Schema):
    """Schema defining the attributes when creating a new model entry."""
    name = ma.String(required=True)
    version = ma.String(required=True)
    description = ma.String(required=True)
    semantics = ma.String(required=True)

class MlModel():
    def __init__(self, db_path='src/db/db.json'):
        """
        Initialize the connection to the database.
        :param db_path: Path to the TinyDB database file.
        """
        self.db = TinyDB(db_path)
        self.Model = Query()

 

    def add_model(self, name, version, description, semantics):
        """
        Add a new model to the database.
        :param name: Name of the model.
        :param version: Version of the model.
        :param description: A short description of the model.
        :semantics description: Semantic description of the model.
        """
        return self.db.insert({'name': name, 'version': version, 'description': description, 'semantics': semantics})

    def get_model(self, model_id):
        """
        Retrieve a model by its ID.
        :param model_id: The ID of the model to retrieve.
        """
        model = self.db.get(doc_id=model_id)
        if model:
            return model
        else:
            return "Model not found."

    def query_models(self, search_criteria):
        """
        Query models based on a search criteria.
        :param search_criteria: A dictionary with field values to search for.
        """
        results = self.db.search(self.Model.matches(search_criteria))
        return results if results else "No models found matching the criteria."
