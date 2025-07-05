"""
Basit test dosyası
"""
import pytest

def test_basic():
    """Basit test"""
    assert 1 + 1 == 2

def test_string():
    """String test"""
    assert "hello" + " world" == "hello world"

@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (2, 3, 5),
    (3, 4, 7),
])
def test_add(a, b, expected):
    """Parametrize test"""
    assert a + b == expected 