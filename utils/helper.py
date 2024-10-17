from flask import jsonify, Blueprint
from utils.models import db, HistoryLogger, TimeStamp
import bcrypt, boto3, os, json
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, create_refresh_token, jwt_required, get_jwt
from itsdangerous import URLSafeTimedSerializer
from celery_config import celery
from sqlalchemy.inspection import inspect
from sqlalchemy.sql import text
from celery_config import env

jwt = JWTManager()
auth = Blueprint('auth', __name__)

class DbHelper:   

    def add_record(self, query):
        try:
            db.session.add(query)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return str(e)
        # finally:
        #     db.session.close()

    def update_record(self):
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return str(e)
        # finally:
        #     db.session.close()

    def delete_record(self, query):
        try:
            db.session.delete(query)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return str(e)
        finally:
            db.session.close()

    def clean_record(self, record):
        return {
            column.key: getattr(record, column.key)
            for column in inspect(record).mapper.column_attrs
            if isinstance(getattr(record, column.key), (str, int, float, bool, type(None), dict, list))
        }

    def log_history(self, table, record, operation, old_record=None, user_id=None):
        old_data = None
        new_data = None

        if operation == 'update':
            old_data = self.clean_record(old_record) 

        if operation in ['insert', 'update']:
            new_data = self.clean_record(record)
            if operation == 'insert':
                db.session.flush()

        if operation == 'delete':
            old_data = self.clean_record(record)

        history_entry = HistoryLogger(
            table_name=table.__tablename__,
            record_id=str(record.id),
            operation=operation,
            old_data=json.dumps(old_data) if old_data else None,
            new_data=json.dumps(new_data) if new_data else None,
            user_id=user_id
        )

        self.add_record(history_entry)

    def log_insert(self, record, user_id=None):
        self.log_history(record.__class__, record, 'insert', user_id)

    def log_update(self, record, old_record=None, user_id=None):
        self.log_history(record.__class__, record, 'update', old_record=old_record, user_id=user_id)

    def log_delete(self, record, user_id=None):
        self.log_history(record.__class__, record, 'delete', user_id)

class PasswordHelper:
    def hash_password(self, password):
        try:
            return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        except Exception as e:
            return jsonify({'message': 'Error hashing password error', 'status': 500}), 500

    def check_password(self,password, hashed_password):
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            return jsonify({'message': 'Error checking password error', 'status': 500}), 500
        
class CodeHelper:

    def __init__(self):
        self.serializer = URLSafeTimedSerializer("secret_key")
        
    def generate_reset_token(self, email):
        return self.serializer.dumps(email, salt='password-reset-salt')
    
    def confirm_reset_token(self, token, expiration=3600):
        try:
            email = self.serializer.loads(
                token,
                salt='password-reset-salt',
                max_age=expiration
            )
        except Exception:
            return None
        return email
        
class AuthenticationHelper:
    
    def create_access_token(self, identity, claims):
        return create_access_token(identity=identity, additional_claims=claims)
    
    def create_refresh_token(self, identity, claims):
        return create_refresh_token(identity=identity, additional_claims=claims)
    

class AuthorizationHelper:

    @jwt_required()
    def get_jwt_token(self):
        try:
            identity = get_jwt_identity()
            claims = get_jwt()

            role = claims.get('role')
            company_id = claims.get('company_id')
            user_id = claims.get('user_id')
            jti = claims.get('jti')

            if not identity:
                return jsonify({'message': 'Token not found', 'status': 401}), 401

            if not role :
                return jsonify({'message': 'Invalid token: role not found', 'status': 401}), 401
            
            if not company_id:
                return jsonify({'message': 'Invalid token: company_id not found', 'status': 401}), 401

            if not claims:
                return jsonify({'message': 'Token not found', 'status': 401}), 401
            
            if not user_id:
                return jsonify({'message': 'Invalid token: user_id not found', 'status': 401}), 401
            
            return {
                'message': 'Access granted',
                'email': identity,
                'role': role,
                'company_id': company_id,
                'user_id': user_id,
                'jti': jti
            }
        except Exception as e:
            return jsonify({'message': 'Error getting token error', 'status': 500}), 500
        
