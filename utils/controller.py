from utils.helper import DbHelper, PasswordHelper, AuthenticationHelper, AuthorizationHelper, CodeHelper, SesHelper, get_jwt_identity, jwt_required, S3Helper
from utils.models import db,User, Client, Project, Task, TaskHours, Company, Timesheet, DimDate, Approval, BlacklistToken
from flask import jsonify, request
from sqlalchemy import func

class Controller:

    def __init__(self):
        self.password_helper = PasswordHelper()
        self.authentication_helper = AuthenticationHelper()

    def register(self):
        try:
            db_helper = DbHelper()
            ses = SesHelper()
            data = request.get_json()
            required_fields = ['company_name', 'firstname', 'email', 'password', 'gender', 'phone']
            if not data or not all(data.get(key) for key in required_fields):
                return jsonify({'message': 'Invalid input: All fields are required', 'status': 400}), 400

            company_name = data['company_name']
            firstname = data['firstname']
            lastname = data.get('lastname')
            role = data.get('role', 'Admin')
            email = data['email']
            phone = data['phone']
            gender = data['gender']
            password = data['password']

            hashed_password = self.password_helper.hash_password(password)
            
            existing_company = Company.query.filter_by(name=company_name, is_archived = False).first()
            if existing_company:
                return jsonify({'message': 'Company with this name already exists', 'status': 409}), 409
            
            if existing_company:
                existing_user = User.query.filter_by(email=email, company_id=existing_company.id, is_archived = False).first()
                if existing_user:
                    return jsonify({'message': 'User with this email already exists in the company', 'status': 409}), 409 
            
            if 'phone' in data:
                phone = data['phone']
                if not phone.isdigit():
                    return jsonify({'message': 'Invalid input: Please write correct no.', 'status': 400}), 400

            company = Company(name=company_name)
            db_helper.add_record(company)

            user = User(firstname=firstname, lastname=lastname, role=role, email=email, phone=phone, gender=gender, password=hashed_password, company_id=company.id)
            db_helper.add_record(user)
            
            reset_url = "http://localhost:5173/login"
            subject = "Welcome to TimeChronos - Simplify your Time Management"
            body_html = f"""
            <h1>Welcome to TimeChronos!</h1>
            <p>Thank you for signing up {user.firstname} for TimeChronos. We're excited to have you on board.</p>
            <p>Please click on the link to login: <a href={reset_url}>{reset_url}</a></p>"""

            ses.send_email.delay(source='contact@digitalshelfiq.com', destination=email, subject=subject, body_html=body_html)

            if user.role == 'Admin':
                user.supervisor_id = user.id
                user.approver_id = user.id
                db_helper.update_record()
            return jsonify({'message': 'Company and user added successfully', 'status': 201})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
    def login(self):
        try:
            data = request.get_json()
            if not data or not 'email' in data or not 'password' in data:
                return jsonify({'message': 'Invalid input: email and password required', 'status': 400}), 400

            email = data['email']
            password = data['password']

            user = User.query.filter_by(email=email, is_archived = False, is_active = True).first()
            if not user:
                return jsonify({'message': 'Incorrect email or password', 'status': 401}), 401

            if not self.password_helper.check_password(password, user.password):
                return jsonify({'message': 'Incorrect email or password', 'status': 401}), 401
            
            claims = {
                'user_name': user.firstname,
                'user_id': str(user.id),
                'company_id': str(user.company_id),
                'role': user.role
            }

            access_token = self.authentication_helper.create_access_token(user.email, claims)
            refresh_token = self.authentication_helper.create_refresh_token(user.email, claims)
            return jsonify({'access_token': access_token,
                            'refresh_token': refresh_token,
                            'status': 200})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
    @jwt_required(refresh= True)   
    def refresh_token(self):
        try:
            current_user = get_jwt_identity()
            user = User.query.filter_by(email=current_user, is_archived = False).first()
            claims = {
                'user_name': user.firstname,
                'user_id': str(user.id),
                'company_id': str(user.company_id),
                'role': user.role
            }
            new_access_token = self.authentication_helper.create_access_token(current_user, claims)                      
            return jsonify(access_token=new_access_token), 200
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
    def forget_password(self):
        try:
            code = CodeHelper()
            ses = SesHelper()
            data = request.get_json()
            if not data or 'email' not in data:
                return jsonify({'message': 'Invalid input: email required', 'status': 400}), 400

            email = data['email']
            user = User.query.filter_by(email=email, is_archived = False).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404

            token = code.generate_reset_token(email)
            reset_url = f"http://localhost:5173/reset-password/{token}"

            subject = "Password Reset Request"
            body_html = f"To reset your password, click the following link: <a href={reset_url}>{reset_url}</a>"
            ses.send_email.delay(source='contact@digitalshelfiq.com', destination=email, subject=subject, body_html=body_html)

            return jsonify({'message': 'Password reset link sent to your email', 'status': 200}), 200
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
    def reset_password_with_token(self, token):
        try:
            db_helper = DbHelper()
            ses = SesHelper()
            code = CodeHelper()
            email = code.confirm_reset_token(token)
            if not email:
                return jsonify({'message': 'Invalid or expired token', 'status': 401}), 401

            data = request.get_json()
            if not data or 'password' not in data:
                return jsonify({'message': 'Password is required', 'status': 400}), 400
            
            new_password = data['password']

            user = User.query.filter_by(email=email, is_archived = False).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404

            hashed_password = self.password_helper.hash_password(new_password)
            user.password = hashed_password
            db_helper.update_record(user)

            subject = "Password reset successfully"
            body_html = f"Your password has been successfully reset."
            ses.send_email.delay(source='contact@digitalshelfiq.com', destination=email, subject=subject, body_html=body_html)

            return jsonify({'message': 'Password reset successfully', 'status': 200}), 200
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def change_password(self):
        try:
            db_helper = DbHelper()
            ses = SesHelper()
            auth = AuthorizationHelper()
            token = auth.get_jwt_token()
            if not token:
                return jsonify({'message': 'Authentication token is missing', 'status': 401}), 401

            email = token.get('email')
            company_id = token.get('company_id')
            
            data = request.get_json()
            if not data or 'current_password' not in data or 'new_password' not in data:
                return jsonify({'message': 'Invalid input: current_password and new_password required', 'status': 400}), 400
            
            current_password = data['current_password']
            new_password = data['new_password']

            user = User.query.filter_by(email=email, company_id=company_id, is_archived = False).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404
            
            if not self.password_helper.check_password(current_password, user.password):
                return jsonify({'message': 'Current password is incorrect', 'status': 401}), 401
            
            hashed_password = self.password_helper.hash_password(new_password)
            user.password = hashed_password
            db_helper.update_record(user)

            subject = "Password change confirmation"
            body_html = f"""
            <p>Dear{user.firstname},</p>
            <p>This is to confirm that the password of your account has been successfully changed. Your account is now secured with the new password that you have set.</p>
            <p>If you did not change your password, please contact us immediately to report any unauthorized access to your account</p>
            <p>Thank you for using our service.</p>
            <p>Best Regards,</p>
            <p>The TimeChronos Team</p>"""

            ses.send_email.delay(source='contact@digitalshelfiq.com', destination=email, subject=subject, body_html=body_html)

            return jsonify({'message': 'Password changed successfully', 'status': 200})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
    def logout(self):
        try:
            db_helper = DbHelper()
            auth = AuthorizationHelper()
            token = auth.get_jwt_token()
            if not token:
                return jsonify({'message': 'Authentication token is missing', 'status': 401}), 401

            email = token.get('email')
            company_id = token.get('company_id')
            
            user = User.query.filter_by(email=email, company_id=company_id, is_archived = False).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404
            
            token_jti = token.get('jti')
            if not (token_jti):
                return jsonify({'message': 'Failed to log out. Token invalidation failed', 'status': 500}), 500
            
            query = BlacklistToken(jti=token_jti)
            db_helper.add_record(query)

            return jsonify({'message': 'User logged out successfully', 'status': 200}), 200
                    
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
class CompanyController:

    def __init__(self):
        self.db_helper = DbHelper()
        self.auth = AuthorizationHelper()
        self.token = self.auth.get_jwt_token()

    def update_company(self):
        try:
            if not self.token:
                return jsonify({'message': 'Authentication token is missing', 'status': 401}), 401

            company_id = self.token.get('company_id')

            data = request.get_json()
            company = Company.query.filter_by(id=company_id, is_archived = False).first()
            if not company:
                return jsonify({'message': 'Company not found', 'status': 404}), 404

            if 'name' in data:
                new_name = data['name']

                existing_company = Company.query.filter_by(name=new_name, is_archived=False).first()
                if existing_company and existing_company.id != company_id:
                    return jsonify({'message': 'A company with the same name already exists.', 'status': 400}), 400
                
                company.name = new_name

            self.db_helper.update_record(company)
            return jsonify({'message': 'Company updated successfully', 'status': 200})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def delete_company(self):
        try:
            if not self.token:
                return jsonify({'message': 'Authentication token is missing', 'status': 401}), 401

            company_id = self.token.get('company_id')

            company = Company.query.filter_by(id=company_id, is_archived = False).first()
            if not company:
                return jsonify({'message': 'Company not found', 'status': 404}), 404

            company.is_archived = True
            company.is_active = False
            self.db_helper.update_record(company)
            return jsonify({'message': 'Company deleted successfully', 'status': 200})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
