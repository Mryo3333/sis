from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from students.views import (
   home_view,
   demo_request,
   login_view,
   logout_view,
   dashboard,
   student_profile,
   attendance,
   marks,
   notices,
   timetable,
   parent_dashboard,
   student_register,
   pending_registrations,
   approve_student,
   reject_student,
   admin_students,
   admin_add_student,
   admin_edit_student,
   admin_delete_student,
   admin_teachers,
   admin_add_teacher,
   admin_edit_teacher,
   admin_delete_teacher,
   admin_departments,
   admin_add_department,
   admin_edit_department,
   admin_delete_department,
   admin_courses,
   admin_add_course,
   admin_edit_course,
   admin_delete_course,
   admin_enrollments,
   admin_exams,
   admin_fees,
   admin_subjects,
   admin_add_subject,
   admin_edit_subject,
   admin_delete_subject,
   admin_teacher_subjects,
   admin_delete_teacher_subject,
   admin_reports,
   admin_notices,
   admin_delete_notice,
   admin_timetable,
   admin_delete_timetable,
   admin_admissions,
   admin_results,
   admin_school_settings,
   admin_notifications,
   admin_analytics,
   admin_campsuses,
   admin_billing,
   admin_library,
   admin_transport,
   admin_hr,
   admin_events,
   student_admissions,
   student_results,
   student_payments,
   admin_payments,
   teacher_students,
   teacher_subjects,
)


