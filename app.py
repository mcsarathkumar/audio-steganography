from flask import Flask
import mimetypes

mimetypes.add_type('application/javascript', '.js')

app = Flask(__name__, static_url_path='', static_folder='dist')
 
@app.route('/')
def index():
    return app.send_static_file(filename="index.html")

@app.route('/<path:path>')
def static_proxy(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(path)

if __name__ == "__main__":
        app.run()