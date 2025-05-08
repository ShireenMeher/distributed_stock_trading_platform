import requests
from paxos.state import proposal_counter
from paxos.learner import learn

# the leader proposes a value to the replicas
# here txn_id =>transaction id, 
# value => value to be proposed,
# replicas => list of replica addresses
def propose(txn_id, value, replicas):
    global proposal_counter

    # Increment the proposal number for each new proposal
    proposal_counter += 1
    proposal_num = proposal_counter

    #STEP-1
    # Send prepare requests to all replicas
    # prepare_oks has the "ok" responses from replicas
    prepare_oks = []
    for replica in replicas:
        try:
            # Send prepare request to each replica
            res = requests.post(f"{replica}/prepare", json={"txn_id": txn_id, "proposal_num": proposal_num}, timeout=2)
            if res.json().get("ok"):
                prepare_oks.append(res.json())
        except:
            continue

    # if we don't get majority, exit
    if len(prepare_oks) < (len(replicas) // 2 + 1):
        return False  # no majority

    #-----------------------------------------------------------

    #STEP-2
    # Check if any replica has accepted a value
    # If yes, use that value for the accept phase
    # If no, use the proposed value
    accepted_val = value
    for ok in prepare_oks:
        accepted = ok.get("accepted")
        if accepted:
            _, accepted_val = accepted

    accept_oks = []
    # Send accept requests to all replicas
    for replica in replicas:
        try:
            res = requests.post(f"{replica}/accept", json={"txn_id": txn_id, "proposal_num": proposal_num, "value": accepted_val}, timeout=2)
            if res.json().get("ok"):
                accept_oks.append(True)
        except:
            continue

    #-----------------------------------------------------------

    #STEP-3
    # Check if we have majority of accept responses
    # If yes, learn the value
    # If no, exit
    if len(accept_oks) >= (len(replicas) // 2 + 1):
        # Call the learn function to store the value, make all replicas learn the value
        learn(txn_id, accepted_val)
        return True
    return False