class UserController:

    def __init__(self):
        self.db_helper = DbHelper()
        self.auth = AuthorizationHelper()
        self.token = self.auth.get_jwt_token()

    def add_user(self):
        try:
            ses = SesHelper()
            password_helper = PasswordHelper()
            data = request.get_json()
            required_fields = ['firstname', 'email', 'role', 'password', 'gender','supervisor_id', 'approver_id']
            if not data or not all(data.get(key) for key in required_fields):
                return jsonify({'message': 'Invalid input: All fields are required', 'status': 400}), 400
            
            if not self.token:
                return jsonify({'message': 'Token not found', 'status': 401}), 401
            
            company_id = self.token.get('company_id')
            
            email = data['email']
            firstname = data['firstname']
            lastname = data.get('lastname')
            role = data['role']
            phone = data.get('phone')
            gender = data['gender']
            password = data['password']
            supervisor_id = data['supervisor_id']
            approver_id = data['approver_id']

            hashed_password = password_helper.hash_password(password)

            if 'phone' in data:
                phone = data['phone']
                if not phone.isdigit():
                    return jsonify({'message': 'Invalid input: Please write correct no.', 'status': 400}), 400

            existing_user = User.query.filter_by(email=email, company_id=company_id, is_archived = False).first()
            if existing_user:
                return jsonify({'message': 'User already exists with this email', 'status': 409}), 409 
            
            user = User(firstname=firstname, lastname=lastname, role=role, email=email, phone=phone, gender=gender, password=hashed_password, company_id=company_id, supervisor_id=supervisor_id, approver_id=approver_id)
            self.db_helper.add_record(user) 

            supervisor = User.query.filter_by(id=supervisor_id, company_id=company_id, is_archived = False).first()
            approver = User.query.filter_by(id=approver_id, company_id=company_id, is_archived=False).first()

            login_url = "http://localhost:5173/login"

            subject = "Timechronos Account Credentials"
            body_html = f"""
            <p>Dear {user.firstname},</p>
            <p> I hope this  message finds you well.</p>
            <p> I am pleased to inform you that an account has been successfully created for you on Timechronos by an administrator. To access your account, please use the following credentials:</p>
                    <p> Username: {user.email}</p> 
                    <p> Password: {password}</p>
            <p>You can log in to your account by clicking the button below:</p>
            <a href={login_url}>
                <button type="button">Login</button>
            </a>
            <p>We are excited to have you on board and look forward to seeing you on Timechronos!</p>
            <p>Best Regards,</p>
            <p>The TimeChronos Team</p>"""
            
            ses.send_email.delay(source='contact@digitalshelfiq.com', destination=email, subject=subject, body_html=body_html)

            return jsonify({
                'message': 'User added successfully', 
                'id': user.id,
                'firstname': user.firstname,
                'lastname': user.lastname,
                'role': user.role,
                'email': user.email,
                'phone': user.phone,
                'gender': user.gender,
                'supervisor_name': supervisor.firstname,
                'approver_name': approver.firstname,
                'is_active': user.is_active,
                'status': 201})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def update_user(self):
        try:
            if not self.token:
                return jsonify({'message': 'Token not found', 'status': 401}), 401
            
            company_id = self.token.get('company_id')
        
            data = request.get_json()
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input: User ID is required', 'status': 400}), 400

            user_id = data['id']

            user = User.query.filter_by(id=user_id, company_id=company_id, is_archived = False).first()
            if not user:
                return jsonify({'message': 'User not found or does not belong to this company', 'status': 404}), 404
            
            if 'email' in data:
                existing_user = User.query.filter_by(email=data['email'], company_id=company_id, is_archived = False).first()
                if existing_user and existing_user.id != user_id:
                    return jsonify({'message': 'Email is already in use by another user', 'status': 409}), 409
            
            if 'phone' in data:
                phone = data['phone']
                if not phone.isdigit():
                    return jsonify({'message': 'Invalid input: Please write correct no.', 'status': 400}), 400
                
            if 'is_active' in data:
                user.is_active = data['is_active']
            
            for key, value in data.items():
                if key != 'id' and value: 
                    setattr(user, key, value)

            self.db_helper.update_record(user)

            return jsonify({'message': 'User updated successfully', 'status': 200}), 200
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def delete_user(self):
        try:
            if not self.token:
                return jsonify({'message': 'Token not found', 'status': 401}), 401
            
            company_id = self.token.get('company_id')
            
            data = request.get_json()
            if not data or 'id' not in data:
                return jsonify({'message': 'Invalid input: User ID is required', 'status': 400}), 400

            user_id = data['id']

            user = User.query.filter_by(id=user_id, company_id=company_id, is_archived = False).first()
            if not user:
                return jsonify({'message': 'User not found or does not belong to this company', 'status': 404}), 404
            
            user.is_archived = True
            user.is_active = False
            self.db_helper.update_record(user)
            return jsonify({'message': 'User deleted successfully', 'status': 200})
        except Exception as e:
            return jsonify({'message': str(e)}), 500
        
    def user_list(self):
        try:
            if not self.token:
                return jsonify({'message': 'Token not found', 'status': 401}), 401
            
            company_id = self.token.get('company_id')
            if not company_id:
                return jsonify({'message': 'Invalid token: company_id missing', 'status': 400}), 400
            
            sort_order = request.args.get('order', 'desc').lower()  
            user_name = request.args.get('name', type=str) 
            is_active = request.args.get('is_active', type=str)

            if sort_order not in ['asc', 'desc']:
                return jsonify({'message': 'Invalid sort_order value. Use "asc" or "desc".', 'status': 400}), 400

            if is_active is not None:
                if is_active.lower() not in ['true', 'false']:
                    return jsonify({'message': 'Invalid is_active value. Use "true" or "false".', 'status': 400}), 400
                is_active_bool = is_active.lower() == 'true'
            else:
                is_active_bool = None

            supervisor_alias = db.aliased(User)
            approver_alias = db.aliased(User)

            query = db.session.query(
                User.id,
                User.firstname,
                User.lastname,
                User.email,
                User.role,
                User.supervisor_id,
                User.approver_id,
                User.is_active,
                User.gender,
                User.created_date,
                supervisor_alias.firstname.label('supervisor_firstname'),
                supervisor_alias.lastname.label('supervisor_lastname'),
                approver_alias.firstname.label('approver_firstname'),
                approver_alias.lastname.label('approver_lastname')
            ).outerjoin(supervisor_alias, User.supervisor_id == supervisor_alias.id) \
            .outerjoin(approver_alias, User.approver_id == approver_alias.id) \
            .filter(
                User.company_id == company_id,
                User.is_archived == False
            )

            if user_name:
                full_name = func.concat(User.firstname,' ',User.lastname)
                query = query.filter(full_name.ilike(f'%{user_name}%'))

            if is_active_bool is not None:
                query = query.filter(User.is_active == is_active_bool)

            if sort_order == 'asc':
                query = query.order_by(User.created_date.asc(), User.created_time.asc())
            else:
                query = query.order_by(User.created_date.desc(), User.created_time.desc())

            users = query.all()
            if not users:
                return jsonify({'message': 'No users found for this company', 'status': 404}), 404

            result = []
            for user in users:
                result.append({
                    'id': str(user.id),
                    'name': f'{user.firstname} {user.lastname}' if user.firstname and user.lastname else user.firstname,
                    'firstname': user.firstname,
                    'lastname': user.lastname,
                    'email': user.email,
                    'role': user.role,
                    'is_active': user.is_active,
                    'gender': user.gender,
                    'supervisor_id': str(user.supervisor_id) if user.supervisor_id else None,
                    'supervisor_name': f'{user.supervisor_firstname} {user.supervisor_lastname}' if user.supervisor_firstname else None,
                    'approver_id': str(user.approver_id) if user.approver_id else None,
                    'approver_name': f'{user.approver_firstname} {user.approver_lastname}' if user.approver_firstname else None
                })

            return jsonify({'users': result, 'status': 200}), 200

        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
