#!/usr/bin/env python3
"""
Migration script to fix existing recommendations that have None for tags.
This should be run once to ensure all existing recommendations have proper tag structure.
"""

from app import app
from models import db, Recommendation

def fix_existing_tags():
    """Fix existing recommendations with None tags"""
    with app.app_context():
        # Find all recommendations where tags is None
        recommendations_with_none_tags = Recommendation.query.filter(
            Recommendation.tags.is_(None)
        ).all()
        
        print(f"Found {len(recommendations_with_none_tags)} recommendations with None tags")
        
        # Update each recommendation to have empty tags dictionary
        for rec in recommendations_with_none_tags:
            rec.tags = {}
            print(f"Fixed recommendation {rec.id}: '{rec.title}'")
        
        # Commit all changes
        db.session.commit()
        print(f"Successfully updated {len(recommendations_with_none_tags)} recommendations")

if __name__ == "__main__":
    print("Starting migration to fix existing tags...")
    fix_existing_tags()
    print("Migration completed!")