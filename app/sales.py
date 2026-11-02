"""Safe SQL integration demo: fixed, parameterized SELECT queries only."""
from __future__ import annotations
import os
import sqlite3
from pathlib import Path

DEMO_ROWS = [
    ('2026-10-05', 'Gram Altın', 15, 6200),
    ('2026-10-10', 'Çeyrek Altın', 7, 10900),
    ('2026-10-19', 'Bilezik', 3, 98000),
    ('2026-11-01', 'Gram Altın', 12, 6500),
    ('2026-11-01', 'Çeyrek Altın', 5, 11200),
    ('2026-11-02', 'Bilezik', 2, 101000),
]


def db_path() -> Path:
    return Path(os.getenv('DEMO_DB_PATH', 'data/demo_sales.sqlite'))


def seed_demo_db(path: Path | None = None) -> Path:
    path = path or db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY, sale_date TEXT NOT NULL,
            product TEXT NOT NULL, quantity INTEGER NOT NULL, unit_price REAL NOT NULL
        )''')
        if conn.execute('SELECT COUNT(*) FROM sales').fetchone()[0] == 0:
            conn.executemany(
                'INSERT INTO sales (sale_date, product, quantity, unit_price) VALUES (?, ?, ?, ?)',
                DEMO_ROWS,
            )
    return path


def monthly_summary(month: str, path: Path | None = None) -> dict:
    path = path or db_path()
    if not path.exists():
        raise FileNotFoundError('Örnek veritabanı yok. Önce python -m app.seed çalıştırın.')
    with sqlite3.connect(f'file:{path.resolve().as_posix()}?mode=ro', uri=True) as conn:
        rows = conn.execute('''SELECT product, SUM(quantity), ROUND(SUM(quantity * unit_price), 2)
            FROM sales WHERE substr(sale_date, 1, 7) = ?
            GROUP BY product ORDER BY SUM(quantity * unit_price) DESC''', (month,)).fetchall()
    return {
        'month': month,
        'products': [{'product': name, 'quantity': count, 'revenue_try': revenue}
                     for name, count, revenue in rows],
        'total_revenue_try': round(sum(row[2] for row in rows), 2),
        'note': 'Yalnızca sentetik örnek veri; gerçek şirket satışları değildir.',
    }
