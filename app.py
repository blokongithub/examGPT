import flask
from flask import Flask, request, jsonify, render_template, redirect, make_response, send_file
import backend
import os
import zipfile
from io import BytesIO

app = flask.Flask(__name__)
HOST = 5000

@app.route('/')
def index():
    return redirect('/home')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        backend.register(username, password) #TODO
        return redirect('/login')

    return render_template('register.html')

def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if backend.login(username, password): #TODO
            return redirect('/generate')
        else:
            return render_template('login.html')

    return render_template('login.html')

@app.route('/generate', methods=['GET', 'POST'])
def generate_exam():
    if request.method == 'POST':
        exam = request.form['exam']
        board = request.form['board']
        subject = request.form['subject']
        questions = int(request.form['questions'])

        # Get the paths of the generated PDF files
        qpdf_file, apdf_file = backend.genexam(exam, board, subject, questions)

        # Create a ZIP file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            zip_file.write(qpdf_file, arcname='question_paper.pdf')
            zip_file.write(apdf_file, arcname='mark_scheme.pdf')
        zip_buffer.seek(0)

        resp = make_response(send_file(zip_buffer, as_attachment=True, download_name='exam.zip', mimetype='application/zip'))
        return resp

    return render_template('generate.html')

if __name__ == '__main__':
    backend.startup()
    app.run(port=HOST, debug=True)