from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.generic import View
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from .utils import TokenGenerator,generate_token
from django.utils.encoding import force_bytes,force_str,DjangoUnicodeDecodeError
from django.core.mail import EmailMessage
from django.conf import settings

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth import authenticate,login,logout
# Create your views here.



def signup(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['pass1']
        confirm_password = request.POST['pass2']
        if password != confirm_password:
            messages.warning(request, 'Password is not matching')
            return render(request, 'signup.html')
        
        
        try:
            if User.objects.get(username=email):
                messages.info(request, 'Email is taken')
                return render(request,'signup.html')
            
        except Exception as identifier:
            pass
        
        user = User.objects.create_user(email, email, password)
        user.is_active = False
        user.save()
        
        email_subject = "Activate your account"
        message = render_to_string('activate.html',{
            'user':user,
            'domain':'127.0.0.1:8000',
            'uid':urlsafe_base64_encode(force_bytes(user.pk)),
            'token':generate_token.make_token(user)
        })
        
        email_message = EmailMessage(email_subject,message,settings.EMAIL_HOST_USER, [email],)
        email_message.send()
        messages.success(request,"Activate your count by clicking the link in your gmaill")
        return redirect('/auth/login/')
        
        
    return render(request, "signup.html")


class ActivateAccountView(View):
    def get(self,request,uidb64,token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception as identifier:
            user = None
        if user is not None and generate_token.check_token(user,token):
            user.is_active=True
            user.save()
            messages.info(request,'Account Activates Successfully')
            return redirect('/auth/login/')
        return render(request,'activatefail.html')
    
    


def handlelogin(request):
    if request.method == 'POST':
        username = request.POST['email']
        userpassword = request.POST['pass1']
        myuser = authenticate(username=username, password=userpassword)
        
        if myuser is not None:
            login(request,myuser)
            messages.success(request,"Login Success")
            return redirect('/')
        
        else:
            messages.error(request,'Invalid Credentials')
            return redirect('/auth/login/')
    return render(request,'login.html')
    

def handlelogout(request):
    logout(request)
    messages.info(request,'Logout Success')
    return redirect('/auth/login/')


class RequestResetEmailView(View):
    def get(self, request):
        return render(request,'request-reset-email.html')
    
    def post(self,request):
        email = request.POST['email']
        user = User.objects.filter(email=email)
        
        if user.exists():
            # current_site = get_current_site(request)
            email_subject = '[Reset your Password]'
            message = render_to_string('reset-user-password.html',{
                'domain':'127.0.0.1:8000',
                'uid':urlsafe_base64_encode(force_bytes(user[0].pk)),
                'token':PasswordResetTokenGenerator().make_token(user[0])
            })
            
            email_message = EmailMessage(email_subject,message,settings.EMAIL_HOST_USER, [email])
            email_message.send()
            
            messages.info(request, 'WE HAVE SSENT AN EMAIL TO YOU WITH INSTRUCTIONS ON HOW TO RESET THE PASSWORD')
            return render(request, 'request-reset-email.html')
        
        
        
class SetNewPasswordView(View):
    def get(self, request, uidb64,token):
        context= {
            'uidb64':uidb64,
            'token':token
        }
        
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)
            
            if not PasswordResetTokenGenerator().check_token(user,token):
                messages.warning(request, 'Password Resset Link is Invalid')
                return render(request, 'request-reset-email.html')
            
            
        except DjangoUnicodeDecodeError as identifier:
            pass
        
        return render(request, 'set-new-password.html', context)
    
    def post(self, request, uidb64,token):
        context = {
            'uidb64':uidb64,
            'token':token
        }
        
        password =request.POST['pass1']
        confirm_password = request.POST['pass2']
        if password != confirm_password:
            messages.warning(request, 'Password is not mathching')
            return render(request, 'set-new-password.html')
        
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)
            user.set_password(password)
            user.save()
            messages.success(request,'Password reset success Please Login with new password')
            return redirect('/auth/login/')
        
        except DjangoUnicodeDecodeError as identifier:
            messages.error(request,'Something went wrong')
            return render(request,'set-new-password.html', context)
        
        