from datetime import datetime
import pandas as pd
import streamlit as st
from streamlit_geolocation import streamlit_geolocation

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Civic360 | Live Municipal Operations",
    page_icon="🌀",
    layout="wide",
)

# Initialize mock in-memory session store
if "reports" not in st.session_state:
    st.session_state.reports = [
        {
            "id": 1,
            "report_id": "REP-1710000001",
            "type": "Pothole",
            "severity": "High",
            "address": "123 Main St, Near Central Park",
            "description": "Large deep pothole blocking right lane.",
            "lat": 18.6298,
            "lon": 73.7997,
            "status": "Submitted",
            "created_at": "2026-03-20T10:30:00",
            "image_url": None,
        },
        {
            "id": 2,
            "report_id": "REP-1710000002",
            "type": "Streetlight Outage",
            "severity": "Medium",
            "address": "45 MG Road, Crossroad 4",
            "description": "Two consecutive streetlights are dark.",
            "lat": 18.6350,
            "lon": 73.8050,
            "status": "In Progress",
            "created_at": "2026-03-19T14:15:00",
            "image_url": None,
        },
    ]

# ==========================================
# 2. SIDEBAR NAVIGATION
# ==========================================
if "role" not in st.session_state:
    st.session_state.role = "Citizen"

with st.sidebar:
    st.title("🌀 CIVIC360")
    st.caption("Live Municipal Operations Portal")
    st.divider()

    st.subheader("Access Control")
    st.session_state.role = st.selectbox(
        "Current Session Role:",
        ["Citizen", "Municipal Admin", "Field Technician"],
        index=0 if st.session_state.role == "Citizen" else 1,
    )

    st.divider()

    st.subheader("Navigation")
    nav_choice = st.radio(
        "Select Portal Module:",
        [
            "📷 Report Hazard",
            "🛣️ Issue Tracker & Operations",
            "📊 Analytics & Spatial Heatmap",
        ],
        label_visibility="collapsed",
    )

# ==========================================
# 3. MODULE 1: REPORT HAZARD
# ==========================================
if nav_choice == "📷 Report Hazard":
    st.header("Report Infrastructure Issue")
    st.caption("Submit new civic hazard report for municipal tracking.")

    st.subheader("1. Live GPS Location Capture")
    location = streamlit_geolocation()
    user_lat = location.get("latitude")
    user_lon = location.get("longitude")

    if user_lat and user_lon:
        st.success(
            f"📍 **GPS Captured:** Latitude `{user_lat:.5f}`, Longitude `{user_lon:.5f}`"
        )
    else:
        st.warning(
            "⚠️ Location not captured yet. Please grant browser permissions and click 'Get Location'."
        )

    st.divider()

    with st.form("hazard_form", clear_on_submit=True):
        st.subheader("2. Hazard Details & Documentation")

        col_a, col_b = st.columns(2)
        with col_a:
            category_selection = st.selectbox(
                "Hazard Classification*",
                [
                    "Pothole",
                    "Surface Crack / Alligator Cracking",
                    "Open Drain / Manhole",
                    "Debris or Road Blockage",
                    "Traffic Light / Sign Failure",
                    "Streetlight Outage",
                    "Other (Specify Below)",
                ],
            )

            custom_category = ""
            if category_selection == "Other (Specify Below)":
                custom_category = st.text_input(
                    "Custom Hazard Type*", placeholder="e.g. Fallen Tree"
                )

            severity = st.select_slider(
                "Observed Severity*",
                options=["Low", "Medium", "High", "Critical"],
                value="Medium",
            )

        with col_b:
            address = st.text_input(
                "Street Address / Landmark*",
                placeholder="e.g. Opposite City Hospital",
            )

        uploaded_file = st.file_uploader(
            "Attach Photographic Proof", type=["png", "jpg", "jpeg", "webp"]
        )

        description = st.text_area(
            "Operational Description*",
            placeholder="Describe dimensions, traffic impact...",
            height=100,
        )

        submitted = st.form_submit_button(
            "Submit Hazard Report", type="primary", use_container_width=True
        )

        if submitted:
            final_category = (
                custom_category.strip()
                if category_selection == "Other (Specify Below)"
                else category_selection
            )

            if not address or not description:
                st.error("Please fill in all required fields marked with *")
            elif (
                category_selection == "Other (Specify Below)"
                and not custom_category.strip()
            ):
                st.error("Please specify your custom hazard type.")
            elif not user_lat or not user_lon:
                st.error("GPS coordinates missing! Capture location first.")
            else:
                rep_id = f"REP-{int(datetime.now().timestamp())}"

                new_report = {
                    "id": len(st.session_state.reports) + 1,
                    "report_id": str(rep_id),
                    "type": str(final_category),
                    "severity": str(severity),
                    "address": str(address),
                    "description": str(description),
                    "lat": float(user_lat),
                    "lon": float(user_lon),
                    "status": "Submitted",
                    "created_at": datetime.now().isoformat(),
                    "image_url": None,
                }

                st.session_state.reports.insert(0, new_report)
                st.success(f"Report **{rep_id}** recorded locally!")
                st.balloons()

