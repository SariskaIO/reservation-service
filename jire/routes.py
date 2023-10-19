from jire import app, manager, csrf
from flask import request, render_template, redirect, url_for, jsonify, flash, json
from flask_api import status
from .CustomExceptions import ConferenceExists, ConferenceNotAllowed, OverlappingReservation
import jwt
import requests

from flask import Flask
from flask_restplus import Resource, Api, fields
from functools import wraps

# Create the Flask app
app = Flask(__name)
api = Api(app, version='1.0', title='Conference API', description='API for managing conferences')

# Define a namespace
ns = api.namespace('conferences', description='Conference operations')

# Define a model for the response data
conference_model = api.model('Conference', {
    'name': fields.String(required=True, description='Conference name'),
    'date': fields.String(required=True, description='Conference date')
})

# Mock data (you can replace this with your actual data)
conferences_data = [
    {'name': 'Conference A', 'date': '2023-10-25'},
    {'name': 'Conference B', 'date': '2023-11-15'},
]



# Define the token_required decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get the token from the request's authorization header
        try:
            authorization_header = request.headers.get('Authorization')
            token = authorization_header.split(" ")[1]
        except (IndexError, AttributeError):
            return jsonify({'message': 'Token is missing or invalid'}), 401

        try:
            # Get the header data from the token
            header = jwt.get_unverified_header(token)
            if not header.get('kid'):
                return jsonify({'message': 'Token is invalid'}), 401

            # Construct the public key URL based on 'kid' and fetch the public key data
            public_key_url = f'{SECRET_MANAGEMENT_SERVICE_PUBLIC_KEY_URL}/{header["kid"]}'  # Replace with your public key service URL
            response = requests.get(public_key_url)

            if response.status_code == 200:
                public_key_data = response.json()
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(public_key_data)

                # Verify and decode the token
                decoded_token = jwt.decode(
                    token,
                    public_key,
                    algorithms=[header['alg']],
                    issuer='sariska',
                    audience=['media_messaging_co-browsing', 'messaging']
                )

                # Return the decoded token to the decorated function
                return f(decoded_token, *args, **kwargs)

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid'}), 401
        except Exception as e:
            return jsonify({'message': 'An error occurred during token verification', 'error': str(e)}), 500

        return jsonify({'message': 'Token is missing or invalid'}), 401

    return decorated

    
@token_required
@api.doc('list_conferences')
@app.route('/conferences', methods=['GET'])
def show_conferences(current_user):
    conferences = manager.all_conferences(current_user)  # Replace with your database query to fetch conferences
    # Assuming conferences is a list of dictionaries or objects that can be easily serialized to JSON
    return jsonify({'conferences': conferences})

@token_required
@api.doc('list_conferences')
@app.route('/reservations')
def show_current_user(current_user):
    reservations = manager.all_reservations(current_user)  # Replace with your database query to fetch reservations
    # Assuming reservations is a list of dictionaries or objects that can be easily serialized to JSON
    print("reservations")
    print(reservations)
    return jsonify({'reservations': reservations})

@token_required
@api.doc('list_conferences')
@app.route('/reservation/create', methods=['POST'])
def create_reservation(current_user):
    data = request.get_json()  # Assuming clients send data as JSON

    if data is None:
        return jsonify({'error': 'Invalid JSON data in request'}), status.HTTP_400_BAD_REQUEST

    # Perform validation on the JSON data
    validation_errors = validate_reservation_data(data)

    if validation_errors:
        return jsonify({'error': 'Validation failed', 'validation_errors': validation_errors}), status.HTTP_400_BAD_REQUEST

    # Validate the JSON data or apply any necessary data transformation
    # Example data structure: {'start_time': '2023-10-18T12:00', 'duration': 15, 'name': 'Sample Room'}
    # Ensure that the required fields are present in the JSON data

    # Example validation:
    if 'start_time' not in data or 'duration' not in data or 'name' not in data:
        return jsonify({'error': 'Missing required fields in JSON data'}), status.HTTP_400_BAD_REQUEST

    # Other data transformations and validation as needed

    data['duration'] *= 60  # Convert minutes to seconds

    try:
        manager.add_reservation(data, current_user)
        return jsonify({'message': 'Reservation created successfully'}), status.HTTP_201_CREATED
    except OverlappingReservation as e:
        return jsonify({'error': e.message}), status.HTTP_400_BAD_REQUEST


@token_required
@api.doc('list_conferences')
@app.route('/reservation/delete/<id>', methods=['DELETE'])
def delete_reservation(current_user, id):
    try:
        manager.delete_reservation(id=id, current_user)
        return jsonify({'message': 'Reservation deleted successfully'}), status.HTTP_200_OK
    except Exception as e:
        # Handle the specific exception that might be raised if the deletion fails.
        # You can customize the error message based on your application's logic.
        return jsonify({'error': str(e)}), status.HTTP_400_BAD_REQUEST

