import pickle
import cv2
import mediapipe as mp
import numpy as np
import time
import re
from spellchecker import SpellChecker


# ================= UTILS =================
def collapse_repeats(text):
    # YESYESYES -> YES
    return re.sub(r'\b(\w+)( \1\b)+', r'\1', text)


def normalize_letters(word):
    # JJJJ -> J, HEEELLO -> HELLO
    return re.sub(r'(.)\1{2,}', r'\1', word)


def wrap_text(text, max_len=40):
    words = text.split()
    lines, line = [], ""
    for w in words:
        if len(line) + len(w) <= max_len:
            line += w + " "
        else:
            lines.append(line)
            line = w + " "
    lines.append(line)
    return lines


# ================= MAIN =================
def main():
    # -------- Load model --------
    model_dict = pickle.load(open("./model/model.p", "rb"))
    model = model_dict["model"]

    spell = SpellChecker()

    # -------- MediaPipe (FIXED) --------
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    # -------- Camera --------
    cap = cv2.VideoCapture(0)

    # -------- Sentence state --------
    sentence = ""
    current_token = ""

    last_label = None
    stable_count = 0
    STABLE_THRESHOLD = 12

    last_seen_time = time.time()
    WORD_GAP = 1.2
    SENTENCE_GAP = 3.0

    print("📷 Sentence inference running (Q to quit)")

    # -------- Fullscreen --------
    cv2.namedWindow("Sentence Inference", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(
        "Sentence Inference",
        cv2.WND_PROP_FULLSCREEN,
        cv2.WINDOW_FULLSCREEN
    )

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        label = None
        hand_present = False

        # -------- Hand detection --------
        if results.multi_hand_landmarks:
            hand_present = True
            last_seen_time = time.time()

            hand = results.multi_hand_landmarks[0]
            mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

            x_, y_, data = [], [], []
            for lm in hand.landmark:
                x_.append(lm.x)
                y_.append(lm.y)

            for lm in hand.landmark:
                data.append(lm.x - min(x_))
                data.append(lm.y - min(y_))

            try:
                label = model.predict([np.array(data)])[0]
            except:
                label = None

        # -------- Stability filter --------
        if label == last_label and label is not None:
            stable_count += 1
        else:
            stable_count = 0

        if stable_count == STABLE_THRESHOLD:
            # If fine-tuned WORD label (HELLO, YES, ILOVEYOU)
            if len(label) > 1:
                sentence += label.lower() + " "
            else:
                if not current_token.endswith(label.lower()):
                    current_token += label.lower()
            stable_count = 0

        last_label = label

        # -------- Word break --------
        if not hand_present and time.time() - last_seen_time > WORD_GAP:
            if current_token:
                fixed = normalize_letters(current_token)
                corrected = spell.correction(fixed) or fixed
                sentence += corrected + " "
                current_token = ""
            last_seen_time = time.time()

        # -------- Sentence end --------
        if not hand_present and time.time() - last_seen_time > SENTENCE_GAP:
            sentence = collapse_repeats(sentence.strip())
            if sentence and not sentence.endswith((".", "!", "?")):
                sentence += ". "
            last_seen_time = time.time()

        # -------- UI --------
        panel_w = 500
        canvas = np.zeros((h, w + panel_w, 3), dtype=np.uint8)
        canvas[:, :w] = frame
        cv2.rectangle(canvas, (w, 0), (w + panel_w, h), (30, 30, 30), -1)

        cv2.putText(
            canvas, "Sentence Output",
            (w + 20, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2
        )

        y = 80
        display = sentence + current_token
        for line in wrap_text(display):
            cv2.putText(
                canvas, line,
                (w + 20, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2
            )
            y += 35

        if label:
            cv2.putText(
                canvas, f"Detected: {label}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
            )

        cv2.imshow("Sentence Inference", canvas)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
