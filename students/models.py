"""
The Student model: the table that stores the information of the platform.

The model is the LAST LINE OF DEFENCE. Even if somebody bypasses the web
form (Django admin, Django shell, a script...), `save()` calls `full_clean()`
so an invalid record can never reach the database.

Mapping of the 6 data-quality rules inside this file:
    1. COMPLETENESS -> every field is required (no `blank=True`, no `null=True`).
    2. VALIDITY     -> `validators=[...]` on the fields (email, phone,
                        Student ID, average between 0 and 20).
    3. ACCURACY     -> `validate_date_of_birth()` on the `date_of_birth` field.
    4. CONSISTENCY  -> the `normalise_*()` helpers inside `clean()`.
    5. UNIQUENESS   -> `unique=True` in the database + a clear message in
                        `validate_unique()`.
    6. TIMELINESS   -> `created_at` (auto_now_add) and `updated_at` (auto_now).

IMPORTANT NOTE ABOUT THE ERRORS
    Django's `full_clean()` runs three steps in this order:
        1. `clean_fields()`  -> checks the format of each field (the validators)
        2. `clean()`         -> the consistency clean-up written below
        3. `validate_unique()` -> checks the duplicates
    Because step 1 already produces the error messages, `clean()` must NOT
    check the same things again, otherwise the user would see the same
    message twice. That is why `clean()` only *normalises* the values here.
"""

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .validators import (
    BAC_AVERAGE_ERROR,
    BAC_AVERAGE_MAX,
    BAC_AVERAGE_MIN,
    SPECIALTY_CHOICES,
    WILAYA_CHOICES,
    WILAYA_NAMES,
    calculate_age,
    normalise_email,
    normalise_name,
    normalise_phone,
    normalise_student_id,
    validate_algerian_phone,
    validate_consent,
    validate_date_of_birth,
    validate_student_id,
)


