import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from tqdm import tqdm
from backend.utils.priority_ai import analyze_priority

df = pd.read_csv("priority_testset.csv")

y_true = []
y_pred = []

for _, row in tqdm(df.iterrows(), total=len(df)):
    text = str(row['text'])
    true_label = str(row['label'])
    res = analyze_priority(text)
    pred_label = res.get('priority')  
    if pred_label and 'PASSED' in pred_label.upper():
        pred_label = 'Critical'
    y_true.append(true_label)
    y_pred.append(pred_label)

print("Priority classification results:")
print(f"Samples evaluated: {len(y_true)}")
print("Accuracy:", accuracy_score(y_true, y_pred))
print("\nClassification Report:\n", classification_report(y_true, y_pred))
print("\nConfusion Matrix:\n", confusion_matrix(y_true, y_pred))
