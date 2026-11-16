
import argparse
import certifi
import json
import re
import sqlite3
import ssl
import sys
import urllib.error
import urllib.request

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


# ============================================================
# INTERNMATCH AI - OFFICIAL PMIS DISCOVERY
# ============================================================

API_BASE = "https://api.ncs.gov.in/api/pmis/sso"

SOURCE_URL = "https://ncs.gov.in/Pmis-jobList"
OFFICIAL_APPLY_URL = "https://pminternship.mca.gov.in/login/"

DB_PATH = Path(__file__).resolve().parent / "internships.db"

PAGE_SIZE = 500
MAX_PAGES_PER_STATE = 20
TIMEZONE = ZoneInfo("Asia/Kolkata")

SSL_CONTEXT = ssl.create_default_context(
    cafile=certifi.where()
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 InternMatchAI/1.0",
    "Accept": "application/json",
}


# ============================================================
# DATABASE METADATA COLUMNS
# ============================================================

NEW_COLUMNS = {
    "ncs_internship_id": "TEXT",
    "stipend": "TEXT",
    "duration": "INTEGER",
    "mode_of_internship": "TEXT",
    "sector": "TEXT",
    "area_field": "TEXT",
    "district": "TEXT",
    "state": "TEXT",
    "opportunities": "INTEGER",
    "candidates_applied": "INTEGER",
    "minimum_qualification": "TEXT",
    "application_start_date": "TEXT",
    "application_end_date": "TEXT",
    "listing_status": "TEXT",
    "company_logo_url": "TEXT",
    "address": "TEXT",
}


# ============================================================
# GENERAL HELPERS
# ============================================================

def now_ist():
    return datetime.now(TIMEZONE).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def fetch_json(url):
    request = urllib.request.Request(
        url,
        headers=HEADERS
    )

    try:
        with urllib.request.urlopen(
            request,
            context=SSL_CONTEXT,
            timeout=40
        ) as response:

            if response.status != 200:
                raise RuntimeError(
                    f"HTTP error {response.status}: {url}"
                )

            content = response.read().decode(
                "utf-8",
                errors="replace"
            )

            return json.loads(content)

    except urllib.error.HTTPError as error:
        raise RuntimeError(
            f"HTTP {error.code}: {url}"
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            f"Network error: {error.reason}"
        ) from error

    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Invalid JSON received from: {url}"
        ) from error


def clean_text(value):
    if value is None:
        return ""

    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)

    return str(value).strip()


def safe_integer(value):
    if value is None or value == "":
        return None

    try:
        return int(value)
    except (ValueError, TypeError):
        match = re.search(r"\d+", str(value))

        if match:
            return int(match.group())

        return None


def parse_date(value):
    if not value:
        return None

    value = str(value).strip()

    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(
                value[:26],
                fmt
            ).date()
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).date()
    except ValueError:
        return None


def determine_listing_status(start_value, end_value):
    today = datetime.now(TIMEZONE).date()

    start_date = parse_date(start_value)
    end_date = parse_date(end_value)

    if end_date and today > end_date:
        return "CLOSED"

    if start_date and today < start_date:
        return "UPCOMING"

    if start_date or end_date:
        return "OPEN"

    return "UNKNOWN"


# ============================================================
# OFFICIAL API
# ============================================================

def fetch_states():
    print("\nFetching official state list...")

    states = fetch_json(
        f"{API_BASE}/states"
    )

    if not isinstance(states, list) or not states:
        raise RuntimeError(
            "Official state list is empty or invalid."
        )

    valid_states = []

    for state in states:
        if not isinstance(state, dict):
            continue

        state_id = state.get("id")
        state_name = clean_text(state.get("name"))

        if state_id is None or not state_name:
            continue

        valid_states.append({
            "id": state_id,
            "name": state_name,
            "code": state.get("code"),
        })

    if not valid_states:
        raise RuntimeError(
            "No valid states found in API response."
        )

    print(
        f"Official states available: {len(valid_states)}"
    )

    return valid_states


