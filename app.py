from flask import Flask, request, render_template_string
import trimesh
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>3D Print Quote Calculator</title>
<style>
body { font-family: Arial, sans-serif; padding: 20px; }
h1 { color: #333; }
form { margin-bottom: 20px; }
input[type=file] {
    display: block;
    margin-bottom: 10px;
    border: 2px dotted green;
    padding: 20px;
    width: 300px;
}
button {
    background-color: #007BFF;
    color: white;
    padding: 10px 20px;
    border: none;
    cursor: pointer;
    font-size: 16px;
    border-radius: 5px;
}
button:hover { background-color: #0056b3; }
.result { margin-top: 20px; }
</style>
</head>
<body>
<h1>3D Print Quote Calculator</h1>
<form method="POST" enctype="multipart/form-data">
    <input type="file" name="file" accept=".stl,.obj,.3mf" required>
    <button type="submit">Get Quote</button>
</form>
{% if result %}
<div class="result">
    <strong>Volume:</strong> {{ result.volume }} mm³<br>
    <strong>Surface Area:</strong> {{ result.area }} mm²<br>
    <strong>Estimated Cost:</strong> ${{ result.cost }}
</div>
{% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        file = request.files.get("file")
        if file:
            filename = file.filename.lower()
            ext = os.path.splitext(filename)[1]
            file_type = None
            if ext == ".stl":
                file_type = "stl"
            elif ext == ".obj":
                file_type = "obj"
            elif ext == ".3mf":
                file_type = "3mf"
            else:
                return "Unsupported file type", 400

            try:
                mesh = trimesh.load(file, file_type=file_type)
                # If Scene, merge into single mesh
                if isinstance(mesh, trimesh.Scene):
                    mesh = mesh.dump(concatenate=True)

                volume = mesh.volume if hasattr(mesh, 'volume') else 0
                area = mesh.area if hasattr(mesh, 'area') else 0

                # Simple cost formula: $0.05 per cubic mm
                cost = round(volume * 0.05, 2)

                result = {
                    "volume": round(volume, 2),
                    "area": round(area, 2),
                    "cost": cost
                }
            except Exception as e:
                return f"Error processing file: {str(e)}", 500

    return render_template_string(HTML_TEMPLATE, result=result)

if __name__ == "__main__":
    app.run(debug=True)
