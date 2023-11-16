from flask import Blueprint, session, redirect, render_template, request, current_app, jsonify, url_for
from utils.admin_site_helper import handle_login
from google_auth_oauthlib.flow import Flow
import requests
from pip._vendor import cachecontrol
import google.auth.transport.requests
from google.oauth2 import id_token
import pdb


admin = Blueprint("admin", __name__)


# ----------------------- Initialize global variables -----------------------
TEMPORARY_STORAGE = {}

TEMPORARY_STORAGE['flow_login_with_google'] = {}
TEMPORARY_STORAGE['redirect_url_login_with_google'] = {}
# ----------------------- END OF Initialize global variables. -----------------------



@admin.before_request
def before_request():
    pass


@admin.route('/')
def index():
    if session.get('login_admin'):
        return "You are logged in as admin."
    else:
        return redirect('/admin/login')

#---------------------------------------------------------------------------------------------
@admin.route('/account')
def account():
    if session.get('login_admin'):
        page_parameters = {'page_name': 'Admin Information - Spring Success blog', 'user_name': session['username_admin'], \
                           'login_status': True, 'login_url': "/admin/login", \
                            'logout_url': "/admin/log-out", 'redirect_after_logout': "/"}
        return render_template('admin/user_account.html', **page_parameters)
    
    return redirect(url_for('admin.login', redirect_url = request.url))

#---------------------------------------------------------------------------------------------
@admin.route('/log-out')
def logout():
    session.pop('username_admin', None)
    session.pop('login_admin', None)
    return redirect('/')

#---------------------------------------------------------------------------------------------
@admin.route('/login', methods = ['GET', 'POST'])
def login():
    redirect_url = request.args.get('redirect_url', '/admin')

    # login_mode = request.args.get('mode', '')
    # if login_mode != 'default':
    #     return redirect(url_for('admin.login_with_google') + '?redirectUrl=' + redirect_url)
    
    if request.method == 'GET':
        page_parameters = {'redirect_url': redirect_url, 'sign_up_url': '/admin', 'handle_route': request.url,
                           'page_name': 'Spring Success blog'}
        return render_template('admin/login_page.html', **page_parameters)
    
    data = request.get_json()

    admin_username, admin_password = current_app.config['admin_account']['username'], current_app.config['admin_account']['password']
    status, response = handle_login(data, admin_username, admin_password)

    if status:
        session['username_admin'] = data.get('username')
        session['login_admin'] = True
        session['login_type_admin'] = 'default'

    return response

# ---------------------- Login With Google functions ----------------------
@admin.route('/login-with-google')
def login_with_google():
    redirectUrl = request.args.get('redirectUrl', '/')

    client_secrets_file = current_app.config["login_with_google"]["client_secrets_file"]
    scopes = current_app.config["login_with_google"]["scopes"]
    redirect_uri = request.base_url + '/callback'
    # Remember to also include this redirect_url in: current_app.config["login_with_google"]["web"]["redirect_uris"][1]

    flow = Flow.from_client_secrets_file(client_secrets_file=client_secrets_file,
                                         scopes=scopes,
                                         redirect_uri = redirect_uri)
    
    authorization_url, state = flow.authorization_url()

    session['state_login_with_google_admin'] = state

    TEMPORARY_STORAGE['flow_login_with_google'][session['state_login_with_google_admin']] = flow
    TEMPORARY_STORAGE['redirect_url_login_with_google'][session['state_login_with_google_admin']] = redirectUrl

    return redirect(authorization_url)

@admin.route('/login-with-google/callback')
def callback_login_with_google():
    if not session.get('state_login_with_google_admin'):
        return redirect('/admin/login-with-google')
    
    flow = TEMPORARY_STORAGE['flow_login_with_google'][session['state_login_with_google_admin']]
    redirectUrl = TEMPORARY_STORAGE['redirect_url_login_with_google'][session['state_login_with_google_admin']]
    state_login_with_google = session.get('state_login_with_google_admin')

    # Delete temporary storage:
    TEMPORARY_STORAGE['flow_login_with_google'].pop(session['state_login_with_google_admin'])
    TEMPORARY_STORAGE['redirect_url_login_with_google'].pop(session['state_login_with_google_admin'])
    session.pop('state_login_with_google_admin')
    

    if state_login_with_google != request.args['state']:
        return redirect('/admin/login-with-google')
    
    GOOGLE_CLIENT_ID = current_app.config["login_with_google"]["web"]["client_id"]

    flow.fetch_token(authorization_response = request.url)

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    google_id = id_info.get('sub')
    google_name = id_info.get('name')
    google_email = id_info.get('email')

    if google_email in current_app.config['admin_emails']:
        session['username_admin'] = google_name
        session['login_admin'] = True
        session['login_type_admin'] = 'google'

        return redirect(redirectUrl)
    
    page_parameters = {'page_name': 'Admin Information - Spring Success blog', 'name': google_name,
                       'email': google_email,
                       'login_status': session.get('login_admin'), 'login_url': "/admin/login?redirect_url=" + redirectUrl,
                       'logout_url': "/admin/log-out", 'redirect_after_logout': "/"}
    
    return render_template("admin/user_account.html", **page_parameters)

# ---------------------- END OF Login With Google functions. ----------------------