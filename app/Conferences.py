from typing import Union
from CustomExceptions import ConferenceExists, OverlappingReservation
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy import between, or_, create_engine
from sqlalchemy.ext.declarative import declarative_base
import logging
import os
from Reservation import Base, Reservation
Session = sessionmaker()

class Manager:
    def __init__(self): 
        self.__logger = logging.getLogger()
        engine = create_engine(os.environ['RESERVATION_SERVICE_DATABASE_URL'], echo=False)
        Base.metadata.create_all(engine)
        Session.configure(bind=engine)
        self.session = Session()

    def all_reservations(self, current_user = None) -> list:
        """Get all reservations as dict"""
        owner_id = current_user['context']['group']

        filter = self.session.query(Reservation) \
            .filter(Reservation.owner_id == owner_id) \
            .filter(Reservation.active == False) \
            .order_by(Reservation.id)
        return filter.all()

    def all_conferences(self, current_user = None) -> list:
        """Get all conferences as dict"""
        owner_id = current_user['context']['group']
        filter = self.session.query(Reservation) \
            .filter(Reservation.active == True) \
            .filter(Reservation.owner_id == owner_id) \
            .order_by(Reservation.id)
        return filter.all()

    def allocate(self, data: dict, current_user = None)-> dict:
        """Check if the conference request matches a reservation."""
        name = data.get('name')

        # Check for conflicting conference
        event = self.get_conference_without_owner_id(name=name, current_user=current_user)
        print("get_conference_without_owner_id event", event)
        if event:
            self.__logger.info(f'Conference {event.id} already exists')
            raise ConferenceExists(event.id)

        # Check for existing reservation
        event = self.get_reservation_without_owner_id(name=name, current_user=current_user)
        print("get_conference_without_owner_id event for get_reservation_without_owner_id", event)
        if event:
            # Raise ConferenceNotAllowed if necessary
            event.check_allowed(owner=data.get('mail_owner'), start_time=data.get('start_time'))
            self.__logger.debug(f'Reservation for room {name} checked, conference can start.')
            event.active = True
            self.session.commit()
        else:
            self.__logger.debug(f'No reservation found for room {name}')
            event = self.add_conference(data=data, current_user=current_user)
            # Check for overlapping reservations for PostgreSQL
            self.check_overlapping_reservations(event, current_user)
        data = event.get_jicofo_api_dict()
        print("get_conference_without_owner_id event for data", str(data))
        return data

    def delete_conference(self, id: int = None, name: str = None, current_user=None) -> bool:
        """Delete a conference in the database"""
        event = self.session.query(Reservation) \
            .filter(Reservation.id == id) \
            .filter(Reservation.active == True) \
            .first()

        if event is None:
            self.__logger.error('Delete failed, could not find conference in the database')
            return False

        self.session.delete(event)
        self.session.commit()
        return True

    def add_conference(self, data: dict, current_user = None) -> str:
        """Add a conference to the database"""
        event = Reservation().from_dict(data, current_user)
        event.active = True
        self.session.add(event)
        self.session.commit()
        self.__logger.debug(f'Add conference {event.id} - {event.name} to the database')
        return event


    def get_conference_without_owner_id(self, id: int = None, name: str = None, current_user = None) -> Union[Reservation, None]:
        """Get the conference information"""
        owner_id = current_user['context']['group']

        return self.session.query(Reservation) \
            .filter(Reservation.name == name) \
            .filter(Reservation.active == True) \
            .first()

    def get_conference(self, id: int = None, name: str = None, current_user = None) -> Union[Reservation, None]:
        """Get the conference information"""
        owner_id = current_user['context']['group']

        return self.session.query(Reservation) \
            .filter(Reservation.name == name) \
            .filter(Reservation.owner_id == owner_id) \
            .filter(Reservation.active == True) \
            .first()

    def get_conference_by_name(self, name: str = None, current_user = None) -> Union[Reservation, None]:
        """Get the conference information by conference name"""
        owner_id = current_user['context']['group']

        return self.session.query(Reservation) \
            .filter(Reservation.name == name) \
            .filter(Reservation.owner_id == owner_id) \
            .filter(Reservation.active == True) \
            .first()

    def delete_reservation(self, id: int = None, name: str = None, current_user = None) -> bool:
        owner_id = current_user['context']['group']

        """Delete a reservation in the database"""
        event = self.session.query(Reservation) \
            .filter(Reservation.owner_id == owner_id) \
            .filter(Reservation.name == name) \
            .first()

        if event is None:
            self.__logger.error('Delete failed, could not find reservation in the database')
            return False

        self.session.delete(event)
        self.session.commit()
        return True

    def delete_reservation_by_id(self, id: int = None, name: str = None, current_user = None) -> bool:
        owner_id = current_user['context']['group']

        """Delete a reservation in the database"""
        event = self.session.query(Reservation) \
            .filter(Reservation.id == id) \
            .first()

        if event is None:
            self.__logger.error('Delete failed, could not find reservation in the database')
            return False

        self.session.delete(event)
        self.session.commit()
        return True

    def get_reservation_without_owner_id(self, id: int = None, name: str = None, current_user = None) -> Union[Reservation, None]:
        """Get the reservation information"""
        return self.session.query(Reservation) \
            .filter(Reservation.name == name) \
            .filter(Reservation.active == False) \
            .first()


    def get_reservation(self, id: int = None, name: str = None, current_user = None) -> Union[Reservation, None]:
        """Get the reservation information"""
        owner_id = current_user['context']['group']

        return self.session.query(Reservation) \
            .filter(Reservation.owner_id == owner_id) \
            .filter(Reservation.name == name) \
            .filter(Reservation.active == False) \
            .first()

    def get_reservation_by_id(self, id: int = None, current_user = None) -> Union[Reservation, None]:
        """Get the reservation information"""
        owner_id = current_user['context']['group']
        print("id,,,,,,,,,,,,,,,", id, current_user)
        return self.session.query(Reservation) \
            .filter(Reservation.owner_id == owner_id) \
            .filter(Reservation.id == id) \
            .filter(Reservation.active == False) \
            .first()

    def add_reservation(self, data: dict, current_user = None) -> int:
        """Add a reservation to the database."""
        event = Reservation().from_dict(data, current_user=current_user)
        # Check if this reservation overlaps with other reservations (same name)
        self.check_overlapping_reservations(event, current_user)
        # Check if this reservation might start before active conferences with the same name end.
        self.check_overlapping_conference(event, current_user)

        print("add_reservation", event)
        print("add_reservation", event.start_time)
        print("timezone", event.timezone)

        self.session.add(event)
        self.session.commit()
        self.__logger.debug(f'Add reservation for room {event.name} to the database')

        return event

    def check_overlapping_conference(self, event: Reservation, current_user) -> bool:
        """Check if start and end time of the new entry overlap with an existing reservation."""
        owner_id = current_user['context']['group']
        time_filter = between(event.start_time, Reservation.start_time, Reservation.end_time)
        result = self.session.query(Reservation) \
                             .filter(Reservation.name == event.name) \
                             .filter(time_filter) \
                             .filter(Reservation.active is True) \
                             .first()

        if result is not None:
            message = f'A conference with this name currently exists. Your reservation can only \
                        start once the event is over, which will be at {result.end_time_formatted}'
            raise ConferenceExists(message=message)

        return True

    def check_overlapping_reservations(self, event: Reservation, current_user) -> bool:
        """Check if start time of the new entry overlaps with existing conferences."""
        owner_id = current_user['context']['group']
        results = self.session.query(Reservation) \
                             .filter(Reservation.name == event.name) \
                             .filter(event.start_time <= Reservation.end_time) \
                             .filter(event.end_time >= Reservation.start_time) \
                             .filter(Reservation.active is False)

        if results.count():
            raise OverlappingReservation(events=results.all())

        return True