
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def clean_text(value):
    """Convert values safely into lowercase text."""
    if value is None:
        return ""
    return str(value).strip().lower()


def split_skills(value):
    """Convert comma-separated skills into a normalized set."""
    if not value:
        return set()

    skills = re.split(r"[,;\n|]+", str(value))

    return {
        skill.strip().lower()
        for skill in skills
        if skill.strip()
    }


def get_profile_text(profile):
    """Support both new saved profiles and older homepage profiles."""

    qualification = clean_text(profile.get("qualification"))
    branch = clean_text(
        profile.get("branch") or profile.get("field")
    )
    skills = clean_text(profile.get("skills"))
    domain = clean_text(
        profile.get("preferred_domain") or profile.get("interests")
    )
    location = clean_text(
        profile.get("preferred_location") or profile.get("location")
    )

    return " ".join([
        qualification,
        branch,
        skills,
        domain,
        location
    ]).strip()


def recommend_internships(profile, internships, limit=6):
    """
    Recommend internships using TF-IDF and additional profile matching.

    Match score is a relevance score, not a guarantee of selection.
    """

    if not internships:
        return []

    profile = profile or {}

    profile_text = get_profile_text(profile)

    # Student profile details
    student_skills = split_skills(profile.get("skills"))

    student_domain = clean_text(
        profile.get("preferred_domain") or profile.get("interests")
    )

    student_location = clean_text(
        profile.get("preferred_location") or profile.get("location")
    )

    student_qualification = clean_text(
        profile.get("qualification")
    )

    student_branch = clean_text(
        profile.get("branch") or profile.get("field")
    )

    internship_texts = []

    for item in internships:
        internship_texts.append(" ".join([
            clean_text(item.get("title")),
            clean_text(item.get("category")),
            clean_text(item.get("skills")),
            clean_text(item.get("location")),
            clean_text(item.get("qualification")),
            clean_text(item.get("description"))
        ]))

    # TF-IDF similarity
    documents = [profile_text] + internship_texts

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2)
        )

        matrix = vectorizer.fit_transform(documents)

        similarity_scores = cosine_similarity(
            matrix[0:1],
            matrix[1:]
        ).flatten()

    except ValueError:
        similarity_scores = [0.0] * len(internships)

    ranked = []

    for item, similarity in zip(internships, similarity_scores):

        result = dict(item)

        internship_skills = split_skills(item.get("skills"))

        # 1. Skill matching
        matched_skills = student_skills.intersection(
            internship_skills
        )

        skill_score = (
            len(matched_skills) / len(student_skills) * 100
            if student_skills else 0
        )

        # 2. Domain matching
        internship_category = clean_text(item.get("category"))
        internship_title = clean_text(item.get("title"))

        domain_match = bool(
            student_domain
            and (
                student_domain in internship_category
                or internship_category in student_domain
                or student_domain in internship_title
            )
        )

        # 3. Location matching
        internship_location = clean_text(item.get("location"))

        location_match = bool(
            student_location
            and internship_location
            and (
                student_location in internship_location
                or internship_location in student_location
                or internship_location in ("remote", "work from home")
            )
        )

        # 4. Qualification matching
        internship_qualification = clean_text(
            item.get("qualification")
        )

        qualification_match = bool(
            student_qualification
            and internship_qualification
            and (
                student_qualification in internship_qualification
                or internship_qualification in student_qualification
            )
        )

        # 5. Branch matching
        branch_match = bool(
            student_branch
            and student_branch in (
                internship_category + " " + internship_title
            )
        )

        # Weighted relevance score
        final_score = (
            float(similarity) * 60
            + skill_score * 20
            + (10 if domain_match else 0)
            + (5 if location_match else 0)
            + (3 if qualification_match else 0)
            + (2 if branch_match else 0)
        )

        final_score = round(min(final_score, 100), 1)

        # Recommendation explanations
        reasons = []

        if matched_skills:
            reasons.append(
                "Matching skills: " + ", ".join(sorted(matched_skills))
            )

        if domain_match:
            reasons.append("Matches your preferred domain")

        if location_match:
            reasons.append("Matches your preferred location")

        if qualification_match:
            reasons.append("Qualification matches")

        if branch_match:
            reasons.append("Related to your academic branch")

        if not reasons:
            reasons.append("Some profile details match this opportunity")

        result["match_score"] = final_score
        result["match_reasons"] = reasons

        ranked.append(result)

    ranked.sort(
        key=lambda x: x["match_score"],
        reverse=True
    )

    return ranked
