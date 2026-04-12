import numpy as np
import tritonclient.http as httpclient
from PIL import Image
from .classes import CLASS_NAMES

TRITON_SERVER_URL = "trition.toolmen.bime.ntu.edu.tw"
MODEL_NAME = "rice_bug_model"
MODEL_VERSION = "1"
INPUT_NAME = "input"
OUTPUT_NAME = "output"

def preprocess(image, target_size=(224, 224)):
    # Resize
    image = image.resize(target_size)
    # Convert to numpy array and normalize [0, 1]
    img_array = np.array(image).astype(np.float32) / 255.0
    # Add batch dimension: (1, H, W, C)
    img_array = np.expand_dims(img_array, axis=0)
    # Transpose to (1, C, H, W)
    img_array = np.transpose(img_array, (0, 3, 1, 2)).copy()
    return img_array

def infer(image):
    try:
        triton_client = httpclient.InferenceServerClient(url=TRITON_SERVER_URL)
        
        # Ensure RGB and preprocess image
        if image.mode != 'RGB':
            image = image.convert('RGB')
        input_data = preprocess(image)

        # Set up the input tensor
        infer_input = httpclient.InferInput(INPUT_NAME, input_data.shape, "FP32")
        infer_input.set_data_from_numpy(input_data, binary_data=False)

        # Set up the output tensor
        infer_output = httpclient.InferRequestedOutput(OUTPUT_NAME, binary_data=False)

        # Perform inference
        response = triton_client.infer(
            model_name=MODEL_NAME,
            model_version=MODEL_VERSION,
            inputs=[infer_input],
            outputs=[infer_output]
        )
        
        logits = response.as_numpy(OUTPUT_NAME)
        
        # Softmax to get probabilities
        exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
        probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
        probs = probs[0]

        # Get Top 3 predictions to keep DB compatibility
        # If there are fewer than 3 classes, it will handle it correctly
        num_classes = len(CLASS_NAMES)
        k = min(3, num_classes)
        top_k_indices = np.argsort(probs)[-k:][::-1]
        
        results = []
        for idx in top_k_indices:
            results.append({
                "class": CLASS_NAMES[idx],
                "probability": float(probs[idx])
            })
            
        # If fewer than 3 results, pad with dummy values for DB compatibility
        while len(results) < 3:
            results.append({
                "class": "N/A",
                "probability": 0.0
            })
            
        return results

    except Exception as e:
        print(f"API Inference error: {e}")
        return None
