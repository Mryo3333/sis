from django.contrib import admin
from django.contrib.auth.models import User

from .models import (
    Department,
    Course,
    Teacher,
    Subject,
    TeacherSubject,
    Student,
    Enrollment,
    Attendance,
    Exam,
    Mark,
    Fee,
    UserProfile,
    ActivityLog,
    AdmissionApplication,
)


# ============================================================
# DEPARTMENT
# ============================================================

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):

    list_display = (
        "department_id",
        "department_name",
        "status",
    )

    search_fields = (
        "department_name",
    )

    list_filter = (
        "status",
    )


# ============================================================
# COURSE
# ============================================================

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):

    list_display = (
        "course_id",
        "course_name",
        "department",
        "duration_years",
        "status",
    )

    search_fields = (
        "course_name",
    )

    list_filter = (
        "department",
        "status",
    )


# ============================================================
# TEACHER
# ============================================================

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):

    list_display = (
        "teacher_id",
        "name",
        "email",
        "department",
        "status",
    )

    search_fields = (
        "teacher_id",
        "name",
        "email",
    )

    list_filter = (
        "department",
        "status",
    )


# ============================================================
# SUBJECT
# ============================================================

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):

    list_display = (
        "subject_id",
        "subject_code",
        "subject_name",
        "course",
        "semester",
        "credits",
        "status",
    )

    search_fields = (
        "subject_code",
        "subject_name",
    )

    list_filter = (
        "course",
        "semester",
        "status",
    )


# ============================================================
# TEACHER SUBJECT
# ============================================================

@admin.register(TeacherSubject)
class TeacherSubjectAdmin(admin.ModelAdmin):

    list_display = (
        "teacher",
        "subject",
        "academic_year",
        "semester",
    )

    list_filter = (
        "academic_year",
        "semester",
    )

    search_fields = (
        "teacher__name",
        "subject__subject_name",
        "subject__subject_code",
    )


# ============================================================
# STUDENT
# ============================================================

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):

    list_display = (
        "student_id",
        "name",
        "email",
        "course",
        "semester",
        "admission_year",
        "registration_status",
        "status",
    )

    search_fields = (
        "student_id",
        "name",
        "email",
        "phone",
    )

    list_filter = (
        "status",
        "course",
        "semester",
        "admission_year",
    )


    def registration_status(self, obj):

        try:

            profile = obj.user_profile

            return profile.registration_status

        except UserProfile.DoesNotExist:

            return "No Profile"

    registration_status.short_description = "Registration"

    # ========================================================
    # APPROVE STUDENTS
    # ========================================================

    @admin.action(description="Approve selected students")
    def approve_students(self, request, queryset):

        approved = 0

        for student in queryset:

            try:

                profile = student.user_profile

            except UserProfile.DoesNotExist:

                continue

            profile.registration_status = "Approved"
            profile.save()

            if profile.user:

                profile.user.is_active = True
                profile.user.save()

            approved += 1

        self.message_user(
            request,
            f"{approved} student(s) approved successfully."
        )

    # ========================================================
    # REJECT STUDENTS
    # ========================================================

    @admin.action(description="Reject selected students")
    def reject_students(self, request, queryset):

        rejected = 0

        for student in queryset:

            try:

                profile = student.user_profile

            except UserProfile.DoesNotExist:

                continue

            profile.registration_status = "Rejected"
            profile.save()

            if profile.user:

                profile.user.is_active = False
                profile.user.save()

            rejected += 1

        self.message_user(
            request,
            f"{rejected} student(s) rejected.")


@admin.register(AdmissionApplication)
class AdmissionApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "application_id",
        "applicant_name",
        "email",
        "phone",
        "course",
        "source",
        "status",
        "created_at",
    )

    search_fields = (
        "applicant_name",
        "email",
        "phone",
    )

    list_filter = (
        "status",
        "source",
        "created_at",
    )

    list_editable = ("status",)
    readonly_fields = ("created_at",)


# ============================================================
# ENROLLMENT
# ============================================================

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):

    list_display = (
        "enrollment_id",
        "student",
        "subject",
        "academic_year",
        "semester",
        "enrollment_date",
        "status",
    )

    search_fields = (
        "student__student_id",
        "student__name",
        "subject__subject_name",
        "subject__subject_code",
    )

    list_filter = (
        "academic_year",
        "semester",
        "status",
    )


# ============================================================
# ATTENDANCE
# ============================================================

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):

    list_display = (
        "attendance_id",
        "student",
        "subject",
        "date",
        "status",
        "marked_by",
    )

    search_fields = (
        "student__student_id",
        "student__name",
        "subject__subject_code",
        "subject__subject_name",
    )

    list_filter = (
        "status",
        "date",
        "subject",
    )


# ============================================================
# EXAM
# ============================================================

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):

    list_display = (
        "exam_id",
        "exam_name",
        "exam_type",
        "semester",
        "academic_year",
        "start_date",
        "end_date",
    )

    search_fields = (
        "exam_name",
        "academic_year",
    )

    list_filter = (
        "exam_type",
        "semester",
        "academic_year",
    )


# ============================================================
# MARK
# ============================================================

@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):

    list_display = (
        "mark_id",
        "student",
        "subject",
        "exam",
        "marks_obtained",
        "max_marks",
        "entered_by",
        "created_at",
    )

    search_fields = (
        "student__student_id",
        "student__name",
        "subject__subject_code",
        "subject__subject_name",
        "exam__exam_name",
    )

    list_filter = (
        "subject",
        "exam",
    )


# ============================================================
# FEE
# ============================================================

@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):

    list_display = (
        "fee_id",
        "student",
        "academic_year",
        "semester",
        "fee_type",
        "amount",
        "amount_paid",
        "status",
        "payment_date",
    )

    search_fields = (
        "student__student_id",
        "student__name",
    )

    list_filter = (
        "academic_year",
        "semester",
        "fee_type",
        "status",
    )


# ============================================================
# USER PROFILE
# ============================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "role",
        "student",
        "teacher",
        "registration_status",
    )

    search_fields = (
        "user__username",
        "student__student_id",
        "student__name",
        "teacher__teacher_id",
        "teacher__name",
    )

    list_filter = (
        "role",
        "registration_status",
    )

    actions = (
        "approve_profiles",
        "reject_profiles",
    )

    # ========================================================
    # APPROVE
    # ========================================================

    @admin.action(description="Approve selected registrations")
    def approve_profiles(self, request, queryset):

        approved = 0

        for profile in queryset:

            profile.registration_status = "Approved"
            profile.save()

            if profile.user:

                profile.user.is_active = True
                profile.user.save()

            approved += 1

        self.message_user(
            request,
            f"{approved} registration(s) approved successfully."
        )

    # ========================================================
    # REJECT
    # ========================================================

    @admin.action(description="Reject selected registrations")
    def reject_profiles(self, request, queryset):

        rejected = 0

        for profile in queryset:

            profile.registration_status = "Rejected"
            profile.save()

            if profile.user:

                profile.user.is_active = False
                profile.user.save()

            rejected += 1

        self.message_user(
            request,
            f"{rejected} registration(s) rejected."
        )


# ============================================================
# ACTIVITY LOG
# ============================================================

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):

    list_display = (
        "log_id",
        "user",
        "action",
        "timestamp",
    )

    search_fields = (
        "user__username",
        "action",
    )

    list_filter = (
        "timestamp",
    )


# ============================================================
# DJANGO USERS
# ============================================================

# We intentionally DO NOT unregister Django's built-in User.
# The normal Django Users section remains available.