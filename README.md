# AI-Based Internship Recommendation Engine for PM Internship Scheme

A local academic prototype built with Python Flask, SQLite, HTML, CSS, JavaScript-compatible frontend, and scikit-learn.

## Features
- Student profile form: qualification, field, skills, preferred location and interests.
- SQLite database with illustrative sample internship records.
- TF-IDF text vectorization and cosine similarity ranking.
- Responsive homepage, results cards and project information page.

## Important
The included internship records are fictional demonstration data. This project is **not** an official PM Internship Scheme portal and does not fetch live vacancies. Before presenting real opportunities, replace the demo records with verified listings and display their source, date and application link. A match score is text similarity, not a probability of selection.

## Requirements
- Windows or Linux
- Python 3.10 or newer
- VS Code (recommended)

## Setup on Windows
1. Extract the ZIP file.
2. Open the extracted `pm_internship_recommendation_engine` folder in VS Code.
3. Open Terminal > New Terminal.
4. Create a virtual environment:

   ```powershell
   py -m venv venv
   ```

5. Activate it:

   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt terminal and run:

   ```bat
   venv\Scripts\activate.bat
   ```

6. Install libraries:

   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

7. Start the website:

   ```bash
   python app.py
   ```

8. Open this address in your browser:

   `http://127.0.0.1:5000`

The SQLite database `internships.db` is created automatically on the first run.

## Setup on Linux
```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```
Then visit `http://127.0.0.1:5000`.

## Project structure
```text
pm_internship_recommendation_engine/
├── app.py
├── database.py
├── recommender.py
├── requirements.txt
├── README.md
├── internships.db       # generated automatically when app runs
├── templates/
│   ├── base.html
│   ├── index.html
│   └── about.html
└── static/
    └── style.css
```

## How the recommendation works
1. Flask receives the student's profile from the form.
2. The app reads internship records from SQLite.
3. `TfidfVectorizer` converts the profile and internship text into numerical vectors.
4. `cosine_similarity` calculates how similar each internship is to the profile.
5. The app sorts the records by similarity and displays the top six.

## How to customize
- Add or edit sample internships in `SAMPLE_INTERNSHIPS` in `database.py`.
- If you change the sample records after the database has already been created, delete `internships.db` once and restart the app to reseed it. This deletes only the local demo database.
- To use MySQL, replace the SQLite connection functions in `database.py` with a MySQL connector and update `requirements.txt`.
- For a stronger final-year project, add verified scheme vacancy data, filters, student login, application links, feedback, and evaluation against manually labelled relevant internships.

## Troubleshooting
- `python is not recognized`: install Python from python.org and enable "Add Python to PATH", then reopen VS Code.
- `No module named flask` or `sklearn`: activate the virtual environment and run `pip install -r requirements.txt`.
- `Address already in use`: stop the other Flask process or change the port in `app.py`.
- Browser cannot connect: confirm the terminal shows Flask running, then open `http://127.0.0.1:5000`.
- PowerShell activation blocked: use the Command Prompt activation command shown above.

## Academic explanation
**Problem:** Students may find it difficult to identify internships that align with their education, skills and interests.

**Proposed solution:** A content-based recommendation engine ranks internship descriptions against a student's profile.

**Algorithm:** TF-IDF + cosine similarity.

**Why this algorithm:** It is lightweight, explainable, works with text fields, and is suitable for a small prototype dataset. It is a baseline recommender, not a trained predictive model.
