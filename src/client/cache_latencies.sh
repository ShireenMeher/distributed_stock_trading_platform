#!/bin/bash

mkdir -p logs

for p in 0.0 0.2 0.4 0.6 0.8 1.0; do
  echo "Running for p=$p with cache"

  for i in {1..5}; do
    python3 client.py cached $i $p &
  done

  echo "Running for p=$p without cache"
  for i in {1..5}; do
    python3 client.py nocache $i $p &
  done


  wait
done

echo "All latencies logged"

python3 src/plot_cache_latency_plots.py
python3 src/plot_cache_evictions.py

echo "All plots done"

