import random
import string

def random_lower_string() -> str:
    """Generate random lowercase string"""
    return "".join(random.choices(string.ascii_lowercase, k=32))

def random_email() -> str:
    """Generate random email"""
    return f"{random_lower_string()}@example.com"

def random_integer() -> int:
    """Generate random integer"""
    return random.randint(1, 1000)

def random_float() -> float:
    """Generate random float"""
    return random.uniform(0, 100)

def random_bool() -> bool:
    """Generate random boolean"""
    return random.choice([True, False]) 