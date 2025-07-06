"""Simple local vote counter."""

class Node:
    """Maintain local counters for nodes A and B."""

    def __init__(self):
        self.counts = {"A": 0, "B": 0}
        self.value = self._calculate_total()

    def _calculate_total(self) -> int:
        return sum(self.counts.values())

    def record_vote(self, node_id: str) -> None:
        """Increment the counter for the given node."""
        if node_id in self.counts:
            self.counts[node_id] += 1
            self.value = self._calculate_total()
