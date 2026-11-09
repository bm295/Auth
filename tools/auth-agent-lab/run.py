"""Orchestrate an Auth JWT regression task with resumable local handoffs."""
import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time

from verify import CASES, JAVA

SOURCE = JAVA / "src/main/java/com/authdemo/jwt/JwtTokenService.java"
CONTRACT = {
    "acceptsTokenMintedByDotnet": "Both accept and Java preserves sub and tenant_id",
    "rejectsTamperedSignature": "Both reject a token with corrupted signature bytes",
    "rejectsWrongIssuer": "Both reject a correctly signed JWT with the wrong issuer",
    "rejectsWrongAudience": "Both reject a correctly signed JWT with the wrong audience",
    "rejectsExpiredToken": "Both reject a correctly signed expired JWT",
}
AUDIENCE_CHECK = " || !audience.equals(claims.get(\"aud\"))"
MUTATION_MARKER = "AUTH_GATE_REJECTED_WRONG_AUDIENCE"
RESPONSE = "\nReturn only JSON inside <result> and </result> tags."
IMPLEMENT_TASK = (
    "Author 1 to 4 additional .NET-to-Java JWT regression cases. Return a JSON array "
    'with objects {"claim":"aud or iss","value":"alternate string"}. Pick values likely '
    "to reveal an overly permissive comparison such as a case change or trailing whitespace. "
    "Every case must be rejected by both validators. The runner compiles this data into "
    "executable checks, so your output must contain only the case definitions."
)


def git(root, *args):
    return subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *args], cwd=root,
                          text=True, stdout=subprocess.PIPE, check=True).stdout


def save_json(path, value):
    pending = path.with_suffix(".tmp")
    pending.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    pending.replace(path)


@contextmanager
def run_lock(directory):
    with (directory / "lock").open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("This run is already active") from error
        yield


def run_process(argv, cwd, timeout, stdout, stderr, prompt=None):
    with stdout.open("w") as out, stderr.open("w") as err:
        proc = subprocess.Popen(argv, cwd=cwd, text=True, stdout=out, stderr=err,
                                stdin=subprocess.PIPE if prompt is not None else subprocess.DEVNULL,
                                start_new_session=True)
        try:
            proc.communicate(input=prompt, timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
            if isinstance(error, KeyboardInterrupt):
                raise
            raise RuntimeError(f"Timed out after {timeout / 60:g} minutes") from error
    return proc.returncode


def parse_response(raw):
    matches = re.findall(r"<result>\s*(.*?)\s*</result>", raw, re.S)
    if len(matches) > 1:
        raise ValueError("Expected one result block")
    return json.loads(matches[0] if matches else raw)


def check_cases(cases):
    if not isinstance(cases, list) or not 1 <= len(cases) <= 4:
        raise ValueError("Expected 1–4 regression cases")
    seen = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"claim", "value"}:
            raise ValueError("Each regression case requires claim and value")
        claim, value = case["claim"], case["value"]
        if claim not in ("iss", "aud") or not isinstance(value, str):
            raise ValueError("Unsupported regression case")
        original = "AuthDemoIssuer" if claim == "iss" else "AuthDemoAudience"
        if not value.strip() or not value.isprintable() or len(value) > 64 or value == original:
            raise ValueError("Invalid alternative claim value")
        if (claim, value) in seen:
            raise ValueError("Duplicate regression case")
        seen.add((claim, value))


