import psycopg2
import os

def get_db_connection():
    conn = psycopg2.connect(
        host="dpg-cv8oiprqf0us73bbbbfg-a.oregon-postgres.render.com",
        database="patrimonio_ppfk",
        user="patrimonio_ppfk_user",
        password="SabopRq1mqHqRXBZaZBaWsEcqfHYJWM2"
    )
    return conn
