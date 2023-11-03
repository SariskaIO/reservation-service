
## ACCESS SWAGGER UI: [here](https://scheduler.dev.sariska.io/)

## Features

The Sariska Meeting Scheduler API offers the following key features:

1. **Create Room Reservations**: You can create room reservations for meetings, specifying room, date, start time, stop time, and time zone.

2. **Overlapping Reservation Checks**: The system automatically checks for overlapping reservations to prevent scheduling conflicts.

3. **Conference Management**: The API provides functionality to list current running conferences and upcoming scheduled meetings.

## API Documentation

You can access the Swagger documentation for the Sariska Meeting Scheduler API [here](https://scheduler.dev.sariska.io/). The Swagger documentation provides detailed information on available endpoints, request and response formats, and example usage.

Please refer to the Swagger documentation for complete API reference and usage instructions.


## Workflow

1. Check if the conference already exists (e.g., Conference xyz already exists).

2. If a reservation exists:
   
   a. Check if the owner is the same as the user who created the reservation. If not, display: "This user is not allowed to start this conference!"

   b. If the conference has not started yet, show: "The conference has not started yet."

3. If no reservation exists, proceed to create one.

## Reservation Fields

### mail_owner:
   - Represents the user ID of the user creating the reservation, e.g., 108118294675469988012@sariska.io.

### name:
   - Represents the room name or conference name.

### duration:
   - Represents the duration of the conference.

### start_time:
   - Represents the start time of the conference in the format of date and time.

### timezone:
   - Represents the time zone of the user creating the reservation. [Check here](https://gist.github.com/brajendrak00068/09f938a4cd63a064dfb459e10948ceb9) for a list of supported time zones.

### pin:
   - Conference PIN (if any).


## Development Quick Start

If you're looking to develop with the Sariska Meeting Scheduler API, here are some quick commands to get you started:

**Set the Environment to Development:**
```bash

cd app

export FLASK_ENV=development

flask run

```
## Production Deployment

```bash 

cd app

export FLASK_ENV=production

```

## Docker Deployment

For containerized deployments, refer to the Makefile for instructions and commands on building and running your Docker containers.

We hope this brief guide helps you get started with the Sariska Meeting Scheduler API. For in-depth details and examples, please refer to our Swagger documentation. If you have any questions or need further assistance, feel free to reach out to our support team. Happy scheduling!

## Screenshots


![AG Grid demo](https://s3.ap-south-1.amazonaws.com/sariska.io/Screenshot+2023-10-31+at+8.20.51+PM.png)

