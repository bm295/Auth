import os
import requests


class Node:
    def __init__(self):
        peers_env = os.getenv("PEERS", "")
        self.peers = [p.strip() for p in peers_env.split(',') if p.strip()]

        resources_env = os.getenv("RESOURCES", "")
        self.resources = {r.strip(): 0 for r in resources_env.split(',') if r.strip()}

    def add_resource(self, name: str):
        if name not in self.resources:
            self.resources[name] = 0
            self.replicate()

    def increment(self, name: str):
        if name not in self.resources:
            self.resources[name] = 0
        self.resources[name] += 1
        self.replicate()

    def set_resources(self, new_resources: dict):
        """Merge resources from peers, keeping the max value for each key."""
        for key, val in new_resources.items():
            if not isinstance(val, int):
                continue
            if key not in self.resources or val > self.resources[key]:
                self.resources[key] = val

    def replicate(self):
        for peer in self.peers:
            try:
                requests.post(f"{peer}/update", json={"resources": self.resources}, timeout=1)
            except requests.RequestException:
                # ignore failed replication
                pass