class AwsHelper:

    def __init__(self):
        self.client_sqs = boto3.client('sqs', region_name='us-east-2')
        
        self.client_ses = boto3.client('ses', region_name='us-east-1')
        
        if not env['aws_access_key_id'] or not env['aws_secret_access_key_id']:
            raise ValueError("AWS credentials are missing. Please set 'aws_access_key_id' and 'aws_secret_access_key_id'.")

    def send_email(self, source, destination, subject, body_html):
        try:
            
            response = self.client_ses.send_email(
                Source=source,  # sender's email address
                Destination={'ToAddresses': [destination]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {
                        'Html': {'Data': body_html}
                    }
                }
            )
            print("Email send successfully")
        except Exception as e:
            print(f"An error occurred: {e}")
            return str(e)
        
    def send_message(self, queue_url, message_body):
        try:
            response = self.client_sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=message_body
            )
            print("Message sent successfully")
        except Exception as e:
            print(f"An error occurred: {e}")
            return str(e)
        
    

class S3Helper:

    def __init__(self):
        self.client_s3 = boto3.client('s3', aws_access_key_id=env['aws_access_key_id'],
                                  aws_secret_access_key=env['aws_secret_access_key_id'], region_name='us-east-2')
        
        
    # Returns a list of all buckets 
    def bucket_list_names(self):
        try:
            bucket_list = []
            response = self.client_s3.list_buckets()
            for bucket in response['Buckets']:
                bucket_list.append(bucket['Name'])
            return bucket_list
        except Exception as e:
            print(f"An error occurred: {e}")
            return str(e)
        
    # Returns all objects in a bucket   
    def objects_list(self,bucket_name, prefix=''): 
        try:
            response = self.client_s3.list_objects_v2(
                Bucket = bucket_name,
                Prefix = prefix  # optional
            )
            return response
        except Exception as e:
            print(f"An error occurred: {e}")
            return str(e)
        
    def create_s3_bucket(self, bucket_name):
        try:
            response = self.client_s3.create_bucket(
                Bucket = bucket_name,
                CreateBucketConfiguration={'LocationConstraint': 'us-east-2'}
            )
            print(response)
            return response
        except Exception as e:
            print(f"An error occurred: {e}")
            return str(e)
    
    def upload_file_to_object(self,file_path,bucket_name,file_key):
        try:
            response = self.client_s3.upload_file(
                Filename = file_path,                                                
                Bucket = bucket_name,                                                 
                Key = file_key                                                    
            )           
            return response
        except Exception as e:
            print(f"An error occurred: {e}")
            return str(e)
        
    # Adds an object to a bucket    
    def put_object_in_s3(self,file,bucket_name,file_key):
        try:
            response = self.client_s3.put_object(
                Body = file,
                Bucket = bucket_name,
                Key = file_key 
            )
            return response
        except Exception as e:
            print(f"An error occurred: {e}")
            return str(e)
        
    # Retrieves an object from s3    
    def get_object(self,bucket_name,file_key):
        try:
            response = self.client_s3.get_object(
                Bucket = bucket_name,
                Key = file_key 
            )
            return response
        except Exception as e:
            print(f"An error occurred: {e}")
            return str(e)
        
    def generate_presigned_of_img(self, bucket_name, file_key):
        try:
            response = self.client_s3.generate_presigned_url(
                ClientMethod = 'get_object',
                Params = {
                    'Bucket': bucket_name,
                    'Key': file_key,
                },
                ExpiresIn= 604800
            )
            return response
        except Exception as e:
            print(f"An error occurred: {e}")
            return str(e)
        
