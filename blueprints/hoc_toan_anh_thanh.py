from flask import Blueprint, session, render_template, redirect, request, current_app, url_for, jsonify
from utils.hoc_toan_anh_thanh_helper import handle_login, handle_sign_up, tra_cuu_tien_trinh_hoc_tap as tra_cuu_tien_trinh_hoc_tap_helper
from utils.common_utils import read_google_docs
import requests
from pip._vendor import cachecontrol
import google.auth.transport.requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import pdb
from utils import hoc_toan_anh_thanh_helper


app = Blueprint("hoc_toan_anh_thanh", __name__)


# Initialize global variables: --------------------------------------------------------
TEMPORARY_STORAGE = {}

TEMPORARY_STORAGE['flow_login_with_google'] = {}
TEMPORARY_STORAGE['redirect_url_login_with_google'] = {}
# END OF Initialize global variables. -------------------------------------------------


@app.before_request
def before_request():
    # session['hoc_toan_anh_thanh'] = {}
    pass


@app.route('/')
def index():
    if session.get("login_HTAT"):
        username = session["username_HTAT"]
        login_status = session["login_HTAT"]
        return render_template('me/Mentor/index.html', user=username, login_status=login_status)
    
    username = None
    login_status = False
    return render_template('me/Mentor/index.html', user=username, login_status=login_status)

@app.route('/user-account')
def user_account():
    if session.get("login_HTAT"):
        username = session["username_HTAT"]
        return render_template('hoc_toan_anh_thanh/user_account.html', user=username, login_status=session["login_HTAT"])
    return redirect('/login')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    github_access_token = current_app.config["github"]["access_token"]

    redirectUrl = request.args.get('redirectUrl', '/hoc-toan-anh-thanh')
    sign_in_template = 'hoc_toan_anh_thanh/sign_in_sign_up/index.html'
    page_parameters = {'openFunction': 'SignIn', 'redirectUrl': redirectUrl}

    if request.method == 'GET':
        return render_template(sign_in_template, **page_parameters)
    
    username = request.form['username_login']
    password = request.form['password_login']

    page_parameters = handle_login(page_parameters=page_parameters, username=username, password=password,
                                                             github_access_token=github_access_token)
    
    if page_parameters['status_login']:
        session["username_HTAT"] = username
        session["login_HTAT"] = True
        session['login_type_HTAT'] = 'default'


    return render_template(sign_in_template, **page_parameters)


@app.route('/log-out')
def log_out():
    if not session.get("login_HTAT"):
        return redirect('/hoc-toan-anh-thanh')
    
    # Delete the 'user' variable from the session['hoc_toan_anh_thanh']
    session.pop('username_HTAT', None)
    # Delete the 'login_status' variable from the session['hoc_toan_anh_thanh']
    session["login_HTAT"] = False
    # Redirect to the homepage or any other desired page after logout
    return redirect('/hoc-toan-anh-thanh')

@app.route('/sign-up', methods = ['GET', 'POST'])
def sign_up():
    github_access_token = current_app.config["github"]["access_token"]

    redirectUrl = request.args.get('redirectUrl', '/hoc-toan-anh-thanh')
    sign_up_template = 'hoc_toan_anh_thanh/sign_in_sign_up/index.html'
    page_parameters = {'openFunction': 'SignUp', 'redirectUrl': redirectUrl}

    if request.method == 'GET':
        return render_template(sign_up_template, **page_parameters)
    
    name = request.form['name_signup']
    username = request.form['username_signup']
    password = request.form['password_signup']
    file_id = request.form['file_id']

    page_parameters = handle_sign_up(github_access_token, page_parameters, name, username, password, file_id)

    return render_template(sign_up_template, **page_parameters)

@app.route('/bang-thong-bao')
def bang_thong_bao():
    docs_link = "https://docs.google.com/document/d/1Ps5FOD89x2QODf0snY4Jrj0lVm_4aTisRp3hqRwJgcc/edit"
    document_content = read_google_docs(docs_link=docs_link)
    return render_template('hoc_toan_anh_thanh/bang_thong_bao.html', content = document_content)

