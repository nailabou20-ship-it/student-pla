# Student Information Platform

**ESGEN â€” Master in Data Management**
A web platform where students fill in their information through a form, and
where the administrator views, searches and exports the records.

---

## 1. Quick start (one click)

Two files do the job for you:

| File | What it does |
|---|---|
| **`launcher.bat`** | Prepares everything and starts the server. **Double-click it.** |
| `stop.bat` | Stops the server if the launcher window was closed by mistake. |

**Double-click `launcher.bat`** and it will:

1. check that Python is installed,
2. create the virtual environment `.venv` (only the first time),
3. install Django (only the first time),
4. create the database `db.sqlite3` (the tables),
5. create the administrator account **admin / admin123**,
6. add 5 demo students (only if the database is empty),
7. start the server and **open your browser** on <http://127.0.0.1:8000/>.

> The launcher is safe to run as many times as you want: each step checks
> whether it is already done and skips it.
>
> Press **CTRL + C** in the launcher window to stop the server.

---

## 2. The commands to run (Windows)

Open the **PowerShell** in the folder `C:\Users\Naila\Desktop\project`
(the folder that contains `manage.py`).

### Step 1 â€” Create the virtual environment (only once)

```powershell
python -m venv .venv
```

A virtual environment is an isolated box that contains the packages of this
project only. It does not modify the Python installed on your computer.

### Step 2 â€” Activate it

```powershell
.\.venv\Scripts\Activate.ps1
```

Your prompt now starts with `(.venv)`. If PowerShell refuses (execution
policy), run this command once:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 3 â€” Install Django

```powershell
pip install -r requirements.txt
```

### Step 4 â€” Create the database (the tables)

```powershell
python manage.py migrate
```

This creates the file `db.sqlite3` (a SQLite database = a file, no server
needed).

### Step 5 â€” Create the administrator account

```powershell
python manage.py createsuperuser
```

Answer the questions (username, email, password). The account created during
this build is: **admin / admin123** â€” change the password for a real use.

### Step 6 â€” (Optional) Add a few demo students

```powershell
python manage.py seed_students
```

### Step 7 â€” Start the server

```powershell
python manage.py runserver
```

Then open in the browser:

| Page | Address |
|---|---|
| The list of the students | <http://127.0.0.1:8000/> |
| The registration form | <http://127.0.0.1:8000/add/> |
| The CSV export | <http://127.0.0.1:8000/export/csv/> |
| The administration | <http://127.0.0.1:8000/admin/> |

To stop the server press **Ctrl + C**.

### Step 8 â€” Run the automatic tests

```powershell
python manage.py test
```

Result: `Ran 14 tests ... OK`.

> **Useful commands**
> - `python manage.py check` â€” checks that the project has no problem.
> - `python manage.py makemigrations students` â€” after changing the model.
> - `python manage.py shell` â€” a Python console with the database available.

---

## 3. The folder structure

```
project/
â”œâ”€â”€ launcher.bat                # DOUBLE-CLICK THIS to start the project
â”œâ”€â”€ stop.bat                    # stops the server if needed
â”œâ”€â”€ manage.py                   # the main command of Django
â”œâ”€â”€ requirements.txt            # the packages needed
â”œâ”€â”€ db.sqlite3                  # the database (created by migrate)
â”œâ”€â”€ student_portal/             # the PROJECT (the configuration)
â”‚   â”œâ”€â”€ settings.py             # SQLite, applications, time zone
â”‚   â”œâ”€â”€ urls.py                 # the routes of the project
â”‚   â”œâ”€â”€ asgi.py  /  wsgi.py     # the servers
â”œâ”€â”€ students/                   # the APP (the code of the platform)
â”‚   â”œâ”€â”€ models.py               # the Student table + the rules
â”‚   â”œâ”€â”€ forms.py                # the form + the friendly messages
â”‚   â”œâ”€â”€ views.py                # the pages (list, form, export)
â”‚   â”œâ”€â”€ urls.py                 # the routes of the app
â”‚   â”œâ”€â”€ admin.py                # the administration
â”‚   â”œâ”€â”€ validators.py           # the rules written ONCE for model + form
â”‚   â”œâ”€â”€ exporters.py            # the CSV file
â”‚   â”œâ”€â”€ tests.py                # the 6 rules tested automatically
â”‚   â”œâ”€â”€ migrations/             # the history of the database
â”‚   â”œâ”€â”€ management/commands/
â”‚   â”‚   â””â”€â”€ seed_students.py    # the demo data command
â”‚   â”œâ”€â”€ templates/students/     # base.html, form.html, list.html
â”‚   â””â”€â”€ static/students/
â”‚       â””â”€â”€ style.css           # the simple style sheet
â””â”€â”€ README.md
```

---

## 4. How the rules are applied

The most important idea of this project:

> **The rules are written ONCE in `students/validators.py` and are called
> from BOTH the model and the form.**

| # | Rule | Where it is checked | Example of message |
|---|---|---|---|
| 1 | **Completeness** | every field is required (no `blank=True`) | "The email address is required." |
| 2 | **Validity** | `validators=[...]` on the fields | "Enter a valid email address." |
| 3 | **Accuracy** | `validate_date_of_birth()` | "The date of birth cannot be in the future." |
| 4 | **Consistency** | `normalise_*()` in `Model.clean()` | (fixed silently) |
| 5 | **Uniqueness** | `unique=True` + `validate_unique()` | "The Student ID ST202501 is already registered." |
| 6 | **Timeliness** | `auto_now_add` / `auto_now` | (automatic) |

