#/usr/bin/python3
from flask import Flask, request, jsonify, send_file, render_template
from api_convert import do_convert
import flask_hparam as args
from hparam import hparam as hp
import librosa
import numpy as np
import scipy
import uuid
app = Flask(__name__)


#@app.route('/')
#def hello():
#    return "Hello World!"

@app.route("/")
def fileFrontPage():
	return render_template('index.html')

@app.route('/convert1')
def voice_convert1():
	api_request = request.get_json()
	#logdir_train1 = '{}/{}/train1'.format(hp.logdir_path, args.case1)
	#logdir_train2 = '{}/{}/train2'.format(hp.logdir_path, args.case2)
	logdir_train1 = '/home/irfan/Desktop/deep-voice-conversion/ckpt/{}/train1'.format(args.case1)
	logdir_train2 = '/home/irfan/Desktop/deep-voice-conversion/ckpt/{}/train2'.format(args.case2)

	audio, y_audio = do_convert(args.ckpt, args.case1, logdir1=logdir_train1, logdir2=logdir_train2, wavs=api_request['wavs'])
	print(audio.shape)
	scipy.io.wavfile.write("./results/a1.wav", 16000, audio[0].astype(np.float32))
	return { "data": "success"}

@app.route('/convert', methods=['POST'])
def voice_convert():
	#api_request = request.get_json()
	#logdir_train1 = '{}/{}/train1'.format(hp.logdir_path, args.case1)
	#logdir_train2 = '{}/{}/train2'.format(hp.logdir_path, args.case2)
	file_ = request.files['file']
	filepath = "./upload/{}".format(file_.filename)
	file_.save(filepath)
	logdir_train1 = '/home/irfan/Desktop/deep-voice-conversion/ckpt/{}/train1'.format(args.case1)
	logdir_train2 = '/home/irfan/Desktop/deep-voice-conversion/ckpt/{}/train2'.format(args.case2)

	audio, y_audio = do_convert(args.ckpt, args.case1, logdir1=logdir_train1, logdir2=logdir_train2, wavs=filepath)
	wavfilename="./results/{}.wav".format(uuid.uuid4().hex)
	scipy.io.wavfile.write(wavfilename, 16000, y_audio[0])
	return send_file(
	wavfilename,
	mimetype="audio/wav",
	as_attachment=False,
	attachment_filename="result.wav")

@app.route('/upload', methods=['GET','POST'])
def upload_and_convert():
	if request.method == 'POST':
		#api_request = request.get_json()
		#logdir_train1 = '{}/{}/train1'.format(hp.logdir_path, args.case1)
		#logdir_train2 = '{}/{}/train2'.format(hp.logdir_path, args.case2)
		file_ = request.files['file']
		filepath = "./upload/{}".format(file_.filename)
		file_.save(filepath)
		logdir_train1 = '/home/irfan/Desktop/deep-voice-conversion/ckpt/{}/train1'.format(args.case1)
		logdir_train2 = '/home/irfan/Desktop/deep-voice-conversion/ckpt/{}/train2'.format(args.case2)

		audio, y_audio = do_convert(args.ckpt, args.case1, logdir1=logdir_train1, logdir2=logdir_train2, wavs=filepath)
		wavfilename="./results/{}.wav".format(uuid.uuid4().hex)
		scipy.io.wavfile.write(wavfilename, 16000, audio[0])
		return send_file(
		wavfilename,
		mimetype="audio/wav",
		as_attachment=False,
		attachment_filename="result.wav")
	else:
		return '''
		   
<!doctype html>
<head>

		<link rel="stylesheet" href="css/bootstrap4.min.css" type="text/css">
		<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
	
	<style>
		.topnav {
 		overflow: hidden;
  		background-color: #333;
  		height:60px;
  		border-radius: 6px;
	}
	.button1{
            background-color: crimson;
		border: none;
  		color: white;
  		padding: 8px 15px;
  		text-align: center;
  		text-decoration: none;
  		display: inline-block;
  font-size: 15px;
  margin: 4px 2px;
  cursor: pointer;
  border-radius: 12px;
        }
		.button2{
            background-color: burlywood;
		border: none;
  		color: white;
  		padding: 8px 15px;
  		text-align: center;
  		text-decoration: none;
  		display: inline-block;
  font-size: 15px;
  margin: 4px 2px;
  cursor: pointer;
  border-radius: 12px;
        }
		
		</style>
</head>
	<nav class="navbar-expand-lg bg-darknavbar navbar-expand-lg bg-dark navbar-dark text-white"><h4>Mimi Robo</h4>
	<ul class="navbar-nav">
	  <li class="nav-item active">
		<a class="nav-link" href="doosra.html">Generate Voice</a>
	  </li>
	</ul>
  </nav>
	<div align="center">
		<title>Upload new File</title>
		<h1>Upload new File</h1>
		<form method=post enctype=multipart/form-data class="button2">
		  <input type=file name=file>
		  <input type=submit value=Upload class="button1">
		</form>
	
	</div>
		
		    '''

if __name__ == '__main__':
    app.run()
