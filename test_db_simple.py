#!/usr/bin/env python3
"""
Simple database test to check if saving and retrieving works
"""

import sys
import os
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.database import db_manager
from app.schemas import FinalBrief, SourceSummary, SourceMetadata

def test_database():
    print("Testing database functionality...")
    
    # Create a simple test brief
    test_brief = FinalBrief(
        brief_id=f"test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        topic="Test Topic",
        summary="Test summary",
        key_findings=["Finding 1", "Finding 2"],
        methodology="Test methodology",
        sources=[],
        recommendations=["Rec 1", "Rec 2"],
        limitations=["Limit 1"],
        generated_at=datetime.utcnow(),
        execution_time=10.0,
        token_usage={"total": 100},
        cost_estimate=0.001
    )
    
    print(f"1. Saving test brief: {test_brief.brief_id}")
    try:
        db_manager.save_brief(test_brief, "test_user_123")
        print("   ✓ Brief saved successfully")
    except Exception as e:
        print(f"   ✗ Error saving brief: {e}")
        return False
    
    print("2. Retrieving user briefs...")
    try:
        briefs = db_manager.get_user_briefs("test_user_123")
        print(f"   ✓ Found {len(briefs)} briefs")
        if len(briefs) > 0:
            print(f"   ✓ First brief ID: {briefs[0].brief_id}")
            print(f"   ✓ First brief topic: {briefs[0].topic}")
        else:
            print("   ✗ No briefs found!")
            return False
    except Exception as e:
        print(f"   ✗ Error retrieving briefs: {e}")
        return False
    
    print("3. Database test completed successfully! ✓")
    return True

if __name__ == "__main__":
    test_database()