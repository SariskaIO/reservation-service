from flask import Flask, request, jsonify
from flask_api import status
from flask_restx import Api, Resource, fields
from functools import wraps
from flasgger import Swagger
import jwt
import requests
import re
import os
from datetime import datetime
import pytz
from CustomExceptions import ConferenceExists, ConferenceNotAllowed, OverlappingReservation
from Reservation import Base, Reservation
from Conferences import Manager

app = Flask(__name__)
api = Api(app, version='1.0', title='Conference API', description='API for managing conferences')
swagger = Swagger(app)
manager = Manager()
# Define a namespace
conference_ns = api.namespace('/api/v1/scheduler/conference', description='Conference operations')
reservation_ns = api.namespace('/api/v1/scheduler/reservation', description='Reservation operations')
conference_model = api.model('Conference', {
    'id': fields.Integer,
    'mail_owner': fields.String,
    'date': fields.String,
    'location': fields.String,
    'name': fields.String,
    'start_time': fields.String,
    'timezone': fields.String,
    'pin': fields.String,
})

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
                    audience=['media_messaging_co-browsing', 'messaging']
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


@conference_ns.route('')
class Conferences(Resource):
    @token_required
    @conference_ns.marshal_list_with(conference_model)
    def post(self):
        try:
            # If a user enters the conference, check for reservations
            output = manager.allocate(conference_data)
        except ConferenceExists as e:
            # Conference already exists
            return jsonify({'conflict_id': e.id}), status.HTTP_409_CONFLICT
        except ConferenceNotAllowed as e:
            # Confernce cannot be created: user not allowed or conference has not started
            return jsonify({'message': e.message}), status.HTTP_403_FORBIDDEN
        else:
            # Conference was created, send back details
            return jsonify(output), status.HTTP_200_OK

    @token_required
    @api.doc('Get All Conferences')
    @conference_ns.marshal_list_with(conference_model)
    def get(self, current_user):
        # Retrieve a list of all conferences
        conferences = manager.all_conferences(current_user)
        return {'conferences': conferences}

@conference_ns.route('/<id>')
class ConferenceByID(Resource):
    @token_required
    @conference_ns.marshal_list_with(conference_model)
    def get(self, current_user, id):
        # Retrieve a specific conference by its ID
        conference_info = manager.get_conference(id, current_user).get_jicofo_api_dict()
        return conference_info, status.HTTP_200_OK

    @token_required
    @conference_ns.marshal_list_with(conference_model)
    def delete(self, current_user, id):
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
    @api.doc('Get Conference by Name')
    def get(current_user, self, name):
        try:
            conference = manager.get_conference_by_name(name, current_user)
            return conference.get_jicofo_api_dict(), status.HTTP_200_OK
        except Exception as e:
            return {}, status.HTTP_404_NOT_FOUND

@reservation_ns.route('')
class Reservations(Resource):
    @token_required
    @api.doc('Get Reservations')
    @reservation_ns.expect(conference_model)  # Expect JSON data in request
    def get(current_user, self):
        # Replace with your database query to fetch reservations
        print("current_user", current_user)
        reservations = manager.all_reservations(current_user)
        return {'reservations': reservations}

    @token_required
    @api.doc('Create Reservation')
    @reservation_ns.expect(conference_model)  # Expect JSON data in request
    def post(current_user, self):
        data = request.get_json()
        if data is None:
            return {'error': 'Invalid JSON data in request'}, status.HTTP_400_BAD_REQUEST

        validation_errors = validate_reservation_data(data)
        if validation_errors:
            return {'error': 'Validation failed', 'validation_errors': validation_errors}, status.HTTP_400_BAD_REQUEST

        if 'start_time' not in data or 'duration' not in data or 'name' not in data:
            return {'error': 'Missing required fields in JSON data'}, status.HTTP_400_BAD_REQUEST

        data['duration'] *= 60
        try:
            manager.add_reservation(data, current_user)
            return {'message': 'Reservation created successfully'}, status.HTTP_201_CREATED
        except OverlappingReservation as e:
            return {'error': e.message}, status.HTTP_400_BAD_REQUEST

@reservation_ns.route('/<id>')
class Reservation(Resource):
    @token_required
    @api.doc('Delete Reservation')
    @reservation_ns.expect(conference_model)  # Expect JSON data in request
    def delete(current_user, self, id):
        try:
            manager.delete_reservation(id=id, current_user=current_user)
            return {'message': 'Reservation deleted successfully'}, status.HTTP_200_OK
        except Exception as e:
            return {'error': str(e)}, status.HTTP_400_BAD_REQUEST

def validate_reservation_data(data):
    validation_errors = {}

    if 'start_time' not in data:
        validation_errors['start_time'] = 'Start time is required'
    else:
        try:
            datetime.strptime(data['start_time'], '%Y-%m-%dT%H:%M')
        except ValueError:
            validation_errors['start_time'] = 'Invalid datetime format'

    if 'timezone' in data and data['timezone'] not in [tz[0] for tz in pytz.common_timezones]:
        validation_errors['timezone'] = 'Invalid timezone'

    if 'name' not in data:
        validation_errors['name'] = 'Room name is required'
    else:
        name = data['name']
        if not re.match(r'^[a-zA-Z0-9_ -]*$', name):
            validation_errors['name'] = 'Allowed characters for room names are: a-z, 0-9, -, _, and space'

    if 'room_name' not in data:
        validation_errors.append(('room_name', 'Room name is required'))
    else:
        room_name = data['room_name']
        if not re.match(r'^[a-zA-Z0-9_ -]*$', room_name):
            validation_errors.append(('room_name', 'Allowed characters for room names are: a-z, 0-9, -, _, and space'))

    if 'pin' in data:
        pin = data['pin']
        if not re.match(r'^[a-zA-Z0-9]*$', pin):
            validation_errors['pin']

    if 'duration' in data:
        duration = data['duration']
        if not re.match(r'^[1-9]\d*$', duration):
            validation_errors['duration'] = 'Duration should be a positive integer.'


if __name__ == '__main__':
    app.run(debug=True)