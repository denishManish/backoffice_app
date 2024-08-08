import os
from django.core.files.storage import default_storage
from django.db import models
from django.utils.translation import gettext_lazy as _


class Course(models.Model):
    """
    Represents a course that can be accessed by teachers and other users.

    Attributes:
        id (BigAutoField): Primary key.
        name (CharField): Name of the course.
        min_age (PositiveSmallIntegerField): Minimum age for students.
        max_age (PositiveSmallIntegerField): Maximum age allowed for students.
        image (ImageField): (__Optional__) <br> 
            Image for the course. Uploads to 'course_images\\' directory.
        link (URLField): (__Optional__) <br>
            Link to the course.
        status (CharField): (__Optional, Default: 'HIDDEN'__) <br> 
            Current status of the course, can be ACTIVE, HIDDEN, or ARCHIVED.
        note (TextField): (__Optional__) <br> 
            Additional notes about the course. 
    
    Other Parameters: Relationships
        categories (Category): __ManyToManyField__ <br>
            Categories this course belongs to.

        lessons (Lesson): __ForeignKey from `Lesson` model__ <br>
            Lessons that are part of this course. <br>
            Accessible as `lessons`, accessible in query as `lesson`.
        employees (Employee): __ManyToManyField from `Employee` model__ <br>
            Teachers that have access for this course. <br>
            Accessible as `teachers`, accessible in query as `teacher`.
        partners (Partner): __ManyToManyField from `Partner` model__ <br>
            Partners that have access to this course. <br>
            `Right now is not implemented and all partners have access to all courses.`

    Methods:
        __str__: Returns string representation of the course.
        save: Custom save method to handle image update.
        delete: Deletes the course and it's associated image from the storage.
    """
    class Status(models.TextChoices):
        """
        Represent the status of the course.

        Attributes:
            ACTIVE (str): `active` in the database <br>
                course is active
            HIDDEN (str): `hidden` in the database <br>
                course is temporarily hidden due to maintenance or updates
            ARCHIVED (str): `archived` in the database <br>
                course is archived
        """
        ACTIVE = "active", _("Active")
        HIDDEN = "hidden", _("Hidden")
        ARCHIVED = "archived", _("Archived")

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50)
    min_age = models.PositiveSmallIntegerField()
    max_age = models.PositiveSmallIntegerField()
    image = models.ImageField(upload_to="course_images/", blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    status = models.CharField(max_length=25, choices=Status, default=Status.HIDDEN)
    note = models.TextField(blank=True, null=True)
    
    categories = models.ManyToManyField('Category', related_name="courses", related_query_name="course")

    def __str__(self):
        """
        Returns string representation of the course.

        Returns:
            name (str): Name of the course.
        """
        return self.name
    
    def save(self, *args, **kwargs):
        """
        Custom save method to handle image update.
        If new image is provided old one is deleted.
        If course have an image and on update the new one isn't provided we not rewrite image field with Null value.
        """
        is_update = self.pk is not None

        if is_update:
            old_course = Course.objects.get(pk=self.pk)
            if old_course.image and self.image and old_course.image != self.image:
                default_storage.delete(old_course.image.name)
            if old_course.image and not self.image:
                self.image = old_course.image.name.split("/")[-1]

        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """
        Deletes the course and it's associated image from the storage.

        Arguments:
            *args (tuple): Positional arguments.
            **kwargs (dict): Keyword arguments.

        Raises:
            Exception: If there is an error deleting the image from the storage.
        """
        if self.image:
            try:
                default_storage.delete(self.image.name)
            except Exception as e:
                print(f"Error deleting image from S3: {e}")

        super(Course, self).delete(*args, **kwargs)


class Category(models.Model):
    """
    Represents a category for courses which can be nested to create a hierarchy of categories.

    Attributes:
        id (BigAutoField): Primary key.
        name (CharField): Name of the category, must be unique.
    
    Other Parameters: Relationships
        parent (OneToMany): __ForeignKey__ <br>
            Optional parent category to establish a hierarchy.
        subcategories (ManyToOne): __RelatedName from `Category` model__ <br>
            Children categories. <br>
            Accessible as 'subcategories', accessible in query as 'subcategory'.

        courses (Course): __ManyToManyField from `Course` model__ <br>
            Courses associated with this category. <br>
            Accessible as 'courses', accessible in query as 'course'.

    Methods:
        __str__: Returns the string representation of the category.
    """
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=150, unique=True)

    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True, 
        related_name='subcategories', 
        related_query_name="subcategory"
    )

    def __str__(self):
        """
        Returns the string representation of the category.

        Returns:
            name(str): Name of the category.
        """
        return self.name


