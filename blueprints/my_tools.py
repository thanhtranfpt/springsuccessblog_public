from flask import Blueprint, render_template, request, redirect, render_template_string, current_app
from utils.my_tools_helper import video_audio_mixer
from utils.common_utils import read_google_docs

app = Blueprint("my_tools", __name__)


# Initialize global variables: --------------------------------------------------------
# END OF Initialize global variables. -------------------------------------------------


@app.route('/')
def index():
    return render_template("my_tools/index.html")

@app.route('/video_audio_mixer', methods = ['GET', 'POST'])
def video_audio_mixer_tool():
    if request.method == 'GET':
        return render_template("my_tools/video_audio_mixer/uploads.html")
    
    video = request.files['video']
    audio = request.files['audio']
    audio_late_seconds = int(request.form.get("audio_late_seconds"))
    video_volumnx_percentage = float(request.form.get("video_volumnx_percentage"))/100

    mixer = video_audio_mixer()
    success, status = mixer.process_files(video=video, audio=audio, audio_late_seconds=audio_late_seconds, video_volumnx_percentage=video_volumnx_percentage, UPLOAD_FOLDER=current_app.config['UPLOAD_FOLDER'], RESULT_FOLDER=current_app.config["RESULT_FOLDER"])

    if success:
        # Sử dụng hàm của bạn để kết hợp audio và video
        mixer.mix()
        resultVideoUrl = "/" + mixer.result_path
        return render_template('my_tools/video_audio_mixer/uploads.html', resultVideoUrl = resultVideoUrl)
    
    if status == 0:
        return redirect(request.url)
    return 'Invalid file format!'


@app.route('/test_html', methods = ['GET', 'POST'])
def test_html():
    if request.method == 'POST':
        docs_link = request.form.get('docs_link')
        document_content = read_google_docs(docs_link=docs_link)
        return render_template_string(document_content)
    return render_template('my_tools/test_html/input_form.html')