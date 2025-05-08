# paxos/learner.py

from paxos.state import learned_values

def learn(txn_id, value):
    learned_values[txn_id] = value
