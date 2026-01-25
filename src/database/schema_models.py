from enum import Enum

class NodeLabel(str, Enum):
    """
    Labels for Nodes in the Pre-Crime Knowledge Graph.
    """
    CITIZEN = "Citizen"
    LOCATION = "Location"
    VISION = "Vision"  # "Red Ball" generated node (optional, or represented by relationship)
    EVENT = "Event"    # Crime event

class RelationshipType(str, Enum):
    """
    Types of Relationships.
    """
    KNOWS = "KNOWS"                 # Social: Citizen -> Citizen
    WAS_AT = "WAS_AT"               # Movement: Citizen -> Location
    COMMITTED_CRIME = "COMMITTED_CRIME" # History: Citizen -> Location
    WILL_COMMIT = "WILL_COMMIT"     # Prediction: Citizen -> Location (The "Red Ball")

class NodeProperty(str, Enum):
    """
    Property keys for Nodes.
    """
    ID = "id"
    NAME = "name"
    RISK_BASE = "risk_base"
    STATUS = "status"
    TYPE = "type"
    SECURITY_LEVEL = "security_level"

class EdgeProperty(str, Enum):
    """
    Property keys for Relationships.
    """
    TIMESTAMP = "timestamp"
    DURATION = "duration_minutes"
    DATE = "date"
    TYPE = "type"
    SEVERITY = "severity"
    RISK_SCORE = "risk_score"
    COLOR = "color"