class ClientController:

    def __init__(self):
        self.db_helper = DbHelper()
        self.auth = AuthorizationHelper()                    
        self.token = self.auth.get_jwt_token()

    def add_client(self):
        try:
            data = request.get_json()
            required_fields = ['name', 'email']
            if not data or not all(data.get(key) for key in required_fields):
                return jsonify({'message': 'Invalid input: All fields are required', 'status': 400}), 400
            
            if not self.token:
                return jsonify({'message': 'Token not found', 'status': 401}), 401
            
            company_id = self.token.get('company_id')
            name = data['name']
            email = data['email']
            phone = data.get('phone')

            if not phone.isdigit():
                    return jsonify({'message': 'Invalid input: Please write correct no.', 'status': 400}), 400

            existing_client = Client.query.filter_by(email=email, company_id=company_id, is_archived = False).first()
            if existing_client:
                return jsonify({'message': 'Client already exists', 'status': 409}), 409 
            
            client = Client(name=name, email=email, phone=phone, company_id=company_id)
            self.db_helper.add_record(client)
            self.db_helper.log_insert(client, self.token.get('user_id'))

            return jsonify({
                'message': 'Client added successfully', 
                'id': client.id, 
                'name':client.name, 
                'email':client.email, 
                'phone':client.phone, 
                'status': 201
            })
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def update_client(self):
        try:
            if not self.token:
                return jsonify({'message': 'Token not found', 'status': 401}), 401
            
            company_id = self.token.get('company_id')
            
            data = request.get_json()
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input: Client ID is required', 'status': 400}), 400

            client_id = data['id']
            client = Client.query.filter_by(id=client_id, company_id=company_id, is_archived = False).first()
            if not client:
                return jsonify({'message': 'Client not found or does not belong to this company', 'status': 404}), 404
            
            if 'email' in data:
                existing_client = Client.query.filter_by(email=data['email'], company_id=company_id, is_archived = False).first()
                if existing_client and existing_client.id != client_id:
                    return jsonify({'message': 'Email is already in use by another client', 'status': 409}), 409
            
            if 'phone' in data and not data['phone'].isdigit():
                return jsonify({'message': 'Invalid input: Phone number must be exactly 10 digits', 'status': 400}), 400
            
            if 'is_active' in data:
                client.is_active = data['is_active']
            
            for key, value in data.items():
                if key != 'id' and value:
                    setattr(client, key, value)
            #self.db_helper.update_record()(old_client, client, self.token.get('user_id'))           
            self.db_helper.update_record()

            return jsonify({'message': 'Client updated successfully', 'status': 200})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def delete_client(self):
        try:
            if not self.token:
                return jsonify({'message': 'Token not found', 'status': 401}), 401
            
            company_id = self.token.get('company_id')
        
            data = request.get_json()
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input: Client ID is required', 'status': 400}), 400

            client_id = data['id']

            client = Client.query.filter_by(id=client_id, company_id=company_id, is_archived = False).first()
            if not client:
                return jsonify({'message': 'Client not found or does not belong to this company', 'status': 404}), 404
            
            client.is_archived = True
            client.is_active = False
            self.db_helper.update_record()
            self.db_helper.log_delete(client, self.token.get('user_id'))
            return jsonify({'message': 'Client deleted successfully', 'status': 200})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def client_list(self):
        try:
            company_id = self.token.get('company_id')
            if not company_id:
                return jsonify({'message': 'Invalid token: company_id missing', 'status': 400}), 400
            
            sort_order = request.args.get('order', 'desc').lower()  
            client_name = request.args.get('client', type=str) 
            is_active = request.args.get('is_active', type=str)

            if sort_order not in ['asc', 'desc']:
                return jsonify({'message': 'Invalid sort_order value. Use "asc" or "desc".', 'status': 400}), 400

            if is_active is not None:
                if is_active.lower() not in ['true', 'false']:
                    return jsonify({'message': 'Invalid is_active value. Use "true" or "false".', 'status': 400}), 400
                is_active_bool = is_active.lower() == 'true'
            else:
                is_active_bool = None

            query = Client.query.filter_by(company_id=company_id, is_archived=False)

            
            if client_name:
                query = query.filter(Client.name.ilike(f'%{client_name}%'))

            if is_active_bool is not None:
                query = query.filter(Client.is_active == is_active_bool)

            if sort_order == 'asc':
                query = query.order_by(Client.created_date.asc(), Client.created_time.asc())
            else:
                query = query.order_by(Client.created_date.desc(), Client.created_time.desc())

            clients = query.all()
            if not clients:
                return jsonify({'message': 'No client found in this company', 'status': 404}), 404
            
            client_list = []
            for client in clients:
                client_list.append({
                    'id': str(client.id),
                    'name': client.name ,
                    'email': client.email,
                    'phone': client.phone,
                    'is_active': client.is_active
                })

            return jsonify({
                'clients': client_list,
                'status': 200
            })
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

