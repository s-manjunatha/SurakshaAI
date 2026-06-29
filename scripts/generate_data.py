"""
SurakshAI Synthetic Data Generator
Generates realistic Indian crime dataset with relational integrity.
"""
import os
import sys
import uuid
import random
import hashlib
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import psycopg2
from psycopg2.extras import execute_values
from faker import Faker
from passlib.context import CryptContext

fake = Faker("en_IN")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DATABASE_URL = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql://surakshai:surakshai_secret@localhost:5432/surakshai",
)

# Configurable counts (use env vars for full dataset)
COUNTS = {
    "stations": int(os.getenv("SEED_STATIONS", "500")),
    "firs": int(os.getenv("SEED_FIRS", "100000")),
    "criminals": int(os.getenv("SEED_CRIMINALS", "20000")),
    "victims": int(os.getenv("SEED_VICTIMS", "50000")),
    "vehicles": int(os.getenv("SEED_VEHICLES", "100000")),
    "phones": int(os.getenv("SEED_PHONES", "100000")),
    "bank_accounts": int(os.getenv("SEED_BANK_ACCOUNTS", "50000")),
}

KARNATAKA_DISTRICTS = [
    "Bengaluru Urban", "Bengaluru Rural", "Mysuru", "Mangaluru", "Hubballi",
    "Belagavi", "Kalaburagi", "Ballari", "Davanagere", "Shivamogga",
    "Tumakuru", "Udupi", "Hassan", "Mandya", "Chitradurga", "Raichur",
    "Bidar", "Kolar", "Chikkamagaluru", "Dakshina Kannada", "Uttara Kannada",
]

CRIME_TYPES = [
    "theft", "robbery", "burglary", "assault", "murder", "kidnapping",
    "fraud", "cyber_crime", "drug_offense", "domestic_violence",
    "vehicle_theft", "chain_snatching", "rape", "dowry_harassment",
    "corruption", "money_laundering", "extortion", "other",
]

STATUSES = ["registered", "under_investigation", "charge_sheet_filed", "closed", "pending_trial", "convicted", "acquitted"]
PRIORITIES = ["low", "medium", "high", "critical"]
GENDERS = ["Male", "Female", "Other"]
VEHICLE_MAKES = ["Maruti", "Hyundai", "Tata", "Mahindra", "Honda", "Toyota", "Bajaj", "Hero"]
BANKS = ["SBI", "HDFC", "ICICI", "Axis", "Canara", "PNB", "Karnataka Bank", "Union Bank"]

# Karnataka bounding box approx
LAT_RANGE = (12.0, 16.5)
LNG_RANGE = (74.0, 78.5)


def uid():
    return str(uuid.uuid4())


def batch_insert(conn, table, columns, rows, batch_size=5000):
    if not rows:
        return
    cols = ", ".join(columns)
    template = "(" + ", ".join(["%s"] * len(columns)) + ")"
    cur = conn.cursor()
    for i in range(0, len(rows), batch_size):
        chunk = rows[i : i + batch_size]
        execute_values(cur, f"INSERT INTO {table} ({cols}) VALUES %s", chunk, template=template)
    cur.close()


def generate_stations(conn, n):
    print(f"Generating {n} police stations...")
    rows = []
    for i in range(n):
        district = random.choice(KARNATAKA_DISTRICTS)
        lat = random.uniform(*LAT_RANGE)
        lng = random.uniform(*LNG_RANGE)
        rows.append((
            uid(), f"{district.split()[0][:3].upper()}-PS-{i+1:04d}",
            f"{district.split()[0][:3].upper()}-PS-{i+1:04d}",
            district, "Karnataka", fake.address(), lat, lng, fake.phone_number(),
        ))
    batch_insert(conn, "police_stations",
                 ["id", "name", "code", "district", "state", "address", "latitude", "longitude", "phone"], rows)
    cur = conn.cursor()
    cur.execute("SELECT id, district FROM police_stations")
    stations = cur.fetchall()
    cur.close()
    return stations


