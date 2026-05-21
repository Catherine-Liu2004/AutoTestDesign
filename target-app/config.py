import os


class Config:
    # Flask core
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-todoapp-2026')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///./todoapp.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Authentication rules (BVA / Decision-Table targets)
    JWT_EXPIRY_HOURS: int = 24
    MAX_FAILED_LOGINS: int = 5        # lock account after N consecutive failures
    LOCKOUT_MINUTES: int = 15         # lock duration in minutes

    # Task limits
    MAX_TASKS_PER_USER: int = 100     # max tasks a user may own


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_EXPIRY_HOURS = 1
