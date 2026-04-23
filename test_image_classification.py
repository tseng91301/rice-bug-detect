from cnn.classifier import Classifier
classifier = Classifier("saved_models/17classes/best_model.pth", "dataset")
result = classifier.predict("dataset_extend/外米綴蛾-幼蟲/2026-04-13_153101_91c73669-90ec-4d6b-9ea9-90e716235ec0.jpg")
print(result)