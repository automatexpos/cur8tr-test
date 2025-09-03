from datetime import datetime
from sqlalchemy import Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from app import db
import re



class User(db.Model):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile: Mapped["Profile"] = relationship("Profile", back_populates="user", uselist=False)
    following: Mapped[List["Follow"]] = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower")
    followers: Mapped[List["Follow"]] = relationship("Follow", foreign_keys="Follow.followed_id", back_populates="followed")
    likes: Mapped[List["Like"]] = relationship("Like", back_populates="user")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="user")
    
    def get_follower_count(self):
        """Get the number of followers for this user's profile"""
        if not self.profile:
            return 0
        return len(self.followers)
    
    def is_following(self, user):
        """Check if this user is following another user"""
        return Follow.query.filter_by(follower_id=self.id, followed_id=user.id).first() is not None
    
    def __repr__(self):
        return f'<User {self.username}>'

class Profile(db.Model):
    __tablename__ = 'profiles'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    bio: Mapped[str] = mapped_column(Text)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    profile_image: Mapped[str] = mapped_column(Text)
    instagram_handle: Mapped[str] = mapped_column(String(30))
    tiktok_handle: Mapped[str] = mapped_column(String(30))
    country: Mapped[str] = mapped_column(String(56))  # <-- Add this line
    city: Mapped[str] = mapped_column(String(56))     # <-- Add this line
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")
    categories: Mapped[list["Category"]] = relationship("Category", back_populates="profile", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Profile {self.name}>'

class Category(db.Model):
    __tablename__ = 'categories'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey('profiles.id'), nullable=False)
    
    # Relationships
    profile: Mapped["Profile"] = relationship("Profile", back_populates="categories")
    recommendations: Mapped[list["Recommendation"]] = relationship("Recommendation", back_populates="category", cascade="all, delete-orphan")
    
    # Unique constraint on slug within profile
    __table_args__ = (db.UniqueConstraint('profile_id', 'slug', name='unique_category_slug_per_profile'),)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    pro_tip: Mapped[Optional[str]] = mapped_column(Text)  # Pro tip field for insider knowledge
    url: Mapped[str] = mapped_column(String(500))
    image: Mapped[str] = mapped_column(Text)  # Base64 data URL for recommendation image
    rating: Mapped[int] = mapped_column(Integer)  # 1-5 thumbs up rating
    cost_rating: Mapped[str] = mapped_column(String(10))  # $, $$, $$$, $$$$
    location: Mapped[str] = mapped_column(String(300))  # Address, city, state, country
    tags: Mapped[Optional[dict]] = mapped_column(JSON)  # JSON field storing tags: {"categories": ["food"], "collections": ["sayulita", "summer-2025"]}
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('categories.id'), nullable=False)
    
    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="recommendations")
    likes: Mapped[List["Like"]] = relationship("Like", back_populates="recommendation", cascade="all, delete-orphan")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="recommendation", cascade="all, delete-orphan", order_by="Comment.created_at.desc()")

    
    def get_like_count(self):
        """Get the number of likes for this recommendation"""
        return len(self.likes)
    
    def is_liked_by(self, user):
        """Check if this recommendation is liked by a specific user"""
        if not user:
            return False
        return any(like.user_id == user.id for like in self.likes)
    
    def get_google_maps_link(self):
        """Generate a Google Maps link for the location"""
        if not self.location:
            return None
        import urllib.parse
        encoded_location = urllib.parse.quote(self.location)
        return f"https://www.google.com/maps/search/{encoded_location}"
    
    def get_tags(self):
        """Get tags as a simple list combining categories and collections"""
        if not self.tags:
            return []
        
        tags = []
        if 'categories' in self.tags:
            tags.extend(self.tags['categories'])
        if 'collections' in self.tags:
            tags.extend(self.tags['collections'])
        return tags
    
    def add_tag(self, tag_name, tag_type='collection'):
        """Add a tag to this recommendation"""
        if not self.tags:
            self.tags = {'categories': [], 'collections': []}
        
        tag_slug = slugify(tag_name)
        if tag_type == 'category':
            if tag_slug not in self.tags.get('categories', []):
                if 'categories' not in self.tags:
                    self.tags['categories'] = []
                self.tags['categories'].append(tag_slug)
        else:
            if tag_slug not in self.tags.get('collections', []):
                if 'collections' not in self.tags:
                    self.tags['collections'] = []
                self.tags['collections'].append(tag_slug)
        
        # Mark as modified for SQLAlchemy
        self.tags = self.tags.copy()
    
    def remove_tag(self, tag_name, tag_type=None):
        """Remove a tag from this recommendation"""
        if not self.tags:
            return
        
        tag_slug = slugify(tag_name)
        
        if tag_type == 'category' or tag_type is None:
            if 'categories' in self.tags and tag_slug in self.tags['categories']:
                self.tags['categories'].remove(tag_slug)
        
        if tag_type == 'collection' or tag_type is None:
            if 'collections' in self.tags and tag_slug in self.tags['collections']:
                self.tags['collections'].remove(tag_slug)
        
        # Mark as modified for SQLAlchemy
        self.tags = self.tags.copy()
    
    def has_tag(self, tag_name):
        """Check if recommendation has a specific tag"""
        if not self.tags:
            return False
        
        tag_slug = slugify(tag_name)
        return (tag_slug in self.tags.get('categories', []) or 
                tag_slug in self.tags.get('collections', []))
    
    def __repr__(self):
        return f'<Recommendation {self.title}>'

def slugify(text):
    """Convert text to URL-friendly slug"""
    if not text:
        return ""
    # Convert to lowercase and replace non-alphanumeric characters with hyphens
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', text.lower().strip())
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug[:50]  # Limit length

class Follow(db.Model):
    __tablename__ = 'follows'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    follower_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    followed_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    follower: Mapped["User"] = relationship("User", foreign_keys=[follower_id], back_populates="following")
    followed: Mapped["User"] = relationship("User", foreign_keys=[followed_id], back_populates="followers")
    
    # Unique constraint to prevent duplicate follows
    __table_args__ = (db.UniqueConstraint('follower_id', 'followed_id', name='unique_follow'),)
    
    def __repr__(self):
        return f'<Follow {self.follower_id} -> {self.followed_id}>'

class Like(db.Model):
    __tablename__ = 'likes'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    recommendation_id: Mapped[int] = mapped_column(Integer, ForeignKey('recommendations.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="likes")
    recommendation: Mapped["Recommendation"] = relationship("Recommendation", back_populates="likes")
    
    # Unique constraint to prevent duplicate likes
    __table_args__ = (db.UniqueConstraint('user_id', 'recommendation_id', name='unique_like'),)
    
    def __repr__(self):
        return f'<Like {self.user_id} -> {self.recommendation_id}>'

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    recommendation_id: Mapped[int] = mapped_column(Integer, ForeignKey('recommendations.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="comments")
    recommendation: Mapped["Recommendation"] = relationship("Recommendation", back_populates="comments")
    
    def __repr__(self):
        return f'<Comment {self.id} by {self.user_id} on {self.recommendation_id}>'
