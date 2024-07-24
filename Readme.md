Welcome to the documentation for the CORDS ML Resource API!

## Introduction

The ML Resource Management REST API is an API designed to manage and track machine learning artifacts. This API facilitates the storage, retrieval, and management of artifacts generated during the machine learning workflow, particularly those produced by ML Flow. It also manages semantic descriptions of these ML artifacts to enhance understanding and usability.

## Key Functionality

The ML Resource Management API provides the following functionality:

1. Manage ML Artifacts:
  * Create new entries for ML realted assets along with their meta data. Eg: Data Sets, ML Models and Federated Learning Trainings. 
  * Update existing ML related assets
  * Retrieve and view all ML related assets and who created them
2. Semantic Management:
  * Automatically generate semantic descriptions for ML related assets
  * Update semantic descriptions
  * Query artifacts based on semantic descriptions
3. Integration with ML Flow:
  * Retrieve artifacts linked to specific ML Flow runs
  * Extract the meta data from ML Flow and convert them as ML asset semantics
4. Keep track of Data Space connectors and generate IDSA connector compatible resource descriptions.
  * Register IDS connectors for sharing ML data assets
  * Automatically generate resource descriptions of ML assets to be shared 

## Key Modules

This project is written using Python 3.10.1.

The project utilizes the following modules:

* **Flask**: A micro-framework for web application development, which includes dependencies such as:
  * **click**: A package for creating command-line interfaces (CLI)
  * **itsdangerous**: A library to cryptographically sign your data and files
  * **Jinja2**: A templating engine for Python
  * **MarkupSafe**: Provides XML/HTML markup safe strings
  * **Werkzeug**: A set of utilities for creating WSGI-compatible web applications
* **APIFairy**: An API framework for Flask that enhances API creation and documentation, including:
  * **Flask-Marshmallow**: Integration of Flask and Marshmallow for object serialization and deserialization
  * **Flask-HTTPAuth**: Provides simple HTTP authentication support
  * **apispec**: Generates API specifications that are compliant with the OpenAPI specification
