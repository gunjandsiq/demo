from flask import Blueprint, jsonify, request
from utils.models import db
from utils.controller import UserController, ClientController, ProjectController, TaskController, TaskHourController, Controller, TimesheetController, CompanyController, ApproverController

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
        con = Controller()
        return con.register()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/login', methods=['POST'])
def login():
    try:    
        con = Controller()
        return con.login()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
   
@api.route('/refreshtoken', methods=['POST'])
def refresh_token():
    try:    
        con = Controller()
        return con.refresh_token()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/forgotpassword', methods=['POST'])
def forget_password():
    try:    
        con = Controller()
        return con.forget_password()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/resetpassword', methods=['POST'])
def reset_password():
    try:
        token = request.args.get('token')
        if not token:
            return jsonify({'message': 'Token is required', 'status': 400}), 400

        con = Controller()
        return con.reset_password_with_token(token)
    except Exception as e:
        return jsonify({'message': str(e), 'status': 500}), 500
    
@api.route('/changepassword', methods=['POST'])
def change_password():
    try:    
        con = Controller()
        return con.change_password()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/updatecompany', methods=['POST'])
def update_company():
    try:
        company = CompanyController()
        return company.update_company()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/deletecompany', methods=['POST'])
def delete_company():
    try:
        company = CompanyController()
        return company.delete_company()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/adduser', methods=['POST'])
def add_user():
    try:
        user = UserController()
        return user.add_user()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/updateuser', methods=['POST'])
def update_user():
    try:
        user = UserController()
        return user.update_user()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/deleteuser', methods=['POST'])
def delete_user():
    try:
        user = UserController()
        return user.delete_user()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/userlist', methods=['GET'])
def user_list():
    try:
        user = UserController()
        return user.user_list()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/addclient', methods=['POST'])
def add_client():
    try:
        client = ClientController()
        return client.add_client()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/updateclient', methods=['POST'])
def update_client():
    try:
        client = ClientController()
        return client.update_client()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/deleteclient', methods=['POST'])
def delete_client():
    try:
        client = ClientController()
        return client.delete_client()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/clientlist', methods=['GET'])
def client_list():
    try:
        client = ClientController()
        return client.client_list()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/addproject', methods=['POST'])
def add_project():
    try:
        project = ProjectController()
        return project.add_project()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/updateproject', methods=['POST'])
def update_project():
    try:
        project = ProjectController()
        return project.update_project()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/deleteproject', methods=['POST'])
def delete_project():
    try:
        project = ProjectController()
        return project.delete_project()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/projectlist', methods=['GET'])
def project_list():
    try:
        project = ProjectController()
        return project.project_list()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/addtask', methods=['POST'])
def add_task():
    try:
        task = TaskController()
        return task.add_task()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/updatetask', methods=['POST'])
def update_task():
    try:
        task = TaskController()
        return task.update_task()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/deletetask', methods=['POST'])
def delete_task():
    try:
        task = TaskController()
        return task.delete_task()
    except Exception as e:
        return jsonify({'message': str(e)}), 500   

@api.route('/tasklist', methods=['GET'])
def task_list():
    try:
        task = TaskController()
        return task.task_list()
    except Exception as e:
        return jsonify({'message': str(e)}), 500  
    
@api.route('/addtimesheet', methods=['POST'])
def add_timesheet():
    try:
        timesheet = TimesheetController()
        return timesheet.add_timesheet()
    except Exception as e:
        return jsonify({'message': str(e)}), 500 

@api.route('/updatetimesheet', methods=['POST'])
def update_timesheet():
    try:
        timesheet = TimesheetController()
        return timesheet.update_timesheet()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/deletetimesheet' , methods=['POST'])
def delete_timesheet():
    try:
        timesheet = TimesheetController()
        return timesheet.delete_timesheet()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/timesheetlist', methods=['GET'])
def timesheet_list():
    try:
        timesheet = TimesheetController()
        return timesheet.timesheet_list()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/addtaskhours', methods=['POST'])
def add_taskhours():
    try:
        taskhour = TaskHourController()
        return taskhour.add_taskhours()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/updatetaskhours', methods=['POST']) 
def update_taskhours():
    try:
        taskhour = TaskHourController()
        return taskhour.update_taskhours()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/deletetaskhours', methods=['POST'])   
def delete_taskhours():
    try:
        taskhour = TaskHourController()
        return taskhour.delete_taskhours()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/taskhourslist', methods=['POST'])
def taskhours_list():
    try:
        taskhour = TaskHourController()
        return taskhour.taskhours_list()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/approvalrequest', methods=['POST'])
def send_approval():
    try:
        app = ApproverController()
        return app.send_approval_request()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/recallrequest', methods=['POST'])
def send_recall():
    try:
        recall = ApproverController()
        return recall.send_recall_request()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/approvetimesheet', methods=['POST'])
def approve_timesheet():
    try:
        approver = ApproverController()
        return approver.approve_timesheet()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/rejecttimesheet', methods=['POST'])
def reject_timesheet():
    try:
        approver = ApproverController()
        return approver.reject_timesheet()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/approverlist', methods=['GET'])
def approver_list():
    try:
        approver = ApproverController()
        return approver.approver_list()
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api.route('/metadata', methods=['GET'])
def metadata():
    try:
        client = ClientController()
        project = ProjectController()
        task = TaskController()
        timesheet = TimesheetController()

        return jsonify(client.client_list(), project.project_list(), task.task_list(), timesheet.timesheet_list())
    except Exception as e:
        return jsonify({'message': str(e)}), 500

    



