import os
import wave
from flask import Flask, request, redirect, jsonify, send_file
import mimetypes
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException
import json
import numpy as np
from scipy.io import wavfile

mimetypes.add_type('application/javascript', '.js')
ALLOWED_EXTENSIONS = set(['wav'])

# File Signature of WAV file is "52 49 46 46 ?? ?? ?? ?? 57 41 56 45", based on the file signature the following bytearray segments are framed
WAV_FILE_FIRST_SEGMENT = bytearray([0x52, 0x49, 0x46, 0x46])
WAV_FILE_INTERMEDIATE_SEGMENT = bytearray([0x00, 0x00, 0x00, 0x00]) # It can hold any values in it
WAV_FILE_SECOND_SEGMENT = bytearray([0x57, 0x41, 0x56, 0x45])
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'tmp')

if not os.path.exists(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

def is_valid_signature(f):
 with open(f, "rb") as file:
    file_contents = file.read(len(WAV_FILE_FIRST_SEGMENT) + len(WAV_FILE_INTERMEDIATE_SEGMENT) + len(WAV_FILE_SECOND_SEGMENT))
    file.close()
    return file_contents.startswith(WAV_FILE_FIRST_SEGMENT) and file_contents.startswith(WAV_FILE_SECOND_SEGMENT, len(WAV_FILE_FIRST_SEGMENT) + len(WAV_FILE_INTERMEDIATE_SEGMENT))

def generate(path):
    with open(path, "rb") as f:
        yield from f
    os.remove(path)

def delete_file(filename):
    os.remove(os.path.join(UPLOAD_FOLDER, filename))

app = Flask(__name__, static_url_path='', static_folder='dist')
CORS(app, expose_headers=["Content-Disposition"])
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000


@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "message": e.name
    })
    response.content_type = "application/json"
    return response

@app.route('/')
def index():
    return app.send_static_file(filename="index.html")

