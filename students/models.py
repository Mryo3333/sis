from django.db import models
from django.contrib.auth.models import User


# ============================================================
# DEPARTMENT
# ============================================================

class Department(models.Model):

    department_id = models.AutoField(primary_key=True)

    department_name = models.CharField(
        max_length=100,
        unique=True
    )

    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        default="Active"
    )

    def __str__(self):
        return self.department_name


# ============================================================
# COURSE
# ============================================================

class Course(models.Model):

    course_id = models.AutoField(primary_key=True)

    course_name = models.CharField(
        max_length=100,
        unique=True
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="courses"
    )

    duration_years = models.PositiveIntegerField(default=4)

    status = models.CharField(
        max_length=20,
        default="Active"
    )

    def __str__(self):
        return self.course_name


# ============================================================
# TEACHER
# ============================================================

class Teacher(models.Model):

    teacher_id = models.CharField(
        max_length=20,
        primary_key=True
    )

    name = models.CharField(max_length=100)

    email = models.EmailField(
        unique=True,
        blank=True,
        null=True
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="teachers"
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("Active", "Active"),
            ("Inactive", "Inactive"),
        ],
        default="Active"
    )

    def __str__(self):
        return f"{self.teacher_id} - {self.name}"


# ============================================================
# SUBJECT
# ============================================================

class Subject(models.Model):

    subject_id = models.AutoField(primary_key=True)

    subject_code = models.CharField(
        max_length=20,
        unique=True
    )

    subject_name = models.CharField(max_length=100)

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="subjects"
    )

    semester = models.PositiveIntegerField()

    credits = models.PositiveIntegerField(default=4)

    status = models.CharField(
        max_length=20,
        choices=[
            ("Active", "Active"),
            ("Inactive", "Inactive"),
        ],
        default="Active"
    )

    def __str__(self):
        return f"{self.subject_code} - {self.subject_name}"


# ============================================================
# TEACHER-SUBJECT
# ============================================================

class TeacherSubject(models.Model):

    teacher_subject_id = models.AutoField(primary_key=True)

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="assigned_subjects"
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="assigned_teachers"
    )

    academic_year = models.CharField(max_length=20)

    semester = models.PositiveIntegerField()

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "teacher",
                    "subject",
                    "academic_year",
                    "semester"
                ],
                name="unique_teacher_subject_assignment"
            )
        ]

    def __str__(self):
        return f"{self.teacher} - {self.subject}"


# ============================================================
# STUDENT
# ============================================================

class Student(models.Model):

    student_id = models.CharField(
        max_length=20,
        primary_key=True
    )

    name = models.CharField(max_length=100)

    email = models.EmailField(
        unique=True,
        blank=True,
        null=True
    )

    phone = models.CharField(
        max_length=15,
        blank=True
    )

    date_of_birth = models.DateField(
        blank=True,
        null=True
    )

    gender = models.CharField(
        max_length=20,
        choices=[
            ("Male", "Male"),
            ("Female", "Female"),
            ("Other", "Other"),
        ],
        blank=True
    )

    address = models.TextField(blank=True)

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="students",
        null=True,
        blank=True
    )

    admission_year = models.PositiveIntegerField()

    semester = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=[
            ("Active", "Active"),
            ("Inactive", "Inactive"),
            ("Graduated", "Graduated"),
        ],
        default="Active"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.student_id} - {self.name}"


# ============================================================
# ENROLLMENT
# ============================================================

class Enrollment(models.Model):

    enrollment_id = models.AutoField(primary_key=True)

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )

    academic_year = models.CharField(max_length=20)

    semester = models.PositiveIntegerField()

    enrollment_date = models.DateField(
        auto_now_add=True
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("Active", "Active"),
            ("Completed", "Completed"),
            ("Dropped", "Dropped"),
        ],
        default="Active"
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "student",
                    "subject",
                    "academic_year",
                    "semester"
                ],
                name="unique_student_subject_enrollment"
            )
        ]

    def __str__(self):
        return f"{self.student} - {self.subject}"


# ============================================================
# ATTENDANCE
# ============================================================

class Attendance(models.Model):

    attendance_id = models.AutoField(primary_key=True)

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="attendance_records"
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="attendance_records"
    )

    date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=[
            ("Present", "Present"),
            ("Absent", "Absent"),
            ("Late", "Late"),
        ]
    )

    marked_by = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name="attendance_marked",
        null=True,
        blank=True,
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "student",
                    "subject",
                    "date"
                ],
                name="unique_student_subject_attendance_date"
            )
        ]

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.date}"


