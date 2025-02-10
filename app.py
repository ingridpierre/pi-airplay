from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/now-playing')
def now_playing():
    # Mock data - replace with your actual music source
    return jsonify({
        'title': 'Sample Song',
        'artist': 'Sample Artist',
        'album': 'Sample Album'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)