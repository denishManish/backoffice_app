import uuid
from django.db import models
from django.core.files.storage import default_storage
from django.contrib.auth.models import AbstractUser, Group, BaseUserManager

from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    """
    Custom manager for User, supporting creation of user and superuser with email as the identifier instead of username.
    
    Methods:
        _create_user:
            Private method that creates and saves a User with the given email, password, and extra fields.
        create_user:
            Creates a regular user with the specified email, password, and additional non-sensitive fields.
        create_superuser:
            Creates a superuser with the specified email, password, and extra fields.
    """
    def _create_user(self, email, password, **extra_fields):
        """
        Private method that creates and saves a User with the given email, password, and extra fields.

        Args:
            email (str): User's email.
            password (str): User's password.
            **extra_fields (dict): Extra fields to include in the User model.

        Returns:
            (User): The created user model instance.

        Raises:
            ValueError: If the email is not provided.
        """
        if not email:
            raise ValueError("The given email must be set")
        email = email.lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """
        Creates a regular user with the specified email, password, and additional non-sensitive fields.

        Args:
            email (str): User's email.
            password (str): User's password.
            **extra_fields (dict): Additional fields for the user.

        Returns:
            (User): The created user instance.
        """
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Creates a superuser with the specified email, password, and extra fields.

        Args:
            email (str): Superuser's email.
            password (str): Superuser's password.
            **extra_fields (dict): Additional fields for the superuser.

        Returns:
            (User): The created superuser instance.

        Raises:
            ValueError: If `is_staff` or `is_superuser` is not set to True.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)
    

