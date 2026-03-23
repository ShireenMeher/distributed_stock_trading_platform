## Features

- Leader election among replicas
- Replication and synchronization of order data
- Fault-tolerant recovery on crash and restart
- Transparent failover from the client’s perspective
- Frontend LRU cache layer with latency logging
- Functional and crash failure test scripts

### Prerequisites

- Docker
- Docker Compose
- Python 3.10+ (for running standalone clients/scripts)

### Build & Run

To build and start the application:
```bash
docker-compose up --build
```

By default, this brings up:
- frontend_service
- catalog_service
- order_service_{1,2,3}

## Testing
- Uncomment the tests_runner service in docker-compose.yml.
- run ```docker-compose up --build```
- comment it back to avoid unnecessary runs

## Crash Failure Simulation
- Uncomment the client service in docker-compose.yml.
- chose "simulate_crash_with_leader.sh" in the cms in docker-compose.yml
- run this command to execute the scenario:  ``` docker-compose build client && docker-compose up client```
- Leader crash and recovery
- Random follower crashes
- Validation of order consistency using logs

## Replica Restart Sync Test
- Uncomment the client service in docker-compose.yml.
- chose "replica_stop_and_restart_test.sh" in the cms in docker-compose.yml
- run this command to execute the scenario:  ``` docker-compose build client && docker-compose up client```
- Stops a follower
- Places a trade while it’s down
- Restarts it
- Validates that the follower has correctly synced the missed transaction

## Cache Latency Experiments
- Uncomment the client service in docker-compose.yml.
- chose "cache_latencies.sh" in the cms in docker-compose.yml
- run this command to execute the scenario:  ``` docker-compose build client && docker-compose up client```
- Runs multiple client instances with varying probabilities (p) of using cached data
- Logs latency data
- makes a cache eviction plot to visualise the lru cache implementation