from flask import Flask, request, jsonify, render_template_string
from openai import OpenAI
import os
import json
import re

app = Flask(__name__)

# NOT: client değişkenini burada tanımlamıyoruz, hata vermesin diye aşağıya aldık.

def clean_json_string(json_string):
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, json_string, re.DOTALL)
    if match:
        return match.group(1)
    return json_string

@app.route('/')
def home():
    # API Key kontrolü (Ekrana uyarı basmak için)
    key_status = "✅ Bağlı" if os.environ.get("OPENAI_API_KEY") else "❌ Eksik!"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Keyword Tool</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
    <div class="container py-5">
        <div class="card shadow p-4">
            <h2 class="text-center mb-3">AI Arama Niyeti Analizi</h2>
            <p class="text-center text-muted">API Durumu: <strong>{key_status}</strong></p>
            
            <form id="researchForm">
                <div class="mb-3">
                    <label>Anahtar Kelime</label>
                    <input type="text" class="form-control" id="keyword" placeholder="Örn: Nakliyat" required>
                </div>
                <div class="row">
                    <div class="col-6"><label>Dil</label><select id="language" class="form-select"><option>Turkish</option><option>English</option></select></div>
                    <div class="col-6"><label>Niyet</label><select id="intent" class="form-select"><option>High Buying Intent</option><option>Informational</option></select></div>
                </div>
                <button type="submit" class="btn btn-danger w-100 mt-3" id="analyzeBtn">Analiz Et</button>
            </form>
            <div id="loading" class="text-center mt-3" style="display:none;">Lütfen bekleyin...</div>
            <div id="resultsArea" class="mt-4"></div>
        </div>
    </div>

    <script>
    document.getElementById('researchForm').addEventListener('submit', function(e) {{
        e.preventDefault();
        document.getElementById('loading').style.display = 'block';
        document.getElementById('resultsArea').innerHTML = '';
        
        fetch('/analyze', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{
                keyword: document.getElementById('keyword').value,
                language: document.getElementById('language').value,
                intent: document.getElementById('intent').value
            }})
        }})
        .then(response => response.json())
        .then(data => {{
            document.getElementById('loading').style.display = 'none';
            if(data.error) {{
                document.getElementById('resultsArea').innerHTML = '<div class="alert alert-danger">' + data.error + '</div>';
            }} else {{
                data.forEach(item => {{
                    document.getElementById('resultsArea').innerHTML += '<div class="card p-2 mb-2 border-start border-4 border-danger">' + item.question + ' <span class="badge bg-secondary">' + item.relevancy + '%</span></div>';
                }});
            }}
        }})
        .catch(err => {{
            document.getElementById('loading').style.display = 'none';
            document.getElementById('resultsArea').innerHTML = '<div class="alert alert-danger">Sunucu Hatası.</div>';
        }});
    }});
    </script>
    </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/analyze', methods=['POST'])
def analyze():
    # API KEY'İ BURADA ÇAĞIRIYORUZ (GÜVENLİ YÖNTEM)
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("HATA: API Key bulunamadı.")
        return jsonify({"error": "Sunucuda OPENAI_API_KEY tanımlanmamış!"}), 500

    try:
        client = OpenAI(api_key=api_key)
        data = request.json
        
        system_instruction = f"""
        Generate 3 search questions for keyword: "{data.get('keyword')}" in "{data.get('language')}".
        Format: JSON Array [{{ "question": "...", "relevancy": 90, "type": "Transactional" }}]
        Only JSON.
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system_instruction}]
        )
        content = clean_json_string(response.choices[0].message.content)
        return jsonify(json.loads(content))
        
    except Exception as e:
        print(f"HATA DETAYI: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run()
