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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Print Quote Generator</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }

        .container {
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: #333;
        }

        .drop-area {
            border: 2px dotted green;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            font-size: 18px;
            color: #555;
            margin-bottom: 25px;
            cursor: pointer;
            transition: background-color 0.2s;
        }

        .drop-area.dragover {
            background-color: #e0ffe0;
        }

        input[type="file"] {
            display: none;
        }

        label.button {
            display: inline-block;
            padding: 12px 25px;
            margin: 10px 0;
            font-size: 16px;
            font-weight: bold;
            color: white;
            background-color: #007BFF;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            text-align: center;
            transition: background-color 0.3s;
        }

        label.button:hover {
            background-color: #0056b3;
        }

        .result {
            margin-top: 30px;
            padding: 20px;
            background-color: #f1f8ff;
            border-radius: 8px;
            font-size: 18px;
            color: #333;
            text-align: center;
        }

        .flex-row {
            display: flex;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }

        .flex-row input {
            flex: 1;
            padding: 10px;
            font-size: 16px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>3D Print Quote Generator</h1>

        <form id="quoteForm" method="POST" enctype="multipart/form-data">
            <div class="drop-area" id="drop-area">
                Drag & Drop your STL, OBJ, or 3MF file here<br>or click to select
                <input type="file" id="fileElem" name="file" accept=".stl,.obj,.3mf">
            </div>

            <div class="flex-row">
                <input type="number" step="0.01" name="price_per_gram" placeholder="Price per gram ($)" required>
                <input type="number" step="0.01" name="price_per_mm3" placeholder="Price per mm³ ($)">
            </div>

            <button type="submit" class="button">Calculate Quote</button>
        </form>

        {% if quote %}
        <div class="result">
            <strong>Estimated Price:</strong> ${{ quote }}
        </div>
        {% endif %}
    </div>

    <script>
        const dropArea = document.getElementById("drop-area");
        const fileInput = document.getElementById("fileElem");

        dropArea.addEventListener("click", () => fileInput.click());

        dropArea.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropArea.classList.add("dragover");
        });

        dropArea.addEventListener("dragleave", () => {
            dropArea.classList.remove("dragover");
        });

        dropArea.addEventListener("drop", (e) => {
            e.preventDefault();
            dropArea.classList.remove("dragover");
            fileInput.files = e.dataTransfer.files;
        });
    </script>
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
