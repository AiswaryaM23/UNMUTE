import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from collections import Counter
def main():
    print("Running model training...")
    # 1. Load the data
    print("📂 Loading data.pickle...")
    data_dict = pickle.load(open('./model/data.pickle', 'rb'))

    raw_data = data_dict['data']
    raw_labels = data_dict['labels']

    # --- FIX: FILTER BAD DATA ---
    # We verify that all rows have the same length.
    # We keep only the rows that match the "standard" length (likely 42 or 84).

    # Check lengths of all rows
    lengths = [len(x) for x in raw_data]
    most_common_len = Counter(lengths).most_common(1)[0][0]

    print(f"🔍 Data Analysis: Most common sample length is {most_common_len}")
    print(f"   (Found {len(raw_data)} total samples)")

    clean_data = []
    clean_labels = []

    dropped_count = 0

    for i, row in enumerate(raw_data):
        if len(row) == most_common_len:
            clean_data.append(row)
            clean_labels.append(raw_labels[i])
        else:
            dropped_count += 1

    print(f"🧹 Cleaned Data: Kept {len(clean_data)} samples, Dropped {dropped_count} bad samples.")

    # Convert to numpy array (Now it will work!)
    data = np.array(clean_data)
    labels = np.array(clean_labels)

    # 2. Split into Training (80%) and Testing (20%) sets
    x_train, x_test, y_train, y_test = train_test_split(
        data, labels, test_size=0.2, shuffle=True, stratify=labels
    )

    # 3. Initialize and Train the Random Forest
    print("🧠 Training the Random Forest model...")
    model = RandomForestClassifier(n_estimators=100, n_jobs=-1)
    model.fit(x_train, y_train)

    # 4. Test Accuracy
    y_predict = model.predict(x_test)
    score = accuracy_score(y_predict, y_test)

    print(f"🎉 Model Accuracy: {score * 100:.2f}%")

    # 5. Save the trained model
    f = open('./model/model.p', 'wb')
    pickle.dump({'model': model}, f)
    f.close()
    print("✅ Model saved as 'model.p'. You are ready for the webcam!")
if __name__ == "__main__":
    main()