from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

password = "testpassword"
hashed = pwd_context.hash(password)
print(f"Password: {password}")
print(f"Hash: {hashed}")
print(f"Verify: {pwd_context.verify(password, hashed)}")
