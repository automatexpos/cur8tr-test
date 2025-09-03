from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SelectField, URLField
from wtforms.validators import DataRequired, Email, Length, EqualTo, URL, Optional, Regexp

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=3, max=80, message="Username must be between 3 and 80 characters")
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=6, message="Password must be at least 6 characters")
    ])
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('password', message="Passwords must match")
    ])

class ProfileForm(FlaskForm):
    name = StringField('Profile Name', validators=[
        DataRequired(), 
        Length(min=2, max=100, message="Profile name must be between 2 and 100 characters")
    ])
    bio = TextAreaField('Bio', validators=[Length(max=500, message="Bio must be less than 500 characters")])
    profile_image = FileField('Profile Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Only image files are allowed (JPG, PNG, GIF)')
    ])
    country = StringField('Country', validators=[
        Optional(),
        Length(max=56, message="Country name must be less than 56 characters")
    ])
    city = StringField('City', validators=[
        Optional(),
        Length(max=56, message="City name must be less than 56 characters")

    ])
    instagram_handle = StringField('Instagram Handle', validators=[
        Optional(),
        Length(max=30, message="Instagram handle must be less than 30 characters"),
        Regexp(r'^[a-zA-Z0-9._]+$', message="Instagram handle can only contain letters, numbers, dots, and underscores")
    ])
    tiktok_handle = StringField('TikTok Handle', validators=[
        Optional(),
        Length(max=30, message="TikTok handle must be less than 30 characters"),
        Regexp(r'^[a-zA-Z0-9._]+$', message="TikTok handle can only contain letters, numbers, dots, and underscores")
    ])
    is_public = BooleanField('Make profile public', default=True)

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[
        DataRequired(), 
        Length(min=2, max=100, message="Category name must be between 2 and 100 characters")
    ])
    description = TextAreaField('Description', validators=[
        Length(max=300, message="Description must be less than 300 characters")
    ])

class RecommendationForm(FlaskForm):
    category_id = SelectField('Category', validators=[DataRequired()], coerce=int)
    title = StringField('Title', validators=[
        DataRequired(), 
        Length(min=2, max=200, message="Title must be between 2 and 200 characters")
    ])
    rating = SelectField('Rating', validators=[DataRequired()], choices=[
        (5, '👍👍👍👍👍 - Absolutely love it!'),
        (4, '👍👍👍👍 - Really great'),
        (3, '👍👍👍 - Pretty good'),
        (2, '👍👍 - It\'s okay'),
        (1, '👍 - Meh, not great')
    ], coerce=int)


    cost_rating = SelectField('Cost', validators=[DataRequired()], choices=[
        ('$', '$ - Budget-friendly'),
        ('$$', '$$ - Moderate'),
        ('$$$', '$$$ - Expensive'),
        ('$$$$', '$$$$ - Premium/Luxury')
    ])
    description = TextAreaField('Description', validators=[
        Length(max=1000, message="Description must be less than 1000 characters")
    ])
    pro_tip = TextAreaField('Pro Tip', validators=[
        Optional(),
        Length(max=500, message="Pro tip must be less than 500 characters")
    ], render_kw={'placeholder': 'Share an insider tip or secret about this recommendation...'})
    url = URLField('URL', validators=[Optional(), URL(message="Please enter a valid URL")])
    location = StringField('Location', validators=[
        Optional(),
        Length(max=300, message="Location must be less than 300 characters")
    ])
    image = FileField('Recommendation Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Only image files are allowed (JPG, PNG, GIF)')
    ])
    
    # Tagging fields
    category_tags = StringField('Category Tags', validators=[Optional()],
                               render_kw={'placeholder': 'e.g., food, coffee, restaurants (separate with commas)'})
    collection_tags = StringField('Collection Tags', validators=[Optional()],
                                 render_kw={'placeholder': 'e.g., sayulita, summer-2025, date-night (separate with commas)'})

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[
        DataRequired(message="Comment cannot be empty"),
        Length(min=1, max=500, message="Comment must be between 1 and 500 characters")
    ], render_kw={"placeholder": "Share your thoughts about this recommendation..."})
