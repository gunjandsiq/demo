from utils.helper import DbHelper, passwordHelper
from utils.models import db,User, Client, Project, Task, TaskHours, Company
from flask import jsonify, request

class CompanyContoller:
    def register(self):
        try:
            db_helper = DbHelper()
            hash = passwordHelper()
            data = request.get_json()
            required_fields = ['company_name', 'firstname', 'lastname', 'email', 'password']
            if not data or not all(data.get(key) for key in required_fields):
                return jsonify({'message': 'Invalid input: All fields are required'}), 400

            company_name = data['company_name']
            firstname = data['firstname']
            lastname = data['lastname']
            email = data['email']
            password = data['password']

            hashed_password = hash.hash_password(password)
            existing_company = Company.query.filter_by(name=company_name).first()
            if existing_company:
                return jsonify({'message': 'Company already exists'}), 409 
            
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return jsonify({'message': 'Email already exists'}), 409 
            
            company = Company(name=company_name)
            db_helper.add_record(company) 

            user = User(firstname=firstname, lastname=lastname, email=email, password=hashed_password, company_id=company.id)
            db_helper.add_record(user)
            return jsonify({'message': 'Company and user added successfully'})
        except Exception as e:
            return jsonify({'message': str(e)}), 500
        
    def login(self):
        try:
            db_helper = DbHelper()
            data = request.get_json()
            if not data or not 'email' in data or not 'password' in data:
                return jsonify({'message': 'Invalid input'}), 400

            email = data['email']
            password = data['password']

            user = User.query.filter_by(email=email).first()
            if not user:
                return jsonify({'message': 'User not found'}), 404

            if not passwordHelper().check_password(password, user.password):
                return jsonify({'message': 'Invalid password'}), 401

            token = db_helper.generate_token(user)
            return jsonify({'token': token})
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    def update_company(self):
        pass

    def delete_company(self):
        pass

class UserContoller:
    # def add_user(self):
    #     try:
    #         db_helper = DbHelper()
    #         data = request.get_json()
    #         if not data or not 'email' in data or not 'firstname' in data or not 'lastname' in data or not 'company_id' in data:
    #             return jsonify({'message': 'Invalid input'}), 400

    #         email = data['email']
    #         firstname = data['firstname']
    #         lastname = data['lastname']
    #         company_id = data['company_id']

    #         existing_user = User.query.filter_by(email=email).first()
    #         if existing_user:
    #             return jsonify({'message': 'Email already exists'}), 409 
            
    #         user = User(firstname=firstname, lastname=lastname, email=email, company_id=company_id)
    #         db_helper.add_record(user) 
    #         return jsonify({'message': 'User added successfully'})
    #     except Exception as e:
    #         return jsonify({'message': str(e)}), 500

    def update_user(self):
        try:
            db_helper = DbHelper()
            data = request.get_json()
            if not data or not 'id' in data or not 'email' in data or not 'firstname' in data or not 'lastname' in data or not 'company_id' in data:
                return jsonify({'message': 'Invalid input'}), 400

            id = data['id']
            email = data['email']
            firstname = data['firstname']
            lastname = data['lastname']
            company_id = data['company_id']

            user = User.query.filter_by(id=id).first()
            if not user:
                return jsonify({'message': 'User not found'}), 404
            
            user.firstname = firstname
            user.lastname = lastname
            user.email = email
            user.company_id = company_id
            db_helper.update_record(user)
            return jsonify({'message': 'User updated successfully'})
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    def delete_user(self):
        try:
            db_helper = DbHelper()
            data = request.get_json()
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input'}), 400

            id = data['id']

            user = User.query.filter_by(id=id).first()
            if not user:
                return jsonify({'message': 'User not found'}), 404
            
            db_helper.delete_record(user)
            return jsonify({'message': 'User deleted successfully'})
        except Exception as e:
            return jsonify({'message': str(e)}), 500

