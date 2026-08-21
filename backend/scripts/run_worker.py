import asyncio
import os
import socket

from app.db.database import async_session_maker
from app.services.jobs import run_worker_forever


def main() -> None:
    worker_id = os.environ.get("WORKER_ID") or f"{socket.gethostname()}-{os.getpid()}"
    asyncio.run(run_worker_forever(async_session_maker, worker_id=worker_id))


if __name__ == "__main__":
    main()