def presentation_upload_path(instance, filename):
    """
    Defines the upload path for presentations and additional files related to lessons. <br>
    File path is a combination of the course name and the original filename.
    
    Args:
        instance (Lesson): The instance of the lesson being saved.
        filename (str): The original filename of the uploaded file.
    
    Returns:
        filepath(str): A file path which is a combination of the course name and the original filename.
    """
    return os.path.join(instance.course.name, filename)


class Lesson(models.Model):
    """
    Represents a lesson which is part of a course.

    Attributes:
        id (BigAutoField): Primary key.
        lesson_number (PositiveSmallIntegerField): (__Optional, Default: 0__) <br> 
            Order number of the lesson within the course.
        name (CharField): Name of the lesson.
        presentation (FileField): (__Optional__) <br> 
            File field for lesson presentations, optional. Uploads to '{course_name}/' directory.
        presentationURL (URLField): (__Optional__) <br> 
            URL of presentation to Google Drive.
        additional_file (FileField): (__Optional__) <br> 
            Additional file for the lesson. Uploads to '{course_name}/' directory.
        description (TextField): (__Optional__) <br> 
            Description of the lesson.
    
    Other Parameters: Relationships
        course (Course): __ForeignKey__ <br>
            The course this lesson belongs to.

    Methods:
        __str__: Returns the string representation of the lesson.
        save: Custom save method to handle files update.
        delete: Deletes the lesson and its associated files from storage.
    """
    
    id = models.BigAutoField(primary_key=True)
    lesson_number = models.PositiveSmallIntegerField(blank=True, default=0)
    name = models.CharField(max_length=100)
    presentation = models.FileField(upload_to=presentation_upload_path, blank=True, null=True)
    presentationURL = models.URLField(blank=True, null=True)
    additional_file = models.FileField(upload_to=presentation_upload_path, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons", related_query_name="lesson")

    def __str__(self):
        """
        Returns the string representation of the lesson.

        Returns:
            name (str): Name of the lesson.
        """
        return self.name
    
    def save(self, *args, **kwargs):
        """
        Custom save method to handle files update.
        If new file is provided old one is deleted.
        If lesson have a file and on update the new one isn't provided we not rewrite it's file field with Null value.
        """
        is_update = self.pk is not None

        if is_update:
            old_lesson = Lesson.objects.get(pk=self.pk)

            if old_lesson.presentation and self.presentation and old_lesson.presentation != self.presentation:
                default_storage.delete(old_lesson.presentation.name)
            if old_lesson.presentation and not self.presentation:
                self.presentation = old_lesson.presentation.name.split("/")[-1]

            if old_lesson.additional_file and self.additional_file and old_lesson.additional_file != self.additional_file:
                default_storage.delete(old_lesson.additional_file.name)
            if old_lesson.additional_file and not self.additional_file:
                self.additional_file = old_lesson.additional_file.name.split("/")[-1]

        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """
        Deletes the lesson and its associated files from storage.

        Args:
            *args (tuple): Positional arguments.
            **kwargs (dict): Keyword arguments.

        Raises:
            Exception: If there is an error deleting the presentation or additional file from the storage.
        """
        if self.presentation:
            try:
                default_storage.delete(self.presentation.name)
            except Exception as e:
                print(f"Error deleting presentation from S3: {e}")
        
        if self.additional_file:
            try:
                default_storage.delete(self.additional_file.name)
            except Exception as e:
                print(f"Error deleting additional file from S3: {e}")

        super(Lesson, self).delete(*args, **kwargs)
    