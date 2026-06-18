import pandas as pd
import random

data = []

for _ in range(5000):
    cgpa = round(random.uniform(5.0, 10.0), 1)
    internship = random.randint(0, 1)
    aptitude = random.randint(40, 100)
    communication = random.randint(40, 100)
    coding = random.randint(40, 100)
    projects = random.randint(0, 8)

    score = (
        cgpa * 10
        + aptitude
        + communication
        + coding
        + projects * 5
        + internship * 15
    )

    placed = "Yes" if score > 250 else "No"

    data.append([
        cgpa,
        internship,
        aptitude,
        communication,
        coding,
        projects,
        placed
    ])

df = pd.DataFrame(
    data,
    columns=[
        "CGPA",
        "Internship",
        "Aptitude",
        "Communication",
        "Coding",
        "Projects",
        "Placed"
    ]
)

df.to_csv("dataset.csv", index=False)

print("5000 rows generated successfully!")