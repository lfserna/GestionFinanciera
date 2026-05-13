import sys
from werkzeug.security import generate_password_hash

password = sys.argv[1] if len(sys.argv) > 1 else 'hola123'
print(generate_password_hash(password))
