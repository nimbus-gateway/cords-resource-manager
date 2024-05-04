import json
from config import settings
from datetime import datetime
import logging

class TrueConnector:
    def __init__(self, url, proxy):
        """
        Initializes a new instance of the TrueConnector class.

        :param url: The URL associated with the connector.
        :param proxy: The proxy URL to be used with the connector.
        """
        self.connector_url = url
        self.connector_proxyurl = proxy

    def create_resource_description_template(self):
        """
        Reads a JSON file to use as a template for resource descriptions.

        :return: A dictionary object representing the JSON template.
        :raises FileNotFoundError: If the 'true_connector_resource.json' file cannot be found.
        :raises json.JSONDecodeError: If the file is not valid JSON.
        """
        try:
            with open(settings.TRUE_CONNECTOR_TEMPLATE, 'r') as file:
                template = json.load(file)
            return template
        except FileNotFoundError:
            raise FileNotFoundError("True Connector: The template file for True Connector was not found.")
        except json.JSONDecodeError:
            raise json.JSONDecodeError("True Connector: Failed to decode JSON from the file.")
        except Exception as e:
            raise Exception(f"An error occurred: {str(e)}")
        
        
    def create_model_resource_description(self, resource_id, title, description, keywords, artifact_semantic):
        """
        Creates a resource description for a model using the provided title, keywords, and artifact semantic.
        The method formats these inputs into a structured dictionary that can be used as metadata for model management.

        :param resource_id: Unique identification for the .
        :param title: A string representing the title of the model.
        :param keywords: A list of strings representing keywords associated with the model.
        :param artifact_semantic: An object containing the semantic description of the artifiact 
        
        :return: A dictionary object representing the resource description with keys for title, keywords, and artifact semantic.
        """
        try:
            template = self.create_resource_description_template()
            _id = "https://w3id.org/idsa/autogen/dataResource/cords_{0}".format(resource_id)
            created = datetime.now().isoformat()
            
            template["@id"] = _id
            template["ids:created"]["@value"] = created
            template["ids:description"][0]["@value"] = description
            template["ids:title"][0]["@value"] = title
            
            keyword_temp = {
                "@type": "http://www.w3.org/2001/XMLSchema#string",
                "@value": ""
            }

            for word in keywords:
                keyword_temp["@value"] = word
                template["ids:keyword"].append(keyword_temp)

            # template["ids:representation"][0]["@id"] = "https://w3id.org/idsa/autogen/dataRepresentation/cords_{0}".format(resource_id)
            # template["ids:representation"][0]["ids:instance"][0]["@id"] = "http://w3id.org/engrd/connector/artifact/cords/{0}".format(resource_id)
            # template["ids:representation"][0]["ids:instance"][0]["@id"]["ids:creationDate"]["@value"] = ""

            template["@context"].update(artifact_semantic["@context"])
            template["cords:mlmetadata"] = artifact_semantic["cords:mlmetadata"]

            return template

        except Exception as e:
            logging.error("TrueConnector: An error occurred: %s", str(e))
            raise Exception("TrueConnector: An error occurred: %s", str(e))
        