class User(AbstractUser):
    """
    User model extending AbstractUser, replacing username with email as the primary identifier.

    Attributes:
        id (BigAutoField): Primary key.
        public_id (UUIDField): Publicly exposed unique identifier.
        email (EmailField): Unique email for the user.
        password (CharField): Hashed user's password.
        username (CharField): (__Isn't used, Optional__) <br>
            Username field  <br>
            (Inherited from Django's AbstractUser)
        first_name (CharField): (__Optional__) <br> 
            User's first name.
        last_name (CharField): (__Optional__) <br> 
            User's last name.
        patronymic (CharField): (__Optional__) <br> 
            User's patronymic.
        gender (CharField): (__Optional, Default: `UNDEFINED`__) <br> 
            User's gender, options are MAN, WOMAN, UNDEFINED.
        birthday (DateField): (__Optional__) <br> 
            User's birthday.
        image (ImageField): (__Optional__) <br> 
            User profile image. Uploads to 'user_images\\' directory.
        phone_number (PositiveBigIntegerField): 
            User's phone number. <br>
            Unique if provided. <br>
            Can be NULL.
        note (TextField): (__Optional__) <br> 
            Additional notes about the user.
        country (CharField): (__Optional__) <br> 
            Country of the user.
        region (CharField): (__Optional__) <br> 
            Region of the user.
        city (CharField): (__Optional__) <br> 
            City of the user.
        street (CharField): (__Optional__) <br> 
            Street of the user.
        house (PositiveSmallIntegerField): (__Optional__) <br> 
            House of the user.
        address_note (CharField): (__Optional__) <br> 
            AAdditional address details.
        is_active (BooleanField): (__Optional, Default: `True`__) <br>
            indicates if the user's account is active. <br>
            (Inherited from Django's AbstractUser)
        is_staff (BooleanField): (__Optional, Default: `False`__) <br>
            True if the user can access the admin panel. <br>
            (Inherited from Django's AbstractUser)
        is_superuser (BooleanField): (__Optional, Default: `False`__) <br>
            True if the user has all permissions without explicitly assigning them. <br>
            (Inherited from Django's AbstractUser)
        last_login (DateTimeField): (__Autoupdates__) <br>
            Indicates the last time the user logged in. <br>
            (Inherited from Django's AbstractUser)
        date_joined (DateTimeField): (__Optional, Default: `creating date`__) <br>
            Indicates the date the user joined. <br>
            (Inherited from Django's AbstractUser)

    Other Parameters: Relationships
        groups (Group): __ManyToManyField from `Group` model__ <br>
            Groups the user belongs to. <br>
            Accessible as 'groups', accessible in query as 'group'.
        permissions (Permission): __ManyToManyField from `Permission` model__ <br>
            Permissions directly assigned to the user. <br>
            Accessible as 'user_permissions', accessible in query as 'user_permission'.
        owned_partner (Partner): __OneToOneField from `Partner` model__ <br>
            Partner the user owns. (should be `owner`) <br>
            Accessible as 'owned_partner'. 
        employee (Employee): __OneToOneField from `Employee` model__ <br>
            Employee instance linked to the user. <br>
            Accessible as 'employee'.

    The USERNAME_FIELD is set to `email`, indicating the primary login field.

    Methods:
        __str__: Returns the string representation of the user's email.
        save: Custom save method to handle image update.
        delete: Custom delete method to handle image deletion if the user is deleted.
    """
    class Gender(models.TextChoices):
        """
        Gender choices for the User model.

        Attributes:
            MAN (str): `man` in the database.
            WOMAN (str): `woman` in the database.
            UNDEFINED (str): `undefined` in the database.
        """
        MAN = "man", _("Man")
        WOMAN = "woman", _("Woman")
        UNDEFINED = "undefined", _("Undefined")

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True)
    email = models.EmailField(unique=True)

    # optional fields
    username = models.CharField(max_length=50, blank=True, null=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    patronymic = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=25, choices=Gender, default=Gender.UNDEFINED)
    birthday = models.DateField(blank=True, null=True)
    image = models.ImageField(upload_to="user_images/", blank=True, null=True)
    phone_number = models.PositiveBigIntegerField(unique=True, blank=True, null=True) # сделать валидацию

    country = models.CharField(max_length=50, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    street = models.CharField(max_length=50, blank=True, null=True)
    house = models.PositiveSmallIntegerField(blank=True, null=True)
    address_note = models.CharField(max_length=150, blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        """
        Returns the string representation of the user.

        Returns:
            email (str): User's email address.
        """
        return self.email
    
    def save(self, *args, **kwargs):
        """
        Custom save method to handle image update.
        If new image is provided old one is deleted.
        If user have an image and on update the new one isn't provided we not rewrite image field with Null value.
        """
        is_update = self.pk is not None

        if is_update:
            old_user = User.objects.get(pk=self.pk)
            if old_user.image and self.image and old_user.image != self.image:
                default_storage.delete(old_user.image.name)
            if old_user.image and not self.image:
                self.image = old_user.image.name.split("/")[-1]

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Custom delete method to handle image deletion if the user is deleted.

        Args:
            args (tuple): Positional arguments.
            kwargs (dict): Keyword arguments.

        Raises:
            Exception: If an error occurs during image deletion from storage.
        """
        if self.image:
            try:
                default_storage.delete(self.image.name)
            except Exception as e:
                print(f"Error deleting image from S3: {e}")

        super(User, self).delete(*args, **kwargs)


class GroupDescription(models.Model):
    """
    Model representing a description for a Django group, extending the base Group model with additional information.

    Attributes:
        description (TextField): (__Optional__) <br>
            Text description of the group.

    Other Parameters: Relationships
        group (Group): __OneToOneField__, Primary key. <br>
            Group instance linked to the GroupDescription. <br>
            Accessible as 'description'. 

    Methods:
        __str__:
            Returns the string representation of group's description if available, otherwise returns an empty string.
    """
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='description', primary_key=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        """
        Returns the string representation of the group's description.

        Returns:
            description (str): Group's description or empty string.
        """
        return self.description or ""
    

def add_group_description(group, description_text):
    """
    Function to easily add or update the description for a specified group through the Django shell. <br>
    Utilizes Django's `update_or_create` method to either update an existing description or create a new one
    for the given group.

    Args:
        group (Group): The group this description is associated with.
        description_text (str): Text description of the group.

    Returns:
        (GroupDescription): The GroupDescription instance that was created or updated.

    Examples:
        >>> from django.contrib.auth.models import Group
        >>> group_instance = Group.objects.get(name='teachers')
        >>> add_group_description(group_instance, 'Teachers with access to courses and lessons.')
    """
    group_description, created = GroupDescription.objects.update_or_create(
        group=group,
        defaults={'description': description_text}
    )
    return group_description