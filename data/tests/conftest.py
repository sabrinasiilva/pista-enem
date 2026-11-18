import sys
from pathlib import Path

# os scripts de data/ são importados como módulos soltos
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
