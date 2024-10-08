from flask import Blueprint, jsonify, request
from utils.models import db, BlacklistToken
from utils.helper import jwt, load_dim_date
from utils.controller import UserController, ClientController, ProjectController, TaskController, TaskHourController, Controller, TimesheetController, CompanyController, ApproverController, ProfileController, Statastics

api = Blueprint('routes', __name__)

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        "message": "The token has expired.",
        "status": 401
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        "message": "Invalid token.",
        "status": 422
    }), 422

@jwt.unauthorized_loader
def unauthorized_token_callback(error):
    return jsonify({
        "message": "Missing token.",
        "status": 403
    }), 403

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify({
        "message": "Token has been revoked.",
        "status": 403
    }), 403

@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    return BlacklistToken.query.filter_by(jti=jti).first() is not None

@api.route('/')
def server():
    return jsonify({'message': 'Server is up and running'})

@api.route('/createdb')
def create_db():
    db.create_all()
    load_dim_date()
    return jsonify({'message': 'Database created and DimDate data loaded successfully'})

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
    
@api.route('/logout', methods=['POST'])
def logout():
    try:    
        con = Controller()
        return con.logout()
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

@api.route('/addduplicateproject', methods=['POST'])   
def duplicate_project():
    try:
        project = ProjectController()
        return project.add_duplicate_project()
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

@api.route('/addduplicatetask', methods=['POST'])
def duplicate_task():
    try:
        task = TaskController()
        return task.add_duplicate_task()
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
    
@api.route('/savetaskhours', methods=['POST'])
def save_taskhours():
    try:
        taskhour = TaskHourController()
        return taskhour.add_taskhours()
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
    
@api.route('/acceptrecallrequest', methods=['POST'])
def accept_recall():
    try:
        recall = ApproverController()
        return recall.accept_recall_request()
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
    
@api.route('/updateprofile', methods=['POST'])
def update_profile():
    try:
        profile = ProfileController()
        return profile.update_profile()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/getprofile', methods=['GET'])
def get_profile():
    try:
        profile = ProfileController()
        return profile.get_profile()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/uploadprofile', methods=['POST'])
def upload_profile():
    try:
        profile = ProfileController()
        return profile.upload_profile_photo()
    except Exception as e:
        return jsonify({'message': str(e)}), 

@api.route('/getstats')
def get_stats():
    try:
        stats = Statastics()
        return stats.get_stats()
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@api.route('/metadata', methods=['GET'])
def metadata():
    try:
        client_controller = ClientController()
        project_controller = ProjectController()
        task_controller = TaskController()
        timesheet_controller = TimesheetController()

        data = {
            'clients': [],
            'projects': [],
            'tasks': [],
            'timesheets': []
        }

        try:
            client_result = client_controller.client_list()
            if isinstance(client_result, list):
                data['clients'] = client_result
            elif hasattr(client_result, 'json') and isinstance(client_result.json, dict):
                data['clients'] = client_result.json.get('clients', [])
        except Exception as e:
            data['clients'] = {'error': str(e)}

        try:
            project_result = project_controller.project_list()
            if isinstance(project_result, list):
                data['projects'] = project_result
            elif hasattr(project_result, 'json') and isinstance(project_result.json, dict):
                data['projects'] = project_result.json.get('projects', [])
        except Exception as e:
            data['projects'] = {'error': str(e)}

        try:
            task_result = task_controller.task_list()
            if isinstance(task_result, list):
                data['tasks'] = task_result
            elif hasattr(task_result, 'json') and isinstance(task_result.json, dict):
                data['tasks'] = task_result.json.get('tasks', [])
        except Exception as e:
            data['tasks'] = {'error': str(e)}

        try:
            timesheet_result = timesheet_controller.timesheet_list()
            if isinstance(timesheet_result, list):
                data['timesheets'] = timesheet_result
            elif hasattr(timesheet_result, 'json') and isinstance(timesheet_result.json, dict):
                data['timesheets'] = timesheet_result.json.get('timesheets', [])
        except Exception as e:
            data['timesheets'] = {'error': str(e)}

        return jsonify({'message': data, 'status': 200}), 200

    except Exception as e:
        return jsonify({'message': str(e)}), 500




    