@app.route('/tra-cuu-tien-trinh-hoc-tap', methods = ['GET', 'POST'])
def tra_cuu_tien_trinh_hoc_tap():
    github_access_token = current_app.config["github"]["access_token"]
    
    if session.get("login_HTAT"):
        # Retrieve user information and login status from the session['hoc_toan_anh_thanh']
        username = session["username_HTAT"]
        login_status = session["login_HTAT"]
    else:
        return redirect('/hoc-toan-anh-thanh/login?redirectUrl=/hoc-toan-anh-thanh/tra-cuu-tien-trinh-hoc-tap')
    
    if request.method == 'GET':
        return render_template('hoc_toan_anh_thanh/tra_cuu_tien_trinh_hoc_tap.html', user=username, login_status=login_status)
    
    sheet_name = request.form.get('month_name')
    response_html = tra_cuu_tien_trinh_hoc_tap_helper(github_access_token=github_access_token,
                                                      username=username, sheet_name=sheet_name)
    
    return response_html

# ---------------------------- Login With Google functions --------------------------
@app.route('/login-with-google')
def login_with_google():
    redirectUrl = request.args.get('redirectUrl', '/hoc-toan-anh-thanh')

    client_secrets_file=current_app.config["login_with_google"]["client_secrets_file"]
    scopes=current_app.config["login_with_google"]["scopes"]
    redirect_uri = request.base_url + '/callback'
    # Remember to also include this redirect_uri in: current_app.config["login_with_google"]["web"]["redirect_uris"][5]
    
    flow = Flow.from_client_secrets_file(client_secrets_file=client_secrets_file,
                                         scopes=scopes,
                                         redirect_uri = redirect_uri)
    
    authorization_url, state = flow.authorization_url()

    session['state_login_with_google_HTAT'] = state

    TEMPORARY_STORAGE['flow_login_with_google'][session['state_login_with_google_HTAT']] = flow
    TEMPORARY_STORAGE['redirect_url_login_with_google'][session['state_login_with_google_HTAT']] = redirectUrl

    return redirect(authorization_url)


@app.route('/login-with-google/callback')
def callback_login_with_google():
    if not session.get("state_login_with_google_HTAT"):
        return redirect('/hoc-toan-anh-thanh/login-with-google')
    
    flow = TEMPORARY_STORAGE['flow_login_with_google'][session['state_login_with_google_HTAT']]
    redirectUrl = TEMPORARY_STORAGE['redirect_url_login_with_google'][session['state_login_with_google_HTAT']]
    state_login_with_google = session['state_login_with_google_HTAT']

    # Delete temporary information:
    TEMPORARY_STORAGE['flow_login_with_google'].pop(session["state_login_with_google_HTAT"])
    TEMPORARY_STORAGE['redirect_url_login_with_google'].pop(session['state_login_with_google_HTAT'])
    session.pop('state_login_with_google_HTAT')


    if state_login_with_google != request.args['state']:
        current_app.config['logger'].info("State does NOT match! Forced to login again.")
        return redirect('/hoc-toan-anh-thanh/login-with-google')
    
    GOOGLE_CLIENT_ID=current_app.config["login_with_google"]["web"]["client_id"]
    
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
    
    session['username_HTAT'] = google_name
    session['login_HTAT'] = True
    session['login_type_HTAT'] = 'google'

    # pdb.set_trace()
    
    
    return redirect(redirectUrl)

# ---------------------------- END OF Login With Google functions --------------------------
@app.route('/change-password', methods = ['GET', 'POST'])
def user_change_password():
    github_access_token = current_app.config['github']['access_token']

    if request.method == 'GET':
        page_name = "Change Password - Học Toán anh Thành"
        return render_template("hoc_toan_anh_thanh/change_password/tiny_form.html", page_name = page_name)
    
    data = request.get_json()
    old_password, new_password, confirm_new_password = data['old_password'], data['new_password'], data['confirm_new_password']

    if not session.get('login_HTAT'):
        response = {
            'status': 2,
            'message': 'REQUIRED: Login first.',
            'login_url': url_for('hoc_toan_anh_thanh.login') + '?redirectUrl=' + request.url
        }
        return jsonify(response)
    
    username = session.get("username_HTAT")
    response = hoc_toan_anh_thanh_helper.change_password(github_access_token=github_access_token,
                                                         username=username,
                                                         new_password=new_password, confirm_new_password=confirm_new_password)
    
    return jsonify(response)