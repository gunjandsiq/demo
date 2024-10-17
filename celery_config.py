from celery import Celery
from config import environment
import psycopg2
from psycopg2 import sql

env = environment['server']
celery = Celery(__name__, broker=env['celery-broker'])

db = env['db'].split('?')[0]

def create_schema():
    try:
        conn = psycopg2.connect(db)
        # Create a cursor object
        cur = conn.cursor()
    
        # Define the schema name
        schema_name = 'timechronos'
    
        # Create the schema using a SQL command
        cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema_name)))
    
        # Commit the changes
        conn.commit()
    
        # Close the cursor and connection    
        cur.close()
        conn.close()
    
        print(f"Schema '{schema_name}' created successfully.")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error creating schema: {error}")