def lambda_handler(event, context):
        try:
            ses = AwsHelper()
            print("Processing SQS messages...")
        
            for record in event['Records']:
                message = json.loads(record['body'])
                
                source = message['source']
                destination = message['destination']
                subject = message['subject']
                body_html = message['body_html']
                
                ses.send_email(source, destination, subject, body_html)

            return {
                'statusCode': 200,
                'body': 'Emails processed successfully'
            }
        except Exception as e:
            print(f"An error occurred: {e}")
            return str(e) 
        
# DimDate query        
dim_date_insert = """
INSERT INTO dim_date
SELECT TO_CHAR(datum,'YYYYMMDD')::INT AS date_id,
       datum AS date_actual,
       EXTRACT(epoch FROM datum) AS epoch,
       TO_CHAR(datum,'Dth') AS day_suffix,
       TO_CHAR(datum,'Day') AS day_name,
       EXTRACT(isodow FROM datum) AS day_of_week,
       EXTRACT(DAY FROM datum) AS day_of_month,
       datum - DATE_TRUNC('quarter',datum)::DATE +1 AS day_of_quarter,
       EXTRACT(doy FROM datum) AS day_of_year,
       TO_CHAR(datum,'W')::INT AS week_of_month,
       EXTRACT(week FROM datum) AS week_of_year,
       TO_CHAR(datum,'YYYY"-W"IW-D') AS week_of_year_iso,
       EXTRACT(MONTH FROM datum) AS month_actual,
       TO_CHAR(datum,'Month') AS month_name,
       TO_CHAR(datum,'Mon') AS month_name_abbreviated,
       EXTRACT(quarter FROM datum) AS quarter_actual,
       CASE
         WHEN EXTRACT(quarter FROM datum) = 1 THEN 'First'
         WHEN EXTRACT(quarter FROM datum) = 2 THEN 'Second'
         WHEN EXTRACT(quarter FROM datum) = 3 THEN 'Third'
         WHEN EXTRACT(quarter FROM datum) = 4 THEN 'Fourth'
       END AS quarter_name,
       EXTRACT(isoyear FROM datum) AS year_actual,
       datum +(1 -EXTRACT(isodow FROM datum))::INT AS first_day_of_week,
       datum +(7 -EXTRACT(isodow FROM datum))::INT AS last_day_of_week,
       datum +(1 -EXTRACT(DAY FROM datum))::INT AS first_day_of_month,
       (DATE_TRUNC('MONTH',datum) +INTERVAL '1 MONTH - 1 day')::DATE AS last_day_of_month,
       DATE_TRUNC('quarter',datum)::DATE AS first_day_of_quarter,
       (DATE_TRUNC('quarter',datum) +INTERVAL '3 MONTH - 1 day')::DATE AS last_day_of_quarter,
       TO_DATE(EXTRACT(isoyear FROM datum) || '-01-01','YYYY-MM-DD') AS first_day_of_year,
       TO_DATE(EXTRACT(isoyear FROM datum) || '-12-31','YYYY-MM-DD') AS last_day_of_year,
       TO_CHAR(datum,'MMYYYY') AS mmyyyy,
       TO_CHAR(datum,'MMDDYYYY') AS mmddyyyy,
       CASE
         WHEN EXTRACT(isodow FROM datum) IN (6,7) THEN TRUE
         ELSE FALSE
       END AS weekend_indr
FROM (SELECT '2016-01-01'::DATE+ SEQUENCE.DAY AS datum
      FROM GENERATE_SERIES (0,29219) AS SEQUENCE (DAY)
      GROUP BY SEQUENCE.DAY) DQ
ORDER BY 1;
"""
# Method to load dimdate
def load_dim_date():
    try:
        with db.engine.connect() as connection:
            connection.execute(text(dim_date_insert))
            connection.commit()
        print("Dim Date data loaded successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify(f"An error occurred: {str(e)}"), 500
