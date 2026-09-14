from django.contrib import admin
from django.urls import path

from students.views import (
    login_view,
    logout_view,
    dashboard,
    attendance,
    marks,
    student_register,
    pending_registrations,
    approve_student,
    reject_student,
    teacher_students,
)


urlpatterns = [

    # ========================================================
    # LOGIN
    # ========================================================

    path(
        "",
        login_view,
        name="login"
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

    # ========================================================
    # TEACHER STUDENTS
    # ========================================================

    path(
        "teacher/students/",
        teacher_students,
        name="teacher_students"
    ),


    # ========================================================
    # STUDENT APPROVAL SYSTEM
    # ========================================================
    #
    # IMPORTANT:
    # These MUST come BEFORE "admin/".
    #
    # Otherwise Django's built-in admin catches the URL first.
    #

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


    # ========================================================
    # DJANGO ADMIN
    # ========================================================

    path(
        "admin/",
        admin.site.urls
    ),

]