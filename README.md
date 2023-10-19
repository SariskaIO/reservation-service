# Sariska Meeting Scheduler

The Sariska Meeting Scheduler is a REST API that allows you to efficiently allocate rooms for meetings while accounting for different time zones and specifying start and stop times. Additionally, the API provides functionality to list current running conferences and upcoming scheduled meetings. This README will guide you through the features and usage of the Sariska Meeting Scheduler.

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
- [Usage Examples](#usage-examples)
- [Contributing](#contributing)
- [License](#license)

## Features

The Sariska Meeting Scheduler API offers the following key features:

1. **Create Room Reservations**: You can create room reservations for meetings, specifying room, date, start time, stop time, and time zone.

2. **Overlapping Reservation Checks**: The system automatically checks for overlapping reservations to prevent scheduling conflicts.

3. **Conference Management**: The API provides functionality to list current running conferences and upcoming scheduled meetings.

## Getting Started

### Prerequisites

Before you begin, ensure you have the following prerequisites:

- An active Sariska Meeting Scheduler API account.
- API credentials (API key, token, etc.).
- A development environment with a tool like Postman or a programming language that can make HTTP requests.

### Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/your-username/sariska-meeting-scheduler.git

   ```

 ```
POST /api/meetings/reserve
{
  "room": "Conference Room A",
  "date": "2023-10-20",
  "start_time": "09:00",
  "stop_time": "10:30",
  "time_zone": "America/New_York"
}

```

```
2.GET /api/conferences/current
    Creating a Room Reservation:
    POST /api/meetings/reserve
    {
      "room": "Conference Room A",
      "date": "2023-10-20",
      "start_time": "09:00",
      "stop_time": "10:30",
      "time_zone": "America/New_York"
    }

```

```
3.GET /api/conferences/current

```