class Student(models.Model):
    """One row of the table = one student."""

    # ------------------------------------------------------------------
    # IDENTITY
    # ------------------------------------------------------------------
    # RULE 2 (validity) + RULE 5 (uniqueness).
    # The validator checks the format "ST + 6 digits".
    # NOTE: the column is 20 characters wide (and not 9) because Django checks
    # the length BEFORE the spaces are removed. A user who types " st202501 "
    # writes 11 characters, and the cleaned value "ST202501" has 9. The
    # validator guarantees that only a 9-character value is ever stored.
    student_id = models.CharField(
        "Student ID",
        max_length=20,
        unique=True,
        validators=[validate_student_id],
        help_text="Format ST + 6 digits, for example ST202501.",
    )

    # RULE 1: required (no `blank=True`). Django says "This field is required."
    first_name = models.CharField("First name", max_length=60)
    last_name = models.CharField("Last name", max_length=60)

    # RULE 3 (accuracy): the date cannot be in the future and the age must be
    # between 17 and 60. The validator produces the message.
    date_of_birth = models.DateField(
        "Date of birth",
        validators=[validate_date_of_birth],
    )

    # RULE 2 (the format, checked by EmailField) + RULE 5 (uniqueness).
    email = models.EmailField("Email", max_length=254, unique=True)

    # RULE 2: Algerian mobile number = 05, 06 or 07 + 8 digits.
    # NOTE: same as above, the column is wider than the cleaned value
    # ("0555 12 34 56" has 13 characters, "0555123456" has 10).
    phone = models.CharField(
        "Phone",
        max_length=20,
        validators=[validate_algerian_phone],
        help_text="Algerian mobile: 05, 06 or 07 followed by 8 digits.",
    )

    # RULE 4: the value must come from the fixed list of 58 wilayas.
    # `error_messages` replaces Django's ugly default message by a clear one.
    wilaya = models.CharField(
        "Wilaya",
        max_length=40,
        choices=WILAYA_CHOICES,
        error_messages={
            "invalid_choice": "Please choose a wilaya from the list.",
        },
    )

    # RULE 4: the value must come from the fixed list of specialties.
    specialty = models.CharField(
        "Specialty",
        max_length=60,
        choices=SPECIALTY_CHOICES,
        error_messages={
            "invalid_choice": "Please choose a specialty from the list.",
        },
    )

    # RULE 2: the average is a mark out of 20.
    bac_average = models.DecimalField(
        "Baccalaureate average",
        max_digits=4,
        decimal_places=2,
        validators=[
            MinValueValidator(BAC_AVERAGE_MIN, message=BAC_AVERAGE_ERROR),
            MaxValueValidator(BAC_AVERAGE_MAX, message=BAC_AVERAGE_ERROR),
        ],
        help_text="Between 0 and 20.",
    )

    # RULE 1: the box must be ticked. `validate_consent` gives the message.
    consent = models.BooleanField(
        "I consent to the processing of my personal data",
        validators=[validate_consent],
    )

    # ------------------------------------------------------------------
    # RULE 6 - TIMELINESS: filled in automatically by Django, never by the user.
    # ------------------------------------------------------------------
    created_at = models.DateTimeField("Created at", auto_now_add=True)
    updated_at = models.DateTimeField("Updated at", auto_now=True)

    # ------------------------------------------------------------------
    # OPTIONS
    # ------------------------------------------------------------------
    class Meta:
        # The newest records are shown first.
        ordering = ["-created_at"]
        verbose_name = "Student"
        verbose_name_plural = "Students"

    # ------------------------------------------------------------------
    # DISPLAY HELPERS
    # ------------------------------------------------------------------
    def __str__(self):
        """Shown in the admin list and in the shell: ST202501 - Ahmed Benali."""
        return f"{self.student_id} - {self.full_name}"

    @property
    def full_name(self):
        """The first name and the last name together."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def age(self):
        """The current age of the student, calculated from the date of birth."""
        return calculate_age(self.date_of_birth)

    @property
    def wilaya_name(self):
        """The name of the wilaya without its code (e.g. "Alger")."""
        return WILAYA_NAMES.get(self.wilaya, self.wilaya)

    # ------------------------------------------------------------------
    # RULE 4 - CONSISTENCY: clean the text before storing it
    # ------------------------------------------------------------------
    def clean(self):
        """Remove the extra spaces and fix the case of the text fields.

        `clean()` is called by `full_clean()`, and therefore by `save()` and
        by every ModelForm built on this model. It never raises an error
        here: the format of the values is already checked by `clean_fields()`
        (see the note at the top of this file).
        """
        super().clean()

        # "  ahmed   ben  " -> "Ahmed Ben"
        if self.first_name:
            self.first_name = normalise_name(self.first_name)
        if self.last_name:
            self.last_name = normalise_name(self.last_name)

        # "  Ahmed.BEN@ESGEN.DZ " -> "ahmed.ben@esgen.dz"
        if self.email:
            self.email = normalise_email(self.email)

        # "0555 12 34 56" -> "0555123456"
        if self.phone:
            self.phone = normalise_phone(self.phone)

        # " st202501 " -> "ST202501"
        if self.student_id:
            self.student_id = normalise_student_id(self.student_id)

        # The wilaya and the specialty are already restricted to the fixed
        # lists by the `choices` option, so only the spaces are removed.
        if self.wilaya:
            self.wilaya = str(self.wilaya).strip()
        if self.specialty:
            self.specialty = str(self.specialty).strip()

    # ------------------------------------------------------------------
    # RULE 5 - UNIQUENESS: a clear message for the duplicates
    # ------------------------------------------------------------------
    def validate_unique(self, exclude=None):
        """Check that the Student ID and the email are not used twice.

        Django's default message ("Student with this Student ID already
        exists.") is replaced by a message that tells the user exactly which
        value is duplicated.
        """
        exclude = exclude or []
        errors = {}

        # --- the Student ID ---
        if "student_id" not in exclude and self.student_id:
            duplicates = Student.objects.filter(student_id=self.student_id)
            if self.pk:
                # When we EDIT a record, the record itself is not a duplicate.
                duplicates = duplicates.exclude(pk=self.pk)
            if duplicates.exists():
                errors["student_id"] = ValidationError(
                    f"The Student ID {self.student_id} is already registered.",
                    code="unique",
                )

        # --- the email ---
        if "email" not in exclude and self.email:
            duplicates = Student.objects.filter(email=self.email)
            if self.pk:
                duplicates = duplicates.exclude(pk=self.pk)
            if duplicates.exists():
                errors["email"] = ValidationError(
                    f"The email {self.email} is already registered.",
                    code="unique",
                )

        if errors:
            raise ValidationError(errors)

    # ------------------------------------------------------------------
    # The safety net: nothing invalid can be saved.
    # ------------------------------------------------------------------
    def save(self, *args, **kwargs):
        """Validate the record before writing it to the database."""
        # full_clean() runs clean_fields(), clean() and validate_unique().
        self.full_clean()
        return super().save(*args, **kwargs)
