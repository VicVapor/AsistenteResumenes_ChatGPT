import os
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from openai import OpenAI

from pypdf import PdfReader

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
upload_dir = os.path.join(basedir, 'uploads')
os.makedirs(upload_dir, exist_ok=True)


# Rutas
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    language = request.form['language']
    text = request.form.get('text')
    file = request.files.get('file')

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        resumen = generate_summary(filepath, language)
    elif text:
        resumen = generate_summary(text, language)
    else:
        resumen = "No se proporcionó ningún archivo o texto."

    return render_template('documentoResumido.html', summary=resumen, language=language)


def generate_summary(filepath, language):
    try:
        load_dotenv()
        api_key = os.environ.get("OPENAI_API_KEY")

        client = OpenAI(api_key=api_key)

        # Primero hay que leer el pdf
        with open(filepath, 'rb') as file:
            reader = PdfReader(file)
            text = ''
            for page in reader.pages:
                text += page.extract_text()

        if (language == "es"):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un experto en resúmenes de documentos"},
                    {"role": "user",
                     "content": f"Dame un resumen en español de este documento: {text}"},
                ],
            )

        elif (language == "en"):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert in document summaries"},
                    {"role": "user",
                     "content": f"Give me a summary in English of this document: {text}"},
                ],
            )

        respuestas = response.choices[0].message.content
        print(respuestas)
        client.close()
        return respuestas

    except Exception as e:
        print(e)
        text = ''
        if (language == "es"):
            text = "Error al generar el resumen. Tal vez el documento no se pudo leer correctamente o es demasiado largo."
        elif (language == "en"):
            text = "Error generating the summary. Perhaps the document could not be read correctly or is too long."
        return text


if __name__ == '__main__':
    # Primero vamos a borrar los archivos de la carpeta uploads para mantenerla limpia en cada inicio
    files = os.listdir(upload_dir)
    for file in files:
        os.remove(os.path.join(upload_dir, file))
    app.run(port=3000)
