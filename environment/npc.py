"""Supervise the upstream NPCs without logging their API key."""
import json
import os
import signal
import subprocess
import sys
import time


def main():
    for key in ("LITELLM_API_KEY", "LITELLM_BASE_URL", "LITELLM_MODEL"):
        if not os.environ.get(key):
            raise SystemExit(f"Missing {key}; configure .env")
    with open(os.environ.get("SCENARIOS_FILE_PATH", "/npc/scenarios.json")) as source:
        names = list(json.load(source))
    children = [subprocess.Popen(
        [sys.executable, "-u", "/npc/run_one_npc.py", "--agent_name", name],
        cwd="/npc",
    ) for name in names]

    def stop(signum, frame):
        for child in children:
            child.terminate()
        for child in children:
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    with open("/tmp/npc-pids.json", "w") as output:
        json.dump([child.pid for child in children], output)
    print(f"Started {len(children)} upstream NPCs", flush=True)
    while all(child.poll() is None for child in children):
        time.sleep(1)
    for child in children:
        if child.poll() is None:
            child.terminate()
    raise SystemExit("An upstream NPC exited; inspect docker compose logs npc")


if __name__ == "__main__":
    main()
