from django.db import connection

from .models import (
    Student,
    Course,
    Teacher,
    Subject,
    Enrollment,
    Attendance,
    Mark,
)


# ============================================================
# 1. INNER JOIN
# Students + Courses
# ============================================================

def students_with_courses():

    query = """
        SELECT
            students_student.student_id,
            students_student.name,
            students_course.course_name
        FROM students_student
        INNER JOIN students_course
            ON students_student.course_id = students_course.course_id
    """

    with connection.cursor() as cursor:

        cursor.execute(query)

        return cursor.fetchall()


# ============================================================
# 2. JOIN
# Teachers + Subjects
# ============================================================

def teachers_with_subjects():

    query = """
        SELECT
            students_teacher.teacher_id,
            students_teacher.name,
            students_subject.subject_name
        FROM students_teacher
        INNER JOIN students_teachersubject
            ON students_teacher.teacher_id =
               students_teachersubject.teacher_id
        INNER JOIN students_subject
            ON students_teachersubject.subject_id =
               students_subject.subject_id
    """

    with connection.cursor() as cursor:

        cursor.execute(query)

        return cursor.fetchall()


# ============================================================
# 3. JOIN
# Students + Subjects + Enrollment
# ============================================================

def students_with_subjects():

    query = """
        SELECT
            students_student.student_id,
            students_student.name,
            students_subject.subject_name,
            students_enrollment.academic_year,
            students_enrollment.semester
        FROM students_student
        INNER JOIN students_enrollment
            ON students_student.student_id =
               students_enrollment.student_id
        INNER JOIN students_subject
            ON students_enrollment.subject_id =
               students_subject.subject_id
    """

    with connection.cursor() as cursor:

        cursor.execute(query)

        return cursor.fetchall()


# ============================================================
# 4. JOIN
# Students + Marks + Subjects + Exams
# ============================================================

def student_marks():

    query = """
        SELECT
            students_student.name,
            students_subject.subject_name,
            students_exam.exam_name,
            students_mark.marks_obtained,
            students_mark.max_marks
        FROM students_mark
        INNER JOIN students_student
            ON students_mark.student_id =
               students_student.student_id
        INNER JOIN students_subject
            ON students_mark.subject_id =
               students_subject.subject_id
        INNER JOIN students_exam
            ON students_mark.exam_id =
               students_exam.exam_id
    """

    with connection.cursor() as cursor:

        cursor.execute(query)

        return cursor.fetchall()


# ============================================================
# 5. UNION
# Students from two courses
# ============================================================

def students_union():

    query = """
        SELECT name
        FROM students_student
        WHERE course_id = 1

        UNION

        SELECT name
        FROM students_student
        WHERE course_id = 2
    """

    with connection.cursor() as cursor:

        cursor.execute(query)

        return cursor.fetchall()


# ============================================================
# 6. INTERSECTION
# Students who have both attendance and marks
# ============================================================

def students_with_attendance_and_marks():

    query = """
        SELECT student_id
        FROM students_attendance

        INTERSECT

        SELECT student_id
        FROM students_mark
    """

    with connection.cursor() as cursor:

        cursor.execute(query)

        return cursor.fetchall()


# ============================================================
# 7. CARTESIAN PRODUCT
# Students × Subjects
# ============================================================

def student_subject_cartesian():

    query = """
        SELECT
            students_student.name,
            students_subject.subject_name
        FROM students_student
        CROSS JOIN students_subject
    """

    with connection.cursor() as cursor:

        cursor.execute(query)

        return cursor.fetchall()