from flask import Flask, request, jsonify, render_template_string
import trimesh

app = Flask(__name__)

# Filament properties
FILAMENT_DENSITY = 1.25 / 1000  # g/mm³
COST_PER_GRAM = {"PLA": 0.12, "PETG": 0.12, "TPU": 0.20, "PETG-CF": 0.20}

# Supported file types
SUPPORTED_EXTENSIONS = ["stl", "obj", "3mf"]

# HTML template
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>3D Print Quote Generator</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        h1 { margin-bottom: 40px; }
        .drop-zone {
            border: 2px dotted green;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            margin-bottom: 20px;
        }
        input[type=file] { display:none; }
        label { font-weight: bold; display:block; }
        select { margin-bottom: 30px; padding: 5px; }
        button {
            background-color: #007BFF;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            display:block;
            margin-bottom: 20px;
        }
        button:hover { background-color: #0056b3; }
        .result { font-size: 1.2em; margin-top: 20px; }
        #loading-bar {
            display:none;
            width: 100%;
            height: 20px;
            background-color: #f3f3f3;
            border-radius: 5px;
            margin-bottom: 20px;
            overflow: hidden;
        }
        #loading-bar-inner {
            height: 100%;
            width: 0%;
            background-color: #007BFF;
            transition: width 0.2s;
        }
        #file-name {
            margin-top: 10px;
            margin-bottom: 20px;
            font-style: italic;
        }
    </style>
</head>
<body>
    <h1>3D Print Quote Generator</h1>

    <label class="drop-zone" for="file">Drag and drop your STL, OBJ, or 3MF file here</label>
    <input type="file" id="file" name="file" onchange="updateFileName()">
    <div id="file-name"></div>

    <label for="material" style="margin-top:50px; margin-bottom:15px;">Select Material:</label>
    <select name="material" id="material">
        <option value="PLA">PLA ($0.12/g)</option>
        <option value="PETG">PETG ($0.12/g)</option>
        <option value="TPU">TPU ($0.20/g)</option>
        <option value="PETG-CF">PETG-CF ($0.20/g)</option>
    </select>

    <button onclick="calculateQuote()">Get Quote</button>

    <div id="loading-bar"><div id="loading-bar-inner"></div></div>

    <div class="result" id="result"></div>

    <script>
        function updateFileName() {
            let fileInput = document.getElementById('file');
            let fileNameDiv = document.getElementById('file-name');
            if (fileInput.files.length > 0) {
                fileNameDiv.textContent = "Selected file: " + fileInput.files[0].name;
            } else {
                fileNameDiv.textContent = "";
            }
        }

        function calculateQuote() {
            let fileInput = document.getElementById('file');
            if (!fileInput.files.length) {
                alert("Please select a file first.");
                return;
            }
            let material = document.getElementById('material').value;
            let file = fileInput.files[0];

            let formData = new FormData();
            formData.append("file", file);
            formData.append("material", material);

            let loadingBar = document.getElementById('loading-bar');
            let loadingInner = document.getElementById('loading-bar-inner');
            let resultDiv = document.getElementById('result');
            resultDiv.textContent = "";
            loadingInner.style.width = '0%';
            loadingBar.style.display = 'block';

            let progress = 0;
            let interval = setInterval(() => {
                if (progress < 90) {
                    progress += 10;
                    loadingInner.style.width = progress + '%';
                }
            }, 300);

            fetch("/calculate", {
                method: "POST",
                body: formData
            }).then(response => response.json())
            .then(data => {
                clearInterval(interval);
                loadingInner.style.width = '100%';
                resultDiv.textContent = data.result;
                setTimeout(() => { loadingBar.style.display = 'none'; }, 500);
            }).catch(err => {
                clearInterval(interval);
                loadingInner.style.width = '0%';
                resultDiv.textContent = "Error: " + err;
                loadingBar.style.display = 'none';
            });
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(TEMPLATE)

@app.route("/calculate", methods=["POST"])
def calculate():
    file = request.files.get("file")
    material = request.form.get("material", "PLA")
    if not file:
        return jsonify({"result": "No file uploaded"})

    ext = file.filename.split(".")[-1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return jsonify({"result": f"Unsupported file type: {ext}"})

    try:
        if ext == "3mf":
            import networkx  # required by trimesh for 3MF
            import lxml
            mesh = trimesh.load(file, file_type="3mf")
        else:
            mesh = trimesh.load(file, file_type=ext)

        volume_mm3 = mesh.volume
        mass_g = volume_mm3 * FILAMENT_DENSITY
        cost = round(mass_g * COST_PER_GRAM.get(material, 0.12), 2)

        return jsonify({"result": f"${cost} ({mass_g:.2f}g)"})
    except Exception as e:
        return jsonify({"result": f"Error processing file: {e}"})

if __name__ == "__main__":
    app.run(debug=True)


