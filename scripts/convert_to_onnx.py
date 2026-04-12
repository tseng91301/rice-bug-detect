import torch
import torch.nn as nn
from torchvision import models
import os

def convert():
    model_path = "saved_models/17classes/best_model.pth"
    output_path = "model_repository/rice_bug_model/1/model.onnx"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 必須與訓練時的架構一致
    model = models.efficientnet_b0(weights=None)
    num_features = model.classifier[1].in_features
    # 這裡硬編碼 17 classes，因為我們知道是 17classes 資料夾
    model.classifier = nn.Sequential(
        nn.Dropout(0.5),
        nn.Linear(num_features, 17)
    )

    # 載入權重
    device = torch.device("cpu")
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    # 建立 dummy input (batch_size, channels, height, width)
    dummy_input = torch.randn(1, 3, 224, 224)

    # 匯出 ONNX
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=17, # 使用較新的 opset
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
    )
    print(f"Model converted successfully and saved to {output_path}")

if __name__ == "__main__":
    convert()