class ProjectController:

    def __init__(self):
        self.db_helper = DbHelper()
        self.auth = AuthorizationHelper()
        self.token = self.auth.get_jwt_token()

    def add_project(self):
        try:
            if not self.token:
                return jsonify({'message': 'Token not found', 'status': 401}), 401
            
            data = request.get_json()

            if not data or 'name' not in data or 'client_id' not in data:
                return jsonify({'message': 'Invalid input: Project name and Client Id required', 'status': 400}), 400

            name = data['name']
            client_id = data['client_id']

            client = Client.query.filter_by(id=client_id, is_archived = False).first()

            existing_project = Project.query.filter_by(name=name, client_id=client_id, is_archived = False).first()
            if existing_project:
                return jsonify({'message': 'Project already exists', 'status': 409}), 409

            project = Project(is_active=True)
            for key, value in data.items():
                if hasattr(Project, key): 
                    setattr(project, key, value)

            self.db_helper.add_record(project)
            self.db_helper.log_insert(project, self.token.get('user_id'))

            return jsonify({
                'message': 'Project added successfully', 
                'id':project.id, 
                'name':project.name, 
                'client_name':client.name, 
                'status': 201
            }), 201
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
    def add_duplicate_project(self):
        try:
            if not self.token:
                return jsonify({'message': 'Token not found', 'status': 401}), 401
            
            data = request.get_json()

            if 'id' in data:
                project= Project.query.filter_by(id=data['id']).first()
                if not project:
                    return jsonify({'message': 'Project not found', 'status': 404}), 404
                
                else:
                    for key, value in data.items():
                        if key != 'id' and value:
                            setattr(project, key, value)

                    self.db_helper.update_record()
                    return jsonify({'message': 'Project updated successfully', 'status': 200}), 200
            project = Project(is_active=True)
            for key, value in data.items():
                if hasattr(Project, key): 
                    setattr(project, key, value)

            self.db_helper.add_record(project)
            self.db_helper.log_insert(project, self.token.get('user_id'))

            return jsonify({'message': 'Project added successfully', 'id':project.id, 'name':project.name, 'status': 201}), 201
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def update_project(self):
        try:
            data = request.get_json()
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input: Project Id required', 'status': 400}), 400

            project_id = data['id']

            project = Project.query.filter_by(id=project_id, is_archived = False).first()
            if not project:
                return jsonify({'message': 'Project not found', 'status': 404}), 404
            
            if 'name' in data:
                new_name = data['name']

                existing_project = Project.query.filter_by(name=new_name, is_archived=False).first()
                if existing_project and existing_project.id != project_id:
                    return jsonify({'message': 'A project with the same name already exists.', 'status': 409}), 409
                
            if 'is_active' in data:
                project.is_active = data['is_active']
            
            for key, value in data.items():
                if key != 'id' and value:
                    setattr(project, key, value)
            #self.db_helper.update_record()(project, self.token.get('user_id')) 
            self.db_helper.update_record()
            return jsonify({'message': 'Project updated successfully', 'status': 200})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def delete_project(self):
        try:
            data = request.get_json()
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input: Project Id required', 'status': 400}), 400

            project_id = data['id']

            project = Project.query.filter_by(id=project_id, is_archived = False).first()
            if not project:
                return jsonify({'message': 'Project not found', 'status': 404}), 404
            
            project.is_archived = True
            project.is_active = False
            self.db_helper.update_record()
            self.db_helper.log_delete(project, self.token.get('user_id'))
            return jsonify({'message': 'Project deleted successfully', 'status': 200})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
      
    def project_list(self):
        try:
            company_id = self.token.get('company_id')
            if not company_id:
                return jsonify({'message': 'Invalid token: company_id missing', 'status': 400}), 400
            
            sort_order = request.args.get('order', 'desc').lower()  
            project_name = request.args.get('project', type=str) 
            is_active = request.args.get('is_active', type=str)   
            client_name = request.args.get('client', type=str)

            if sort_order not in ['asc', 'desc']:
                return jsonify({'message': 'Invalid sort_order value. Use "asc" or "desc".', 'status': 400}), 400

            if is_active is not None:
                if is_active.lower() not in ['true', 'false']:
                    return jsonify({'message': 'Invalid is_active value. Use "true" or "false".', 'status': 400}), 400
                is_active_bool = is_active.lower() == 'true'
            else:
                is_active_bool = None

            query = db.session.query(
                Project.id, 
                Project.name,
                Project.start_date, 
                Project.end_date, 
                Project.is_active, 
                Client.id.label('client_id'), 
                Client.name.label('client_name'), 
            ).join(Client, Project.client_id == Client.id).filter(
                Client.company_id == company_id,
                Project.is_archived == False
            )

            if project_name:
                query = query.filter(Project.name.ilike(f'%{project_name}%'))

            if client_name:
                query = query.filter(Client.name.ilike(f'%{client_name}%'))
            
            if is_active_bool is not None:
                query = query.filter(Project.is_active == is_active_bool)

            if sort_order == 'asc':
                query = query.order_by(Project.created_date.asc(), Project.created_time.asc())
            else:
                query = query.order_by(Project.created_date.desc(), Project.created_time.desc())

            projects = query.all()

            if not projects:
                return jsonify({'message': 'No projects found for this company', 'status': 404}), 404

            project_list = []
            for project in projects:
                project_list.append({
                    'id': str(project.id),
                    'name': project.name,
                    'start_date': project.start_date.strftime('%Y-%m-%d') if project.start_date else None,
                    'end_date': project.end_date.strftime('%Y-%m-%d') if project.end_date else None,
                    'is_active': project.is_active,
                    'client_id': str(project.client_id),
                    'client_name': project.client_name 
                })
            return jsonify({
                'projects': project_list,
                'status': 200
            })
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

