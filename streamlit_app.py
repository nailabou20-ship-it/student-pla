"""
Streamlit version of the Student Information Platform.

WHY THIS FILE EXISTS
    Streamlit is a Python framework that builds a web UI very quickly.
    It runs pure Python code.

    It does NOT run Django, but this app is built to REUSE the Django code:
        * the form    -> students/forms.py     (StudentForm)
        * the model   -> students/models.py    (Student)
        * the rules  -> students/validators.py

    So the UI is written in Streamlit, but the validation rules are NOT
    duplicated: the very same `StudentForm` instance is used. That means the
    student sees the same friendly messages, and the same data (the same
    SQLite database, db.sqlite3) is used.

    The rules are therefore written once and are applied both by the Django
    website (python manage.py runserver) and by this Streamlit app
    (streamlit run streamlit_app.py).

    This file is the "entry point" for a Streamlit deployment.

How to run it locally:
    streamlit run streamlit_app.py

The pages:
    * the registration form
    * the list of all the students already stored in the database
"""

import os
import datetime

import streamlit as st

# ---------------------------------------------------------------------------
# 1. Load the Django settings and create the application registry.
#    This is the magic line that allows us to use the Django models and forms.
# ---------------------------------------------------------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "student_portal.settings")
import django

django.setup()

from students.forms import StudentForm  # noqa: E402  (the import comes after django.setup)
from students.models import Student  # noqa: E402
from students.validators import SPECIALTY_CHOICES, WILAYA_CHOICES  # noqa: E402

# ---------------------------------------------------------------------------
# 2. The page
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Student Information Platform",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 Student Information Platform")
st.markdown(
    "The students fill in their information and the administrator views, "
    "searches and exports the records."
)

# ---------------------------------------------------------------------------
# 3. The registration form
# ---------------------------------------------------------------------------
st.subheader("Register a new student")

student_id = st.text_input("Student ID", value="", key="student_id", placeholder="ST202501")
first_name = st.text_input("First name", value="", key="first_name", placeholder="Ahmed")
last_name = st.text_input("Last name", value="", key="last_name", placeholder="Benali")
date_of_birth = st.date_input(
    "Date of birth",
    value=None,  # None -> the user must choose a date
    max_value=datetime.date.today(),  # the browser forbids a future date
)
email = st.text_input("Email", value="", key="email", placeholder="ahmed.benali@esgen.dz")
phone = st.text_input("Phone", value="", key="phone", placeholder="0555123456")

wilaya = st.selectbox(
    "Wilaya",
    options=[code for code, _label in WILAYA_CHOICES],
    format_func=lambda code: f"{code} - {dict(WILAYA_CHOICES)[code]}",
    key="wilaya",
)

specialty = st.selectbox(
    "Specialty",
    options=[name for name, _label in SPECIALTY_CHOICES],
    key="specialty",
)

bac_average = st.number_input(
    "Baccalaureate average (between 0 and 20)",
    min_value=0.0,
    max_value=20.0,
    step=0.01,
    value=15.0,
    key="bac_average",
)

consent = st.checkbox(
    "I consent to the processing of my personal data",
    value=False,
)

submitted = st.button("Save the student")

if submitted:
    # We build the same dictionary that the Django website receives from a
    # browser form. Then we let the Django form validate it and save it.
    data = {
        "student_id": student_id,
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": date_of_birth,
        "email": email,
        "phone": phone,
        "wilaya": wilaya,
        "specialty": specialty,
        "bac_average": bac_average,
        "consent": consent,
    }

    form = StudentForm(data=data)

    if form.is_valid():
        student = form.save()
        st.success(
            f"The student {student.student_id} ({student.full_name}) has been "
            f"registered successfully."
        )
    else:
        st.error("The student has NOT been saved: please correct the errors.")
        # Show the error message next to each faulty field.
        for field_name, errors in form.errors.items():
            for error in errors:
                st.error(f"**{field_name}** -> {error}")

# ---------------------------------------------------------------------------
# 4. The list of all the students
# ---------------------------------------------------------------------------
st.subheader("All the students in the database")

students = list(Student.objects.order_by("-created_at").all())

st.write(f"There are **{len(students)}** student(s) in the database.")

if students:
    # A simple table (a dataframe) with the information of every student.
    dataframe = [
        [
            s.student_id,
            s.full_name,
            str(s.date_of_birth),
            s.age if s.age is not None else "",
            s.email,
            s.phone,
            s.wilaya_name,
            s.specialty,
            str(s.bac_average),
            "Yes" if s.consent else "No",
            str(s.created_at),
        ]
        for s in students
    ]
    st.dataframe(dataframe, use_container_width=True)

    # A downloadable CSV of the students (same file as the Django version).
    st.download_button(
        label="Download the students as a CSV",
        data=st.text,
        file_name="students.csv",
        mime="text/csv",
    )


# ---------------------------------------------------------------------------
# 5. Help for the person who fills the form
# ---------------------------------------------------------------------------
with st.expander("What is the format of each field?"):
    st.markdown(
        """
        - **Student ID**: ST + 6 digits, for example `ST202501`.
        - **Email**: a valid email address, for example `ahmed.benali@esgen.dz`.
        - **Phone**: Algerian mobile, `05`, `06` or `07` followed by 8 digits,
          for example `0555123456`.
        - **Date of birth**: not in the future, the age must be between 17 and 60.
        - **Baccalaureate average**: a mark between 0 and 20.
        """
    )
