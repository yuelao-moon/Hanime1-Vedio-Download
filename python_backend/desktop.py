from __future__ import annotations

import argparse
import os
import socket
import threading
import time
import webbrowser

import uvicorn

from app.main import create_app


def port_is_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex((host, port)) == 0


def open_when_ready(host: str, port: int) -> None:
    for _ in range(80):
        if port_is_open(host, port):
            webbrowser.open(f"http://{host}:{port}/")
            return
        time.sleep(0.25)


def main() -> None:
    parser = argparse.ArgumentParser(description="Hanime Media Center desktop launcher")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=58080, type=int)
    parser.add_argument("--app-home", default="")
    args = parser.parse_args()

    if args.app_home:
        os.environ["HANIME_APP_HOME"] = args.app_home

    if port_is_open(args.host, args.port):
        webbrowser.open(f"http://{args.host}:{args.port}/")
        return

    threading.Thread(target=open_when_ready, args=(args.host, args.port), daemon=True).start()
    uvicorn.run(create_app(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
