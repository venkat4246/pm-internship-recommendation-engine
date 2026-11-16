
import sqlite3
from pathlib import Path
from datetime import datetime


# --------------------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------------------

DB_PATH = Path(__file__).with_name("internships.db")


def get_connection():
    connection = sqlite3.connect(str(DB_PATH))
    connection.row_factory = sqlite3.Row
    return connection


def current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# --------------------------------------------------
# DEMO INTERNSHIP DATA
# These are sample records, NOT real vacancies.
# --------------------------------------------------

SAMPLE_INTERNSHIPS = [
    (
        "Data Analyst Intern",
        "Data Analytics",
        "Python, SQL, Excel, Power BI",
        "Hyderabad",
        "B.Tech, Degree or equivalent",
        "DEMO opportunity for students interested in data analysis and reporting."
    ),
    (
        "Python Developer Intern",
        "Software Development",
        "Python, Flask, SQL, Git",
        "Remote",
        "B.Tech or equivalent",
        "DEMO opportunity for students interested in Python development."
    ),
    (
        "Web Development Intern",
        "Web Development",
        "HTML, CSS, JavaScript, Python",
        "Hyderabad",
        "B.Tech or Diploma",
        "DEMO opportunity for students interested in frontend and backend development."
    ),
    (
        "Digital Marketing Intern",
        "Marketing",
        "SEO, Social Media, Content Marketing",
        "Remote",
        "Any Degree",
        "DEMO opportunity for students interested in digital marketing."
    ),
    (
        "Finance Operations Intern",
        "Finance",
        "Excel, Accounting, Communication",
        "Hyderabad",
        "B.Com, BBA or equivalent",
        "DEMO opportunity for students interested in finance operations."
    ),
    (
        "Human Resources Intern",
        "Human Resources",
        "Communication, Recruitment, MS Excel",
        "Remote",
        "Any Degree",
        "DEMO opportunity for students interested in human resources."
    ),
    (
        "Business Analyst Intern",
        "Business Analytics",
        "Excel, SQL, Communication, Power BI",
        "Hyderabad",
        "B.Tech, BBA or equivalent",
        "DEMO opportunity for students interested in business analysis."
    ),
    (
        "UI/UX Design Intern",
        "Design",
        "Figma, UI Design, UX Research",
        "Remote",
        "Any Degree",
        "DEMO opportunity for students interested in UI and UX design."
    ),
    (
        "Cybersecurity Intern",
        "Cybersecurity",
        "Networking, Linux, Security Fundamentals",
        "Hyderabad",
        "B.Tech or equivalent",
        "DEMO opportunity for students interested in cybersecurity."
    ),
    (
        "Content Writing Intern",
        "Content",
        "Writing, Research, Communication",
        "Remote",
        "Any Degree",
        "DEMO opportunity for students interested in content writing."
    ),
    (
        "Operations Intern",
        "Operations",
        "Excel, Management, Communication",
        "Hyderabad",
        "Any Degree",
        "DEMO opportunity for students interested in business operations."
    ),
    (
        "Data Science Intern",
        "Data Science",
        "Python, Pandas, NumPy, Machine Learning",
        "Remote",
        "B.Tech or equivalent",
        "DEMO opportunity for students interested in data science."
    )
]


# --------------------------------------------------
# SAFE DATABASE MIGRATIONS
# --------------------------------------------------

def add_missing_columns(connection, table_name, columns):
    existing_columns = {
        row["name"]
        for row in connection.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()
    }

    for column_name, column_definition in columns.items():
        if column_name not in existing_columns:
            connection.execute(
                f"ALTER TABLE {table_name} "
                f"ADD COLUMN {column_name} {column_definition}"
            )


# --------------------------------------------------
# INITIALIZE DATABASE
# --------------------------------------------------

