import os
from dotenv import load_dotenv
from waitress import serve
from app import create_app
from app.utils import print_startup_banner

load_dotenv()
app = create_app()

if __name__ == '__main__':
    host = os.getenv('APP_HOST', '0.0.0.0')
    port = int(os.getenv('APP_PORT', 5050))
    print_startup_banner(port)
    serve(app, host=host, port=port)
