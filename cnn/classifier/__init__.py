import torch
import torch.nn as nn
from torchvision import datasets, models, transforms
from PIL import Image

from . import consts


class Classifier:
    classes: list = []
    model: nn.Module = None
    device: torch.device = None
    transform = consts.DEFAULT_TRANSFORM
    def __init_function(self):
        # 設定 torch 的 device
        if not torch.cuda.is_available():
            print("Warning: Cuda isn't available now.")
        self.device = torch.device("cuda:1" if torch.cuda.is_available() else "cpu")
        # 載入模型
        self.model = models.efficientnet_b0(weights=None) # weights=None 因為我們要載入自己的權重
        num_features = self.model.classifier[1].in_features
        self.model.classifier = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(num_features, len(self.classes))
        )
    def __init__(self, model_path: str, dataset_path: str):
        dataset = datasets.ImageFolder(root=dataset_path)
        self.classes = dataset.classes
        self.__init_function()
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device) # 將模型移至 device
        self.model.eval()     # 設定為評估模式
    
    def predict(self, image_path: str, top_k: int = 3):
        image = Image.open(image_path).convert('RGB')
        image = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(image)
            probs = torch.softmax(outputs, dim=1)

            top_probs, top_indices = torch.topk(probs, k=top_k, dim=1)

        results = []
        for prob, idx in zip(top_probs[0], top_indices[0]):
            results.append({
                "class": self.classes[idx.item()],
                "probability": prob.item()
            })

        return results


