from jire import app, manager, csrf
from flask import request, render_template, redirect, url_for, jsonify
from flask_api import status
from .CustomExceptions import ConferenceExists, ConferenceNotAllowed
from .forms import ReservationForm


@app.route('/conferences', methods=['GET'])
def show_conferences():
    return render_template('conferences.html',
                           active_conferences=manager.conferences_formatted)


@app.route('/')
@app.route('/reservations')
def home():
    form = ReservationForm()
    return render_template('reservations.html',
                           form=form,
                           active_reservations=manager.reservations_formatted)


@app.route('/reservation/create', methods=['POST'])
def reservation():
    form = ReservationForm()
    if form.validate_on_submit():
        manager.add_reservation(form.data)
        app.logger.info('New reservation validation successfull')
    else:
        app.logger.info('New reservation validation failed')
        print(form.errors.items())
    return redirect(url_for('home'))


@app.route('/reservation/delete/<id>', methods=['GET'])
def delete_reservation(id):
    manager.delete_reservation(id=id)
    return redirect(url_for('home'))


@app.route('/conference', methods=['POST'])
@csrf.exempt
def conference():

    try:
        # If a user enters the conference, check for reservations
        output = manager.allocate(request.form)
    except ConferenceExists as e:
        # Conference already exists
        return jsonify({'conflict_id': e.id}), status.HTTP_409_CONFLICT
    except ConferenceNotAllowed as e:
        # Confernce cannot be created: user not allowed or conference has not started
        return jsonify({'message': e.message}), status.HTTP_403_FORBIDDEN
    else:
        return jsonify(output), status.HTTP_200_OK


@app.route('/conference/<id>', methods=['GET', 'DELETE'])
@csrf.exempt
def conference_id(id):

    if request.method == 'GET':
        # In case of 409 CONFLICT Jitsi will request information about the conference
        return jsonify(manager.get_conference(id)), status.HTTP_200_OK
    elif request.method == 'DELETE':
        # Delete the conference after it's over
        if manager.delete_conference(id=id):
            return jsonify({'status': 'OK'}), status.HTTP_200_OK
        else:
            return jsonify({
                'status': 'Failed',
                'message': f'Could not remove {id} from database.'
                }), status.HTTP_403_FORBIDDEN
