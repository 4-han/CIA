import psycopg2
import psycopg2.extras
import uuid
from datetime import datetime
import logging

from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


logging.info(f"DB Config Loaded: HOST={DB_HOST}, PORT={DB_PORT}, NAME={DB_NAME}, USER={DB_USER}") 

def connect_db():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        psycopg2.extras.register_uuid()
        logging.info("Database connection successful.")
        return conn
    except psycopg2.OperationalError as e:
        logging.error(f"Database connection failed using host '{DB_HOST}': {e}") 
        
        raise e
    except Exception as e:
        logging.error(f"An unexpected error occurred during database connection: {e}")
        raise e


def create_interactions_table(conn):
    """Creates the rag_interactions table if it doesn't exist."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS rag_interactions (
                    id UUID PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    username VARCHAR(255),
                    query TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    feedback VARCHAR(10), -- 'up', 'down', or NULL
                    message_id BIGINT -- Telegram message ID for linking feedback
                );
            """)
        conn.commit()
        logging.info("rag_interactions table checked/created successfully.")
    except psycopg2.Error as e:
        conn.rollback()
        logging.error(f"Error creating rag_interactions table: {e}")
        raise e

def insert_interaction(conn, user_id, query, answer, message_id=None, username=None):
    """Inserts a new RAG interaction record into the database."""
    interaction_id = uuid.uuid4()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO rag_interactions (id, user_id, username, query, answer, message_id)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (interaction_id, user_id, username, query, answer, message_id))
        conn.commit()
        logging.info(f"Interaction recorded: {interaction_id}")
        return interaction_id # Return the generated ID
    except psycopg2.Error as e:
        conn.rollback()
        logging.error(f"Error inserting interaction: {e}")
        raise e

def update_feedback(conn, interaction_id, feedback):
    """Updates the feedback for a specific interaction."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE rag_interactions
                SET feedback = %s
                WHERE id = %s;
            """, (feedback, interaction_id))
        conn.commit()
        logging.info(f"Feedback '{feedback}' recorded for interaction {interaction_id}")
    except psycopg2.Error as e:
        conn.rollback()
        logging.error(f"Error updating feedback for interaction {interaction_id}: {e}")
        raise e


if __name__ == "__main__":
    try:
        db_connection = connect_db()
        if db_connection:
            create_interactions_table(db_connection)
            db_connection.close()
    except Exception as e:
        logging.error(f"An error occurred during database script execution: {e}")