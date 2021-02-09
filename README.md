# Jire: Jitsi Reservation System

From [github.com/jitsi/jicofo](https://github.com/jitsi/jicofo/blob/master/doc/reservation.md):

It is possible to connect Jicofo to external conference reservation system using REST API. Before new Jitsi-meet conference is created reservation system will be queried for room availability. The system is supposed to return positive or negative response which also contains conference duration. Jicofo will enforce conference duration and if the time limit is exceeded the conference will be terminated. If any authentication system is enabled then user's identity will be included in the reservation system query.

Jire does this for you.

![Screenshot of the configuration interface](screenshot.png)


## Use with Docker

```
docker build -t jire:latest .
docker run -v "$(pwd)"/log:/usr/src/app/log -p 8080:8080 jire:latest
```

### Configure Jitsi-meet

If you use [docker-jitsi-meet](https://github.com/jitsi/docker-jitsi-meet) you need to change the following lines in `.env`:

```
JICOFO_RESERVATION_ENABLED=true
JICOFO_RESERVATION_REST_BASE_URL=<url-to-your-jire>
```

## Use with gunicorn

```
pip install gunicorn
exec gunicorn -b :8080 main:app
```

## Development

This is a work in progress, pull requests are welcome.

Install with `python setup.py develop` and run with `flask run`.