@app.route('/api/process', methods=["POST"])
def process():
    operation = request.form.get('operation')
    if not operation or operation not in ['encode', 'decode']:
        resp = jsonify({'message' : 'Please enter valid operation as encode/decode'})
        resp.status_code = 400
        return resp
    method = request.form.get('method')
    if not method or method not in ['lsb', 'phase']:
        resp = jsonify({'message' : 'Please enter valid method as lsb/phase'})
        resp.status_code = 400
        return resp
    message = request.form.get('message')
    if operation == 'encode' and (not message or len(message) == 0):
        resp = jsonify({'message' : 'Please enter valid message to encode'})
        resp.status_code = 400
        return resp
    if 'file' not in request.files:
        resp = jsonify({'message' : 'No file part in the request'})
        resp.status_code = 400
        return resp
    file = request.files['file']
    if file.filename == '':
        resp = jsonify({'message' : 'No file selected for uploading'})
        resp.status_code = 400
        return resp
    if not file.filename.lower().endswith(".wav"):
        resp = jsonify({'message' : 'Only .wav file extensions allowed'})
        resp.status_code = 400
        return resp
    filename = secure_filename(file.filename)
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    if not is_valid_signature(os.path.join(UPLOAD_FOLDER, filename)):
        delete_file(filename)
        resp = jsonify({'message' : 'Invalid File contents'})
        resp.status_code = 400
        return resp

    if method == 'lsb':
        if operation == 'encode':

            # Open input file as binary file using wave
            waveaudio = wave.open(os.path.join(UPLOAD_FOLDER, filename), mode='rb')
            # Get the number of audio frames
            wave_nframes = waveaudio.getnframes()
            # Read the n number of audio frames
            wave_readframes = waveaudio.readframes(wave_nframes)
            # Convert the read frames to byte array
            frame_bytes = bytearray(list(wave_readframes))
            # Append dummy data to secret message to fill out rest of the bytes
            # Create bytes to match till the length of the actual wav file
            string = message + int((len(frame_bytes) - (len(message) * 8 * 8)) / 8) * '#'
            # Convert text to bit array 
            # Process is to convert Unicode of the element and convert it to binary, then remove the prepended 0b and apped 0
            bits = list(map(int, ''.join([bin(ord(i)).lstrip('0b').rjust(8,'0') for i in string])))
            # Replace LSB of each byte of the audio data by one bit from the text bit array
            for i, bit in enumerate(bits):
                frame_bytes[i] = (frame_bytes[i] & 254) | bit
            # Get the modified bytes
            frame_modified = bytearray(frame_bytes)
            # Create ouput file name from input file
            output = filename[:-4] + '_encoded' + filename[-4:]
            # Write the encoded audio file
            with wave.open(os.path.join(UPLOAD_FOLDER, output), 'wb') as fd:
                fd.setparams(waveaudio.getparams())
                fd.writeframes(frame_modified)
                fd.close()
            waveaudio.close()
            delete_file(filename)
            resp = app.response_class(generate(os.path.join(UPLOAD_FOLDER, output)), mimetype='audio/wav')
            resp.headers.set('Content-Disposition', 'attachment', filename=output)
            return resp

        else:
            # Open input file as binary file using wave
            waveaudio = wave.open(os.path.join(UPLOAD_FOLDER, filename), mode='rb')
            # Get the number of audio frames
            wave_nframes = waveaudio.getnframes()
            # Read the n number of audio frames
            wave_readframes = waveaudio.readframes(wave_nframes)
            # Convert the read frames to byte array
            frame_bytes = bytearray(list(wave_readframes))
            # Extract the LSB of each byte
            extracted = [frame_bytes[i] & 1 for i in range(len(frame_bytes))]
            # Convert byte array back to string
            string = "".join(chr(int("".join(map(str, extracted[i:i + 8])), 2)) for i in range(0, len(extracted), 8))
            waveaudio.close()
            delete_file(filename)
            # Cut off at the filler characters
            msg = string.split("###")
            if (len(msg) == 1):
                resp = jsonify({'message' : 'The File Does not contain any Encoded Content'})
                resp.status_code = 400
                return resp
            resp = jsonify({'message' : msg[0]})
            resp.status_code = 200
            return resp

    elif  method == 'phase':
        if operation == 'encode':
            # Read the Input file using wavfile provided by scipy package
            rate, audio_data1 = wavfile.read(os.path.join(UPLOAD_FOLDER, filename))
            # Left justify 100 characters using fillers (~)
            string_to_encode = message.ljust(100, '~')
            # Find text length in bits
            text_length = 8 * len(string_to_encode)
            # Find the chunk size using the given text length using numpy package
            chunk_size = int(2 * 2 ** np.ceil(np.log2(2 * text_length)))
            # From the obtained chunk file calculate the number of chunks that has to be created
            number_of_chunks = int(np.ceil(audio_data1.shape[0] / chunk_size))
            # Make a copy of the audio Data
            audio_data = audio_data1.copy()
            #Breaking the Audio into chunks
            if len(audio_data1.shape) == 1:
                audio_data.resize(number_of_chunks * chunk_size, refcheck=False)
                audio_data = audio_data[np.newaxis]
            else:
                audio_data.resize((number_of_chunks * chunk_size, audio_data.shape[1]), refcheck=False)
                audio_data = audio_data.T
            # Take out the chunks
            chunks = audio_data[0].reshape((number_of_chunks, chunk_size))

            # Applying DFT on audio chunks (Fourier Transform), Calculate absolute value element wise, Retruens the angle of chunks, Calculate discrete difference of the given axis
            chunks = np.fft.fft(chunks)
            magnitudes = np.abs(chunks)
            phases = np.angle(chunks)
            phase_diff = np.diff(phases, axis=0)

            # Convert message to encode into binary
            text_in_binary = np.ravel([[int(y) for y in format(ord(x), "08b")] for x in string_to_encode])

            # Convert message in binary to phase differences
            text_in_pi = text_in_binary.copy()
            text_in_pi[text_in_pi == 0] = -1
            text_in_pi = text_in_pi * -np.pi / 2

            mid_chunk = chunk_size // 2

            # Phase conversion
            phases[0, mid_chunk - text_length: mid_chunk] = text_in_pi
            phases[0, mid_chunk + 1: mid_chunk + 1 + text_length] = -text_in_pi[::-1]

            # Compute the phase matrix
            for i in range(1, len(phases)):
                phases[i] = phases[i - 1] + phase_diff[i - 1]
                
            # Apply Inverse fourier trnasform after applying phase differences
            chunks = (magnitudes * np.exp(1j * phases))
            chunks = np.fft.ifft(chunks).real

            # Combining all block of audio again
            audio_data[0] = chunks.ravel().astype(np.int16)    
            output = filename[:-4] + '_phase_encoded' + filename[-4:]
            wavfile.write(os.path.join(UPLOAD_FOLDER, output), rate, audio_data.T)
            delete_file(filename)
            resp = app.response_class(generate(os.path.join(UPLOAD_FOLDER, output)), mimetype='audio/wav')
            resp.headers.set('Content-Disposition', 'attachment', filename=output)
            return resp

        else:
            # Read the Input file using wavfile provided by scipy package
            rate, audio_data = wavfile.read(os.path.join(UPLOAD_FOLDER, filename))
            # Based on the encoded lenght, we consider the length of text block to be 800
            text_length = 800
            # Calculate Block length and mid of block
            block_length = 2 * int(2 ** np.ceil(np.log2(2 * text_length)))
            block_mid = block_length // 2

            # Get header info
            if len(audio_data.shape) == 1:
                code = audio_data[:block_length]
            else:
                code = audio_data[:block_length, 0]
            
            # Get the phase and convert it to binary
            code_phases = np.angle(np.fft.fft(code))[block_mid - text_length:block_mid]
            code_in_binary = (code_phases < 0).astype(np.int16)
            # Convert into characters
            code_in_int_code = code_in_binary.reshape((-1, 8)).dot(1 << np.arange(8 - 1, -1, -1))
            # Combine characters to original text
            decoded_text = "".join(np.char.mod("%c", code_in_int_code)).replace("~", "")
            delete_file(filename)
            resp = jsonify({'message' : decoded_text})
            resp.status_code = 200
            return resp

@app.route('/<path:path>')
def static_proxy(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(path)

if __name__ == "__main__":
    try:
        app.run()
    except Exception as e:
        print(e)