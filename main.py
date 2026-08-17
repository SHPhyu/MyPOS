from pos.db import init_db
from pos.app import run

if __name__ == "__main__":
    init_db()
    run()
