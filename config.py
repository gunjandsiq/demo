from datetime import timedelta
from dotenv import load_dotenv
import os

load_dotenv()

rds_password = os.getenv('RDS_PASSWORD')
rds_user = os.getenv('RDS_USER')
rds_port = os.getenv('RDS_PORT')
rds_host = os.getenv('RDS_HOST')
rds_db = os.getenv('RDS_DB_NAME')

environment = {
    "local":{
        "db": "postgresql://postgres:first@localhost:5432/postgres",
        "redis": "redis://:JustWin12@localhost:6379/0",
        "celery-broker": "redis://:JustWin12@localhost:6379/0",
        "celery-backend": "db+postgresql://postgres:first@localhost:5432/postgres",
        "jwt-access-token-expiration": timedelta(minutes=30),
        "jwt-refresh-token-expiration": timedelta(days=30),
        "aws_access_key_id" : os.getenv('AWS_ACCESS_KEY_ID'),
        "aws_secret_access_key_id" : os.getenv('AWS_SECRET_ACCESS_KEY'),
        "bucket_name" : os.getenv('BUCKET_NAME'),
        "jwt-private-key": open("private_key.pem", "r").read(),
        "jwt-public-key": open("public_key.pem", "r").read(),
        "jwt-algo": "RS256",
        "url": "http://dev.timechronos.com"
    },
    "server": {
        "db": f"postgresql://{rds_user}:{rds_password}@{rds_host}:{rds_port}/{rds_db}",
        "redis":"redis://:JustWin12@localhost:6379/0",
        "jwt-access-token-expiration": timedelta(minutes=30),
        "jwt-refresh-token-expiration": timedelta(days=30),
        "aws_access_key_id" : os.getenv('AWS_ACCESS_KEY_ID'),
        "aws_secret_access_key_id" : os.getenv('AWS_SECRET_ACCESS_KEY'),
        "bucket_name" : os.getenv('BUCKET_NAME'),
        "jwt-private-key": open("private_key.pem", "r").read(),
        "jwt-public-key": open("public_key.pem", "r").read(),
        "jwt-algo": "RS256",
        "url": "dev.timechronos.com"
    }
}