def init_db():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        # USERS TABLE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                profile_picture TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # STUDENT PROFILES TABLE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_profiles (
                user_id INTEGER PRIMARY KEY,
                qualification TEXT DEFAULT '',
                college TEXT DEFAULT '',
                branch TEXT DEFAULT '',
                graduation_year TEXT DEFAULT '',
                skills TEXT DEFAULT '',
                preferred_domain TEXT DEFAULT '',
                preferred_location TEXT DEFAULT '',
                internship_type TEXT DEFAULT '',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # INTERNSHIPS TABLE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS internships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT DEFAULT '',
                skills TEXT DEFAULT '',
                location TEXT DEFAULT '',
                qualification TEXT DEFAULT '',
                description TEXT DEFAULT '',
                company_name TEXT DEFAULT '',
                source_type TEXT DEFAULT 'DEMO',
                application_url TEXT DEFAULT '',
                deadline TEXT DEFAULT '',
                verification_status TEXT DEFAULT 'Demo',
                source_url TEXT DEFAULT '',
                verified_at TEXT DEFAULT ''
            )
        """)

        # MIGRATE EXISTING USERS TABLE
        add_missing_columns(
            connection,
            "users",
            {
                "profile_picture": "TEXT DEFAULT ''"
            }
        )

        # MIGRATE EXISTING STUDENT PROFILES TABLE
        add_missing_columns(
            connection,
            "student_profiles",
            {
                "qualification": "TEXT DEFAULT ''",
                "college": "TEXT DEFAULT ''",
                "branch": "TEXT DEFAULT ''",
                "graduation_year": "TEXT DEFAULT ''",
                "skills": "TEXT DEFAULT ''",
                "preferred_domain": "TEXT DEFAULT ''",
                "preferred_location": "TEXT DEFAULT ''",
                "internship_type": "TEXT DEFAULT ''",
                "updated_at": "TEXT DEFAULT CURRENT_TIMESTAMP"
            }
        )

        # MIGRATE EXISTING INTERNSHIPS TABLE
        add_missing_columns(
            connection,
            "internships",
            {
                "company_name": "TEXT DEFAULT ''",
                "source_type": "TEXT DEFAULT 'DEMO'",
                "application_url": "TEXT DEFAULT ''",
                "deadline": "TEXT DEFAULT ''",
                "verification_status": "TEXT DEFAULT 'Demo'",
                "source_url": "TEXT DEFAULT ''",
                "verified_at": "TEXT DEFAULT ''"
            }
        )

        # Label existing sample records as DEMO.
        cursor.execute("""
            UPDATE internships
            SET source_type = 'DEMO'
            WHERE source_type IS NULL OR TRIM(source_type) = ''
        """)

        cursor.execute("""
            UPDATE internships
            SET verification_status = 'Demo'
            WHERE verification_status IS NULL
               OR TRIM(verification_status) = ''
        """)

        # Insert samples only if the internship table is empty.
        internship_count = cursor.execute(
            "SELECT COUNT(*) FROM internships"
        ).fetchone()[0]

        if internship_count == 0:
            cursor.executemany("""
                INSERT INTO internships (
                    title,
                    category,
                    skills,
                    location,
                    qualification,
                    description,
                    company_name,
                    source_type,
                    application_url,
                    deadline,
                    verification_status,
                    source_url,
                    verified_at
                )
                VALUES (?, ?, ?, ?, ?, ?, '', 'DEMO', '', '', 'Demo', '', '')
            """, SAMPLE_INTERNSHIPS)

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# --------------------------------------------------
# USER FUNCTIONS
# --------------------------------------------------

def create_user(name, email, password_hash):
    connection = get_connection()

    try:
        connection.execute("""
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
        """, (name, email, password_hash))

        connection.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        connection.close()


def get_user_by_email(email):
    connection = get_connection()

    try:
        row = connection.execute("""
            SELECT * FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


def get_user_by_id(user_id):
    connection = get_connection()

    try:
        row = connection.execute("""
            SELECT * FROM users
            WHERE id = ?
        """, (user_id,)).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


# --------------------------------------------------
# PROFILE PICTURE FUNCTIONS
# --------------------------------------------------

def update_profile_picture(user_id, filename):
    connection = get_connection()

    try:
        connection.execute("""
            UPDATE users
            SET profile_picture = ?
            WHERE id = ?
        """, (filename, user_id))

        connection.commit()

    finally:
        connection.close()


