import os
import pickle
import mediapipe as mp
import cv2
import matplotlib.pyplot as plt
def main():
    print("Running image process 1...")
    # --- CONFIGURATION ---
    # POINT THIS TO YOUR UNZIPPED KAGGLE FOLDER
    # Example: If your folder is named 'american_sign_language_letters'
    DATA_DIR = './asl_dataset'

    # MediaPipe Setup
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(static_image_mode=True, min_detection_confidence=0.3)

    data = []
    labels = []

    # Verify path exists
    if not os.path.exists(DATA_DIR):
        print(f"❌ Error: Folder '{DATA_DIR}' not found!")
        print("Please edit the DATA_DIR line to match your folder name.")
        exit()

    print(f"🚀 Starting to process images from: {DATA_DIR}")

    classes = os.listdir(DATA_DIR)
    for dir_ in classes:
        class_path = os.path.join(DATA_DIR, dir_)

        # Skip if it's not a folder
        if not os.path.isdir(class_path):
            continue

        print(f"   📂 Processing Class: {dir_}...")

        # Get all images in the folder
        img_files = os.listdir(class_path)

        # OPTIONAL: Limit to 500 images per class to save time
        # Remove [:500] if you want to use ALL images (slower but more accurate)
        for img_path in img_files[:500]:
            data_aux = []
            x_ = []
            y_ = []

            full_path = os.path.join(class_path, img_path)
            img = cv2.imread(full_path)
            if img is None: continue

            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            results = hands.process(img_rgb)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # 1. Collect all coordinates
                    for i in range(len(hand_landmarks.landmark)):
                        x = hand_landmarks.landmark[i].x
                        y = hand_landmarks.landmark[i].y
                        x_.append(x)
                        y_.append(y)

                    # 2. Normalize (Center the hand data)
                    # This makes the model work even if your hand is in a different corner of the screen
                    for i in range(len(hand_landmarks.landmark)):
                        x = hand_landmarks.landmark[i].x
                        y = hand_landmarks.landmark[i].y
                        data_aux.append(x - min(x_))
                        data_aux.append(y - min(y_))

                data.append(data_aux)
                labels.append(dir_)

    # Save the processed data
    f = open('./model/data.pickle', 'wb')
    pickle.dump({'data': data, 'labels': labels}, f)
    f.close()

    print("\n✅ Processing Complete!")
    print(f"📊 Saved {len(data)} samples into 'data.pickle'")

if __name__ == "__main__":
    main()