class TaskController:

    def __init__(self):
        self.db_helper = DbHelper()
        self.auth = AuthorizationHelper()
        self.token = self.auth.get_jwt_token()

    def add_task(self):
        try:
            data = request.get_json()
            if not data or not 'name' in data or not 'project_id' in data:
                return jsonify({'message': 'Invalid input: Task name and Project Id required', 'status': 400}), 400

            name = data['name']
            project_id = data['project_id']

            project = Project.query.filter_by(id=project_id, is_archived = False).first()

            existing_task = Task.query.filter_by(name=name, project_id=project_id, is_archived = False).first()
            if existing_task:
                return jsonify({'message': 'Task already exists', 'status': 409}), 409
            
            task = Task(is_active=True)
            for key, value in data.items():
                if hasattr(Task, key): 
                    setattr(task, key, value)
            
            self.db_helper.add_record(task)
            self.db_helper.log_insert(task, self.token.get('user_id'))
            return jsonify({
                'message': 'Task added successfully',
                'id': str(task.id),
                'name': task.name,
                'project_name': project.name,
                'start_date': task.start_date,
                'end_date': task.end_date,
                'status': 201})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def add_duplicate_task(self):
        try:
            if not self.token:
                return jsonify({'message': 'Token not found', 'status': 401}), 401
            data = request.get_json()
            
            if 'id' in data:
                task= Task.query.filter_by(id=data['id']).first()
                if not task:
                    return jsonify({'message': 'Task not found', 'status': 404}), 404
                
                else:
                    for key, value in data.items():
                        if key != 'id' and value:
                            setattr(task, key, value)

                    self.db_helper.update_record()
                    return jsonify({'message': 'Task updated successfully', 'status': 200}), 200
            
            task = Task(is_active=True)
            for key, value in data.items():
                if hasattr(Task, key): 
                    setattr(task, key, value)

            self.db_helper.add_record(task)
            self.db_helper.log_insert(task, self.token.get('user_id'))
            return jsonify({'message': 'Task added successfully', 'status': 201}), 201
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
    def update_task(self):
        try:
            data = request.get_json()
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input: Task Id required', 'status': 400}), 400

            task_id = data['id']

            task = Task.query.filter_by(id=task_id, is_archived = False).first()
            if not task:
                return jsonify({'message': 'Task not found', 'status': 404}), 404
            
            if 'name' in data:
                new_name = data['name']

                existing_task = Task.query.filter_by(name=new_name, is_archived=False).first()
                if existing_task and existing_task.id != task_id:
                    return jsonify({'message': 'A task with the same name already exists.', 'status': 409}), 409
        
            if 'is_active' in data:
                task.is_active = data['is_active']
            
            for key, value in data.items():
                if key != 'id' and value:
                    setattr(task, key, value)
            self.db_helper.update_record()
            #self.db_helper.update_record()(task, self.token.get('user_id'))
            return jsonify({'message': 'Task updated successfully', 'status': 200})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def delete_task(self):
        try:
            data = request.get_json()
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input: Task Id required', 'status': 400}), 400

            task_id = data['id']

            task = Task.query.filter_by(id=task_id, is_archived = False).first()
            if not task:
                return jsonify({'message': 'Task not found', 'status': 404}), 404
            
            task.is_archived = True
            task.is_active = False
            self.db_helper.update_record()
            self.db_helper.log_delete(task, self.token.get('user_id'))
            return jsonify({'message': 'Task deleted successfully', 'status': 200})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def task_list(self):
        try:
            company_id = self.token.get('company_id')
            if not company_id:
                return jsonify({'message': 'Invalid token: company_id missing', 'status': 400}), 400
            
            sort_order = request.args.get('order', 'desc').lower()  
            task_name = request.args.get('task', type=str) 
            is_active = request.args.get('is_active', type=str)
            project_name = request.args.get('project', type=str)

            if sort_order not in ['asc', 'desc']:
                return jsonify({'message': 'Invalid sort_order value. Use "asc" or "desc".', 'status': 400}), 400

            if is_active is not None:
                if is_active.lower() not in ['true', 'false']:
                    return jsonify({'message': 'Invalid is_active value. Use "true" or "false".', 'status': 400}), 400
                is_active_bool = is_active.lower() == 'true'
            else:
                is_active_bool = None
            
            query = db.session.query(
                Task.id,
                Task.name,
                Task.start_date,
                Task.end_date,
                Task.is_active,
                Project.id.label('project_id'),
                Project.name.label('project_name'),
                Client.id.label('client_id'),
                Client.name.label('client_name'),
            ).join(Project, Task.project_id == Project.id).join(Client, Project.client_id == Client.id).filter(
                Client.company_id == company_id,
                Task.is_archived == False
            )

            if task_name:
                full_name = func.concat(Task.name)
                query = query.filter(full_name.ilike(f'%{task_name}%'))

            if project_name:
                full_name = func.concat(Project.name)
                query = query.filter(full_name.ilike(f'%{project_name}%'))
            
            if is_active_bool is not None:
                query = query.filter(Task.is_active == is_active_bool)

            if sort_order == 'asc':
                query = query.order_by(Task.created_date.asc(), Task.created_time.asc())
            else:
                query = query.order_by(Task.created_date.desc(), Task.created_time.desc())

            tasks = query.all()
            if not tasks:
                return jsonify({'message': 'No tasks found for this company', 'status': 404}), 404

            task_list = []
            for task in tasks:
                task_list.append({
                    'id': str(task.id),
                    'name': task.name,
                    'start_date': task.start_date.strftime('%Y-%m-%d') if task.start_date else None,
                    'end_date': task.end_date.strftime('%Y-%m-%d') if task.end_date else None,
                    'client_id': str(task.client_id),
                    'client_name': task.client_name,
                    'project_id': str(task.project_id),
                    'project_name': task.project_name,
                    'is_active': task.is_active
                })

            return jsonify({
                'tasks': task_list,
                'status': 200
            })
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500


class TimesheetController:

    def __init__(self):
        self.db_helper = DbHelper()
        self.auth = AuthorizationHelper()
        self.token = self.auth.get_jwt_token()

    def add_timesheet(self):
        try:
            data = request.get_json()
            if not data or not 'date' in data:
                return jsonify({'message': 'Invalid input: Date required', 'status': 400}), 400
            
            if not self.token:
                return jsonify({'message': 'Token not found', 'status': 401}), 401
            
            company_id = self.token.get('company_id')
            email = self.token.get('email')
            user_id = self.token.get('user_id')
            
            user = User.query.filter_by(id = user_id, email=email, company_id=company_id, is_archived = False).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404
            
            date = data['date']

            dimdate = DimDate.query.filter(DimDate.date_actual == date).first()
            name = f'Week {dimdate.week_of_year}, {dimdate.year_actual} Timesheet'

            existing_timesheet = Timesheet.query.filter_by(name=name, user_id=user.id, is_archived = False).first()
            if existing_timesheet:
                return jsonify({'message': 'Timesheet already exists', 'status': 409}), 409
            
            timesheet = Timesheet(name=name, start_date=dimdate.first_day_of_week, end_date=dimdate.last_day_of_week, user_id=user.id)
            self.db_helper.add_record(timesheet)
            self.db_helper.log_insert(timesheet, user_id)
            return jsonify({'message': 'Timesheet added successfully', 'status': 201})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
    def update_timesheet(self):
        try:
            if not self.token:
                return jsonify({'message': 'Token not found', 'status': 401}), 401
            
            company_id = self.token.get('company_id')
            email = self.token.get('email')
            user_id = self.token.get('user_id')
            
            user = User.query.filter_by(id = user_id, email=email, company_id=company_id, is_archived = False).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404
            
            data = request.get_json()
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input: Timesheet Id required', 'status': 400}), 400

            timesheet_id = data['id']

            timesheet = Timesheet.query.filter_by(id=timesheet_id, user_id=user.id, is_archived = False).first()
            if not timesheet:
                return jsonify({'message': 'Timesheet not found or does not belong to this User', 'status': 404}), 404
            
            if timesheet.approval in [Approval.DRAFT, Approval.REJECTED, Approval.RECALLED]:
                for key, value in data.items():
                    if value:
                        setattr(timesheet, key, value)
                self.db_helper.update_record()
                #self.db_helper.update_record()(timesheet, user_id)
                return jsonify({'message': 'Timesheet updated successfully', 'status': 200})
            else:
                return jsonify({'message': 'Cannot update a timesheet that is not in draft or rejected state', 'status': 400})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
    def delete_timesheet(self):
        try:
            if not self.token:
                return jsonify({'message': 'Token not found', 'status': 401}), 401
            
            email = self.token.get('email')
            company_id = self.token.get('company_id')
            user_id = self.token.get('user_id')
        
            user = User.query.filter_by(id=user_id, email=email, company_id=company_id, is_archived = False).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404
            
            data = request.get_json()
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input', 'status': 400}), 400

            timesheet_id = data['id']

            timesheet = Timesheet.query.filter_by(id=timesheet_id, user_id=user.id, is_archived = False).first()
            if not timesheet:
                return jsonify({'message': 'Timesheet not found or does not belong to this User', 'status': 404}), 404
            
            if timesheet.approval == Approval.DRAFT: 
                timesheet.is_archived = True
                timesheet.is_active = False
                self.db_helper.update_record()
                #self.db_helper.update_record()(timesheet, user_id)
                return jsonify({'message': 'Timesheet deleted successfully', 'status': 200})
            else:
                return jsonify({'message': 'Cannot delete a timesheet', 'status': 400})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
    def timesheet_list(self):
        try:
            user_id = self.token.get('user_id')
            email = self.token.get('email')
            company_id = self.token.get('company_id')
           
            user = User.query.filter_by(id=user_id, email=email, company_id=company_id, is_archived=False).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404
            
            sort_order = request.args.get('order', 'desc').lower()  

            if sort_order not in ['asc', 'desc']:
                return jsonify({'message': 'Invalid sort_order value. Use "asc" or "desc".', 'status': 400}), 400

            query = Timesheet.query.filter_by(user_id=user.id, is_archived = False)

            filter_value = request.args.get('filter')
            if filter_value:
                query = query.filter(Timesheet.name.ilike(f'%{filter_value}%'))

            if sort_order == 'asc':
                query = query.order_by(Timesheet.created_date.asc(), Timesheet.created_time.asc())
            else:
                query = query.order_by(Timesheet.created_date.desc(), Timesheet.created_time.desc())

            timesheets = query.all()
            if not timesheets:
                return jsonify({'message': 'No timesheets found for this user', 'status': 200}), 200
            
            timesheet_list = []
            for timesheet in timesheets:
                timesheet_list.append({
                    'id': str(timesheet.id),
                    'name': timesheet.name,
                    'start_date': timesheet.start_date.strftime('%Y-%m-%d'),
                    'end_date': timesheet.end_date.strftime('%Y-%m-%d'),
                    'is_active': timesheet.is_active,
                    'approval': timesheet.approval.value if timesheet.approval else None
                })
            return jsonify({
                'timesheets': timesheet_list,
               'status': 200
            })
        except Exception as e:          
            return jsonify({'message': str(e), 'status': 500}), 500

