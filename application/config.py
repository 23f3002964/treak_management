import os

class Config:
    SECRET_KEY = 'trekking-secret-key-12345'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
        os.path.abspath(os.path.dirname(__file__)), '..', 'instance', 'trekking.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
