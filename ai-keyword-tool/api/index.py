from flask import Flask, request, jsonify, render_template_string
from openai import OpenAI
import os
import json
import re

app = Flask(__name__)

# API Key'i kodun içine yazmıyoruz, Vercel panelinden çekeceğiz
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def clean_json_string(json_string):
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, json_string, re.DOTALL)
    if match:
        return match.group(1)
    return json_string

@app.route('/')
def home():
    # Frontend HTML kodunu buraya gömüyoruz (Tek dosya olması yönetimi kolaylaştırır)
    html_content = """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Keyword Insight Tool</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: #f0f2f5; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            .main-card { border: none; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); background: white; }
            .btn-primary { background-color: #ff2d81; border: none; padding: 12px; border-radius: 10px; font-weight: 600; transition: all 0.3s; }
            .btn-primary:hover { background-color: #d61b65; transform: translateY(-2px); }
            .result-card { border-left: 4px solid #ff2d81; transition: transform 0.2s; }
            .result-card:hover { transform: translateX(5px); }
            .badge-custom { font-size: 0.8em; padding: 5px 10px; border-radius: 6px; }
        </style>
    </head>
    <body>
    <div class="container py-5">
        <div class="row justify-content-center">
            <div class="col-lg-8">
                <div class="main-card p-5 mb-4">
                    <div class="text-center mb-4">
                        <h2 class="fw-bold text-dark">AI Arama Niyeti Analizi</h2>
                        <p class="text-muted">Müşterilerinizin yapay zekaya (ChatGPT, Gemini) sorduğu gizli soruları keşfedin.</p>
                    </div>
                    
                    <form id="researchForm">
                        <div class="mb-4">
                            <label class="form-label fw-bold">Anahtar Kelime / Hizmet</label>
                            <input type="text" class="form-control form-control-lg" id="keyword" placeholder="Örn: Saç Ekimi, SEO Ajansı, Nakliyat..." required>
                        </div>
                        <div class="row g-3">
                            <div class="col-md-6">
                                <label class="form-label fw-bold">Hedef Dil</label>
                                <select class="form-select" id="language">
                                    <option value="Turkish">Türkçe</option>
                                    <option value="English">İngilizce</option>
                                    <option value="German">Almanca</option>
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-bold">Kullanıcı Niyeti</label>
                                <select class="form-select" id="intent">
                                    <option value="High Buying Intent">Yüksek (Satın Alma)</option>
                                    <option value="Research">Araştırma / Bilgi</option>
                                </select>
                            </div>
                        </div>
                        <div class="mt-4">
                            <button type="submit" class="btn btn-primary w-100 shadow" id="analyzeBtn">
                                Analiz Et & Soruları Üret
                            </button>
                        </div>
                    </form>
                </div>

                <div id="loading" class="text-center my-5" style="display:none;">
                    <div class="spinner-border text-primary" role="status"></div>
                    <p class="mt-2 text-muted">Yapay zeka sektörü analiz ediyor...</p>
                </div>

                <div id="resultsArea" style="display:none;">
                    <h5 class="mb-3 fw-bold ps-2">Tespit Edilen AI Arama Sorguları:</h5>
                    <div id="cardsContainer"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
    document.getElementById('researchForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const keyword = document.getElementById('keyword').value;
        const language = document.getElementById('language').value;
        const intent = document.getElementById('intent').value;
        
        document.getElementById('loading').style.display = 'block';
        document.getElementById('resultsArea').style.display = 'none';
        document.getElementById('cardsContainer').innerHTML = '';
        document.getElementById('analyzeBtn').disabled = true;

        fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ keyword, language, intent })
        })
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('cardsContainer');
            if(data.length === 0) {
                container.innerHTML = '<div class="alert alert-warning">Sonuç bulunamadı veya hata oluştu.</div>';
            }
            
            data.forEach(item => {
                let badgeClass = 'bg-secondary';
                if(item.type === 'Transactional') badgeClass = 'bg-success';
                if(item.type === 'Comparison') badgeClass = 'bg-warning text-dark';
                
                const html = `
                <div class="card mb-3 result-card shadow-sm">
                    <div class="card-body">
                        <div class="d-flex justify-content-between mb-2">
                            <span class="badge ${badgeClass} badge-custom">${item.type || 'Genel'}</span>
                            <small class="text-muted fw-bold">%${item.relevancy} Alaka</small>
                        </div>
                        <h5 class="card-title mb-0 text-dark">${item.question}</h5>
                    </div>
                </div>`;
                container.innerHTML += html;
            });
            document.getElementById('loading').style.display = 'none';
            document.getElementById('resultsArea').style.display = 'block';
            document.getElementById('analyzeBtn').disabled = false;
        })
        .catch(err => {
            console.error(err);
            document.getElementById('loading').style.display = 'none';
            document.getElementById('analyzeBtn').disabled = false;
        });
    });
    </script>
    </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    keyword = data.get('keyword')
    language = data.get('language')
    intent = data.get('intent')

    system_instruction = f"""
    Act as an AI Search Intent Expert.
    Keyword: "{keyword}"
    Language: "{language}"
    Intent: "{intent}"

    1. Identify the Persona (e.g., Patient, Manager).
    2. Generate 5 specific questions this persona asks AI.
    
    Output JSON ONLY:
    [
        {{"question": "Question text...", "relevancy": 90, "type": "Transactional"}},
        {{"question": "Question text...", "relevancy": 80, "type": "Comparison"}}
    ]
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo", # veya gpt-3.5-turbo
            messages=[{"role": "system", "content": system_instruction}],
            temperature=0.7
        )
        content = clean_json_string(response.choices[0].message.content)
        return jsonify(json.loads(content))
    except Exception as e:
        print(e)
        return jsonify([])

if __name__ == '__main__':
    app.run()