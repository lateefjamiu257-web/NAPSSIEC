import sqlite3
import os
import json
from datetime import datetime
from app.security import hash_token, hash_password

DB_PATH = os.path.join(os.path.dirname(__file__), "trustvote.db")

def configure_napssiec():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Clear existing tables for a clean, customized NAPSSIEC setup
    cursor.execute("DELETE FROM election_settings")
    cursor.execute("DELETE FROM positions")
    cursor.execute("DELETE FROM candidates")
    cursor.execute("DELETE FROM voters")
    cursor.execute("DELETE FROM ballots")
    cursor.execute("DELETE FROM ballot_items")
    cursor.execute("DELETE FROM audit_logs")

    # 1. Update Election Settings for NAPSSIEC & Chairman Jamiu
    default_pass_hash = hash_password("Chairman2026!")
    cursor.execute("""
    INSERT INTO election_settings 
    (id, title, organization, academic_session, status, chairman_name, chairman_password_hash, start_time, end_time, allow_live_results, last_updated)
    VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "NAPSS General Executive Council & Departmental Elections",
        "National Association of Political Science Students (NAPSS) • Department of Political Science",
        "2026/2027 Academic Session",
        "voting_open",
        "Hon. Jamiu (Chairman, NAPSSIEC)",
        default_pass_hash,
        "2026-09-30 08:00:00",
        "2026-09-30 18:00:00",
        1,
        now_iso
    ))

    # 2. Executive Contested Positions for Political Science
    positions = [
        (1, "President", "Chief Executive of NAPSS, leading student union advocacy, departmental representation and policy formulation.", 1, 1),
        (2, "Vice President", "Academic coordinator, head of academic symposiums, career bootcamps and student welfare.", 2, 1),
        (3, "General Secretary", "Chief administrative officer, documentation, official communiques, and executive resolutions.", 3, 1),
        (4, "Public Relations Officer (P.R.O.)", "Voice of NAPSS, chief information officer, media liaison, and student broadcast manager.", 4, 1),
        (5, "Financial Secretary", "Accountant of the association, public finance reports, transparent dues records, and budget audit.", 5, 1),
        (6, "Director of Socials", "Coordinates NAPSS Cultural Week, Annual Political Science Dinner, debate galas, and social mixers.", 6, 1),
        (7, "Director of Sports & Welfare", "Head of Departmental Champions Cup, welfare stipends coordination, and faculty athletic games.", 7, 1),
    ]
    cursor.executemany("""
    INSERT INTO positions (id, title, description, display_order, max_choices)
    VALUES (?, ?, ?, ?, ?)
    """, positions)

    # 3. Political Science Candidates
    candidates = [
        # President
        (1, "Comrade Michael Okon", "The Diplomat", "Faculty of Social Sciences", "Department of Political Science", "400 Level",
         "Strengthening departmental diplomacy, securing international relations internship linkages, and establishing student welfare defense.", "#2563eb", 1),
        (1, "Amina Zahra Bello", "Iron Lady", "Faculty of Social Sciences", "Department of Political Science", "400 Level",
         "Digital resource hub for political research, subsidized departmental study materials, and inclusive women in governance initiatives.", "#7c3aed", 2),
        (1, "Segun Daniel Adeleke", "Policy Architect", "Faculty of Social Sciences", "Department of Political Science", "400 Level",
         "Zero unexplained dues increment, transparent bi-monthly town hall meetings, and renovated departmental seminar library.", "#059669", 3),

        # Vice President
        (2, "Zainab Omotola Hassan", "Zainy Policy", "Faculty of Social Sciences", "Department of Political Science", "300 Level",
         "Annual Political Thought Colloquium, academic peer tutoring groups, and departmental scholarship guide.", "#db2777", 1),
        (2, "Victor Kalu Nnamdi", "VK", "Faculty of Social Sciences", "Department of Political Science", "300 Level",
         "Public policy debate championships, career fairs with civil service and NGOs, and hostel welfare committee.", "#d97706", 2),

        # General Secretary
        (3, "Deborah Temitope Adeyemi", "The Scribe", "Faculty of Social Sciences", "Department of Political Science", "300 Level",
         "Instant digital issuance of departmental clearance certificates and open online archive for all congress resolutions.", "#0284c7", 1),
        (3, "Usman Farouk Abubakar", "Farouk Admin", "Faculty of Social Sciences", "Department of Political Science", "300 Level",
         "Automated departmental SMS/email newsletter, swift handling of student petitions, and seamless congress minutes.", "#4f46e5", 2),

        # Public Relations Officer (P.R.O.)
        (4, "Samuel Babatunde Alabi", "Voice of NAPSS", "Faculty of Social Sciences", "Department of Political Science", "300 Level",
         "Rebranding NAPSS media presence, interactive podcast on contemporary global politics, and active real-time updates.", "#0891b2", 1),
        (4, "Faith Chidera Okeke", "Clarion Faith", "Faculty of Social Sciences", "Department of Political Science", "300 Level",
         "Departmental digital noticeboard, prompt dissemination of exam timetables, and student feedback channel.", "#ea580c", 2),

        # Financial Secretary
        (5, "Kehinde Badmus", "The Comptroller", "Faculty of Social Sciences", "Department of Political Science", "300 Level",
         "Full quarterly publication of income and expenditures on the student portal, zero financial leakages, and digitized receipting.", "#16a34a", 1),
        (5, "Fatima Sani Mohammed", "Hon. Ledger", "Faculty of Social Sciences", "Department of Political Science", "300 Level",
         "Prudent fiscal allocation for departmental activities, emergency health assistance fund, and accountable dues auditing.", "#ca8a04", 2),

        # Director of Socials
        (6, "Tobi Bakare", "DJ Statesman", "Faculty of Social Sciences", "Department of Political Science", "300 Level",
         "Legendary NAPSS Annual Gala & Awards Night, Cultural Day with foreign embassy guests, and departmental game nights.", "#9333ea", 1),
        (6, "Sandra Ifeoma Eke", "Queen Sandra", "Faculty of Social Sciences", "Department of Political Science", "300 Level",
         "Creative arts exposition, departmental movie screening and policy documentary nights, and networking soirées.", "#ec4899", 2),

        # Director of Sports & Welfare
        (7, "Emeka Chukwu", "Captain Emeka", "Faculty of Social Sciences", "Department of Political Science", "300 Level",
         "Revitalizing the Political Science Football Team (The Diplomats), inter-level football tournament, and gym discounts.", "#15803d", 1),
        (7, "Ahmed Lawal", "Coach Ahmed", "Faculty of Social Sciences", "Department of Political Science", "300 Level",
         "Indoor board games competitions (Chess, Scrabble, Table Tennis), female sports inclusion, and medical first-aid kit.", "#0284c7", 2),
    ]
    cursor.executemany("""
    INSERT INTO candidates (position_id, full_name, nickname, faculty, department, level, manifesto, avatar_color, display_order)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, candidates)

    # 4. Accredited Voters featuring the specific user emails provided!
    test_voters = [
        ("POS/2022/1001", "Jamiu Lateef", "lateefjamiu251@gmail.com", "Faculty of Social Sciences", "Department of Political Science", "NAPSS-JAM1"),
        ("POS/2022/1002", "Azeem Saheed", "saheedazeem4@gmail.com", "Faculty of Social Sciences", "Department of Political Science", "NAPSS-SAH2"),
        ("POS/2022/1003", "Salaudeen Adewale", "adewalesalaudeen0106@gmail.com", "Faculty of Social Sciences", "Department of Political Science", "NAPSS-ADE3"),
        ("POS/2022/1004", "Emmanuel Shields", "manndshields@gmail.com", "Faculty of Social Sciences", "Department of Political Science", "NAPSS-MAN4"),
        # Additional Political Science classmates for complete electorate demonstration
        ("POS/2022/1005", "Chioma Blessing Nwosu", "c.nwosu@pos.edu.ng", "Faculty of Social Sciences", "Department of Political Science", "NAPSS-POS105"),
        ("POS/2022/1006", "Babatunde Idris Bello", "b.bello@pos.edu.ng", "Faculty of Social Sciences", "Department of Political Science", "NAPSS-POS106"),
        ("POS/2022/1007", "Khadijah Maryam Danjuma", "k.danjuma@pos.edu.ng", "Faculty of Social Sciences", "Department of Political Science", "NAPSS-POS107"),
        ("POS/2022/1008", "David Osagie Egharevba", "d.egharevba@pos.edu.ng", "Faculty of Social Sciences", "Department of Political Science", "NAPSS-POS108"),
    ]

    for student_id, name, email, faculty, dept, token in test_voters:
        t_hash = hash_token(token)
        cursor.execute("""
        INSERT INTO voters (student_id, full_name, email, faculty, department, token, token_hash, is_accredited, has_voted, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0, ?)
        """, (student_id, name, email, faculty, dept, token, t_hash, now_iso))

    # Audit Log
    cursor.execute("""
    INSERT INTO audit_logs (timestamp, action, actor, ip_address, details)
    VALUES (?, ?, ?, ?, ?)
    """, (
        now_iso,
        "NAPSSIEC_CONFIGURED",
        "Hon. Jamiu (Chairman, NAPSSIEC)",
        "127.0.0.1",
        "Configured Department of Political Science NAPSS Executive Elections with 7 offices and custom voter roll."
    ))

    conn.commit()
    conn.close()
    print(">>> NAPSSIEC & Political Science election configured successfully!")

if __name__ == "__main__":
    configure_napssiec()
