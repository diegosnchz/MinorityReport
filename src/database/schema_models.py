from enum import Enum

class NodeLabel(str, Enum):
    """
    Labels for Nodes in the Knowledge Graph.
    Ref: Section 1 & 4 of Technical Notes.
    """
    LOCATION = "Location"
    HIDEOUT = "Hideout"
    POLICE_STATION = "PoliceStation"
    USER = "User"

class RelationshipType(str, Enum):
    """
    Types of Relationships between Nodes.
    """
    CONNECTED_TO = "CONNECTED_TO"  # Bidirectional/Undirected concept (Street implementation)
    WATCHED_BY = "WATCHED_BY"      # Directed: PoliceStation -> Location
    HAS_TARGET = "HAS_TARGET"      # User -> Location (Goal)

class NodeProperty(str, Enum):
    """
    Property keys for Nodes.
    """
    ID = "uid"
    X = "x"
    Y = "y"
    TYPE = "type"
    CAPACITY = "capacity"
    NAME = "name"

class EdgeProperty(str, Enum):
    """
    Property keys for Relationships.
    """
    DISTANCE = "distance"
    RISK_LEVEL = "risk_level"  # Float 0.0 - 1.0
