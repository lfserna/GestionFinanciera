import os
from dotenv import load_dotenv
from waitress import serve
from app import app
from app.utils import print_startup_banner

load_dotenv()

host = os.getenv('APP_HOST', '0.0.0.0')
port = int(os.getenv('APP_PORT', 5050))

if __name__ == '__main__':
    print_startup_banner(port)
    serve(app, host=host, port=port)