def generate_locations(conn, n):
    print(f"Generating {n} locations...")
    rows = []
    for _ in range(n):
        district = random.choice(KARNATAKA_DISTRICTS)
        lat = random.uniform(*LAT_RANGE)
        lng = random.uniform(*LNG_RANGE)
        rows.append((
            uid(), fake.street_name(), fake.address(), district,
            fake.city(), fake.postcode(), lat, lng, "crime_scene",
        ))
    batch_insert(conn, "locations",
                 ["id", "name", "address", "district", "taluk", "pincode", "latitude", "longitude", "location_type"], rows)
    cur = conn.cursor()
    cur.execute("SELECT id, district, latitude, longitude FROM locations")
    locs = cur.fetchall()
    cur.close()
    return locs


def generate_criminals(conn, n):
    print(f"Generating {n} criminals...")
    rows = []
    for i in range(n):
        fir_count = random.randint(0, 8)
        risk = min(100, fir_count * 12 + random.randint(0, 30))
        is_repeat = fir_count >= 3
        rows.append((
            uid(), fake.name(), fake.first_name() if random.random() > 0.5 else None,
            random.randint(18, 65), random.choice(GENDERS),
            hashlib.sha256(str(random.randint(10**11, 10**12 - 1)).encode()).hexdigest(),
            fake.address(), random.choice(KARNATAKA_DISTRICTS),
            None, risk, is_repeat,
            random.choice([None, "Gang A", "Gang B", "Syndicate X"]) if random.random() > 0.85 else None,
            fake.sentence() if random.random() > 0.7 else None,
        ))
    batch_insert(conn, "criminals",
                 ["id", "name", "alias", "age", "gender", "aadhaar_hash", "address", "district",
                  "photo_url", "risk_score", "is_repeat_offender", "gang_affiliation", "modus_operandi"], rows)
    cur = conn.cursor()
    cur.execute("SELECT id FROM criminals")
    ids = [r[0] for r in cur.fetchall()]
    cur.close()
    return ids


def generate_victims(conn, n):
    print(f"Generating {n} victims...")
    rows = []
    for _ in range(n):
        rows.append((
            uid(), fake.name(), random.randint(5, 80), random.choice(GENDERS),
            fake.address(), random.choice(KARNATAKA_DISTRICTS), fake.phone_number(),
        ))
    batch_insert(conn, "victims", ["id", "name", "age", "gender", "address", "district", "contact_phone"], rows)
    cur = conn.cursor()
    cur.execute("SELECT id FROM victims")
    ids = [r[0] for r in cur.fetchall()]
    cur.close()
    return ids


def generate_firs(conn, n, stations, locations):
    print(f"Generating {n} FIRs...")
    rows = []
    fir_ids = []
    year = datetime.now().year
    for i in range(n):
        fid = uid()
        fir_ids.append(fid)
        station = random.choice(stations)
        loc = random.choice(locations)
        crime = random.choice(CRIME_TYPES)
        status = random.choice(STATUSES)
        is_solved = status in ("closed", "convicted", "acquitted")
        incident = fake.date_time_between(start_date="-3y", end_date="now")
        rows.append((
            fid, f"FIR/{station[1][:3]}/{year}/{i+1:06d}",
            station[0], crime, status, random.choice(PRIORITIES),
            f"{crime.replace('_', ' ').title()} case in {station[1]}",
            fake.paragraph(nb_sentences=4),
            incident, incident + timedelta(hours=random.randint(1, 48)),
            loc[0], None,
            random.sample(["IPC 379", "IPC 420", "IPC 302", "IPC 376", "IPC 323", "IPC 506"], k=random.randint(1, 3)),
            fake.sentence() if random.random() > 0.5 else None,
            is_solved, incident + timedelta(days=random.randint(30, 365)) if is_solved else None,
        ))
        if len(rows) >= 10000:
            batch_insert(conn, "fir",
                         ["id", "fir_number", "station_id", "crime_type", "status", "priority", "title",
                          "description", "incident_date", "registered_date", "location_id",
                          "investigating_officer_id", "ipc_sections", "summary", "is_solved", "solved_date"], rows)
            rows = []
            print(f"  ... {i+1}/{n} FIRs inserted")
    if rows:
        batch_insert(conn, "fir",
                     ["id", "fir_number", "station_id", "crime_type", "status", "priority", "title",
                      "description", "incident_date", "registered_date", "location_id",
                      "investigating_officer_id", "ipc_sections", "summary", "is_solved", "solved_date"], rows)
    return fir_ids


