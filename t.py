from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from PIL import Image
from flask import render_template
import tritonclient.http as httpclient
from tritonclient.utils import InferenceServerException
# from torch.utils.data import DataLoader
# from torchvision.datasets import ImageFolder
# Initialize Flask app
app = Flask(__name__)
# Enable CORS for all routes
CORS(app)

# --- Triton Server Configuration ---
# **IMPORTANT**: Replace these with your actual Triton server details.
TRITON_SERVER_URL = "trition.toolmen.bime.ntu.edu.tw"  # Host and port
MODEL_NAME = "rice_bug_model"  # The name of your model in Triton
MODEL_VERSION = "1"  # The version of your model

# Define the input and output names for your model from the model's config.pbtxt
INPUT_NAME = "input_image"
OUTPUT_NAME = "logits"

# Initialize Triton Client
# try:
#     triton_client = httpclient.InferenceServerClient(url=TRITON_SERVER_URL)
# except Exception as e:
#     print(f"Could not create Triton client: {e}")
#     triton_client = None
@app.route('/')
def index():
    return render_template('standalone_frontend.html')

@app.route('/predict', methods=['POST'])
def predict():
    triton_client = httpclient.InferenceServerClient(url=TRITON_SERVER_URL)
    if not triton_client:
        return jsonify({'error': 'Triton client is not initialized. Check server URL.'}), 503

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        
        
        img = Image.open(file.stream).convert('RGB')
        # print(np.shape(img))
        
        # **NOTE**: Adjust the size and preprocessing to match your model's requirements
        img = img.resize((224, 224))
        
        img_array = np.array(img).astype(np.float32)
        # print(np.shape(img_array))
        # Normalize if required by your model
        # img_array = img_array / 255.0
        
        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        # print(np.shape(img_array))
        img_array = np.transpose(img_array, (0, 3, 1, 2)).copy()/255
        # print(img_array)
        # --- 2. Call Triton Server using tritonclient ---
        
        # Set up the input tensor
        infer_input = httpclient.InferInput(INPUT_NAME, img_array.shape, "FP32")
        infer_input.set_data_from_numpy(img_array, binary_data=False)

        # Set up the output tensor
        infer_output = httpclient.InferRequestedOutput(OUTPUT_NAME, binary_data=False)

        # Perform inference
        results = triton_client.infer(
            model_name=MODEL_NAME,
            model_version=MODEL_VERSION,
            inputs=[infer_input],
            outputs=[infer_output]
        )
        # --- 3. Process Response ---
        prediction_output = results.as_numpy(OUTPUT_NAME)
        # print(prediction_output)
        predicted_class_index = np.argmax(prediction_output[0])
        # print(predicted_class_index)
        # confidence = float(np.max(prediction_output[0]))
        class_name = ['潰瘍病','煤煙病','油斑病','薊馬','潛葉蛾','蚜蟲','健康植株']
        
        # **NOTE**: You would typically have a list of class names to map the index to a label
        # class_names = ["ClassA", "ClassB", ...]
        # predicted_class_label = class_names[predicted_class_index]
        predicted_class_label = f"Class_{predicted_class_index}"

        return jsonify({
            'class': class_name[predicted_class_index],
            # 'confidence': confidence
        })

    except InferenceServerException as e:
        print(f"Inference failed: {e}")
        return jsonify({'error': f'Inference failed: {e}'}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)