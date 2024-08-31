from flask import Blueprint, jsonify, request
from utils.models import db
from utils.controller import UserContoller, ClientContoller, ProjectContoller, TaskContoller, TaskHourContoller, CompanyContoller


api = Blueprint('routes', __name__)

@api.route('/')
def server():
    return jsonify({'message': 'Server is up and running'})

@api.route('/createdb')
def create_db():
    db.create_all()
    return jsonify({'message': 'Database created'})

@api.route('/dropdb')
def drop_db():
    db.drop_all()
    return jsonify({'message': 'Database dropped'})

@api.route('/register', methods=['POST'])
def register():
    try:    
        company = CompanyContoller()
        return company.register()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/login', methods=['POST'])
def login():
    try:    
        company = CompanyContoller()
        return company.login()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/updateuser', methods=['POST'])
def update_user():
    try:
        user = UserContoller()
        return user.update_user()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/deleteuser', methods=['POST'])
def delete_user():
    try:
        user = UserContoller()
        return user.delete_user()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/addclient', methods=['POST'])
def add_client():
    try:
        client = ClientContoller()
        return client.add_client()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/updateclient', methods=['POST'])
def update_client():
    try:
        client = ClientContoller()
        return client.update_client()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/deleteclient', methods=['POST'])
def delete_client():
    try:
        client = ClientContoller()
        return client.delete_client()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/clientlist')
def client_list():
    try:
        client = ClientContoller()
        return client.client_list()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/addproject', methods=['POST'])
def add_project():
    try:
        project = ProjectContoller()
        return project.add_project()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/updateproject', methods=['POST'])
def update_project():
    try:
        project = ProjectContoller()
        return project.update_project()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/deleteproject', methods=['POST'])
def delete_project():
    try:
        project = ProjectContoller()
        return project.delete_project()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/projectlist')
def project_list():
    try:
        project = ProjectContoller()
        return project.project_list()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/addtask', methods=['POST'])
def add_task():
    try:
        task = TaskContoller()
        return task.add_task()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/updatetask', methods=['POST'])
def update_task():
    try:
        task = TaskContoller()
        return task.update_task()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/deletetask', methods=['POST'])
def delete_task():
    try:
        task = TaskContoller()
        return task.delete_task()
    except Exception as e:
        return jsonify({'message': str(e)}), 500     

@api.route('/addtaskhours', methods=['POST'])
def add_meta():
    try:
        meta = TaskHourContoller()
        return meta.add_taskhours()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/updatetaskhours', methods=['POST']) 
def update_meta():
    try:
        meta = TaskHourContoller()
        return meta.update_taskhours()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/deletetaskhours', methods=['POST'])   
def delete_meta():
    try:
        meta = TaskHourContoller()
        return meta.delete_taskhours()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/taskhourslist', methods=['GET'])
def meta_list():
    try:
        meta = TaskHourContoller()
        return meta.taskhours_list()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/metadata', methods=['GET'])
def metadata():
    try:
        client = ClientContoller()
        project = ProjectContoller()
        task = TaskContoller()
        taskhour = TaskHourContoller()

        return client.client_list(), project.project_list()
                # 'tasks': task.task_list(),
                # 'task hours': taskhour.taskhours_list()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

    



