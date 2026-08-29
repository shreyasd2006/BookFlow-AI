import pandas as pd
import streamlit as st

from db.database import get_all_bookings


def _status_badge(status):
    value = str(status).lower()
    if value == "confirmed":
        return "✅ Confirmed"
    if value == "cancelled":
        return "❌ Cancelled"
    return str(status)


def show_admin_dashboard():
    try:
        bookings = get_all_bookings()

        if not bookings:
            with st.container(border=True):
                st.markdown("## 📭 No reservations yet")
                st.caption(
                    "Confirmed restaurant reservations will appear here."
                )
            return

        df = pd.DataFrame(bookings)

        total_bookings = len(df)
        total_customers = df["email"].nunique() if "email" in df else 0
        confirmed = (
            df["status"].astype(str).str.lower().eq("confirmed").sum()
            if "status" in df
            else total_bookings
        )
        total_guests = (
            pd.to_numeric(df["number_of_guests"], errors="coerce")
            .fillna(0)
            .sum()
            if "number_of_guests" in df
            else 0
        )

        st.subheader("📊 Reservation Overview")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Reservations", total_bookings)
        with c2:
            st.metric("Customers", total_customers)
        with c3:
            st.metric("Confirmed", int(confirmed))
        with c4:
            st.metric("Guests", int(total_guests))

        st.divider()

        st.subheader("🔎 Find Reservations")
        search = st.text_input(
            "Search",
            placeholder="Name, email, phone, occasion, or request...",
            label_visibility="collapsed",
        )

        use_date_filter = st.checkbox("Filter by reservation date")
        selected_date = None
        if use_date_filter:
            selected_date = st.date_input("Reservation date")

        filtered = df.copy()

        if search:
            term = search.strip().lower()
            searchable = [
                "name",
                "email",
                "phone",
                "occasion",
                "special_requests",
                "dietary_requirements",
                "booking_type",
            ]
            mask = pd.Series(False, index=filtered.index)
            for column in searchable:
                if column in filtered.columns:
                    mask |= (
                        filtered[column]
                        .astype(str)
                        .str.lower()
                        .str.contains(term, na=False)
                    )
            filtered = filtered[mask]

        if selected_date is not None and "date" in filtered.columns:
            selected = selected_date.strftime("%Y-%m-%d")
            filtered = filtered[
                filtered["date"].astype(str).str.startswith(selected, na=False)
            ]

        st.divider()
        st.subheader(f"📋 Reservations · {len(filtered)} results")

        if filtered.empty:
            st.info("No reservations match the current filters.")
            return

        display_df = filtered.copy()

        if "created_at" in display_df.columns:
            created = pd.to_datetime(display_df["created_at"], errors="coerce")
            display_df["created_at"] = created.dt.strftime(
                "%d %b %Y, %I:%M %p"
            ).fillna("")

        if "status" in display_df.columns:
            display_df["status"] = display_df["status"].map(_status_badge)

        display_df = display_df.rename(
            columns={
                "id": "Reservation ID",
                "name": "Customer",
                "email": "Email",
                "phone": "Phone",
                "booking_type": "Type",
                "number_of_guests": "Guests",
                "date": "Date",
                "time": "Time",
                "occasion": "Occasion",
                "dietary_requirements": "Dietary",
                "special_requests": "Special Requests",
                "status": "Status",
                "created_at": "Created",
            }
        )

        columns = [
            "Reservation ID",
            "Customer",
            "Guests",
            "Date",
            "Time",
            "Email",
            "Phone",
            "Occasion",
            "Dietary",
            "Special Requests",
            "Status",
            "Created",
        ]
        columns = [column for column in columns if column in display_df.columns]

        st.dataframe(
            display_df[columns],
            width="stretch",
            hide_index=True,
            height=500,
        )

        csv_data = display_df[columns].to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Export reservations as CSV",
            data=csv_data,
            file_name="bookflow_reservations.csv",
            mime="text/csv",
        )

    except Exception as error:
        st.error("Could not load reservation information.")
        with st.expander("Technical details"):
            st.code(str(error))
