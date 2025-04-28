#!/bin/bash

#change the run_type to "docker" or "nondocker" based on build type
run_type="nondocker"

# Clean previous logs
rm -f logs/lookup_latency_${run_type}_*.log

# lets call i is the concurrency level
for i in {1..5}
do
    echo "Running $i concurrent lookup clients..."
    for j in $(seq 1 $i)
    do
        python3 src/client.py lookup $i $j $run_type &
    done
    wait
done
echo "All lookup clients finished."
