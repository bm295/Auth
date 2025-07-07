# Local Voting Demo

This repository demonstrates a minimal voting application using Python and
Flask. Two nodes, **A** and **B**, keep their own vote counters locally. The
interface displays buttons for each node and shows the current counter values.
Each click simply increments the corresponding local counter without any network
replication.

You can still launch two Flask processes with `cluster_demo.py` to see two
independent nodes running side by side.

## Installation

```bash
pip install -r requirements.txt
```

## Running

Start two instances of the application on ports `5000` and `5001`:

```bash
# terminal 1
FLASK_APP=run.py flask run -p 5000

# terminal 2
FLASK_APP=run.py flask run -p 5001
```

Open a browser at `http://localhost:5000/voting` (or `http://localhost:5001/voting`)
and click any of the node boxes. Each button posts to the local server and
increments the matching counter. The layout is responsive so it works well on
mobile screens.

### Running the demo script

To quickly see two nodes sharing the same counter, run:

```bash
python cluster_demo.py
```

This starts two Flask servers on ports 5000 and 5001 so you can vote on two
independent nodes. Each process exposes its own counters and the web UI displays
"Node A" and "Node B".

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

## Demonstrating Latency

A common challenge in distributed systems is network latency. To see how delayed
communication affects user experience, the application includes a "slow" voting
endpoint that sleeps for two seconds before recording a vote. Buttons labelled
"Slow A" and "Slow B" trigger this delayed path so you can compare response
times with the normal voting flow.

Run the app as usual and click the slow buttons to observe the latency impact:

```bash
FLASK_APP=run.py flask run -p 5000
```

## Cache Definition in Distributed Systems

A cache is a temporary storage layer that holds a subset of data so future requests are served faster. In distributed systems, caches may be shared among multiple nodes to reduce latency and load on the underlying resource. The `cluster_demo.py` script uses a shared dictionary managed by Python's `multiprocessing` module as a simple distributed cache for vote counters.
