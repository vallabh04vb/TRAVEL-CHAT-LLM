from neo4j import GraphDatabase

class MemoryAgent:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def store_preference(self, user_id, preference_type, preference_value):
        # Store a preference for a user in the graph database
        with self.driver.session() as session:
            query = """
            MERGE (u:User {userId: $user_id})
            MERGE (p:Preference {type: $preference_type, value: $preference_value})
            MERGE (u)-[:HAS_PREFERENCE]->(p)
            """
            session.run(query, user_id=user_id, preference_type=preference_type, preference_value=preference_value)

    def get_preferences(self, user_id):
        # Retrieve preferences for a user
        with self.driver.session() as session:
            query = """
            MATCH (u:User {userId: $user_id})-[:HAS_PREFERENCE]->(p:Preference)
            RETURN p.type AS type, p.value AS value
            """
            result = session.run(query, user_id=user_id)
            preferences = {record["type"]: record["value"] for record in result}
            return preferences

    def update_preference(self, user_id, preference_type, new_value):
        # Update a specific preference for a user
        with self.driver.session() as session:
            query = """
            MATCH (u:User {userId: $user_id})-[:HAS_PREFERENCE]->(p:Preference {type: $preference_type})
            SET p.value = $new_value
            """
            session.run(query, user_id=user_id, preference_type=preference_type, new_value=new_value)
