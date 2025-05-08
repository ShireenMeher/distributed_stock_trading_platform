# paxos/state.py

accepted_proposals = {}  # {txn_id: (proposal_number, value)}
promised_proposals = {}  # {txn_id: proposal_number}
learned_values = {}      # {txn_id: value}
proposal_counter = 0
