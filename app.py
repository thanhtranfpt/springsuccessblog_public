from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
import os

from config.loader import cfg
from utils.logging_utils import Logger
from utils.me_sites_helper import render_certificate_images

from blueprints.admin import admin
from blueprints.my_notes import my_notes
from blueprints.hoc_toan_anh_thanh import app as hoc_toan_anh_thanh
from blueprints.my_tools import app as my_tools


app = Flask(__name__, template_folder = './templates')
CORS(app=app)


#-----------------------------------------------------------------------------
#------------------- Thiết lập các configs: ----------------------------------
# App logger
app.config["logger"] = Logger(log_file_path=cfg.app["log_file"]["path"], max_log_size=cfg.app["log_file"]["max_log_size"], max_kept_size=cfg.app["log_file"]["max_kept_size"])

# App secret
app.secret_key = cfg.app['secret_key']

# Running Environment:
app.config['env'] = cfg.env
if "OAUTHLIB_INSECURE_TRANSPORT" in app.config['env']:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = cfg.env['OAUTHLIB_INSECURE_TRANSPORT']

# App folders
app.config['UPLOAD_FOLDER'] = cfg.app['UPLOAD_FOLDER']
app.config['RESULT_FOLDER'] = cfg.app['RESULT_FOLDER']
app.config['DOWNLOAD_FOLDER'] = cfg.app['DOWNLOAD_FOLDER']
folders = [app.config['UPLOAD_FOLDER'], app.config['RESULT_FOLDER'], app.config['DOWNLOAD_FOLDER']]
for folder in folders:
    if not os.path.isdir(folder):
        os.mkdir(folder)

# Admin sites
app.config['admin_account'] = cfg.app["admin_account"]
app.config['admin_emails'] = cfg.app["admin_emails"]

# GitHub
app.config["github"] = cfg.github

# My notes
app.config["my_notes"] = cfg.my_notes

# Login with Google
app.config["login_with_google"] = cfg.login_with_google

app.config["logger"].info(str(app.config) + "\n - KEYS: " + str(app.config.keys()), topic = "Completed configuration setup.")
#------------------- Done of Thiết lập các configs. ---------------------------
#------------------------------------------------------------------------------


@app.route('/')
def index():
    return render_template('me/index.html')

@app.route('/about-me')
def about_me():
    pos_list, src_list, num_images = render_certificate_images()
    return render_template('me/cv/index.html', pos_list = pos_list, src_list = src_list, num_images = num_images)

@app.route('/' + app.config['DOWNLOAD_FOLDER'] + '/<filename>')
def download_result(filename):
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


#-------------------- Admin sites -----------------------
app.register_blueprint(admin, url_prefix='/admin')

#--------------------- My notes -------------------------
app.register_blueprint(my_notes, url_prefix = '/notes')

#--------------------- Học Toán anh Thành ---------------
app.register_blueprint(hoc_toan_anh_thanh, url_prefix = '/hoc-toan-anh-thanh')

#--------------------- My tools -------------------------
app.register_blueprint(my_tools, url_prefix = '/tools')



if __name__ == '__main__':
    app.run(debug=True)