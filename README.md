# Jire: Reservation System for Jitsi Meet

From [github.com/jitsi/jicofo](https://github.com/jitsi/jicofo/blob/master/doc/reservation.md):

It is possible to connect Jicofo to external conference reservation system using REST API. Before new Jitsi-meet conference is created reservation system will be queried for room availability. The system is supposed to return positive or negative response which also contains conference duration. Jicofo will enforce conference duration and if the time limit is exceeded the conference will be terminated. If any authentication system is enabled then user's identity will be included in the reservation system query.

Jire does this for you.
## Features
* Create room reservations
* System checks for overlapping reservations and conferences

### To be implemented
* Edit or reschedule a reservation
* Allow users to login and and manage their own conferences

_Note:_ Conferences created without a reservation are set to a duration of 6 hours by default.

## Run with Docker

```
docker build -t jire:latest .
docker run -v "$(pwd)"/log:/opt/venv/log "$(pwd)"/data:/opt/venv/data -p 8080:8080 jire:latest
```

### Configure Jitsi Meet

If you use [docker-jitsi-meet](https://github.com/jitsi/docker-jitsi-meet) you need to change the following lines in `.env`:

```
JICOFO_RESERVATION_ENABLED=true
JICOFO_RESERVATION_REST_BASE_URL=<url-to-your-jire>
```

If you want to add Jire to your existing docker-jitsi-meet setup you could use the following compose file:

```
version: '3'

services:
  jire:
    image: jire:latest
    restart: unless-stopped
    volumes:
      - ./log:/opt/venv/log
      - ./data:/opt/venv/data
    ports:
      - 127.0.0.1:8080:8080
    environment:
      - PUBLIC_URL=https://meet.example.com

networks:
    default:
        external:
            name: jitsi-meet_meet.jitsi
```

And set the endpoint in `.env` with
```
JICOFO_RESERVATION_REST_BASE_URL=http://jire:8080
```

Restart jicofo and you're good to go.

## Run with gunicorn

```
pip install gunicorn
exec gunicorn -b :8080 main:app
```

## Development

This is a work in progress, pull requests are welcome.

Install with `python setup.py develop` and run with `flask run`.

[![name](link to image on GH)](https://s3.ap-south-1.amazonaws.com/www.sariska.io/Screenshot%202022-10-06%20at%2010.59.14%20PM.png?response-content-disposition=inline&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEDwaCmFwLXNvdXRoLTEiRzBFAiAiDYRqjUljvr6zUVzUzdZbVrGzYYI4So4lBrFvC0RVogIhAMlbYnZPqNQci%2Bjr7oNBePFWPFsv7hItkdOO3sdnkwvoKu0CCPX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEQARoMNzE4NzYyNDk2Njg1Igwpau9j9Hb6b2C4a6MqwQIMbDUPWIfXSdmUqAPwRhm2ppaYeidvCzkiFio9Iwm3LMjCOQ61pfGnOJljkJAuXmCmieu7qHozZelLb7WyOShyGlm9tZesohKJOsOZFatVFebLRD3NACW3p6Cpb5g%2FlgiZMZ9zABT0v49BiIPFYP45%2F%2BW1kePEcpU0IrmZXffFolWag0ElHQe2sT9MjGF%2BM4Rr9DBM6WcKOrXAtbj7NJgn4vKEqoqUECPoXqyqn3lZqQtIPaFpjDkfnwXiVHg4pg5l6iMJ%2Bv362b4Yd%2FRxiu5KG3wLgCwCW148fH9cj%2FkDoP8Ycc3YSSvhuLuBKhs%2FxFUPFbGMAQFHPzWasQBJix2sNl%2Fq8EaJTWrA4nQfqrUR6Dvqzw1nswY7TeGjyWOJtTXaGObGamq3xY9QWIxeJAoAxQQ65HOTfQQjYjQWyT6uwT0wh%2FD8mQY6swLDo0bHaiTj%2B8T%2BgQSJJrd315Buwto15yR2%2FJ0UYNNLaGnZuYuBmIkt1OW3CmS88WGVXM86S%2BO22Z5TLB0LzncXNt9Ucyrjm7NHYLL4DvFFBt9nETe90KuvWv%2BNZ%2B61nFEeqYNO79gnAWNX9480cIjLSCVRBWzVPYl8OsGEZtvCuZ8A4hhDlIucv4tu3jEdYQC92%2FMABJtLpOUCAx%2FkOvZ9osniz%2B8VyCtv9my%2FbXhb0%2BBvTIk0goqfJx%2BqyzmetrUM5vYQ5IUkZ6CEszBO8KQMOQDDn4zZkAI1hrPb3s%2FSjsjEERLh2Dq5KUuXiZe7P4iuQPEi2rVAnF4KXkFzbnbTPPYU%2FVGNdx%2Bfhdzn1eH4IN%2FRX%2F9mHapxCTIALzgEJqB72W8SDvI4DlY5RUDgi3OWcV2p&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20221006T202009Z&X-Amz-SignedHeaders=host&X-Amz-Expires=300&X-Amz-Credential=ASIA2OWMVKKWRSGVOVR6%2F20221006%2Fap-south-1%2Fs3%2Faws4_request&X-Amz-Signature=386d0778ef220514790d1085f7049ffc72afa954684b883383fadf53757e5d57)




