"""Ever user has a 'userpreference' object attatched to them,
containing things like OTP keys, password reset keys, encryption settings,
and so on."""
from django.db import models
from django.contrib.auth.models import User
import pyotp

class Userpreference(models.Model):
    """Any information about the user that isn't tasks or events would be
    stored here."""
    user = models.OneToOneField(User)
    otp = models.BooleanField(default=False)
    otpkey = models.CharField(max_length=16)
    activationurl = models.CharField(max_length=30, default="", unique=True)

    @staticmethod
    def createprefs(newuser):
        """This is called when a new user is created. It simply creates the
        associated userpreference for them."""
        newprefs = Userpreference(
            user=newuser,
            otp=False,
            otpkey=pyotp.random_base32(),
            activationurl=pyotp.random_base32()
        )
        newprefs.save()

    def __string__(self):
        return self.user

# Create your models here.
