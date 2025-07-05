import multiprocessing
import os
import time

from app import create_app


def run_node(port: int, peers):
    os.environ["PEERS"] = ','.join(peers)
    app = create_app()
    app.run(port=port, debug=False, use_reloader=False)


def main():
    ports = [5000, 5001]
    processes = []
    for port in ports:
        peers = [f"http://localhost:{p}" for p in ports if p != port]
        p = multiprocessing.Process(target=run_node, args=(port, peers))
        p.start()
        processes.append(p)
    print(f"Started {len(processes)} nodes. Access them at {', '.join([f'http://localhost:{p}' for p in ports])}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for p in processes:
            p.terminate()
        for p in processes:
            p.join()


if __name__ == "__main__":
    main()
