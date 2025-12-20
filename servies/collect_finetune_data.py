import os
import cv2
import mediapipe as mp
import pickle
import numpy as np
def main():
    # --- CONFIGURATION ---
    OUTPUT_FILE = './model/my_real_data.pickle'
    SAMPLES_PER_CLASS = 200

    # Setup MediaPipe
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    hands = mp_hands.Hands(static_image_mode=False, min_detection_confidence=0.3)

    # Load existing personal data if it exists, otherwise create new
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'rb') as f:
            data_dict = pickle.load(f)
            data = data_dict['data']
            labels = data_dict['labels']
        print(f"📂 Loaded existing personal data: {len(data)} samples")
    else:
        data = []
        labels = []
        print("✨ Creating new personal data file.")

    cap = cv2.VideoCapture(0)

    print("\n---------------------------------------")
    target_class = input("Which letter do you want to fix? (e.g. A): ").upper()
    print(f"Ready to record '{target_class}'. Press 'Q' when ready!")
    print("---------------------------------------")

    while True:
        ret, frame = cap.read()
        if not ret: break

        # Mirror the frame (Make sure this matches your inference script!)
        frame = cv2.flip(frame, 1)

        cv2.putText(frame, f"Target: {target_class}", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 3, cv2.LINE_AA)
        cv2.putText(frame, "Press 'Q' to Start Recording", (10, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow('Collector', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # --- START RECORDING ---
    counter = 0
    while counter < SAMPLES_PER_CLASS:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)  # Mirror again to match

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]

            # EXTRACT FEATURES
            data_aux = []
            x_ = []
            y_ = []

            for i in range(len(hand_landmarks.landmark)):
                x = hand_landmarks.landmark[i].x
                y = hand_landmarks.landmark[i].y
                x_.append(x)
                y_.append(y)

            for i in range(len(hand_landmarks.landmark)):
                x = hand_landmarks.landmark[i].x
                y = hand_landmarks.landmark[i].y
                data_aux.append(x - min(x_))
                data_aux.append(y - min(y_))

            # Add to list
            data.append(data_aux)
            labels.append(target_class)

            counter += 1

            # Visual Feedback
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        # Progress Bar
        cv2.rectangle(frame, (0, 0), (counter * 3, 20), (0, 255, 0), -1)
        cv2.imshow('Collector', frame)
        cv2.waitKey(1)

    # Save Updated Data
    with open(OUTPUT_FILE, 'wb') as f:
        pickle.dump({'data': data, 'labels': labels}, f)

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n✅ Successfully saved {SAMPLES_PER_CLASS} samples for '{target_class}'!")
    print(f"Total personal samples: {len(data)}")
if __name__ == "__main__":
    main()