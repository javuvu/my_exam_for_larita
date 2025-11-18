import sqlite3

conn = sqlite3.connect("questions.db")
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE questions ADD COLUMN tags TEXT")
    print("Columna 'tags' añadida correctamente.")
except Exception as e:
    print("No se pudo añadir la columna (quizá ya existe):", e)

conn.commit()
conn.close()
