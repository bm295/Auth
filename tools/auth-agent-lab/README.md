# Auth JWT Contract Lab

From the repository root on Linux or macOS, use Python 3.10+, Git, .NET 8 SDK,
Java 21 and Maven. Live mode also needs authenticated Codex CLI, Claude Code
and Kiro CLI with the Kiro V3 headless harness and its API key. The run starts
from the current Git commit.

```bash
# Run the fixed cross-runtime matrix without any agent.
python3 tools/auth-agent-lab/verify.py

# Exercise all handoffs and the regression gate without provider credentials.
python3 tools/auth-agent-lab/run.py --mode mock --mutation --minutes 8

# Use Kiro for spec, Codex for test cases, Claude Code for review.
python3 tools/auth-agent-lab/run.py --minutes 8

# Compare with Codex alone under the same case constraints and verification gate.
python3 tools/auth-agent-lab/run.py --mode single --minutes 8
```

The runner invokes headless CLI processes directly. It gives each CLI the inputs
for its role via stdin in a temporary working directory. CAO and tmux are
optional outside this lab. Use standard local CLI installations with no
additional tools, plugins or MCP servers that can modify the project. The
runner accepts structured data only and commits the generated regression
case manifest in a disposable Git worktree. It executes a fixed test harness
that never runs agent-authored code. All tokens and signing material in the
lab belong to the local demo.

A run records `state.json`, `contract.json`, `candidate.diff`, `review.json`,
`report.md` and per-step logs under `.auth-agent-lab/run-*/`. Single mode omits
the spec and independent review. Mock mode uses deterministic handoffs.
Verification builds the exact reviewed commit and checks the Maven test report
for all required scenarios. Rejected review or verification can request one
repair. A CLI error, timeout or invalid handoff blocks the current step.
Continue the same run after fixing the cause.

```bash
python3 tools/auth-agent-lab/run.py --resume .auth-agent-lab/run-EXAMPLE
```

In mutation mode the fixed matrix must first pass on the candidate commit.
The runner then disables Java audience validation in a second checkout. The
verification gate must specifically report the wrong-audience regression
before the runner can report success. The second checkout is removed afterward.
The successful candidate remains available for human review. Inspect or export
it before removing the worktree.

```bash
git -C .auth-agent-lab/run-EXAMPLE/worktree show HEAD
git worktree remove .auth-agent-lab/run-EXAMPLE/worktree
```

Compare `report.md` for elapsed time and repair rounds on the same base commit.
The fixed tests are shared by both modes. Review their generated extra cases
and record manual interventions alongside the results.
