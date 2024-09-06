from utils.helper import DbHelper, PasswordHelper, AuthenticationHelper, AuthorizationHelper, CodeHelper, SesHelper, get_jwt_identity, jwt_required
from utils.models import db,User, Client, Project, Task, TaskHours, Company, Timesheet, DimDate, Approval
from flask import jsonify, request, url_for

class Controller:

    def __init__(self):
        self.db_helper = DbHelper()
        self.password_helper = PasswordHelper()
        self.authentication_helper = AuthenticationHelper()

    def register(self):
        try:
            data = request.get_json()
            required_fields = ['company_name', 'firstname', 'email', 'password', 'gender', 'phone']
            if not data or not all(data.get(key) for key in required_fields):
                return jsonify({'message': 'Invalid input: All fields are required', 'status': 400}), 400

            company_name = data['company_name']
            firstname = data['firstname']
            lastname = data.get('lastname')
            role = data.get('role', 'Admin')
            email = data['email']
            phone = data['phone'],
            gender = data['gender']
            password = data['password']

            hashed_password = self.password_helper.hash_password(password)
            
            existing_company = Company.query.filter_by(name=company_name).first()
            if existing_company:
                existing_user = User.query.filter_by(email=email, company_id=existing_company.id).first()
                if existing_user:
                    return jsonify({'message': 'User with this email already exists in the company', 'status': 409}), 409 
            
            if 'phone' in data:
                phone = data['phone']
                if len(phone) != 10 or not phone.isdigit():
                    return jsonify({'message': 'Invalid input: Phone number must be exactly 10 digits', 'status': 400}), 400

            if existing_company:
                company = existing_company
            else:
                company = Company(name=company_name)
                self.db_helper.add_record(company)

            user = User(firstname=firstname, lastname=lastname, role=role, email=email, phone=phone, gender=gender, password=hashed_password, company_id=company.id)
            self.db_helper.add_record(user)

            if user.role == 'Admin':
                user.supervisor_id = user.id
                user.approver_id = user.id
                self.db_helper.update_record()
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

            user = User.query.filter_by(email=email).first()
            if not user:
                return jsonify({'message': 'Incorrect email or password', 'status': 401}), 401

            if not self.password_helper.check_password(password, user.password):
                return jsonify({'message': 'Incorrect email or password', 'status': 401}), 401

            access_token = self.authentication_helper.create_access_token(user.email, {'role': user.role, 'company_id': str(user.company_id), 'user_id': str(user.id)})
            refresh_token = self.authentication_helper.create_refresh_token(user.email, {'role': user.role, 'company_id': str(user.company_id), 'user_id': str(user.id)})
            return jsonify({'access_token': access_token,
                            'refresh_token': refresh_token,
                            'status': 200})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
    @jwt_required(refresh=True)
    def refresh_token(self):
        current_user = get_jwt_identity()
        user = User.query.filter_by(email=current_user).first()
        claims = {
            'user_id': str(user.id),
            'company_id': str(user.company_id),
            'role': user.role
        }

        new_access_token = self.authentication_helper.create_access_token(current_user, claims)
        return jsonify(access_token=new_access_token), 200
        
    def forget_password(self):
        try:
            code = CodeHelper()
            ses = SesHelper()
            data = request.get_json()
            if not data or 'email' not in data:
                return jsonify({'message': 'Invalid input: email required', 'status': 400}), 400

            email = data['email']
            user = User.query.filter_by(email=email).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404

            token = code.generate_reset_token(email)
            reset_url = url_for('routes.reset_password', token=token, _external=True)

            subject = "Password Reset Request"
            body_html = f"To reset your password, click the following link: <a href={reset_url}>{reset_url}</a>"
            ses.send_email(source='contact@digitalshelfiq.com', destination=email, subject=subject, body_html=body_html)

            return jsonify({'message': 'Password reset link sent to your email', 'status': 200}), 200
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
    def reset_password_with_token(self, token):
        try:
            code = CodeHelper()
            email = code.confirm_reset_token(token)
            if not email:
                return jsonify({'message': 'Invalid or expired token', 'status': 401}), 401

            data = request.get_json()
            if not data or 'password' not in data:
                return jsonify({'message': 'Password is required', 'status': 400}), 400
            
            new_password = data['password']

            user = User.query.filter_by(email=email).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404

            # Reset the user's password
            hashed_password = self.password_helper.hash_password(new_password)
            user.password = hashed_password
            self.db_helper.update_record()

            return jsonify({'message': 'Password reset successfully', 'status': 200}), 200
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def change_password(self):
        try:
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

            user = User.query.filter_by(email=email, company_id=company_id).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404
            
            if not self.password_helper.check_password(current_password, user.password):
                return jsonify({'message': 'Current password is incorrect', 'status': 401}), 401
            
            hashed_password = self.password_helper.hash_password(new_password)
            user.password = hashed_password
            self.db_helper.update_record()

            return jsonify({'message': 'Password changed successfully', 'status': 200})
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
            company = Company.query.filter_by(id=company_id).first()
            if not company:
                return jsonify({'message': 'Company not found', 'status': 404}), 404

            if 'name' in data:
                company.name = data['name']

            self.db_helper.update_record()
            return jsonify({'message': 'Company updated successfully', 'status': 200})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def delete_company(self):
        try:
            if not self.token:
                return jsonify({'message': 'Authentication token is missing', 'status': 401}), 401

            company_id = self.token.get('company_id')

            company = Company.query.filter_by(id=company_id).first()
            if not company:
                return jsonify({'message': 'Company not found', 'status': 404}), 404

            company.is_archived = True
            company.is_active = False
            self.db_helper.update_record()
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
                if len(phone) != 10 or not phone.isdigit():
                    return jsonify({'message': 'Invalid input: Phone number must be exactly 10 digits', 'status': 400}), 400

            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return jsonify({'message': 'Email already exists', 'status': 409}), 409 
            
            user = User(firstname=firstname, lastname=lastname, role=role, email=email, phone=phone, gender=gender, password=hashed_password, company_id=company_id, supervisor_id=supervisor_id, approver_id=approver_id)
            self.db_helper.add_record(user) 
            return jsonify({'message': 'User added successfully', 'status': 201})
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

            user = User.query.filter_by(id=user_id, company_id=company_id).first()
            if not user:
                return jsonify({'message': 'User not found or does not belong to this company', 'status': 404}), 404

            if 'email' in data and data['email'] != user.email:
                return jsonify({'message': 'Email cannot be updated', 'status': 409}), 409
            
            if 'phone' in data:
                phone = data['phone']
                if len(phone) != 10 or not phone.isdigit():
                    return jsonify({'message': 'Invalid input: Phone number must be exactly 10 digits', 'status': 400}), 400
            
            for key, value in data.items():
                if key not in ['id', 'email']: 
                    setattr(user, key, value)

            self.db_helper.update_record()

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

            user = User.query.filter_by(id=user_id, company_id=company_id).first()
            if not user:
                return jsonify({'message': 'User not found or does not belong to this company', 'status': 404}), 404
            
            user.is_archived = True
            user.is_active = False
            self.db_helper.update_record()
            return jsonify({'message': 'User deleted successfully', 'status': 200})
        except Exception as e:
            return jsonify({'message': str(e)}), 500
        
    def user_list(self):
        try:
            if not self.token:
                return jsonify({'message': 'Token not found', 'status': 401}), 401
            
            company_id = self.token.get('company_id')

            supervisor_alias = db.aliased(User)
            approver_alias = db.aliased(User)

            users = db.session.query(
                User.id,
                User.firstname,
                User.lastname,
                User.email,
                User.role,
                User.supervisor_id,
                User.approver_id,
                User.is_active,
                User.gender,
                supervisor_alias.firstname.label('supervisor_firstname'),
                supervisor_alias.lastname.label('supervisor_lastname'),
                approver_alias.firstname.label('approver_firstname'),
                approver_alias.lastname.label('approver_lastname')
            ).outerjoin(supervisor_alias, User.supervisor_id == supervisor_alias.id) \
            .outerjoin(approver_alias, User.approver_id == approver_alias.id) \
            .filter(
                User.company_id == company_id,
                User.is_archived == False
            ).all()

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
            required_fields = ['firstname', 'email']
            if not data or not all(data.get(key) for key in required_fields):
                return jsonify({'message': 'Invalid input: All fields are required', 'status': 400}), 400
            
            if not self.token:
                return jsonify({'message': 'Token not found', 'status': 401}), 401
            
            company_id = self.token.get('company_id')
            firstname = data['firstname']
            lastname = data.get('lastname')
            email = data['email']
            phone = data.get('phone')

            if phone and (len(phone) != 10 or not phone.isdigit()):
                return jsonify({'message': 'Invalid input: Phone number must be exactly 10 digits', 'status': 400}), 400

            existing_client = Client.query.filter_by(email=email, company_id=company_id).first()
            if existing_client:
                return jsonify({'message': 'Client already exists', 'status': 409}), 409 
            
            client = Client(firstname=firstname, lastname=lastname, email=email, phone=phone, company_id=company_id)
            self.db_helper.add_record(client)
            return jsonify({'message': 'Client added successfully', 'status': 201})
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

            client = Client.query.filter_by(id=client_id, company_id=company_id).first()
            if not client:
                return jsonify({'message': 'Client not found or does not belong to this company', 'status': 404}), 404

            if 'email' in data and client.email == data['email']:
                return jsonify({'message': 'No changes made. Email is the same', 'status': 409}), 409
            
            if 'email' in data:
                existing_client = Client.query.filter_by(email=data['email'], company_id=company_id).first()
                if existing_client and existing_client.id != client_id:
                    return jsonify({'message': 'Email is already in use by another client', 'status': 409}), 409
            
            if 'phone' in data and (len(data['phone'])!= 10 or not data['phone'].isdigit()):
                return jsonify({'message': 'Invalid input: Phone number must be exactly 10 digits', 'status': 400}), 400
        
            for key, value in data.items():
                if key != 'id':
                    setattr(client, key, value)
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

            client = Client.query.filter_by(id=client_id, company_id=company_id).first()
            if not client:
                return jsonify({'message': 'Client not found or does not belong to this company', 'status': 404}), 404
            
            client.is_archived = True
            client.is_active = False
            self.db_helper.update_record()
            return jsonify({'message': 'Client deleted successfully', 'status': 201})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def client_list(self):
        try:
            company_id = self.token.get('company_id')

            clients = Client.query.filter_by(company_id=company_id, is_archived=False).all()

            if not clients:
                return jsonify({'message': 'No data found', 'status': 404}), 404

            client_list = []
            for client in clients:
                client_list.append({
                    'id': str(client.id),
                    'name': f'{client.firstname} {client.lastname}' if client.firstname and client.lastname else client.firstname,
                    'firstname': client.firstname,
                    'lastname': client.lastname,
                    'email': client.email,
                    'phone': client.phone,
                    'is_active': client.is_active
                })

            return {
                'clients': client_list,
                'status': 200
            }

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

            existing_project = Project.query.filter_by(name=name, client_id=client_id).first()
            if existing_project:
                return jsonify({'message': 'Project already exists', 'status': 409}), 409

            project = Project(is_active=True)
            for key, value in data.items():
                if hasattr(Project, key): 
                    setattr(project, key, value)

            self.db_helper.add_record(project)

            return jsonify({'message': 'Project added successfully', 'status': 201}), 201
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def update_project(self):
        try:
            data = request.get_json()
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input: Project Id required', 'status': 400}), 400

            project_id = data['id']

            project = Project.query.filter_by(id=project_id).first()
            if not project:
                return jsonify({'message': 'Project not found', 'status': 404}), 404
            
            for key, value in data.items():
                    setattr(project, key, value)
            self.db_helper.update_record()
            return jsonify({'message': 'Project updated successfully', 'status': 201})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def delete_project(self):
        try:
            data = request.get_json()
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input: Project Id required', 'status': 400}), 400

            project_id = data['id']

            project = Project.query.filter_by(id=project_id).first()
            if not project:
                return jsonify({'message': 'Project not found', 'status': 404}), 404
            
            project.is_archived = True
            project.is_active = False
            self.db_helper.update_record()
            return jsonify({'message': 'Project deleted successfully', 'status': 201})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
    def project_list(self):
        try:
            company_id = self.token.get('company_id')
            if not company_id:
                return jsonify({'message': 'Invalid token: company_id missing', 'status': 400}), 400
            
            projects = db.session.query(
                Project.id, 
                Project.name,
                Project.start_date, 
                Project.end_date, 
                Project.is_active, 
                Client.id.label('client_id'), 
                Client.firstname, 
                Client.lastname
                ).join(Client, Project.client_id == Client.id).filter(
                    Client.company_id == company_id, Project.is_archived == False).all()
            
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
                    'client_name': f'{project.firstname} {project.lastname}'
                })

            return {
                'projects': project_list,
                'status': 200
            }

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

            existing_task = Task.query.filter_by(name=name, project_id=project_id).first()
            if existing_task:
                return jsonify({'message': 'Task already exists', 'status': 409}), 409
            
            task = Task(is_active=True)
            for key, value in data.items():
                if hasattr(Task, key): 
                    setattr(task, key, value)
            
            self.db_helper.add_record(task)
            return jsonify({'message': 'Task added successfully', 'status': 201})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def update_task(self):
        try:
            data = request.get_json()
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input: Task Id required', 'status': 400}), 400

            task_id = data['id']

            task = Task.query.filter_by(id=task_id).first()
            if not task:
                return jsonify({'message': 'Task not found', 'status': 404}), 404
            
            for key, value in data.items():
                    setattr(task, key, value)
            self.db_helper.update_record()
            return jsonify({'message': 'Task updated successfully', 'status': 201})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def delete_task(self):
        try:
            data = request.get_json()
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input: Task Id required', 'status': 400}), 400

            task_id = data['id']

            task = Task.query.filter_by(id=task_id).first()
            if not task:
                return jsonify({'message': 'Task not found', 'status': 404}), 404
            
            task.is_archived = True
            task.is_active = False
            self.db_helper.update_record()
            return jsonify({'message': 'Task deleted successfully', 'status': 201})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def task_list(self):
        try:
            company_id = self.token.get('company_id')
            
            tasks = db.session.query(
                Task.id,
                Task.name,
                Task.start_date,
                Task.end_date,
                Task.is_active,
                Project.id.label('project_id'),
                Project.name.label('project_name'),
                Client.id.label('client_id'),
                Client.firstname,
                Client.lastname
            ).join(Project, Task.project_id == Project.id).join(Client, Project.client_id == Client.id).filter(
                Client.company_id == company_id,
                Task.is_archived == False
            ).all()
            
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
                    'client_name': f'{task.firstname} {task.lastname}',
                    'project_id': str(task.project_id),
                    'project_name': task.project_name,
                    'is_active': task.is_active
                })

            return {
                'tasks': task_list,
                'status': 200
            }
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
            
            email = self.token.get('email')
            company_id = self.token.get('company_id')
            
            user = User.query.filter_by(email=email, company_id=company_id).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404
            
            date = data['date']

            dimdate = DimDate.query.filter(DimDate.date_actual == date).first()
            name = f'Week {dimdate.week_of_year}, {dimdate.year_actual} Timesheet'

            existing_timesheet = Timesheet.query.filter_by(name=name, user_id=user.id).first()
            if existing_timesheet:
                return jsonify({'message': 'Timesheet already exists', 'status': 409}), 409
            
            timesheet = Timesheet(name=name, start_date=dimdate.first_day_of_week, end_date=dimdate.last_day_of_week, user_id=user.id)
            self.db_helper.add_record(timesheet)
            return jsonify({'message': 'Timesheet added successfully', 'status': 201})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
    def update_timesheet(self):
        try:
            if not self.token:
                return jsonify({'message': 'Token not found', 'status': 401}), 401
            
            email = self.token.get('email')
            company_id = self.token.get('company_id')
    
            user = User.query.filter_by(email=email, company_id=company_id).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404
            
            data = request.get_json()
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input: Timesheet Id required', 'status': 400}), 400

            timesheet_id = data['id']

            timesheet = Timesheet.query.filter_by(id=timesheet_id, user_id=user.id).first()
            if not timesheet:
                return jsonify({'message': 'Timesheet not found or does not belong to this User', 'status': 404}), 404
            
            if timesheet.approval in [Approval.DRAFT, Approval.REJECTED, Approval.RECALLED]:
                for key, value in data.items():
                    setattr(timesheet, key, value)
                self.db_helper.update_record()
                return jsonify({'message': 'Timesheet updated successfully', 'status': 201})
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
        
            user = User.query.filter_by(email=email, company_id=company_id).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404
            
            data = request.get_json()
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input', 'status': 400}), 400

            timesheet_id = data['id']

            timesheet = Timesheet.query.filter_by(id=timesheet_id, user_id=user.id).first()
            if not timesheet:
                return jsonify({'message': 'Timesheet not found or does not belong to this User', 'status': 404}), 404
            
            if timesheet.approval == Approval.DRAFT: 
                timesheet.is_archived = True
                timesheet.is_active = False
                self.db_helper.update_record()
                return jsonify({'message': 'Timesheet deleted successfully', 'status': 200})
            else:
                return jsonify({'message': 'Cannot delete a timesheet', 'status': 400})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
    def timesheet_list(self):
        try:
            email = self.token.get('email')
            company_id = self.token.get('company_id')
           
            user = User.query.filter_by(email=email, company_id=company_id).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404
            
            timesheets = Timesheet.query.filter_by(user_id=user.id, is_archived = False).all()
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
            return {
                'timesheets': timesheet_list,
               'status': 200
            }
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
            required_fields = ['values', 'task_id', 'timesheet_id']
            
            if not data or any(field not in data for field in required_fields):
                return jsonify({'message': 'Invalid input: values, task_id, and timesheet_id are required', 'status': 400}), 400

            values = data['values']
            if len(values) != 7:
                return jsonify({'message': 'Values array must have exactly 7 elements', 'status': 400}), 400

            task_id = data['task_id']
            timesheet_id = data['timesheet_id']

            existing_meta = TaskHours.query.filter_by(task_id=task_id, timesheet_id=timesheet_id).first()
            if existing_meta:
                return jsonify({'message': 'TaskHours already exists', 'status': 409}), 409
            
            meta = TaskHours(values=values, task_id=task_id, timesheet_id=timesheet_id)    
            self.db_helper.add_record(meta)
            return jsonify({'message': 'TaskHours added successfully', 'status': 201})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
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

                existing_taskhour = TaskHours.query.filter_by(task_id=task_id, timesheet_id=timesheet_id).first()
                if existing_taskhour:
                    return jsonify({'message': f'TaskHours already exists for task_id {task_id}', 'status': 409}), 409

                taskhour = TaskHours(values=values, task_id=task_id, timesheet_id=timesheet_id)
                self.db_helper.add_record(taskhour)

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
            
            for key, value in data.items():
                    setattr(taskhours, key, value)

            self.db_helper.update_record()
            return jsonify({'message': 'TaskHours updated successfully', 'status': 201})
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
            
            taskhours.is_active = False
            self.db_helper.delete_record() 
            return jsonify({'message': 'TaskHours deleted successfully', 'status': 201})
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500

    def taskhours_list(self):
        try:
            user_id = self.token.get('user_id')
            data = request.get_json()
            if not data or not 'timesheet_id' in data:
                return jsonify({'message': 'timesheet_id is required', 'status': 400}), 400
            
            timesheet_id = data['timesheet_id']
            
            timesheet = Timesheet.query.filter(Timesheet.id == timesheet_id, user_id==user_id).first()
            if not timesheet:
                return jsonify({'message': 'Timesheet not found', 'status': 404}), 404

            taskhours = TaskHours.query.filter_by(timesheet_id=timesheet_id, is_active=True).all()
            taskhour_list = []
            
            for taskhour in taskhours:
                timesheet = Timesheet.query.filter(Timesheet.id == taskhour.timesheet_id).first()
                task = Task.query.filter(Task.id == taskhour.task_id).first()
                project = Project.query.filter(Project.id == task.project_id).first()
                client = Client.query.filter(Client.id == project.client_id).first()
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
                    'client_name': f'{client.firstname} {client.lastname}',
                    'project_id': str(project.id),  
                    'project_name': project.name,
                    'is_active': taskhour.is_active,
                    'timesheet_id': str(taskhour.timesheet_id),
                    'timesheet_name': timesheet.name if timesheet else None,
                })               
            return {
                'taskhours': taskhour_list,
                'status': 200
            }
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

            user = User.query.filter_by(id=user_id).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404

            approver = User.query.filter_by(id=user.approver_id).first()
            if not approver:
                return jsonify({'message': 'No approver found for this user', 'status': 404}), 404
            
            timesheet = Timesheet.query.filter_by(id=timesheet_id, user_id=user_id).first()
            if not timesheet:
                return jsonify({'message': 'Timesheet not found', 'status': 404}), 404
            
            if timesheet.approval == Approval.APPROVED:
                return jsonify({'message': 'Timesheet is already approved', 'status': 409}), 409
            
            else:
                timesheet.approval = Approval.APPROVED
                self.db_helper.update_record()

                subject = 'Timesheet Approved'
                body_html = f'''
                    <h1>Timesheet Approved</h1>
                    <p>Dear {user.firstname},</p>
                    <p>Your timesheet "{timesheet.name}" has been approved.</p>
                    <p>Please review it at your convenience.</p>'''

                ses.send_email(approver.email, user.email, subject, body_html)
                return jsonify({'message': 'Timesheet approved successfully', 'status': 201})
        except Exception as e:
            return jsonify({'message': str(e)}), 500


    def reject_timesheet(self):
        try:
            ses = SesHelper()
            data = request.get_json()
            required_fields = ['timesheet_id']
            
            if not data or any(field not in data for field in required_fields):
                return jsonify({'message': 'Invalid input: timesheet_id required', 'status': 400}), 400
            
            timesheet_id = data['timesheet_id']
            user_id = self.token.get('user_id')

            user = User.query.filter_by(id=user_id).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404

            approver = User.query.filter_by(id=user.approver_id).first()
            if not approver:
                return jsonify({'message': 'No approver found for this user', 'status': 404}), 404
            
            timesheet = Timesheet.query.filter_by(id=timesheet_id, user_id=user_id).first()
            if not timesheet:
                return jsonify({'message': 'Timesheet not found', 'status': 404}), 404
            
            if timesheet.approval == Approval.REJECTED:
                return jsonify({'message': 'Timesheet is already rejected', 'status': 409}), 409
            
            elif timesheet.approval == Approval.APPROVED:
                return jsonify({'message': 'Timesheet cannot be rejected if it has been approved', 'status': 409}), 409
            
            else:
                timesheet.approval = Approval.REJECTED
                self.db_helper.update_record()

                subject = 'Timesheet Rejected'
                body_html = f'''
                    <h1>Timesheet Rejected</h1>
                    <p>Dear {user.firstname},</p>
                    <p>Your timesheet "{timesheet.name}" has been rejected.</p>
                    <p>Please review the reason for rejection and make necessary adjustments.</p>'''

                ses.send_email(approver.email, user.email, subject, body_html)
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

            user = User.query.filter_by(id=user_id).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404

            approver = User.query.filter_by(id=user.approver_id).first()
            if not approver:
                return jsonify({'message': 'No approver found for this user', 'status': 404}), 404

            timesheet = Timesheet.query.filter_by(id=timesheet_id, user_id=user_id).first()
            if not timesheet:
                return jsonify({'message': 'Timesheet not found', 'status': 404}), 404
            
            if timesheet.approval == Approval.DRAFT:
                timesheet.approval = Approval.PENDING
                self.db_helper.update_record()

                subject = 'Timesheet Approval Request'
                body_html = f'''
                    <h1>Timesheet Approval Request</h1>
                    <p>Dear {approver.firstname},</p>
                    <p>A new timesheet has been requested by {user.firstname} {user.lastname}.</p>
                    <p>Please review and take the necessary action.</p>'''
            
                ses.send_email(source='contact@digitalshelfiq.com', destination=approver.email, subject=subject, body_html=body_html)
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

            user = User.query.filter_by(id=user_id).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404
            
            approver = User.query.filter_by(id=user.approver_id).first()
            if not approver:
                return jsonify({'message': 'No approver found for this user', 'status': 404}), 404
            
            subject = 'Timesheet Recall Request'
            body_html = f'''
                <h1>Timesheet Recall Request</h1>
                <p>Dear {approver.firstname},</p>
                <p>A recall timesheet request has been made by {user.firstname} {user.lastname} for the timesheet.</p>
                <p>Please review and approve or reject the recall request.</p>'''

            timesheet = Timesheet.query.filter_by(id=timesheet_id, user_id=user_id).first()
            if not timesheet:
                return jsonify({'message': 'Timesheet not found', 'status': 404}), 404
            
            if timesheet.approval == Approval.APPROVED:
                timesheet.approval = Approval.RECALLED
                self.db_helper.update_record()

                ses.send_email(source='contact@digitalshelfiq.com', destination=approver.email, subject=subject, body_html=body_html)
                return jsonify({'message': 'Recall request sent successfully', 'status': 201})
            else:
                return jsonify({'message': 'Timesheet cannot be recall', 'status': 400}), 400
            
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
    def approver_list(self):
        try:
            user_id = self.token.get('user_id')
            user = User.query.filter_by(approver_id=user_id).first()
            if not user:
                return jsonify({'message': 'User not found', 'status': 404}), 404
            
            timesheets = Timesheet.query.filter_by(user_id=user.id).all()

            if not timesheets:
                return jsonify({'message': 'No timesheets found for this user', 'timesheets': [], 'status': 200}), 200
            
            timesheet_list = []
            for timesheet in timesheets:
                timesheet_data = {
                    'id': timesheet.id,
                    'name': timesheet.name,
                    'status': timesheet.approval.value, 
                    'start_date': timesheet.start_date.strftime('%Y-%m-%d'),
                    'end_date': timesheet.end_date.strftime('%Y-%m-%d'),
                    'employee_name': f"{user.firstname} {user.lastname}" if user.firstname and user.lastname else user.firstname
                }
                timesheet_list.append(timesheet_data)
            
                return jsonify({'message': 'Timesheets and approver retrieved successfully', 'timesheets': timesheet_list, 'status': 200})
            
        except Exception as e:
            return jsonify({'message': str(e), 'status': 500}), 500
        
    
            
            
            