def generate_relationships(conn, fir_ids, criminal_ids, victim_ids):
    print("Generating FIR-criminal and FIR-victim relationships...")
    fc_rows, fv_rows = [], []
    for fid in fir_ids:
        for cid in random.sample(criminal_ids, k=random.randint(1, min(3, len(criminal_ids)))):
            fc_rows.append((uid(), fid, cid, random.choice(["accused", "suspect", "witness"])))
        for vid in random.sample(victim_ids, k=random.randint(0, min(2, len(victim_ids)))):
            fv_rows.append((uid(), fid, vid))
        if len(fc_rows) >= 50000:
            batch_insert(conn, "fir_criminals", ["id", "fir_id", "criminal_id", "role"], fc_rows)
            fc_rows = []
        if len(fv_rows) >= 50000:
            batch_insert(conn, "fir_victims", ["id", "fir_id", "victim_id"], fv_rows)
            fv_rows = []
    if fc_rows:
        batch_insert(conn, "fir_criminals", ["id", "fir_id", "criminal_id", "role"], fc_rows)
    if fv_rows:
        batch_insert(conn, "fir_victims", ["id", "fir_id", "victim_id"], fv_rows)


def generate_assets(conn, criminal_ids):
    n_v = COUNTS["vehicles"]
    n_p = COUNTS["phones"]
    n_b = COUNTS["bank_accounts"]
    print(f"Generating {n_v} vehicles, {n_p} phones, {n_b} bank accounts...")

    v_rows, p_rows, b_rows = [], [], []
    account_ids = []

    for i in range(n_v):
        owner = random.choice(criminal_ids) if random.random() > 0.3 else None
        v_rows.append((
            uid(), f"KA-{random.randint(10,99)}-{chr(random.randint(65,90))}{chr(random.randint(65,90))}-{random.randint(1000,9999)}",
            random.choice(VEHICLE_MAKES), fake.word().title(), random.choice(["White", "Black", "Red", "Blue", "Silver"]),
            random.choice(["Car", "Motorcycle", "Auto", "Truck"]), owner, random.random() > 0.95,
        ))
        if len(v_rows) >= 10000:
            batch_insert(conn, "vehicles",
                         ["id", "registration_number", "make", "model", "color", "vehicle_type", "owner_criminal_id", "is_stolen"], v_rows)
            v_rows = []

    for i in range(n_p):
        owner = random.choice(criminal_ids) if random.random() > 0.2 else None
        p_rows.append((
            uid(), f"+91{random.randint(7000000000, 9999999999)}",
            f"{random.randint(10**14, 10**15-1)}", random.choice(["Jio", "Airtel", "Vi", "BSNL"]),
            owner, True,
        ))
        if len(p_rows) >= 10000:
            batch_insert(conn, "phones", ["id", "phone_number", "imei", "operator", "owner_criminal_id", "is_active"], p_rows)
            p_rows = []

    for i in range(n_b):
        aid = uid()
        account_ids.append(aid)
        owner = random.choice(criminal_ids) if random.random() > 0.25 else None
        b_rows.append((
            aid, str(random.randint(10**10, 10**12 - 1)),
            f"{random.choice(['SBIN', 'HDFC', 'ICIC', 'UTIB', 'CNRB'])}{random.randint(10000, 99999)}",
            random.choice(BANKS), fake.name(), owner, random.random() > 0.9,
        ))
        if len(b_rows) >= 10000:
            batch_insert(conn, "bank_accounts",
                         ["id", "account_number", "ifsc_code", "bank_name", "account_holder_name", "owner_criminal_id", "is_flagged"], b_rows)
            b_rows = []

    if v_rows:
        batch_insert(conn, "vehicles",
                     ["id", "registration_number", "make", "model", "color", "vehicle_type", "owner_criminal_id", "is_stolen"], v_rows)
    if p_rows:
        batch_insert(conn, "phones", ["id", "phone_number", "imei", "operator", "owner_criminal_id", "is_active"], p_rows)
    if b_rows:
        batch_insert(conn, "bank_accounts",
                     ["id", "account_number", "ifsc_code", "bank_name", "account_holder_name", "owner_criminal_id", "is_flagged"], b_rows)

    # Transactions
    print("Generating transactions...")
    tx_rows = []
    fir_cur = conn.cursor()
    fir_cur.execute("SELECT id FROM fir LIMIT 5000")
    fir_sample = [r[0] for r in fir_cur.fetchall()]
    fir_cur.close()

    for _ in range(min(200000, len(account_ids) * 4)):
        fa, ta = random.sample(account_ids, 2)
        amount = Decimal(str(round(random.uniform(100, 5000000), 2)))
        is_susp = random.random() > 0.92
        tx_rows.append((
            uid(), fa, ta, amount,
            fake.date_time_between(start_date="-1y", end_date="now"),
            random.choice(["NEFT", "RTGS", "IMPS", "UPI"]),
            f"TXN{random.randint(10**8, 10**10)}",
            is_susp, "Unusual transaction pattern" if is_susp else None,
            random.choice(fir_sample) if is_susp and fir_sample else None,
        ))
        if len(tx_rows) >= 10000:
            batch_insert(conn, "transactions",
                         ["id", "from_account_id", "to_account_id", "amount", "transaction_date",
                          "transaction_type", "reference_number", "is_suspicious", "suspicion_reason", "fir_id"], tx_rows)
            tx_rows = []
    if tx_rows:
        batch_insert(conn, "transactions",
                     ["id", "from_account_id", "to_account_id", "amount", "transaction_date",
                      "transaction_type", "reference_number", "is_suspicious", "suspicion_reason", "fir_id"], tx_rows)

    return account_ids