@token_required
@api.doc('list_conferences')
@app.route('/conference', methods=['POST'])
def create_conference(current_user):
    data = request.get_json()  # Assuming clients send data as JSON

    if data is None:
        return jsonify({'error': 'Invalid JSON data in request'}), status.HTTP_400_BAD_REQUEST

    # Validate the JSON data or apply any necessary data transformation
    # Example data structure: {'user_id': '123', 'conference_name': 'MyConference'}
    # Ensure that the required fields are present in the JSON data

    # Example validation:
    if 'user_id' not in data or 'conference_name' not in data:
        return jsonify({'error': 'Missing required fields in JSON data'}), status.HTTP_400_BAD_REQUEST

    # Other data transformations and validation as needed

    try:
        output = manager.allocate(data, current_user)
        return jsonify(output), status.HTTP_200_OK  # Respond with the output from 'manager.allocate'
    except ConferenceExists as e:
        return jsonify({'conflict_id': e.id}), status.HTTP_409_CONFLICT
    except ConferenceNotAllowed as e:
        return jsonify({'message': e.message}), status.HTTP_403_FORBIDDEN


@token_required
@api.doc('list_conferences')
@app.route('/conference/<id>', methods=['GET', 'DELETE'])
def get_or_delete_conference(current_user, id):
    if request.method == 'GET':
        # In case of 409 CONFLICT Jitsi will request information about the conference
        conference_info = manager.get_conference(id).get_jicofo_api_dict()
        return jsonify(conference_info), status.HTTP_200_OK
    elif request.method == 'DELETE':
        # Delete the conference after it's over
        try:
            if manager.delete_conference(id=id, current_user):
                return jsonify({'status': 'OK'}), status.HTTP_200_OK
            else:
                # Jicofo does not seem to care what is sent back
                return jsonify({'status': 'Failed'}), status.HTTP_403_FORBIDDEN
        except Exception as e:
            return jsonify({'error': str(e)}), status.HTTP_500_INTERNAL_SERVER_ERROR

@token_required
@api.doc('list_conferences')
@api.marshal_list_with(conference_model)
@app.route('/room/<name>', methods=['GET', 'OPTIONS'])
def conference_name(current_user, name): 
    res = ""
    try:
        res = manager.get_conference_by_name(name, current_user).get_jicofo_api_dict()
    except Exception as e:
        res = {}

    response = app.response_class(headers={
                                "Access-Control-Allow-Origin": "*",
                                "Access-Control-Allow-Headers": "origin, x-requested-with, content-type",
                                "Access-Control-Allow-Methods":"PUT, GET, POST, DELETE, OPTIONS"
                                },
                                response=json.dumps(res),
                                status=status.HTTP_200_OK,
                                mimetype='application/json')
    return response

def validate_reservation_data(data):
    validation_errors = {}

    # Validate 'start_time'
    if 'start_time' not in data:
        validation_errors['start_time'] = 'Start time is required'
    else:
        try:
            datetime.strptime(data['start_time'], '%Y-%m-%dT%H:%M')
        except ValueError:
            validation_errors['start_time'] = 'Invalid datetime format'

    # Validate 'timezone'
    if 'timezone' in data and data['timezone'] not in [tz[0] for tz in pytz.common_timezones]:
        validation_errors['timezone'] = 'Invalid timezone'

    # Validate 'name'
    if 'name' not in data:
        validation_errors['name'] = 'Room name is required'
    else:
        name = data['name']
        if not re.match(r'^[a-zA-Z0-9_ -]*$', name):
            validation_errors['name'] = 'Allowed characters for room names are: a-z, 0-9, -, _, and space'

    # Validate 'pin'
    if 'pin' in data:
        pin = data['pin']
        if not re.match(r'^[a-zA-Z0-9]*$', pin):
            validation_errors['pin'] = 'Invalid characters in the pin'

    # Validate 'mail_owner'
    if 'mail_owner' in data:
        mail_owner = data['mail_owner']
        if not re.match(r'^\S+@\S+\.\S+$', mail_owner):
            validation_errors['mail_owner'] = 'Invalid email format'

    # Validate 'duration'
    if 'duration' in data:
        try:
            data['duration'] = int(data['duration'])
            if data['duration'] <= 0:
                validation_errors['duration'] = 'Duration must be a positive integer'
        except ValueError:
            validation_errors['duration'] = 'Duration must be a valid integer'

    return validation_errors       