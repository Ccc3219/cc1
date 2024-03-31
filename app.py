from flask import Flask, redirect, url_for, render_template, jsonify, Markup, request, Response
from pyEEG.Models.Operation import Analysis, FileManager, StateMessages
from pyEEG.Utils.Extensions import importEdf
from pyEEG.Models import Data
import os, datasets, time

app = Flask(__name__)

# 设置 SESSION_COOKIE_SAMESITE 为 'None'，以将 Cookie SameSite 属性设置为 None
app.config['SESSION_COOKIE_SAMESITE'] = 'None'

CURRENT_ANALYSIS=None
APP_DEBUG = False
welcome_message = """
  Eeg Analysis
"""

@app.route('/')
@app.route('/index')
@app.route('/welcome')
def home():
    global CURRENT_ANALYSIS
    CURRENT_ANALYSIS = None
    return render_template('welcome.html', title="Welcome", msg=Markup(welcome_message))

@app.route('/bad-req')
def invalid():
    return redirect(url_for("home"))


@app.route('/test')
def test():
    return render_template("test.html", title="test");

@app.route("/test_events")
def test_events():
    def event_stream():
        n= 0
        while True:
            yield "data: %s\n\n" % n
            n+=1

    return Response(event_stream(), mimetype='text/event-stream')


@app.route('/file_upload')
def file_upload():
   return render_template('fileupload.html', title="Yeni Analiz Yarat", script="data-upload.js")

@app.route('/handle_file_upload', methods=["POST", "GET"])
def handleFileUpload():
    global CURRENT_ANALYSIS
    if request.method == "POST":
        name = request.form['name']
        file = request.files['file']
        filename = file.filename
        if filename == "":
            msg = StateMessages.fail()
            msg["msg"] = "您尚未上传文件！"
            return jsonify(msg)
        else:
            path = FileManager.createNewDir()
            file_path = os.path.join(path, file.filename)
            file.save(file_path)
            try:
                f = FileManager.importEdf(file_path)
                d = Data.Dataset(f)
                d.initialize()
                CURRENT_ANALYSIS = Analysis(name, d)
                msg = StateMessages.success()
                msg["msg"] = "文件上传成功"
                msg["custom"] = CURRENT_ANALYSIS.getDictNoSignal()
                return jsonify(msg)
            except Exception as e:
                msg = StateMessages.fail()
                msg["msg"] = str(e)
                return jsonify(msg)
    if request.method == "GET" and APP_DEBUG :
        try:
            CURRENT_ANALYSIS = Analysis.createTestAnalysis()
            msg = StateMessages.success()
            msg["msg"] = "文件成功上传"
            msg["custom"] = CURRENT_ANALYSIS.getDictNoSignal()
            return jsonify(msg)
        except Exception as e:
            msg = StateMessages.fail()
            msg["msg"] = str(e)
            return jsonify(msg)
"""
这个请求是通过 data-upload.js 脚本中的方式发送的。表单数据中包含了edf文件
"""


@app.route("/workbench")
def renderWorkbench():
    global CURRENT_ANALYSIS
    if APP_DEBUG:
        try:
            CURRENT_ANALYSIS = Analysis.createTestAnalysis()
        except Exception as e:
            msg = StateMessages.fail()
            msg["msg"] = str(e)
            return jsonify(msg)
    if CURRENT_ANALYSIS != None:
        return render_template("workbench.html", title=(CURRENT_ANALYSIS.dataset.Name + " - Workbench"), script = "eeg-ui.js")
    else:
        return StateMessages.fail()

@app.route("/get_data", methods=["POST"])
def get_data():
    return_msg = StateMessages.success(msg="Successfully updated!", data=CURRENT_ANALYSIS.dataset.getDict())
    return return_msg

@app.route("/hp_prefilter", methods=["POST"])
def apply_hp_filter():
    hp_cutoff = float(request.form["hp_cutoff"])
    order = int(request.form["order"])
    if order > 5:
        order = 5
    print(hp_cutoff)
    CURRENT_ANALYSIS.dataset.high_pass_filter(hp_cutoff, order)
    return StateMessages.success(msg="滤波器成功应用")

@app.route("/lp_prefilter", methods=["POST"])
def apply_lp_filter():
    lp_cutoff = float(request.form["lp_cutoff"])
    order = int(request.form["order"])
    if order > 5:
         order = 5
    print(lp_cutoff)
    CURRENT_ANALYSIS.dataset.low_pass_filter(lp_cutoff, order)
    return StateMessages.success(msg="滤波器成功应用.")


app.run(host="127.0.0.1", port=5000)
if APP_DEBUG:
    print("Debug Mode Activated!")