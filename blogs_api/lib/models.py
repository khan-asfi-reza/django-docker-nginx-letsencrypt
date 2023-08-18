from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract model that set creation time and update time automatically
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        get_latest_by = 'created_at'
        abstract = True


class LowerCaseCharField(models.CharField):
    """
    Auto Converts text to lower case field
    """
    def to_python(self, value):
        value = super(LowerCaseCharField, self).to_python(value)
        if isinstance(value, str):
            return value.lower()
        return value
