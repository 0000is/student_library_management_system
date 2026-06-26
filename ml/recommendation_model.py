import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    roc_auc_score
)

# ================= DATASET =================

np.random.seed(42)

n_records = 100

downloads = np.random.randint(5, 120, n_records)
author_popularity = np.random.randint(0, 2, n_records)
category_science = np.random.randint(0, 2, n_records)

recommended = []

for d, a, c in zip(downloads, author_popularity, category_science):
    score = d

    if a == 1:
        score += 20

    if c == 1:
        score += 10

    if score > 70:
        recommended.append(1)
    else:
        recommended.append(0)

# Add small noise
for i in np.random.choice(range(n_records), size=10, replace=False):
    recommended[i] = 1 - recommended[i]

data = pd.DataFrame({
    "downloads": downloads,
    "author_popularity": author_popularity,
    "category_science": category_science,
    "recommended": recommended
})

# ================= TRAIN MODEL =================

X = data[["downloads", "author_popularity", "category_science"]]
y = data["recommended"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

# ================= EVALUATION =================

y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
auc = roc_auc_score(y_test, y_prob)

print("\n===== MODEL PERFORMANCE =====")
print("Accuracy:", round(accuracy, 4))
print("Precision:", round(precision, 4))
print("Recall:", round(recall, 4))
print("F1-Score:", round(f1, 4))
print("AUC-ROC:", round(auc, 4))

print("\nConfusion Matrix")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report")
print(classification_report(y_test, y_pred))

# ================= RECOMMEND FUNCTION =================

def recommend_books(book_data):
    recommendations = []

    for book in book_data:
        if book.get("downloads", 0) > 40:
            recommendations.append(book)

    return recommendations