# ============================================================
# EXAM
# ============================================================

class Exam(models.Model):

    exam_id = models.AutoField(primary_key=True)

    exam_name = models.CharField(max_length=100)

    exam_type = models.CharField(
        max_length=30,
        choices=[
            ("Midterm", "Midterm"),
            ("Final", "Final"),
            ("Practical", "Practical"),
        ]
    )

    semester = models.PositiveIntegerField()

    academic_year = models.CharField(max_length=20)

    start_date = models.DateField(
        blank=True,
        null=True
    )

    end_date = models.DateField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.exam_name} - Semester {self.semester}"


# ============================================================
# MARK
# ============================================================

class Mark(models.Model):

    mark_id = models.AutoField(primary_key=True)

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="marks"
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="marks"
    )

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="marks"
    )

    marks_obtained = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    max_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    entered_by = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name="marks_entered"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "student",
                    "subject",
                    "exam"
                ],
                name="unique_student_subject_exam_mark"
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(marks_obtained__gte=0)
                    & models.Q(max_marks__gt=0)
                    & models.Q(marks_obtained__lte=models.F("max_marks"))
                ),
                name="valid_mark_values",
            ),
        ]

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.exam}"


# ============================================================
# FEE
# ============================================================

class Fee(models.Model):

    fee_id = models.AutoField(primary_key=True)

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="fees"
    )

    academic_year = models.CharField(max_length=20)

    semester = models.PositiveIntegerField()

    fee_type = models.CharField(
        max_length=50,
        choices=[
            ("Tuition", "Tuition"),
            ("Exam", "Exam"),
            ("Library", "Library"),
            ("Other", "Other"),
        ]
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    payment_date = models.DateField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("Paid", "Paid"),
            ("Partial", "Partial"),
            ("Pending", "Pending"),
        ],
        default="Pending"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(amount__gte=0)
                    & models.Q(amount_paid__gte=0)
                    & models.Q(amount_paid__lte=models.F("amount"))
                ),
                name="valid_fee_values",
            )
        ]

    def __str__(self):
        return f"{self.student} - {self.fee_type} - {self.academic_year}"


class FeePayment(models.Model):

    payment_id = models.AutoField(primary_key=True)

    fee = models.ForeignKey(
        Fee,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    payment_method = models.CharField(
        max_length=30,
        choices=[
            ("Cash", "Cash"),
            ("Bank Transfer", "Bank Transfer"),
            ("Card", "Card"),
            ("Mobile Money", "Mobile Money"),
            ("Other", "Other"),
        ],
        default="Cash"
    )

    reference = models.CharField(max_length=120, blank=True, default="")

    payment_date = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ("Pending", "Pending"),
            ("Completed", "Completed"),
            ("Failed", "Failed"),
            ("Refunded", "Refunded"),
        ],
        default="Completed"
    )

    notes = models.TextField(blank=True, default="")

    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_payments"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="positive_fee_payment_amount",
            ),
        ]

    def __str__(self):
        return f"{self.fee} - {self.amount} ({self.status})"


class AdmissionApplication(models.Model):

    application_id = models.AutoField(primary_key=True)

    applicant_name = models.CharField(max_length=150)

    email = models.EmailField(blank=True, default="")

    phone = models.CharField(max_length=30, blank=True, default="")

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="admissions",
        null=True,
        blank=True
    )

    preferred_year = models.PositiveIntegerField(default=2026)

    source = models.CharField(
        max_length=50,
        choices=[
            ("Website", "Website"),
            ("Referral", "Referral"),
            ("Walk-in", "Walk-in"),
            ("Social Media", "Social Media"),
        ],
        default="Website"
    )

    notes = models.TextField(blank=True, default="")

    status = models.CharField(
        max_length=20,
        choices=[
            ("New", "New"),
            ("Under Review", "Under Review"),
            ("Approved", "Approved"),
            ("Rejected", "Rejected"),
        ],
        default="New"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.applicant_name} - {self.status}"


