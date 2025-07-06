# Distributed Voting System

This repository demonstrates a minimal distributed voting system using Python
and Flask. For the sake of the example we do not use a real database. Instead a
stub component returns a predefined vote count so you can focus on the logic of
replicating values between nodes. Each node keeps a local counter and when a
vote is recorded the new count is replicated to all peers.

The example is intentionally simple so you can run multiple nodes locally and
observe them replicating the vote count between each other. A helper script
`cluster_demo.py` is included to automatically start two nodes for testing vote
replication.

## Installation

```bash
pip install -r requirements.txt
```

## Running

Start two instances and assign them the node identifiers `A` and `B`.  Each node
must know the addresses of the others via the `PEERS` environment variable.

If `PEERS` is not provided, the application assumes a peer at
`http://localhost:5001` so the UI always shows two clickable nodes.

```bash
# terminal 1
export PEERS="http://localhost:5001"
export NODE_ID=A
FLASK_APP=run.py flask run -p 5000

# terminal 2
export PEERS="http://localhost:5000"
export NODE_ID=B
FLASK_APP=run.py flask run -p 5001
```

Open a browser at `http://localhost:5000` or `http://localhost:5001` and click
any of the node boxes. Each button sends a vote request directly to the
corresponding node (e.g. clicking **Node B** from the page served on port 5000
will post to `http://localhost:5001/vote`). Each node keeps its own counter and
replicates the results to its peers so the totals stay in sync. The layout is
responsive so it works well on mobile screens.

### Running the demo script

To quickly see two nodes sharing the same counter, run:

```bash
python cluster_demo.py
```

This starts two Flask servers on ports 5000 and 5001 that replicate the counter
value between them. Each process is assigned the IDs `A` and `B` respectively
so the web UI displays "Node A" and "Node B".

### Distributed Voting Example

This section illustrates how nodes can share a resource and maintain
incremental counters when processing votes.

**Scenario**

* Multiple nodes accept user votes at the same time.
* Votes are written to a shared resource so each node has a consistent view.
* Each node keeps a vote counter that increments whenever a vote is recorded.

**Example Diagram**

```
       Node A                      Node B
     ┌───────────┐              ┌───────────┐
     │ Vote Count│              │ Vote Count│
     │  Counter  │              │  Counter  │
     └───────────┘              └───────────┘
             │ Increment (+1)         │ Increment (+1)
             ▼                        ▼
        ┌───────────────────────────────────┐
        │                                   │
        │        Shared Resource            │
        │        (Vote Records)             │
        │                                   │
        └───────────────────────────────────┘
```

**How it Works**

1. Nodes A and B receive votes concurrently.
2. Each node increments its local counter and writes to the shared resource.
3. The resource keeps the vote records consistent while counters track totals.
4. Distributed algorithms keep the counters in sync even with concurrent updates.
