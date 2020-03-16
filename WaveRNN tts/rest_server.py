#/usr/bin/python3
from flask import Flask, request, jsonify, send_file
import infer
import uuid
import zipfile, os

os.makedirs('quick_start/tts_weights/', exist_ok=True)
os.makedirs('quick_start/voc_weights/', exist_ok=True)

zip_ref = zipfile.ZipFile('pretrained/ljspeech.wavernn.mol.800k.zip', 'r')
zip_ref.extractall('quick_start/voc_weights/')
zip_ref.close()

zip_ref = zipfile.ZipFile('pretrained/ljspeech.tacotron.r2.180k.zip', 'r')
zip_ref.extractall('quick_start/tts_weights/')
zip_ref.close()
app = Flask(__name__)

@app.route('/tts_json',methods=['POST'])
def tts_json():
    # video: list of base64 of frames
    api_request = request.get_json()
    wav_filename = infer.tts(api_request["text"].strip())
    return send_file(
        wav_filename,
        mimetype="audio/wav",
        as_attachment=True,
        attachment_filename=wav_filename)


@app.route('/tts',methods=['GET','POST'])
def tts_form():
    # video: list of base64 of frames
    if request.method == 'POST':
        input_text = request.form['text'].strip()
        wav_filename = infer.tts(input_text)
        return send_file(
            wav_filename,
            mimetype="audio/wav",
            as_attachment=True,
            attachment_filename=wav_filename)
    return ''''
            <html>  

            <head>  
                <title>upload</title>  
                
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
            background-color: #4CAF50;
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


            <body>  
                    <!-- <div class="topnav">
                            <br>
                            <a class="navbar-brand text-white"  href="#"><h4>Mimic Robo</h4></a>
                            <ul class="navbar-nav">
                                <li class="nav-item active">
                                  <a class="nav-link" href="pehla.html">Pass Audio</a>
                                </li>
                              </ul>
                            
                            </div>
                         -->
                            <nav class="navbar-expand-lg bg-darknavbar navbar-expand-lg bg-dark navbar-dark text-white"><h4 align="center">Mimi Robo</h4>
                                <ul class="navbar-nav">
                                  <li class="nav-item active">
                                    <!-- <a class="nav-link" href="pehla.html">Upload a new File</a> -->
                                  </li>
                                </ul>
                              </nav>
                        </br>
                    </br>
                </br>


                            <div align="center">
                                    <form action = "/tts" method="POST" enctype="multipart/form-data">
                                     <select value="Select a speaker">
                                         <option value="Speaker1">Speaker1</option>
                                     </select>

                                    </br>
                                </br>
                                        <label for="name" align="center">Text:</label><input name="text"  style="height:45px; width:500px;padding:10px,10px;">
                                    </br>
                                </br>
                        
                                        <input type="submit" class="button1" value="Generate Voice">
                                   </form> 

                            </div>
                            
                
            </body>  
            </html>    

    '''


@app.route("/")
def hello():
    return "Hello World!"

@app.route("/error")
def get_nothing():
    """ Route for intentional error. """
    return "" # intentional non-existent variable


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
