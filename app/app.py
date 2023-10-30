from flask import Flask, request, jsonify
from flask_api import status
from flask_restx import Api, Resource, fields, apidoc
from functools import wraps
from flasgger import Swagger, swag_from
import jwt
import requests
import re
import os
from datetime import datetime
import pytz
from CustomExceptions import ConferenceExists, ConferenceNotAllowed, OverlappingReservation
from Reservation import Base, Reservation
from Conferences import Manager
from flask_cors import CORS  # Import Flask-CORS
from flask import Flask, request, Response, g
import uuid
import json
import logging

app = Flask(__name__)
CORS(app)
app.config['RESTX_MASK_SWAGGER'] = False
authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}
logging.basicConfig(level=logging.INFO) 

swagger = Swagger(app)
api = Api(
    app,
    version='1.0',
    base_path="https://api.dev.sariska.io",
    host="api.dev.sariska.io",  # Update the host URL
    title='Conference API',
    description='API for managing conferences',
    authorizations=authorizations,
    terms_url='https://www.sariska.io/terms-of-service',
    base_url='https://api.dev.sariska.io'  # Set the base URL for Swagger
)
manager = Manager()

# Define a namespace
# Define a new namespace for the token generation route
token_ns = api.namespace('api/v1/misc/generate-token', description='Generate JWT Token')
# Define a model for the request body
token_request_model = api.model('TokenRequest', {
    'apiKey': fields.String(
        description='Please pass apiKey tied to your sariska account',
        required=True,
        example='iufwenufewifweifiuTbddhbdjhjfbjfjwfjwfj'
    ),
    'user': fields.Nested(api.model('User', {
        'id': fields.String(description='User ID of a participant if known', example='ytyVgh'),
        'name': fields.String(description='Name of a participant if known', example='Nick'),
        'email': fields.String(description='Email ID of participant if known', example='nick@gmail.com'),
        'avatar': fields.String(description='Avatar of a participant if known', example='https://some-storage-location/nick.jpg'),
        'moderator': fields.Boolean(description='Is the given participant a moderator', example=False)
    })),
    'exp': fields.String(description='Pass exp claim of JWT token', example='24 hours'),
    'nbf': fields.String(description='Pass nbf claim of JWT token', example=''),
    'scope': fields.String(description='Pass scope of token (messaging, media, sariska, or leave it blank)', example='')
})

# Define the response model
token_response_model = api.model('TokenResponse', {
    'token': fields.String(description='Generated JWT token')
})

reservation_ns = api.namespace('api/v1/scheduler/reservation', description='Reservation operations for upcoming scheduled meetings')
conference_model = api.model('Conference', {
    'id': fields.Integer(
        required=True,
        example=1245,
        description='The id created reservation'
    ),
    'mail_owner': fields.String(
        required=True,
        example='ekefk@ed.dd',
        description='The email address of the conference owner.'
    ),
    'name': fields.String(
        required=True,
        example='myroom123',
        description='The name of the conference room.'
    ),
    'duration': fields.String(
        required=True,
        example=60,  # Sample duration in minutes
        description='The duration of the conference in minutes.'
    ),
    'start_time': fields.DateTime(
        required=True,
        example='2023-09-28T15:08',
        description='The start time of the conference in ISO 8601 format.'
    ),
    'timezone': fields.String(
        required=True,
        example='America/New York',
        default='America/New York',
        description='The timezone of the conference.'
    ),
    'pin': fields.String(
        example='1234',  # Remove required=True for an optional field
        description='The PIN for accessing the conference (optional).'
    ),
})

conference_model_with_only_id = api.model('Conference', {
    'id': fields.Integer(
        required=True,
        example=1245,
        description='The id created reservation'
    )
})

conference_model_without_id = api.model('Conference', {
    'mail_owner': fields.String(
        required=True,
        example='ekefk@ed.dd',
        description='The email address of the conference owner.'
    ),
    'name': fields.String(
        required=True,
        example='myroom123',
        description='The name of the conference room.'
    ),
    'duration': fields.String(
        required=True,
        example=60,  # Sample duration in minutes
        description='The duration of the conference in minutes.'
    ),
    'start_time': fields.DateTime(
        required=True,
        example='2023-09-28T15:08',
        description='The start time of the conference in ISO 8601 format.'
    ),
    'timezone': fields.String(
        required=True,
        example='America/New York',
        default='America/New York',
        description='The timezone of the conference.'
    ),
    'pin': fields.String(
        example='1234',  # Remove required=True for an optional field
        description='The PIN for accessing the conference (optional).'
    ),
})

