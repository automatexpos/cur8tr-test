"""
Tagging API routes for CUR8tr - Simple JSON-based tagging system
"""

from flask import Blueprint, request, jsonify, session
from functools import wraps
from sqlalchemy import and_, or_
from models import User, Profile, Recommendation, Category, slugify
from app import db
import json

bp = Blueprint("tagging", __name__, url_prefix="/api")

def login_required_api(f):
    """Decorator for API routes that require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current user from session"""
    if 'user_id' not in session:
        return None
    return User.query.get(session['user_id'])

@bp.route('/tags', methods=['GET'])
def get_all_tags():
    """Get all available tags from recommendations"""
    user_id = session.get('user_id')
    
    # Get tags from public recommendations or user's own recommendations
    if user_id:
        user = get_current_user()
        recommendations = db.session.query(Recommendation).join(Category).join(Profile).filter(
            or_(
                Profile.is_public == True,
                Profile.user_id == user_id
            )
        ).all()
    else:
        recommendations = db.session.query(Recommendation).join(Category).join(Profile).filter(
            Profile.is_public == True
        ).all()
    
    # Collect all unique tags
    categories = set()
    collections = set()
    
    for rec in recommendations:
        if rec.tags:
            if 'categories' in rec.tags:
                categories.update(rec.tags['categories'])
            if 'collections' in rec.tags:
                collections.update(rec.tags['collections'])
    
    return jsonify({
        'categories': sorted(list(categories)),
        'collections': sorted(list(collections))
    }), 200

@bp.route('/tags/categories', methods=['GET'])
def get_categories():
    """Get all category tags"""
    # Default categories
    default_categories = [
        'books', 'youtube-channels', 'food', 'where-to-stay', 'apps', 'products'
    ]
    
    # Get additional categories from recommendations
    user_id = session.get('user_id')
    if user_id:
        recommendations = db.session.query(Recommendation).join(Category).join(Profile).filter(
            or_(
                Profile.is_public == True,
                Profile.user_id == user_id
            )
        ).all()
    else:
        recommendations = db.session.query(Recommendation).join(Category).join(Profile).filter(
            Profile.is_public == True
        ).all()
    
    additional_categories = set()
    for rec in recommendations:
        if rec.tags and 'categories' in rec.tags:
            additional_categories.update(rec.tags['categories'])
    
    all_categories = set(default_categories)
    all_categories.update(additional_categories)
    
    return jsonify({
        'categories': [
            {
                'id': cat,
                'name': cat.replace('-', ' ').title(),
                'kind': 'category'
            }
            for cat in sorted(list(all_categories))
        ]
    }), 200

@bp.route('/tags/collections', methods=['GET'])
@login_required_api
def get_collections():
    """Get user's collection tags"""
    user = get_current_user()
    
    # Get collections from user's recommendations
    recommendations = db.session.query(Recommendation).join(Category).join(Profile).filter(
        Profile.user_id == user.id
    ).all()
    
    collections = set()
    for rec in recommendations:
        if rec.tags and 'collections' in rec.tags:
            collections.update(rec.tags['collections'])
    
    return jsonify({
        'collections': [
            {
                'id': col,
                'name': col.replace('-', ' ').title(),
                'kind': 'collection'
            }
            for col in sorted(list(collections))
        ]
    }), 200