def fetch_state_page(state_id, page):
    url = (
        f"{API_BASE}/internships"
        f"?page={page}"
        f"&size={PAGE_SIZE}"
        f"&stateId={state_id}"
    )

    response = fetch_json(url)

    if not isinstance(response, dict):
        raise RuntimeError(
            f"Invalid internship response for state {state_id}"
        )

    records = response.get("internships")

    if not isinstance(records, list):
        raise RuntimeError(
            f"Missing internships list for state {state_id}"
        )

    return records


# ============================================================
# STATE-WISE COLLECTION
# ============================================================

def collect_all_internships():
    states = fetch_states()

    all_records = {}
    state_reports = []

    failed_states = []
    incomplete_states = []

    total_received = 0
    duplicate_count = 0
    conflicting_records = 0
    invalid_records = 0

    print("\n" + "=" * 70)
    print("OFFICIAL PMIS STATE-WISE COLLECTION")
    print("=" * 70)

    for state in states:

        state_id = state["id"]
        state_name = state["name"]

        page = 1
        state_received = 0
        state_ids = set()

        print(
            f"\nCollecting: {state_name} "
            f"(ID: {state_id})"
        )

        try:
            while True:

                records = fetch_state_page(
                    state_id,
                    page
                )

                if not records:
                    break

                total_received += len(records)
                state_received += len(records)

                for record in records:

                    if not isinstance(record, dict):
                        invalid_records += 1
                        continue

                    internship_id = record.get(
                        "internshipId"
                    )

                    if internship_id is None:
                        invalid_records += 1
                        continue

                    internship_id = str(
                        internship_id
                    ).strip()

                    if not internship_id:
                        invalid_records += 1
                        continue

                    if internship_id in state_ids:
                        duplicate_count += 1

                    state_ids.add(internship_id)

                    if internship_id in all_records:

                        duplicate_count += 1

                        old_record = all_records[
                            internship_id
                        ]

                        if old_record != record:
                            conflicting_records += 1

                        all_records[internship_id] = record

                    else:
                        all_records[internship_id] = record

                print(
                    f"  Page {page}: {len(records)} records | "
                    f"Unique in state: {len(state_ids)}"
                )

                if len(records) < PAGE_SIZE:
                    break

                page += 1

                if page > MAX_PAGES_PER_STATE:
                    incomplete_states.append(
                        state_name
                    )

                    print(
                        "  WARNING: Maximum page limit reached."
                    )

                    break

            state_reports.append({
                "state": state_name,
                "received": state_received,
                "unique": len(state_ids),
            })

            print(
                f"  State received: {state_received}"
            )

            print(
                f"  State unique IDs: {len(state_ids)}"
            )

        except Exception as error:

            failed_states.append({
                "state": state_name,
                "error": str(error),
            })

            print(
                f"  ERROR collecting {state_name}: {error}"
            )

    collection_complete = (
        len(failed_states) == 0
        and len(incomplete_states) == 0
        and len(state_reports) == len(states)
    )

    print("\n" + "=" * 70)
    print("COLLECTION SUMMARY")
    print("=" * 70)

    print("States available:", len(states))
    print("States processed:", len(state_reports))
    print("Total records received:", total_received)
    print("Unique internship IDs:", len(all_records))
    print("Duplicate encounters:", duplicate_count)
    print("Conflicting duplicate records:", conflicting_records)
    print("Invalid records skipped:", invalid_records)

    print("\nSTATE-WISE REPORT")

    for report in state_reports:
        print(
            f"{report['state']:45} "
            f"Received: {report['received']:5} | "
            f"Unique: {report['unique']:5}"
        )

    if failed_states:
        print("\nFAILED STATES")

        for item in failed_states:
            print(
                f"- {item['state']}: {item['error']}"
            )

    if incomplete_states:
        print("\nINCOMPLETE STATES")

        for name in incomplete_states:
            print("-", name)

    print("\nCollection complete:", collection_complete)

    return {
        "records": all_records,
        "states": states,
        "state_reports": state_reports,
        "failed_states": failed_states,
        "incomplete_states": incomplete_states,
        "collection_complete": collection_complete,
        "total_received": total_received,
        "unique_count": len(all_records),
        "duplicate_count": duplicate_count,
        "conflicting_records": conflicting_records,
        "invalid_records": invalid_records,
    }


