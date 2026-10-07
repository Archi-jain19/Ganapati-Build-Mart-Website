import os
import shutil
import sqlite3
import mysql.connector
from mysql.connector import Error as MySQLError
from werkzeug.security import generate_password_hash

IS_VERCEL = bool(os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if IS_VERCEL:
    DB_PATH = '/tmp/ganapati.db'
    packaged_db = os.path.join(BASE_DIR, 'ganapati.db')
    if not os.path.exists(DB_PATH) and os.path.exists(packaged_db):
        try:
            shutil.copy2(packaged_db, DB_PATH)
        except Exception:
            pass
else:
    DB_PATH = os.path.join(BASE_DIR, 'ganapati.db')

# MySQL connection settings (can be customized via environment variables)
MYSQL_CONFIG = {
    'host': os.environ.get('DB_HOST', '148.113.4.193'),
    'user': os.environ.get('DB_USER', 'gbmartin_root'),
    'password': os.environ.get('DB_PASSWORD', 'aakash@1609'),
    'database': os.environ.get('DB_NAME', 'gbmartin_product_db'),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'connection_timeout': int(os.environ.get('DB_TIMEOUT', 2))
}

USE_SQLITE = os.environ.get('USE_SQLITE', '').lower() in ('1', 'true', 'yes')


class SQLiteCursorAdapter:
    def __init__(self, cursor, dictionary=False):
        self._cursor = cursor
        self._dictionary = dictionary

    def execute(self, query, params=None):
        sqlite_query = query.replace('%s', '?')
        if params is not None and len(params) > 0:
            if isinstance(params, (list, tuple)):
                return self._cursor.execute(sqlite_query, params)
            return self._cursor.execute(sqlite_query, (params,))
        return self._cursor.execute(sqlite_query)

    def executemany(self, query, seq_of_params):
        sqlite_query = query.replace('%s', '?')
        return self._cursor.executemany(sqlite_query, seq_of_params)

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        if self._dictionary:
            return dict(row)
        return row

    def fetchall(self):
        rows = self._cursor.fetchall()
        if self._dictionary:
            return [dict(r) for r in rows]
        return rows

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    def close(self):
        try:
            self._cursor.close()
        except Exception:
            pass


class SQLiteConnectionAdapter:
    def __init__(self, conn):
        self._conn = conn
        self._is_connected = True

    def cursor(self, dictionary=False):
        if dictionary:
            self._conn.row_factory = sqlite3.Row
        else:
            self._conn.row_factory = None
        cur = self._conn.cursor()
        return SQLiteCursorAdapter(cur, dictionary=dictionary)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._is_connected = False
        try:
            self._conn.close()
        except Exception:
            pass

    def is_connected(self):
        return self._is_connected


def init_sqlite_db(target_path=None):
    db_file = target_path or DB_PATH
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            brand TEXT,
            description TEXT,
            image_url TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS contact_inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            subject TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Seed brands if empty
    cur.execute("SELECT COUNT(*) FROM brands")
    if cur.fetchone()[0] == 0:
        sample_brands = [
            ('Advance Decorative Laminates', 'advance.svg'),
            ('CenturyPly', 'century.svg'),
            ('Chroma', 'chroma.svg'),
            ('Duro Plywood', 'duro.svg'),
            ('Godrej Architectural', 'godrej.svg'),
            ('Greenlam Laminates', 'greenlam.svg'),
            ('Greenply Plywood', 'greenply.svg'),
            ('Häfele Hardware', 'hafele.svg'),
            ('Hettich Fittings', 'hettich.svg'),
            ('Ivas Modular', 'ivas.svg'),
            ('Merino Laminates', 'merino.svg'),
            ('Virgo Panels', 'virgo.svg')
        ]
        cur.executemany("INSERT INTO brands (name, url) VALUES (?, ?)", sample_brands)

    # Seed users if empty
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        admin_pass = generate_password_hash('admin123')
        cur.execute("INSERT INTO users (username, password, name) VALUES (?, ?, ?)",
                    ('admin', admin_pass, 'Administrator'))
        cur.execute("INSERT INTO users (username, password, name) VALUES (?, ?, ?)",
                    ('admin@gbmart.in', admin_pass, 'Ganapati Admin'))

    # Seed products if empty
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        sample_products = [
            (
                'Greenply Club 700 Plywood',
                'Plywood',
                'Greenply',
                'Premium fire-retardant structural grade plywood engineered with unextended BWP resin for heavy-duty applications.',
                'https://www.greenply.com:5001/originalthumbnail1726826783158-7331.jpg'
            ),
            (
                'Greenply Club 500 Plywood',
                'Plywood',
                'Greenply',
                'Calibrated marine grade BWR plywood with 100% core composure and anti-termite treatment.',
                'https://www.greenply.com:5001/thumbnail1710915299824-5828.jpg'
            ),
            (
                'Greenply Platinum Plywood',
                'Plywood',
                'Greenply',
                'Flagship 2x fire-retardant structural hardwood plywood with lifetime warranty against borers.',
                'https://www.greenply.com:5001/thumbnail1710915962554-9648.jpg'
            ),
            (
                'Century Club Prime Plywood',
                'Plywood',
                'CenturyPly',
                'Waterproof marine ply powered by ViroKill technology and 25-year borer and termite resistance warranty.',
                'https://images.unsplash.com/photo-1546484396-fb3fc6f95f98?auto=format&fit=crop&w=600&q=80'
            ),
            (
                'Greenlam Wool Textured Laminate',
                'Laminates',
                'Greenlam',
                '1.5mm high-pressure designer decorative laminate with ultra-matte wool finish and anti-scratch coating.',
                'https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?auto=format&fit=crop&w=600&q=80'
            ),
            (
                'Greenlam Charcoal Suede Laminate',
                'Laminates',
                'Greenlam',
                'Contemporary deep charcoal suede architectural surface laminate for luxury modular interiors.',
                'https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=600&q=80'
            ),
            (
                'Merino Matt Natural Woodgrain Laminate',
                'Laminates',
                'Merino',
                'Specialized antibacterial and antifungal decorative sheet featuring realistic Nordic oak textures.',
                'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&w=600&q=80'
            ),
            (
                'Hettich Sensys Soft-Close Hinge',
                'Hardware',
                'Hettich',
                'Concealed European cabinet hinge with integrated Silent System cushioning and wide angle opening.',
                'https://images.unsplash.com/photo-1581291518857-4e27b48ff24e?auto=format&fit=crop&w=600&q=80'
            ),
            (
                'Häfele Matrix Box Drawer System',
                'Hardware',
                'Häfele',
                'Heavy load bearing double-walled drawer runner system with synchronized feather-light glide.',
                'https://images.unsplash.com/photo-1558997519-83ea9252edf8?auto=format&fit=crop&w=600&q=80'
            ),
            (
                'Godrej High-Security Mortise Door Lock',
                'Hardware',
                'Godrej',
                'Brass deadbolt architectural mortise handle set engineered for exterior main entry security.',
                'https://images.unsplash.com/photo-1558002038-1055907df827?auto=format&fit=crop&w=600&q=80'
            ),
            (
                'Century Natural Teak Veneer Sheet',
                'Veneer',
                'CenturyPly',
                'Natural handcrafted burr teak architectural timber surface slicing for luxury paneling and furniture.',
                'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=600&q=80'
            ),
            (
                'Duro Natural Smoked Oak Veneer',
                'Veneer',
                'Duro',
                'Double-pressed real FSC wood veneer featuring exotic European smoked dark oak grain patterns.',
                'https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?auto=format&fit=crop&w=600&q=80'
            )
        ]
        cur.executemany('''
            INSERT INTO products (product_name, category, brand, description, image_url)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_products)

    conn.commit()
    conn.close()


init_sqlite_db()

_mysql_available = None

def check_mysql_connection():
    global _mysql_available
    if _mysql_available is not None:
        return _mysql_available
    if USE_SQLITE:
        _mysql_available = False
        return False
    # If on Vercel and DB_HOST is still the unreachable default, skip slow network timeout
    if IS_VERCEL and MYSQL_CONFIG['host'] == '148.113.4.193':
        _mysql_available = False
        return False
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        if conn.is_connected():
            conn.close()
            _mysql_available = True
            return True
    except Exception:
        _mysql_available = False
        return False
    _mysql_available = False
    return False

def get_connection():
    """
    Returns an active database connection.
    Attempts MySQL if configured and available; otherwise uses local/serverless SQLite.
    """
    if check_mysql_connection():
        try:
            return mysql.connector.connect(**MYSQL_CONFIG)
        except Exception:
            pass
    conn = sqlite3.connect(DB_PATH)
    return SQLiteConnectionAdapter(conn)
