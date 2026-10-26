"""Automatisk retting av FY1-08-strompris-og-energi.

Hver sjekk i SJEKKER er én deltest, og poengene fordeles likt på dem.
De samme sjekkene ligger i "Test løsningen din"-cellen nederst i notebooken.
"""
import pytest

from notebook_loader import last_notebook

def naer(a, b, rel=1e-3):
    """Sant hvis tallet a er innenfor rel (relativt) av b."""
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) <= rel * abs(b)


def S(tekst):
    """Gjør tekst om til et sympy-uttrykk, f.eks. S("x**2 - 1")."""
    import sympy
    return sympy.sympify(tekst, locals={n: sympy.Symbol(n) for n in ("N", "O", "Q", "S")})


def lik(a, b):
    """Sant hvis a og b er matematisk like.

    Lister og mengder sammenlignes uten hensyn til rekkefølge, tupler (koordinater) i rekkefølge.
    """
    import sympy
    if a is None:
        return False
    if isinstance(b, tuple):
        if not isinstance(a, (tuple, list, sympy.Tuple)) or len(a) != len(b):
            return False
        return all(lik(x, y) for x, y in zip(a, b))
    if isinstance(b, (list, set)):
        if isinstance(a, sympy.FiniteSet):
            a = list(a)
        if not isinstance(a, (list, tuple, set)) or len(a) != len(b):
            return False
        rest = list(a)
        for y in b:
            for i, x in enumerate(rest):
                if lik(x, y):
                    del rest[i]
                    break
            else:
                return False
        return True
    if isinstance(b, dict):
        if not isinstance(a, dict) or len(a) != len(b):
            return False
        a = {str(k): v for k, v in a.items()}
        return all(str(k) in a and lik(a[str(k)], v) for k, v in b.items())
    try:
        a, b = sympy.sympify(a), sympy.sympify(b)
    except (sympy.SympifyError, TypeError):
        return False
    vanlige = lambda u: u.subs({s: sympy.Symbol(s.name) for s in u.free_symbols})
    a, b = vanlige(a), vanlige(b)
    if isinstance(a, sympy.Set) or isinstance(b, sympy.Set):
        return a == b
    if getattr(b, "is_Relational", False):
        return a == b
    try:
        return sympy.simplify(a - b) == 0
    except TypeError:
        return a == b

oppgave = last_notebook("oppgave")

SJEKKER = [
    ('1', 'priser(data) skal gi listen med NOK_per_kWh', "list(priser([{'NOK_per_kWh': 0.10592, 'EUR_per_kWh': 0.01012, 'EXR': 10.4665, 'time_start': '2026-10-25T00:00:00+02:00', 'time_end': '2026-10-25T01:00:00+02:00'}, {'NOK_per_kWh': 0.20786, 'EUR_per_kWh': 0.01986, 'EXR': 10.4665, 'time_start': '2026-10-25T01:00:00+02:00', 'time_end': '2026-10-25T02:00:00+02:00'}, {'NOK_per_kWh': 0.58162, 'EUR_per_kWh': 0.05557, 'EXR': 10.4665, 'time_start': '2026-10-25T02:00:00+02:00', 'time_end': '2026-10-25T03:00:00+02:00'}])) == [0.10592, 0.20786, 0.58162]"),
    ('2_energi', 'energi_kwh(2000, 0.5) skal gi 1 kWh', 'naer(energi_kwh(2000, 0.5), 1) and naer(energi_kwh(60, 24), 1.44)'),
    ('2_kostnad', 'kostnad(1000, 24, 1.5) skal gi 36 kr', 'naer(kostnad(1000, 24, 1.5), 36) and naer(kostnad(2000, 0.05, 2), 0.2)'),
    ('3', 'dusjenergi_kwh(10, 12, 30) skal gi ca. 4.19 kWh', 'naer(dusjenergi_kwh(10, 12, 30), 120 * 4186 * 30 / 3.6e6, rel=1e-4)'),
    ('4_eksempel', 'billigste_start([3, 1, 2, 5, 0.5, 0.4], 2) skal gi 4', 'billigste_start([3, 1, 2, 5, 0.5, 0.4], 2) == 4'),
    ('4_start', 'billigste_start([1, 1, 9, 9], 2) skal gi 0', 'billigste_start([1, 1, 9, 9], 2) == 0 and billigste_start([5, 4, 3, 2, 1], 3) == 2'),
    ('4_en', 'billigste_start([4, 2, 3], 1) skal gi 1', 'billigste_start([4, 2, 3], 1) == 1'),
]


@pytest.mark.parametrize(
    "beskrivelse,uttrykk", [s[1:] for s in SJEKKER], ids=[s[0] for s in SJEKKER]
)
def test_sjekk(beskrivelse, uttrykk):
    navnerom = {**vars(oppgave), "naer": naer, "lik": lik, "S": S}
    assert eval(uttrykk, navnerom), beskrivelse
