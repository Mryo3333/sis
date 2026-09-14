from django.core.management.base import BaseCommand

from students.models import Course, Department, Subject


UNIVERSITY_DATA = {
    "School of Computing": {
        "BSc Computer Science": [
            ("CS101", "Programming Fundamentals", 1),
            ("CS102", "Data Structures", 2),
            ("CS203", "Database Systems", 3),
            ("CS204", "Web Development", 3),
            ("CS305", "Operating Systems", 5),
            ("CS306", "Computer Networks", 5),
            ("CS407", "Software Engineering", 7),
            ("CS408", "Artificial Intelligence", 7),
        ],
        "BSc Information Technology": [
            ("IT101", "Introduction to IT", 1),
            ("IT202", "Networking Basics", 2),
            ("IT203", "Database Design", 3),
            ("IT304", "Cybersecurity", 4),
            ("IT405", "Cloud Computing", 5),
            ("IT406", "Mobile App Development", 6),
        ],
    },
    "School of Business": {
        "BBA": [
            ("BA101", "Principles of Management", 1),
            ("BA102", "Financial Accounting", 1),
            ("BA203", "Marketing Management", 3),
            ("BA204", "Business Law", 3),
            ("BA305", "Human Resource Management", 5),
            ("BA306", "Strategic Management", 5),
        ],
        "BCom": [
            ("BC101", "Business Economics", 1),
            ("BC102", "Financial Reporting", 2),
            ("BC203", "Taxation", 3),
            ("BC204", "Corporate Finance", 4),
            ("BC305", "Auditing", 5),
        ],
    },
    "School of Engineering": {
        "BEng Civil Engineering": [
            ("CE101", "Engineering Mathematics", 1),
            ("CE102", "Engineering Drawing", 1),
            ("CE203", "Structural Analysis", 3),
            ("CE204", "Surveying", 3),
            ("CE305", "Hydraulics", 5),
            ("CE306", "Geotechnical Engineering", 5),
        ],
        "BEng Mechanical Engineering": [
            ("ME101", "Engineering Physics", 1),
            ("ME102", "Workshop Practice", 1),
            ("ME203", "Thermodynamics", 3),
            ("ME204", "Fluid Mechanics", 3),
            ("ME305", "Machine Design", 5),
            ("ME306", "Manufacturing Technology", 5),
        ],
    },
    "School of Health Sciences": {
        "BSc Nursing": [
            ("NS101", "Anatomy", 1),
            ("NS102", "Physiology", 1),
            ("NS203", "Fundamentals of Nursing", 3),
            ("NS204", "Microbiology", 3),
            ("NS305", "Community Health Nursing", 5),
            ("NS306", "Mental Health Nursing", 5),
        ],
    },
}


def seed_university_data():
    created_count = 0

    for department_name, courses in UNIVERSITY_DATA.items():
        department, _ = Department.objects.get_or_create(
            department_name=department_name,
            defaults={"description": f"Academic programs in {department_name}", "status": "Active"},
        )

        for course_name, subjects in courses.items():
            course, created = Course.objects.get_or_create(
                course_name=course_name,
                defaults={
                    "department": department,
                    "duration_years": 4,
                    "status": "Active",
                },
            )
            if created:
                created_count += 1

            for subject_code, subject_name, semester in subjects:
                Subject.objects.get_or_create(
                    subject_code=subject_code,
                    defaults={
                        "subject_name": subject_name,
                        "course": course,
                        "semester": semester,
                        "credits": 3,
                        "status": "Active",
                    },
                )

    return created_count


class Command(BaseCommand):
    help = "Seed the project with university departments, courses, and subjects."

    def handle(self, *args, **options):
        created_count = seed_university_data()
        self.stdout.write(
            self.style.SUCCESS(f"University seed complete. Added {created_count} new courses.")
        )
