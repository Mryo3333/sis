
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from students.models import (
    Attendance,
    Course,
    Department,
    Enrollment,
    Exam,
    Fee,
    FeePayment,
    Fee,
    Mark,
    Student,
    Subject,
    Teacher,
    TeacherSubject,
    UserProfile,
)


class UniversityDashboardTests(TestCase):

    def create_academic_data(self):
        department = Department.objects.create(department_name="Engineering")
        course = Course.objects.create(course_name="BEng Testing", department=department, duration_years=4)
        subject = Subject.objects.create(
            subject_code="TST101",
            subject_name="Testing Fundamentals",
            course=course,
            semester=1,
            credits=3,
        )
        other_subject = Subject.objects.create(
            subject_code="TST102",
            subject_name="Other Testing",
            course=course,
            semester=1,
            credits=3,
        )
        teacher = Teacher.objects.create(
            teacher_id="T-TEST",
            name="Test Teacher",
            department=department,
        )
        student = Student.objects.create(
            student_id="S-TEST",
            name="Test Student",
            email="test.student@example.com",
            course=course,
            admission_year=2026,
            semester=1,
        )
        Enrollment.objects.create(
            student=student,
            subject=subject,
            academic_year="2026-27",
            semester=1,
        )
        return department, subject, other_subject, teacher, student

    def test_seed_university_data_creates_course_subject_records(self):
        call_command("seed_university_data")
        self.assertGreater(Department.objects.count(), 0)
        self.assertGreater(Course.objects.count(), 0)
        self.assertGreater(Subject.objects.count(), 0)

    def test_student_dashboard_displays_dynamic_summary(self):
        department = Department.objects.create(
            department_name="School of Computing",
            description="Technology studies",
            status="Active",
        )
        course = Course.objects.create(
            course_name="BSc Computer Science",
            department=department,
            duration_years=4,
            status="Active",
        )
        subject = Subject.objects.create(
            subject_code="CS101",
            subject_name="Programming Fundamentals",
            course=course,
            semester=1,
            credits=3,
            status="Active",
        )
        teacher = Teacher.objects.create(
            teacher_id="T-101",
            name="Dr. Adams",
            email="teacher@example.com",
            department=department,
            status="Active",
        )
        student = Student.objects.create(
            student_id="S-1001",
            name="Alice Student",
            email="student@example.com",
            phone="1234567890",
            course=course,
            admission_year=2024,
            semester=1,
            status="Active",
        )
        user = User.objects.create_user(
            username="alice",
            email="student@example.com",
            password="securepass123",
        )
        UserProfile.objects.create(
            user=user,
            role="Student",
            registration_status="Approved",
            student=student,
            teacher=None,
        )
        Enrollment.objects.create(
            student=student,
            subject=subject,
            academic_year="2024-25",
            semester=1,
            status="Active",
        )
        Attendance.objects.create(
            student=student,
            subject=subject,
            date="2024-01-15",
            status="Present",
            marked_by=teacher,
        )
        Fee.objects.create(
            student=student,
            academic_year="2024-25",
            semester=1,
            fee_type="Tuition",
            amount=2000,
            amount_paid=1200,
            payment_date="2024-01-10",
            status="Partial",
        )
        exam = Exam.objects.create(
            exam_name="Midterm Exam",
            exam_type="Midterm",
            semester=1,
            academic_year="2024-25",
            start_date="2024-02-01",
            end_date="2024-02-05",
        )
        Mark.objects.create(
            student=student,
            subject=subject,
            exam=exam,
            marks_obtained=78,
            max_marks=100,
            entered_by=teacher,
        )

        self.client.force_login(user)
        response = self.client.get("/dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fee Summary")
        self.assertContains(response, "Programming Fundamentals")

    def test_registration_requires_matching_password_confirmation(self):
        department = Department.objects.create(department_name="Registration")
        course = Course.objects.create(course_name="Registration Course", department=department)

        response = self.client.post("/register/", {
            "student_id": "S-REG",
            "name": "New Student",
            "email": "new.student@example.com",
            "course": course.pk,
            "username": "newstudent",
            "password": "password123",
            "confirm_password": "",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords do not match.")
        self.assertFalse(Student.objects.filter(student_id="S-REG").exists())

    def test_teacher_cannot_mark_attendance_for_unassigned_subject(self):
        _, subject, other_subject, teacher, student = self.create_academic_data()
        TeacherSubject.objects.create(
            teacher=teacher,
            subject=subject,
            academic_year="2026-27",
            semester=1,
        )
        user = User.objects.create_user(username="teacher", password="password123")
        UserProfile.objects.create(user=user, role="Teacher", registration_status="Approved", teacher=teacher)
        self.client.force_login(user)

        response = self.client.post("/attendance/", {
            "subject_id": other_subject.pk,
            "attendance_date": "2026-08-31",
            f"status_{student.student_id}": "Present",
        })

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Attendance.objects.filter(subject=other_subject).exists())

    def test_admin_can_mark_attendance_without_teacher(self):
        _, subject, _, _, student = self.create_academic_data()
        user = User.objects.create_user(username="admin", password="password123")
        UserProfile.objects.create(user=user, role="Admin", registration_status="Approved")
        self.client.force_login(user)

        response = self.client.post("/attendance/", {
            "subject_id": subject.pk,
            "attendance_date": "2026-08-31",
            f"status_{student.student_id}": "Absent",
        })

        self.assertEqual(response.status_code, 302)
        record = Attendance.objects.get(student=student, subject=subject)
        self.assertEqual(record.status, "Absent")
        self.assertIsNone(record.marked_by)

    def test_attendance_resubmission_updates_existing_record(self):
        _, subject, _, teacher, student = self.create_academic_data()
        TeacherSubject.objects.create(teacher=teacher, subject=subject, academic_year="2026-27", semester=1)
        user = User.objects.create_user(username="teacher-edit", password="password123")
        UserProfile.objects.create(user=user, role="Teacher", registration_status="Approved", teacher=teacher)
        self.client.force_login(user)

        payload = {"subject_id": subject.pk, "attendance_date": "2026-08-31", f"status_{student.student_id}": "Absent"}
        self.client.post("/attendance/", payload)
        payload[f"status_{student.student_id}"] = "Present"
        self.client.post("/attendance/", payload)

        self.assertEqual(Attendance.objects.get(student=student, subject=subject).status, "Present")

    def test_student_cannot_overpay_fee(self):
        _, subject, _, _, student = self.create_academic_data()
        fee = Fee.objects.create(
            student=student, academic_year="2026-27", semester=1,
            fee_type="Tuition", amount=100, amount_paid=80, status="Partial",
        )
        user = User.objects.create_user(username="student-pay", password="password123")
        UserProfile.objects.create(user=user, role="Student", registration_status="Approved", student=student)
        self.client.force_login(user)

        response = self.client.post("/student/payments/", {"fee_id": fee.pk, "amount": "25", "method": "Cash"})

        self.assertEqual(response.status_code, 200)
        fee.refresh_from_db()
        self.assertEqual(fee.amount_paid, 80)
        self.assertFalse(FeePayment.objects.filter(fee=fee).exists())
