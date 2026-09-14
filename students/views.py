
from decimal import Decimal, InvalidOperation

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from .management.commands.seed_university_data import seed_university_data
from .models import (
    ActivityLog,
    AdmissionApplication,
    Attendance,
    Campus,
    CampusEvent,
    Course,
    Department,
    Enrollment,
    Exam,
    ExamResult,
    Fee,
    FeePayment,
    LibraryBook,
    LibraryIssue,
    Mark,
    Notice,
    Notification,
    ParentProfile,
    PayrollRecord,
    SchoolSettings,
    StaffMember,
    Student,
    Subject,
    SubscriptionInvoice,
    Teacher,
    TeacherSubject,
    TimetableEntry,
    TransportRoute,
    UserProfile,
)


def is_admin_user(request):
    if not request.user.is_authenticated:
        return False
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return False
    return profile.role == "Admin" and profile.registration_status == "Approved"


def parse_int(value, default, minimum=None):
    """Parse form integers without allowing malformed input to cause a 500."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(parsed, minimum) if minimum is not None else parsed


def home_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    attendance_total = Attendance.objects.count()
    attendance_present = Attendance.objects.filter(status="Present").count()
    attendance_rate = round((attendance_present / attendance_total) * 100) if attendance_total else 0
    fee_total = Fee.objects.aggregate(total=Sum("amount"))["total"] or 0
    return render(request, "students/home.html", {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "attendance_rate": attendance_rate,
        "fee_total": fee_total,
    })


def demo_request(request):
    if request.method == "POST":
        applicant_name = (request.POST.get("applicant_name") or "").strip()
        email = (request.POST.get("email") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        notes = (request.POST.get("notes") or "").strip()
        if applicant_name and email:
            AdmissionApplication.objects.create(
                applicant_name=applicant_name,
                email=email,
                phone=phone,
                source="Website",
                notes=f"Demo request: {notes}".strip(),
            )
            return render(request, "students/demo_request.html", {"submitted": True})
        return render(request, "students/demo_request.html", {
            "error": "Please enter your name and email address.",
            "form_data": request.POST,
        })
    return render(request, "students/demo_request.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")

        pending_user = User.objects.filter(username=username).first()
        if pending_user is not None:
            profile = getattr(pending_user, "profile", None)
            if profile is not None and profile.role == "Student" and profile.registration_status == "Pending":
                return render(
                    request,
                    "students/login.html",
                    {"error": "Your student account is pending admin approval."},
                )

        return render(request, "students/login.html", {"error": "Invalid username or password."})

    return render(request, "students/login.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


def student_register(request):
    courses = Course.objects.filter(status="Active").order_by("course_name")

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        student_id = (request.POST.get("student_id") or "").strip()
        name = (request.POST.get("name") or "").strip()
        email = (request.POST.get("email") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        date_of_birth = request.POST.get("date_of_birth") or None
        gender = request.POST.get("gender") or ""
        address = (request.POST.get("address") or "").strip()
        course_id = request.POST.get("course")
        admission_year = request.POST.get("admission_year")
        semester = request.POST.get("semester")
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        confirm_password = request.POST.get("confirm_password") or ""

        errors = []
        if not student_id or not name or not email:
            errors.append("Please fill in all required fields.")
        if not username or not password:
            errors.append("Username and password are required.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if User.objects.filter(username=username).exists():
            errors.append("This username is already taken.")
        if email and User.objects.filter(email=email).exists():
            errors.append("This email is already connected to a user account.")
        if Student.objects.filter(student_id=student_id).exists():
            errors.append("This student ID is already in use.")
        if email and Student.objects.filter(email=email).exists():
            errors.append("This email is already registered.")

        try:
            course = Course.objects.get(course_id=course_id, status="Active")
        except (Course.DoesNotExist, TypeError, ValueError):
            errors.append("Please select a valid course.")
            course = None

        try:
            parsed_admission_year = int(admission_year) if admission_year else timezone.now().year
            parsed_semester = int(semester) if semester else 1
            if parsed_admission_year < 1 or parsed_semester < 1:
                raise ValueError
        except (TypeError, ValueError):
            errors.append("Admission year and semester must be positive numbers.")
            parsed_admission_year = timezone.now().year
            parsed_semester = 1

        if errors:
            return render(request, "students/student_register.html", {"courses": courses, "error": errors[0], "form_data": request.POST})

        with transaction.atomic():
            student = Student.objects.create(
                student_id=student_id,
                name=name,
                email=email,
                phone=phone,
                date_of_birth=date_of_birth,
                gender=gender,
                address=address,
                course=course,
                admission_year=parsed_admission_year,
                semester=parsed_semester,
                status="Active",
            )

            student_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=name.split()[0],
                last_name=" ".join(name.split()[1:]) if len(name.split()) > 1 else "",
            )
            student_user.is_active = False
            student_user.save(update_fields=["is_active"])

            UserProfile.objects.create(
                user=student_user,
                role="Student",
                registration_status="Pending",
                student=student,
                teacher=None,
            )

        return render(request, "students/registration_success.html", {"student": student, "username": username})

    return render(request, "students/student_register.html", {"courses": courses})


@login_required
def pending_registrations(request):
    if not is_admin_user(request):
        return redirect("dashboard")
    pending_profiles = UserProfile.objects.filter(role="Student", registration_status="Pending").select_related("user", "student", "student__course").order_by("-user__date_joined")
    return render(request, "students/pending_registrations.html", {"pending_profiles": pending_profiles})


@login_required
def approve_student(request, profile_id):
    if not is_admin_user(request):
        return redirect("dashboard")
    if request.method != "POST":
        return redirect("pending_registrations")
    profile = UserProfile.objects.filter(pk=profile_id, role="Student").first()
    if profile is not None:
        profile.registration_status = "Approved"
        profile.user.is_active = True
        profile.user.save(update_fields=["is_active"])
        profile.save(update_fields=["registration_status"])
        ActivityLog.objects.create(user=request.user, action=f"Approved student: {profile.user.username}")
    return redirect("pending_registrations")


@login_required
def reject_student(request, profile_id):
    if not is_admin_user(request):
        return redirect("dashboard")
    if request.method != "POST":
        return redirect("pending_registrations")
    profile = UserProfile.objects.filter(pk=profile_id, role="Student").first()
    if profile is not None:
        profile.registration_status = "Rejected"
        profile.user.is_active = False
        profile.user.save(update_fields=["is_active"])
        profile.save(update_fields=["registration_status"])
        ActivityLog.objects.create(user=request.user, action=f"Rejected student: {profile.user.username}")
    return redirect("pending_registrations")


@login_required
def dashboard(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        logout(request)
        return redirect("login")

    if profile.role == "Admin":
        if not Department.objects.exists():
            seed_university_data()
        school_settings = SchoolSettings.objects.first()
        if school_settings is None:
            school_settings = SchoolSettings.objects.create(
                school_name="Cloud Campus",
                short_name="CC",
                tagline="Smart campus operations",
                subscription_plan="Growth",
            )
        total_students = Student.objects.count()
        total_teachers = Teacher.objects.count()
        total_departments = Department.objects.count()
        total_courses = Course.objects.filter(status="Active").count()
        total_subjects = Subject.objects.filter(status="Active").count()
        pending_students = UserProfile.objects.filter(role="Student", registration_status="Pending").count()
        pending_fees = Fee.objects.filter(status__in=["Pending", "Partial"]).count()
        fee_summary = Fee.objects.aggregate(total_amount=Sum("amount"), total_paid=Sum("amount_paid"))
        total_fee_amount = fee_summary["total_amount"] or 0
        total_fee_paid = fee_summary["total_paid"] or 0
        recent_notifications = Notification.objects.order_by("-created_at")[:5]
        return render(request, "students/admin_dashboard.html", {
            "user": request.user,
            "admin_name": request.user.get_full_name() or request.user.username,
            "total_students": total_students,
            "total_teachers": total_teachers,
            "total_departments": total_departments,
            "total_courses": total_courses,
            "total_subjects": total_subjects,
            "pending_students": pending_students,
            "pending_fees": pending_fees,
            "total_fee_amount": total_fee_amount,
            "total_fee_paid": total_fee_paid,
            "school_settings": school_settings,
            "recent_notifications": recent_notifications,
        })

    if profile.role == "Teacher":
        teacher = getattr(profile, "teacher", None)
        if teacher is None:
            return redirect("logout")

        # Get teacher assignments and subjects
        assignment_rows = TeacherSubject.objects.filter(teacher=teacher).select_related("subject", "subject__course")
        subjects = [a.subject for a in assignment_rows if getattr(a, 'subject', None) is not None]

        # Optional: selected subject via querystring to show per-subject students
        selected_subject = None
        subject_id = request.GET.get('subject')
        if subject_id:
            try:
                sid = int(subject_id)
                ts = TeacherSubject.objects.filter(teacher=teacher, subject__subject_id=sid).select_related('subject').first()
                if ts:
                    selected_subject = ts.subject
            except (ValueError, TypeError):
                selected_subject = None

        # Students enrolled in any of the teacher's subjects (unique)
        student_qs = Student.objects.filter(enrollments__subject__in=subjects).distinct() if subjects else Student.objects.none()
        students_list = student_qs.select_related('course').order_by('student_id')
        total_students = student_qs.count()
        total_subjects = len(subjects)

        # If a subject is selected, prepare that subject's students
        subject_students = None
        if selected_subject is not None:
            subject_students = Student.objects.filter(enrollments__subject=selected_subject).select_related('course').order_by('student_id').distinct()

        # Attendance average for these subjects (percentage of Present)
        attendance_qs = Attendance.objects.filter(subject__in=subjects) if subjects else Attendance.objects.none()
        total_attendance = attendance_qs.count()
        present_count = attendance_qs.filter(status="Present").count() if total_attendance else 0
        average_attendance = round((present_count / total_attendance * 100), 2) if total_attendance else 0

        # Average marks percentage across marks for these subjects
        marks_qs = Mark.objects.filter(subject__in=subjects) if subjects else Mark.objects.none()
        average_marks = 0
        if marks_qs.exists():
            total_pct = 0
            count = 0
            for m in marks_qs:
                try:
                    pct = (float(m.marks_obtained) / float(m.max_marks)) * 100 if m.max_marks and m.max_marks > 0 else 0
                    total_pct += pct
                    count += 1
                except Exception:
                    continue
            average_marks = round((total_pct / count), 2) if count else 0

        return render(request, "students/teacher_dashboard.html", {
            "teacher": teacher,
            "assignments": assignment_rows,
            "subjects": subjects,
            "selected_subject": selected_subject,
            "subject_students": subject_students,
            "students_list": students_list,
            "total_subjects": total_subjects,
            "total_students": total_students,
            "average_attendance": average_attendance,
            "average_marks": average_marks,
        })

    if profile.role == "Parent":
        parent_profile = getattr(request.user, "parent_profile", None)
        if parent_profile is None:
            return redirect("logout")
        children = parent_profile.students.select_related("course").order_by("student_id")
        notices = Notice.objects.filter(is_active=True, audience__in=["All", "Parent"]).order_by("-published_at")[:5]
        return render(request, "students/parent_dashboard.html", {
            "parent": parent_profile,
            "children": children,
            "total_students": children.count(),
            "notices": notices,
        })

    student = profile.student
    if student is None:
        return redirect("logout")

    course = student.course
    enrollment_rows = Enrollment.objects.filter(student=student).select_related("subject", "subject__course")
    subjects = [item.subject for item in enrollment_rows if item.subject]
    if not subjects and course:
        subjects = list(Subject.objects.filter(course=course, status="Active").order_by("semester", "subject_name"))

    attendance_records = Attendance.objects.filter(student=student).select_related("subject", "marked_by").order_by("-date")
    marks = Mark.objects.filter(student=student).select_related("subject", "exam").order_by("-created_at")
    fee_entries = Fee.objects.filter(student=student).order_by("academic_year", "semester")
    fee_total = sum(float(item.amount) for item in fee_entries)
    fee_paid = sum(float(item.amount_paid) for item in fee_entries)
    fee_due = max(fee_total - fee_paid, 0)

    return render(request, "students/student_dashboard.html", {
        "student": student,
        "course": course,
        "subjects": subjects,
        "subject_list": subjects,
        "attendance_records": attendance_records,
        "present_count": attendance_records.filter(status="Present").count(),
        "absent_count": attendance_records.filter(status="Absent").count(),
        "marks": marks,
        "fees": fee_entries,
        "fee_total": fee_total,
        "fee_paid": fee_paid,
        "fee_due": fee_due,
        "pending_fees": fee_entries.filter(status__in=["Pending", "Partial"]).count(),
    })


@login_required
def admin_library(request):
    if not is_admin_user(request):
        return redirect("dashboard")

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        author = (request.POST.get("author") or "").strip()
        category = (request.POST.get("category") or "General").strip()
        isbn = (request.POST.get("isbn") or "").strip()
        rack_number = (request.POST.get("rack_number") or "").strip()
        total_copies = parse_int(request.POST.get("total_copies"), 1, minimum=1)
        if title and author:
            book = LibraryBook.objects.create(
                title=title,
                author=author,
                category=category,
                isbn=isbn,
                rack_number=rack_number,
                total_copies=max(total_copies, 1),
                available_copies=max(total_copies, 1),
            )
            ActivityLog.objects.create(user=request.user, action=f"Added library book: {book.title}")
        return redirect("admin_library")

    books = LibraryBook.objects.order_by("title")
    issues = LibraryIssue.objects.select_related("book", "student", "staff").order_by("-issued_date")[:20]
    return render(request, "students/admin_library.html", {"books": books, "issues": issues})


@login_required
def admin_transport(request):
    if not is_admin_user(request):
        return redirect("dashboard")

    if request.method == "POST":
        route_name = (request.POST.get("route_name") or "").strip()
        driver_name = (request.POST.get("driver_name") or "").strip()
        vehicle_number = (request.POST.get("vehicle_number") or "").strip()
        pickup_point = (request.POST.get("pickup_point") or "").strip()
        drop_point = (request.POST.get("drop_point") or "").strip()
        capacity = parse_int(request.POST.get("capacity"), 40, minimum=1)
        if route_name:
            TransportRoute.objects.create(
                route_name=route_name,
                driver_name=driver_name,
                vehicle_number=vehicle_number,
                pickup_point=pickup_point,
                drop_point=drop_point,
                capacity=max(capacity, 1),
            )
            ActivityLog.objects.create(user=request.user, action=f"Added transport route: {route_name}")
        return redirect("admin_transport")

    routes = TransportRoute.objects.order_by("route_name")
    return render(request, "students/admin_transport.html", {"routes": routes})


@login_required
def admin_hr(request):
    if not is_admin_user(request):
        return redirect("dashboard")

    if request.method == "POST":
        staff_id = (request.POST.get("staff_id") or "").strip()
        name = (request.POST.get("name") or "").strip()
        role = (request.POST.get("role") or "Staff").strip()
        department_id = request.POST.get("department")
        phone = (request.POST.get("phone") or "").strip()
        email = (request.POST.get("email") or "").strip()
        if staff_id and name:
            department = Department.objects.filter(department_id=department_id).first() if department_id else None
            staff = StaffMember.objects.create(
                staff_id=staff_id,
                name=name,
                role=role,
                department=department,
                phone=phone,
                email=email,
            )
            PayrollRecord.objects.create(
                staff=staff,
                pay_period=timezone.now().strftime("%Y-%m"),
                basic_salary=Decimal("0.00"),
                allowance=Decimal("0.00"),
                deductions=Decimal("0.00"),
                net_salary=Decimal("0.00"),
                status="Pending",
            )
            ActivityLog.objects.create(user=request.user, action=f"Added staff record: {staff.name}")
        return redirect("admin_hr")

    staff_members = StaffMember.objects.select_related("department").order_by("name")
    payroll = PayrollRecord.objects.select_related("staff").order_by("-pay_period")[:20]
    return render(request, "students/admin_hr.html", {"staff_members": staff_members, "payroll": payroll, "departments": Department.objects.order_by("department_name")})


@login_required
def admin_events(request):
    if not is_admin_user(request):
        return redirect("dashboard")

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        event_type = (request.POST.get("event_type") or "Academic").strip()
        start_date = request.POST.get("start_date") or timezone.now().date()
        end_date = request.POST.get("end_date") or start_date
        venue = (request.POST.get("venue") or "").strip()
        description = (request.POST.get("description") or "").strip()
        if title:
            CampusEvent.objects.create(
                title=title,
                event_type=event_type,
                start_date=start_date,
                end_date=end_date,
                venue=venue,
                description=description,
            )
            ActivityLog.objects.create(user=request.user, action=f"Added event: {title}")
        return redirect("admin_events")

    events = CampusEvent.objects.order_by("start_date")
    return render(request, "students/admin_events.html", {"events": events})


@login_required
def admin_school_settings(request):
    if not is_admin_user(request):
        return redirect("dashboard")

    settings = SchoolSettings.objects.first()
    if settings is None:
        settings = SchoolSettings.objects.create(
            school_name="Cloud Campus",
            short_name="CC",
            tagline="Smart campus operations",
            subscription_plan="Growth",
        )

    if request.method == "POST":
        settings.school_name = (request.POST.get("school_name") or settings.school_name).strip() or settings.school_name
        settings.short_name = (request.POST.get("short_name") or settings.short_name).strip() or settings.short_name
        settings.tagline = (request.POST.get("tagline") or settings.tagline).strip()
        settings.address = (request.POST.get("address") or settings.address).strip()
        settings.phone = (request.POST.get("phone") or settings.phone).strip()
        settings.email = (request.POST.get("email") or settings.email).strip()
        settings.website = (request.POST.get("website") or settings.website).strip()
        settings.academic_year = (request.POST.get("academic_year") or settings.academic_year).strip()
        settings.campus_count = parse_int(request.POST.get("campus_count"), settings.campus_count, minimum=1)
        settings.subscription_plan = (request.POST.get("subscription_plan") or settings.subscription_plan).strip()
        settings.save()
        ActivityLog.objects.create(user=request.user, action=f"Updated school settings: {settings.school_name}")
        return redirect("admin_school_settings")

    return render(request, "students/admin_school_settings.html", {"settings": settings})


@login_required
def admin_notifications(request):
    if not is_admin_user(request):
        return redirect("dashboard")

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        message = (request.POST.get("message") or "").strip()
        category = request.POST.get("category") or "General"
        audience = request.POST.get("audience") or "All"
        if title and message:
            Notification.objects.create(
                title=title,
                message=message,
                category=category,
                audience=audience,
                created_by=request.user,
            )
            ActivityLog.objects.create(user=request.user, action=f"Broadcasted notification: {title}")
        return redirect("admin_notifications")

    notifications = Notification.objects.order_by("-created_at")
    return render(request, "students/admin_notifications.html", {"notifications": notifications})


@login_required
def admin_analytics(request):
    if not is_admin_user(request):
        return redirect("dashboard")

    settings = SchoolSettings.objects.first() or SchoolSettings.objects.create(
        school_name="Cloud Campus",
        short_name="CC",
        tagline="Smart campus operations",
        subscription_plan="Growth",
    )

    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_departments = Department.objects.count()
    total_courses = Course.objects.count()
    total_notifications = Notification.objects.count()
    total_fee_collected = Fee.objects.aggregate(total=Sum("amount_paid"))["total"] or 0
    total_fee_due = Fee.objects.aggregate(total=Sum("amount"))["total"] or 0
    fee_balance = max(float(total_fee_due) - float(total_fee_collected), 0)

    campuses = Campus.objects.order_by("campus_name")
    invoices = SubscriptionInvoice.objects.select_related("school").order_by("-issue_date")[:10]

    return render(request, "students/admin_analytics.html", {
        "settings": settings,
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_departments": total_departments,
        "total_courses": total_courses,
        "total_notifications": total_notifications,
        "total_fee_collected": total_fee_collected,
        "fee_balance": fee_balance,
        "campuses": campuses,
        "invoices": invoices,
    })


@login_required
def admin_campsuses(request):
    if not is_admin_user(request):
        return redirect("dashboard")

    if request.method == "POST":
        campus_name = (request.POST.get("campus_name") or "").strip()
        city = (request.POST.get("city") or "").strip()
        region = (request.POST.get("region") or "").strip()
        address = (request.POST.get("address") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        email = (request.POST.get("email") or "").strip()
        if campus_name:
            Campus.objects.create(
                campus_name=campus_name,
                city=city,
                region=region,
                address=address,
                phone=phone,
                email=email,
            )
        return redirect("admin_campuses")

    campus_list = Campus.objects.order_by("campus_name")
    return render(request, "students/admin_campsuses.html", {"campuses": campus_list})


@login_required
def admin_billing(request):
    if not is_admin_user(request):
        return redirect("dashboard")

    if request.method == "POST":
        plan_name = request.POST.get("plan_name") or "Growth"
        amount = request.POST.get("amount") or "0"
        status = request.POST.get("status") or "Pending"
        notes = (request.POST.get("notes") or "").strip()
        school = SchoolSettings.objects.first() or SchoolSettings.objects.create(
            school_name="Cloud Campus", short_name="CC", subscription_plan="Growth"
        )
        try:
            parsed_amount = Decimal(amount)
        except (InvalidOperation, ValueError):
            parsed_amount = Decimal('0')
        SubscriptionInvoice.objects.create(
            school=school,
            plan_name=plan_name,
            amount=parsed_amount,
            status=status,
            notes=notes,
        )
        return redirect("admin_billing")

    invoices = SubscriptionInvoice.objects.select_related("school").order_by("-issue_date")
    return render(request, "students/admin_billing.html", {"invoices": invoices})


@login_required
def parent_dashboard(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return redirect("login")

    if profile.role != "Parent":
        return redirect("dashboard")

    parent_profile = getattr(request.user, "parent_profile", None)
    if parent_profile is None:
        return redirect("dashboard")

    children = parent_profile.students.select_related("course").order_by("student_id")
    children_summary = []
    for child in children:
        fee_entries = list(Fee.objects.filter(student=child).order_by("academic_year", "semester"))
        total_amount = sum(float(item.amount) for item in fee_entries)
        total_paid = sum(float(item.amount_paid) for item in fee_entries)
        fee_due = max(total_amount - total_paid, 0)
        children_summary.append({
            "student": child,
            "total_amount": total_amount,
            "total_paid": total_paid,
            "fee_due": fee_due,
            "status": "Paid" if fee_due <= 0 else "Pending",
        })

    notices = Notice.objects.filter(
        Q(is_active=True),
        Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now()),
        audience__in=["All", "Parent"],
    ).order_by("-published_at")[:5]
    return render(
        request,
        "students/parent_dashboard.html",
        {
            "parent": parent_profile,
            "children": children,
            "children_summary": children_summary,
            "total_students": children.count(),
            "notices": notices,
        },
    )


@login_required
def notices(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return redirect("login")

    allowed_roles = ["All"]
    if profile.role == "Admin":
        allowed_roles = ["All", "Admin"]
    elif profile.role == "Teacher":
        allowed_roles = ["All", "Teacher"]
    elif profile.role == "Student":
        allowed_roles = ["All", "Student"]
    elif profile.role == "Parent":
        allowed_roles = ["All", "Parent"]

    notice_items = Notice.objects.filter(
        Q(is_active=True),
        Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now()),
        audience__in=allowed_roles,
    ).order_by("-published_at")
    if not notice_items.exists():
        notice_items = [
            Notice(title="Campus reopen schedule", content="All classes will resume as scheduled on Monday with gate access from 7:30 AM.", category="General", audience="All"),
            Notice(title="Midterm exam calendar", content="Midterm examinations for the School of Business and Engineering are posted in the academic calendar.", category="Examination", audience="Student"),
            Notice(title="Fee payment reminder", content="Final semester fee balances are due before the last Friday of the month to avoid late penalties.", category="Fees", audience="Parent"),
        ]

    return render(request, "students/notices.html", {"notices": notice_items, "role": profile.role})


@login_required
def timetable(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return redirect("login")

    if profile.role == "Admin":
        entries = TimetableEntry.objects.select_related("subject", "teacher", "teacher__department").order_by("day_of_week", "start_time")
    elif profile.role == "Teacher":
        entries = TimetableEntry.objects.filter(teacher=profile.teacher).select_related("subject", "teacher", "teacher__department").order_by("day_of_week", "start_time")
    elif profile.role == "Student":
        entries = TimetableEntry.objects.filter(subject__enrollments__student=profile.student).distinct().select_related("subject", "teacher", "teacher__department").order_by("day_of_week", "start_time")
    elif profile.role == "Parent":
        parent_profile = getattr(request.user, "parent_profile", None)
        student_ids = list(parent_profile.students.values_list("pk", flat=True)) if parent_profile else []
        if not student_ids:
            entries = TimetableEntry.objects.none()
        else:
            entries = TimetableEntry.objects.filter(subject__enrollments__student_id__in=student_ids).distinct().select_related("subject", "teacher", "teacher__department").order_by("day_of_week", "start_time")
    else:
        entries = TimetableEntry.objects.none()

    if not entries.exists():
        entries = [
            TimetableEntry(subject=Subject.objects.order_by("subject_name").first(), teacher=Teacher.objects.order_by("teacher_id").first(), day_of_week="Monday", start_time="09:00:00", end_time="10:30:00", room="A-201"),
            TimetableEntry(subject=Subject.objects.order_by("subject_name").first(), teacher=Teacher.objects.order_by("teacher_id").first(), day_of_week="Wednesday", start_time="11:00:00", end_time="12:30:00", room="LAB-2"),
        ]

    return render(request, "students/timetable.html", {"entries": entries, "role": profile.role})


@login_required
def admin_notices(request):
    if not is_admin_user(request):
        return redirect("dashboard")

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        content = (request.POST.get("content") or "").strip()
        category = request.POST.get("category") or "General"
        audience = request.POST.get("audience") or "All"
        if title and content:
            Notice.objects.create(
                title=title,
                content=content,
                category=category,
                audience=audience,
                created_by=request.user,
            )
        return redirect("admin_notices")

    notices = Notice.objects.order_by("-published_at")
    return render(request, "students/admin_notices.html", {"notices": notices})


@login_required
def admin_delete_notice(request, notice_id):
    if not is_admin_user(request):
        return redirect("dashboard")

    if request.method == "POST":
        Notice.objects.filter(notice_id=notice_id).delete()
    return redirect("admin_notices")


@login_required
def admin_timetable(request):
    if not is_admin_user(request):
        return redirect("dashboard")

    if request.method == "POST":
        subject_id = request.POST.get("subject")
        teacher_id = request.POST.get("teacher")
        day_of_week = request.POST.get("day_of_week") or "Monday"
        start_time = request.POST.get("start_time") or "09:00"
        end_time = request.POST.get("end_time") or "10:30"
        room = (request.POST.get("room") or "").strip()
        academic_year = request.POST.get("academic_year") or "2026-2027"
        semester = request.POST.get("semester") or 1

        subject = Subject.objects.filter(subject_id=subject_id).first()
        teacher = Teacher.objects.filter(teacher_id=teacher_id).first() if teacher_id else None
        if subject:
            TimetableEntry.objects.create(
                subject=subject,
                teacher=teacher,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                room=room,
                academic_year=academic_year,
                semester=parse_int(semester, 1, minimum=1),
            )
        return redirect("admin_timetable")

    timetable_entries = TimetableEntry.objects.select_related("subject", "teacher", "teacher__department").order_by("day_of_week", "start_time")
    return render(request, "students/admin_timetable.html", {
        "entries": timetable_entries,
        "subjects": Subject.objects.order_by("subject_name"),
        "teachers": Teacher.objects.select_related("department").order_by("name"),
    })


@login_required
def admin_delete_timetable(request, timetable_id):
    if not is_admin_user(request):
        return redirect("dashboard")

    if request.method == "POST":
        TimetableEntry.objects.filter(timetable_id=timetable_id).delete()
    return redirect("admin_timetable")


@login_required
def student_admissions(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return redirect("login")

    if profile.role != "Student":
        return redirect("dashboard")

    student = profile.student
    if student is None:
        return redirect("dashboard")

    if request.method == "POST":
        applicant_name = (request.POST.get("applicant_name") or student.name or "").strip()
        email = (request.POST.get("email") or student.email or "").strip()
        phone = (request.POST.get("phone") or student.phone or "").strip()
        course_id = request.POST.get("course") or (student.course_id if student.course else "")
        preferred_year = request.POST.get("preferred_year") or timezone.now().year
        source = request.POST.get("source") or "Website"
        notes = (request.POST.get("notes") or "").strip()

        if not applicant_name or not email:
            return render(
                request,
                "students/student_admissions.html",
                {
                    "student": student,
                    "courses": Course.objects.filter(status="Active"),
                    "applications": AdmissionApplication.objects.filter(email__iexact=(student.email or "")).order_by("-created_at"),
                    "error": "Applicant name and email are required.",
                },
            )

        parsed_year = parse_int(preferred_year, timezone.now().year, minimum=1)
        AdmissionApplication.objects.create(
            applicant_name=applicant_name,
            email=email,
            phone=phone,
            course_id=course_id or None,
            preferred_year=parsed_year,
            source=source,
            notes=notes,
            status="New",
        )
        return redirect("student_admissions")

    applications = AdmissionApplication.objects.filter(email__iexact=(student.email or "")).order_by("-created_at")
    return render(
        request,
        "students/student_admissions.html",
        {
            "student": student,
            "courses": Course.objects.filter(status="Active"),
            "applications": applications,
        },
    )


@login_required
def admin_admissions(request):
    if not is_admin_user(request):
        return redirect("dashboard")

    if request.method == "POST":
        app_id = request.POST.get("application_id")
        new_status = request.POST.get("status") or "New"
        if app_id:
            app = AdmissionApplication.objects.filter(application_id=app_id).first()
            if app is not None and new_status in {"New", "Under Review", "Approved", "Rejected"}:
                app.status = new_status
                app.save(update_fields=["status"])
        return redirect("admin_admissions")

    applications = AdmissionApplication.objects.select_related("course").order_by("-created_at")
    return render(
        request,
        "students/admin_admissions.html",
        {"applications": applications},
    )


@login_required
def student_results(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return redirect("login")

    if profile.role != "Student":
        return redirect("dashboard")

    student = profile.student
    if student is None:
        return redirect("dashboard")

    results = ExamResult.objects.filter(student=student).select_related("subject", "exam").order_by("-published_at")
    average_score = 0
    if results.exists():
        percentages = []
        for item in results:
            try:
                if item.max_marks and float(item.max_marks) > 0:
                    percentages.append((float(item.marks_obtained) / float(item.max_marks)) * 100)
            except Exception:
                continue
        average_score = round(sum(percentages) / len(percentages), 2) if percentages else 0

    return render(
        request,
        "students/student_results.html",
        {"student": student, "results": results, "average_score": average_score},
    )


@login_required
def admin_results(request):
    if not is_admin_user(request):
        return redirect("dashboard")

    results = ExamResult.objects.select_related("student", "subject", "exam").order_by("-published_at")
    return render(
        request,
        "students/admin_results.html",
        {"results": results},
    )


@login_required
def attendance(request):
    """
    GET: Show subjects assigned to the teacher (or all subjects for admin) and, when ?subject= is present,
    show students enrolled in that subject so the teacher can mark attendance.

    POST: Save attendance records for the provided subject and date. Teachers and Admins may mark attendance.
    """
    profile = request.user.profile

    # Permission: only teachers and admins can mark attendance; students can view their own records elsewhere
    if request.method == "POST":
        if profile.role not in {"Teacher", "Admin"}:
            return redirect("dashboard")

        subject_id = request.POST.get("subject_id")
        attendance_date_str = request.POST.get("attendance_date")
        try:
            from datetime import datetime

            attendance_date = datetime.strptime(attendance_date_str, "%Y-%m-%d").date() if attendance_date_str else timezone.now().date()
        except Exception:
            attendance_date = timezone.now().date()

        subject = Subject.objects.filter(subject_id=subject_id).first()
        if subject is None:
            return redirect("attendance")

        if profile.role == "Teacher" and not TeacherSubject.objects.filter(
            teacher=profile.teacher, subject=subject
        ).exists():
            return redirect("attendance")

        # Get students enrolled in this subject
        students = Student.objects.filter(enrollments__subject=subject).distinct()

        marked_by = None
        if profile.role == "Teacher" and getattr(profile, "teacher", None) is not None:
            marked_by = profile.teacher

        # Save attendance for each student, using get_or_create to avoid duplicates
        for student in students:
            key = f"status_{student.student_id}"
            status = request.POST.get(key) or "Present"
            if status not in {"Present", "Absent", "Late"}:
                status = "Present"
            Attendance.objects.update_or_create(
                student=student,
                subject=subject,
                date=attendance_date,
                defaults={"status": status, "marked_by": marked_by},
            )

        ActivityLog.objects.create(user=request.user, action=f"Marked attendance for {subject.subject_code} on {attendance_date}")
        return redirect(f"/attendance/?subject={subject.subject_id}")

    # GET handling: build subjects list and optional selected subject context
    if profile.role == "Admin":
        subjects = Subject.objects.select_related("course").order_by("subject_name")
    elif profile.role == "Teacher":
        # subjects assigned to this teacher
        subjects = Subject.objects.filter(assigned_teachers__teacher=profile.teacher).select_related("course").distinct().order_by("subject_name")
    else:
        subjects = Subject.objects.none()

    selected_subject = None
    students = None
    subject_id = request.GET.get("subject")
    if subject_id:
        selected_subject = Subject.objects.filter(subject_id=subject_id).select_related("course").first()
        if profile.role == "Teacher" and selected_subject is not None:
            if not TeacherSubject.objects.filter(teacher=profile.teacher, subject=selected_subject).exists():
                selected_subject = None
        if selected_subject:
            students = Student.objects.filter(enrollments__subject=selected_subject).distinct().order_by("student_id")

    today = timezone.now().date()

    # For display of past attendance records (teacher sees their own marked records)
    if profile.role == "Admin":
        records = Attendance.objects.select_related("student", "subject", "marked_by").order_by("-date")
    elif profile.role == "Teacher":
        records = Attendance.objects.filter(marked_by=profile.teacher).select_related("student", "subject", "marked_by").order_by("-date")
    else:
        records = Attendance.objects.filter(student=profile.student).select_related("student", "subject", "marked_by").order_by("-date")

    return render(
        request,
        "students/attendance.html",
        {
            "attendance_records": records,
            "subjects": subjects,
            "selected_subject": selected_subject,
            "students": students,
            "today": today,
        },
    )


@login_required
def marks(request):
    profile = request.user.profile
    teacher = getattr(profile, "teacher", None) if profile.role == "Teacher" else None
    subjects = Subject.objects.filter(
        assigned_teachers__teacher=teacher,
        status="Active",
    ).select_related("course").distinct().order_by("subject_name") if teacher else Subject.objects.none()
    selected_subject = None
    selected_exam = None
    exams = Exam.objects.none()
    students = Student.objects.none()
    existing_marks = {}
    subject_id = request.POST.get("subject_id") or request.GET.get("subject")
    exam_id = request.POST.get("exam_id") or request.GET.get("exam")

    if subject_id:
        selected_subject = subjects.filter(subject_id=subject_id).first()
    if selected_subject is not None:
        exams = Exam.objects.filter(semester=selected_subject.semester).order_by("-start_date", "exam_name")
        students = Student.objects.filter(
            enrollments__subject=selected_subject,
            enrollments__status="Active",
        ).distinct().select_related("course").order_by("student_id")
        if exam_id:
            selected_exam = exams.filter(exam_id=exam_id).first()
        if selected_exam is not None:
            existing_marks = {
                mark.student_id: mark
                for mark in Mark.objects.filter(
                    student__in=students, subject=selected_subject, exam=selected_exam
                ).select_related("student")
            }
            if request.method == "POST":
                for student in students:
                    raw_value = (request.POST.get(f"marks_{student.student_id}") or "").strip()
                    if not raw_value:
                        continue
                    try:
                        value = Decimal(raw_value)
                    except (InvalidOperation, ValueError):
                        continue
                    if value < 0 or value > 100:
                        continue
                    Mark.objects.update_or_create(
                        student=student,
                        subject=selected_subject,
                        exam=selected_exam,
                        defaults={
                            "marks_obtained": value,
                            "max_marks": Decimal("100"),
                            "entered_by": teacher,
                        },
                    )
                return redirect(f"/marks/?subject={selected_subject.subject_id}&exam={selected_exam.exam_id}")

    records = Mark.objects.filter(entered_by=teacher).select_related(
        "student", "subject", "exam", "entered_by"
    ).order_by("-created_at") if teacher else Mark.objects.none()
    return render(request, "students/marks.html", {
        "marks": records,
        "subjects": subjects,
        "selected_subject": selected_subject,
        "selected_exam": selected_exam,
        "exams": exams,
        "students": students,
        "existing_marks": existing_marks,
    })


@login_required
def student_profile(request):
    """Dedicated student profile page with academic, attendance, marks, and fee summary."""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return redirect("login")

    if profile.role != "Student":
        return redirect("dashboard")

    student = profile.student
    if student is None:
        return redirect("dashboard")

    enrollment_rows = Enrollment.objects.filter(student=student).select_related("subject", "subject__course")
    subjects = [item.subject for item in enrollment_rows if item.subject]
    if not subjects and student.course:
        subjects = list(Subject.objects.filter(course=student.course, status="Active").order_by("semester", "subject_name"))

    attendance_qs = Attendance.objects.filter(student=student).select_related("subject", "marked_by").order_by("-date")
    attendance_records = attendance_qs[:10]
    total_attendance = attendance_qs.count()
    present_attendance = attendance_qs.filter(status="Present").count()
    attendance_pct = round((present_attendance / total_attendance) * 100, 2) if total_attendance else 0

    marks = Mark.objects.filter(student=student).select_related("subject", "exam").order_by("-created_at")
    average_marks = 0
    if marks.exists():
        percentages = []
        for item in marks:
            try:
                if item.max_marks and float(item.max_marks) > 0:
                    percentages.append((float(item.marks_obtained) / float(item.max_marks)) * 100)
            except Exception:
                continue
        average_marks = round(sum(percentages) / len(percentages), 2) if percentages else 0

    fee_entries = Fee.objects.filter(student=student).order_by("academic_year", "semester")
    total_amount = sum(float(item.amount) for item in fee_entries)
    total_paid = sum(float(item.amount_paid) for item in fee_entries)
    fee_due = max(total_amount - total_paid, 0)

    return render(
        request,
        "students/student_profile.html",
        {
            "student": student,
            "subjects": subjects,
            "attendance_records": attendance_records,
            "attendance_pct": attendance_pct,
            "present_attendance": present_attendance,
            "total_attendance": total_attendance,
            "marks": marks,
            "average_marks": average_marks,
            "fees": fee_entries,
            "total_amount": total_amount,
            "total_paid": total_paid,
            "fee_due": fee_due,
            "course": student.course,
        },
    )


@login_required
def admin_students(request):
    if not is_admin_user(request):
        return redirect("dashboard")
    students = Student.objects.select_related("course").order_by("student_id")
    query = (request.GET.get("q") or "").strip()
    if query:
        students = students.filter(Q(student_id__icontains=query) | Q(name__icontains=query) | Q(email__icontains=query))
    edit_student = None
    edit_id = (request.GET.get("edit") or "").strip()
    if edit_id:
        edit_student = Student.objects.select_related("course").filter(student_id=edit_id).first()
    return render(request, "students/admin_students.html", {"students": students, "search": query, "courses": Course.objects.filter(status="Active"), "edit_student": edit_student})


# ----------------------
# TEACHER: Students list
# ----------------------
@login_required
def teacher_students(request):
    """Show list of students assigned to the logged-in teacher."""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return redirect("login")
    if profile.role != "Teacher" or not getattr(profile, "teacher", None):
        return redirect("dashboard")

    # Students enrolled in any subject assigned to this teacher
    students = Student.objects.filter(
        enrollments__subject__assigned_teachers__teacher=profile.teacher
    ).distinct().select_related("course").order_by("student_id")

    total_students = students.count()

    return render(request, "students/teacher_students.html", {"students": students, "total_students": total_students})


@login_required
def teacher_subjects(request):
    """Show only the subjects assigned to the logged-in teacher."""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return redirect("login")
    teacher = getattr(profile, "teacher", None) if profile.role == "Teacher" else None
    if teacher is None:
        return redirect("dashboard")

    subjects = Subject.objects.filter(
        assigned_teachers__teacher=teacher,
        status="Active",
    ).select_related("course").distinct().order_by("semester", "subject_name")
    return render(request, "students/teacher_subjects.html", {"subjects": subjects})


@login_required
def admin_add_student(request):
    if not is_admin_user(request):
        return redirect("dashboard")
    if request.method != "POST":
        return redirect("admin_students")
    student_id = (request.POST.get("student_id") or "").strip()
    name = (request.POST.get("name") or "").strip()
    email = (request.POST.get("email") or "").strip()
    phone = (request.POST.get("phone") or "").strip()
    course_id = request.POST.get("course")
    semester = request.POST.get("semester") or "1"
    year = request.POST.get("admission_year") or str(timezone.now().year)
    username = (request.POST.get("username") or "").strip()
    password = request.POST.get("password") or ""
    if not student_id or not name or not email or not course_id:
        return redirect("admin_students")
    course = Course.objects.filter(course_id=course_id, status="Active").first()
    if course is None:
        return redirect("admin_students")
    if Student.objects.filter(student_id=student_id).exists() or Student.objects.filter(email=email).exists():
        return redirect("admin_students")
    parsed_year = parse_int(year, timezone.now().year, minimum=1)
    parsed_semester = parse_int(semester, 1, minimum=1)
    student = Student.objects.create(student_id=student_id, name=name, email=email, phone=phone, course=course, admission_year=parsed_year, semester=parsed_semester, status="Active")
    if username and password:
        user = User.objects.create_user(username=username, email=email, password=password, first_name=name.split()[0], last_name=" ".join(name.split()[1:]) if len(name.split()) > 1 else "")
        UserProfile.objects.create(user=user, role="Student", registration_status="Approved", student=student)
    ActivityLog.objects.create(user=request.user, action=f"Added student: {student.student_id} - {student.name}")
    return redirect("admin_students")


@login_required
def admin_edit_student(request, student_id):
    if not is_admin_user(request):
        return redirect("dashboard")
    if request.method != "POST":
        return redirect(f"/admin/students/?edit={student_id}")
    student = Student.objects.filter(student_id=student_id).first()
    if student is None:
        return redirect("admin_students")
    name = (request.POST.get("name") or "").strip()
    email = (request.POST.get("email") or "").strip()
    phone = (request.POST.get("phone") or "").strip()
    semester = request.POST.get("semester") or student.semester
    year = request.POST.get("admission_year") or student.admission_year
    status = (request.POST.get("status") or student.status).strip()
    if not name or not email:
        return redirect(f"/admin/students/?edit={student_id}")
    course_id = request.POST.get("course")
    if course_id:
        try:
            student.course = Course.objects.get(course_id=course_id, status="Active")
        except Course.DoesNotExist:
            pass
    student.name = name
    student.email = email
    student.phone = phone
    student.semester = parse_int(semester, student.semester, minimum=1)
    student.admission_year = parse_int(year, student.admission_year, minimum=1)
    student.status = status if status in {"Active", "Inactive", "Graduated"} else student.status
    student.save()
    ActivityLog.objects.create(user=request.user, action=f"Updated student: {student.student_id} - {student.name}")
    return redirect("admin_students")


@login_required
def admin_delete_student(request, student_id):
    if not is_admin_user(request):
        return redirect("dashboard")
    if request.method != "POST":
        return redirect("admin_students")
    student = Student.objects.filter(student_id=student_id).first()
    if student is None:
        return redirect("admin_students")
    profile = UserProfile.objects.filter(student=student).select_related("user").first()
    if profile is not None:
        user = profile.user
        profile.delete()
        if user is not None:
            user.delete()
    student.delete()
    ActivityLog.objects.create(user=request.user, action=f"Deleted student: {student_id}")
    return redirect("admin_students")


@login_required
def admin_teachers(request):
    if not is_admin_user(request):
        return redirect("dashboard")
    teachers = Teacher.objects.select_related("department").order_by("teacher_id")
    query = (request.GET.get("q") or "").strip()
    if query:
        teachers = teachers.filter(Q(teacher_id__icontains=query) | Q(name__icontains=query) | Q(email__icontains=query))
    edit_teacher = None
    edit_id = (request.GET.get("edit") or "").strip()
    if edit_id:
        edit_teacher = Teacher.objects.select_related("department").filter(teacher_id=edit_id).first()
    return render(request, "students/admin_teachers.html", {"teachers": teachers, "search": query, "departments": Department.objects.filter(status="Active"), "edit_teacher": edit_teacher})


@login_required
def admin_add_teacher(request):
    if not is_admin_user(request):
        return redirect("dashboard")
    if request.method != "POST":
        return redirect("admin_teachers")
    teacher_id = (request.POST.get("teacher_id") or "").strip()
    name = (request.POST.get("name") or "").strip()
    email = (request.POST.get("email") or "").strip()
    department_id = request.POST.get("department")
    status = (request.POST.get("status") or "Active").strip()
    username = (request.POST.get("username") or "").strip()
    password = request.POST.get("password") or ""
    if not teacher_id or not name or not department_id:
        return redirect("admin_teachers")
    department = Department.objects.filter(department_id=department_id, status="Active").first()
    if department is None:
        return redirect("admin_teachers")
    if Teacher.objects.filter(teacher_id=teacher_id).exists() or (email and Teacher.objects.filter(email=email).exists()):
        return redirect("admin_teachers")
    teacher = Teacher.objects.create(teacher_id=teacher_id, name=name, email=email or None, department=department, status=status if status in {"Active", "Inactive"} else "Active")
    if username and password and len(password) >= 6:
        user = User.objects.create_user(username=username, email=email or "", password=password, first_name=name.split()[0], last_name=" ".join(name.split()[1:]) if len(name.split()) > 1 else "")
        UserProfile.objects.create(user=user, role="Teacher", registration_status="Approved", teacher=teacher)
    ActivityLog.objects.create(user=request.user, action=f"Added teacher: {teacher.teacher_id} - {teacher.name}")
    return redirect("admin_teachers")


@login_required
def admin_edit_teacher(request, teacher_id):
    if not is_admin_user(request):
        return redirect("dashboard")
    if request.method != "POST":
        return redirect(f"/admin/teachers/?edit={teacher_id}")
    teacher = Teacher.objects.filter(teacher_id=teacher_id).first()
    if teacher is None:
        return redirect("admin_teachers")
    name = (request.POST.get("name") or "").strip()
    email = (request.POST.get("email") or "").strip()
    department_id = request.POST.get("department")
    status = (request.POST.get("status") or "Active").strip()
    username = (request.POST.get("username") or "").strip()
    password = request.POST.get("password") or ""
    if not name or not department_id:
        return redirect(f"/admin/teachers/?edit={teacher_id}")
    department = Department.objects.filter(department_id=department_id, status="Active").first()
    if department is None:
        return redirect(f"/admin/teachers/?edit={teacher_id}")
    teacher.name = name
    teacher.email = email or None
    teacher.department = department
    teacher.status = status if status in {"Active", "Inactive"} else "Active"
    teacher.save()
    profile = UserProfile.objects.filter(teacher=teacher).select_related("user").first()
    if profile is not None:
        user = profile.user
        if username and user.username != username:
            if User.objects.filter(username=username).exclude(pk=user.pk).exists():
                return redirect(f"/admin/teachers/?edit={teacher_id}")
            user.username = username
        user.email = email or ""
        if password and len(password) >= 6:
            user.set_password(password)
        user.save()
    elif username and password and len(password) >= 6:
        user = User.objects.create_user(username=username, email=email or "", password=password, first_name=name.split()[0], last_name=" ".join(name.split()[1:]) if len(name.split()) > 1 else "")
        UserProfile.objects.create(user=user, role="Teacher", registration_status="Approved", teacher=teacher)
    ActivityLog.objects.create(user=request.user, action=f"Updated teacher: {teacher.teacher_id} - {teacher.name}")
    return redirect("admin_teachers")


@login_required
def admin_delete_teacher(request, teacher_id):
    if not is_admin_user(request):
        return redirect("dashboard")
    if request.method != "POST":
        return redirect("admin_teachers")
    teacher = Teacher.objects.filter(teacher_id=teacher_id).first()
    if teacher is None:
        return redirect("admin_teachers")
    profile = UserProfile.objects.filter(teacher=teacher).select_related("user").first()
    if profile is not None:
        user = profile.user
        profile.delete()
        if user is not None:
            user.delete()
    teacher.delete()
    ActivityLog.objects.create(user=request.user, action=f"Deleted teacher: {teacher_id}")
    return redirect("admin_teachers")


@login_required
def admin_teacher_subjects(request):
    if not is_admin_user(request):
        return redirect("dashboard")

    assignments = TeacherSubject.objects.select_related("teacher", "subject", "subject__course").order_by("teacher__name", "subject__subject_name")
    query = (request.GET.get("q") or "").strip()
    if query:
        assignments = assignments.filter(
            Q(teacher__name__icontains=query)
            | Q(teacher__teacher_id__icontains=query)
            | Q(subject__subject_name__icontains=query)
            | Q(subject__subject_code__icontains=query)
        )

    if request.method == "POST":
        teacher_id = (request.POST.get("teacher") or "").strip()
        subject_id = (request.POST.get("subject") or "").strip()
        academic_year = (request.POST.get("academic_year") or "").strip()
        semester = request.POST.get("semester") or ""
        if teacher_id and subject_id and academic_year and semester:
            teacher = Teacher.objects.filter(teacher_id=teacher_id).first()
            subject = Subject.objects.filter(subject_id=subject_id).first()
            if teacher and subject:
                TeacherSubject.objects.get_or_create(
                    teacher=teacher,
                    subject=subject,
                    academic_year=academic_year,
                    semester=parse_int(semester, 1, minimum=1),
                )
        return redirect("admin_teacher_subjects")

    return render(
        request,
        "students/admin_teacher_subjects.html",
        {
            "assignments": assignments,
            "search": query,
            "teachers": Teacher.objects.filter(status="Active").order_by("name"),
            "subjects": Subject.objects.filter(status="Active").select_related("course").order_by("subject_name"),
        },
    )


@login_required
def admin_delete_teacher_subject(request, assignment_id):
    if not is_admin_user(request):
        return redirect("dashboard")
    if request.method != "POST":
        return redirect("admin_teacher_subjects")
    TeacherSubject.objects.filter(teacher_subject_id=assignment_id).delete()
    return redirect("admin_teacher_subjects")


@login_required
def admin_reports(request):
    if not is_admin_user(request):
        return redirect("dashboard")

    students = Student.objects.select_related("course").order_by("student_id")
    attendance_stats = []
    for student in students:
        records = Attendance.objects.filter(student=student)
        total = records.count()
        present = records.filter(status="Present").count()
        pct = round((present / total) * 100, 2) if total else 0
        attendance_stats.append({
            "student": student,
            "attendance_pct": pct,
            "present": present,
            "total": total,
        })

    low_attendance = sorted(attendance_stats, key=lambda item: item["attendance_pct"])[:8]

    marks_stats = []
    for student in students:
        marks = Mark.objects.filter(student=student)
        if not marks.exists():
            continue
        percentages = []
        for item in marks:
            try:
                percentages.append((float(item.marks_obtained) / float(item.max_marks)) * 100 if item.max_marks else 0)
            except Exception:
                continue
        avg = round(sum(percentages) / len(percentages), 2) if percentages else 0
        marks_stats.append({"student": student, "average_mark": avg})

    performance = sorted(marks_stats, key=lambda item: item["average_mark"], reverse=True)[:8]

    total_attendance = Attendance.objects.count()
    present_count = Attendance.objects.filter(status="Present").count()
    overall_attendance = round((present_count / total_attendance) * 100, 2) if total_attendance else 0

    total_fee_paid = float(Fee.objects.aggregate(total_paid=Sum("amount_paid"))["total_paid"] or 0)
    total_fee_due = float(Fee.objects.aggregate(total_due=Sum("amount"))["total_due"] or 0) - total_fee_paid

    return render(
        request,
        "students/admin_reports.html",
        {
            "overall_attendance": overall_attendance,
            "total_students": students.count(),
            "total_teachers": Teacher.objects.count(),
            "total_subjects": Subject.objects.filter(status="Active").count(),
            "total_fee_paid": total_fee_paid,
            "total_fee_due": max(total_fee_due, 0),
            "low_attendance": low_attendance,
            "performance": performance,
        },
    )


@login_required
def admin_departments(request):
    if not is_admin_user(request):
        return redirect("dashboard")
    departments = Department.objects.order_by("department_name")
    query = (request.GET.get("q") or "").strip()
    if query:
        departments = departments.filter(Q(department_name__icontains=query) | Q(description__icontains=query))
    edit_department = None
    edit_id = (request.GET.get("edit") or "").strip()
    if edit_id:
        edit_department = Department.objects.filter(department_id=int(edit_id)).first()
    return render(
        request,
        "students/admin_departments.html",
        {"departments": departments, "search": query, "edit_department": edit_department},
    )


@login_required
def admin_add_department(request):
    if not is_admin_user(request):
        return redirect("dashboard")
    if request.method != "POST":
        return redirect("admin_departments")
    name = (request.POST.get("department_name") or "").strip()
    if not name:
        return redirect("admin_departments")
    Department.objects.create(
        department_name=name,
        description=request.POST.get("description") or "",
        status=(request.POST.get("status") or "Active").strip(),
    )
    return redirect("admin_departments")


@login_required
def admin_edit_department(request, department_id):
    if not is_admin_user(request):
        return redirect("dashboard")
    if request.method != "POST":
        return redirect(f"/admin/departments/?edit={department_id}")
    department = Department.objects.filter(department_id=department_id).first()
    if department is None:
        return redirect("admin_departments")
    department.department_name = (request.POST.get("department_name") or department.department_name).strip()
    department.description = request.POST.get("description") or ""
    status = (request.POST.get("status") or department.status).strip()
    department.status = status if status in {"Active", "Inactive"} else department.status
    department.save()
    return redirect("admin_departments")


@login_required
def admin_delete_department(request, department_id):
    if not is_admin_user(request):
        return redirect("dashboard")
    if request.method != "POST":
        return redirect("admin_departments")
    Department.objects.filter(department_id=department_id).delete()
    return redirect("admin_departments")


@login_required
def admin_courses(request):
    if not is_admin_user(request):
        return redirect("dashboard")
    courses = Course.objects.select_related("department").order_by("course_name")
    query = (request.GET.get("q") or "").strip()
    if query:
        courses = courses.filter(Q(course_name__icontains=query) | Q(department__department_name__icontains=query))
    edit_course = None
    edit_id = (request.GET.get("edit") or "").strip()
    if edit_id:
        edit_course = Course.objects.select_related("department").filter(course_id=int(edit_id)).first()
    return render(
        request,
        "students/admin_courses.html",
        {"courses": courses, "search": query, "departments": Department.objects.filter(status="Active"), "edit_course": edit_course},
    )


@login_required
def admin_add_course(request):
    if not is_admin_user(request):
        return redirect("dashboard")
    if request.method != "POST":
        return redirect("admin_courses")
    name = (request.POST.get("course_name") or "").strip()
    department_id = request.POST.get("department")
    if not name or not department_id:
        return redirect("admin_courses")
    department = Department.objects.filter(department_id=department_id).first()
    if department is None:
        return redirect("admin_courses")
    Course.objects.create(
        course_name=name,
        department=department,
        duration_years=parse_int(request.POST.get("duration_years"), 4, minimum=1),
        status=(request.POST.get("status") or "Active").strip(),
    )
    return redirect("admin_courses")


@login_required
def admin_edit_course(request, course_id):
    if not is_admin_user(request):
        return redirect("dashboard")
    if request.method != "POST":
        return redirect(f"/admin/courses/?edit={course_id}")
    course = Course.objects.filter(course_id=course_id).first()
    if course is None:
        return redirect("admin_courses")
    course.course_name = (request.POST.get("course_name") or course.course_name).strip()
    department_id = request.POST.get("department")
    if department_id:
        department = Department.objects.filter(department_id=department_id).first()
        if department is not None:
            course.department = department
    course.duration_years = parse_int(request.POST.get("duration_years"), course.duration_years, minimum=1)
    course.status = (request.POST.get("status") or course.status).strip()
    course.save()
    return redirect("admin_courses")


@login_required
def admin_delete_course(request, course_id):
    if not is_admin_user(request):
        return redirect("dashboard")
    if request.method != "POST":
        return redirect("admin_courses")
    Course.objects.filter(course_id=course_id).delete()
    return redirect("admin_courses")


@login_required
def admin_enrollments(request):
    if not is_admin_user(request):
        return redirect("dashboard")

    enrollments = Enrollment.objects.select_related(
        "student",
        "subject",
        "subject__course"
    ).order_by("-academic_year", "-semester", "student__student_id")

    return render(
        request,
        "students/admin_enrollments.html",
        {"enrollments": enrollments}
    )


@login_required
def admin_exams(request):
    if not is_admin_user(request):
        return redirect("dashboard")

    exams = Exam.objects.order_by("-start_date", "-end_date", "exam_name")

    return render(
        request,
        "students/admin_exams.html",
        {"exams": exams}
    )


@login_required
def admin_fees(request):
    if not is_admin_user(request):
        return redirect("dashboard")

    fees = Fee.objects.select_related("student").order_by("-payment_date", "-amount")

    return render(
        request,
        "students/admin_fees.html",
        {"fees": fees}
    )


@login_required
def student_payments(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return redirect("login")

    if profile.role != "Student":
        return redirect("dashboard")

    student = profile.student
    if student is None:
        return redirect("dashboard")

    outstanding_fees = Fee.objects.filter(student=student).order_by("academic_year", "semester")

    if request.method == "POST":
        fee_id = request.POST.get("fee_id")
        amount_raw = (request.POST.get("amount") or "0").strip()
        method = request.POST.get("method") or "Cash"
        reference = (request.POST.get("reference") or "").strip()
        notes = (request.POST.get("notes") or "").strip()

        try:
            amount = Decimal(amount_raw)
        except (InvalidOperation, ValueError):
            amount = Decimal("0")

        valid_methods = {choice[0] for choice in FeePayment._meta.get_field("payment_method").choices}
        fee = outstanding_fees.filter(fee_id=fee_id).first()
        remaining = (fee.amount - fee.amount_paid) if fee is not None else Decimal("0")
        if fee is None or amount <= 0 or amount > remaining or method not in valid_methods:
            return render(request, "students/student_payments.html", {
                "student": student,
                "fees": outstanding_fees,
                "payments": FeePayment.objects.filter(fee__student=student).select_related("fee").order_by("-payment_date"),
                "error": "Please choose a valid fee and enter a payment amount greater than zero.",
            })

        with transaction.atomic():
            fee = Fee.objects.select_for_update().get(pk=fee.pk)
            remaining = fee.amount - fee.amount_paid
            if amount > remaining:
                return render(request, "students/student_payments.html", {
                    "student": student,
                    "fees": outstanding_fees,
                    "payments": FeePayment.objects.filter(fee__student=student).select_related("fee").order_by("-payment_date"),
                    "error": "The payment cannot exceed the remaining fee balance.",
                })
            fee.amount_paid += amount
            fee.payment_date = timezone.now().date()
            fee.status = "Paid" if fee.amount_paid >= fee.amount else "Partial"
            fee.save(update_fields=["amount_paid", "payment_date", "status"])
            FeePayment.objects.create(
                fee=fee,
                amount=amount,
                payment_method=method,
                reference=reference,
                status="Completed",
                notes=notes,
                recorded_by=request.user,
            )
        return redirect("student_payments")

    return render(request, "students/student_payments.html", {
        "student": student,
        "fees": outstanding_fees,
        "payments": FeePayment.objects.filter(fee__student=student).select_related("fee").order_by("-payment_date"),
    })


@login_required
def admin_payments(request):
    if not is_admin_user(request):
        return redirect("dashboard")

    payments = FeePayment.objects.select_related("fee", "fee__student", "recorded_by").order_by("-payment_date")
    return render(request, "students/admin_payments.html", {"payments": payments})


@login_required
def admin_subjects(request):
    if not is_admin_user(request):
        return redirect("dashboard")
    subjects = Subject.objects.select_related("course").order_by("subject_name")
    query = (request.GET.get("q") or "").strip()
    if query:
        subjects = subjects.filter(Q(subject_code__icontains=query) | Q(subject_name__icontains=query) | Q(course__course_name__icontains=query))
    edit_subject = None
    edit_id = (request.GET.get("edit") or "").strip()
    if edit_id:
        edit_subject = Subject.objects.select_related("course").filter(subject_id=int(edit_id)).first()
    return render(
        request,
        "students/admin_subjects.html",
        {"subjects": subjects, "search": query, "courses": Course.objects.filter(status="Active"), "edit_subject": edit_subject},
    )


@login_required
def admin_add_subject(request):
    if not is_admin_user(request):
        return redirect("dashboard")
    if request.method != "POST":
        return redirect("admin_subjects")
    code = (request.POST.get("subject_code") or "").strip()
    name = (request.POST.get("subject_name") or "").strip()
    course_id = request.POST.get("course")
    if not code or not name or not course_id:
        return redirect("admin_subjects")
    course = Course.objects.filter(course_id=course_id).first()
    if course is None:
        return redirect("admin_subjects")
    Subject.objects.create(
        subject_code=code,
        subject_name=name,
        course=course,
        semester=parse_int(request.POST.get("semester"), 1, minimum=1),
        credits=parse_int(request.POST.get("credits"), 4, minimum=1),
        status=(request.POST.get("status") or "Active").strip(),
    )
    return redirect("admin_subjects")


@login_required
def admin_edit_subject(request, subject_id):
    if not is_admin_user(request):
        return redirect("dashboard")
    if request.method != "POST":
        return redirect(f"/admin/subjects/?edit={subject_id}")
    subject = Subject.objects.filter(subject_id=subject_id).first()
    if subject is None:
        return redirect("admin_subjects")
    subject.subject_code = (request.POST.get("subject_code") or subject.subject_code).strip()
    subject.subject_name = (request.POST.get("subject_name") or subject.subject_name).strip()
    course_id = request.POST.get("course")
    if course_id:
        course = Course.objects.filter(course_id=course_id).first()
        if course is not None:
            subject.course = course
    subject.semester = parse_int(request.POST.get("semester"), subject.semester, minimum=1)
    subject.credits = parse_int(request.POST.get("credits"), subject.credits, minimum=1)
    subject.status = (request.POST.get("status") or subject.status).strip()
    subject.save()
    return redirect("admin_subjects")


@login_required
def admin_delete_subject(request, subject_id):
    if not is_admin_user(request):
        return redirect("dashboard")
    if request.method != "POST":
        return redirect("admin_subjects")
    Subject.objects.filter(subject_id=subject_id).delete()
    return redirect("admin_subjects")
