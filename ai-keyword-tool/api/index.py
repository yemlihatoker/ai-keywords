from flask import Flask, request, jsonify, render_template_string
import os
import json
import re

# NOT: OpenAI'ı burada import ETMİYORUZ. Aşağıda edeceğiz.
# Böylece site açılırken hata vermeyecek.

app = Flask(__name__)

def clean_json_string(json_string):
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, json_string, re.DOTALL)
    if match:
        return match.group(1)
    return json_string

@app.route('/')
def home():
    html_content = """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Analiz Aracı</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
    <div class="container py-5">
        <div class="card shadow p-4">
            <h2 class="text-center text-primary mb-3">AI Arama Niyeti Analizi</h2>
            <div class="alert alert-success text-center">✅ Site Başarıyla Açıldı!</div>
            
            <form id="researchForm">
                <div class="mb-3">
                    <label class="fw-bold">Anahtar Kelime</label>
                    <input type="text" class="form-control" id="keyword" placeholder="Örn: Nakliyat" required>
                </div>
                <div class="row mb-3">
                    <div class="col"><label>Dil</label><select id="language" class="form-select"><option>Turkish</option><option>English</option></select></div>
                    <div class="col"><label>Niyet</label><select id="intent" class="form-select"><option>High Buying Intent</option><option>Informational</option></select></div>
                </div>
                <button type="submit" class="btn btn-primary w-100" id="analyzeBtn">Analiz Et</button>
            </form>
            <div id="loading" class="text-center mt-3" style="display:none;">
                <div class="spinner-border text-primary" role="status"></div>
                <p>Yapay zeka düşünüyor...</p>
            </div>
            <div id="resultsArea" class="mt-4"></div>
        </div>
    </div>

    <script>
    document.getElementById('researchForm').addEventListener('submit', function(e) {
        e.preventDefault();
        document.getElementById('loading').style.display = 'block';
        document.getElementById('resultsArea').innerHTML = '';
        
        fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                keyword: document.getElementById('keyword').value,
                language: document.getElementById('language').value,
                intent: document.getElementById('intent').value
            })
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('loading').style.display = 'none';
            if(data.error) {
                document.getElementById('resultsArea').innerHTML = '<div class="alert alert-danger"><b>Hata:</b> ' + data.error + '</div>';
            } else {
                data.forEach(item => {
                    let color = item.type === 'Transactional' ? 'success' : 'warning';
                    document.getElementById('resultsArea').innerHTML += 
                        '<div class="card p-3 mb-2 border-start border-4 border-'+color+' shadow-sm">' + 
                        '<h5>' + item.question + '</h5>' +
                        '<small class="text-muted">Alaka: %' + item.relevancy + ' • Tür: ' + item.type + '</small></div>';
                });
            }
        })
        .catch(err => {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('resultsArea').innerHTML = '<div class="alert alert-danger">Sunucu bağlantı hatası.</div>';
        });
    });
    </script>
    </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/analyze', methods=['POST'])
def analyze():
    # KÜTÜPHANELERİ BURADA İÇE AKTARIYORUZ (Lazy Import)
    # Eğer requirements.txt hatası varsa, hatayı burada yakalayıp ekrana basacağız.
    try:
        from openai import OpenAI
    except ImportError:
        return jsonify({"error": "OpenAI kütüphanesi bulunamadı! Lütfen requirements.txt dosyasının ana dizinde olduğundan emin olun."}), 500

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return jsonify({"error": "API Anahtarı (OPENAI_API_KEY) Vercel ayarlarında eksik."}), 500

    try:
        client = OpenAI(api_key=api_key)
        data = request.json
        
        system_instruction = f"""
        Generate 3 search questions for keyword: "{data.get('keyword')}" in "{data.get('language')}".
        Format: JSON Array ONLY. Example: [{{ "question": "...", "relevancy": 90, "type": "Transactional" }}]
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system_instruction}]
        )
        content = clean_json_string(response.choices[0].message.content)
        return jsonify(json.loads(content))
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run()
