# Distributed Stock Trading System

A fault-tolerant, distributed stock trading platform built using microservices, featuring **replication, leader election, and Paxos-based consensus** to ensure consistency under failures.

---

## Highlights

- Replicated Order Service with leader election
- **Paxos-based consensus for consistent order replication**
- Fault-tolerant system with automatic failover
- Replica sync & recovery after crashes
- Microservices architecture (Frontend, Catalog, Order)
- Concurrent request handling (thread-per-session)
- LRU Cache layer with latency benchmarking
- Dockerized deployment
- Load testing + failure simulations

---

## System Architecture

- **Frontend Service**
  - Routes requests to leader replica
  - Handles failover transparently

- **Catalog Service**
  - Manages stock data (price, quantity)
  - Thread-safe updates with persistence

- **Order Service (Replicated)**
  - 3 replicas
  - Leader-based coordination
  - **Paxos consensus ensures all replicas agree on order sequence**

---

## Core Concepts

- Leader election & failover  
- Replication via propagation + sync  
- **Paxos (Proposer, Acceptor, Learner roles)**  
- Eventual + consensus-based consistency  
- Distributed request routing  
- Caching + latency optimization  
- Crash recovery & state reconciliation  

---

## Paxos Implementation

- Each replica acts as:
  - **Proposer (leader)**
  - **Acceptor**
  - **Learner**

- Workflow:
  1. **Prepare Phase** → Leader proposes with proposal number  
  2. **Promise Phase** → Majority accepts proposal  
  3. **Accept Phase** → Value (order) proposed  
  4. **Learn Phase** → All replicas commit the order  

- Ensures:
  - Strong agreement across replicas  
  - Consistent ordering of transactions  
  - Fault tolerance under node failures  

---

## Getting Started

### Prerequisites
- Docker
- Docker Compose
- Python 3.10+

### Run the system

```bash
docker-compose up --build
```

### Services started:

- frontend_service
- catalog_service
- order_service_1,2,3

## Testing & Experiments

### Functional + Unit Testing

- Covers trade + lookup flows
- Includes failure scenarios

### Crash Failure Simulation

Simulates:

- Leader crash & re-election
- Random replica failures
- Data consistency validation

```bash
docker-compose build client && docker-compose up client
```

### Replica Sync Test

- Stops a replica
- Executes trades
- Restarts replica
- Verifies missed data sync

### Cache & Latency Experiments

- Compares cached vs non-cached lookup performance
- Runs concurrent clients with varying workloads
- Generates latency + eviction plots

## What This Project Demonstrates

This project focuses on core distributed systems principles:

- Distributed system design under failures
- Consensus algorithms (Paxos) in practice
- Strong vs eventual consistency trade-offs
- Scalable and concurrent service design
- Performance evaluation with real workloads


## Why this project?

This project focuses on real-world distributed systems challenges.

This project was built to understand:

- How do systems stay consistent when nodes fail?
- How do replicas agree on a single state?
- How do we recover without losing data?

## Tech Stack

- Python (HTTP servers, concurrency)
- Docker & Docker Compose
- REST APIs
- Paxos consensus protocol
- ThreadPoolExecutor (concurrency)
- LRU Cache implementation

## Future Improvements

- Consensus protocol (Paxos/Raft) for stronger consistency
- Distributed logging & monitoring
- Horizontal scaling with service discovery
- Persistent database integration

Built as part of distributed systems exploration and hands-on system design learning.