class ExamResult(models.Model):

    result_id = models.AutoField(primary_key=True)

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="exam_results"
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="exam_results"
    )

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="exam_results"
    )

    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)

    max_marks = models.DecimalField(max_digits=5, decimal_places=2)

    grade = models.CharField(max_length=5, default="A")

    remarks = models.TextField(blank=True, default="")

    published_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ("Published", "Published"),
            ("Draft", "Draft"),
        ],
        default="Published"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "subject", "exam"],
                name="unique_student_subject_exam_result"
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(marks_obtained__gte=0)
                    & models.Q(max_marks__gt=0)
                    & models.Q(marks_obtained__lte=models.F("max_marks"))
                ),
                name="valid_exam_result_values",
            ),
        ]

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.grade}"


# ============================================================
# NOTICE BOARD
# ============================================================

class Notice(models.Model):

    notice_id = models.AutoField(primary_key=True)

    title = models.CharField(max_length=200)

    content = models.TextField()

    category = models.CharField(
        max_length=30,
        choices=[
            ("Academic", "Academic"),
            ("Examination", "Examination"),
            ("Fees", "Fees"),
            ("Event", "Event"),
            ("General", "General"),
        ],
        default="General"
    )

    audience = models.CharField(
        max_length=20,
        choices=[
            ("All", "All"),
            ("Admin", "Admin"),
            ("Teacher", "Teacher"),
            ("Student", "Student"),
            ("Parent", "Parent"),
        ],
        default="All"
    )

    is_active = models.BooleanField(default=True)

    published_at = models.DateTimeField(auto_now_add=True)

    expires_at = models.DateTimeField(blank=True, null=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_notices"
    )

    def __str__(self):
        return f"{self.title} ({self.audience})"


# ============================================================
# TIMETABLE
# ============================================================

class TimetableEntry(models.Model):

    timetable_id = models.AutoField(primary_key=True)

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="timetable_entries"
    )

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="timetable_entries"
    )

    day_of_week = models.CharField(
        max_length=15,
        choices=[
            ("Monday", "Monday"),
            ("Tuesday", "Tuesday"),
            ("Wednesday", "Wednesday"),
            ("Thursday", "Thursday"),
            ("Friday", "Friday"),
            ("Saturday", "Saturday"),
            ("Sunday", "Sunday"),
        ]
    )

    start_time = models.TimeField()

    end_time = models.TimeField()

    room = models.CharField(max_length=80, blank=True, default="")

    academic_year = models.CharField(max_length=20, default="2026-2027")

    semester = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.subject.subject_code} - {self.day_of_week} {self.start_time}"


# ============================================================
# USER PROFILE / LOGIN ROLE
# ============================================================

class UserProfile(models.Model):

    ROLE_CHOICES = [
        ("Admin", "Admin"),
        ("Teacher", "Teacher"),
        ("Student", "Student"),
        ("Parent", "Parent"),
    ]

    REGISTRATION_STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    registration_status = models.CharField(
        max_length=20,
        choices=REGISTRATION_STATUS_CHOICES,
        default="Approved"
    )

    student = models.OneToOneField(
        Student,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_profile"
    )

    teacher = models.OneToOneField(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_profile"
    )

    def __str__(self):
        return f"{self.user.username} - {self.role} - {self.registration_status}"


class ParentProfile(models.Model):

    parent_id = models.AutoField(primary_key=True)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="parent_profile"
    )

    name = models.CharField(max_length=200)

    phone = models.CharField(max_length=30, blank=True, default="")

    email = models.EmailField(blank=True, default="")

    address = models.TextField(blank=True, default="")

    students = models.ManyToManyField(
        Student,
        related_name="parents",
        blank=True
    )

    def __str__(self):
        return self.name


# ============================================================
# ACTIVITY LOG
# ============================================================

class ActivityLog(models.Model):

    log_id = models.AutoField(primary_key=True)

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="activity_logs"
    )

    action = models.CharField(max_length=255)

    timestamp = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user} - {self.action}"


