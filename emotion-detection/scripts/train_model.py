"""
Train a lightweight CNN on the FER2013 dataset.
Usage:
  1. Download FER2013: https://www.kaggle.com/datasets/msambare/fer2013
  2. Place fer2013.csv in the data/ folder
  3. Run: python train_model.py

Output: ../model/emotion_model.h5
"""

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks
import matplotlib.pyplot as plt

# ─── Config ─────────────────────────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/fer2013.csv")
MODEL_OUTPUT = os.path.join(os.path.dirname(__file__), "../model/emotion_model.h5")
EMOTIONS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
IMG_SIZE = 48
BATCH_SIZE = 64
EPOCHS = 50


# ─── Data Loading ────────────────────────────────────────────────────────────
def load_fer2013(path: str):
    df = pd.read_csv(path)
    X, y = [], []
    for _, row in df.iterrows():
        pixels = np.array(row["pixels"].split(), dtype="float32")
        img = pixels.reshape(IMG_SIZE, IMG_SIZE, 1) / 255.0
        X.append(img)
        y.append(int(row["emotion"]))
    return np.array(X), tf.keras.utils.to_categorical(np.array(y), num_classes=7)


# ─── Model Architecture ──────────────────────────────────────────────────────
def build_model():
    model = models.Sequential([
        # Block 1
        layers.Conv2D(32, (3, 3), padding="same", input_shape=(48, 48, 1)),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.Conv2D(32, (3, 3), padding="same"),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.MaxPooling2D(2, 2),
        layers.Dropout(0.25),

        # Block 2
        layers.Conv2D(64, (3, 3), padding="same"),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.Conv2D(64, (3, 3), padding="same"),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.MaxPooling2D(2, 2),
        layers.Dropout(0.25),

        # Block 3
        layers.Conv2D(128, (3, 3), padding="same"),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.Conv2D(128, (3, 3), padding="same"),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.MaxPooling2D(2, 2),
        layers.Dropout(0.25),

        # Dense head
        layers.Flatten(),
        layers.Dense(512),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.Dropout(0.5),
        layers.Dense(256),
        layers.Activation("relu"),
        layers.Dropout(0.3),
        layers.Dense(7, activation="softmax"),
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    print("Loading FER2013 dataset...")
    X, y = load_fer2013(DATA_PATH)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Train: {len(X_train)}, Val: {len(X_val)}")

    # Data augmentation
    datagen = tf.keras.preprocessing.image.ImageDataGenerator(
        rotation_range=10,
        width_shift_range=0.1,
        height_shift_range=0.1,
        horizontal_flip=True,
        zoom_range=0.1,
    )
    datagen.fit(X_train)

    model = build_model()
    model.summary()

    os.makedirs(os.path.dirname(MODEL_OUTPUT), exist_ok=True)

    cbs = [
        callbacks.ModelCheckpoint(MODEL_OUTPUT, save_best_only=True, monitor="val_accuracy"),
        callbacks.EarlyStopping(patience=10, restore_best_weights=True),
        callbacks.ReduceLROnPlateau(factor=0.5, patience=5, min_lr=1e-6),
    ]

    history = model.fit(
        datagen.flow(X_train, y_train, batch_size=BATCH_SIZE),
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        callbacks=cbs,
    )

    # Plot training curves
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(history.history["accuracy"], label="Train")
    axes[0].plot(history.history["val_accuracy"], label="Val")
    axes[0].set_title("Accuracy")
    axes[0].legend()

    axes[1].plot(history.history["loss"], label="Train")
    axes[1].plot(history.history["val_loss"], label="Val")
    axes[1].set_title("Loss")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(MODEL_OUTPUT), "training_curves.png"))
    print(f"\n✅ Model saved to {MODEL_OUTPUT}")


if __name__ == "__main__":
    main()
