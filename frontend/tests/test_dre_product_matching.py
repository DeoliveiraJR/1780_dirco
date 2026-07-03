import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pages.dre import _produto_eh_equivalente


def test_produto_eh_equivalente_matches_singular_and_plural():
    assert _produto_eh_equivalente("111111227: CHEQUES ESPECIAIS", "Cheque especial")
    assert _produto_eh_equivalente("111111227: CHEQUES ESPECIAIS", "Cheques especiais")
    assert _produto_eh_equivalente("111111227: CHEQUE ESPECIAL", "Cheques especiais")
