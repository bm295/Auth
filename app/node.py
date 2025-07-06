import os
import requests

class StubVoteDB:
    """Very small in-memory stand-in for a real database."""

    def __init__(self, initial_count: int = 0):
        self.count = initial_count

    def get_count(self) -> int:
        return self.count

    def add_vote(self) -> None:
        self.count += 1


class Node:
    def __init__(self):
        peers_env = os.getenv("PEERS", "")
        self.peers = [p.strip() for p in peers_env.split(',') if p.strip()]
        if not self.peers:
            default_peer = os.getenv("DEFAULT_PEER", "http://localhost:5001")
            self.peers = [default_peer]

        initial = int(os.getenv("INITIAL_VOTES", "0"))
        self.db = StubVoteDB(initial)

        # default to node "A" if no identifier is provided so that running two
        # nodes locally shows "Node A" and "Node B" in the UI.  Pre-populate
        # counters for both nodes so the UI always displays both entries.
        self.node_id = os.getenv("NODE_ID", "A")

        # maintain counters for both Node A and Node B regardless of which
        # identifier this instance uses
        self.counts = {"A": 0, "B": 0}
        self.counts[self.node_id] = self.db.get_count()
        self.value = self._calculate_total()

    def _calculate_total(self) -> int:
        return sum(self.counts.values())


    def record_vote(self):
        self.db.add_vote()
        self.counts[self.node_id] = self.db.get_count()
        self.value = self._calculate_total()
        self.replicate()

    def merge_counts(self, peer_counts: dict):
        updated = False
        for node_id, count in peer_counts.items():
            if count > self.counts.get(node_id, 0):
                self.counts[node_id] = count
                updated = True
        if updated:
            self.value = self._calculate_total()

    def replicate(self):
        for peer in self.peers:
            try:
                requests.post(
                    f"{peer}/update",
                    json={"counts": self.counts},
                    timeout=1,
                )
            except requests.RequestException:
                # ignore failed replication
                pass
