import pickle
import cv2
import mediapipe as mp
import numpy as np
import time

def main():
    # ================= LOAD MODEL =================
    model_dict = pickle.load(open('./model/model.p', 'rb'))
    model = model_dict['model']

    # ================= MEDIAPIPE SETUP =================
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    mp_styles = mp.solutions.drawing_styles

    hands = mp_hands.Hands(
        static_image_mode=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    # ================= CAMERA =================
    cap = cv2.VideoCapture(0)

    # ================= SENTENCE STATE =================
    sentence = ""
    current_word = ""

    last_char = None
    stable_count = 0
    STABLE_THRESHOLD = 10  # frames

    last_hand_time = time.time()
    SPACE_TIMEOUT = 1.2  # seconds without hand = space

    print("📷 Sentence Inference Started | Press 'Q' to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        H, W, _ = frame.shape

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        predicted_char = None
        hand_detected = False

        # ================= HAND DETECTION =================
        if results.multi_hand_landmarks:
            hand_detected = True
            last_hand_time = time.time()

            hand_landmarks = results.multi_hand_landmarks[0]
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_styles.get_default_hand_landmarks_style(),
                mp_styles.get_default_hand_connections_style()
            )

            data_aux = []
            x_ = []
            y_ = []

            for lm in hand_landmarks.landmark:
                x_.append(lm.x)
                y_.append(lm.y)

            for lm in hand_landmarks.landmark:
                data_aux.append(lm.x - min(x_))
                data_aux.append(lm.y - min(y_))

            try:
                prediction = model.predict([np.asarray(data_aux)])
                predicted_char = prediction[0]
            except:
                predicted_char = None

        # ================= LETTER STABILITY LOGIC =================
        if predicted_char == last_char and predicted_char is not None:
            stable_count += 1
        else:
            stable_count = 0

        if stable_count == STABLE_THRESHOLD:
            # Avoid repeated same letter spam
            if len(current_word) == 0 or current_word[-1] != predicted_char:
                current_word += predicted_char
            stable_count = 0

        last_char = predicted_char

        # ================= SPACE DETECTION =================
        if not hand_detected:
            if time.time() - last_hand_time > SPACE_TIMEOUT:
                if current_word != "":
                    sentence += current_word + " "
                    current_word = ""
                last_hand_time = time.time()

        # ================= UI DISPLAY =================
        panel_width = 450
        combined = np.zeros((H, W + panel_width, 3), dtype=np.uint8)

        # Left: camera
        combined[:, :W] = frame

        # Right: text panel
        cv2.rectangle(
            combined,
            (W, 0),
            (W + panel_width, H),
            (30, 30, 30),
            -1
        )

        cv2.putText(
            combined,
            "Sentence Output:",
            (W + 20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        display_text = sentence + current_word

        y0 = 80
        for i, line in enumerate(wrap_text(display_text, 35)):
            cv2.putText(
                combined,
                line,
                (W + 20, y0 + i * 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

        # Show predicted letter
        if predicted_char:
            cv2.putText(
                combined,
                f"Letter: {predicted_char}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

        cv2.imshow("Sign Language Sentence Detector", combined)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


def wrap_text(text, max_len):
    words = text.split(" ")
    lines = []
    line = ""
    for word in words:
        if len(line) + len(word) <= max_len:
            line += word + " "
        else:
            lines.append(line)
            line = word + " "
    lines.append(line)
    return lines


if __name__ == "__main__":
    main()
