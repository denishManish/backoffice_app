from django.db import models
from django.utils.translation import gettext_lazy as _
from user_management.models import User
from course_management.models import Course
    

class Partner(models.Model):
    """
    Represents a business partner entity.

    Attributes:
        id (BigAutoField): Primary key.
        name (CharField): Name of the partner.
        legal_entity (CharField): Legal entity information.
        creating_date (DateField): Auto-filled on the date of creation partner instance. <br>
            Partnership start date. 
        information (TextField): (__Optional__) <br>
            Additional information about the partner.
        status (CharField): (__Optional, Default: 'ACTIVE'__) <br>
            Operational status of the partner, can be ACTIVE or INACTIVE.
        country (CharField): Country of the partner.
        region (CharField): Region of the partner.
        city (CharField): City of the partner.
        street (CharField): Street of the partner.
        house (PositiveSmallIntegerField): House number.
        address_note (CharField): (__Optional__) <br>
            Additional address details.
    
    Other Parameters: Relationships
        owner (User): __OneToOneField__ <br>
            The user who owns this partner entity. <br>
            Can be NULL.
        courses (Course): __ManyToManyField__ <br>
            Courses accessible by this partner. <br>
            Not currently implemented, all partners have access to all courses.
        
        employees (Employee): __ForeignKey from `Employee` model__ <br>
            Partner's employees. <br>
            Accessible as 'employees', accessible in query as 'employee'.
        branches (Branch): __ForeignKey from `Branch` model__ <br>
            Partner's branches. <br>
            Accessible as 'branches', accessible in query as 'branch'.

    Methods:
        __str__(self): Returns the string representation of the partner.
    """
    class Status(models.TextChoices):
        """
        Represents the operational status of the partner.

        Attributes:
            ACTIVE (str): `active` in the database <br>
                Partner is active.
            INACTIVE (str): `inactive` in the database <br>
                Partner is not active.
        """
        ACTIVE = "active", _("Active")
        INACTIVE = "inactive", _("Inactive")

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    legal_entity = models.CharField(max_length=500)
    creating_date = models.DateField(auto_now_add=True)
    information = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=25, choices=Status, default=Status.ACTIVE)

    country = models.CharField(max_length=50)
    region = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    street = models.CharField(max_length=50)
    house = models.PositiveSmallIntegerField()
    address_note = models.CharField(max_length=50, blank=True, null=True)

    owner = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, related_name='owned_partner')
    courses = models.ManyToManyField(Course, related_name="partners_with_access", related_query_name="partners_with_access")

    def __str__(self):
        return self.name


class Employee(models.Model):
    """
    Represents an employee of the partner.

    Attributes:
        bank_account_number (IntegerField): Bank account number for payroll purposes.
        status (CharField): (__Optional, Default: 'ACTIVE'__) <br>
            Employment status with choices such as ACTIVE, INACTIVE, LEFT, FIRED.

    Other Parameters: Relationships
        user (User): __OneToOneField__, Primary key.
            The user instance linked to this employee.
        partner (Partner): __ForeignKey__ <br>
            The partner to whom the employee is associated.
        branches (Branch): __ManyToManyField__ <br>
            Branches where the employee works.
        courses (Course): __ManyToManyField__ <br>
            Courses that the employee teaches or manages.

    Methods:
        __str__(self): Returns the string representation of the employee.
    """
    class Status(models.TextChoices):
        """
        Represents the employment status of the employee.

        Attributes:
            ACTIVE (str): `active` in the database <br>
                Employee is active.
            INACTIVE (str): `inactive` in the database <br>
                Employee is not active.
            LEFT (str): `left` in the database <br>
                Employee has voluntarily left the organization.
            FIRED (str): `fired` in the database <br>
                Employee is fired.
        """
        ACTIVE = "active", _("Active")
        INACTIVE = "inactive", _("Inactive")
        LEFT = "left", _("Left")
        FIRED = "fired", _("Fired")

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name="employee")
    bank_account_number = models.IntegerField()
    status = models.CharField(max_length=25, choices=Status, default=Status.ACTIVE)

    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="employees", related_query_name="employee")
    branches = models.ManyToManyField('Branch', related_name="employees", related_query_name="employee")
    courses = models.ManyToManyField(Course, related_name="teachers", related_query_name="teacher")

    def __str__(self):
        """
        Returns the string representation of the employee.

        Returns:
            email (str): User's email address.
        """
        return self.user.email


class Branch(models.Model):
    """
    Represents a physical location, branch of a business partner, such as an office or educational center.

    Attributes:
        id (BigAutoField): Primary key.
        name (CharField): Name of the branch.
        opening_date (DateField): Date when the branch was opened.
        country (CharField): Country of the branch.
        region (CharField): Region of the branch.
        city (CharField): City of the branch.
        street (CharField): Street of the branch.
        house (PositiveSmallIntegerField): House number.
        floor (PositiveSmallIntegerField): Floor number.
        address_note (CharField): (__Optional__) <br>
            Additional address details.
        status (CharField): (__Optional, Default: 'ACTIVE'__) <br>
            Operational status of the branch, can be ACTIVE or INACTIVE.
        area (PositiveSmallIntegerField): Size of the branch in square meters.
        note (TextField): (__Optional__) <br>
            Additional notes about the branch.

    Other Parameters: Relationships
        partner (Partner): __ForeignKey__ <br>
            The partner that owns this branch.
        employees (Employee): __ManyToManyField from `Employee` model__ <br>
            Employees that work at this branch. <br>
            Accessible as 'employees', accessible in query as 'employee'.
    
    Methods:
        __str__(self): Returns the string representation of the branch.
    """
    class Status(models.TextChoices):
        """
        Represents the operational status of the branch.

        Attributes:
            ACTIVE (str): `active` in the database <br>
                Branch is active.
            INACTIVE (str): `inactive` in the database <br>
                Branch is not active.
        """
        ACTIVE = "active", _("Active")
        INACTIVE = "inactive", _("Inactive")

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    opening_date = models.DateField()
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="branches", related_query_name="branch")
    status = models.CharField(max_length=25, choices=Status, default=Status.ACTIVE)
    note = models.TextField(blank=True, null=True)
    area = models.PositiveSmallIntegerField()

    country = models.CharField(max_length=50)
    region = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    street = models.CharField(max_length=50)
    house = models.PositiveSmallIntegerField()
    floor = models.PositiveSmallIntegerField()
    address_note = models.CharField(max_length=150, blank=True, null=True)

    def __str__(self):
        """
        Returns the string representation of the branch.

        Returns:
            name (str): Name of the branch.
        """
        return self.name
    