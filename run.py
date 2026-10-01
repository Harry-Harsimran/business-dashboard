
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import db
from app import app


def main():
    if not db.DB_PATH.exists():
        print("No database found — generating sample dataset...")
        db.init_db()
    app.run(debug=False, host="127.0.0.1", port=5000)


if __name__ == "__main__":
    main()