urlpatterns = [

    # ========================================================
    # CUSTOM SIS ADMIN PAGES
    # IMPORTANT: These MUST come before Django's admin/ route.
    # ========================================================

    path(
        "admin/pending-registrations/",
        pending_registrations,
        name="pending_registrations"
    ),

    path(
        "admin/approve-student/<int:profile_id>/",
        approve_student,
        name="approve_student"
    ),

    path(
        "admin/reject-student/<int:profile_id>/",
        reject_student,
        name="reject_student"
    ),

    path(
        "admin/students/",
        admin_students,
        name="admin_students"
    ),

    path(
        "admin/students/add/",
        admin_add_student,
        name="admin_add_student"
    ),

    path(
        "admin/students/<str:student_id>/edit/",
        admin_edit_student,
        name="admin_edit_student"
    ),

    path(
        "admin/students/<str:student_id>/delete/",
        admin_delete_student,
        name="admin_delete_student"
    ),

    path(
        "admin/teachers/",
        admin_teachers,
        name="admin_teachers"
    ),

    path(
        "admin/teachers/add/",
        admin_add_teacher,
        name="admin_add_teacher"
    ),

    path(
        "admin/teachers/<str:teacher_id>/edit/",
        admin_edit_teacher,
        name="admin_edit_teacher"
    ),

    path(
        "admin/teachers/<str:teacher_id>/delete/",
        admin_delete_teacher,
        name="admin_delete_teacher"
    ),

    path(
        "admin/departments/",
        admin_departments,
        name="admin_departments"
    ),

    path(
        "admin/departments/add/",
        admin_add_department,
        name="admin_add_department"
    ),

    path(
        "admin/departments/<int:department_id>/edit/",
        admin_edit_department,
        name="admin_edit_department"
    ),

    path(
        "admin/departments/<int:department_id>/delete/",
        admin_delete_department,
        name="admin_delete_department"
    ),

    path(
        "admin/courses/",
        admin_courses,
        name="admin_courses"
    ),

    path(
        "admin/courses/add/",
        admin_add_course,
        name="admin_add_course"
    ),

    path(
        "admin/courses/<int:course_id>/edit/",
        admin_edit_course,
        name="admin_edit_course"
    ),

    path(
        "admin/courses/<int:course_id>/delete/",
        admin_delete_course,
        name="admin_delete_course"
    ),

    path(
        "admin/subjects/",
        admin_subjects,
        name="admin_subjects"
    ),

    path(
        "admin/subjects/add/",
        admin_add_subject,
        name="admin_add_subject"
    ),

    path(
        "admin/subjects/<int:subject_id>/edit/",
        admin_edit_subject,
        name="admin_edit_subject"
    ),

    path(
        "admin/subjects/<int:subject_id>/delete/",
        admin_delete_subject,
        name="admin_delete_subject"
    ),

    path(
        "admin/teacher-subjects/",
        admin_teacher_subjects,
        name="admin_teacher_subjects"
    ),

    path(
        "admin/teacher-subjects/<int:assignment_id>/delete/",
        admin_delete_teacher_subject,
        name="admin_delete_teacher_subject"
    ),

    path(
        "admin/reports/",
        admin_reports,
        name="admin_reports"
    ),

    path(
        "admin/enrollments/",
        admin_enrollments,
        name="admin_enrollments"
    ),

    path(
        "admin/exams/",
        admin_exams,
        name="admin_exams"
    ),

    path(
        "admin/fees/",
        admin_fees,
        name="admin_fees"
    ),

    path(
        "admin/notices/",
        admin_notices,
        name="admin_notices"
    ),

    path(
        "admin/notices/<int:notice_id>/delete/",
        admin_delete_notice,
        name="admin_delete_notice"
    ),

    path(
        "admin/timetable/",
        admin_timetable,
        name="admin_timetable"
    ),

    path(
        "admin/timetable/<int:timetable_id>/delete/",
        admin_delete_timetable,
        name="admin_delete_timetable"
    ),

    path(
        "admin/admissions/",
        admin_admissions,
        name="admin_admissions"
    ),

    path(
        "admin/results/",
        admin_results,
        name="admin_results"
    ),

    path(
        "admin/payments/",
        admin_payments,
        name="admin_payments"
    ),

    path(
        "admin/settings/",
        admin_school_settings,
        name="admin_school_settings"
    ),

    path(
        "admin/analytics/",
        admin_analytics,
        name="admin_analytics"
    ),

    path(
        "admin/campuses/",
        admin_campsuses,
        name="admin_campuses"
    ),

    path(
        "admin/billing/",
        admin_billing,
        name="admin_billing"
    ),

    path(
        "admin/communications/",
        admin_notifications,
        name="admin_notifications"
    ),

    path(
        "admin/library/",
        admin_library,
        name="admin_library"
    ),

    path(
        "admin/transport/",
        admin_transport,
        name="admin_transport"
    ),

    path(
        "admin/hr/",
        admin_hr,
        name="admin_hr"
    ),

    path(
        "admin/events/",
        admin_events,
        name="admin_events"
    ),


    # ========================================================
    # DJANGO ADMIN
    # Keep this AFTER the custom /admin/... SIS routes.
    # ========================================================

    path(
        "admin/",
        admin.site.urls
    ),


    # ========================================================
    # LOGIN
    # ========================================================

    path(
        "",
        home_view,
        name="home"
    ),

    path(
        "home/",
        home_view,
        name="home"
    ),

    path(
        "demo/",
        demo_request,
        name="demo_request"
    ),

    path(
        "login/",
        login_view,
        name="login"
    ),


    # ========================================================
    # STUDENT REGISTRATION
    # ========================================================

    path(
        "register/",
        student_register,
        name="student_register"
    ),


    # ========================================================
    # LOGOUT
    # ========================================================

    path(
        "logout/",
        logout_view,
        name="logout"
    ),


    # ========================================================
    # DASHBOARD
    # ========================================================

    path(
        "dashboard/",
        dashboard,
        name="dashboard"
    ),

    path(
        "student/profile/",
        student_profile,
        name="student_profile"
    ),

    path(
        "notices/",
        notices,
        name="notices"
    ),

    path(
        "timetable/",
        timetable,
        name="timetable"
    ),

    path(
        "parent-dashboard/",
        parent_dashboard,
        name="parent_dashboard"
    ),

    path(
        "student/admissions/",
        student_admissions,
        name="student_admissions"
    ),

    path(
        "student/results/",
        student_results,
        name="student_results"
    ),

    path(
        "student/payments/",
        student_payments,
        name="student_payments"
    ),


    # ========================================================
    # TEACHER ATTENDANCE
    # ========================================================

    path(
        "attendance/",
        attendance,
        name="attendance"
    ),


    # ========================================================
    # TEACHER MARKS
    # ========================================================

    path(
        "marks/",
        marks,
        name="marks"
    ),

    path(
        "teacher/students/",
        teacher_students,
        name="teacher_students"
    ),

    path(
        "teacher/subjects/",
        teacher_subjects,
        name="teacher_subjects"
    ),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
