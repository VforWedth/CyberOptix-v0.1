from django.shortcuts import redirect, render
from userauths.forms import UserRegisterForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages

def register_view(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            
            # Auto-login after registration
            login(request, user)
            messages.success(request, f"Welcome {username}! Your account was created successfully!")
            return redirect("flame:home")
        else:
            # Pass form errors to template
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.title()}: {error}")
    else:
        form = UserRegisterForm()

    context = {'form': form}
    return render(request, "userauths/sign-up.html", context)

def login_view(request):
    if request.user.is_authenticated:
        messages.warning(request, "You are already logged in.")
        return redirect("flame:home")
    
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")  # Changed from password1 to password
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, "You are now logged in.")
            return redirect("flame:home")
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, "userauths/sign-in.html")

def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        request.session.flush()       
        

    else: 
        messages.warning(request, "No user is currently logged in.")
    return redirect("userauths:sign-in")
