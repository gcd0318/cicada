from config import PORT
from model import app, db, logger

if ('__main__' ==  __name__):
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=PORT)
