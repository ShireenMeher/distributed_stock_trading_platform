import matplotlib.pyplot as plt
import re

CACHE_SIZE = 5  # Set your cache size here
log_path = "/app/frontend_logs/CACHE_ACTIVITY.log"

def parse_cache_log(log_path):
    with open(log_path) as f:
        lines = f.readlines()

    cache = []
    timeline = []  # stores snapshots of cache

    for line in lines:
        match = re.search(r'CACHE (HIT|MISS|INSERT|EVICT): (.+)', line)
        if not match:
            continue

        action, item = match.groups()
        if action == 'HIT':
            if item in cache:
                cache.remove(item)
                cache.append(item)

        elif action == 'INSERT':
            if item in cache:
                cache.remove(item)
            elif len(cache) >= CACHE_SIZE:
                cache.pop(0)  # evict LRU
            cache.append(item)

        elif action == 'EVICT':
            if item in cache:
                cache.remove(item)

        # Take snapshot of cache
        timeline.append(cache.copy())

    return timeline

import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors

def plot_cache_timeline(timeline, sample_rate=5):
    sampled_timeline = timeline[::sample_rate]
    items = set(i for snapshot in sampled_timeline for i in snapshot)
    color_map = dict(zip(sorted(items), cm.tab20.colors))  # assign distinct colors

    fig_height = max(6, len(sampled_timeline) * 0.3)  # dynamic height
    fig, ax = plt.subplots(figsize=(14, fig_height))  # improved readability

    for t, state in enumerate(sampled_timeline):
        for pos, item in enumerate(state):
            color = color_map[item]
            ax.text(pos, t, item, ha='center', va='center',
                    fontsize=6,  # smaller text
                    bbox=dict(boxstyle='round,pad=0.1', fc=color, alpha=0.4))  # tighter box

    ax.set_xlabel("Cache Position (0 = LRU)")
    ax.set_ylabel("Sampled Time Step")
    ax.set_title(f"Cache State Over Time (Sampled Every {sample_rate} Ops)")
    ax.set_xlim(-0.5, CACHE_SIZE - 0.5)
    ax.set_ylim(-1, len(sampled_timeline))
    ax.invert_yaxis()
    ax.grid(True, linestyle='--', alpha=0.3)

    plt.tight_layout()
    plt.savefig("cache_replacement_clean.png", dpi=300)
    plt.show()

# Run this
timeline = parse_cache_log(log_path)
plot_cache_timeline(timeline)