class TaskHourController:

    def __init__(self):
        self.db_helper = DbHelper()
        self.auth = AuthorizationHelper()
        self.token = self.auth.get_jwt_token()
        
    def add_taskhours(self):
        try:
            data = request.get_json()

            if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
                return jsonify({'message': 'Invalid input: a list of task hours objects is required', 'status': 400}), 400

            for entry in data:
                required_fields = ['values', 'task_id', 'timesheet_id']
                
                if any(field not in entry for field in required_fields):
                    return jsonify({'message': 'Invalid input: each object must contain values, task_id, and timesheet_id', 'status': 400}), 400

                values = entry['values']
                if len(values) != 7:
                    return jsonify({'message': 'Values array must have exactly 7 elements', 'status': 400}), 400

                task_id = entry['task_id']
                timesheet_id = entry['timesheet_id']

                timesheet = Timesheet.query.filter_by(id = timesheet_id, is_archived=False).first()
                if not timesheet:
                    return jsonify({'message': 'Timesheet not found or does not belong to this User', 'status': 404}), 404
                
                if timesheet.approval not in [Approval.DRAFT, Approval.REJECTED]:
                    return jsonify({'message': 'Cannot add taskhours for a timesheet that is not in draft or rejected state', 'status': 400}), 400

                existing_taskhour = TaskHours.query.filter_by(task_id=task_id, timesheet_id=timesheet_id).first()
                if existing_taskhour:
                    return jsonify({'message': f'TaskHours already exists for task_id {task_id}', 'status': 409}), 409

                taskhour = TaskHours(values=values, task_id=task_id, timesheet_id=timesheet_id)
                self.db_helper.add_record(taskhour)
                self.db_helper.log_insert(taskhour, self.token.get('user_id'))

            return jsonify({'message': 'TaskHours added successfully', 'status': 201})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500


    def update_taskhours(self):
        try:
            data = request.get_json()
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input: TaskHours Id required', 'status': 400}), 400
            
            taskhours_id = data['id']

            taskhours = TaskHours.query.filter_by(id=taskhours_id).first()
            if not taskhours:
                return jsonify({'message': 'TaskHours not found', 'status': 404}), 404
            
            timesheet = Timesheet.query.filter_by(id=taskhours.timesheet_id, is_archived=False).first()
            if not timesheet or timesheet.approval not in [Approval.DRAFT, Approval.REJECTED]:
                return jsonify({'message': 'Cannot update taskhours for a timesheet that is not in draft state', 'status': 400}), 400
            
            task_id = data.get('task_id')
            if task_id:
                existing_taskhour = TaskHours.query.filter_by(task_id=task_id, timesheet_id=taskhours.timesheet_id).first()
                if existing_taskhour and existing_taskhour.id != taskhours_id:
                    return jsonify({'message': f'TaskHours already exists for task_id {task_id}', 'status': 409}), 409
            
            for key, value in data.items():
                if hasattr(taskhours, key) and value is not None:
                    setattr(taskhours, key, value)

            self.db_helper.update_record()
            #self.db_helper.update_record()(taskhours, self.token.get('user_id'))
            return jsonify({'message': 'TaskHours updated successfully', 'status': 200})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def delete_taskhours(self):
        try:
            data = request.get_json()
            
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input: TaskHours Id required', 'status': 400}), 400
            
            taskhours_id = data['id']

            taskhours = TaskHours.query.filter_by(id=taskhours_id).first()
            if not taskhours:
                return jsonify({'message': 'TaskHours not found', 'status': 404}), 404
            
            timesheet = Timesheet.query.filter_by(id=taskhours.timesheet_id, is_archived=False).first()
            if not timesheet or timesheet.approval!= Approval.DRAFT:
                return jsonify({'message': 'Cannot delete taskhours for a timesheet that is not in draft state', 'status': 400}), 400
            
            taskhours.is_active = False
            self.db_helper.delete_record(taskhours)
            self.db_helper.log_delete(taskhours, self.token.get('user_id'))
            return jsonify({'message': 'TaskHours deleted successfully', 'status': 200})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def taskhours_list(self):
        try:
            user_id = self.token.get('user_id')
            data = request.get_json()
            if not data or not 'timesheet_id' in data:
                return jsonify({'message': 'timesheet_id is required', 'status': 400}), 400
            
            timesheet_id = data['timesheet_id']
            
            timesheet = Timesheet.query.filter_by(id=timesheet_id, user_id=user_id, is_archived=False).first()
            if not timesheet:
                return jsonify({'message': 'Timesheet not found', 'status': 404}), 404

            user = User.query.filter_by(id=timesheet.user_id, is_archived=False).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404
                    
            sort_order = request.args.get('order', 'desc').lower()

            if sort_order not in ['asc', 'desc']:
                return jsonify({'message': 'Invalid sort_order value. Use "asc" or "desc".', 'status': 400}), 400

            query = TaskHours.query.filter_by(timesheet_id=timesheet_id, is_active=True)

            if sort_order == 'asc':
                query = query.order_by(TaskHours.created_date.asc(), TaskHours.created_time.asc())
            else:
                query = query.order_by(TaskHours.created_date.desc(), TaskHours.created_time.desc())

            taskhours = query.all()
            
            taskhour_list = []
            for taskhour in taskhours:
                task = Task.query.filter_by(id=taskhour.task_id).first()
                project = Project.query.filter_by(id=task.project_id).first()
                client = Client.query.filter_by(id=project.client_id).first()

                if not task or not project or not client:
                    continue 

                taskhour_list.append({
                    'id': str(taskhour.id),                               
                    'mon' : taskhour.values[0],
                    'tue' : taskhour.values[1],
                    'wed' : taskhour.values[2],
                    'thu' : taskhour.values[3],
                    'fri' : taskhour.values[4],
                    'sat' : taskhour.values[5],
                    'sun' : taskhour.values[6],
                    'task_id': str(taskhour.task_id),
                    'task_name': task.name, 
                    'client_id': str(client.id),
                    'client_name': client.name,
                    'project_id': str(project.id),  
                    'project_name': project.name,
                    'is_active': taskhour.is_active
                })  
                  
            return jsonify({
            'timesheet_details': {
                'timesheet_id': str(timesheet.id),
                'timesheet_name': timesheet.name if timesheet else None,
                'start_date': timesheet.start_date.strftime('%Y-%m-%d'),
                'end_date': timesheet.end_date.strftime('%Y-%m-%d'),
                'is_active': timesheet.is_active,
                'approval': timesheet.approval.value if timesheet.approval else None,
                'user_id': str(user.id),
                'user_name': f'{user.firstname} {user.lastname}'
            },
            'taskhours': taskhour_list,
            'status': 200,
        }), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500
        
