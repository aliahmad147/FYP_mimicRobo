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
	logdir_train1 = '/home/hassan/Desktop/deep-voice-conversion/ckpt/{}/train1'.format(args.case1)
	logdir_train2 = '/home/hassan/Desktop/deep-voice-conversion/ckpt/{}/train2'.format(args.case2)

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
		logdir_train1 = '/home/hassan/Desktop/deep-voice-conversion/ckpt/{}/train1'.format(args.case1)
		logdir_train2 = '/home/hassan/Desktop/deep-voice-conversion/ckpt/{}/train2'.format(args.case2)

		audio, y_audio = do_convert(args.ckpt, args.case1, logdir1=logdir_train1, logdir2=logdir_train2, wavs=filepath)
		wavfilename="./results/{}.wav".format(uuid.uuid4().hex)
		scipy.io.wavfile.write(wavfilename, 16000, audio[0])
		return send_file(
		wavfilename,
		mimetype="audio/wav",
		as_attachment=True,
		attachment_filename="result.wav")
	else:
		return render_template("index.html")


if __name__ == '__main__':
    app.run()
