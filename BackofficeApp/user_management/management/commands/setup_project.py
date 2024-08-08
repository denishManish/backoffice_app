from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.core.files import File
from django.core.files.storage import default_storage
from django.contrib.auth.models import Group
from django.db.models import Q
from user_management.models import User
from partner_management.models import Employee
from course_management.models import Course, Category, Lesson
import random


def upload_file_to_minio(file_path, storage_path):
    with open("user_management/management/commands/"+file_path, "rb") as file:
        django_file = File(file)
        return default_storage.save(storage_path, django_file)


class Command(BaseCommand):
    """
    Django management command to set up the initial database state, including data load and initial configurations.

    Examples:
        ```
        python manage.py setup_project
        ```
    """
    help = 'Sets up the database and loads initial data'    

    def handle(self, *args, **options):
        """
        Handles the database setup by `makemigrations` and `migrate`. <br>
        Loads data fixtures and sets up initial configurations:

        - groups.json
        - partner_management.json
        - course_management.json

        Creates users, sets them into the groups. <br>
        Set owners to partner instances. <br>
        Creates employees and branches for each partner. <br>
        Sets categories to course instances. <br>
        Call command `fill_groups` to set up permissions to each group.

        Raises:
            CommandError: Raised if there is an issue with loading fixtures, setting up initial configurations,
                or any other setup step.
        """
        self.stdout.write(self.style.SUCCESS('Creating migration files...'))
        call_command('makemigrations')

        self.stdout.write(self.style.SUCCESS('Applying database migrations...'))
        call_command('migrate')


        self.stdout.write(self.style.SUCCESS('Loading groups and setting permissions...'))
        try:
            call_command('loaddata', 'groups.json')  # 3 groups: superuser, owner, teacher
            call_command('fill_groups')
        except Exception as e:
            raise CommandError(f'Failed to load groups and fill them with permissions: {e}')

        superuser_group = Group.objects.get(name="superuser")
        owner_group = Group.objects.get(name="owner")
        teacher_group = Group.objects.get(name="teacher")


        self.stdout.write(self.style.SUCCESS('Loading fixtures...'))
        try:
            call_command('loaddata', 'users.json')       # 1 superuser and 5 owners
            call_command('loaddata', 'partners.json')    # 5 partners
            call_command('loaddata', 'branches.json')    # 11 total branches: 3,3,1,2,2 (for each partner)
            call_command('loaddata', 'employees.json')   # 25 total employees: 5 for each partner
            call_command('loaddata', 'categories.json')  # 5 total categories: 3 main ones, 2 subcategories
            call_command('loaddata', 'courses.json')     # 4 courses
            call_command('loaddata', "lessons.json")     # 12 total lessons: 3 for each course
        except Exception as e:
            raise CommandError(f'Failed to load fixtures: {e}')



        self.stdout.write(self.style.SUCCESS('Setting hashed passwords and groups for users...'))

        superuser = User.objects.get(email="superuser@gmail.com")
        superuser.groups.add(superuser_group)
        superuser.set_password('superuser')
        superuser.save()

        owner_emails = [f"owner{partner}@gmail.com" for partner in range(1,6)]
        for email in owner_emails:
            owner = User.objects.get(email=email)
            owner.groups.add(owner_group)
            owner.set_password(email.split('@')[0])  # password is the email prefix (e.g., 'owner1')
            owner.save()

        teacher_emails = [f"teacher{partner}{num}@gmail.com" for partner in range(1, 6) for num in range(1, 6)]
        for email in teacher_emails:
            teacher = User.objects.get(email=email)
            teacher.groups.add(teacher_group)
            teacher.set_password(email.split('@')[0])  # password is the email prefix (e.g., 'teacher11')
            teacher.save()



        self.stdout.write(self.style.SUCCESS('Setting categories for courses...'))

        roblox_course = Course.objects.get(name="Курс по Roblox")
        pencilcode_course = Course.objects.get(name="Курс по Pencil Code")
        python_course = Course.objects.get(name="Курс по Python")
        js_course = Course.objects.get(name="Курс по JavaScript")

        mb_category = Category.objects.get(name="Mbyte")
        gb_category = Category.objects.get(name="Gbyte")
        tb_category = Category.objects.get(name="Tbyte")
        python_subcategory = Category.objects.get(name="Python")
        js_subcategory = Category.objects.get(name="JavaScript")

        roblox_course.categories.add(mb_category)
        pencilcode_course.categories.add(gb_category)
        python_course.categories.add(tb_category, python_subcategory)
        js_course.categories.add(tb_category, js_subcategory)



        self.stdout.write(self.style.SUCCESS('Setting random courses for teachers...'))
        
        all_courses = [roblox_course, pencilcode_course, python_course, js_course]
        teachers = Employee.objects.all()
        for teacher in teachers:
            num_courses = random.randint(1, len(all_courses))
            courses_to_assign = random.sample(all_courses, num_courses)
            teacher.courses.set(courses_to_assign)


        
        self.stdout.write(self.style.SUCCESS(
            'Setting a few files for lessons of Roblox course, image for this course and for teachers "teacher11" and "teacher12"...')
        )

        roblox_course.image = upload_file_to_minio("test_files/roblox_logo.png", "course_images/roblox_logo.png")
        roblox_course.save()

        roblox_lesson_1 = Lesson.objects.get(Q(lesson_number=1) & Q(course=roblox_course))
        roblox_lesson_1.presentation = upload_file_to_minio(
            "test_files/roblox_lesson_1.pptx", 
            f"{roblox_course.name}/roblox_lesson_1.pptx"
        )
        roblox_lesson_1.additional_file = upload_file_to_minio(
            "test_files/additional_files_lesson_1.zip",
            f"{roblox_course.name}/additional_files_lesson_1.zip"
        )
        roblox_lesson_1.save()

        roblox_lesson_2 = Lesson.objects.get(Q(lesson_number=2) & Q(course=roblox_course))
        roblox_lesson_2.presentation = upload_file_to_minio(
            "test_files/roblox_lesson_2.pptx", 
            f"{roblox_course.name}/roblox_lesson_2.pptx"
        )
        roblox_lesson_2.additional_file = upload_file_to_minio(
            "test_files/additional_files_lesson_2.zip",
            f"{roblox_course.name}/additional_files_lesson_2.zip"
        )
        roblox_lesson_2.save()

        roblox_lesson_3 = Lesson.objects.get(Q(lesson_number=3) & Q(course=roblox_course))
        roblox_lesson_3.presentation = upload_file_to_minio(
            "test_files/roblox_lesson_3.pptx", 
            f"{roblox_course.name}/roblox_lesson_3.pptx"
        )
        roblox_lesson_3.additional_file = upload_file_to_minio(
            "test_files/additional_files_lesson_1.zip",
            f"{roblox_course.name}/additional_files_lesson_3.zip"
        )
        roblox_lesson_3.save()

        teacher11 = User.objects.get(email="teacher11@gmail.com")
        teacher11.image = upload_file_to_minio("test_files/user_logo.png", "user_images/user_logo.png")
        teacher11.save()

        teacher12 = User.objects.get(email="teacher12@gmail.com")
        teacher12.image = upload_file_to_minio("test_files/user_logo2.png", "user_images/user_logo2.png")
        teacher12.save()

        

        self.stdout.write(self.style.SUCCESS('Successfully set up the database!'))