class ApproverController:

    def __init__(self):
        self.db_helper = DbHelper()
        self.auth = AuthorizationHelper()
        self.token = self.auth.get_jwt_token()

    def approve_timesheet(self):
        try:
            ses = SesHelper()
            data = request.get_json()
            required_fields = ['timesheet_id']
            
            if not data or any(field not in data for field in required_fields):
                return jsonify({'message': 'Invalid input: timesheet_id required', 'status': 400}), 400
            
            timesheet_id = data['timesheet_id']
            user_id = self.token.get('user_id')
            company_id = self.token.get('company_id')

            timesheet = Timesheet.query.filter_by(id=timesheet_id, is_archived=False).first()
            if not timesheet:
                return jsonify({'message': 'Timesheet not found', 'status': 404}), 404
            
            user = User.query.filter_by(id=timesheet.user_id, company_id=company_id, is_archived=False).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404
            
            approver = User.query.filter_by(id=user.approver_id, company_id=company_id, is_archived=False).first()
            if not approver:
                return jsonify({'message': 'No approver found for this user', 'status': 404}), 404

            if str(approver.id) != str(user_id):
                return jsonify({'message': 'You are not authorized to approve this timesheet', 'status': 403}), 403
                
            if timesheet.approval == Approval.APPROVED:
                return jsonify({'message': 'Timesheet is already approved', 'status': 409}), 409
            
            else:
                timesheet.approval = Approval.APPROVED
                self.db_helper.update_record()
                #self.db_helper.update_record()(timesheet, user_id)

                subject = 'Timesheet Approved'
                body_html = f'''
                    <h1>Timesheet Approved</h1>
                    <p>Dear {user.firstname},</p>
                    <p>Your timesheet "{timesheet.name}" has been approved.</p>
                    <p>Please review it at your convenience.</p>'''

                ses.send_email.delay(approver.email, user.email, subject, body_html)
                return jsonify({'message': 'Timesheet approved successfully', 'status': 201})
        except Exception as e:
            return jsonify({'message': str(e)}), 500


    def reject_timesheet(self):
        try:
            ses = SesHelper()
            data = request.get_json()
            required_fields = ['timesheet_id', 'feedback']
            
            if not data or any(field not in data for field in required_fields):
                return jsonify({'message': 'Invalid input: timesheet_id and feedback is required', 'status': 400}), 400
            
            timesheet_id = data['timesheet_id']
            feedback = data['feedback']
            user_id = self.token.get('user_id')
            company_id = self.token.get('company_id')

            timesheet = Timesheet.query.filter_by(id=timesheet_id, is_archived=False).first()
            if not timesheet:
                return jsonify({'message': 'Timesheet not found', 'status': 404}), 404
            
            user = User.query.filter_by(id=timesheet.user_id, company_id=company_id, is_archived=False).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404
            
            approver = User.query.filter_by(id=user.approver_id, company_id=company_id, is_archived=False).first()
            if not approver:
                return jsonify({'message': 'No approver found for this user', 'status': 404}), 404

            if str(approver.id) != str(user_id):
                return jsonify({'message': 'You are not authorized to reject this timesheet', 'status': 403}), 403
            
            if timesheet.approval == Approval.REJECTED:
                return jsonify({'message': 'Timesheet is already rejected', 'status': 409}), 409
            
            elif timesheet.approval == Approval.APPROVED:
                return jsonify({'message': 'Timesheet cannot be reject, it has been approved', 'status': 409}), 409
            
            else:
                timesheet.approval = Approval.REJECTED
                self.db_helper.update_record()
                #self.db_helper.update_record()(timesheet, user_id)

                subject = 'Timesheet Rejected'
                body_html = f'''
                    <h1>Timesheet Rejected</h1>
                    <p>Dear {user.firstname},</p>
                    <p>Your timesheet "{timesheet.name}" has been rejected, because of this "{feedback}"</p>
                    <p>Please review the reason for rejection and make necessary adjustments.</p>'''

                ses.send_email.delay(approver.email, user.email, subject, body_html)
                return jsonify({'message': 'Timesheet rejected successfully', 'status': 201})
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    def send_approval_request(self):
        try:
            ses = SesHelper()
            data = request.get_json()
            required_fields = ['timesheet_id']
            
            if not data or any(field not in data for field in required_fields):
                return jsonify({'message': 'Invalid input: timesheet_id required', 'status': 400}), 400

            timesheet_id = data['timesheet_id']
            user_id = self.token.get('user_id')
            company_id = self.token.get('company_id')

            user = User.query.filter_by(id=user_id, company_id=company_id, is_archived=False).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404

            approver = User.query.filter_by(id=user.approver_id, is_archived=False).first()
            if not approver:
                return jsonify({'message': 'No approver found for this user', 'status': 404}), 404

            timesheet = Timesheet.query.filter_by(id=timesheet_id, is_archived=False).first()
            if not timesheet:
                return jsonify({'message': 'Timesheet not found', 'status': 404}), 404
            
            if timesheet.approval == Approval.DRAFT or timesheet.approval == Approval.REJECTED:
                timesheet.approval = Approval.PENDING
                self.db_helper.update_record()
                #self.db_helper.update_record()(timesheet, user_id)

                subject = 'Timesheet Approval Request'
                body_html = f'''
                    <h1>Timesheet Approval Request</h1>
                    <p>Dear {approver.firstname},</p>
                    <p>A new timesheet has been requested by {user.firstname} {user.lastname}.</p>
                    <p>Please review and take the necessary action.</p>'''
            
                ses.send_email.delay(source=user.email, destination=approver.email, subject=subject, body_html=body_html)
                return jsonify({'message': 'Approval request sent successfully', 'status': 201})
            
            else:
                return jsonify({'message': 'Timesheet is not in draft state', 'status': 400}), 400
            
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
    def send_recall_request(self):
        try:
            ses = SesHelper()
            data = request.get_json()
            required_fields = ['timesheet_id']
            
            if not data or any(field not in data for field in required_fields):
                return jsonify({'message': 'Invalid input: timesheet_id required', 'status': 400}), 400

            timesheet_id = data['timesheet_id']
            user_id = self.token.get('user_id')
            company_id = self.token.get('company_id')

            user = User.query.filter_by(id=user_id, company_id=company_id, is_archived=False).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404
            
            approver = User.query.filter_by(id=user.approver_id, is_archived=False).first()
            if not approver:
                return jsonify({'message': 'No approver found for this user', 'status': 404}), 404
            
            subject = 'Timesheet Recall Request'
            body_html = f'''
                <h1>Timesheet Recall Request</h1>
                <p>Dear {approver.firstname},</p>
                <p>A recall timesheet request has been made by {user.firstname} {user.lastname} for the timesheet.</p>
                <p>Please review and approve or reject the recall request.</p>'''

            timesheet = Timesheet.query.filter_by(id=timesheet_id, is_archived=False).first()
            if not timesheet:
                return jsonify({'message': 'Timesheet not found', 'status': 404}), 404
            
            if timesheet.approval == Approval.APPROVED:
                timesheet.approval = Approval.RECALLED
                self.db_helper.update_record()
                #self.db_helper.update_record()(timesheet, user_id)

                ses.send_email.delay(source=user.email, destination=approver.email, subject=subject, body_html=body_html)
            else:
                return jsonify({'message': 'Timesheet cannot be accepted as it is not in recalled status', 'status': 400}), 400
            
            return jsonify({'message': 'Recall request accepted successfully', 'status': 201})
            
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
    def accept_recall_request(self):
        try:
            ses = SesHelper()
            data = request.get_json()
            required_fields = ['timesheet_id']
            
            if not data or any(field not in data for field in required_fields):
                return jsonify({'message': 'Invalid input: timesheet_id required', 'status': 400}), 400

            timesheet_id = data['timesheet_id']
            user_id = self.token.get('user_id')
            company_id = self.token.get('company_id')

            timesheet = Timesheet.query.filter_by(id=timesheet_id, is_archived=False).first()
            if not timesheet:
                return jsonify({'message': 'Timesheet not found', 'status': 404}), 404
            
            user = User.query.filter_by(id=timesheet.user_id, company_id=company_id, is_archived=False).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404
            
            approver = User.query.filter_by(id=user.approver_id, company_id=company_id, is_archived=False).first()
            if not approver:
                return jsonify({'message': 'No approver found for this user', 'status': 404}), 404

            if str(approver.id) != str(user_id):
                return jsonify({'message': 'You are not authorized to accept recall request this timesheet', 'status': 403}), 403
            
            if timesheet.approval == Approval.RECALLED:
                timesheet.approval = Approval.DRAFT
                self.db_helper.update_record()
                #self.db_helper.update_record()(timesheet, user_id)
            
                subject = 'Timesheet Recall Accepted'
                body_html = f'''
                    <h1>Timesheet Recall Accepted</h1>
                    <p>Dear {user.firstname},</p>
                    <p>Your recall timesheet for the "{timesheet.name}" has been accepted.</p>
                    <p>Please review and make necessary adjustments.</p>'''
                
                ses.send_email.delay(source=approver.email, destination=user.email, subject=subject, body_html=body_html)
            else:
                return jsonify({'message': 'Timesheet cannot be accepted as it is not in recalled status', 'status': 400}), 400
            
            return jsonify({'message': 'Recall request accepted successfully', 'status': 201})
        
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
    def approver_list(self):
        try:    
            user_id = self.token.get('user_id')
            company_id = self.token.get('company_id')
            users = User.query.filter_by(approver_id=user_id, company_id=company_id, is_archived=False).all()
            if not users:
                return jsonify({'message': 'User is not approver', 'status': 404}), 404
            
            timesheet_list = []
            for approver in users:
                timesheets = Timesheet.query.filter(Timesheet.user_id == approver.id, Timesheet.approval != Approval.DRAFT).all()

                if not timesheets:
                    return jsonify({'message': 'No timesheets found for approval', 'timesheets': [], 'status': 200}), 200
            
                for timesheet in timesheets:
                    employee = User.query.get(timesheet.user_id)
                    timesheet_data = {
                        'id': timesheet.id,
                        'name': timesheet.name,
                        'status': timesheet.approval.value, 
                        'start_date': timesheet.start_date.strftime('%Y-%m-%d'),
                        'end_date': timesheet.end_date.strftime('%Y-%m-%d'),
                        'employee_name': f"{employee.firstname} {employee.lastname}" if employee.firstname and employee.lastname else employee.firstname
                    }
                    timesheet_list.append(timesheet_data)

                    if not timesheet_list:
                        return jsonify({'message': 'No timesheets found for approval', 'timesheets': [], 'status': 200}), 200
            
                return jsonify({'message': 'Timesheets and approver retrieved successfully', 'timesheets': timesheet_list, 'status': 200})
            
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

