"""Views controlling the user settings page. So 2FA, password resetting,
encryption, and other settings, and their relevant pages."""
import json
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template
import pyotp
import qrcode
from .models import Userpreference
from profilepage.models import Task, Event
from fd_register.views import test_user
import re

@login_required
def settings_page(request):
    """Settings page"""
    return render(request, 'userprefs/settingspage.html')

@login_required
def enable_otp(request):
    """Page to enable 2FA on the account."""
    return render(request, 'userprefs/enableotp.html')

@login_required
def change_password(request):
    """Password change page. This only displays the page,
    not the actual logic. That's 'changepassword_confirm.'"""
    return render(request, 'userprefs/changepassword.html')

@login_required
def change_email(request):
    """Email change page. This only displays the insturction
    page, not any actual logic."""
    if request.method != 'POST':
        return render(request, 'userprefs/changemail.html')
    else:
        reqprefs = request.user.userpreference
        password = request.POST['password']
        newmail = request.POST['newemail']
        valid = True
        if not re.match(r'[^@]+@[^@]+\.[^@]+', newmail):
            messages.error(request, "not a valid email address")
            valid = False
        if not request.user.check_password(password):
            messages.error(request, "Password does not match.")
            valid = False
        if valid == True:
            reqprefs.pendingmail = newmail
            reqprefs.newmailcode = pyotp.random_base32()
            reqprefs.save()
            send_newemail(request, request.user)
            messages.success(request, "Confirmation email sent!")
            return HttpResponseRedirect(reverse('userprefs:settings_page'))
        return  HttpResponseRedirect(reverse('userprefs:change_email'))

def send_newemail(request, user):
    """Send the email with the verification URL."""
    message_template = get_template("userprefs/changemail.txt")
    activationurl = request.build_absolute_uri(reverse('userprefs:confirm_email'))
    emailcode = user.userpreference.newmailcode
    message = message_template.render({'activationurl':activationurl, 'emailcode':emailcode})
    newmail = user.userpreference.pendingmail
    send_mail("Verify your new email address",
             message,
             "noreply@fruitydo.alexskc.xyz",
             [newmail],
             fail_silently=False)

@login_required
def confirm_email(request):
    """The URL in the verfication email. Check if the code matches
    what's on the profile, and then redirect them back to settings."""
    user = request.user
    if request.GET['emailcode'] == user.userpreference.newmailcode:
        user.email = user.userpreference.pendingmail
        user.userpreference.pendingmail = ""
        user.userpreference.newmailcode = ""
        user.save()
        user.userpreference.save()
        messages.success(request, "Email successfully changed!")
    else:
        messages.error("Email code does not match or was not provided.")
    return HttpResponseRedirect(reverse('userprefs:settings_page'))

@login_required
def changepassword_confirm(request):
    """Password changing logic. Enter the old password,
    and a new password with confirmation. Change password on success."""
    oldpass = request.POST['currentpass']
    newpass = request.POST['newpass']
    newpass_confirm = request.POST['newpass_confirm']
    # Throw some values into the validator that won't raise any flags.
    rand = pyotp.random_base32()
    if not request.user.check_password(oldpass):
        messages.error(request, "Incorrect current password.")
    elif not test_user(request, rand, newpass, newpass_confirm, rand + '@example.com'):
        return HttpResponseRedirect(reverse('userprefs:settings_page'))
    else:
        request.user.set_password(newpass)
        request.user.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, "Successfully changed password.")
    return HttpResponseRedirect(reverse('userprefs:settings_page'))

@login_required
def disable_otp(request):
    """Button to disable OTP. There's no page for this. Just a single
    button on the user settings page."""
    request.user.userpreference.otp = False
    request.user.userpreference.save()
    messages.success(request, "Disabled Two Factor Authentication.")
    return HttpResponseRedirect(reverse('userprefs:settings_page'))

@login_required
def otp_qrcode(request):
    """The QRcode image that's generated for the user to scan with their
    phone."""
    otpkey = pyotp.TOTP(request.user.userpreference.otpkey)
    provision = otpkey.provisioning_uri("Fruitydo")
    otpqr = qrcode.make(provision)
    response = HttpResponse(content_type="image/png")
    otpqr.save(response, "PNG")
    return response

@login_required
def confirm_otp(request):
    """The button to enable 2FA on the user's account. They need to first
    enter the current OTP code before simply enabling it to make sure that
    everything is configured properly for both the user and the server."""
    user = request.user
    confirmcode = request.POST['confirmcode']
    otpkey = pyotp.TOTP(request.user.userpreference.otpkey)
    if confirmcode == otpkey.now():
        user.userpreference.otp = True
        user.userpreference.save()
        messages.success(request, "Enabled Two Factor Authentication.")
    else:
        messages.error(request, "Key does not match.")
    return HttpResponseRedirect(reverse('userprefs:settings_page'))

@login_required
def crypto_settings(request):
    """The encryption settings page. 
    Most crypto-related stuff is client-side, so there's not much to this."""
    if request.method != "POST":
        return render(request, 'userprefs/crypto_settings.html')
    elif request.method == "POST" and request.user.userpreference.encryption == False:
        password = request.POST["password"]
        if request.user.check_password(password):
            return render(request, 'userprefs/crypto_settings.html')
        else:
            messages.error(request, "Invalid password")
            return HttpResponseRedirect(reverse('userprefs:settings_page'))
    elif request.method == "POST" and request.user.userpreference.encryption == True:
        return HttpResponse("not implemented.")

@login_required
def confirm_crypto(request):
    """Enable crypto on the user's account after completing the process."""
    encryptedpass = request.POST["encryptedpass"]
    if request.user.check_password(request.POST["accpass"]):
        request.user.userpreference.encryptedkey = encryptedpass
        request.user.userpreference.encryption = True
        request.user.userpreference.save()
        messages.success(request, "Encryption successfully enabled!")
        return HttpResponse("success")
    else:
        messages.error("Account password does not match.")
        return HttpResponse("failure")

@login_required
def crypto_key(request):
    return HttpResponse(request.user.userpreference.encryptedkey)

@login_required
def all_tasks(request):
    tasks = Task.objects.filter(User_id=request.user.id)
    totalevents = []
    for task in tasks:
        events = Event.objects.filter(Task_id=task.id)
        for event in events:
            eventdata = {'id': task.id, 'description': event.event_description, 'pub_date': event.pub_date}
            totalevents.append(eventdata)
    finaldata = json.dumps(totalevents, cls=DjangoJSONEncoder)
    return HttpResponse(finaldata, content_type='application/json')

@login_required
def disable_crypto(request):
    request.user.userpreference.encryption = False
    request.user.userpreference.save()
    messages.success(request, "Encryption successfully disabled")
    return HttpResponse("success")
