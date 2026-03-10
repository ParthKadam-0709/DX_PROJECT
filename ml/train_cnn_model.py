import tensorflow as tf
import pandas as pd
import os

from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras import layers, models

# -------------------------------
# Paths
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, "dataset.csv")

# -------------------------------
# Load CSV
# -------------------------------
df = pd.read_csv("C:\\Users\\parth\\Downloads\\plant dataset kaggle.zip")

print("Dataset Loaded")
print(df.head())

# -------------------------------
# Parameters
# -------------------------------
img_size = (224,224)
batch_size = 32

# -------------------------------
# Data Augmentation
# -------------------------------
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    validation_split=0.2
)

# -------------------------------
# Load Images from CSV
# -------------------------------
train = train_datagen.flow_from_dataframe(
    dataframe=df,
    x_col="image_path",
    y_col="label",
    target_size=img_size,
    batch_size=batch_size,
    class_mode="categorical",
    subset="training"
)

val = train_datagen.flow_from_dataframe(
    dataframe=df,
    x_col="image_path",
    y_col="label",
    target_size=img_size,
    batch_size=batch_size,
    class_mode="categorical",
    subset="validation"
)

print("Classes:", train.class_indices)

# -------------------------------
# MobileNetV2 Model
# -------------------------------
base_model = MobileNetV2(
    weights='imagenet',
    include_top=False,
    input_shape=(224,224,3)
)

base_model.trainable = False

model = models.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dense(128, activation='relu'),
    layers.Dropout(0.5),
    layers.Dense(train.num_classes, activation='softmax')
])

# -------------------------------
# Compile
# -------------------------------
model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

# -------------------------------
# Training
# -------------------------------
print("Starting training...")
model.fit(train, validation_data=val, epochs=20)

# -------------------------------
# Fine Tuning
# -------------------------------
base_model.trainable = True

for layer in base_model.layers[:-20]:
    layer.trainable = False

model.compile(
    optimizer=tf.keras.optimizers.Adam(1e-5),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

print("Fine tuning...")
model.fit(train, validation_data=val, epochs=10)

# -------------------------------
# Save Model
# -------------------------------
model.save("cnn_model.h5")

print("Model saved successfully")