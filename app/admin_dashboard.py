import pandas as pd
import streamlit as st

from db.database import cancel_booking, get_all_bookings, get_booking_by_id, update_booking


def _status_badge(status):
    value = str(status).lower()
    if value == "confirmed":
        return "🟢 Confirmed"
    if value == "cancelled":
        return "🔴 Cancelled"
    return str(status)


def _normalize_date(value):
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


def _normalize_time(value):
    text = str(value or "").strip()
    if len(text) >= 5:
        return text[:5]
    return text


def _render_admin_actions(filtered):
    st.divider()
    st.subheader("🛠️ Manage Reservation")
    st.caption("Edit reservation details or cancel a reservation from the dashboard.")

    options = {
        int(row["id"]): (
            f"#{int(row['id'])} · {row['name']} · {row['date']} · {row['time']}"
        )
        for _, row in filtered.iterrows()
    }

    selected_id = st.selectbox(
        "Choose a reservation",
        options=list(options.keys()),
        format_func=lambda booking_id: options[booking_id],
    )

    booking = get_booking_by_id(selected_id)
    if not booking:
        st.warning("That reservation could not be loaded.")
        return

    with st.form(f"edit_reservation_{selected_id}"):
        left, right = st.columns(2)

        with left:
            name = st.text_input("Customer name", value=booking.get("name") or "")
            email = st.text_input("Email", value=booking.get("email") or "")
            phone = st.text_input("Phone", value=booking.get("phone") or "")
            guests = st.number_input(
                "Guests",
                min_value=1,
                max_value=50,
                value=int(booking.get("number_of_guests") or 1),
            )

        with right:
            current_date = _normalize_date(booking.get("date"))
            reservation_date = st.date_input(
                "Reservation date",
                value=current_date,
            )
            reservation_time = st.text_input(
                "Reservation time (HH:MM)",
                value=_normalize_time(booking.get("time")),
            )
            occasion = st.text_input("Occasion", value=booking.get("occasion") or "")
            status = st.selectbox(
                "Status",
                ["Confirmed", "Cancelled"],
                index=0 if str(booking.get("status")).lower() != "cancelled" else 1,
            )

        dietary = st.text_area(
            "Dietary requirements",
            value=booking.get("dietary_requirements") or "",
        )
        requests = st.text_area(
            "Special requests",
            value=booking.get("special_requests") or "",
        )

        save_changes = st.form_submit_button("💾 Save Changes", type="primary")

    if save_changes:
        time_value = str(reservation_time or "").strip()
        name_value = str(name or "").strip()
        email_value = str(email or "").strip()
        phone_value = str(phone or "").strip()

        if not reservation_date:
            st.error("Please provide a valid reservation date.")
        elif len(time_value) != 5 or time_value[2:3] != ":":
            st.error("Use HH:MM format for the reservation time, for example 20:00.")
        elif not name_value or not email_value or not phone_value:
            st.error("Name, email, and phone cannot be empty.")
        else:
            update_booking(
                selected_id,
                {
                    "name": name_value,
                    "email": email_value,
                    "phone": phone_value,
                    "number_of_guests": int(guests or 1),
                    "date": reservation_date.strftime("%Y-%m-%d"),
                    "time": time_value,
                    "occasion": str(occasion).strip() if occasion else None,
                    "dietary_requirements": str(dietary).strip() if dietary else None,
                    "special_requests": str(requests).strip() if requests else None,
                    "status": status,
                },
            )
            st.success(f"Reservation #{selected_id} updated successfully.")
            st.rerun()

    current_status = str(booking.get("status") or "").lower()
    if current_status != "cancelled":
        with st.expander("⚠️ Cancel this reservation"):
            st.warning("This changes the reservation status to Cancelled. The record remains available for audit and export.")
            if st.button(
                "Cancel Reservation",
                type="secondary",
                key=f"cancel_reservation_{selected_id}",
            ):
                if cancel_booking(selected_id):
                    st.success(f"Reservation #{selected_id} cancelled.")
                    st.rerun()
                else:
                    st.error("The reservation could not be cancelled.")
    else:
        st.info("This reservation is already cancelled. You can restore it by changing its status to Confirmed and saving.")


def show_admin_dashboard():
    try:
        bookings = get_all_bookings()

        if not bookings:
            with st.container(border=True):
                st.markdown("## 📭 No reservations yet")
                st.caption("Confirmed restaurant reservations will appear here.")
            return

        df = pd.DataFrame(bookings)

        total_bookings = len(df)
        total_customers = df["email"].nunique() if "email" in df else 0
        confirmed = (
            df["status"].astype(str).str.lower().eq("confirmed").sum()
            if "status" in df
            else total_bookings
        )
        cancelled = (
            df["status"].astype(str).str.lower().eq("cancelled").sum()
            if "status" in df
            else 0
        )
        total_guests = (
            pd.to_numeric(df["number_of_guests"], errors="coerce")
            .fillna(0)
            .sum()
            if "number_of_guests" in df
            else 0
        )

        st.subheader("📊 Reservation Overview")

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("Reservations", total_bookings)
        with c2:
            st.metric("Customers", total_customers)
        with c3:
            st.metric("Confirmed", int(confirmed))
        with c4:
            st.metric("Cancelled", int(cancelled))
        with c5:
            st.metric("Guests", int(total_guests))

        st.divider()
        st.subheader("🔎 Find Reservations")

        f1, f2 = st.columns([3, 2])
        with f1:
            search = st.text_input(
                "Search",
                placeholder="Name, email, phone, occasion, or request...",
                label_visibility="collapsed",
            )
        with f2:
            status_filter = st.selectbox(
                "Status",
                ["All statuses", "Confirmed", "Cancelled"],
                label_visibility="collapsed",
            )

        use_date_filter = st.checkbox("Filter by reservation date")
        selected_date = st.date_input("Reservation date") if use_date_filter else None

        filtered = df.copy()

        if search:
            term = str(search).strip().lower()
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

        if status_filter != "All statuses" and "status" in filtered.columns:
            filtered = filtered[
                filtered["status"].astype(str).str.lower()
                == status_filter.lower()
            ]

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
            height=430,
        )

        csv_data = display_df[columns].to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Export current results as CSV",
            data=csv_data,
            file_name="bookflow_reservations.csv",
            mime="text/csv",
        )

        _render_admin_actions(filtered)

    except Exception as error:
        st.error("Could not load reservation information.")
        with st.expander("Technical details"):
            st.code(str(error))
