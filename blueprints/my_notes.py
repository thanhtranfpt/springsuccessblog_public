from flask import Blueprint, request, current_app, render_template, jsonify, session, redirect, url_for, render_template_string
from utils.my_notes_helper import get_notes_list, get_categories_info, post_note as post_note_helper, create_category_helper, load_notes
from utils import my_notes_helper
from utils.common_utils import convert_to_snake_case
import requests
import json


my_notes = Blueprint("my_notes", __name__)


# Initialize global variables: --------------------------------------------------------
# END OF Initialize global variables. -------------------------------------------------



@my_notes.before_request
def before_request():
    pass


@my_notes.route('/')
def index():
    github_access_token = current_app.config["github"]["access_token"]

    category_name = request.args.get('category', '')
    category_id = convert_to_snake_case(category_name)

    notes_list = get_notes_list(category=category_id, github_access_token=github_access_token)

    page_title = "Spring Success Notes"
    heading = category_name if category_name else "My Notebook"
    
    return render_template("my_notes/my_notes_v2.html", page_title = page_title, heading = heading, notes_list = notes_list)

@my_notes.route('/post', methods = ['GET', 'POST'])
def post_note():
    github_access_token = current_app.config["github"]["access_token"]

    if request.method == 'GET':
        
        categories_info = get_categories_info(github_access_token=github_access_token)
        
        return render_template('my_notes/post_form.html', categories_info = categories_info)
    
    if not session.get('login_my_notes'):
        response_data = {
            'status_code': -1,
            'message': 'Login required: Please login to Spring Success Notebook first, then comeback to this page to create your category again!',
            'loginUrl': request.url.replace('post', 'enter-secret-key?redirectUrl=/notes/post')
            }
        return jsonify(response_data)
    
    # title = request.form['title']
    # content = request.form['content']
    # custom_others = request.form['custom_others']
    # category = request.form['category']
    # tags = request.form['tags']
    # visible = request.form['visible']

    data = request.get_json()
    
    title, content, custom_others, category, tags, visible = data['title'], data['content'], data['custom_others'], data['category'], data['tags'], data['visible']

    response_data = post_note_helper(github_access_token, title, content, custom_others, category, tags, visible)

    return jsonify(response_data)


@my_notes.route('/add-category', methods = ['GET', 'POST'])
def create_category():
    github_access_token = current_app.config["github"]["access_token"]
    
    if request.method == 'GET':
        return render_template('my_notes/with_category/create_category.html')
    
    if not session.get('login_my_notes'):
        response_data = {
            'status': '-1',
            'message': 'Please login to Spring Success Notebook first, then comeback to this page to create your category again!',
            'loginUrl': request.url.replace('add-category', 'enter-secret-key?redirectUrl=/notes/add-category')
        }
        return jsonify(response_data)
    
    catName = request.form['catName']
    catType = request.form['catType']
    catDesc = request.form['catDesc']
    
    response_data = create_category_helper(catName=catName, catType=catType, catDesc=catDesc,
                                           github_access_token=github_access_token)
    
    return jsonify(response_data)


@my_notes.route('/show-secret-note', methods = ['GET', 'POST'])
def get_secret_note():
    if not session.get("login_my_notes"):
        if request.method == 'GET':
            return redirect('/enter-secret-key?redirectUrl=' + request.url)
        
        data = request.get_json()
        secret_key = data["secret_key"]
        if secret_key != current_app.config["my_notes"]["secret_key"]:
            response = {
                'status_code': 0,
                'message': "Nhập sai mã bí mật!"
            }

            return jsonify(response)
        
    note_id = request.args.get("noteID", "")
    if note_id == '':
        response = {
            'status_code': 0,
            'message': 'Note ID NONE.'
        }
        return jsonify(response)
    
    notes = load_notes(github_access_token=current_app.config["github"]["access_token"])
    if note_id not in notes['id'].values:
        response = {
            'status_code': 0,
            'message': 'Note ID NOT exists.'
        }
        return jsonify(response)
    
    notes.set_index('id', inplace=True)
    note_content = notes.loc[note_id, 'content']
    note_custom_others = notes.loc[note_id, 'custom_others']
    response = {
        'status_code': 1,
        'note_content': note_content,
        'note_custom_others': note_custom_others
    }

    return jsonify(response)

@my_notes.route('/enter-secret-key', methods = ['GET', 'POST'])
def enter_secret_key():
    if request.method == 'GET':
        redirectUrl = request.args.get('redirectUrl', '/notes')
        return render_template('my_notes/secret_key_input_form/index.html', redirectUrl = redirectUrl)
    
    data = request.get_json()
    secret_key = data['secret_key']

    if secret_key == current_app.config["my_notes"]["secret_key"]:
        session["login_my_notes"] = True

        response = {
            'status_code': 1,
            'message': 'Mã bí mật đúng rồi.'
        }
        
        return jsonify(response)
    
    response = {
        'status_code': 0,
        'message': 'Mã bí mật KHÔNG ĐÚNG!'
    }

    return jsonify(response)

