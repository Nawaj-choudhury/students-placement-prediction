import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib

# Load dataset
data = pd.read_csv("dataset.csv")

# Convert Yes/No to 1/0
data["Placed"] = data["Placed"].map({"Yes": 1, "No": 0})

# Features and Target
X = data[["CGPA", "Internship", "Aptitude"]]
y = data["Placed"]

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)
model.fit(X_train, y_train)

# Accuracy
accuracy = model.score(X_test, y_test)
print("Model Accuracy:", accuracy)
joblib.dump(accuracy, "accuracy.pkl")

# Predict new student
prediction = model.predict([[8.2, 1, 80]])

if prediction[0] == 1:
    print("Student is likely to be PLACED")
else:
    print("Student is likely NOT PLACED")

joblib.dump(model, "model.pkl")
print("Model saved successfully")