import os
import uuid
import numpy as np
import logging
import cv2
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.optimizers import Adam

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-2024')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'dcm'}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATHS = {
    "normal_tc": os.path.join(BASE_DIR, "classifier_models", "final_normal_tc.keras"),
    "early_vs_late": os.path.join(BASE_DIR, "classifier_models", "final_early_vs_late_model.keras")
}

models = {}

def safe_load_model(name, path):
    try:
        logger.info(f"Loading {name} model from: {path}")
        if not os.path.exists(path):
            logger.error(f"Model file not found: {path}")
            return None
            
        model = load_model(path, compile=False)
        model.compile(
            optimizer=Adam(learning_rate=0.0001),
            loss="binary_crossentropy",
            metrics=["accuracy"]
        )
        logger.info(f"{name} model loaded successfully")
        return model
    except Exception as e:
        logger.error(f"Error loading {name} model: {e}")
        return None

def initialize_models():
    for key, path in MODEL_PATHS.items():
        model = safe_load_model(key, path)
        if model is not None:
            models[key] = model
            
    if not models:
        logger.critical("No models could be loaded. Exiting...")
        exit(1)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def preprocess_image(image_path, target_size=(224, 224)):
    try:
        # معالجة ملفات DICOM
        if image_path.lower().endswith('.dcm'):
            try:
                import pydicom
                dicom_data = pydicom.dcmread(image_path)
                img = dicom_data.pixel_array
                
                # تحويل إلى تدرجات الرمادي إذا لزم الأمر
                if len(img.shape) == 2:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
                elif len(img.shape) == 3 and img.shape[2] == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
                    
                img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            except ImportError:
                logger.error("pydicom not installed. Cannot process DICOM files.")
                raise ValueError("DICOM processing requires pydicom library")
        else:
            # معالجة الصور العادية
            img = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Unable to read image file")
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
        # تغيير الحجم والتطبيع
        img = cv2.resize(img, target_size)
        img = img.astype("float32") / 255.0
        img = np.expand_dims(img, axis=0)
        return img
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "models_loaded": len(models) > 0,
        "model_names": list(models.keys())
    })

@app.route("/static/uploads/<filename>")
def serve_uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/api/upload", methods=["POST"])
def upload_file():
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
            
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "error": "Empty filename"}), 400
            
        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "Invalid file type"}), 400
            
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit(".", 1)[1].lower()
        unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex}.{file_extension}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)
        
        return jsonify({
            "success": True,
            "file_id": unique_filename,
            "filename": original_filename,
            "file_size": os.path.getsize(filepath),
            "image_data": f"/static/uploads/{unique_filename}"
        })
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({"success": False, "error": "Upload failed"}), 500

@app.route("/api/analyze", methods=["POST"])
def analyze_image():
    try:
        if not models:
            return jsonify({"success": False, "error": "No models loaded"}), 503
            
        data = request.get_json()
        if not data or "file_id" not in data:
            return jsonify({"success": False, "error": "No file ID provided"}), 400
            
        file_id = data["file_id"]
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
        
        if not os.path.exists(filepath):
            return jsonify({"success": False, "error": "File not found"}), 404
            
        processed = preprocess_image(filepath)
        result = {}
        
        if "normal_tc" in models:
            pred = models["normal_tc"].predict(processed, verbose=0)
            tc_prob = float(pred[0][0]) 
            normal_prob = 1 - tc_prob    
            
            is_normal = normal_prob > 0.5
            result["normal"] = bool(is_normal)
            result["confidence"] = normal_prob if is_normal else tc_prob
            

            if not is_normal and "early_vs_late" in models:
                stage_pred = models["early_vs_late"].predict(processed, verbose=0)
                late_prob = float(stage_pred[0][0])
                early_prob = 1 - late_prob
                
                is_late = late_prob > 0.5
                result["stage"] = "late" if is_late else "early"
                result["stage_confidence"] = late_prob if is_late else early_prob
        
        return jsonify({
            "success": True, 
            "result": result
        })
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return jsonify({"success": False, "error": "Analysis failed"}), 500

@app.errorhandler(413)
def handle_large_file(error):
    return jsonify({"success": False, "error": "File too large"}), 413

@app.errorhandler(404)
def handle_not_found(error):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404

@app.errorhandler(500)
def handle_internal_error(error):
    return jsonify({"success": False, "error": "Internal server error"}), 500

if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    initialize_models()
    logger.info("Models initialized successfully")
    app.run(debug=True)