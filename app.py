from flask import Flask, request, render_template_string, jsonify
import trimesh
import uuid

app = Flask(__name__)

# Realistic densities in g/cm³
MATERIAL_DENSITIES = {
    "PLA": 1.25,
    "PETG": 1.27,
    "TPU": 1.20
}

# Prices per gram
MATERIAL_PRICES = {
    "PLA": 0.12,
    "PETG": 0.12,
    "TPU": 0.20
}

calculation_results = {}

HTML = """
<!doctype html>
<html>
<head>
    <title>3D Print Quote</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        form, .result { margin-top: 20px; }
        input, select, button { margin: 5px 0; padding: 8px; width: 250px; }
    </style>
</head>
<body>
<h1>3D Print Quote</h1>

<form id="quoteForm" enctype="multipart/form-data">
    <label for="file">Upload 3D model (STL, OBJ, 3MF):</label><br>
    <input type="file" id="file" name="file" required><br>
    
    <label for="material">Select material:</label><br>
    <select name="material" id="material" required>
        <option value="PLA">PLA ($0.12/g)</option>
        <option value="PETG">PETG ($0.12/g)</option>
        <option value="TPU">TPU ($0.20/g)</option>
    </select><br>

    <button type="submit">Calculate Price</button>
</form>

<div class="result" id="result"></div>

<script>
document.getElementById('quoteForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const file = document.getElementById('file').files[0];
    const material = document.getElementById('material').value;
    if (!file) return alert("Please select a file");

    const formData = new FormData();
    formData.append('file', file);
    formData.append('material', material);

    const response = await fetch('/calculate', {
        method: 'POST',
        body: formData
    });
    const data = await response.json();

    const resultDiv = document.getElementById('result');
    resultDiv.innerText = 'Calculating...';

    const interval = setInterval(async () => {
        const res = await fetch(`/result/${data.id}`);
        const json = await res.json();
        if (json.result) {
            resultDiv.innerText = 'Price: ' + json.result;
            clearInterval(interval);
        }
    }, 1000);
});
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/calculate', methods=['POST'])
def calculate():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file_content = request.files['file']
    material = request.form.get('material', 'PLA')

    calc_id = str(uuid.uuid4())
    calculation_results[calc_id] = None

    try:
        file_type = file_content.filename.split('.')[-1].lower()
        if file_type not in ['stl', 'obj', '3mf']:
            calculation_results[calc_id] = f"Error: Unsupported file type {file_type}"
        else:
            mesh = trimesh.load(file_content, file_type=file_type)
            # Volume in mm³ → cm³
            volume_cm3 = mesh.volume / 1000
            mass_g = volume_cm3 * MATERIAL_DENSITIES.get(material, 1.25)
            price = mass_g * MATERIAL_PRICES.get(material, 0.12)
            calculation_results[calc_id] = f"${price:.2f}"
    except Exception as e:
        calculation_results[calc_id] = f"Error: {str(e)}"

    return jsonify({"id": calc_id})

@app.route('/result/<calc_id>')
def result(calc_id):
    return jsonify({"result": calculation_results.get(calc_id)})

if __name__ == '__main__':
    app.run(debug=True)