* **Cords Semantic Lib**
  * **Purpose**: A custom library for semantic operations.
  * **Repository**: [Cords Semantic Lib](https://github.com/nimbus-gateway/cords-semantics-lib)

* **MLFlow**: ML Flow Python SDK for connecting with MLFlow server  

## Build From Source

```
docker build -t cords_resource_manager .
docker compose up
```

## Basic Flow 

This API allows the user to prepare the assets to be shared on the Data Space using IDS connectors. It has a feature to extract metadata from MLFlow and convert to a IDS compatible resource description. Finally, when the contract negotation is done ML asset trasfer can be initiated from the API. Once this service is started the API documentation can be accessed from [http://localhost:5000/docs](http://localhost:5000/docs). Use the Resource Manager [Postman Collection](https://github.com/nimbus-gateway/cords-mve/blob/main/CORDS_Resource_Manager_postman_collection.json) to interact with the API.


### 1. Registering a new user for managing ML assets at the provider end.

```
curl -X POST http://localhost:5000/api/users/register \
-H "Content-Type: application/json" \
-H "User-Agent: PostmanRuntime/7.39.0" \
-H "Accept: */*" \
-H "Cache-Control: no-cache" \
-H "Host: localhost:5000" \
-H "Accept-Encoding: gzip, deflate, br" \
-d '{
    "email": "tharindu.prf@gmail.com",
    "password": "password123",
    "first_name": "Tharindu",
    "last_name": "Ranathunga",
    "role": "ML Engineer"
}'
```

### 2. Get auth token to authenticte the other API calls. 

The base64 encorded user name password is added as the header here. 

```
curl -X POST http://localhost:5000/api/users/get-auth-token \
  -H 'Authorization: Basic dGhhcmluZHUucHJmQGdtYWlsLmNvbTpwYXNzd29yZDEyMw==' \
  -H 'User-Agent: PostmanRuntime/7.39.0' \
  -H 'Accept: */*' \
  -H 'Cache-Control: no-cache' \
  -H 'Host: localhost:5000' \
  -H 'Accept-Encoding: gzip, deflate, br' \
  -H 'Connection: keep-alive' \
  -H 'Content-Length: 0'
```
Use the response token of this call to authenticate other calls.

### 3. Register a ML Model as an asset to be shared in the data space. 

More details about the request body can be found in the [API doc](http://localhost:5000/docs) 

```
curl -X POST http://localhost:5000/api/ml_models/add_model \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer LNUDU7YPEeYPcXPXqZPF8jDEiFrVnFmwLTbwYwzxrF8' \
  -H 'User-Agent: PostmanRuntime/7.39.0' \
  -H 'Accept: */*' \
  -H 'Cache-Control: no-cache' \
  -H 'Host: localhost:5000' \
  -H 'Accept-Encoding: gzip, deflate, br' \
  -H 'Connection: keep-alive' \
  -H 'Content-Length: 224' \
  -d '{
    "name": "Test Model 1",
    "version": "1.0",
    "description": "This model is a test model",
    "ml_flow_model_path": "mlflow-artifacts:/208444466607110357/2c8c2fc3fefe4c56a29ac325c0bac39c/artifacts/knnmodel"
}'
```

### 4. Register a data space connector for sharing assets
```
curl -X POST http://localhost:5000/api/dataspace_connector/add_connector \
  -H 'Content-Type: application/json' \
  -H 'Accept: */*' \
  -H 'Cache-Control: no-cache' \
  -H 'Accept-Encoding: gzip, deflate, br' \
  -H 'Connection: keep-alive' \
  -H 'Content-Length: 504' \
  -d '{
    "id": "https://w3id.org/engrd/connector/provider21",
    "name": "CORDS True Connector",
    "type": "ids:BaseConnector",
    "description": "Data Provider Connector description",
    "public_key": "TUlJREdqQ0NBcCtnQXdJQkFnSUJBVEFLQmdncWhrak9QUVFEQWpCTk1Rc3dDUVlEVlFRR0V3SkZVekVNTUFvR0ExVUVDZ3dEVTFGVE1SQXdEZ1lEVlFRTERBZFVaWE4wVEdGaU1SNHdIQVlEVlFRRERCVlNaV1psY21WdVkyVlVaWE4wWW1Wa1U=",
    "access_url": "https://89.19.88.88:8449/",
    "reverse_proxy_url": "https://localhost:8184/proxy"
}'
```


### 4. Creating a resource to be shared in data space. 

This could be a ML model, Raw Data Dump or a Federated Learning Training (Refered by the asset_id). In this version only ML models are supported to be registered as a resource.
This also link to the prefered data space connector that the resource will be shared. 

```
curl -X POST http://localhost:5000/api/dataspace_resource/create_resource \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer LNUDU7YPEeYPcXPXqZPF8jDEiFrVnFmwLTbwYwzxrF8' \
  -H 'User-Agent: PostmanRuntime/7.39.0' \
  -H 'Accept: */*' \
  -H 'Cache-Control: no-cache' \
  -H 'Host: localhost:5000' \
  -H 'Accept-Encoding: gzip, deflate, br' \
  -H 'Connection: keep-alive' \
  -H 'Content-Length: 224' \
  -d '{
    "asset_id": "344f0e124bfb7363651bb080c3ca36f43a23094ab6566e1943f7592b7ff620e9",
    "connector_id": "https://w3id.org/engrd/connector/provider21",
    "resource_id": "1b2888f8c6032ee0223373cab9c62380f594e22435170b9cad8a62769d8810ea",
    "timestamp": "2024-05-31T13:37:55.708378",
    "type": "model"
}'
```



### 5. Register the resource on IDS Connector.

This will create the resource description using the IDS Information model. Moreover, metadata of the shared resource (Eg: ML semantics) are embeded to the resource description using the CORDS ontology.  

```
curl -X POST http://localhost:5000/api/dataspace_connector/register_resource/1b2888f8c6032ee0223373cab9c62380f594e22435170b9cad8a62769d8810ea \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer LNUDU7YPEeYPcXPXqZPF8jDEiFrVnFmwLTbwYwzxrF8' \
  -H 'User-Agent: PostmanRuntime/7.39.0' \
  -H 'Accept: */*' \
  -H 'Cache-Control: no-cache' \
  -H 'Host: localhost:5000' \
  -H 'Accept-Encoding: gzip, deflate, br' \
  -H 'Connection: keep-alive' \
  -H 'Content-Length: 224' \
  -d '{
    "title": "Example IDS Resource1",
    "description": "This is an example IDS Resource",
    "keywords": ["cords", "energy prediction"],
    "catalog_id": "https://w3id.org/idsa/autogen/resourceCatalog/1ce75044-fd7d-4002-9117-051c7005f4ba"
}'
```