def remove_profile_picture(user_id):
    connection = get_connection()

    try:
        connection.execute("""
            UPDATE users
            SET profile_picture = ''
            WHERE id = ?
        """, (user_id,))

        connection.commit()

    finally:
        connection.close()


# --------------------------------------------------
# STUDENT PROFILE FUNCTIONS
# --------------------------------------------------

def save_student_profile(user_id, profile):
    connection = get_connection()

    try:
        connection.execute("""
            INSERT INTO student_profiles (
                user_id,
                qualification,
                college,
                branch,
                graduation_year,
                skills,
                preferred_domain,
                preferred_location,
                internship_type,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(user_id)
            DO UPDATE SET
                qualification = excluded.qualification,
                college = excluded.college,
                branch = excluded.branch,
                graduation_year = excluded.graduation_year,
                skills = excluded.skills,
                preferred_domain = excluded.preferred_domain,
                preferred_location = excluded.preferred_location,
                internship_type = excluded.internship_type,
                updated_at = excluded.updated_at
        """, (
            user_id,
            profile.get("qualification", ""),
            profile.get("college", ""),
            profile.get("branch", ""),
            profile.get("graduation_year", ""),
            profile.get("skills", ""),
            profile.get("preferred_domain", ""),
            profile.get("preferred_location", ""),
            profile.get("internship_type", ""),
            current_timestamp()
        ))

        connection.commit()

    finally:
        connection.close()


def get_student_profile(user_id):
    connection = get_connection()

    try:
        row = connection.execute("""
            SELECT * FROM student_profiles
            WHERE user_id = ?
        """, (user_id,)).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


# --------------------------------------------------
# INTERNSHIP FUNCTIONS
# --------------------------------------------------

def get_all_internships():
    connection = get_connection()

    try:
        rows = connection.execute("""
            SELECT * FROM internships
            ORDER BY id DESC
        """).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def get_internship_by_id(internship_id):
    connection = get_connection()

    try:
        row = connection.execute("""
            SELECT * FROM internships
            WHERE id = ?
        """, (internship_id,)).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


# --------------------------------------------------
# ADD OR UPDATE AN INTERNSHIP
# --------------------------------------------------

def add_internship(internship):
    connection = get_connection()

    try:
        cursor = connection.execute("""
            INSERT INTO internships (
                title,
                category,
                skills,
                location,
                qualification,
                description,
                company_name,
                source_type,
                application_url,
                deadline,
                verification_status,
                source_url,
                verified_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            internship.get("title", ""),
            internship.get("category", ""),
            internship.get("skills", ""),
            internship.get("location", ""),
            internship.get("qualification", ""),
            internship.get("description", ""),
            internship.get("company_name", ""),
            internship.get("source_type", "DEMO"),
            internship.get("application_url", ""),
            internship.get("deadline", ""),
            internship.get("verification_status", "Demo"),
            internship.get("source_url", ""),
            internship.get("verified_at", "")
        ))

        connection.commit()
        return cursor.lastrowid

    finally:
        connection.close()


def update_internship(internship_id, internship):
    connection = get_connection()

    try:
        connection.execute("""
            UPDATE internships
            SET
                title = ?,
                category = ?,
                skills = ?,
                location = ?,
                qualification = ?,
                description = ?,
                company_name = ?,
                source_type = ?,
                application_url = ?,
                deadline = ?,
                verification_status = ?,
                source_url = ?,
                verified_at = ?
            WHERE id = ?
        """, (
            internship.get("title", ""),
            internship.get("category", ""),
            internship.get("skills", ""),
            internship.get("location", ""),
            internship.get("qualification", ""),
            internship.get("description", ""),
            internship.get("company_name", ""),
            internship.get("source_type", "DEMO"),
            internship.get("application_url", ""),
            internship.get("deadline", ""),
            internship.get("verification_status", "Demo"),
            internship.get("source_url", ""),
            internship.get("verified_at", ""),
            internship_id
        ))

        connection.commit()

    finally:
        connection.close()
