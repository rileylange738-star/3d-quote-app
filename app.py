from flask import Flask, request, render_template_string
import trimesh
import io

app = Flask(__name__)

# Filament properties
FILAMENT_DENSITY = 1.25 / 1000  # g/mm³ (PLA example)
COST_PER_GRAM = 0.12

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
        .drop-zone {
            border: 2px dotted green;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            margin-bottom: 20px;
        }
        input[type=file] { display:none; }
        button {
            background-color: #007BFF;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover { background-color: #0056b3; }
        .result { font-size: 1.2em; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>3D Print Quote Generator</h1>
    <form method="POST" enctype="multipart/form-data">
        <label class="drop-zone" for="file">Drag and drop your STL, OBJ, or 3MF file here</label>
        <input type="file" id="file" name="file" required>
        <br>
        <button type="submit">Get Quote</button>
    </form>
    {% if result %}
        <div class="result">Estimated Cost: {{ result }}</div>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            return "No file uploaded", 400

        ext = file.filename.split(".")[-1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return f"Unsupported file type: {ext}", 400

        try:
            # Load 3D mesh
            if ext == "3mf":
                import networkx  # required by trimesh for 3MF
                import lxml
                mesh = trimesh.load(file, file_type="3mf")
            else:
                mesh = trimesh.load(file, file_type=ext)

            # Calculate volume in mm³
            volume_mm3 = mesh.volume
            mass_g = volume_mm3 * FILAMENT_DENSITY
            cost = round(mass_g * COST_PER_GRAM, 2)

            return render_template_string(TEMPLATE, result=f"${cost} ({mass_g:.2f}g)")
        except Exception as e:
            return f"Error processing file: {e}", 500

    return render_template_string(TEMPLATE)

if __name__ == "__main__":
    app.run(debug=True)