# ============================================================
# CONVERT OFFICIAL RECORDS TO DATABASE FORMAT
# ============================================================

def prepare_record(record):

    internship_id = str(
        record.get("internshipId", "")
    ).strip()

    title = clean_text(
        record.get("internshipTitle")
    )

    company = clean_text(
        record.get("companyName")
    )

    sector = clean_text(
        record.get("sector")
    )

    area_field = clean_text(
        record.get("areaField")
    )

    district = clean_text(
        record.get("district")
    )

    state = clean_text(
        record.get("state")
    )

    qualification = clean_text(
        record.get("minimumQualification")
    )

    stipend = clean_text(
        record.get("stipend")
    )

    duration_value = record.get(
        "durationOfInternship"
    )

    duration = safe_integer(
        duration_value
    )

    mode = clean_text(
        record.get("modeOfInternship")
    )

    opportunities = safe_integer(
        record.get("numberOfOpportunities")
    )

    candidates_applied = safe_integer(
        record.get("candidatesAlreadyApplied")
    )

    start_date = clean_text(
        record.get("applicationStartDate")
    )

    end_date = clean_text(
        record.get("applicationEndDate")
    )

    listing_status = determine_listing_status(
        start_date,
        end_date
    )

    address_parts = [
        clean_text(record.get("addressLine1")),
        clean_text(record.get("addressLine2")),
        clean_text(record.get("village")),
        clean_text(record.get("block")),
        district,
        state,
        clean_text(record.get("pincode")),
    ]

    address = ", ".join(
        part for part in address_parts if part
    )

    location_parts = [
        part for part in [district, state] if part
    ]

    location = ", ".join(location_parts)

    category = area_field or sector or "Other"

    skill_parts = []

    if sector:
        skill_parts.append(sector)

    if area_field and area_field not in skill_parts:
        skill_parts.append(area_field)

    skills = ", ".join(skill_parts)

    description_parts = [
        "Official PM Internship Scheme opportunity.",
        f"Company: {company}" if company else "",
        f"Sector: {sector}" if sector else "",
        f"Field: {area_field}" if area_field else "",
        f"Stipend: {stipend}" if stipend else "",
        f"Duration: {duration_value}" if duration_value else "",
        f"Mode: {mode}" if mode else "",
        f"Available opportunities: {opportunities}"
        if opportunities is not None else "",
        f"Candidates applied: {candidates_applied}"
        if candidates_applied is not None else "",
        f"Location: {location}" if location else "",
    ]

    description = "\n".join(
        part for part in description_parts if part
    )

    application_url = clean_text(
        record.get("applyLink")
    )

    if not application_url.startswith(
        "https://pminternship.mca.gov.in/"
    ):
        application_url = OFFICIAL_APPLY_URL

    return {
        "title": title,
        "category": category,
        "skills": skills,
        "location": location or "Not specified",
        "qualification": qualification or "Not specified",
        "description": description,
        "company_name": company,
        "source_type": "PMIS",
        "application_url": application_url,
        "deadline": end_date,
        "verification_status": "Verified",
        "source_url": SOURCE_URL,
        "verified_at": now_ist(),

        "ncs_internship_id": internship_id,
        "stipend": stipend,
        "duration": duration,
        "mode_of_internship": mode,
        "sector": sector,
        "area_field": area_field,
        "district": district,
        "state": state,
        "opportunities": opportunities,
        "candidates_applied": candidates_applied,
        "minimum_qualification": qualification,
        "application_start_date": start_date,
        "application_end_date": end_date,
        "listing_status": listing_status,
        "company_logo_url": clean_text(
            record.get("companyLogo")
        ),
        "address": address,
    }