class ClientContoller:
    def add_client(self):
        try:
            db_helper = DbHelper()
            data = request.get_json()
            if not data or not 'name' in data or not 'company_id' in data:
                return jsonify({'message': 'Invalid input'}), 400

            name = data['name']
            company_id = data['company_id']

            existing_client = Client.query.filter_by(name=name, company_id=company_id).first()
            if existing_client:
                return jsonify({'message': 'Email already exists'}), 409 
            
            client = Client(name=name, company_id=company_id)
            db_helper.add_record(client)
            return jsonify({'message': 'Client added successfully'})
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    def update_client(self):
        try:
            db_helper = DbHelper()
            data = request.get_json()
            if not data or not 'id' in data or not 'name' in data:
                return jsonify({'message': 'Invalid input'}), 400

            id = data['id']
            name = data['name']
            company_id = data['company_id']

            client = Client.query.filter_by(id=id).first()
            if not client:
                return jsonify({'message': 'Client not found'}), 404
            
            client.name = name
            client.company_id = company_id
            db_helper.update_record()
            return jsonify({'message': 'Client updated successfully'})
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    def delete_client(self):
        try:
            db_helper = DbHelper()
            data = request.get_json()
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input'}), 400

            id = data['id']

            client = Client.query.filter_by(id=id).first()
            if not client:
                return jsonify({'message': 'Client not found'}), 404
            
            db_helper.delete_record(client)
            return jsonify({'message': 'Client deleted successfully'})
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    def client_list(self):
        try:
            clients = Client.query.all()
            client_list = []

            for client in clients:
                client_list.append({
                    'id': str(client.id),
                    'name': client.name
                })
            return client_list
        except Exception as e:
            return jsonify({'message': str(e)}), 500

class ProjectContoller:
    def add_project(self):
        try:
            db_helper = DbHelper()
            data = request.get_json()
            if not data or not 'name' in data or not 'client_id' in data:
                return jsonify({'message': 'Invalid input'}), 400

            name = data['name']
            client_id = data['client_id']

            existing_project = Project.query.filter_by(name=name, client_id=client_id).first()
            if existing_project:
                return jsonify({'message': 'Project already exists'}), 409

            project = Project(name=name, client_id=client_id)
            db_helper.add_record(project)
            return jsonify({'message': 'Project added successfully'})
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    def update_project(self):
        try:
            db_helper = DbHelper()
            data = request.get_json()
            if not data or not 'id' in data or not 'name' in data or not 'client_id' in data:
                return jsonify({'message': 'Invalid input'}), 400

            id = data['id']
            name = data['name']
            client_id = data['client_id']

            project = Project.query.filter_by(id=id).first()
            if not project:
                return jsonify({'message': 'Project not found'}), 404
            
            project.name = name
            project.client_id = client_id
            db_helper.update_record()
            return jsonify({'message': 'Project updated successfully'})
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    def delete_project(self):
        try:
            db_helper = DbHelper()
            data = request.get_json()
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input'}), 400

            id = data['id']

            project = Project.query.filter_by(id=id).first()
            if not project:
                return jsonify({'message': 'Project not found'}), 404
            
            db_helper.delete_record(project)
            return jsonify({'message': 'Project deleted successfully'})
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    def project_list(self):
        try:
            projects = Project.query.all()
            project_list = []

            for project in projects:
                client = Client.query.get(project.client_id)
                project_list.append({
                    'id': str(project.id),
                    'name': project.name,
                    'client_id': str(project.client_id),
                    'client_name': client.name if client else None
                })
            return project_list
        except Exception as e:
            return jsonify({'message': str(e)}), 500

class TaskContoller:
    def add_task(self):
        try:
            db_helper = DbHelper()
            data = request.get_json()
            if not data or not 'name' in data or not 'project_id' in data or not 'start_date' in data or not 'end_date' in data:
                return jsonify({'message': 'Invalid input'}), 400

            name = data['name']
            project_id = data['project_id']
            start_date = data['start_date']
            end_date = data['end_date']

            existing_task = Task.query.filter_by(name=name, project_id=project_id).first()
            if existing_task:
                return jsonify({'message': 'Task already exists'}), 409
            
            task = Task(name=name, project_id=project_id, start_date=start_date, end_date=end_date)
            db_helper.add_record(task)
            return jsonify({'message': 'Task added successfully'})
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    def update_task(self):
        try:
            db_helper = DbHelper()
            data = request.get_json()
            if not data or not 'id' in data or not 'name' in data or not 'project_id' in data or not 'start_date' in data or not 'end_date' in data:
                return jsonify({'message': 'Invalid input'}), 400

            id = data['id']
            name = data['name']
            project_id = data['project_id']
            start_date = data['start_date']
            end_date = data['end_date']

            task = Task.query.filter_by(id=id).first()
            if not task:
                return jsonify({'message': 'Task not found'}), 404
            
            task.name = name
            task.project_id = project_id
            task.start_date = start_date
            task.end_date = end_date
            db_helper.update_record()
            return jsonify({'message': 'Task updated successfully'})
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    def delete_task(self):
        try:
            db_helper = DbHelper()
            data = request.get_json()
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input'}), 400

            id = data['id']

            task = Task.query.filter_by(id=id).first()
            if not task:
                return jsonify({'message': 'Task not found'}), 404
            
            db_helper.delete_record(task)
            return jsonify({'message': 'Task deleted successfully'})
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    def task_list(self):
        try:
            tasks = Task.query.all()
            task_list = []

            for task in tasks:
                project = Project.query.get(task.project_id)
                client = Client.query.get(project.client_id)
                task_list.append({
                    'id': str(task.id),
                    'name': task.name,
                    'client_id': str(client.id) if client else None,
                    'project_id': str(project.id) if project else None,
                })

            return task_list
        except Exception as e:
            return jsonify({'message': str(e)}), 500