class ProfileController:
    
    def __init__(self):
        self.db_helper = DbHelper()
        self.auth = AuthorizationHelper()
        self.token = self.auth.get_jwt_token()

    def update_profile(self):
        data = request.get_json()
        user_id = self.token.get('user_id')
        company_id = self.token.get('company_id')

        user = User.query.filter_by(id=user_id, company_id=company_id, is_archived=False).first()
        if not user:
            return jsonify({'message': 'User not found', 'status': 404}), 404
        
        fields_to_update = ['firstname', 'lastname', 'phone', 'date_of_birth', 'address', 'gender']
    
        for field in fields_to_update:
            if field in data:
                setattr(user, field, data[field])
        
        self.db_helper.update_record()
        return jsonify({'message': 'Profile updated successfully', 'status': 200})
        
    def get_profile(self):
        user_id = self.token.get('user_id')
        company_id = self.token.get('company_id')

        company = Company.query.get(company_id)
        if not company:
            return jsonify({'message': 'Company not found', 'status': 404}), 404

        user = User.query.filter_by(id=user_id, company_id=company_id, is_archived=False).first()
        if not user:
            return jsonify({'message': 'User not found', 'status': 404}), 404
        
        supervisor = User.query.filter(User.id == user.supervisor_id).first()
        approver = User.query.filter(User.id == user.approver_id).first()
        
        profile_data = {
            'id': user.id,
            'firstname': user.firstname,
            'lastname': user.lastname,
            'email': user.email,
            'phone': user.phone,
            'role': user.role,
            'company_name': company.name,
            'date_of_birth': user.date_of_birth.strftime('%Y-%m-%d') if user.date_of_birth else None,
            'address': user.address if user.address else None,
            'gender': user.gender,
            'supervisor_name': f'{supervisor.firstname} {supervisor.lastname}' if supervisor.lastname else supervisor.firstname,
            'approver_name': f'{approver.firstname} {approver.lastname}' if supervisor.lastname else supervisor.firstname
        }
        
        return jsonify({'message': 'Profile retrieved successfully', 'data': profile_data, 'status': 200}), 200
    
    def upload_profile_photo(self):
        s3 = S3Helper()
        user_id = self.token.get('user_id')
        company_id = self.token.get('company_id')

        user = User.query.filter_by(id=user_id, company_id=company_id, is_archived=False).first()
        if not user:
            return jsonify({'message': 'User not found', 'status': 404}), 404
        
        if 'file' not in request.files:
            return jsonify({'message': 'No file provided', 'status': 400}), 400
    
        file = request.files['file']
     
        try:
            s3_key = f'User_profile/{file}'
            
            file_url = s3.put_object_in_s3(s3_key, 'timechronos', file)
            if not file_url:
                return jsonify({'message': 'Failed to upload profile photo', 'status': 500}), 500

            user.profile_photo_url = file_url
            self.db_helper.update_record()

            return jsonify({'message': 'Profile photo uploaded successfully', 'url': file_url, 'status': 200}), 200
        except Exception as e:
            return jsonify({'message': f'An error occurred: {str(e)}', 'status': 500}), 500

