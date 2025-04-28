import glob
import matplotlib.pyplot as plt

def get_latency_data_for_graphs(prefix):
    latencies = []
    for i in range(1, 6):  # concurrency levels 1 to 5
        pattern = f"logs/{prefix}_{i}_*.log"
        files = glob.glob(pattern)
        batch = []
        for f in files:
            with open(f) as file:
                batch.append(float(file.read().strip()))
        avg_latency = (sum(batch) / len(batch) * 1000) if batch else 0
        latencies.append(avg_latency)
    return latencies

lookup_nondocker_times = get_latency_data_for_graphs("lookup_latency_nondocker")
trade_nondocker_times = get_latency_data_for_graphs("trade_latency_nondocker")
lookup_docker_times = get_latency_data_for_graphs("lookup_latency_docker")
trade_docker_times = get_latency_data_for_graphs("trade_latency_docker")

plt.plot(range(1, 6), lookup_nondocker_times, marker='o', linestyle='-', label='Lookup Without Docker')
plt.plot(range(1, 6), trade_nondocker_times, marker='s', linestyle='-', label='Trade Without Docker')
plt.plot(range(1, 6), lookup_docker_times, marker='o', linestyle='--', label='Lookup With Docker')
plt.plot(range(1, 6), trade_docker_times, marker='s', linestyle='--', label='Trade With Docker')

plt.xlabel("Number of Concurrent Clients")
plt.ylabel("Average Latency (ms)")
plt.title("Latency vs Concurrency for Lookup and Trade Requests (With and Without Docker)")
plt.legend()
plt.grid(True)
plt.xticks([1, 2, 3, 4, 5])
plt.savefig("latency_plot.png")
plt.show()

plt.figure()
plt.plot(range(1, 6), lookup_docker_times, marker='o', linestyle='--', label='Lookup With Docker')
plt.plot(range(1, 6), trade_docker_times, marker='s', linestyle='--', label='Trade With Docker')

plt.xlabel("Number of Concurrent Clients")
plt.ylabel("Average Latency (ms)")
plt.title("Latency vs Concurrency for Lookup and Trade Requests (With Docker)")
plt.legend()
plt.grid(True)
plt.xticks([1, 2, 3, 4, 5])
plt.savefig("latency_plot_docker.png")
plt.show()

plt.figure()
plt.plot(range(1, 6), lookup_nondocker_times, marker='o', linestyle='-', label='Lookup Without Docker')
plt.plot(range(1, 6), trade_nondocker_times, marker='s', linestyle='-', label='Trade Without Docker')

plt.xlabel("Number of Concurrent Clients")
plt.ylabel("Average Latency (ms)")
plt.title("Latency vs Concurrency for Lookup and Trade Requests (Without Docker)")
plt.legend()
plt.grid(True)
plt.xticks([1, 2, 3, 4, 5])
plt.savefig("latency_plot_nondocker.png")
plt.show()