class TaskHourContoller:
    def add_taskhours(self):
        try:
            db_helper = DbHelper()
            data = request.get_json()
            required_fields = ['values', 'start_date', 'task_id', 'user_id']
            
            if not data or any(field not in data for field in required_fields):
                return jsonify({'message': 'Invalid input: values, start_date, task_id, and user_id are required'}), 400

            values = data['values']
            if len(values) != 7:
                return jsonify({'message': 'Values array must have exactly 7 elements'}), 400

            start_date = data['start_date']
            task_id = data['task_id']
            user_id = data['user_id']

            existing_meta = TaskHours.query.filter_by(task_id=task_id, user_id=user_id).first()
            if existing_meta:
                return jsonify({'message': 'TaskHours already exists'}), 409
            
            meta = TaskHours(values=values, start_date=start_date, task_id=task_id, user_id=user_id)    
            db_helper.add_record(meta)
            return jsonify({'message': 'TaskHours added successfully'})
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    def update_taskhours(self):
        try:
            db_helper = DbHelper()
            data = request.get_json()
            required_fields = ['id', 'values', 'start_date', 'task_id', 'user_id']
            
            if not data or any(field not in data for field in required_fields):
                return jsonify({'message': 'Invalid input: id, values, start_date, task_id, and user_id are required'}), 400
            
            values = data['values']
            if len(values) != 7:
                return jsonify({'message': 'Values array must have exactly 7 elements'}), 400
            
            meta_id = data['id']
            start_date = data['start_date']
            task_id = data['task_id']
            user_id = data['user_id']

            meta = TaskHours.query.get(meta_id)
            if not meta:
                return jsonify({'message': 'TaskHours not found'}), 404
            
            meta.values = values
            meta.start_date = start_date
            meta.task_id = task_id
            meta.user_id = user_id

            db_helper.update_record()
            return jsonify({'message': 'TaskHours updated successfully'})
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    def delete_taskhours(self):
        try:
            db_helper = DbHelper()
            data = request.get_json()
            
            if not data or not 'id' in data:
                return jsonify({'message': 'Invalid input'}), 400
            
            meta_id = data['id']

            meta = TaskHours.query.get(meta_id)
            if not meta:
                return jsonify({'message': 'TaskHours not found'}), 404

            db_helper.delete_record(meta)
            return jsonify({'message': 'TaskHours deleted successfully'})
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    def taskhours_list(self):
        try:
            metas = TaskHours.query.all()
            meta_list = []
            
            for meta in metas:
                task = Task.query.filter(Task.id == meta.task_id).first()
                project = Project.query.filter(Project.id == task.project_id).first()
                client = Client.query.filter(Client.id == project.client_id).first()
                meta_list.append({
                    'id': str(meta.id),
                    'mon' : meta.values[0],
                    'tue' : meta.values[1],
                    'wed' : meta.values[2],
                    'thu' : meta.values[3],
                    'fri' : meta.values[4],
                    'sat' : meta.values[5],
                    'sun' : meta.values[6],
                    'start_date': meta.start_date.strftime('%Y-%m-%d'),
                    'task_name': task.name, 
                    'project_name': project.name,
                    'client_name': client.name,
                    'user_id': str(meta.user_id)  
                })               
            return meta_list
        except Exception as e:
            return jsonify({'message': str(e)}), 500
        

