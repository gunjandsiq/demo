from celery import Celery

celery = Celery(__name__, broker="redis://:JustWin12@localhost:6379/0")