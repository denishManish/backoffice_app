from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from partner_management.models import Employee, Branch

class Command(BaseCommand):
    """
    Django management command to set up and assign permissions to predefined user groups.

    Examples:
        ```
        python manage.py fill_groups
        ```
    """
    help = 'Sets up permissions for groups'

    def handle(self, *args, **options):
        """
        Handle the setup of group permissions. <br>
        Retrieves necessary Permission objects based on codenames 
            and assigns these permissions to the 'owner' and 'teacher' groups.

        Examples:
            ```
            superuser have all permissions.

            owner can:
                - view_course, 
                - change_course, # only teacher list
                - view_lesson, 
                - view_category,
                
                - view_partner,
                - change_partner,

                - add_branch,
                - view_branch,
                - change_branch,
                - delete_branch,

                - add_employee,
                - view_employee,
                - change_employee,
                - delete_employee

            teacher can:
                - view_course, 
                - view_lesson, 
                - view_category,
                - view_employee,
                - view_branch,
                - view_partner,
            ```
         
        Raises:
            `Permission.DoesNotExist`: If a permission with the specified codename does not exist.
            `Group.DoesNotExist`: If the specified group does not exist.
        """
        self.stdout.write(self.style.SUCCESS('Setting up permissions for groups...'))
        try:
            # Retrieve permission instances 
            view_course = Permission.objects.get(codename='view_course')
            change_course = Permission.objects.get(codename='change_course')

            view_lesson = Permission.objects.get(codename='view_lesson')

            view_category = Permission.objects.get(codename='view_category')

            change_partner = Permission.objects.get(codename='change_partner')
            view_partner = Permission.objects.get(codename='view_partner')

            add_branch = Permission.objects.get(codename='add_branch')
            view_branch = Permission.objects.get(codename='view_branch')
            change_branch = Permission.objects.get(codename='change_branch')
            delete_branch = Permission.objects.get(codename='delete_branch')

            add_employee = Permission.objects.get(codename='add_employee')
            view_employee = Permission.objects.get(codename='view_employee')
            change_employee = Permission.objects.get(codename='change_employee')
            delete_employee = Permission.objects.get(codename='delete_employee')

            # Setup permissions for owner group
            owner_group = Group.objects.get(name="owner")
            owner_group.permissions.add(
                view_course, 
                change_course, # only teacher list
                view_lesson, 
                view_category,
                
                view_partner,
                change_partner,

                add_branch,
                view_branch,
                change_branch,
                delete_branch,

                add_employee,
                view_employee,
                change_employee,
                delete_employee
            )
            
            # Setup permissions for teacher group
            teacher_group = Group.objects.get(name="teacher")
            teacher_group.permissions.add(
                view_course, 
                view_lesson,
                view_category,
                view_employee,
                view_branch,
                view_partner
            )

            self.stdout.write(self.style.SUCCESS('Successfully set up permissions for groups!'))
        except Permission.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            raise CommandError('Failed to setup permissions due to missing permission.')

        except Group.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            raise CommandError('Failed to setup permissions due to missing group.')