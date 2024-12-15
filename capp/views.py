from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q, Count, Avg, Case, When
from django.contrib.auth.forms import UserCreationForm
from .models import Room, Message, UserProfile, TranslationMetric, Feedback
from .forms import UserProfileForm, CustomUserCreationForm, FeedbackForm
from .translation import Translator
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models.functions import TruncDate, ExtractHour
import json
import logging

logger = logging.getLogger(__name__)
translator = Translator()

def register(request):
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            
            login(request, user)
            messages.success(request, "Welcome to BizNest! Your account has been created successfully.")
            return redirect('rooms')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        user_form = CustomUserCreationForm()
        profile_form = UserProfileForm()
    
    return render(request, 'register.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back to BizNest, {username}!")
            return redirect('rooms')
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login_view')

@login_required
def rooms(request):
    rooms = Room.objects.all()
    return render(request, 'rooms.html', {
        'rooms': rooms,
        'title': 'BizNest Rooms'
    })

@login_required
def room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    return render(request, 'room.html', {
        'room': room,
        'title': f'BizNest - {room.name}'
    })

@login_required
def search(request):
    query = request.GET.get('q', '')
    results = []
    
    if query:
        results = Room.objects.filter(
            Q(name__icontains=query) |
            Q(slug__icontains=query)
        )
    
    return render(request, 'search.html', {
        'results': results,
        'query': query,
        'title': 'Search BizNest Rooms'
    })

@login_required
def profile_settings(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user.userprofile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your language preference has been updated successfully.")
            return redirect('profile_settings')
    else:
        form = UserProfileForm(instance=request.user.userprofile)
    
    return render(request, 'profile_settings.html', {
        'form': form,
        'title': 'Language Settings'
    })

@login_required
def create_room(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        pin = request.POST.get('pin')
        if name and pin:
            if not Room.objects.filter(slug=pin).exists():
                room = Room.objects.create(name=name, slug=pin)
                messages.success(request, f"Room '{name}' has been created with PIN: {pin}")
                return redirect('room', room_id=room.id)
            else:
                messages.error(request, "A room with this PIN already exists.")
    
    return render(request, 'create_room.html', {'title': 'Create New Room'})

@login_required
def join_room(request):
    if request.method == 'POST':
        pin = request.POST.get('pin')
        if pin:
            room = Room.objects.filter(slug=pin).first()
            if room:
                return redirect('room', room_id=room.id)
            else:
                messages.error(request, "No room found with this PIN.")
    
    return render(request, 'join_room.html', {'title': 'Join Room'})

@login_required
def feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.nameer = request.user
            feedback.save()
            messages.success(request, "Thank you for your feedback!")
            return redirect('rooms')
    else:
        form = FeedbackForm()
    
    return render(request, 'feedback.html', {
        'form': form,
        'title': 'Provide Feedback'
    })

@staff_member_required
def admin_dashboard(request):
    # Basic stats
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    total_feedbacks = Feedback.objects.count()
    online_users = User.objects.filter(
        last_login__gte=timezone.now() - timezone.timedelta(minutes=15)
    ).count()
    
    # Language statistics
    language_stats = list(UserProfile.objects.values('preferred_language')
        .annotate(count=Count('id'))
        .order_by('-count'))
    
    # Format data for charts
    language_labels = [stat['preferred_language'] for stat in language_stats]
    language_counts = [stat['count'] for stat in language_stats]
    
    # Hourly activity
    hourly_activity = list(Message.objects.annotate(
        hour=ExtractHour('date_added')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('hour'))
    
    hourly_labels = [str(h['hour']) + ':00' for h in hourly_activity]
    hourly_counts = [h['count'] for h in hourly_activity]
    
    # User growth (last 30 days)
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    user_growth = list(User.objects.filter(
        date_joined__gte=thirty_days_ago
    ).annotate(
        date=TruncDate('date_joined')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date'))
    
    growth_labels = [g['date'].strftime('%Y-%m-%d') for g in user_growth]
    growth_counts = [g['count'] for g in user_growth]
    
    # Simple keyword-based feedback analysis
    positive_words = {'good', 'great', 'excellent', 'amazing', 'love', 'helpful', 'thanks', 'thank', 'awesome'}
    negative_words = {'bad', 'poor', 'terrible', 'hate', 'useless', 'difficult', 'not working', 'problem'}
    
    feedback_sentiments = {
        'positive': 0,
        'neutral': 0,
        'negative': 0
    }
    
    # Get recent feedbacks with sentiment
    recent_feedbacks = []
    for feedback in Feedback.objects.select_related('nameer').order_by('-created_at')[:5]:
        words = set(feedback.feedinfo.lower().split())
        
        if any(word in positive_words for word in words):
            sentiment = 'positive'
            feedback_sentiments['positive'] += 1
        elif any(word in negative_words for word in words):
            sentiment = 'negative'
            feedback_sentiments['negative'] += 1
        else:
            sentiment = 'neutral'
            feedback_sentiments['neutral'] += 1
            
        recent_feedbacks.append({
            'nameer': feedback.nameer,
            'feedinfo': feedback.feedinfo,
            'created_at': feedback.created_at,
            'sentiment': sentiment
        })
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'online_users': online_users,
        'total_feedbacks': total_feedbacks,
        'language_labels': json.dumps(language_labels),
        'language_counts': json.dumps(language_counts),
        'hourly_labels': json.dumps(hourly_labels),
        'hourly_counts': json.dumps(hourly_counts),
        'growth_labels': json.dumps(growth_labels),
        'growth_counts': json.dumps(growth_counts),
        'feedback_sentiments': json.dumps(feedback_sentiments),
        'recent_feedbacks': recent_feedbacks,
    }
    
    return render(request, 'admin_dashboard.html', context)

@staff_member_required
def admin_feedback(request):
    feedbacks = Feedback.objects.all().order_by('-created_at')
    paginator = Paginator(feedbacks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_feedback.html', {
        'page_obj': page_obj,
        'total_feedbacks': feedbacks.count(),
        'title': 'User Feedback'
    })

def developers(request):
    developers = [
        {
            'name': 'Bright Bunhu',
            'email': 'brightbunhu4@gmail.com',
            'reg_number': 'R232208V',
            'role': 'Lead Developer',
            'phone': '+263 XX XXX XXXX'
        },
        {
            'name': 'Brighton Sande',
            'email': 'brighonkiddy28@gmail.com',
            'reg_number': 'R232303E',
            'role': 'Backend Developer',
            'phone': '+263 XX XXX XXXX'
        },
        {
            'name': 'Shania Nyaude',
            'email': 'r235384x@students.msu.ac.zw',
            'reg_number': 'R235384X',
            'role': 'Frontend Developer',
            'phone': '+263 XX XXX XXXX'
        },
        {
            'name': 'Chikomborero Manyere',
            'email': 'R233226w@students.msu.ac.zw',
            'reg_number': 'R233226W',
            'role': 'UI/UX Designer',
            'phone': '+263 XX XXX XXXX'
        },
        {
            'name': 'Denzel Mhandu',
            'email': 'r234433p@students.msu.ac.zw',
            'reg_number': 'R234433P',
            'role': 'Quality Assurance',
            'phone': '+263 XX XXX XXXX'
        }
    ]
    
    return render(request, 'developers.html', {
        'developers': developers,
        'title': 'Our Development Team'
    })

@staff_member_required
def translation_metrics(request):
    # Get metrics from the database
    metrics = TranslationMetric.objects.all()
    
    # Calculate success rate
    success_rate = (metrics.filter(success=True).count() / metrics.count()) * 100 if metrics.count() > 0 else 0
    
    # Calculate average translation time
    avg_translation_time = metrics.aggregate(Avg('translation_time'))['translation_time__avg'] or 0
    
    # Get recent metrics
    recent_metrics = metrics.order_by('-timestamp')[:10]
    
    # Get language pair statistics
    language_pairs = metrics.values('source_language', 'target_language')\
        .annotate(
            count=Count('id'), 
            avg_time=Avg('translation_time'),
            success_rate=Count(Case(When(success=True, then=1))) * 100.0 / Count('id')
        )\
        .order_by('-count')[:5]
    
    context = {
        'success_rate': success_rate,
        'avg_translation_time': avg_translation_time,
        'recent_metrics': recent_metrics,
        'language_pairs': language_pairs,
        'total_translations': metrics.count(),
        'successful_translations': metrics.filter(success=True).count(),
        'failed_translations': metrics.filter(success=False).count(),
    }
    
    return render(request, 'translation_metrics.html', context)
