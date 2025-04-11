from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory
from werkzeug.utils import secure_filename
import os
from stt_tts import speech_to_text, text_to_speech
from genai import model, upload_to_gemini
import fitz
import base64

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
PDF_FOLDER = 'pdfs'
RESPONSE_FOLDER = 'responses'
ALLOWED_EXTENSIONS = {'wav'}

for folder in [UPLOAD_FOLDER, PDF_FOLDER, RESPONSE_FOLDER]:
    os.makedirs(folder, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_files():
    files = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if allowed_file(filename):
            files.append(filename)
    files.sort(reverse=True)
    return files

def get_response_files():
    files = []
    for filename in os.listdir(RESPONSE_FOLDER):
        if filename.endswith('.wav'):
            base = filename[:-4]
            txt = base + '.txt'
            if txt in os.listdir(RESPONSE_FOLDER):
                files.append((filename, txt))
    files.sort(reverse=True)
    return files

def extract_pdf_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

@app.route('/')
def index():
    files = get_files()
    response_files = get_response_files()
    active_pdf = None
    if os.path.exists('active_pdf.txt'):
        with open('active_pdf.txt', 'r') as f:
            active_pdf = os.path.basename(f.read().strip())
    return render_template('index.html', files=files, active_pdf=active_pdf, responses=response_files)

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'pdf' not in request.files:
        return 'No PDF file uploaded.', 400
    file = request.files['pdf']
    filename = secure_filename(file.filename)
    file_path = os.path.join(PDF_FOLDER, filename)
    file.save(file_path)
    with open('active_pdf.txt', 'w') as f:
        f.write(file_path)
    return redirect('/')

@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'audio_data' not in request.files:
        return 'No audio data', 400
    file = request.files['audio_data']

    with open('active_pdf.txt', 'r') as f:
        pdf_path = f.read().strip()
    book_name = os.path.splitext(os.path.basename(pdf_path))[0]

    timestamp = datetime.now().strftime("%Y%m%d-%I%M%S%p")
    base_audio_filename = book_name + '_' + timestamp + '_Question.wav'
    audio_path = os.path.join(UPLOAD_FOLDER, base_audio_filename)
    file.save(audio_path)

    audio_question = upload_to_gemini(audio_path, mime_type="audio/wav")
    
    #transcript = speech_to_text(audio_path)

    speech_to_text(audio_path)

    #book_text = extract_pdf_text(pdf_path)

    book_pdf = upload_to_gemini(pdf_path, mime_type="application/pdf")

    # prompt = f"""
    # The following is the content of a book:
    # {book_text}.

    # Learn using this book and answer the following question:

    # "{transcript}"

    # Provide a helpful and concise response based only on the book.
    # """

    prompt = f"""
    The PDF file of a book is given.

    Learn using this book and answer the question/questions from the given audio file

    Provide a helpful and concise response based only on the book.
    """

    response = model.generate_content(contents=[book_pdf, audio_question, prompt])
    answer = response.text

    response_basename = f"{book_name}_{timestamp}"
    response_txt_path = os.path.join(RESPONSE_FOLDER, response_basename + '.txt')
    with open(response_txt_path, 'w') as f:
        f.write(answer)

    response_audio_path = os.path.join(RESPONSE_FOLDER, response_basename + '.wav')
    text_to_speech(text=answer, speech_file_path=response_audio_path)

    return redirect('/')

@app.route('/upload_text', methods=['POST'])
def upload_text():
    text = request.form['text']
    filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    text_to_speech(text=text, speech_file_path=file_path)

    text_file_path = file_path + '.txt'
    with open(text_file_path, "w") as f:
        f.write(text)

    # sentiment_file_path = file_path + '_sentiment.txt'
    # with open(sentiment_file_path, "w") as f:
    #     f.write("Sentiment Type: " + sentiment_type(text))

    return redirect('/')

@app.route('/script.js', methods=['GET'])
def scripts_js():
    return send_file('./script.js')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/responses/<filename>')
def response_file(filename):
    return send_from_directory(RESPONSE_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
    #app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
