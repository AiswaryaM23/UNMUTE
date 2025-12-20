import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from collections import Counter

def main():
    # 1. Load Original Kaggle Data
    print("📂 Loading  Dataset...")
    kaggle_dict = pickle.load(open('./model/data.pickle', 'rb'))
    k_data = kaggle_dict['data']
    k_labels = kaggle_dict['labels']

    # 2. Load Your New Real-World Data
    print("📂 Loading Your Personal Data...")
    try:
        my_dict = pickle.load(open('./model/my_real_data.pickle', 'rb'))
        m_data = my_dict['data']
        m_labels = my_dict['labels']
        print(f"   Found {len(m_data)} personal samples.")
    except FileNotFoundError:
        print("❌ No personal data found! Run 'collect_finetune_data.py' first.")
        exit()

    # 3. CLEAN UP (Filter bad data lengths from Kaggle data)
    # (Your personal data is likely clean, but Kaggle data had errors before)
    expected_len = 42 # 21 landmarks * 2 coords
    clean_k_data = []
    clean_k_labels = []

    for i, row in enumerate(k_data):
        if len(row) == expected_len:
            clean_k_data.append(row)
            clean_k_labels.append(k_labels[i])

    # 4. MERGE DATASETS
    # We combine the lists
    final_data = clean_k_data + m_data
    final_labels = clean_k_labels + m_labels

    print(f"📊 Final Dataset Size: {len(final_data)} samples")
    print(f"   (Kaggle: {len(clean_k_data)} + Yours: {len(m_data)})")

    # 5. RETRAIN MODEL
    data = np.array(final_data)
    labels = np.array(final_labels)

    x_train, x_test, y_train, y_test = train_test_split(
        data, labels, test_size=0.2, shuffle=True, stratify=labels
    )

    print("🧠 Retraining Random Forest with Mixed Data...")
    # We increase estimators slightly to handle the variance
    model = RandomForestClassifier(n_estimators=150, n_jobs=-1)
    model.fit(x_train, y_train)

    # 6. Evaluate
    y_predict = model.predict(x_test)
    score = accuracy_score(y_predict, y_test)
    print(f"🎉 New Model Accuracy: {score * 100:.2f}%")

    # Save
    f = open('./model/model.p', 'wb')
    pickle.dump({'model': model}, f)
    f.close()
    print("✅ Saved new 'model.p'. Try running inference now!")

if __name__ =="__main__":
    main()