class SchoolSettings(models.Model):

    settings_id = models.AutoField(primary_key=True)

    school_name = models.CharField(max_length=200, default="Cloud Campus")
    short_name = models.CharField(max_length=50, default="CC")
    tagline = models.CharField(max_length=200, blank=True, default="Smart campus operations")
    address = models.TextField(blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    website = models.URLField(blank=True, default="")
    academic_year = models.CharField(max_length=20, default="2026-2027")
    campus_count = models.PositiveIntegerField(default=1)
    subscription_plan = models.CharField(
        max_length=30,
        choices=[
            ("Starter", "Starter"),
            ("Growth", "Growth"),
            ("Enterprise", "Enterprise"),
        ],
        default="Growth"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.school_name


class Notification(models.Model):

    notification_id = models.AutoField(primary_key=True)

    title = models.CharField(max_length=180)
    message = models.TextField()
    category = models.CharField(
        max_length=25,
        choices=[
            ("General", "General"),
            ("Academic", "Academic"),
            ("Exam", "Exam"),
            ("Fee", "Fee"),
            ("System", "System"),
        ],
        default="General",
    )
    audience = models.CharField(
        max_length=20,
        choices=[
            ("All", "All"),
            ("Admin", "Admin"),
            ("Teacher", "Teacher"),
            ("Student", "Student"),
            ("Parent", "Parent"),
        ],
        default="All",
    )
    is_sent = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.audience})"


class Campus(models.Model):

    campus_id = models.AutoField(primary_key=True)
    campus_name = models.CharField(max_length=150)
    city = models.CharField(max_length=100, blank=True, default="")
    region = models.CharField(max_length=100, blank=True, default="")
    address = models.TextField(blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.campus_name


class SubscriptionInvoice(models.Model):

    invoice_id = models.AutoField(primary_key=True)
    school = models.ForeignKey(SchoolSettings, on_delete=models.CASCADE, related_name="invoices")
    plan_name = models.CharField(max_length=30, default="Growth")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=[
            ("Paid", "Paid"),
            ("Pending", "Pending"),
            ("Overdue", "Overdue"),
            ("Cancelled", "Cancelled"),
        ],
        default="Pending",
    )
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    def __str__(self):
        return f"{self.school.school_name} - {self.plan_name} ({self.status})"


class StaffMember(models.Model):

    staff_id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="staff_members",
        null=True,
        blank=True,
    )
    role = models.CharField(max_length=80)
    status = models.CharField(
        max_length=20,
        choices=[
            ("Active", "Active"),
            ("On Leave", "On Leave"),
            ("Inactive", "Inactive"),
        ],
        default="Active",
    )
    joined_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.staff_id} - {self.name}"


class PayrollRecord(models.Model):

    payroll_id = models.AutoField(primary_key=True)
    staff = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name="payroll_records")
    pay_period = models.CharField(max_length=20)
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=[
            ("Paid", "Paid"),
            ("Pending", "Pending"),
            ("Overdue", "Overdue"),
        ],
        default="Pending",
    )
    paid_on = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.staff.name} - {self.pay_period}"


class LibraryBook(models.Model):

    book_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=150)
    category = models.CharField(max_length=60, default="General")
    isbn = models.CharField(max_length=40, blank=True, default="")
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    rack_number = models.CharField(max_length=50, blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=[
            ("Available", "Available"),
            ("Low Stock", "Low Stock"),
            ("Archived", "Archived"),
        ],
        default="Available",
    )

    def __str__(self):
        return f"{self.title} by {self.author}"


class LibraryIssue(models.Model):

    issue_id = models.AutoField(primary_key=True)
    book = models.ForeignKey(LibraryBook, on_delete=models.CASCADE, related_name="issues")
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name="library_issues")
    staff = models.ForeignKey(StaffMember, on_delete=models.SET_NULL, null=True, blank=True, related_name="library_issues")
    issued_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    returned_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("Issued", "Issued"),
            ("Returned", "Returned"),
            ("Overdue", "Overdue"),
        ],
        default="Issued",
    )

    def __str__(self):
        return f"{self.book.title} - {self.status}"


class TransportRoute(models.Model):

    route_id = models.AutoField(primary_key=True)
    route_name = models.CharField(max_length=120)
    driver_name = models.CharField(max_length=120, blank=True, default="")
    vehicle_number = models.CharField(max_length=40, blank=True, default="")
    pickup_point = models.CharField(max_length=150, blank=True, default="")
    drop_point = models.CharField(max_length=150, blank=True, default="")
    capacity = models.PositiveIntegerField(default=40)
    status = models.CharField(
        max_length=20,
        choices=[
            ("Active", "Active"),
            ("Paused", "Paused"),
            ("Maintenance", "Maintenance"),
        ],
        default="Active",
    )

    def __str__(self):
        return self.route_name


class CampusEvent(models.Model):

    event_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=50, default="Academic")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    venue = models.CharField(max_length=200, blank=True, default="")
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title
