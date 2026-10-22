"""
Shared data-quality helpers for the `students` app.

WHY does this file exist?
    Every rule of the specification must be applied in TWO different places:
        1. in the MODEL  -> so nobody can insert bad data through the admin,
                            the Django shell, or a future API.
        2. in the FORM   -> so the student sees a friendly message right next
                            to the field he/she got wrong.
    Writing the same rule twice would be a maintenance risk, so the *logic*
    lives here (this file) and both the model and the form simply call it.

Each helper follows the same contract:
    * it takes the RAW value coming from the user,
    * it CLEANS it (removes extra spaces, fixes the case, ...) when needed,
    * it raises `ValidationError` with a readable message when the value is
      not acceptable.
"""

import re
from datetime import date

from django.core.exceptions import ValidationError


# ===========================================================================
# RULE 4 - CONSISTENCY: the two FIXED reference lists
# ===========================================================================

# The 58 Algerian wilayas, using the official numbering in force since 1984.
# Format: (code, name). We store the CODE (e.g. "16") in the database because
# a code is a stable identifier, while a name can be spelled in several ways.
WILAYAS = [
    ("01", "Adrar"),
    ("02", "Chlef"),
    ("03", "Laghouat"),
    ("04", "Oum El Bouaghi"),
    ("05", "Batna"),
    ("06", "Bejaia"),
    ("07", "Biskra"),
    ("08", "Bechar"),
    ("09", "Blida"),
    ("10", "Bouira"),
    ("11", "Tamanrasset"),
    ("12", "Tebessa"),
    ("13", "Tlemcen"),
    ("14", "Tiaret"),
    ("15", "Tizi Ouzou"),
    ("16", "Alger"),
    ("17", "Djelfa"),
    ("18", "Jijel"),
    ("19", "Setif"),
    ("20", "Saida"),
    ("21", "Skikda"),
    ("22", "Sidi Bel Abbes"),
    ("23", "Annaba"),
    ("24", "Guelma"),
    ("25", "Constantine"),
    ("26", "Medea"),
    ("27", "Mostaganem"),
    ("28", "M'Sila"),
    ("29", "Mascara"),
    ("30", "Ouargla"),
    ("31", "Oran"),
    ("32", "El Bayadh"),
    ("33", "Illizi"),
    ("34", "Bordj Bou Arreridj"),
    ("35", "Boumerdes"),
    ("36", "El Tarf"),
    ("37", "Tindouf"),
    ("38", "Tissemsilt"),
    ("39", "El Oued"),
    ("40", "Khenchela"),
    ("41", "Souk Ahras"),
    ("42", "Tipaza"),
    ("43", "Mila"),
    ("44", "Ain Defla"),
    ("45", "Naama"),
    ("46", "Ain Temouchent"),
    ("47", "Ghardaia"),
    ("48", "Relizane"),
    ("49", "Timimoun"),
    ("50", "Bordj Badji Mokhtar"),
    ("51", "Ouled Djellal"),
    ("52", "Beni Abbes"),
    ("53", "In Salah"),
    ("54", "In Guezzam"),
    ("55", "Touggourt"),
    ("56", "Djanet"),
    ("57", "El M'Ghair"),
    ("58", "El Menfiaa"),
]

# Django needs a list of (value, label) tuples to build a dropdown.
# We show "16 - Alger" so the user sees both the code and the name.
WILAYA_CHOICES = [(code, f"{code} - {name}") for code, name in WILAYAS]

# The specialties taught at the school (Management & Digital Economy).
SPECIALTIES = [
    "Management",
    "Marketing",
    "Digital Marketing",
    "Accounting and Finance",
    "Banking and Insurance",
    "Business Law",
    "Human Resources Management",
    "Logistics and Transport",
    "International Business",
    "Information Systems",
    "Data Management and Analytics",
    "Tourism and Hotel Management",
    "Public Finance",
    "Entrepreneurship and Innovation",
]
SPECIALTY_CHOICES = [(name, name) for name in SPECIALTIES]

# A `set` behaves like a list but answers "is this value inside me?" instantly.
# We use it to check a value against the fixed lists.
WILAYA_CODES = {code for code, _ in WILAYAS}
SPECIALTY_NAMES = set(SPECIALTIES)

# A quick way to display the name of a wilaya from its code.
WILAYA_NAMES = {code: name for code, name in WILAYAS}


# ===========================================================================
# RULE 2 - VALIDITY: the regular expressions
# ===========================================================================

# Student ID = "ST" + exactly 6 digits  ->  ST202501
# IGNORECASE is used because the *normalisation* step turns "st202501" into
# "ST202501" anyway; the regex just has to accept both spellings.
STUDENT_ID_REGEX = re.compile(r"^ST\d{6}$", re.IGNORECASE)

# Algerian mobile number = 05 / 06 / 07 followed by exactly 8 digits.
# Spaces and dots are tolerated here and removed by `normalise_phone`.
PHONE_REGEX = re.compile(r"^(05|06|07)\d{8}$")

