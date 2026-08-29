import sqlite3
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = ROOT_DIR / "bookings.db"


REQUIRED_BOOKING_COLUMNS = {
    "booking_type": "TEXT NOT NULL DEFAULT 'Restaurant Table Reservation'",
    "date": "TEXT NOT NULL DEFAULT ''",
    "time": "TEXT NOT NULL DEFAULT ''",
    "status": "TEXT NOT NULL DEFAULT 'Confirmed'",
    "created_at": "TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
    "number_of_guests": "INTEGER",
    "occasion": "TEXT",
    "dietary_requirements": "TEXT",
    "special_requests": "TEXT",
}


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def _existing_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            booking_type TEXT NOT NULL DEFAULT 'Restaurant Table Reservation',
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Confirmed',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            number_of_guests INTEGER,
            occasion TEXT,
            dietary_requirements TEXT,
            special_requests TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
        """
    )

    existing = _existing_columns(cursor, "bookings")
    for column, definition in REQUIRED_BOOKING_COLUMNS.items():
        if column not in existing:
            cursor.execute(f"ALTER TABLE bookings ADD COLUMN {column} {definition}")

    connection.commit()
    connection.close()


def get_or_create_customer(cursor, booking):
    cursor.execute(
        "SELECT customer_id FROM customers WHERE email = ?",
        (booking["email"],),
    )
    customer = cursor.fetchone()

    if customer:
        customer_id = customer["customer_id"]
        cursor.execute(
            """
            UPDATE customers
            SET name = ?, phone = ?
            WHERE customer_id = ?
            """,
            (booking["name"], booking["phone"], customer_id),
        )
        return customer_id

    cursor.execute(
        """
        INSERT INTO customers (name, email, phone)
        VALUES (?, ?, ?)
        """,
        (booking["name"], booking["email"], booking["phone"]),
    )
    return cursor.lastrowid


def save_booking(booking):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        customer_id = get_or_create_customer(cursor, booking)

        cursor.execute(
            """
            INSERT INTO bookings (
                customer_id,
                booking_type,
                date,
                time,
                status,
                number_of_guests,
                occasion,
                dietary_requirements,
                special_requests
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                customer_id,
                booking.get("booking_type", "Restaurant Table Reservation"),
                booking["date"],
                booking["time"],
                "Confirmed",
                booking.get("number_of_guests"),
                booking.get("occasion"),
                booking.get("dietary_requirements"),
                booking.get("special_requests"),
            ),
        )

        booking_id = cursor.lastrowid
        connection.commit()
        return booking_id

    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _booking_select_query(where_clause="", params=()):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        f"""
        SELECT
            bookings.id,
            customers.customer_id,
            customers.name,
            customers.email,
            customers.phone,
            bookings.booking_type,
            bookings.number_of_guests,
            bookings.date,
            bookings.time,
            bookings.occasion,
            bookings.dietary_requirements,
            bookings.special_requests,
            bookings.status,
            bookings.created_at
        FROM bookings
        INNER JOIN customers
            ON bookings.customer_id = customers.customer_id
        {where_clause}
        ORDER BY bookings.created_at DESC
        """,
        params,
    )
    rows = cursor.fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_all_bookings():
    return _booking_select_query()


def get_booking_by_id(booking_id):
    rows = _booking_select_query("WHERE bookings.id = ?", (booking_id,))
    return rows[0] if rows else None


def get_bookings_by_contact(email=None, phone=None):
    email = (email or "").strip()
    phone = (phone or "").strip()

    if not email and not phone:
        return []

    conditions = []
    params = []

    if email:
        conditions.append("LOWER(customers.email) = LOWER(?)")
        params.append(email)

    if phone:
        conditions.append("customers.phone = ?")
        params.append(phone)

    where_clause = "WHERE " + " OR ".join(conditions)
    return _booking_select_query(where_clause, tuple(params))


def search_bookings(search_term):
    value = f"%{search_term}%"
    return _booking_select_query(
        """
        WHERE customers.name LIKE ?
           OR customers.email LIKE ?
           OR customers.phone LIKE ?
           OR bookings.booking_type LIKE ?
           OR bookings.occasion LIKE ?
           OR bookings.special_requests LIKE ?
           OR bookings.dietary_requirements LIKE ?
        """,
        (value, value, value, value, value, value, value),
    )


def update_booking(booking_id, updates):
    allowed_booking_fields = {
        "date",
        "time",
        "number_of_guests",
        "occasion",
        "dietary_requirements",
        "special_requests",
        "status",
    }
    allowed_customer_fields = {"name", "email", "phone"}

    booking_updates = {
        key: value
        for key, value in updates.items()
        if key in allowed_booking_fields
    }
    customer_updates = {
        key: value
        for key, value in updates.items()
        if key in allowed_customer_fields
    }

    if not booking_updates and not customer_updates:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "SELECT customer_id FROM bookings WHERE id = ?",
            (booking_id,),
        )
        row = cursor.fetchone()
        if not row:
            return False

        customer_id = row["customer_id"]

        if booking_updates:
            assignments = ", ".join(f"{key} = ?" for key in booking_updates)
            values = list(booking_updates.values()) + [booking_id]
            cursor.execute(
                f"UPDATE bookings SET {assignments} WHERE id = ?",
                values,
            )

        if customer_updates:
            assignments = ", ".join(f"{key} = ?" for key in customer_updates)
            values = list(customer_updates.values()) + [customer_id]
            cursor.execute(
                f"UPDATE customers SET {assignments} WHERE customer_id = ?",
                values,
            )

        connection.commit()
        return True

    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def cancel_booking(booking_id):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "UPDATE bookings SET status = 'Cancelled' WHERE id = ?",
            (booking_id,),
        )
        changed = cursor.rowcount > 0
        connection.commit()
        return changed
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
