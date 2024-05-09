from src import create_app
from config import settings


if __name__ == "__main__":

    app = create_app()
    app.run(host= settings.HOST,
            port= settings.PORT,
            debug= settings.DEBUG)
    
