"""Run the cross-runtime contract against a local ASP.NET Core process."""
import argparse
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen
from xml.etree import ElementTree

JAVA = Path("java/auth-jwt-library")
CASES = Path("tools/auth-agent-lab/regression-cases.json")
EXPECTED = {
    "acceptsTokenMintedByDotnet", "rejectsTamperedSignature", "rejectsWrongIssuer",
    "rejectsWrongAudience", "rejectsExpiredToken",
}


def wait_for_app(server, url):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("ASP.NET Core stopped before it was ready")
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except (URLError, TimeoutError):
            time.sleep(0.2)
    raise RuntimeError("ASP.NET Core did not become ready")


def verify(root):
    subprocess.run(["dotnet", "build", "Auth.csproj", "-c", "Release"], cwd=root, check=True)
    with socket.socket() as port:
        port.bind(("127.0.0.1", 0))
        url = f"http://127.0.0.1:{port.getsockname()[1]}"
    report = root / JAVA / "target/surefire-reports/TEST-com.authdemo.jwt.JwtInteropTest.xml"
    report.unlink(missing_ok=True)
    env = {**os.environ, "ASPNETCORE_URLS": url}
    command = ["mvn", "-B", "-f", str(JAVA / "pom.xml"), "test", f"-Dauth.demo.url={url}"]
    cases = root / CASES
    expected = set(EXPECTED)
    if cases.is_file():
        command.append(f"-Dauth.demo.cases={cases}")
        expected.add("rejectsAgentRegressionCases")
    server = subprocess.Popen(["dotnet", "bin/Release/net8.0/Auth.dll"], cwd=root,
                              env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_for_app(server, url)
        result = subprocess.run(command, cwd=root, check=False)
    finally:
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
    if report.is_file():
        cases = ElementTree.parse(report).getroot().findall("testcase")
        failures = {case.attrib["name"] for case in cases if case.find("failure") is not None}
        if "rejectsWrongAudience" in failures:
            print("AUTH_GATE_REJECTED_WRONG_AUDIENCE", flush=True)
        passed = {case.attrib["name"] for case in cases if not len(case.findall("failure"))
                  and not len(case.findall("error")) and not len(case.findall("skipped"))}
        if result.returncode == 0 and expected <= passed:
            print(f"Auth JWT contract passed ({len(expected)} scenarios).")
            return 0
    print("Auth JWT contract failed or expected test cases did not execute.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    try:
        sys.exit(verify(args.root.resolve()))
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
