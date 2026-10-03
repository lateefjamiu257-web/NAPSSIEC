# TrustVote — Credible, Fair & Auditable Election Platform

**TrustVote** is a secure electronic voting and election administration platform built specifically to guarantee free, fair, credible, and verifiable elections for university student unions, faculties, and professional associations.

---

## 🏛️ The 4 Pillars of Credibility & Fairness

1. **One-Time Voter Access Tokens (Zero Double Voting)**:
   - Every eligible voter receives an encrypted, high-entropy unique access token (e.g. `TV-ENG101`).
   - The instant a ballot is validated, the token status is permanently updated to `has_voted = 1` in an atomic database transaction. Any attempt to reuse the token is rejected and flagged in the audit logs.

2. **Cryptographic Secrecy via Decoupled Ballots (Secret Ballot Guarantee)**:
   - When a vote is cast, voter accreditation records are strictly decoupled from ballot records.
   - The ballot table stores only the chosen candidates, timestamp, and a public verification receipt hash.
   - It is mathematically impossible for anyone—even database administrators or committee members—to link a voter's identity to their candidate choices.

3. **Public Ballot Verification Receipts (Individual Verifiability)**:
   - Upon casting a vote, the voter is issued a digital Verification Receipt Hash (e.g. `REC-8F92...`).
   - Any student can enter their receipt hash into the Public Verification Portal (`/verify-receipt`) at any time to verify that their vote is recorded inside the official ballot box and included in the tally.

4. **Immutable Audit Trail Ledger**:
   - Every system event (election status changes, voter authentication attempts, candidate nominations, ballot casting events) is logged in an append-only audit trail with actor name, timestamp, and IP address.

---

## 🚀 Quick Start Guide

### 1. Launch the Server
In PowerShell or Terminal:
```powershell
python run.py
```

The application will initialize the database and start the server at:
- **Public Portal & Landing Page**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Voter Accreditation & Ballot Casting**: [http://127.0.0.1:8000/vote](http://127.0.0.1:8000/vote)
- **Public Receipt Verification**: [http://127.0.0.1:8000/verify-receipt](http://127.0.0.1:8000/verify-receipt)
- **Live Tabulation & Official Results**: [http://127.0.0.1:8000/results](http://127.0.0.1:8000/results)
- **Chairman Command Room**: [http://127.0.0.1:8000/admin/login](http://127.0.0.1:8000/admin/login)

---

## 🧪 Testing Credentials for Electoral Committee

### Chairman Credentials
- **Portal**: [http://127.0.0.1:8000/admin/login](http://127.0.0.1:8000/admin/login)
- **Secret Key**: `Chairman2026!`

### Pre-loaded Sample Voter Tokens (Ready to Cast Ballot)
| Student ID | Full Name | Faculty | Voter Token |
| :--- | :--- | :--- | :--- |
| `AUSU/2022/1001` | Chukwudi Paul Nwosu | Faculty of Engineering | `TV-ENG101` |
| `AUSU/2022/1002` | Aisha Abubakar Sani | Faculty of Social Sciences | `TV-SOC102` |
| `AUSU/2022/1003` | Babatunde John Davies | Faculty of Law | `TV-LAW103` |
| `AUSU/2022/1004` | Maryam Idris Kabir | Faculty of Science | `TV-SCI104` |
| `AUSU/2022/1005` | Emeka Jude Okafor | Faculty of Management Sciences | `TV-MGT105` |
| `AUSU/2022/1006` | Temitope Elizabeth Cole | Faculty of Arts | `TV-ART106` |

---

## 📋 Electoral Lifecycle Phases

The Chairman can switch the election phase at any time from the Command Room:
1. **Draft / Setup**: Configure contested offices and nominate cleared candidates.
2. **Accreditation Only**: Voters can verify their eligibility and token validity.
3. **🟢 Voting Open**: Active balloting open across campus.
4. **🟡 Voting Paused**: Temporary freeze in case of an announcement or inquiry.
5. **🔴 Voting Closed**: Balloting ends; no further votes accepted.
6. **🔵 Results Certified**: Chairman digitally signs and certifies official returns.

---

## 📂 Project Structure

```
trustvote/
├── app/
│   ├── database.py       # SQLite connection, schema, seeding & audit logger
│   ├── models.py         # Pydantic request & validation models
│   ├── security.py       # Token hashing, secret salt & receipt generation
│   ├── main.py           # FastAPI web application & REST endpoints
│   └── templates/        # Responsive Jinja2 UI templates (Tailwind CSS)
│       ├── base.html
│       ├── index.html
│       ├── vote_auth.html
│       ├── ballot.html
│       ├── verify_receipt.html
│       ├── results.html
│       ├── results_locked.html
│       ├── admin_login.html
│       └── admin_dashboard.html
├── sample_voters.csv     # Sample voter roster for bulk import
├── run.py                # Server entry-point
└── README.md             # Documentation
```
