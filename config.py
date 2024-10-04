from datetime import timedelta
import os

rds_password = os.getenv('RDS_PASSWORD')

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
        "bucket_name" : "timechronos"
    },
    "server": {
        "db": f"postgresql://postgres:{rds_password}@tpnretail.can7hv0elab6.us-east-2.rds.amazonaws.com:5432/postgres",
        "redis":"redis://:JustWin12@localhost:6379/0",
        "jwt-access-token-expiration": timedelta(minutes=30),
        "jwt-refresh-token-expiration": timedelta(days=30),
        "aws_access_key_id" : os.getenv('AWS_ACCESS_KEY_ID'),
        "aws_secret_access_key_id" : os.getenv('AWS_SECRET_ACCESS_KEY'),
        "bucket_name" : "timechronos"
    }
}