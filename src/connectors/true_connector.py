import json
from config import settings
from datetime import datetime, timezone
import logging
import requests
from requests.auth import HTTPBasicAuth
import traceback
import uuid
from src.models.policy_model import PolicyModel

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
            template["ids:representation"][0]["ids:instance"][0]["@id"] = "http://w3id.org/engrd/connector/artifact/{0}".format(resource_id)
            template["ids:contractOffer"][0]["ids:permission"][0]["ids:target"]["@id"] = "http://w3id.org/engrd/connector/artifact/{0}".format(resource_id)
            template["ids:contractOffer"][0]["ids:permission"][0]["@id"] = "hellloooo"
            


            template["@context"].update(artifact_semantic["@context"])
            template["cords:mlmetadata"] = artifact_semantic["cords:mlmetadata"]

            new_template = self.create_permisions(resource_id, template)

            return new_template

        except Exception as e:
            logging.error("TrueConnector: An error occurred: %s", str(e))
            traceback.print_exc()
            raise Exception("TrueConnector: An error occurred: %s", str(e))
        
    def create_resource_description(self, resource_id, type, title, description, keywords, artifact_semantic):
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
            _id = "https://w3id.org/idsa/autogen/dataResource/{0}".format(resource_id)
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

            template["ids:representation"][0]["@id"] = "https://w3id.org/idsa/autogen/dataRepresentation/{0}".format(resource_id)
            template["ids:representation"][0]["ids:instance"][0]["@id"] = "https://w3id.org/idsa/autogen/artifact/{0}".format(resource_id)
            template["ids:contractOffer"][0]["ids:permission"][0]["ids:target"]["@id"] = "http://w3id.org/engrd/connector/artifact/cords/{0}".format(resource_id)
            template["ids:contractOffer"][0]["ids:permission"][0]["@id"] = "https://w3id.org/idsa/autogen/permission/{0}".format(resource_id)
            template["ids:contractOffer"][0]["ids:contractStart"]["@value"] = formatted_datetime
            template["ids:contractOffer"][0]["ids:contractDate"]["@value"] = formatted_datetime

            


            template["@context"].update(artifact_semantic["@context"])

            if type == 'model':
                template["cords:mlmetadata"] = artifact_semantic["cords:mlmetadata"]
            elif type == 'fl_service':
                template["cords:flmetadata"] = artifact_semantic["cords:flmetadata"]
            new_template = self.create_permisions(resource_id, template)

            return new_template

        except Exception as e:
            logging.error("TrueConnector: An error occurred: %s", str(e))
            traceback.print_exc()
            raise Exception("TrueConnector: An error occurred: %s", str(e))
        
    
        
    def create_permisions(self,resource_id, current_template):
        policymodel = PolicyModel()

        
        permissions, fl_permissions = policymodel.formalize_policies(resource_id)
        logging.debug("Permissions: %s", permissions)
        logging.debug("FL Permissions: %s", fl_permissions)
        
        logging.info("Generating an ID for contract")
        current_template["ids:contractOffer"][0]["@id"] = "https://w3id.org/idsa/autogen/contractOffer/{0}".format(uuid.uuid4())

        logging.info("Permissions: " + str(permissions))
        # current_template["ids:contractOffer"][0]["ids:permission"] = []


        if len(permissions) > 0:
            for i in range(len(permissions)):
                permission = permissions[i]
                current_template["ids:contractOffer"][0]["ids:permission"].append(permission)
                current_template["ids:contractOffer"][0]["ids:permission"][i]["ids:target"]["@id"] = "http://w3id.org/engrd/connector/artifact/{0}".format(resource_id)
        
        # this is specially for handling federated learnining policies
        if len(fl_permissions) > 0:
             current_template["cords:flpolicies"] = []
             for i in range(len(fl_permissions)):
                fl_permission = fl_permissions[i]
                current_template["cords:flpolicies"].append(fl_permission)
                current_template["cords:flpolicies"][i]["ids:target"]["@id"] = "http://w3id.org/engrd/connector/artifact/{0}".format(resource_id)

        return current_template


        
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

        logging.info("========= Final Resource Description ==============")
        print(resource_description)
        
        # Make the request
        response = requests.post(url, json=resource_description, headers=headers, auth=auth, verify=False)
        
        # Check the response
        if response.status_code == 200:
            logging.info("Request successful!")
            return response.json()  # Assuming the response is JSON
        else:
            logging.error("Failed to send request.")
            logging.error("Status code: %s", str(response.status_code))
            logging.error("Response content: %s", str(response.text))
            return False




