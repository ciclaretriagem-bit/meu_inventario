import os
import csv
import json
from flask import Flask, render_template, request
from oauth2client.service_account import ServiceAccountCredentials
import gspread

app = Flask(__name__)
CSV_FILE = 'estoque.csv'

MATERIAIS_ORDEM = [
    "PET Cristal", "PET Misto/Cor", "PET Óleo", "PET Azul", "PET Verde", 
    "Alumínio", "PP Natural", "PP Color", "PEAD Natural/Br", "PEAD Cores", 
    "Metálicos", "Aerosol", "Papelao"
]

def inicializar_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Material', 'Quantidade'])
            for mat in MATERIAIS_ORDEM:
                writer.writerow([mat, 0.0])

def ler_estoque():
    estoque = {}
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            estoque[row['Material']] = float(row['Quantidade'])
    return estoque

def salvar_estoque(estoque):
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Material', 'Quantidade'])
        for mat in MATERIAIS_ORDEM:
            writer.writerow([mat, estoque.get(mat, 0.0)])

inicializar_csv()

@app.route('/')
def index():
    return render_template('index.html', materiais=MATERIAIS_ORDEM)

@app.route('/selecionar/<material>')
def selecionar(material):
    estoque = ler_estoque()
    return render_template('ajuste.html', material=material, qtd_atual=estoque.get(material, 0.0))

@app.route('/atualizar', methods=['POST'])
def atualizar():
    material = request.form.get('material')
    operacao = request.form.get('operacao')
    incremento = 0.5 if material in ["Metálicos", "Papelao"] else 1.0
    estoque = ler_estoque()
    qtd_atual = estoque.get(material, 0.0)
    if operacao == 'somar':
        estoque[material] = round(qtd_atual + incremento, 2)
    elif operacao == 'subtrair':
        estoque[material] = round(max(0.0, qtd_atual - incremento), 2)
    salvar_estoque(estoque)
    return render_template('ajuste.html', material=material, qtd_atual=estoque[material])

@app.route('/gravar')
def gravar():
    estoque = ler_estoque()
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Lê a credencial diretamente da memória (variável de ambiente)
        creds_data = json.loads(os.environ['GOOGLE_CREDENTIALS_JSON'])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_data, scope)
        client = gspread.authorize(creds)
        sheet = client.open("Controle de Triagem Ciclare").sheet1
        linha_dados = [estoque.get(mat, 0.0) for mat in MATERIAIS_ORDEM]
        sheet.append_row(linha_dados)
        salvar_estoque({mat: 0.0 for mat in MATERIAIS_ORDEM})
        return '''<script>alert("Contagem enviada!"); window.location.href="/";</script>'''
    except Exception as e:
        return f"Erro ao gravar: {str(e)} <br> <a href='/'>Voltar</a>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
