"""Seed de datos de prueba para desarrollo local.

Uso:
    python scripts/seed.py

Crea usuarios (password: password123), posts de changas y perfiles de
changadores. Es idempotente: borra y recrea los datos de prueba.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

import bcrypt

DB_PATH = "changas.db"
PASSWORD = "password123"

NOW = datetime.now(timezone.utc).isoformat(sep=" ", timespec="seconds")


def main() -> None:
    pw_hash = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode()

    usuarios = [
        # (id, nombre, email, rol_actual, tags)
        ("cliente1", "Carlos Cliente", "cliente@test.com", "CLIENTE", ["plomeria", "electricidad"]),
        ("cliente2", "Clara Consumidora", "cliente2@test.com", "CLIENTE", ["gas"]),
        ("changador1", "Gabriel Gasista", "changador@test.com", "CHANGADOR", ["gas", "plomeria"]),
        ("changador2", "Pedro Plomero", "changador2@test.com", "CHANGADOR", ["plomeria"]),
    ]

    posts = [
        # (id, titulo, descripcion_corta, tags, barrio, user_id)
        ("post1", "Arreglar canilla que pierde", "Canilla de cocina gotea hace una semana", ["plomeria"], "Palermo", "cliente1"),
        ("post2", "Instalar estufa a gas", "Estufa nueva, necesita conexion y prueba", ["gas"], "Caballito", "cliente1"),
        ("post3", "Revisar perdida de gas", "Olor a gas en el lavadero", ["gas"], "Flores", "cliente2"),
    ]

    perfiles = [
        # (id, nombre, especialidades, user_id)
        ("perfil1", "Gabriel Gasista", ["gas", "plomeria"], "changador1"),
        ("perfil2", "Pedro Plomero", ["plomeria"], "changador2"),
    ]

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    seed_user_ids = [u[0] for u in usuarios]
    marks = ",".join("?" * len(seed_user_ids))
    cur.execute(f"DELETE FROM swipes WHERE user_id IN ({marks})", seed_user_ids)
    cur.execute(f"DELETE FROM cotizaciones WHERE creado_por_id IN ({marks})", seed_user_ids)
    cur.execute(f"DELETE FROM mensajes WHERE autor_id IN ({marks})", seed_user_ids)
    cur.execute(f"DELETE FROM matches WHERE user_a_id IN ({marks}) OR user_b_id IN ({marks})", seed_user_ids * 2)
    cur.execute(f"DELETE FROM changas_posts WHERE user_id IN ({marks})", seed_user_ids)
    cur.execute(f"DELETE FROM changadores_perfiles WHERE user_id IN ({marks})", seed_user_ids)
    cur.execute(f"DELETE FROM usuarios WHERE id IN ({marks})", seed_user_ids)

    for uid, nombre, email, rol, tags in usuarios:
        cur.execute(
            "INSERT INTO usuarios (id, nombre, email, password_hash, google_id, rol_actual, tags, created_at)"
            " VALUES (?, ?, ?, ?, NULL, ?, ?, ?)",
            (uid, nombre, email, pw_hash, rol, json.dumps(tags), NOW),
        )

    for pid, titulo, desc, tags, barrio, uid in posts:
        cur.execute(
            "INSERT INTO changas_posts (id, titulo, descripcion_corta, fotos, tags, barrio, user_id, created_at)"
            " VALUES (?, ?, ?, '[]', ?, ?, ?, ?)",
            (pid, titulo, desc, json.dumps(tags), barrio, uid, NOW),
        )

    for prid, nombre, esp, uid in perfiles:
        cur.execute(
            "INSERT INTO changadores_perfiles (id, nombre, fotos_trabajos, especialidades, user_id, created_at)"
            " VALUES (?, ?, '[]', ?, ?, ?)",
            (prid, nombre, json.dumps(esp), uid, NOW),
        )

    con.commit()
    con.close()

    print(f"Seed OK — {len(usuarios)} usuarios, {len(posts)} posts, {len(perfiles)} perfiles.")
    print(f"Password de todos los usuarios: {PASSWORD}")


if __name__ == "__main__":
    main()
