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

    def __init__(self):
        self.auth = AuthorizationHelper()
        self.token = self.auth.get_jwt_token()
        self.user_id = self.token.get('user_id')

    def add_record(self, query):
        try:
            query.created_by = self.user_id
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
            
            print(jti)
            
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