class Lab:
    def __init__(self, directory, state):
        self.directory = directory
        self.state = state
        self.root = Path(state["root"])
        self.work = directory / "worktree"
        self.base = state["base"]
        self.timeout = state["minutes"] * 60

    def persist(self):
        save_json(self.directory / "state.json", self.state)
        lines = ["# Auth Agent Lab", "", f'- Mode: {self.state["mode"]}',
                 f'- Status: {self.state["status"]}', f"- Base: {self.base}",
                 f'- Candidate: {self.state.get("candidate", "pending")}',
                 f'- Repair rounds: {self.state["round"]}',
                 f'- Audience mutation: {self.state["mutation"]}', "",
                 "| Step | Result | Seconds |", "| --- | --- | ---: |"]
        for event in self.state["events"]:
            lines.append(f'| {event["step"]} | {event["result"]} | {event["seconds"]} |')
        if self.state.get("mutation_detected"):
            lines.append("\nThe verification gate rejected the deliberate audience regression.")
        lines.extend(["", "Artifacts and process logs are stored beside this report."])
        (self.directory / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def agent(self, role, prompt):
        if self.state["mode"] == "mock":
            return {
                "spec": {"checks": list(CONTRACT), "rationale": "Shared JWT acceptance matrix"},
                "implement": [{"claim": "aud", "value": "authDemoAudience"}],
                "review": {"verdict": "PASS", "evidence": "The candidate tests audience case sensitivity."},
            }[role]
        with tempfile.TemporaryDirectory(prefix="auth-agent-") as empty_dir:
            cwd = Path(empty_dir)
            round_id = self.state["round"]
            prefix = self.directory / f"{role}-{round_id}"
            stdout = prefix.with_suffix(".stdout.log")
            stderr = prefix.with_suffix(".stderr.log")
            if role == "spec":
                argv = ["kiro-cli", "chat", "--v3", "--no-interactive"]
            elif role == "implement":
                final = cwd / "response.txt"
                argv = ["codex", "-a", "never", "exec", "--ephemeral",
                        "--sandbox", "read-only", "--skip-git-repo-check",
                        "--output-last-message", str(final), "-"]
            else:
                argv = ["claude", "--print", "--tools", "", "--setting-sources", "",
                        "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}']
            if run_process(argv, cwd, self.timeout, stdout, stderr, prompt + RESPONSE):
                raise RuntimeError(f"{role} CLI failed. See {stderr.name}")
            output = final if role == "implement" else stdout
            return parse_response(output.read_text(encoding="utf-8"))

    def spec(self):
        program = git(self.root, "show", f"{self.base}:Program.cs")
        source = git(self.root, "show", f"{self.base}:{SOURCE.as_posix()}")
        result = self.agent("spec", "Specify this JWT contract. Return a JSON object with "
                            'checks (array of the exact check IDs below) and rationale (string).\n'
                            f"{json.dumps(CONTRACT)}\n\n{program[:7500]}\n\n{source}")
        if (not isinstance(result, dict) or not isinstance(result.get("checks"), list)
                or sorted(result["checks"]) != sorted(CONTRACT)
                or not isinstance(result.get("rationale"), str) or not result["rationale"].strip()):
            raise ValueError("Invalid specification handoff")
        save_json(self.directory / "contract.json", result)

    def implement(self):
        prompt = f"{IMPLEMENT_TASK}\nMandatory checks: {json.dumps(CONTRACT)}"
        spec = self.directory / "contract.json"
        if spec.exists():
            prompt += "\nSpec: " + spec.read_text(encoding="utf-8")
        if self.state.get("feedback"):
            prompt += "\nPrevious feedback: " + self.state["feedback"]
        cases = self.agent("implement", prompt)
        check_cases(cases)
        if not self.work.exists():
            git(self.root, "worktree", "add", "--detach", str(self.work), self.base)
        current = git(self.work, "rev-parse", "HEAD").strip()
        known = self.state.get("candidate", self.base)
        if current != known:
            # Recover a commit completed immediately before the previous runner stopped.
            parent = git(self.work, "rev-parse", "HEAD^").strip()
            files = git(self.work, "diff", "--name-only", known, current).splitlines()
            if parent != known or files != [CASES.as_posix()]:
                raise RuntimeError("Run worktree HEAD was changed externally")
        status = git(self.work, "status", "--porcelain", "--untracked-files=all").splitlines()
        if any(line[3:] != CASES.as_posix() for line in status):
            raise RuntimeError("Run worktree has edits outside the generated cases")
        save_json(self.work / CASES, cases)
        git(self.work, "add", "--", CASES.as_posix())
        if git(self.work, "diff", "--cached", "--name-only").strip():
            git(self.work, "-c", "user.name=Auth Agent Lab", "-c",
                "user.email=auth-agent-lab@localhost", "-c", "commit.gpgsign=false",
                "commit", "-m", "Add agent-authored JWT regression cases")
        candidate = git(self.work, "rev-parse", "HEAD").strip()
        (self.directory / "candidate.diff").write_text(
            git(self.work, "diff", self.base, candidate), encoding="utf-8")
        self.state["candidate"] = candidate

    def review(self):
        diff = (self.directory / "candidate.diff").read_text(encoding="utf-8")
        sha = self.state["candidate"]
        result = self.agent("review", f"Review the JWT regression cases for commit {sha}. "
                            "Check that the cases add a meaningful comparison edge and fit "
                            "the fixed cross-runtime contract. Return JSON with verdict "
                            '(PASS or FAIL) and evidence (string).\n'
                            f"Contract: {json.dumps(CONTRACT)}\n{diff}")
        if (not isinstance(result, dict) or result.get("verdict") not in ("PASS", "FAIL")
                or not isinstance(result.get("evidence"), str) or not result["evidence"].strip()):
            raise ValueError("Invalid review handoff")
        result["commit"] = sha
        save_json(self.directory / f'review-{self.state["round"]}.json', result)
        save_json(self.directory / "review.json", result)
        if result["verdict"] == "FAIL":
            return result["evidence"]

    def verify(self):
        sha = self.state["candidate"]
        if git(self.work, "rev-parse", "HEAD").strip() != sha or git(self.work, "status", "--porcelain"):
            raise RuntimeError("Verification requires the exact clean candidate commit")
        script = Path(__file__).with_name("verify.py")
        round_id = self.state["round"]
        stdout = self.directory / f"verify-{round_id}.stdout.log"
        stderr = self.directory / f"verify-{round_id}.stderr.log"
        code = run_process([sys.executable, str(script), "--root", str(self.work)],
                           self.work, self.timeout, stdout, stderr)
        if code:
            details = stdout.read_text(encoding="utf-8", errors="replace")[-2000:]
            return f"Verification failed on {sha}. See {stdout.name} and {stderr.name}.\n{details}"
        if self.state["mutation"]:
            self.verify_mutation(script, sha)

    def verify_mutation(self, script, sha):
        # A separate checkout leaves the reviewed commit and its worktree intact.
        work = self.directory / "mutation-worktree"
        if work.exists():
            git(self.root, "worktree", "remove", "--force", str(work))
        git(self.root, "worktree", "add", "--detach", str(work), sha)
        try:
            source = work / SOURCE
            content = source.read_text(encoding="utf-8")
            if content.count(AUDIENCE_CHECK) != 1:
                raise RuntimeError("Could not locate the Java audience check for the demo mutation")
            source.write_text(content.replace(AUDIENCE_CHECK, ""), encoding="utf-8")
            stdout = self.directory / "mutation.stdout.log"
            stderr = self.directory / "mutation.stderr.log"
            code = run_process([sys.executable, str(script), "--root", str(work)],
                               work, self.timeout, stdout, stderr)
            if code != 1 or MUTATION_MARKER not in stdout.read_text(encoding="utf-8").splitlines():
                raise RuntimeError("Mutation demo did not prove the gate rejects a missing audience check")
            self.state["mutation_detected"] = True
        finally:
            git(self.root, "worktree", "remove", "--force", str(work))

    def execute(self):
        steps = {"spec": ("implement", self.spec),
                 "implement": ("verify" if self.state["mode"] == "single" else "review", self.implement),
                 "review": ("verify", self.review),
                 "verify": ("awaiting_human_review", self.verify)}
        while self.state["next"] in steps:
            stage = self.state["next"]
            next_stage, action = steps[stage]
            self.state["status"] = f"running_{stage}"
            self.persist()
            start = time.monotonic()
            try:
                feedback = action()
            except (ValueError, TypeError, RuntimeError, OSError, subprocess.CalledProcessError,
                    KeyboardInterrupt) as error:
                self.finish(stage, "blocked", start)
                print(f"{stage}: {error}", file=sys.stderr)
                return 1
            if feedback:
                self.state["feedback"] = feedback[:4000]
                if self.state["round"] == 0:
                    self.state["round"] = 1
                    self.state["next"] = "implement"
                    self.finish(stage, "repair_requested", start)
                    continue
                self.finish(stage, "blocked", start)
                print(feedback, file=sys.stderr)
                return 1
            self.state["next"] = next_stage
            self.finish(stage, "passed", start)
        self.state["status"] = "awaiting_human_review"
        self.persist()
        return 0

    def finish(self, step, result, start):
        self.state["events"].append({"step": step, "result": result,
                                     "seconds": round(time.monotonic() - start, 2)})
        self.state["status"] = result
        self.persist()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--minutes", type=float, default=8, help="Timeout per stage")
    parser.add_argument("--mode", choices=["multi", "single", "mock"], default="multi")
    parser.add_argument("--mutation", action="store_true", help="Prove the gate detects a deliberate Java audience regression")
    parser.add_argument("--resume", type=Path, help="Existing run directory")
    args = parser.parse_args()
    if not 0 < args.minutes < float("inf"):
        parser.error("--minutes must be a finite positive value")
    if args.resume:
        directory = args.resume.resolve()
    else:
        root = Path(git(Path(__file__).resolve().parent, "rev-parse", "--show-toplevel").strip())
        runs = root / ".auth-agent-lab"
        runs.mkdir(exist_ok=True)
        directory = Path(tempfile.mkdtemp(prefix="run-", dir=runs))
    print(f"Run artifacts: {directory}", flush=True)
    with run_lock(directory):
        if args.resume:
            state = json.loads((directory / "state.json").read_text(encoding="utf-8"))
        else:
            state = {"root": str(root), "base": git(root, "rev-parse", "HEAD").strip(),
                     "mode": args.mode, "minutes": args.minutes, "status": "pending",
                     "next": "implement" if args.mode == "single" else "spec",
                     "round": 0, "events": [], "mutation": args.mutation}
        return Lab(directory, state).execute()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
