import pickle
import cv2
import mediapipe as mp
import numpy as np
def main():
    # 1. Load the trained model
    model_dict = pickle.load(open('./model/model.p', 'rb'))
    model = model_dict['model']

    # 2. Setup Camera & MediaPipe
    cap = cv2.VideoCapture(0)

    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

    # min_detection_confidence=0.5 makes it stricter (less noise)
    hands = mp_hands.Hands(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)

    print("📷 Camera starting... Press 'Q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        H, W, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame for hands
        results = hands.process(frame_rgb)

        data_aux = []
        x_ = []
        y_ = []

        if results.multi_hand_landmarks:
            # Only process the FIRST hand detected
            hand_landmarks = results.multi_hand_landmarks[0]

            # Draw the Skeleton
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )

            # Extract Coordinates (Same math as training)
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

            # Prediction
            # We need to reshape the data to look like a single sample
            try:
                prediction = model.predict([np.asarray(data_aux)])
                predicted_char = prediction[0]

                # Display Result
                cv2.rectangle(frame, (0, 0), (160, 70), (0, 0, 0), -1)
                cv2.putText(frame, predicted_char, (10, 50), cv2.FONT_HERSHEY_SIMPLEX,
                            1.3, (0, 255, 0), 3, cv2.LINE_AA)
            except Exception as e:
                # Sometimes data_aux might be the wrong length if MediaPipe glitches
                pass

        cv2.imshow('Sign Language Detector', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
if __name__ == "__main__":
    main()