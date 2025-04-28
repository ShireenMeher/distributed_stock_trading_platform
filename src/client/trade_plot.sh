#!/bin/bash

# change the run_type to "docker" or "nondocker" based on build type
run_type="nondocker"

# Clean previous logs
rm -f logs/trade_latency_${run_type}_*.log

for i in {1..5}
do
    echo "Running $i concurrent trade clients..."
    for j in $(seq 1 $i)
    do
        python3 src/client.py trade $i $j $run_type &
    done
    wait
done
echo "All trade clients finished."