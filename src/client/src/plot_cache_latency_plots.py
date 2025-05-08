import matplotlib.pyplot as plt
import os
import re
from collections import defaultdict

def fetch_latency_as_float(file_path):
    with open(file_path) as f:
        return float(f.read().strip())

def parse_logs():
    # Data structure: {cache_state: {p: {'lookup': [...], 'trade': [...]}}}
    data = {'cache': defaultdict(lambda: {'lookup': [], 'trade': []}),
            'nocache': defaultdict(lambda: {'lookup': [], 'trade': []})}

    for fname in os.listdir("logs"):
        match = re.match(r"(cache|nocache)_(lookup|trade)_([0-9.]+)_(\d+).log", fname)
        if match:
            cache_state, req_type, p_str, client_id = match.groups()
            p = float(p_str)
            latency = fetch_latency_as_float(os.path.join("logs", fname))
            data[cache_state][p][req_type].append(latency)

    print(data)
    return data

def plot_latency():
    data = parse_logs()
    ps = sorted(set(p for p in data['cache']) | set(p for p in data['nocache']))

    color_map = {
        'lookup': 'tab:blue',
        'trade': 'tab:orange'
    }

    for req_type in ['lookup', 'trade']:
        plt.figure()
        for cache_state in ['cache', 'nocache']:
            y = []
            for p in ps:
                latencies = data[cache_state][p][req_type]
                avg_latency = sum(latencies)/len(latencies) if latencies else 0
                y.append(avg_latency)
            plt.plot(ps, y, marker='o', label=f"{req_type.upper()} - Cache {cache_state.upper()}")

        plt.xlabel("Probability of Follow-up Trade (p)")
        plt.ylabel(f"Average {req_type.capitalize()} Latency (s)")
        plt.title(f"{req_type.capitalize()} Latency vs Probability")
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{req_type}_latency_plot.png")
        plt.show()

def plot_combined_latency():
    data = parse_logs()
    ps = sorted(set(p for p in data['cache']) | set(p for p in data['nocache']))

    plt.figure(figsize=(10, 6))

    color_map = {
        'lookup': 'tab:blue',
        'trade': 'tab:green'
    }

    for req_type in ['lookup', 'trade']:
        for cache_state in ['cache', 'nocache']:
            y = []
            for p in ps:
                latencies = data[cache_state][p][req_type]
                avg_latency = sum(latencies)/len(latencies) if latencies else 0
                y.append(avg_latency)
            linestyle = '-' if cache_state == 'cache' else '--'
            label = f"{req_type.capitalize()} - {cache_state.capitalize()}"
            plt.plot(ps, y, marker='o', linestyle=linestyle, color=color_map[req_type], label=label)

    plt.xlabel("Probability of Follow-up Trade (p)")
    plt.ylabel("Average Latency (s)")
    plt.title("Latency vs Probability (All Types Combined)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("combined_latency_plot.png")
    plt.show()


if __name__ == "__main__":
    plot_latency()
    plot_combined_latency()