# Age limits for a student (RULE 3 - ACCURACY).
MIN_AGE = 17
MAX_AGE = 60

# The baccalaureate average is a mark out of 20 (RULE 2 - VALIDITY).
BAC_AVERAGE_MIN = 0
BAC_AVERAGE_MAX = 20
BAC_AVERAGE_ERROR = "The baccalaureate average must be between 0 and 20."


# ===========================================================================
# RULE 4 - CONSISTENCY: the normalisation helpers
# ===========================================================================

def normalise_student_id(value):
    """Remove the surrounding spaces and put the ID in upper case.

    " st202501 " -> "ST202501"
    """
    if value is None:
        return value
    return str(value).strip().upper()


def normalise_name(value):
    """Remove the EXTRA spaces and capitalise the first letter of every word.

    "  ahmed   ben  "  -> "Ahmed Ben"
    "  mohamed amine " -> "Mohamed Amine"
    """
    if value is None:
        return value
    # split() without argument removes every kind of space (space, tab, ...)
    # and " ".join(...) puts a single space back between the words.
    cleaned = " ".join(str(value).split())
    # .title() writes the first letter of each word in capitals.
    return cleaned.title()


def normalise_email(value):
    """Remove the surrounding spaces and write the email in lower case.

    "  Ahmed.BEN@ESGEN.DZ " -> "ahmed.ben@esgen.dz"
    """
    if value is None:
        return value
    return str(value).strip().lower()


def normalise_phone(value):
    """Remove every space, dot and dash from the phone number.

    "0555 12 34 56" -> "0555123456"
    """
    if value is None:
        return value
    return re.sub(r"[\s.\-]", "", str(value).strip())


# ===========================================================================
# RULE 2 - VALIDITY: the format checkers
# ===========================================================================

def validate_student_id(value):
    """Check the format of the Student ID: ST + 6 digits."""
    candidate = normalise_student_id(value)
    if not STUDENT_ID_REGEX.match(candidate or ""):
        raise ValidationError(
            "Student ID must be written as ST followed by 6 digits "
            "(example: ST202501).",
            code="invalid_student_id",
        )
    return candidate


def validate_algerian_phone(value):
    """Check the format of the Algerian mobile number: 05/06/07 + 8 digits."""
    candidate = normalise_phone(value)
    if not PHONE_REGEX.match(candidate or ""):
        raise ValidationError(
            "The phone number must be a valid Algerian mobile: 05, 06 or 07 "
            "followed by 8 digits (example: 0555123456).",
            code="invalid_phone",
        )
    return candidate


def validate_wilaya(value):
    """Check that the wilaya belongs to the fixed list of 58 wilayas."""
    candidate = str(value).strip() if value is not None else ""
    if candidate not in WILAYA_CODES:
        raise ValidationError(
            "Please choose a wilaya from the list.",
            code="invalid_wilaya",
        )
    return candidate


def validate_specialty(value):
    """Check that the specialty belongs to the fixed list of specialties."""
    candidate = str(value).strip() if value is not None else ""
    if candidate not in SPECIALTY_NAMES:
        raise ValidationError(
            "Please choose a specialty from the list.",
            code="invalid_specialty",
        )
    return candidate


def validate_bac_average(value):
    """Check that the baccalaureate average is between 0 and 20."""
    if value is None:
        return value
    number = float(value)
    if number < BAC_AVERAGE_MIN or number > BAC_AVERAGE_MAX:
        raise ValidationError(BAC_AVERAGE_ERROR, code="invalid_average")
    return value


def validate_consent(value):
    """Check that the consent box has been ticked (RULE 1 - completeness)."""
    if not value:
        raise ValidationError(
            "You must give your consent to the processing of your personal data.",
            code="consent_required",
        )
    return value


# ===========================================================================
# RULE 3 - ACCURACY: the date of birth
# ===========================================================================

def calculate_age(date_of_birth, today=None):
    """Return the age (in full years) of a person born on `date_of_birth`.

    Example: born 2000-05-10, today 2026-10-21 -> 26 years old.
    """
    if date_of_birth is None:
        return None
    today = today or date.today()
    return (
        today.year
        - date_of_birth.year
        - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    )


def validate_date_of_birth(value):
    """Check the date of birth: not in the future, and an age of 17 to 60."""
    if value is None:
        return value

    today = date.today()

    # (a) the date cannot be in the future
    if value > today:
        raise ValidationError(
            "The date of birth cannot be in the future.",
            code="future_date_of_birth",
        )

    # (b) the age must be between 17 and 60
    age = calculate_age(value, today)
    if age < MIN_AGE or age > MAX_AGE:
        raise ValidationError(
            f"The age must be between {MIN_AGE} and {MAX_AGE} years "
            f"(the given date of birth means {age} years old).",
            code="invalid_age",
        )
    return value
