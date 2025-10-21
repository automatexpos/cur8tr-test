import os
import random
import string
import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import render_template, request, redirect, url_for, flash, session, abort, send_from_directory, make_response, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import User, Profile, Category, Recommendation, Follow, Like, Comment
from forms import LoginForm, RegisterForm, ProfileForm, CategoryForm, RecommendationForm, CommentForm
from utils import generate_qr_code, slugify, create_default_categories, get_personalized_welcome_message
from utils_image import get_safe_image_url, create_modern_placeholder  
from messages import UserMessages, flash_auth, flash_content, flash_social

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash_auth('access_denied')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash_auth('access_denied')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def save_uploaded_file(file):
    """Convert uploaded file to base64 data URL for database storage"""
    if file and file.filename:
        # Read file data
        file.seek(0)
        file_data = file.read()
        
        # Get file extension to determine MIME type
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        # Map common extensions to MIME types
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg', 
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        
        mime_type = mime_types.get(ext, 'image/jpeg')
        
        # Convert to base64 data URL
        import base64
        base64_data = base64.b64encode(file_data).decode('utf-8')
        data_url = f"data:{mime_type};base64,{base64_data}"
        
        return data_url
    return None

def register_routes(app, db):
    """Register all application routes"""
    
    # Register tagging API routes
    from routes_tagging import bp as tagging_bp
    app.register_blueprint(tagging_bp)
    
    # Context processor for template access to current user and image helpers
    @app.context_processor
    def inject_current_user():
        """Make current user available in templates"""
        def get_current_user():
            if 'user_id' in session:
                return User.query.get(session['user_id'])
            return None
        return dict(get_current_user=get_current_user)
    
    # Template filter for safe image display
    @app.template_filter('safe_image')
    def safe_image_filter(image_field, fallback_title="Image", width=400, height=300):
        """Template filter to ensure images are always valid"""
        return get_safe_image_url(image_field, fallback_title, (width, height))
    
    @app.route('/')
    def home():
        """Home page showing recent recommendations and public profiles"""
        # Get recent public profiles (limit to 3)
        profiles = Profile.query.filter_by(is_public=True).order_by(Profile.created_at.desc()).limit(3).all()
        
        # Get most recent recommendations from public profiles (limit to 8)
        recent_recommendations = db.session.query(Recommendation).join(Category).join(Profile).filter(
            Profile.is_public == True
        ).order_by(Recommendation.created_at.desc()).limit(8).all()
        
        # Get Popular Pro Tips (top 3 most upvoted with pro tips from current month)
        from datetime import datetime, timedelta
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        popular_pro_tips = db.session.query(Recommendation).join(Category).join(Profile).filter(
            Profile.is_public == True,
            Recommendation.pro_tip != None,
            Recommendation.pro_tip != '',
            Recommendation.created_at >= current_month_start
        ).outerjoin(Like).group_by(Recommendation.id).order_by(
            db.func.count(Like.id).desc(),
            Recommendation.created_at.desc()
        ).limit(4).all()
        
        # If not enough tips from current month, get from all time
        if len(popular_pro_tips) < 4:
            popular_pro_tips = db.session.query(Recommendation).join(Category).join(Profile).filter(
                Profile.is_public == True,
                Recommendation.pro_tip != None,
                Recommendation.pro_tip != ''
            ).outerjoin(Like).group_by(Recommendation.id).order_by(
                db.func.count(Like.id).desc(),
                Recommendation.created_at.desc()
            ).limit(4).all()
        
        return render_template('home.html', 
                             profiles=profiles, 
                             recent_recommendations=recent_recommendations,
                             popular_pro_tips=popular_pro_tips)
    
    @app.route('/test-messages')
    def test_messages():
        """Demo page for elegant message system"""
        return render_template('test_messages.html')

    @app.route('/auth/register', methods=['GET', 'POST'])
    def register():
        """User registration with 6-digit verification"""
        import logging
        logging.info(f"Register route accessed: method={request.method}")
        
        form = RegisterForm()
        
        if request.method == 'POST':
            logging.info(f"POST data received: {request.form}")
            logging.info(f"Form validation errors: {form.errors}")
            logging.info(f"Form validate_on_submit: {form.validate_on_submit()}")
        
        if form.validate_on_submit():
            logging.info("Form validation passed, processing registration")
            
            # Check if user already exists
            if User.query.filter_by(username=form.username.data).first():
                logging.info(f"Username {form.username.data} already exists")
                flash_auth('register_username_taken')
                return render_template('auth/register.html', form=form)
            
            if User.query.filter_by(email=form.email.data).first():
                logging.info(f"Email {form.email.data} already registered")
                flash_auth('register_email_taken')
                return render_template('auth/register.html', form=form)
            
            # Generate 6-digit verification code
            verification_code = ''.join(random.choices(string.digits, k=6))
            logging.info(f"Generated verification code: {verification_code}")
            
            # Store user data in session for verification step
            session['pending_user'] = {
                'username': form.username.data,
                'email': form.email.data,
                'password_hash': generate_password_hash(form.password.data),
                'verification_code': verification_code,
                'expires_at': (datetime.now() + timedelta(minutes=10)).isoformat()
            }
            
            # In a real app, send verification email here
            # For now, we'll show the code on the page  
            flash_auth('register_success')
            flash(f'Verification code: {verification_code} (expires in 10 minutes)', 'info')
            logging.info("Redirecting to verification page")
            return redirect(url_for('verify_registration'))
        else:
            if request.method == 'POST':
                logging.error(f"Form validation failed: {form.errors}")
        
        return render_template('auth/register.html', form=form)

    @app.route('/auth/verify', methods=['GET', 'POST'])
    def verify_registration():
        """Verify 6-digit code and complete registration"""
        if 'pending_user' not in session:
            flash_auth('register_success') # Redirect them to register with helpful message
            return redirect(url_for('register'))
        
        pending_user = session['pending_user']
        expires_at = datetime.fromisoformat(pending_user['expires_at'])
        
        if datetime.now() > expires_at:
            del session['pending_user']
            flash_auth('verify_expired')
            return redirect(url_for('register'))
        
        if request.method == 'POST':
            code = request.form.get('verification_code', '').strip()
            if code == pending_user['verification_code']:
                # Create the user
                user = User(
                    username=pending_user['username'],
                    email=pending_user['email'],
                    password_hash=pending_user['password_hash'],
                    is_verified=True
                )
                db.session.add(user)
                db.session.commit()
                
                del session['pending_user']
                session['user_id'] = user.id
                flash_auth('verify_success')
                return redirect(url_for('dashboard'))
            else:
                flash_auth('verify_invalid_code')
        
        return render_template('auth/verify.html', pending_user=pending_user)

    @app.route('/auth/login', methods=['GET', 'POST'])
    def login():
        """User login"""
        import logging
        logging.basicConfig(level=logging.DEBUG)
        logging.info(f"=== LOGIN ATTEMPT: method={request.method} ===")
        
        form = LoginForm()
        
        if request.method == 'POST':
            logging.info(f"POST data: {dict(request.form)}")
            logging.info(f"Session before: {dict(session)}")
            
            # Get form data directly (bypass WTForms validation for simplicity)
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            
            logging.info(f"Extracted - Username: '{username}', Password length: {len(password)}")
            
            # Check if user exists
            user = User.query.filter_by(username=username).first()
            logging.info(f"User lookup result: {user is not None}")
            
            if user:
                logging.info(f"User details - ID: {user.id}, Verified: {user.is_verified}")
                password_valid = check_password_hash(user.password_hash, password)
                logging.info(f"Password validation: {password_valid}")
                
                if password_valid and user.is_verified:
                    # Login successful
                    session.clear()  # Clear any old session data
                    session['user_id'] = user.id
                    session.permanent = True
                    logging.info(f"SUCCESS: User {username} logged in, session: {dict(session)}")
                    flash_auth('login_success')
                    
                    # Simple redirect - no absolute URL or cache-busting needed
                    logging.info(f"Redirecting to dashboard")
                    return redirect(url_for('dashboard'))
                elif not user.is_verified:
                    logging.info("User not verified")
                    flash_auth('login_unverified')
                elif not password_valid:
                    logging.info("Invalid password")
                    flash_auth('login_wrong_password')
            else:
                logging.info("User not found")
                flash_auth('login_user_not_found')
        
        logging.info("Rendering login form")
        return render_template('auth/login.html', form=form)

    @app.route('/auth/forgot', methods=['GET', 'POST'])
    def forgot_password():
        """Password reset request page"""
        if request.method == 'POST':
            email = request.form.get('email', '').strip()
            user = User.query.filter_by(email=email).first()
            if user:
                # In a real app, send password reset email here
                flash('Password reset instructions sent to your email.', 'info')
            else:
                flash('No account found with that email.', 'warning')
        return render_template('auth/forgot.html')

    @app.route('/test-session')
    def test_session():
        """Test session functionality for deployment debugging"""
        import json
        session['test'] = 'working'
        session_data = {
            'session_test': session.get('test'), 
            'user_id': session.get('user_id'),
            'all_session_keys': list(session.keys()),
            'session_cookie_domain': app.config.get('SESSION_COOKIE_DOMAIN'),
            'session_cookie_path': app.config.get('SESSION_COOKIE_PATH'),
            'request_host': request.host,
            'request_url': request.url
        }
        return f"<pre>{json.dumps(session_data, indent=2)}</pre>"

    @app.route('/whoami')
    def whoami():
        """Authentication probe endpoint"""
        import json
        return json.dumps({
            "authenticated": session.get('user_id') is not None,
            "user_id": session.get('user_id'),
            "session_keys": list(session.keys()),
            "headers": {
                "Host": request.host,
                "X-Forwarded-Proto": request.headers.get("X-Forwarded-Proto"),
                "User-Agent": request.headers.get("User-Agent", "")[:50] + "..."
            }
        })

    @app.route("/cookie-diag")
    def cookie_diag():
        """Cookie diagnostic endpoint to test cookie setting/reading"""
        import json
        resp = make_response(json.dumps({
            "received_cookie": request.cookies.get("cookie_diag"),
            "host": request.host,
            "xfp": request.headers.get("X-Forwarded-Proto"),
            "all_cookies": dict(request.cookies)
        }))
        # Auto-detect production environment for cookie security
        import os
        is_production = os.environ.get('REPL_ID') is not None
        
        resp.set_cookie(
            "cookie_diag", "hello",
            httponly=True,
            secure=is_production,       # True for HTTPS deployment, False for local HTTP
            samesite="Lax"              # switch to "None" if embedded/iframe
            # NOTE: no domain, no path overrides
        )
        resp.headers['Content-Type'] = 'application/json'
        return resp

    @app.route("/cookie-diag-read")
    def cookie_diag_read():
        """Read the diagnostic cookie"""
        import json
        return json.dumps({
            "cookie_diag": request.cookies.get("cookie_diag"),
            "all_cookies": dict(request.cookies)
        })

    @app.route('/auth/logout')
    def logout():
        """User logout"""
        session.pop('user_id', None)
        flash_auth('logout_success')
        return redirect(url_for('home'))
    
    @app.route('/tagging-demo')
    def tagging_demo():
        """Demo page for the new tagging system"""
        return render_template('tagging_demo.html')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        import logging
        logging.info(f"Dashboard accessed by user_id: {session.get('user_id')}")
        user = User.query.get(session['user_id'])
        profile = Profile.query.filter_by(user_id=user.id).first()
        recent_recs = []

        if profile:
            recent_recs = Recommendation.query.join(Category).filter(
                Category.profile_id == profile.id
            ).order_by(Recommendation.created_at.desc()).limit(5).all()

            # Total recommendations
            total_recommendations = Recommendation.query.join(Category).filter(
                Category.profile_id == profile.id
            ).count()

            # Total categories
            total_categories = Category.query.filter_by(profile_id=profile.id).count()

            # Total followers (users who follow this user)
            total_followers = Follow.query.filter_by(followed_id=user.id).count()

            # Total likes (likes on this user's recommendations)
            total_likes = Like.query.join(Recommendation).join(Category).filter(
                Category.profile_id == profile.id
            ).count()

            # Total comments (comments on this user's recommendations)
            total_comments = Comment.query.join(Recommendation).join(Category).filter(
                Category.profile_id == profile.id
            ).count()
        else:
            total_recommendations = 0
            total_categories = 0
            total_followers = 0
            total_likes = 0
            total_comments = 0

        # Get personalized welcome message
        welcome_message = get_personalized_welcome_message(user, profile)

        dashboard_stats = {
            "total_recommendations": total_recommendations,
            "total_categories": total_categories,
            "total_followers": total_followers,
            "total_likes": total_likes,
            "total_comments": total_comments
        }

        logging.info(f"Rendering dashboard for user: {user.username}")
        return render_template('dashboard/index.html', 
                            user=user, 
                            profile=profile, 
                            recent_recs=recent_recs,
                            welcome_message=welcome_message,
                            dashboard_stats=dashboard_stats)

    @app.route('/dashboard/profile', methods=['GET', 'POST'])
    @login_required
    def dashboard_profile():
        """Manage user profile"""
        user = User.query.get(session['user_id'])
        profile = Profile.query.filter_by(user_id=user.id).first()
        
        form = ProfileForm()
        if form.validate_on_submit():
            print(form.data)
            # Handle profile image upload
            profile_image_url = None
            if form.profile_image.data:
                profile_image_url = save_uploaded_file(form.profile_image.data)
            
            if profile:
                profile.name = form.name.data
                profile.bio = form.bio.data
                profile.country = form.country.data
                profile.city = form.city.data
                if profile_image_url:
                    profile.profile_image = profile_image_url
                profile.instagram_handle = form.instagram_handle.data
                profile.tiktok_handle = form.tiktok_handle.data
                profile.is_public = form.is_public.data
            else:
                # Create new profile
                slug = slugify(form.name.data)
                counter = 1
                original_slug = slug
                while Profile.query.filter_by(slug=slug).first():
                    slug = f"{original_slug}-{counter}"
                    counter += 1
                
                profile = Profile(
                    name=form.name.data,
                    bio=form.bio.data,
                    country=form.country.data,
                    city=form.city.data,
                    profile_image=profile_image_url,
                    instagram_handle=form.instagram_handle.data,
                    tiktok_handle=form.tiktok_handle.data,
                    slug=slug,
                    user_id=user.id,
                    is_public=form.is_public.data
                )
                db.session.add(profile)
                db.session.flush()
                
                # Create default categories for new profile
                create_default_categories(profile)
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('dashboard_profile'))
                
        if profile:
            form.name.data = profile.name
            form.bio.data = profile.bio
            form.country.data = profile.country
            form.city.data = profile.city
            form.instagram_handle.data = profile.instagram_handle
            form.tiktok_handle.data = profile.tiktok_handle
            form.is_public.data = profile.is_public
        
        return render_template('dashboard/profile.html', form=form, profile=profile)

    @app.route('/dashboard/categories')
    @login_required
    def dashboard_categories():
        """Manage categories"""
        user = User.query.get(session['user_id'])
        profile = Profile.query.filter_by(user_id=user.id).first()
        
        if not profile:
            flash('Please create a profile first.', 'warning')
            return redirect(url_for('dashboard_profile'))
        
        # Check if user has default categories, if not create them
        default_category_names = ["Books", "YouTube Channels", "I Recommend Following", "Food", "Where To Stay", "Apps", "Products"]
        existing_categories = Category.query.filter_by(profile_id=profile.id).all()
        
        existing_names = [cat.name for cat in existing_categories]
        
        # Create missing default categories
        missing_defaults = [name for name in default_category_names if name not in existing_names]
        if missing_defaults:
            create_default_categories(profile)
            db.session.commit()
            if len(missing_defaults) > 0:
                flash(f'Added {len(missing_defaults)} default categories to your profile!', 'success')
        
        categories = Category.query.filter_by(profile_id=profile.id).order_by(Category.name).all()
        
        # Add total recommendations count for each category
        for category in categories:
            category.count = Recommendation.query.filter_by(category_id=category.id).count()
        
        return render_template('dashboard/categories.html', categories=categories, profile=profile)

    @app.route('/dashboard/categories/new', methods=['GET', 'POST'])
    @login_required
    def new_category():
        """Create new category"""
        user = User.query.get(session['user_id'])
        profile = Profile.query.filter_by(user_id=user.id).first()
        
        if not profile:
            flash('Please create a profile first.', 'warning')
            return redirect(url_for('dashboard_profile'))
        
        form = CategoryForm()
        if form.validate_on_submit():
            slug = slugify(form.name.data)
            # Ensure unique slug within profile
            counter = 1
            original_slug = slug
            while Category.query.filter_by(profile_id=profile.id, slug=slug).first():
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            category = Category(
                name=form.name.data,
                description=form.description.data,
                slug=slug,
                profile_id=profile.id
            )
            db.session.add(category)
            db.session.commit()
            flash('Category created successfully!', 'success')
            return redirect(url_for('dashboard_categories'))
        
        return render_template('dashboard/category_form.html', form=form, title="New Category")

    @app.route('/dashboard/categories/form')
    @login_required
    def category_form_modal():
        """Serve the category form HTML for modal (AJAX)"""
        form = CategoryForm()
        return render_template('dashboard/category_form.html', form=form, title="New Category")

    @app.route('/dashboard/categories/<int:category_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_category(category_id):
        """Edit category"""
        user = User.query.get(session['user_id'])
        profile = Profile.query.filter_by(user_id=user.id).first()
        category = Category.query.filter_by(id=category_id, profile_id=profile.id).first_or_404()
        
        form = CategoryForm()
        if form.validate_on_submit():
            # Update slug if name changed
            if category.name != form.name.data:
                slug = slugify(form.name.data)
                counter = 1
                original_slug = slug
                while Category.query.filter_by(profile_id=profile.id, slug=slug).filter(Category.id != category.id).first():
                    slug = f"{original_slug}-{counter}"
                    counter += 1
                category.slug = slug
            
            category.name = form.name.data
            category.description = form.description.data
            db.session.commit()
            flash('Category updated successfully!', 'success')
            return redirect(url_for('dashboard_categories'))
        
        form.name.data = category.name
        form.description.data = category.description
        return render_template('dashboard/category_form.html', form=form, title="Edit Category")

    @app.route('/dashboard/categories/<int:category_id>/delete', methods=['POST'])
    @login_required
    def delete_category(category_id):
        """Delete category"""
        user = User.query.get(session['user_id'])
        profile = Profile.query.filter_by(user_id=user.id).first()
        category = Category.query.filter_by(id=category_id, profile_id=profile.id).first_or_404()
        
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully!', 'success')
        return redirect(url_for('dashboard_categories'))

    @app.route('/dashboard/recommendations')
    @login_required
    def dashboard_recommendations():
        """Manage recommendations"""
        user = User.query.get(session['user_id'])
        profile = Profile.query.filter_by(user_id=user.id).first()
        
        if not profile:
            flash('Please create a profile first.', 'warning')
            return redirect(url_for('dashboard_profile'))
        
        recommendations = Recommendation.query.join(Category).filter(
            Category.profile_id == profile.id
        ).order_by(Recommendation.created_at.desc()).all()
        
        return render_template('dashboard/recs.html', recommendations=recommendations, profile=profile)

    @app.route('/dashboard/recommendations/new', methods=['GET', 'POST'])
    @login_required
    def new_recommendation():
        """Create new recommendation"""
        user = User.query.get(session['user_id'])
        profile = Profile.query.filter_by(user_id=user.id).first()
        
        if not profile:
            flash('Please create a profile first.', 'warning')
            return redirect(url_for('dashboard_profile'))
        
        categories = Category.query.filter_by(profile_id=profile.id).all()
        if not categories:
            flash('Please create a category first.', 'warning')
            return redirect(url_for('new_category'))
        
        form = RecommendationForm()
        form.category_id.choices = [(c.id, c.name) for c in categories]
        
        if form.validate_on_submit():
            # Handle image upload
            image_url = None
            if form.image.data:
                image_url = save_uploaded_file(form.image.data)
            
            recommendation = Recommendation(
                title=form.title.data,
                description=form.description.data,
                pro_tip=form.pro_tip.data,
                url=form.url.data,
                image=image_url,
                rating=form.rating.data,
                cost_rating=form.cost_rating.data,
                location=form.location.data,
                category_id=form.category_id.data
            )
            
            # Process tags
            tags_data = {}
            if form.category_tags.data:
                category_tags = [tag.strip() for tag in form.category_tags.data.split(',') if tag.strip()]
                if category_tags:
                    from models import slugify
                    tags_data['categories'] = [slugify(tag) for tag in category_tags]
            
            if form.collection_tags.data:
                collection_tags = [tag.strip() for tag in form.collection_tags.data.split(',') if tag.strip()]
                if collection_tags:
                    from models import slugify
                    tags_data['collections'] = [slugify(tag) for tag in collection_tags]
            
            # Always set tags, even if empty
            recommendation.tags = tags_data if tags_data else {}
            
            db.session.add(recommendation)
            db.session.commit()
            flash('Recommendation added successfully!', 'success')
            return redirect(url_for('dashboard_recommendations'))
        
        return render_template('dashboard/rec_form.html', form=form, title="New Recommendation")

    @app.route('/dashboard/recommendations/<int:rec_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_recommendation(rec_id):
        """Edit recommendation"""
        user = User.query.get(session['user_id'])
        profile = Profile.query.filter_by(user_id=user.id).first()
        recommendation = Recommendation.query.join(Category).filter(
            Recommendation.id == rec_id,
            Category.profile_id == profile.id
        ).first_or_404()
        
        categories = Category.query.filter_by(profile_id=profile.id).all()
        form = RecommendationForm()
        form.category_id.choices = [(c.id, c.name) for c in categories]
        
        if form.validate_on_submit():
            # Handle image upload
            if form.image.data:
                recommendation.image = save_uploaded_file(form.image.data)
            
            recommendation.title = form.title.data
            recommendation.description = form.description.data
            recommendation.pro_tip = form.pro_tip.data
            recommendation.url = form.url.data
            recommendation.rating = form.rating.data
            recommendation.cost_rating = form.cost_rating.data
            recommendation.location = form.location.data
            recommendation.category_id = form.category_id.data
            
            # Process tags
            tags_data = {}
            if form.category_tags.data:
                category_tags = [tag.strip() for tag in form.category_tags.data.split(',') if tag.strip()]
                if category_tags:
                    from models import slugify
                    tags_data['categories'] = [slugify(tag) for tag in category_tags]
            
            if form.collection_tags.data:
                collection_tags = [tag.strip() for tag in form.collection_tags.data.split(',') if tag.strip()]
                if collection_tags:
                    from models import slugify
                    tags_data['collections'] = [slugify(tag) for tag in collection_tags]
            
            # Always set tags, even if empty
            recommendation.tags = tags_data if tags_data else {}
            
            db.session.commit()
            flash('Recommendation updated successfully!', 'success')
            return redirect(url_for('dashboard_recommendations'))
        
        form.title.data = recommendation.title
        form.description.data = recommendation.description
        form.pro_tip.data = recommendation.pro_tip
        form.url.data = recommendation.url
        form.rating.data = recommendation.rating
        form.cost_rating.data = recommendation.cost_rating
        form.location.data = recommendation.location
        form.category_id.data = recommendation.category_id
        
        # Populate tag fields
        if recommendation.tags:
            if 'categories' in recommendation.tags:
                form.category_tags.data = ', '.join(recommendation.tags['categories'])
            if 'collections' in recommendation.tags:
                form.collection_tags.data = ', '.join(recommendation.tags['collections'])
        
        return render_template('dashboard/rec_form.html', form=form, title="Edit Recommendation", recommendation=recommendation)

    @app.route('/dashboard/recommendations/<int:rec_id>/delete', methods=['POST'])
    @login_required
    def delete_recommendation(rec_id):
        """Delete recommendation"""
        user = User.query.get(session['user_id'])
        profile = Profile.query.filter_by(user_id=user.id).first()
        recommendation = Recommendation.query.join(Category).filter(
            Recommendation.id == rec_id,
            Category.profile_id == profile.id
        ).first_or_404()
        
        db.session.delete(recommendation)
        db.session.commit()
        flash('Recommendation deleted successfully!', 'success')
        return redirect(url_for('dashboard_recommendations'))

    @app.route('/dashboard/share')
    @login_required
    def dashboard_share():
        """Share profile page"""
        user = User.query.get(session['user_id'])
        profile = Profile.query.filter_by(user_id=user.id).first()
        
        if not profile:
            flash('Please create a profile first.', 'warning')
            return redirect(url_for('dashboard_profile'))
        
        profile_url = url_for('view_profile', slug=profile.slug, _external=True)
        qr_filename = None
        
        if profile.is_public:
            # Generate QR code
            qr_filename = generate_qr_code(profile_url, profile.name)
        
        return render_template('dashboard/share.html', 
                             profile=profile, 
                             profile_url=profile_url,
                             qr_filename=qr_filename)

    @app.route('/qr/<filename>')
    def serve_qr(filename):
        """Serve QR code images"""
        return send_from_directory('static/qrcodes', filename)

    @app.route('/p/<slug>')
    def view_profile(slug):
        """View public profile"""
        profile = Profile.query.filter_by(slug=slug, is_public=True).first_or_404()
        categories = Category.query.filter_by(profile_id=profile.id).order_by(Category.name).all()
        return render_template('profile.html', profile=profile, categories=categories)

    @app.route('/follow/<int:user_id>', methods=['POST'])
    @login_required  
    def follow_user(user_id):
        """Follow a user"""
        current_user = User.query.get(session['user_id'])
        user_to_follow = User.query.get_or_404(user_id)
        
        # Check if already following
        if current_user.is_following(user_to_follow):
            flash('You are already following this user.', 'info')
            return redirect(request.referrer or url_for('index'))
        
        # Create follow relationship
        follow = Follow(follower_id=current_user.id, followed_id=user_to_follow.id)
        db.session.add(follow)
        db.session.commit()
        
        flash(f'You are now following {user_to_follow.profile.name if user_to_follow.profile else user_to_follow.username}!', 'success')
        return redirect(request.referrer or url_for('index'))

    @app.route('/unfollow/<int:user_id>', methods=['POST'])
    @login_required
    def unfollow_user(user_id):
        """Unfollow a user"""
        current_user = User.query.get(session['user_id'])
        user_to_unfollow = User.query.get_or_404(user_id)
        
        # Find and remove follow relationship
        follow = Follow.query.filter_by(follower_id=current_user.id, followed_id=user_to_unfollow.id).first()
        if follow:
            db.session.delete(follow)
            db.session.commit()
            flash(f'You have unfollowed {user_to_unfollow.profile.name if user_to_unfollow.profile else user_to_unfollow.username}.', 'success')
        else:
            flash('You are not following this user.', 'info')
        
        return redirect(request.referrer or url_for('index'))

    @app.route('/p/<profile_slug>/<category_slug>')
    def view_category(profile_slug, category_slug):
        """View category page"""
        profile = Profile.query.filter_by(slug=profile_slug, is_public=True).first_or_404()
        category = Category.query.filter_by(profile_id=profile.id, slug=category_slug).first_or_404()
        recommendations = Recommendation.query.filter_by(category_id=category.id).order_by(Recommendation.created_at.desc()).all()
        
        # Get current user for edit/delete permissions
        current_user = None
        if 'user_id' in session:
            current_user = User.query.get(session['user_id'])
            
        return render_template('category.html', profile=profile, category=category, recommendations=recommendations, current_user=current_user)
    
    @app.route('/p/<profile_slug>/<category_slug>/<int:rec_id>', methods=['GET', 'POST'])
    def view_recommendation(profile_slug, category_slug, rec_id):
        """View detailed recommendation page with comment functionality"""
        profile = Profile.query.filter_by(slug=profile_slug, is_public=True).first_or_404()
        category = Category.query.filter_by(profile_id=profile.id, slug=category_slug).first_or_404()
        recommendation = Recommendation.query.filter_by(category_id=category.id, id=rec_id).first_or_404()
        
        # Get current user for like status and commenting
        current_user = None
        if 'user_id' in session:
            current_user = User.query.get(session['user_id'])
        
        # Handle comment submission
        comment_form = CommentForm()
        if comment_form.validate_on_submit() and current_user:
            comment = Comment(
                content=comment_form.content.data,
                user_id=current_user.id,
                recommendation_id=recommendation.id
            )
            db.session.add(comment)
            db.session.commit()
            flash('Comment added successfully!', 'success')
            return redirect(url_for('view_recommendation', profile_slug=profile_slug, category_slug=category_slug, rec_id=rec_id))
        
        return render_template('recommendation.html', profile=profile, category=category, recommendation=recommendation, current_user=current_user, comment_form=comment_form)
    
    @app.route('/p/<profile_slug>/<category_slug>/<int:rec_id>/like', methods=['POST'])
    @login_required  
    def like_recommendation(profile_slug, category_slug, rec_id):
        """Like/unlike a recommendation"""
        profile = Profile.query.filter_by(slug=profile_slug, is_public=True).first_or_404()
        category = Category.query.filter_by(profile_id=profile.id, slug=category_slug).first_or_404()
        recommendation = Recommendation.query.filter_by(id=rec_id, category_id=category.id).first_or_404()
        
        user = User.query.get(session['user_id'])
        existing_like = Like.query.filter_by(user_id=user.id, recommendation_id=recommendation.id).first()
        
        if existing_like:
            # Unlike - remove the existing like
            db.session.delete(existing_like)
            action = 'unliked'
        else:
            # Like - create new like
            like = Like(user_id=user.id, recommendation_id=recommendation.id)
            db.session.add(like)
            action = 'liked'
        
        db.session.commit()
        
        # Return JSON response for AJAX or redirect for form submission
        if request.method == 'POST':
            return jsonify({
                'success': True,
                'action': action,
                'like_count': recommendation.get_like_count(),
                'is_liked': recommendation.is_liked_by(user)
            })
        else:
            flash(f'Recommendation {action}!', 'success')
            return redirect(url_for('view_recommendation', profile_slug=profile_slug, category_slug=category_slug, rec_id=rec_id))

    
    @app.route('/p/<profile_slug>/<category_slug>/<int:rec_id>/comment/<int:comment_id>/delete', methods=['POST'])
    @login_required
    def delete_comment(profile_slug, category_slug, rec_id, comment_id):
        """Delete a comment (only by the comment author or recommendation owner)"""
        profile = Profile.query.filter_by(slug=profile_slug, is_public=True).first_or_404()
        category = Category.query.filter_by(profile_id=profile.id, slug=category_slug).first_or_404()
        recommendation = Recommendation.query.filter_by(category_id=category.id, id=rec_id).first_or_404()
        comment = Comment.query.filter_by(id=comment_id, recommendation_id=recommendation.id).first_or_404()
        
        current_user = User.query.get(session['user_id'])
        
        # Allow deletion if user is comment author or recommendation owner
        if comment.user_id == current_user.id or recommendation.category.profile.user_id == current_user.id:
            db.session.delete(comment)
            db.session.commit()
            flash('Comment deleted successfully!', 'success')
        else:
            flash('You can only delete your own comments.', 'error')
        
        return redirect(url_for('view_recommendation', profile_slug=profile_slug, category_slug=category_slug, rec_id=rec_id))

    @app.route('/admin')
    @admin_required
    def admin_dashboard():
        """Admin dashboard"""
        user_count = User.query.count()
        profile_count = Profile.query.filter_by(is_public=True).count()
        recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
        
        return render_template('admin/index.html', 
                             user_count=user_count,
                             profile_count=profile_count,
                             recent_users=recent_users,
                             config=app.config)

    @app.route('/test-login')
    def test_login():
        """Test login page with direct form submission"""
        return render_template('test_login.html')