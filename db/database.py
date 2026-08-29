import sqlite3
from pathlib import Path


# -------------------------------------------------
# DATABASE PATH
# -------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = (
    ROOT_DIR
    / "bookings.db"
)


# -------------------------------------------------
# GET DATABASE CONNECTION
# -------------------------------------------------

def get_connection():
    """
    Create and return a SQLite connection.
    """

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = (
        sqlite3.Row
    )

    return connection


# -------------------------------------------------
# INITIALIZE DATABASE
# -------------------------------------------------

def initialize_database():
    """
    Create the required database tables
    if they do not already exist.
    """

    connection = get_connection()

    cursor = connection.cursor()


    # =============================================
    # CUSTOMERS TABLE
    # =============================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (

            customer_id INTEGER
                PRIMARY KEY AUTOINCREMENT,

            name TEXT
                NOT NULL,

            email TEXT
                NOT NULL
                UNIQUE,

            phone TEXT
                NOT NULL

        )
        """
    )


    # =============================================
    # BOOKINGS TABLE
    # =============================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (

            id INTEGER
                PRIMARY KEY AUTOINCREMENT,

            customer_id INTEGER
                NOT NULL,

            booking_type TEXT
                NOT NULL,

            date TEXT
                NOT NULL,

            time TEXT
                NOT NULL,

            status TEXT
                NOT NULL
                DEFAULT 'Confirmed',

            created_at TEXT
                NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (customer_id)
                REFERENCES customers (
                    customer_id
                )

        )
        """
    )


    connection.commit()

    connection.close()


# -------------------------------------------------
# GET OR CREATE CUSTOMER
# -------------------------------------------------

def get_or_create_customer(
    cursor,
    booking,
):
    """
    Find an existing customer by email.

    If the customer does not exist,
    create a new customer.

    Returns:
        customer_id
    """

    cursor.execute(
        """
        SELECT customer_id
        FROM customers
        WHERE email = ?
        """,
        (
            booking["email"],
        ),
    )

    customer = cursor.fetchone()


    # ---------------------------------------------
    # EXISTING CUSTOMER
    # ---------------------------------------------

    if customer:

        customer_id = (
            customer["customer_id"]
        )

        # Update latest name and phone
        cursor.execute(
            """
            UPDATE customers
            SET
                name = ?,
                phone = ?
            WHERE customer_id = ?
            """,
            (
                booking["name"],
                booking["phone"],
                customer_id,
            ),
        )

        return customer_id


    # ---------------------------------------------
    # NEW CUSTOMER
    # ---------------------------------------------

    cursor.execute(
        """
        INSERT INTO customers (
            name,
            email,
            phone
        )
        VALUES (
            ?,
            ?,
            ?
        )
        """,
        (
            booking["name"],
            booking["email"],
            booking["phone"],
        ),
    )

    return cursor.lastrowid


# -------------------------------------------------
# SAVE BOOKING
# -------------------------------------------------

def save_booking(booking):
    """
    Save a confirmed booking.

    Steps:
    1. Get or create customer.
    2. Create booking linked to customer.
    3. Return booking ID.
    """

    connection = get_connection()

    cursor = connection.cursor()

    try:

        # -----------------------------------------
        # GET / CREATE CUSTOMER
        # -----------------------------------------

        customer_id = (
            get_or_create_customer(
                cursor,
                booking,
            )
        )


        # -----------------------------------------
        # CREATE BOOKING
        # -----------------------------------------

        cursor.execute(
            """
            INSERT INTO bookings (

                customer_id,
                booking_type,
                date,
                time,
                status

            )
            VALUES (
                ?,
                ?,
                ?,
                ?,
                ?
            )
            """,
            (
                customer_id,
                booking["booking_type"],
                booking["date"],
                booking["time"],
                "Confirmed",
            ),
        )


        booking_id = (
            cursor.lastrowid
        )


        # -----------------------------------------
        # COMMIT
        # -----------------------------------------

        connection.commit()

        return booking_id


    except Exception:

        # Undo incomplete transaction
        connection.rollback()

        raise


    finally:

        connection.close()


# -------------------------------------------------
# GET ALL BOOKINGS
# -------------------------------------------------

def get_all_bookings():
    """
    Return all bookings with their
    associated customer details.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT

            bookings.id,

            customers.name,
            customers.email,
            customers.phone,

            bookings.booking_type,
            bookings.date,
            bookings.time,
            bookings.status,
            bookings.created_at

        FROM bookings

        INNER JOIN customers

        ON bookings.customer_id
            =
            customers.customer_id

        ORDER BY
            bookings.created_at DESC
        """
    )

    bookings = (
        cursor.fetchall()
    )

    connection.close()

    return bookings


# -------------------------------------------------
# SEARCH BOOKINGS
# -------------------------------------------------

def search_bookings(search_term):
    """
    Search bookings using customer details
    or booking type.
    """

    connection = get_connection()

    cursor = connection.cursor()

    search_value = (
        f"%{search_term}%"
    )

    cursor.execute(
        """
        SELECT

            bookings.id,

            customers.name,
            customers.email,
            customers.phone,

            bookings.booking_type,
            bookings.date,
            bookings.time,
            bookings.status,
            bookings.created_at

        FROM bookings

        INNER JOIN customers

        ON bookings.customer_id
            =
            customers.customer_id

        WHERE

            customers.name LIKE ?

            OR customers.email LIKE ?

            OR customers.phone LIKE ?

            OR bookings.booking_type LIKE ?

        ORDER BY
            bookings.created_at DESC
        """,
        (
            search_value,
            search_value,
            search_value,
            search_value,
        ),
    )

    bookings = (
        cursor.fetchall()
    )

    connection.close()

    return bookings