def generate_evidence(conn, fir_ids):
    print("Generating evidence...")
    rows = []
    ev_types = ["physical", "digital", "documentary", "forensic", "witness_statement", "cctv"]
    for fid in random.sample(fir_ids, k=min(len(fir_ids), int(len(fir_ids) * 0.6))):
        for _ in range(random.randint(1, 4)):
            rows.append((uid(), fid, random.choice(ev_types), fake.sentence(), fake.date_time_between(start_date="-2y", end_date="now"), None, None, random.random() > 0.3))
        if len(rows) >= 10000:
            batch_insert(conn, "evidence", ["id", "fir_id", "evidence_type", "description", "collected_date", "collected_by", "file_url", "is_verified"], rows)
            rows = []
    if rows:
        batch_insert(conn, "evidence", ["id", "fir_id", "evidence_type", "description", "collected_date", "collected_by", "file_url", "is_verified"], rows)


def setup_users(conn):
    print("Setting up demo users...")
    admin_hash = pwd_context.hash("Admin@123")
    users = [
        ("00000000-0000-0000-0000-000000000001", "admin", "admin@surakshai.gov.in", admin_hash, "System Administrator", "admin", "ADMIN-001"),
        (uid(), "investigator1", "inv@surakshai.gov.in", pwd_context.hash("Investigator@123"), "Ravi Kumar", "investigator", "INV-001"),
        (uid(), "officer1", "officer@surakshai.gov.in", pwd_context.hash("Officer@123"), "Priya Sharma", "officer", "OFF-001"),
        (uid(), "supervisor1", "sup@surakshai.gov.in", pwd_context.hash("Supervisor@123"), "Anil Reddy", "supervisor", "SUP-001"),
    ]
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE username != 'admin' OR id != '00000000-0000-0000-0000-000000000001'")
    cur.execute("UPDATE users SET password_hash = %s WHERE username = 'admin'", (admin_hash,))
    for u in users[1:]:
        cur.execute(
            "INSERT INTO users (id, username, email, password_hash, full_name, role, badge_number, station_id) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, '00000000-0000-0000-0000-000000000001') ON CONFLICT (username) DO NOTHING",
            (*u,),
        )
    conn.commit()
    cur.close()


def main():
    print("=" * 60)
    print("SurakshAI Data Generator")
    print("=" * 60)
    print(f"Target counts: {COUNTS}")

    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False

    try:
        setup_users(conn)
        stations = generate_stations(conn, COUNTS["stations"])
        locations = generate_locations(conn, min(COUNTS["firs"], 50000))
        criminal_ids = generate_criminals(conn, COUNTS["criminals"])
        victim_ids = generate_victims(conn, COUNTS["victims"])
        fir_ids = generate_firs(conn, COUNTS["firs"], stations, locations)
        generate_relationships(conn, fir_ids, criminal_ids, victim_ids)
        generate_assets(conn, criminal_ids)
        generate_evidence(conn, fir_ids)
        conn.commit()
        print("\nData generation complete!")
        print(f"  Stations: {COUNTS['stations']}")
        print(f"  FIRs: {COUNTS['firs']}")
        print(f"  Criminals: {COUNTS['criminals']}")
        print(f"  Victims: {COUNTS['victims']}")
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
