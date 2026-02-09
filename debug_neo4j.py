
import os
import sys
from neo4j import GraphDatabase

# URIs to test
uris = [
    "bolt://127.0.0.1:7687",
    "neo4j://127.0.0.1:7687",
    "bolt://localhost:7687"
]

auth = ("neo4j", "secret_password_123")

print("--- Testing Neo4j Connectivity ---")
print(f"Driver version: {GraphDatabase.__module__}")

for uri in uris:
    print(f"\nTesting URI: {uri}")
    try:
        # Try with default settings
        with GraphDatabase.driver(uri, auth=auth) as driver:
            try:
                driver.verify_connectivity()
                print(f"SUCCESS: Connected to {uri}")
            except Exception as e:
                print(f"FAILED verify_connectivity: {e}")
                
                # Try creating a session anyway
                try:
                    with driver.session() as session:
                        res = session.run("RETURN 1").single()
                        print(f"SUCCESS: Query returned {res[0]}")
                except Exception as e2:
                    print(f"FAILED session run: {e2}")

    except Exception as e:
        print(f"FAILED to update driver: {e}")

print("\n--- End of Test ---")