# ==========================================
# 4. MODULE 2: ISSUE TRACKER & OPERATIONS
# ==========================================
elif nav_choice == "🛣️ Issue Tracker & Operations":
    st.header("Municipal Operations Dashboard")
    st.caption("Live dynamic queue view.")

    reports = st.session_state.reports

    total_reps = len(reports)
    pending_reps = sum(
        1
        for r in reports
        if r.get("status") in ["Submitted", "Under Review", "In Progress"]
    )
    resolved_reps = sum(
        1 for r in reports if r.get("status") == "Resolved"
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Live Logged Tickets", total_reps)
    m2.metric("Active Queue", pending_reps)
    m3.metric("Resolved", resolved_reps)

    st.divider()

    if not reports:
        st.info("No active reports logged.")
    else:
        for idx_pos, report in enumerate(reports):
            row_id = report["id"]
            rep_id = report.get("report_id", "REP-UNKNOWN")

            with st.expander(
                f"**[{rep_id}] {report.get('type')}** — {report.get('address')} ({report.get('status')})"
            ):
                c1, c2, c3 = st.columns([2, 2, 2])
                with c1:
                    st.write(
                        f"**Logged At:** {str(report.get('created_at', ''))[:16]}"
                    )
                    st.write(f"**Address:** {report.get('address')}")
                with c2:
                    st.write(f"**Severity:** {report.get('severity')}")
                    st.write(
                        f"**GPS:** {report.get('lat', 0):.4f}, {report.get('lon', 0):.4f}"
                    )
                with c3:
                    st.write(f"**Current Status:** `{report.get('status')}`")

                    if st.session_state.role in [
                        "Municipal Admin",
                        "Field Technician",
                    ]:
                        curr_status = report.get("status", "Submitted")
                        status_options = [
                            "Submitted",
                            "Under Review",
                            "In Progress",
                            "Resolved",
                        ]
                        s_idx = (
                            status_options.index(curr_status)
                            if curr_status in status_options
                            else 0
                        )

                        new_status = st.selectbox(
                            "Update Status",
                            status_options,
                            index=s_idx,
                            key=f"status_{row_id}",
                        )

                        if new_status != curr_status:
                            st.session_state.reports[idx_pos]["status"] = new_status
                            st.success("Status updated!")
                            st.rerun()

                st.markdown("---")
                st.write(f"**Description:** {report.get('description')}")
                if report.get("image_url"):
                    st.image(
                        report["image_url"],
                        caption="Evidence Photo",
                        width=300,
                    )

# ==========================================
# 5. MODULE 3: ANALYTICS & SPATIAL HEATMAP
# ==========================================
elif nav_choice == "📊 Analytics & Spatial Heatmap":
    st.header("Real-Time Spatial Analytics")
    reports = st.session_state.reports

    if not reports:
        st.info("No spatial data available.")
    else:
        df_reports = pd.DataFrame(reports)

        col_map, col_chart = st.columns([1.5, 1])
        with col_map:
            st.subheader("Live Spatial Coordinates Map")
            if "lat" in df_reports.columns and "lon" in df_reports.columns:
                st.map(df_reports[["lat", "lon"]], zoom=12)

        with col_chart:
            st.subheader("Submissions by Classification")
            if "type" in df_reports.columns:
                st.bar_chart(df_reports["type"].value_counts())
