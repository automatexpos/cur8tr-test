import os
import re
import qrcode
from io import BytesIO
from PIL import Image
import unicodedata

def slugify(text):
    """
    Convert text to a URL-friendly slug
    """
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Convert to lowercase and replace spaces/special chars with hyphens
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[-\s]+', '-', text)
    
    return text

def generate_qr_code(url, filename_prefix):
    """
    Generate QR code for the given URL and save it to static/qrcodes/
    Returns the filename of the generated QR code
    """
    # Create qrcodes directory if it doesn't exist
    qr_dir = os.path.join('static', 'qrcodes')
    os.makedirs(qr_dir, exist_ok=True)
    
    # Generate QR code
    qr = qrcode.main.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save the image
    filename = f"{slugify(filename_prefix)}_qr.png"
    filepath = os.path.join(qr_dir, filename)
    img.save(filepath)
    
    return filename

def send_verification_email(email, code):
    """
    Send verification email (placeholder for actual email implementation)
    In a real app, this would use a service like SendGrid, Mailgun, etc.
    """
    # For now, just log the verification code
    import logging
    logging.info(f"Verification code for {email}: {code}")
    return True

def format_url(url):
    """
    Format URL to ensure it has a protocol
    """
    if not url:
        return url
    
    if not url.startswith(('http://', 'https://')):
        return f"https://{url}"
    
    return url

