# Simple Distributed Counter

This repository demonstrates a minimal distributed system using Python and Flask.
Each node maintains an integer counter. When a node increments its counter it
broadcasts the new value to its peers through HTTP requests. The peers then
update their own counters if the received value is greater.

The example is intentionally simple so you can run multiple nodes locally and
observe them replicating the counter value between each other.

## Installation

```bash
pip install -r requirements.txt
```

## Running

Start two or more instances. Each node must know the addresses of the others via
the `PEERS` environment variable.

```bash
# terminal 1
export PEERS="http://localhost:5001"
FLASK_APP=run.py flask run -p 5000

# terminal 2
export PEERS="http://localhost:5000"
FLASK_APP=run.py flask run -p 5001
```

Open a browser at `http://localhost:5000` or `http://localhost:5001` and click
"Increment" on either instance. The counter value should stay in sync across all
nodes.