@bp.route('/recommendations', methods=['GET'])
def get_recommendations_by_tags():
    """Get recommendations filtered by tags"""
    tags_param = request.args.get('tags', '')
    user_id = session.get('user_id')
    
    # Parse tags parameter
    if tags_param:
        tag_list = [tag.strip() for tag in tags_param.split(',') if tag.strip()]
    else:
        tag_list = []
    
    # Build query for public recommendations or user's own
    if user_id:
        query = db.session.query(Recommendation).join(Category).join(Profile).filter(
            or_(
                Profile.is_public == True,
                Profile.user_id == user_id
            )
        )
    else:
        query = db.session.query(Recommendation).join(Category).join(Profile).filter(
            Profile.is_public == True
        )
    
    # Filter by tags if provided
    if tag_list:
        # Create filter conditions for each tag
        conditions = []
        for tag in tag_list:
            tag_slug = slugify(tag)
            # Check if tag exists in either categories or collections
            conditions.append(
                or_(
                    Recommendation.tags.op('->>')('categories').like(f'%"{tag_slug}"%'),
                    Recommendation.tags.op('->>')('collections').like(f'%"{tag_slug}"%')
                )
            )
        
        # Apply AND logic (recommendation must have all specified tags)
        if conditions:
            query = query.filter(and_(*conditions))
    
    recommendations = query.order_by(Recommendation.created_at.desc()).limit(50).all()
    
    # Convert to dict
    rec_list = []
    for rec in recommendations:
        rec_dict = {
            'id': rec.id,
            'title': rec.title,
            'description': rec.description,
            'url': rec.url,
            'image': rec.image,
            'rating': rec.rating,
            'cost_rating': rec.cost_rating,
            'location': rec.location,
            'tags': rec.get_tags(),
            'created_at': rec.created_at.isoformat() if rec.created_at else None,
            'category': {
                'id': rec.category.id,
                'name': rec.category.name,
                'slug': rec.category.slug
            } if rec.category else None,
            'profile': {
                'id': rec.category.profile.id,
                'name': rec.category.profile.name,
                'slug': rec.category.profile.slug
            } if rec.category and rec.category.profile else None
        }
        rec_list.append(rec_dict)
    
    return jsonify(rec_list), 200

@bp.route('/recommendations/<int:rec_id>/tags', methods=['POST'])
@login_required_api
def add_tag_to_recommendation(rec_id):
    """Add a tag to a recommendation"""
    rec = Recommendation.query.get(rec_id)
    if not rec:
        return jsonify({"error": "Recommendation not found"}), 404
    
    user = get_current_user()
    if rec.category.profile.user_id != user.id:
        return jsonify({"error": "You can only edit your own recommendations"}), 403
    
    data = request.get_json()
    if not data or 'tag' not in data:
        return jsonify({"error": "Tag name required"}), 400
    
    tag_name = data['tag'].strip()
    tag_type = data.get('type', 'collection')  # 'category' or 'collection'
    
    if not tag_name:
        return jsonify({"error": "Tag name cannot be empty"}), 400
    
    rec.add_tag(tag_name, tag_type)
    db.session.commit()
    
    return jsonify({
        'id': rec.id,
        'tags': rec.get_tags(),
        'message': f'Tag "{tag_name}" added successfully'
    }), 200

@bp.route('/recommendations/<int:rec_id>/tags', methods=['DELETE'])
@login_required_api
def remove_tag_from_recommendation(rec_id):
    """Remove a tag from a recommendation"""
    rec = Recommendation.query.get(rec_id)
    if not rec:
        return jsonify({"error": "Recommendation not found"}), 404
    
    user = get_current_user()
    if rec.category.profile.user_id != user.id:
        return jsonify({"error": "You can only edit your own recommendations"}), 403
    
    data = request.get_json()
    if not data or 'tag' not in data:
        return jsonify({"error": "Tag name required"}), 400
    
    tag_name = data['tag'].strip()
    tag_type = data.get('type')  # Optional: 'category' or 'collection'
    
    rec.remove_tag(tag_name, tag_type)
    db.session.commit()
    
    return jsonify({
        'id': rec.id,
        'tags': rec.get_tags(),
        'message': f'Tag "{tag_name}" removed successfully'
    }), 200

@bp.route('/recommendations/<int:rec_id>/tags', methods=['PUT'])
@login_required_api
def set_recommendation_tags(rec_id):
    """Set all tags for a recommendation (replaces existing)"""
    rec = Recommendation.query.get(rec_id)
    if not rec:
        return jsonify({"error": "Recommendation not found"}), 404
    
    user = get_current_user()
    if rec.category.profile.user_id != user.id:
        return jsonify({"error": "You can only edit your own recommendations"}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON data required"}), 400
    
    categories = data.get('categories', [])
    collections = data.get('collections', [])
    
    # Create new tags structure
    new_tags = {}
    if categories:
        new_tags['categories'] = [slugify(cat) for cat in categories if cat.strip()]
    if collections:
        new_tags['collections'] = [slugify(col) for col in collections if col.strip()]
    
    rec.tags = new_tags if new_tags else None
    db.session.commit()
    
    return jsonify({
        'id': rec.id,
        'tags': rec.get_tags(),
        'message': 'Tags updated successfully'
    }), 200