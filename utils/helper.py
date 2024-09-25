from flask import jsonify, Blueprint
from utils.models import db, HistoryLogger, TimeStamp
import bcrypt, boto3, os, json
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, create_refresh_token, jwt_required, get_jwt
from itsdangerous import URLSafeTimedSerializer
from celery_config import celery
from sqlalchemy.inspection import inspect

jwt = JWTManager()
auth = Blueprint('auth', __name__)

aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key_id = os.getenv('AWS_SECRET_ACCESS_KEY')

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
        
class SesHelper:

    @celery.task(bind=True)
    def send_email(self, source, destination, subject, body_html, *args, **kwargs):
        try:
            client_ses = boto3.client('ses', aws_access_key_id=aws_access_key_id,
                                  aws_secret_access_key=aws_secret_access_key_id, region_name='us-east-1')
            
            response = client_ses.send_email(
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

class S3Helper:

    def __init__(self):
        self.client_s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id,
                                  aws_secret_access_key=aws_secret_access_key_id, region_name='us-east-1')
        
        # self.bucket_name = os.getenv('AWS_BUCKET_NAME')
        # if not self.bucket_name:
        #     raise ValueError("AWS_BUCKET_NAME environment variable is not set")
        
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
