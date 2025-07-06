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
        self.value = self.db.get_count()


    def record_vote(self):
        self.db.add_vote()
        self.value += 1
        self.replicate()

    def set_value(self, new_value: int):
        if new_value > self.value:
            self.value = new_value

    def replicate(self):
        for peer in self.peers:
            try:
                requests.post(f"{peer}/update", json={"value": self.value}, timeout=1)
            except requests.RequestException:
                # ignore failed replication
                pass
