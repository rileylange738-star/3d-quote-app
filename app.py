from flask import Flask, request, render_template_string
import trimesh
import os

app = Flask(__name__)

# Price per gram based on material
MATERIAL_PRICES = {
    "PLA": 0.12,
    "PETG": 0.12,
    "TPU": 0.20
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>3D Print Quote</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        input, select, button { margin: 10px 0; padding: 8px; width: 300px; }
        .result { margin-top: 20px; font-weight: bold; }
    </style>
</head>
<body>
    <h1>3D Print Quote Calculator</h1>
    <form method="post" enctype="multipart/form-data">
        <label>Upload 3D Model (STL/OBJ/3MF):</label><br>
        <input type="file" name="model" required><br>

        <label>Select Material:</label><br>
        <select name="material" required>
            <option value="PLA">PLA ($0.12/g)</option>
            <option value="PETG">PETG ($0.12/g)</option>
            <option value="TPU">TPU ($0.20/g)</option>
        </select><br>

        <button type="submit">Calculate</button>
    </form>
    {% if cost is not none %}
        <div class="result">
            Estimated Cost: ${{ "%.2f"|format(cost) }}
        </div>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def calculate_cost():
    cost = None
    if request.method == "POST":
        uploaded_file = request.files.get("model")
        material = request.form.get("material")
        price_per_gram = MATERIAL_PRICES.get(material, 0.20)  # fallback to 0.20

        if uploaded_file:
            # Save the uploaded file temporarily
            os.makedirs("temp_model", exist_ok=True)
            filepath = os.path.join("temp_model", uploaded_file.filename)
            uploaded_file.save(filepath)

            try:
                # Load model and compute volume in mm^3
                mesh = trimesh.load(filepath)
                volume_mm3 = mesh.volume if hasattr(mesh, "volume") else 0

                # Approximate weight in grams (PLA/PETG/TPU density ~1.24 g/cm³)
                density = 1.24  # g/cm³
                weight_grams = volume_mm3 / 1000 * density  # convert mm³ to cm³
                cost = weight_grams * price_per_gram

            except Exception as e:
                cost = 0
                print("Error loading model:", e)
            finally:
                os.remove(filepath)

    return render_template_string(HTML_TEMPLATE, cost=cost)

if __name__ == "__main__":
    app.run(debug=True)
