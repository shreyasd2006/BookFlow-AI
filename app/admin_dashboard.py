import streamlit as st
import pandas as pd

from db.database import get_all_bookings


# =================================================
# ADMIN DASHBOARD
# =================================================

def show_admin_dashboard():

    try:

        # ---------------------------------------------
        # LOAD BOOKINGS
        # ---------------------------------------------

        bookings = get_all_bookings()


        # ---------------------------------------------
        # EMPTY STATE
        # ---------------------------------------------

        if not bookings:

            with st.container(border=True):

                st.markdown("## 📭 No bookings yet")

                st.caption(
                    "Customer bookings will appear here "
                    "after they are confirmed."
                )

            return


        # ---------------------------------------------
        # CREATE DATAFRAME
        # ---------------------------------------------

        df = pd.DataFrame(
            bookings
        )


        # ---------------------------------------------
        # CONVERT CREATED AT
        # ---------------------------------------------

        if "created_at" in df.columns:

            df["created_at"] = pd.to_datetime(
                df["created_at"],
                errors="coerce",
            )


        # =================================================
        # OVERVIEW
        # =================================================

        st.subheader(
            "📊 Booking Overview"
        )


        total_bookings = len(df)


        # ---------------------------------------------
        # UNIQUE CUSTOMERS
        # ---------------------------------------------

        if "email" in df.columns:

            total_customers = (
                df["email"]
                .astype(str)
                .nunique()
            )

        else:

            total_customers = 0


        # ---------------------------------------------
        # CONFIRMED BOOKINGS
        # ---------------------------------------------

        if "status" in df.columns:

            confirmed_bookings = len(

                df[
                    df["status"]
                    .astype(str)
                    .str.lower()
                    ==
                    "confirmed"
                ]

            )

        else:

            confirmed_bookings = total_bookings


        # ---------------------------------------------
        # TODAY'S BOOKINGS
        # ---------------------------------------------

        today_bookings = 0


        date_column = None


        for possible_column in [
            "date",
            "booking_date",
        ]:

            if possible_column in df.columns:

                date_column = possible_column

                break


        if date_column:

            today_string = (
                pd.Timestamp.today()
                .strftime("%Y-%m-%d")
            )


            today_bookings = len(

                df[
                    df[date_column]
                    .astype(str)
                    .str.startswith(
                        today_string,
                        na=False,
                    )
                ]

            )


        # ---------------------------------------------
        # METRIC CARDS
        # ---------------------------------------------

        col1, col2, col3, col4 = (
            st.columns(4)
        )


        with col1:

            st.metric(
                "📅 Total Bookings",
                total_bookings,
            )


        with col2:

            st.metric(
                "👥 Customers",
                total_customers,
            )


        with col3:

            st.metric(
                "✅ Confirmed",
                confirmed_bookings,
            )


        with col4:

            st.metric(
                "📍 Today",
                today_bookings,
            )


        st.divider()


        # =================================================
        # SEARCH
        # =================================================

        st.subheader(
            "🔎 Find Bookings"
        )


        search_query = st.text_input(
            "Search bookings",
            placeholder=(
                "Search by name, email, phone, "
                "or booking type..."
            ),
        )


        filtered_df = df.copy()


        if search_query:

            search_value = (
                search_query
                .strip()
                .lower()
            )


            searchable_columns = [

                "name",

                "email",

                "phone",

                "booking_type",

                "service",

            ]


            mask = pd.Series(
                False,
                index=filtered_df.index,
            )


            for column in searchable_columns:

                if column in filtered_df.columns:

                    mask = (

                        mask

                        |

                        filtered_df[column]
                        .astype(str)
                        .str.lower()
                        .str.contains(
                            search_value,
                            na=False,
                        )

                    )


            filtered_df = (
                filtered_df[mask]
            )


        # =================================================
        # DATE FILTER
        # =================================================

        if date_column:

            selected_date = st.date_input(
                "Filter by booking date",
                value=None,
            )


            if selected_date:

                selected_date_string = (
                    selected_date.strftime(
                        "%Y-%m-%d"
                    )
                )


                filtered_df = (

                    filtered_df[

                        filtered_df[date_column]
                        .astype(str)
                        .str.startswith(
                            selected_date_string,
                            na=False,
                        )

                    ]

                )


        # =================================================
        # BOOKING RECORDS
        # =================================================

        st.divider()


        records_col, count_col = (
            st.columns([5, 1])
        )


        with records_col:

            st.subheader(
                "📋 Booking Records"
            )


        with count_col:

            st.metric(
                "Results",
                len(filtered_df),
            )


        # ---------------------------------------------
        # EMPTY FILTER RESULT
        # ---------------------------------------------

        if filtered_df.empty:

            st.info(
                "No bookings match your search or filters."
            )

            return


        # ---------------------------------------------
        # DISPLAY COPY
        # ---------------------------------------------

        display_df = (
            filtered_df.copy()
        )


        # ---------------------------------------------
        # FORMAT TIMESTAMP
        # ---------------------------------------------

        if "created_at" in display_df.columns:

            display_df["created_at"] = (

                pd.to_datetime(
                    display_df["created_at"],
                    errors="coerce",
                )

                .dt.strftime(
                    "%d %b %Y, %I:%M %p"
                )

                .fillna("")

            )


        # ---------------------------------------------
        # FRIENDLY COLUMN NAMES
        # ---------------------------------------------

        column_names = {

            "id": "Booking ID",

            "booking_id": "Booking ID",

            "name": "Customer",

            "email": "Email",

            "phone": "Phone",

            "booking_type": "Booking Type",

            "service": "Service",

            "date": "Date",

            "booking_date": "Date",

            "time": "Time",

            "booking_time": "Time",

            "status": "Status",

            "created_at": "Created",

        }


        display_df = display_df.rename(
            columns=column_names
        )


        # ---------------------------------------------
        # ORDER IMPORTANT COLUMNS
        # ---------------------------------------------

        preferred_columns = [

            "Booking ID",

            "Customer",

            "Email",

            "Phone",

            "Booking Type",

            "Service",

            "Date",

            "Time",

            "Status",

            "Created",

        ]


        available_columns = [

            column

            for column
            in preferred_columns

            if column
            in display_df.columns

        ]


        # Include unexpected database columns too

        remaining_columns = [

            column

            for column
            in display_df.columns

            if column
            not in available_columns

        ]


        display_columns = (
            available_columns
            +
            remaining_columns
        )


        display_df = (
            display_df[
                display_columns
            ]
        )


        # =================================================
        # DISPLAY TABLE
        # =================================================

        st.dataframe(
            display_df,
            width="stretch",
            hide_index=True,
            height=500,
        )


        # =================================================
        # DOWNLOAD CSV
        # =================================================

        csv_data = (
            display_df
            .to_csv(
                index=False
            )
            .encode("utf-8")
        )


        st.download_button(
            label="⬇️ Download Booking Data (CSV)",
            data=csv_data,
            file_name="bookflow_bookings.csv",
            mime="text/csv",
        )


    except Exception as error:

        st.error(
            "Could not load booking information."
        )


        with st.expander(
            "Show technical details"
        ):

            st.code(
                str(error)
            )