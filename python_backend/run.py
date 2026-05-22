import argparse
import os

import uvicorn


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=58080, type=int)
    parser.add_argument("--app-home", default="")
    args = parser.parse_args()
    if args.app_home:
        os.environ["HANIME_APP_HOME"] = args.app_home
    uvicorn.run("app.main:create_app", factory=True, host=args.host, port=args.port)
