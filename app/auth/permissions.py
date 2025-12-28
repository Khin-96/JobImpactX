from enum import Enum
from typing import List
import logging

logger = logging.getLogger(__name__)

class Permission(str, Enum):
    ASSESS = "assess"
    EXPLAIN = "explain"
    SCENARIO = "scenario"
    AUDIT_VIEW = "audit_view"
    MANAGE_USERS = "manage_users"
    CONFIGURE_MODEL = "configure_model"

PERMISSION_MATRIX = {
    "Admin": [
        Permission.ASSESS,
        Permission.EXPLAIN,
        Permission.SCENARIO,
        Permission.AUDIT_VIEW,
        Permission.MANAGE_USERS,
        Permission.CONFIGURE_MODEL
    ],
    "Analyst": [
        Permission.ASSESS,
        Permission.EXPLAIN,
        Permission.SCENARIO,
        Permission.AUDIT_VIEW
    ],
    "Viewer": [
        Permission.EXPLAIN
    ]
}

def check_permission(user_role: str, required_permission: Permission) -> bool:
    """Check if user role has required permission."""
    permissions = PERMISSION_MATRIX.get(user_role, [])
    has_permission = required_permission in permissions
    
    if not has_permission:
        logger.warning(f"Access denied: role={user_role}, required_permission={required_permission}")
    
    return has_permission