@my_notes.route('/log-out')
def log_out():
    session.pop('login_my_notes', 'None')
    return redirect('/notes')

@my_notes.route('/update-note', methods = ['GET', 'POST'])
def update_note():
    note_id = request.args.get('noteID', '')
    github_access_token = current_app.config['github']['access_token']

    if request.method == 'GET':
        note = my_notes_helper.get_note(note_id=note_id, github_access_token=github_access_token)
        if note is not None and note['visible'] == 'private' and not session.get('login_my_notes'):
            return redirect(url_for('my_notes.enter_secret_key') + '?redirectUrl=' + request.url)
        
        old_note_content = note['content'] if note is not None else 'Note not founds.'
        return render_template('my_notes/update_form_v2.html', note_id = note_id, old_content = old_note_content)
        # return render_template('my_notes/update_form_v1.html', note_id = note_id)
    
    data = request.get_json()
    note_id, new_content = data['note_id'], data['new_content']

    if not session.get('login_my_notes'):
        response = {
            'status': 2,
            'message': 'Please login to Spring Success Notebooks first, then comeback to this page to update your note again!',
            'login_url': url_for('my_notes.enter_secret_key') + '?redirectUrl=' + request.url
        }
        return jsonify(response)
    
    response = my_notes_helper.update_note(github_access_token=github_access_token,
                                           note_id=note_id, new_content=new_content)
    
    return jsonify(response)

@my_notes.route('/delete-note')
def delete_note():
    github_access_token = current_app.config['github']['access_token']

    note_id = request.args.get('noteID', '')

    if not session.get('login_my_notes'):
        response = {
            'status': 2,
            'message': "Please login to Spring Success Notebooks first, then comeback to this page to delete your note again!",
            'login_url': url_for('my_notes.enter_secret_key') + "?redirectUrl=" + request.url
        }
        return jsonify(response)
    
    response = my_notes_helper.delete_note(github_access_token=github_access_token,
                                           note_id=note_id)
    
    return jsonify(response)

@my_notes.route('/view-note')
def view_note():
    note_id = request.args.get('noteID', '')
    github_access_token = current_app.config['github']['access_token']

    note, categories_list = my_notes_helper.get_note(note_id=note_id, github_access_token=github_access_token, get_categories=True)
    
    if note is None:
        return "Note not founds."
    
    if note['visible'] == 'private' and not session.get('login_my_notes'):
        return redirect(url_for('my_notes.enter_secret_key') + '?redirectUrl=' + request.url)
    
    page_title = "View note - " + note['title']

    return render_template("my_notes/view_note.html", page_title = page_title, note = note, categories_list = categories_list)

@my_notes.route('/delete-category')
def delete_category():
    github_access_token = current_app.config['github']['access_token']
    
    category_id = request.args.get('categoryId', '')

    if not session.get('login_my_notes'):
        response = {
            'status': 2,
            'message': 'Please login to Spring Success Notebooks first, then comeback to this page to delete your category again!',
            'login_url': url_for('my_notes.enter_secret_key') + '?redirectUrl=' + request.url
        }

        return jsonify(response)
    
    response = my_notes_helper.delete_category(category_id=category_id,
                                               github_access_token=github_access_token)
    
    return jsonify(response)

@my_notes.route('/edit-category', methods = ['GET', 'POST'])
def edit_category():
    github_access_token = current_app.config['github']['access_token']
    
    categories_df = my_notes_helper.load_categories(github_access_token=github_access_token)
    
    if request.method == 'GET':
        category_id = request.args.get('categoryId', '')
        if category_id != '':
            categories_df = categories_df[categories_df['id'] == category_id]

        categories_list = json.loads(categories_df.to_json(orient='records'))
        return render_template('my_notes/with_category/edit_category_form.html', categories_list = categories_list,
                               NUM_CATEGORY = len(categories_list))
    
    data = request.form.to_dict()
    print("Received data = ", data)
    category_id = data['category_id']
    new_category_name = data['new_category_name']
    new_category_description = data['new_category_description']

    if not session.get('login_my_notes'):
        response = {
            'status': 2,
            'message': 'Please login to Spring Success Notebooks first, then comeback to this page to edit your category again!',
            'login_url': url_for('my_notes.enter_secret_key') + '?redirectUrl=' + request.url
        }
        return jsonify(response)
    
    response = my_notes_helper.edit_category(github_access_token=github_access_token,
                                             categories_df=categories_df,
                                             category_id=category_id,
                                             new_category_name=new_category_name,
                                             new_category_description=new_category_description)
    
    return response