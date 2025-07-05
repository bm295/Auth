# Distributed Resource Counter

This repository demonstrates a minimal distributed system using Python and Flask.
Each node maintains a set of named counters representing shared resources. When a
resource is added or incremented on one node, the updated resource map is
broadcast to its peers using HTTP requests. Peers merge the data by keeping the
highest value for each resource.

The example is intentionally simple so you can run multiple nodes locally and
observe them replicating the resource counters between each other.

## Installation

```bash
pip install -r requirements.txt
```

## Running

Start two or more instances. Each node must know the addresses of the others via
the `PEERS` environment variable. Optionally seed some resources using the
`RESOURCES` variable.

```bash
# terminal 1
export PEERS="http://localhost:5001"
export RESOURCES="cpu,memory"
FLASK_APP=run.py flask run -p 5000

# terminal 2
export PEERS="http://localhost:5000"
export RESOURCES="cpu,memory"
FLASK_APP=run.py flask run -p 5001
```

Open a browser at `http://localhost:5000` or `http://localhost:5001`. Add or
increment resources on either instance and watch them stay in sync across all
nodes.
