import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

model = load_model("ml/cnn_model.h5")

classes = [
    "Tomato Healthy",
    "Tomato Blight",
    "Potato Early Blight",
    "Potato Late Blight"
]

def predict_disease(img_path):

    img = image.load_img(img_path, target_size=(128,128))
    img = image.img_to_array(img)
    img = img/255
    img = np.expand_dims(img, axis=0)

    pred = model.predict(img)

    return classes[np.argmax(pred)]