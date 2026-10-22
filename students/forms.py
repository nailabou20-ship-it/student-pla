"""
The form the student fills in.

THE FORM APPLIES THE SAME RULES AS THE MODEL
    The model protects the data; the form protects the *user experience*:
    it checks the values as soon as the form is submitted and displays a
    readable message right under the faulty field.

    To avoid writing every rule twice, both the model and the form call the
    same helper functions located in `students/validators.py`.

    A Django ModelForm does NOT copy the validators of the model fields into
    the form fields automatically, so we attach them by hand in `__init__`.
"""

from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator

from .models import Student
from .validators import (
    BAC_AVERAGE_ERROR,
    BAC_AVERAGE_MAX,
    BAC_AVERAGE_MIN,
    SPECIALTY_CHOICES,
    WILAYA_CHOICES,
    normalise_email,
    normalise_name,
    normalise_phone,
    normalise_student_id,
    validate_algerian_phone,
    validate_consent,
    validate_date_of_birth,
    validate_student_id,
)

# The message shown when a required field is left empty (RULE 1).
# The key is the name of the field, the value is the message.
REQUIRED_MESSAGES = {
    "student_id": "The Student ID is required.",
    "first_name": "The first name is required.",
    "last_name": "The last name is required.",
    "date_of_birth": "The date of birth is required.",
    "email": "The email address is required.",
    "phone": "The phone number is required.",
    "wilaya": "The wilaya is required.",
    "specialty": "The specialty is required.",
    "bac_average": "The baccalaureate average is required.",
}


class StudentForm(forms.ModelForm):
    """The form of the Student model, with friendly messages."""

    # ------------------------------------------------------------------
    # These three fields are declared by hand to control their message and
    # their look. The other fields are built automatically from the model.
    # ------------------------------------------------------------------
    wilaya = forms.TypedChoiceField(
        choices=WILAYA_CHOICES,
        label="Wilaya",
        error_messages={
            "invalid_choice": "Please choose a wilaya from the list.",
        },
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    specialty = forms.TypedChoiceField(
        choices=SPECIALTY_CHOICES,
        label="Specialty",
        error_messages={
            "invalid_choice": "Please choose a specialty from the list.",
        },
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    consent = forms.BooleanField(
        # `required=False` because the checkbox is not sent by the browser
        # when it is not ticked. The `validate_consent` validator (added
        # below) is the one that complains when the box is left empty.
        required=False,
        label="I consent to the processing of my personal data",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = Student
        # The order of the fields is the order shown on the page.
        fields = [
            "student_id",
            "first_name",
            "last_name",
            "date_of_birth",
            "email",
            "phone",
            "wilaya",
            "specialty",
            "bac_average",
            "consent",
        ]
        widgets = {
            "student_id": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "ST202501"}
            ),
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ahmed"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Benali"}
            ),
            # `type="date"` shows the little calendar of the browser.
            "date_of_birth": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "ahmed.benali@esgen.dz"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "0555123456"}
            ),
            "bac_average": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0", "max": "20"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ------------------------------------------------------------------
        # 1. Attach the validators of the model to the form fields.
        #    (Django does not do it automatically.)
        # ------------------------------------------------------------------
        self.fields["student_id"].validators.append(validate_student_id)
        self.fields["phone"].validators.append(validate_algerian_phone)
        self.fields["date_of_birth"].validators.append(validate_date_of_birth)
        self.fields["consent"].validators.append(validate_consent)
        self.fields["bac_average"].validators.append(
            MinValueValidator(BAC_AVERAGE_MIN, message=BAC_AVERAGE_ERROR)
        )
        self.fields["bac_average"].validators.append(
            MaxValueValidator(BAC_AVERAGE_MAX, message=BAC_AVERAGE_ERROR)
        )

        # ------------------------------------------------------------------
        # 2. Replace the generic "This field is required." by a message that
        #    says WHICH field is missing (RULE 1 - completeness).
        # ------------------------------------------------------------------
        for name, message in REQUIRED_MESSAGES.items():
            self.fields[name].error_messages["required"] = message

        # ------------------------------------------------------------------
        # 3. Every field must be visible, even when the form is re-displayed
        #    after an error.
        # ------------------------------------------------------------------
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                continue
            css_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css_class} form-control".strip()

    # ------------------------------------------------------------------
    # RULE 4 - CONSISTENCY: clean the values before sending them to the model
    # ------------------------------------------------------------------

    def clean_student_id(self):
        """" st202501 " -> "ST202501"."""
        return normalise_student_id(self.cleaned_data["student_id"])

    def clean_first_name(self):
        """"  ahmed   bel " -> "Ahmed Bel"."""
        return normalise_name(self.cleaned_data["first_name"])

    def clean_last_name(self):
        """"  ben  ali " -> "Ben Ali"."""
        return normalise_name(self.cleaned_data["last_name"])

    def clean_email(self):
        """"  Ahmed.BEN@ESGEN.DZ " -> "ahmed.ben@esgen.dz"."""
        return normalise_email(self.cleaned_data["email"])

    def clean_phone(self):
        """"0555 12 34 56" -> "0555123456"."""
        return normalise_phone(self.cleaned_data["phone"])
