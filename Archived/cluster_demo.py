import multiprocessing
import time

from app import create_app
from app.cache import Cache


def run_node(port: int, shared_store):
    cache = Cache(store=shared_store)
    app = create_app(cache)
    app.run(port=port, debug=False, use_reloader=False)


def main():
    manager = multiprocessing.Manager()
    shared_store = manager.dict()

    ports = [5000, 5001]
    processes = []
    for port in ports:
        p = multiprocessing.Process(target=run_node, args=(port, shared_store))
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
