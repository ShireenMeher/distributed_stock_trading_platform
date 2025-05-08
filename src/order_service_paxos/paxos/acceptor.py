from paxos.state import promised_proposals, accepted_proposals

#this file contains the tricky prepare & acceptor logics

def finalise_prepare(txn_id, proposal_num):
    # IF the proposal number is greater than the promised proposal number
    # OR if the txn_id is not in promised_proposals
    # THEN promise to accept the proposal
    # and return the highest accepted proposal number and value

    #this is to ensure that paxos doesnt accept the outdated proposal
    global promised_proposals
    if txn_id not in promised_proposals or proposal_num > promised_proposals[txn_id]:
        promised_proposals[txn_id] = proposal_num
        return {"ok": True, "accepted": accepted_proposals.get(txn_id)}
    return {"ok": False}

def finalise_accept(txn_id, proposal_num, value):
    # IF the proposal number is greater than the promised proposal number
    # OR if the txn_id is not in promised_proposals
    # THEN accept the proposal

    # this logic makes sure, in case new value is promised, we dont accept the old value
    global promised_proposals
    global accepted_proposals
    if txn_id not in promised_proposals or proposal_num >= promised_proposals[txn_id]:
        promised_proposals[txn_id] = proposal_num
        accepted_proposals[txn_id] = (proposal_num, value)
        return {"ok": True}
    return {"ok": False}
