import pickle
import cv2
import mediapipe as mp
import numpy as np
import time
import re
from spellchecker import SpellChecker

# ================= NORMALIZE REPEATED LETTERS =================
def normalize_word(word):
    # baaaaad -> bad, hellooo -> hello
    return re.sub(r'(.)\1{2,}', r'\1', word)

# ================= REMOVE DUPLICATE WORDS =================
def clean_sentence(text):
    words = text.split()
    clean = []
    for w in words:
        if not clean or w != clean[-1]:
            clean.append(w)
    sentence = " ".join(clean)
    return sentence.capitalize()

# ================= TEXT WRAPPING =================
def wrap_text(text, max_len):
    words = text.split(" ")
    lines, line = [], ""
    for word in words:
        if len(line) + len(word) <= max_len:
            line += word + " "
        else:
            lines.append(line)
            line = word + " "
    lines.append(line)
    return lines

def main():
    # ================= LOAD MODEL =================
    model_dict = pickle.load(open('./model/model.p', 'rb'))
    model = model_dict['model']

    # ================= AUTOCORRECT =================
    spell = SpellChecker(distance=1)

    # ================= MEDIAPIPE =================
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
    STABLE_THRESHOLD = 10

    last_hand_time = time.time()
    SPACE_TIMEOUT = 1.2      # word break
    SENTENCE_TIMEOUT = 3.0   # sentence end

    last_word = None
    last_word_time = 0
    WORD_COOLDOWN = 1.5      # seconds

    print("📷 Sentence inference with autocorrect running | Press Q to quit")

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

            data_aux, x_, y_ = [], [], []

            for lm in hand_landmarks.landmark:
                x_.append(lm.x)
                y_.append(lm.y)

            for lm in hand_landmarks.landmark:
                data_aux.append(lm.x - min(x_))
                data_aux.append(lm.y - min(y_))

            try:
                predicted_char = model.predict([np.asarray(data_aux)])[0]
            except:
                predicted_char = None

        # ================= LETTER STABILITY =================
        if predicted_char == last_char and predicted_char is not None:
            stable_count += 1
        else:
            stable_count = 0

        if stable_count >= STABLE_THRESHOLD:
            now = time.time()
            label = predicted_char.lower() if predicted_char else ""
            # If the predicted label is a word (your fine-tuned labels)
            if len(label) > 1:
                if label != last_word or now - last_word_time > WORD_COOLDOWN:
                    # Autocorrect word
                    normalized = normalize_word(label)
                    corrected = spell.correction(normalized)
                    sentence += (corrected if corrected else normalized) + " "
                    last_word = label
                    last_word_time = now
                    current_word = ""
            # If single letter
            elif label:
                current_word += label

            stable_count = 0

        last_char = predicted_char

        # ================= WORD BREAK =================
        if not hand_detected and time.time() - last_hand_time > SPACE_TIMEOUT:
            if current_word:
                normalized = normalize_word(current_word)
                corrected = spell.correction(normalized)
                sentence += (corrected if corrected else normalized) + " "
                current_word = ""
            last_hand_time = time.time()

        # ================= SENTENCE END + PUNCTUATION =================
        if not hand_detected and time.time() - last_hand_time > SENTENCE_TIMEOUT:
            if sentence and not sentence.strip().endswith(('.', '!', '?')):
                sentence = sentence.strip() + ". "
            last_hand_time = time.time()

        # ================= UI =================
        panel_width = 450
        combined = np.zeros((H, W + panel_width, 3), dtype=np.uint8)
        combined[:, :W] = frame

        cv2.rectangle(combined, (W, 0), (W + panel_width, H), (25, 25, 25), -1)

        cv2.putText(
            combined, "Sentence Output:",
            (W + 20, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2
        )

        display_text = clean_sentence(sentence + current_word)
        y = 80
        for line in wrap_text(display_text, 35):
            cv2.putText(
                combined, line,
                (W + 20, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
            )
            y += 30

        if predicted_char:
            cv2.putText(
                combined, f"Letter/Word: {predicted_char}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
            )

        cv2.imshow("Sign Language Sentence Detector", combined)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
