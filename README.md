Market Data Poller
=====================================

<URL>

How does this work?
----------------

Market Data Poller constantly polls multiple exchanges to extract the latest prices. These price data are then stored in Redis Server to be used by Market Data API.

Application Flow
-------

Client UI <-> Market Data API <-> Redis Server <-> Market Data Poller


Available End points
-------
- NULL

ENV parameters
-------
Available at ./instructions/env.md

## Instructions

To run in development mode:

```bash
$ source venv/bin/activate
$ python ./src/main.py
```

To run in production mode:

```bash
$ nohup python3 src/main.py &
```