**Why the model AND the form?**
The *form* protects the user: it shows the message right under the faulty
field. The *model* protects the data: even if somebody writes directly in the
Django shell or in the admin, `Model.save()` calls `full_clean()` and refuses
to save an invalid record.

**Django's order of validation** (important to understand):
`full_clean()` runs `clean_fields()` (the format of each field) â†’ `clean()`
(the clean-up of the values) â†’ `validate_unique()` (the duplicates). Because of
this, `clean()` in the model only *cleans* the values and never repeats a
check that `clean_fields()` has already done â€” otherwise the user would see
the same message twice.

---

## 5. The 6 invalid test entries (one per rule)

All of them are already written in `students/tests.py` and can be checked with
`python manage.py test`. The base record used is:

| Field | Value |
|---|---|
| Student ID | `ST202501` |
| First name | `Ahmed` |
| Last name | `Benali` |
| Date of birth | `2003-05-10` (23 years old) |
| Email | `ahmed.benali@esgen.dz` |
| Phone | `0555123456` |
| Wilaya | `16` (Alger) |
| Specialty | `Management` |
| Average | `15.50` |
| Consent | ticked |

### Entry 1 â€” Rule 1: Completeness (the email is empty)

```
email = ""            (the field is left empty)
```

**Expected error message** (under the field *Email*):

> The email address is required.

**Same rule, the consent box not ticked:**

```
consent = False
```

**Expected error message** (under the *Consent* box):

> You must give your consent to the processing of your personal data.

### Entry 2 â€” Rule 2: Validity (the email is malformed)

```
email = "ahmed.benali(at)esgen.dz"
```

**Expected error message** (under the field *Email*):

> Enter a valid email address.

**The same rule, the three other format checks:**

| Invalid value | Field | Expected error message |
|---|---|---|
| `ST2501` | Student ID | Student ID must be written as ST followed by 6 digits (example: ST202501). |
| `0123456789` | Phone | The phone number must be a valid Algerian mobile: 05, 06 or 07 followed by 8 digits (example: 0555123456). |
| `25` | Average | The baccalaureate average must be between 0 and 20. |

### Entry 3 â€” Rule 3: Accuracy (the date of birth is in the future)

```
date_of_birth = tomorrow's date
```

**Expected error message** (under the field *Date of birth*):

> The date of birth cannot be in the future.

**The same rule, the age is out of the range** (10 years old and 70 years old):

> The age must be between 17 and 60 years (the given date of birth means 10 years old).

### Entry 4 â€” Rule 4: Consistency (the values are not clean)

```
student_id = "  st202502  "
first_name = "  ahmed   ben  "
last_name  = "  BENALI  "
email      = "  AHMED.BENALI@ESGEN.DZ  "
phone      = "0555 12 34 56"
```

**Expected result:** the record is **accepted** and the values are stored
cleaned (no error message, this rule fixes the data silently):

| Field | Stored value |
|---|---|
| Student ID | `ST202502` |
| First name | `Ahmed Ben` |
| Last name | `Benali` |
| Email | `ahmed.benali@esgen.dz` |
| Phone | `0555123456` |

**And a value that is not in the fixed lists** (`wilaya = "99"`):

> Please choose a wilaya from the list.

### Entry 5 â€” Rule 5: Uniqueness (the Student ID already exists)

```
student_id = "ST202501"     (already registered by another student)
email      = "another.email@esgen.dz"    (a different email, to isolate the check)
```

**Expected error message** (under the field *Student ID*):

> The Student ID ST202501 is already registered.

**And the same rule with the email** (a different ID, the same email):

> The email ahmed.benali@esgen.dz is already registered.

### Entry 6 â€” Rule 6: Timeliness (the dates)

This rule cannot fail: the dates are written by Django itself.

**Expected result:**

- `created_at` = the moment of the first registration (it never changes).
- `updated_at` = the moment of the last modification (it moves forward at
  every save).

**How to check it in the shell:**

```powershell
python manage.py shell
```

```python
from students.models import Student
s = Student.objects.get(student_id="ST202501")
print(s.created_at, s.updated_at)
```

---

## 6. The administration

<http://127.0.0.1:8000/admin/> â†’ *Students â†’ Students*

| Feature | How it is configured |
|---|---|
| Columns shown | `list_display` in `admin.py` |
| Search by ID, name, email, phone | `search_fields` |
| Filters by wilaya, specialty, consent, date | `list_filter` |
| Export to CSV | the action `export_as_csv` (select the rows, then choose the action) |

The public page also has a search box and the two filters (wilaya and
specialty), plus the button **Export to CSV**.

---

## 7. The data of the platform

| Field | Type | Rule |
|---|---|---|
| Student ID | text, 9 characters | `ST` + 6 digits, unique |
| First name | text | required, capitalised |
| Last name | text | required, capitalised |
| Date of birth | date | not in the future, age 17 â†’ 60 |
| Email | text | valid email, lower case, unique |
| Phone | text | Algerian mobile 05/06/07 + 8 digits |
| Wilaya | dropdown | one of the 58 wilayas of Algeria |
| Specialty | dropdown | one of the 14 specialties of the school |
| Baccalaureate average | number | between 0 and 20 |
| Consent | checkbox | must be ticked |
| created_at | date/time | automatic (Django) |
| updated_at | date/time | automatic (Django) |

> The list of the wilayas uses the official numbering in force since 1984
> (01 Adrar â€¦ 58 El Menfiaa). The list of the specialties is in
> `students/validators.py` (`SPECIALTIES`) and can be changed freely.

