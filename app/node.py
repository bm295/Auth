import os
import requests


class Node:
    def __init__(self):
        peers_env = os.getenv("PEERS", "")
        self.peers = [p.strip() for p in peers_env.split(',') if p.strip()]
        if not self.peers:
            default_peer = os.getenv("DEFAULT_PEER", "http://localhost:5001")
            self.peers = [default_peer]
        self.value = 0

    def increment(self):
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
