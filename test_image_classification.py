from cnn.classifier import Classifier
classifier = Classifier("saved_models/17classes/best_model.pth", "dataset")
result = classifier.predict("dataset/米露尾蟲/IMG_2623.JPG")
print(result)