def validate_record(record):

    required_fields = [
        "ncs_internship_id",
        "title",
        "company_name",
    ]

    for field in required_fields:
        if not record.get(field):
            return False

    return True


# ============================================================
# DATABASE MIGRATION
# ============================================================

def migrate_database(connection):

    cursor = connection.cursor()

    cursor.execute(
        "PRAGMA table_info(internships)"
    )

    existing_columns = {
        row[1] for row in cursor.fetchall()
    }

    if not existing_columns:
        raise RuntimeError(
            "The internships table does not exist. "
            "Run the main application first."
        )

    required_base_columns = {
        "id",
        "title",
        "category",
        "skills",
        "location",
        "qualification",
        "description",
        "company_name",
        "source_type",
        "application_url",
        "deadline",
        "verification_status",
        "source_url",
        "verified_at",
    }

    missing_base = (
        required_base_columns - existing_columns
    )

    if missing_base:
        raise RuntimeError(
            "Unexpected database schema. Missing columns: "
            + ", ".join(sorted(missing_base))
        )

    added_columns = []

    for column, column_type in NEW_COLUMNS.items():

        if column not in existing_columns:

            cursor.execute(
                f"ALTER TABLE internships "
                f"ADD COLUMN {column} {column_type}"
            )

            added_columns.append(column)

    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS
        idx_internships_ncs_id
        ON internships(ncs_internship_id)
        WHERE ncs_internship_id IS NOT NULL
          AND ncs_internship_id != ''
    """)

    connection.commit()

    if added_columns:
        print(
            "\nDatabase columns added:",
            ", ".join(added_columns)
        )

    print("Database schema verified.")


# ============================================================
# DRY RUN
# ============================================================

def show_dry_run(collection):

    records = collection["records"]

    print("\n" + "=" * 70)
    print("DRY RUN - NO DATABASE CHANGES")
    print("=" * 70)

    valid_records = []
    invalid_count = 0

    for raw_record in records.values():

        prepared = prepare_record(raw_record)

        if validate_record(prepared):
            valid_records.append(prepared)
        else:
            invalid_count += 1

    print("Collected records:", len(records))
    print("Valid records:", len(valid_records))
    print("Invalid records:", invalid_count)

    print("\nSAMPLE OFFICIAL RECORDS")

    for record in valid_records[:10]:

        print("\n----------------------------------------")
        print("Internship ID:", record["ncs_internship_id"])
        print("Title:", record["title"])
        print("Company:", record["company_name"])
        print("Category:", record["category"])
        print("Location:", record["location"])
        print("Stipend:", record["stipend"])
        print("Duration:", record["duration"])
        print("Status:", record["listing_status"])
        print("Application URL:", record["application_url"])

    print("\n" + "=" * 70)
    print("DRY RUN FINISHED")
    print("Database was not modified.")
    print("=" * 70)

    return valid_records, invalid_count


# ============================================================
# SAFE DATABASE IMPORT
# ============================================================

def import_records(valid_records):

    connection = sqlite3.connect(
        str(DB_PATH),
        timeout=30
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    try:

        migrate_database(connection)

        cursor = connection.cursor()

        columns = [
            "title",
            "category",
            "skills",
            "location",
            "qualification",
            "description",
            "company_name",
            "source_type",
            "application_url",
            "deadline",
            "verification_status",
            "source_url",
            "verified_at",
        ] + list(NEW_COLUMNS.keys())

        placeholders = ", ".join(
            ["?"] * len(columns)
        )

        update_columns = [
            column for column in columns
            if column != "ncs_internship_id"
        ]

        update_clause = ", ".join(
            f"{column}=excluded.{column}"
            for column in update_columns
        )

        sql = f"""
            INSERT INTO internships ({", ".join(columns)})
            VALUES ({placeholders})
            ON CONFLICT(ncs_internship_id)
            WHERE ncs_internship_id IS NOT NULL
              AND ncs_internship_id != ''
            DO UPDATE SET {update_clause}
        """

        inserted = 0
        updated = 0

        for record in valid_records:

            cursor.execute(
                """
                SELECT id
                FROM internships
                WHERE ncs_internship_id = ?
                """,
                (record["ncs_internship_id"],)
            )

            existed = cursor.fetchone() is not None

            values = [
                record.get(column)
                for column in columns
            ]

            cursor.execute(sql, values)

            if existed:
                updated += 1
            else:
                inserted += 1

        connection.commit()

        print("\n" + "=" * 70)
        print("PMIS DATABASE IMPORT SUCCESSFUL")
        print("=" * 70)

        print("New records inserted:", inserted)
        print("Existing records updated:", updated)
        print("Total processed:", len(valid_records))

        cursor.execute("""
            SELECT COUNT(*)
            FROM internships
            WHERE source_type = 'DEMO'
        """)

        demo_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM internships
            WHERE source_type = 'PMIS'
        """)

        pmis_count = cursor.fetchone()[0]

        print("DEMO records preserved:", demo_count)
        print("PMIS records in database:", pmis_count)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "InternMatch AI - Official PMIS discovery "
            "and database importer"
        )
    )

    parser.add_argument(
        "--import",
        dest="do_import",
        action="store_true",
        help="Import verified PMIS records into internships.db"
    )

    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation for scheduled imports"
    )

    args = parser.parse_args()

    # --yes must never trigger an import by itself.
    if args.yes and not args.do_import:
        parser.error("--yes can only be used with --import")

    print("=" * 70)
    print("INTERNMATCH AI - OFFICIAL PMIS DISCOVERY")
    print("=" * 70)

    print("API:", API_BASE)
    print("Database:", DB_PATH)
    print("Page size:", PAGE_SIZE)
    print("Started:", now_ist())

    if not DB_PATH.exists():
        print(
            "\nERROR: internships.db not found."
        )
        print("Run the main application first.")
        sys.exit(1)

    try:

        collection = collect_all_internships()

        if not collection["collection_complete"]:

            print("\nIMPORT BLOCKED")
            print(
                "At least one state failed or was incomplete."
            )
            print(
                "No internship records were imported."
            )

            sys.exit(1)

        valid_records, invalid_count = show_dry_run(
            collection
        )

        if invalid_count > 0:
            print(
                "\nIMPORT BLOCKED: Invalid records were found."
            )
            print(
                "Review the API data before importing."
            )
            sys.exit(1)

        if not valid_records:
            print(
                "\nNo valid records available for import."
            )
            sys.exit(1)

        if args.do_import:

            print("\nIMPORT MODE SELECTED")

            if args.yes:
                print(
                    "Automatic confirmation enabled."
                )
            else:
                print(
                    "Make sure you have backed up internships.db."
                )

                confirmation = input(
                    "\nType IMPORT to continue: "
                ).strip()

                if confirmation != "IMPORT":
                    print(
                        "\nImport cancelled. Database unchanged."
                    )
                    return

            import_records(valid_records)

        else:

            print("\nDRY RUN MODE")
            print(
                "To import manually, run: "
                "python discovery.py --import"
            )
            print(
                "For scheduled import, run: "
                "python discovery.py --import --yes"
            )

        print("\nFinished:", now_ist())

    except KeyboardInterrupt:
        print(
            "\nProcess interrupted. No import was completed."
        )
        sys.exit(1)

    except Exception as error:
        print("\nERROR:", error)
        print("Review the error before trying again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