def truncate_text(text, max_length=100):
    """
    Truncate text to specified length with ellipsis
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."

def get_domain_from_url(url):
    """
    Extract domain name from URL for display purposes
    """
    if not url:
        return ""
    
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return url

def create_default_categories(profile):
    """
    Create default categories for a new profile
    """
    from models import Category
    from app import db
    
    default_categories = [
        ("Books", "Your favorite books and reading recommendations"),
        ("YouTube Channels", "Amazing YouTube channels worth following"),
        ("Food", "Restaurants, recipes, and food recommendations"),
        ("Where To Stay", "Hotels, accommodations, and travel spots"),
        ("Apps", "Useful apps and digital tools"),
        ("Products", "Products and services you love")
    ]
    
    created_categories = []
    
    # Get existing category names to avoid duplicates
    existing_categories = Category.query.filter_by(profile_id=profile.id).all()
    existing_names = [cat.name for cat in existing_categories]
    
    for name, description in default_categories:
        if name not in existing_names:  # Only create if it doesn't exist
            slug = slugify(name)
            # Ensure unique slug within profile
            counter = 1
            original_slug = slug
            while Category.query.filter_by(profile_id=profile.id, slug=slug).first():
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            category = Category(
                name=name,
                description=description,
                slug=slug,
                profile_id=profile.id
            )
            db.session.add(category)
            created_categories.append(category)
    
    return created_categories

def get_personalized_welcome_message(user, profile):
    """
    Generate a personalized welcome message based on user activity, engagement patterns, and time of day
    """
    import datetime
    from models import Recommendation, Like, Comment, Follow
    
    now = datetime.datetime.now()
    hour = now.hour
    day_of_week = now.strftime("%A")
    
    # Enhanced time-based greeting with personality
    if 5 <= hour < 12:
        time_greeting = "Good morning" if hour < 10 else "Morning"
    elif 12 <= hour < 17:
        time_greeting = "Good afternoon" if hour < 15 else "Afternoon"
    elif 17 <= hour < 22:
        time_greeting = "Good evening"
    else:
        time_greeting = "Working late" if 22 <= hour < 24 else "Up early"
    
    # Get comprehensive user activity stats
    if profile:
        categories_count = len(profile.categories)
        
        # Count total recommendations and recent activity
        total_recs = 0
        recent_recs = 0
        recommendations_with_tips = 0
        recommendations_with_tags = 0
        
        for category in profile.categories:
            category_recs = len(category.recommendations)
            total_recs += category_recs
            
            # Count recent recommendations (last 7 days)
            recent_recs += len([r for r in category.recommendations 
                              if r.created_at and (now - r.created_at).days <= 7])
            
            # Count recommendations with pro tips and tags
            recommendations_with_tips += len([r for r in category.recommendations if r.pro_tip])
            recommendations_with_tags += len([r for r in category.recommendations if r.tags])
        
        # Get social engagement stats
        follower_count = user.get_follower_count() if hasattr(user, 'get_follower_count') else 0
        
        # Calculate engagement metrics
        total_likes = 0
        total_comments = 0
        if profile.categories:
            for category in profile.categories:
                for rec in category.recommendations:
                    total_likes += rec.get_like_count()
                    total_comments += len(rec.comments)
        
        # Intelligent activity-based messaging
        if total_recs == 0:
            if categories_count == 0:
                activity_message = "Welcome to CUR8tr! Let's start building your first curated list."
                suggestion = "Create a category for something you're passionate about - books, restaurants, apps, or anything!"
            else:
                activity_message = f"You've set up {categories_count} categories. Time to add your first recommendation!"
                suggestion = "Pick your favorite category and share something you genuinely love."
        elif total_recs < 5:
            engagement_note = f" with {total_likes} likes!" if total_likes > 0 else ""
            activity_message = f"Great progress! {total_recs} recommendation{'s' if total_recs != 1 else ''}{engagement_note}"
            
            if recommendations_with_tips == 0:
                suggestion = "Try adding a 'Pro Tip' to your next recommendation - share insider knowledge!"
            elif recommendations_with_tags == 0:
                suggestion = "Add tags to your recommendations to help organize them by themes or collections."
            else:
                suggestion = "Keep the momentum going - your curated lists are becoming valuable resources."
        elif total_recs < 15:
            quality_score = recommendations_with_tips / total_recs if total_recs > 0 else 0
            activity_message = f"Excellent! {total_recs} recommendations across {categories_count} categories."
            
            if quality_score < 0.3:
                suggestion = "Consider adding Pro Tips to more recommendations - they make your advice extra valuable!"
            elif follower_count == 0:
                suggestion = "Your profile is looking great! Share your unique URL with friends to start building followers."
            else:
                suggestion = f"You're gaining traction with {follower_count} followers. Keep sharing quality recommendations!"
        else:
            expertise_level = "curator extraordinaire" if total_recs >= 30 else "curation expert"
            activity_message = f"Impressive! {total_recs} recommendations - you're a true {expertise_level}!"
            
            if total_comments > 20:
                suggestion = f"Your recommendations are sparking conversations! {total_comments} comments show real engagement."
            elif follower_count > 5:
                suggestion = f"Your influence is growing - {follower_count} followers trust your recommendations."
            else:
                suggestion = "Consider sharing your profile on social media to reach more people who need great recommendations."
        
        # Dynamic milestone detection with personality
        milestone_message = ""
        if total_recs == 1:
            milestone_message = "🎉 First recommendation posted! You're officially a curator now."
        elif total_recs == 5:
            milestone_message = "🌟 5 recommendations! You're building a solid foundation."
        elif total_recs == 10:
            milestone_message = "🔥 Double digits! 10 recommendations is a serious achievement."
        elif total_recs == 25:
            milestone_message = "⭐ 25 recommendations! People are going to love browsing your lists."
        elif total_recs == 50:
            milestone_message = "🚀 50 recommendations! You've built something truly special."
        elif total_recs == 100:
            milestone_message = "👑 100 recommendations! You're in the curator hall of fame."
        elif follower_count == 5:
            milestone_message = "👥 5 followers! Your recommendations are resonating with people."
        elif follower_count == 10:
            milestone_message = f"🎯 {follower_count} followers! You're becoming an influencer in your niches."
        elif follower_count >= 25:
            milestone_message = f"🌟 {follower_count} followers! You're definitely making an impact."
        elif total_likes >= 20:
            milestone_message = f"❤️ {total_likes} total likes! People really appreciate your recommendations."
        elif recent_recs >= 3:
            milestone_message = f"🔥 {recent_recs} new recommendations this week! You're on fire."
        
        # Weekend-specific messages
        weekend_boost = ""
        if day_of_week in ["Saturday", "Sunday"] and hour >= 10:
            if recent_recs == 0:
                weekend_boost = " Perfect weekend time to add some new discoveries!"
            else:
                weekend_boost = " Great weekend for curating!"
        
        # Append weekend boost to suggestion if applicable
        if weekend_boost:
            suggestion += weekend_boost
        
        return {
            'greeting': f"{time_greeting}, {user.username}!",
            'activity': activity_message,
            'suggestion': suggestion,
            'milestone': milestone_message,
            'stats': {
                'recommendations': total_recs,
                'categories': categories_count,
                'followers': follower_count,
                'likes': total_likes,
                'comments': total_comments,
                'recent_activity': recent_recs,
                'quality_indicators': {
                    'with_tips': recommendations_with_tips,
                    'with_tags': recommendations_with_tags
                }
            }
        }
    else:
        # Enhanced messaging for users without profiles
        onboarding_messages = [
            "Welcome to CUR8tr! Let's create your recommendation profile.",
            "Ready to start curating? Your recommendation journey begins here.",
            "Time to share what you love! Create your first curated list.",
        ]
        
        import random
        welcome_variety = random.choice(onboarding_messages)
        
        return {
            'greeting': f"{time_greeting}, {user.username}!",
            'activity': welcome_variety,
            'suggestion': "Start by setting up your profile and adding categories for things you're passionate about.",
            'milestone': "",
            'stats': {
                'recommendations': 0,
                'categories': 0,
                'followers': 0,
                'likes': 0,
                'comments': 0,
                'recent_activity': 0,
                'quality_indicators': {
                    'with_tips': 0,
                    'with_tags': 0
                }
            }
        }