conference_ns = api.namespace('api/v1/scheduler/conference', description='Conference operations for currently running conferences')

def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            token = request.headers['Authorization']

        if not token:
            return jsonify({'message': 'A valid token is missing'})

        try:
            # Get the header data from the token
            header = jwt.get_unverified_header(token.split(' ')[1])
            if not header.get('kid'):
                return jsonify({'message': 'Token is invalid'})

            # Construct the public key URL based on 'kid' and fetch the public key data
            public_key_url = os.getenv("SECRET_MANAGEMENT_SERVICE_PUBLIC_KEY_URL")+"/"+header["kid"]+'.pem'
            response = requests.get(public_key_url)

            if response.status_code == 200:
                # Verify and decode the token
                decoded_token = jwt.decode(
                    token.split(' ')[1],
                    response.content,
                    algorithms=[header['alg']],
                    issuer='sariska',
                    audience=['media_messaging_co-browsing', 'media']
                )
                # Return the decoded token to the decorated function
                return f(decoded_token, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'})
        except jwt.InvalidTokenError:
            return jsonify({'message': public_key_data})
        except Exception as e:
            return jsonify({'message': e})

    return decorator

# Route to generate a JWT token
@token_ns.route('')
class GenerateToken(Resource):
    @api.expect(token_request_model)
    @api.marshal_with(token_response_model)
    def post(self):
        return {'message': 'Token generation route is documented in Swagger'}, status.HTTP_200_OK

# ... (the rest of your Flask app code)
@conference_ns.route('')
class Conferences(Resource):
    @token_required
    @api.doc('Get All Conferences', security='apikey')
    @api.marshal_with(conference_model, as_list=True)
    def get(current_user, self):
        # Retrieve a list of all conferences
        conferences = manager.all_conferences(current_user)
        print("conferences", conferences)
        return conferences

    @token_required
    @api.doc(False)
    def post(current_user, self):
        conference_data = request.get_json()
        print("current_user, self", conference_data, current_user)
        try:
            # If a user enters the conference, check for reservations
            output = manager.allocate(conference_data, current_user)
            return output
        except ConferenceExists as e:
            # Conference already exists
            return jsonify({'conflict_id': e.id}), status.HTTP_409_CONFLICT
        except ConferenceNotAllowed as e:
            # Confernce cannot be created: user not allowed or conference has not started
            return jsonify({'message': e.message}), status.HTTP_403_FORBIDDEN
        else:
            # Conference was created, send back details
            return jsonify(output), status.HTTP_200_OK

@conference_ns.route('/<id>')
class ConferenceByID(Resource):
    @token_required
    @api.doc('Get Conferences by Id', security='apikey')
    @conference_ns.marshal_list_with(conference_model)
    def get(current_user, self, id):
        # Retrieve a specific conference by its ID
        conference_info = manager.get_conference(id, current_user).get_jicofo_api_dict()
        return conference_info, status.HTTP_200_OK

    @token_required
    @api.doc(False)
    def delete(current_user, self,  id):
        # Delete a conference by its ID
        try:
            if manager.delete_conference(id=id, current_user=current_user):
                return {'status': 'OK'}, status.HTTP_200_OK
            else:
                return {'status': 'Failed'}, status.HTTP_403_FORBIDDEN
        except Exception as e:
            return {'error': str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR

@conference_ns.route('/room/<name>')
class ConferenceByName(Resource):
    @token_required
    @api.marshal_with(conference_model)
    @api.doc('Get Conference by Name', security='apikey')
    def get(current_user, self, name):
        try:
            conference = manager.get_conference_by_name(name, current_user)
            return conference.get_jicofo_api_dict(), status.HTTP_200_OK
        except Exception as e:
            return {}, status.HTTP_404_NOT_FOUND

@reservation_ns.route('')
class Reservations(Resource):
    @token_required
    @api.doc('Get Reservations', security='apikey')
    @api.marshal_with(conference_model, as_list=True)
    def get(current_user, self):
        # Replace with your database query to fetch reservations
        print("current_user", current_user)
        app.logger.info('Request received for get reservataion')  # Log a message
        reservations = manager.all_reservations(current_user)
        print("reservations", reservations)
        return reservations

    @token_required
    @api.doc('Create Reservation', security='apikey')
    @reservation_ns.expect(conference_model_without_id)
    @api.marshal_with(conference_model)
    def post(current_user, self):
        data = request.get_json()
        app.logger.info('Request received for create reservataion')  # Log a message
        if data is None:
            return {'error': 'Invalid JSON data in request'}, status.HTTP_400_BAD_REQUEST

        app.logger.info('data', data)  # Log a message
        
        validation_errors = validate_reservation_data(data)
        if validation_errors:
            return {'error': 'Validation failed', 'validation_errors': validation_errors}, status.HTTP_400_BAD_REQUEST

        if 'start_time' not in data or 'duration' not in data or 'name' not in data:
            return {'error': 'Missing required fields in JSON data'}, status.HTTP_400_BAD_REQUEST

        data['duration'] = 60*int(data['duration'])
        try:
            response = manager.add_reservation(data, current_user)
            return response, status.HTTP_201_CREATED
        except OverlappingReservation as e:
            return {'error': e.message}, status.HTTP_400_BAD_REQUEST

@reservation_ns.route('/<id>')
class Reservation(Resource):
    @token_required
    @api.doc('Delete Reservation by Id',security='apikey')
    @api.marshal_with(conference_model_with_only_id, as_list=False)
    def delete(current_user, self, id):
        try:
            manager.delete_reservation_by_id(id=id, name=None, current_user=current_user)
            return {'id': id}, status.HTTP_200_OK
        except Exception as e:
            return {'error': str(e)}, status.HTTP_400_BAD_REQUEST

    @token_required
    @api.doc('Get Reservation by Id', security='apikey')
    @conference_ns.marshal_with(conference_model)
    def get(current_user, self, id):
        # Retrieve a specific reservation by its ID
        print(current_user, id)
        conference_info = manager.get_reservation_by_id(id, current_user).get_jicofo_api_dict()
        return conference_info, status.HTTP_200_OK

@reservation_ns.route('/room/<name>')
class Reservation(Resource):
    @token_required
    @api.doc('Get Reservation by name', security='apikey')
    @conference_ns.marshal_with(conference_model)
    def get(current_user, self, name):
        # Retrieve a specific reservation by its name
        conference_info = manager.get_reservation(None, name, current_user).get_jicofo_api_dict()
        return conference_info, status.HTTP_200_OK


def validate_reservation_data(data):
    validation_errors = {}

    if 'start_time' not in data:
        validation_errors['start_time'] = 'Start time is required'
    else:
        try:
            datetime.strptime(data['start_time'], '%Y-%m-%dT%H:%M')
        except ValueError:
            validation_errors['start_time'] = 'Invalid datetime format'

    print("data", data)

    if 'timezone' in data and data['timezone'].replace(' ', '_') not in pytz.common_timezones:
        validation_errors['timezone'] = 'Invalid timezone'

    if 'name' not in data:
        validation_errors['name'] = 'Room name is required'
    else:
        name = data['name']
        if not re.match(r'^[a-zA-Z0-9_ -]*$', name):
            validation_errors['name'] = 'Allowed characters for room names are: a-z, 0-9, -, _, and space'
            
    if 'pin' in data:
        pin = data['pin']
        if not re.match(r'^[a-zA-Z0-9]*$', pin):
            validation_errors['pin']

    if 'duration' in data:
        duration = data['duration']
        if not isinstance(duration, int):
            validation_errors['duration'] = 'Duration should be an integer.'
        elif duration < 0:
            validation_errors['duration'] = 'Duration should be a non-negative integer.'


@app.after_request
def after_request(resp):
    if 'swagger.json' in request.url:
        original_data = json.loads(resp.get_data())
        # Modify the JSON data as needed
        value = os.environ.get("DEPLOYMENT_ENV")
        if value == "development":
            original_data["host"] = "api.dev.sariska.io"
        elif value == "production":
            original_data["host"] = "api.sariska.io"
        # Serialize the modified data back to JSON
        modified_data = json.dumps(original_data)
        # Create a new response object with the modified JSON data
        new_resp = app.response_class(
            response=modified_data,
            status=resp.status,
            headers=resp.headers,
            content_type=resp.content_type
        )
        return new_resp
    return resp    

if __name__ == '__main__':
    app.run(debug=True)