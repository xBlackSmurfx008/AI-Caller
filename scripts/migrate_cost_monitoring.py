"""Database migration script for cost monitoring tables

This script creates the cost monitoring tables if they don't exist.
Run this before deploying the cost monitoring feature.

Usage:
    python scripts/migrate_cost_monitoring.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.database import init_db, engine
from src.database.models import (
    PricingRule, CostEvent, TaskCostEstimate, TaskCostActual, Budget, CostAlert
)
from sqlalchemy import inspect
from src.utils.logging import get_logger

logger = get_logger(__name__)


def check_table_exists(table_name: str) -> bool:
    """Check if a table exists in the database"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def migrate():
    """Create cost monitoring tables if they don't exist"""
    logger.info("Starting cost monitoring migration...")
    
    # Check which tables exist
    tables_to_create = []
    tables = {
        'pricing_rules': PricingRule,
        'cost_events': CostEvent,
        'task_cost_estimates': TaskCostEstimate,
        'task_cost_actuals': TaskCostActual,
        'budgets': Budget,
        'cost_alerts': CostAlert
    }
    
    for table_name, model in tables.items():
        if not check_table_exists(table_name):
            tables_to_create.append(table_name)
            logger.info(f"Table {table_name} does not exist, will be created")
        else:
            logger.info(f"Table {table_name} already exists, skipping")
    
    if not tables_to_create:
        logger.info("All cost monitoring tables already exist. Migration complete.")
        return
    
    # Create tables
    try:
        logger.info(f"Creating {len(tables_to_create)} new table(s)...")
        init_db()
        logger.info("✅ Migration completed successfully!")
        
        # Verify tables were created
        for table_name in tables_to_create:
            if check_table_exists(table_name):
                logger.info(f"✅ Verified: {table_name} created")
            else:
                logger.error(f"❌ ERROR: {table_name} was not created")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)

