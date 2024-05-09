import json
from config import settings
from datetime import datetime, timezone
import logging
import requests
from requests.auth import HTTPBasicAuth
import traceback
import uuid

cert_path = "certs/cert.pem"

class TrueConnector:
    def __init__(self):
        """
        Initializes a new instance of the TrueConnector class.

        :param url: The URL associated with the connector.
        :param proxy: The proxy URL to be used with the connector.
        """
        self.connector_url = None
        self.connector_proxyurl = None

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
            _id = "https://w3id.org/idsa/autogen/dataResource/cords_{0}".format(str(uuid.uuid4()))
            created = datetime.now(timezone.utc)

            formatted_datetime = created.isoformat(timespec='milliseconds').replace("+00:00", "Z")



            # 2024-03-25T08:34:20.557Z

            # 2024-05-07T12:42:23.022064
            
            template["@id"] = _id
            template["ids:created"]["@value"] = formatted_datetime
            template["ids:modified"]["@value"] = formatted_datetime
            template["ids:description"][0]["@value"] = description
            template["ids:title"][0]["@value"] = title
            template["ids:representation"][0]["ids:created"]["@value"] = formatted_datetime
            template["ids:representation"][0]["ids:instance"][0]["ids:creationDate"]["@value"] = formatted_datetime
            
            
            for word in keywords:
                keyword_temp = {
                    "@type": "http://www.w3.org/2001/XMLSchema#string",
                    "@value": word
                }

                template["ids:keyword"].append(keyword_temp)

            template["ids:representation"][0]["@id"] = "https://w3id.org/idsa/autogen/dataRepresentation/cords_{0}".format(resource_id)
            template["ids:representation"][0]["ids:instance"][0]["@id"] = "{0}".format(resource_id)
            # template["ids:representation"][0]["ids:instance"][0]["@id"]["ids:creationDate"]["@value"] = ""

            template["@context"].update(artifact_semantic["@context"])
            template["cords:mlmetadata"] = artifact_semantic["cords:mlmetadata"]

            return template

        except Exception as e:
            logging.error("TrueConnector: An error occurred: %s", str(e))
            traceback.print_exc()
            raise Exception("TrueConnector: An error occurred: %s", str(e))
        
    def register_resource(self, resource_description, catalog):
        url = "{0}/api/offeredResource/".format(settings.TRUE_CONNECTOR_SD_URL)
        logging.debug("catolog id is %s", catalog)
        headers = {
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "catalog": catalog
        }
        # Encode credentials for basic auth
        auth = HTTPBasicAuth(settings.TRUE_CONNECTOR_API_USER_NAME, settings.TRUE_CONNECTOR_API_PASSWORD)

        print(resource_description)
        
        # Make the request
        response = requests.post(url, json=resource_description, headers=headers, auth=auth, verify=False)
        
        # Check the response
        if response.status_code == 200:
            logging.debug("Request successful!")
            return response.json()  # Assuming the response is JSON
        else:
            logging.error("Failed to send request.")
            logging.error("Status code: %s", str(response.status_code))
            logging.error("Response content: %s", str(response.text))
            return False




