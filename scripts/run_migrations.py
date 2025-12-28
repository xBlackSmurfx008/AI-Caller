"""Run database migrations"""

import subprocess
import sys

if __name__ == "__main__":
    result = subprocess.run(["alembic", "upgrade", "head"], check=False)
    sys.exit(result.returncode)

