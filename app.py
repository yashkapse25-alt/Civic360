from datetime import datetime
import pandas as pd
import streamlit as st
from streamlit_geolocation import streamlit_geolocation

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Civic360 | Live Municipal Operations",
    page_icon="🌀",
    layout="wide",
)

# Custom CSS
st.markdown(
    """
    <style>
        .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
        .stBadge { font-weight: 600; }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# DYNAMIC DATABASE INITIALIZATION
# ==========================================
# Initialized as an empty list so the portal starts fresh without dummy data
if "reports_db" not in st.session_state:
    st.session_state.reports_db = []

if "role" not in st.session_state:
    st.session_state.role = "Citizen"

# ==========================================
# NAVIGATION & SIDEBAR
# ==========================================
with st.sidebar:
    st.title("🌀 CIVIC360")
    st.caption("Live Municipal Operations & Citizen Portal")
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
# MODULE 1: REPORT HAZARD (LIVE GPS)
# ==========================================
if nav_choice == "📷 Report Hazard":
    st.header("Report Infrastructure Issue")
    st.caption(
        "Capture your real-time location and upload photographic proof to dispatch local crews."
    )

    # Automated Browser Geolocation Component
    st.subheader("1. Live GPS Location Capture")
    st.info("Click the button below to fetch your device's live coordinates.")

    location = streamlit_geolocation()

    user_lat = location.get("latitude")
    user_lon = location.get("longitude")

    if user_lat and user_lon:
        st.success(
            f"📍 **GPS Captured:** Latitude `{user_lat:.5f}`, Longitude `{user_lon:.5f}`"
        )
    else:
        st.warning(
            "⚠️ Location not captured yet. Please grant browser location permission and click 'Get Location'."
        )

    st.divider()

    # Form Submission
    with st.form("hazard_submission_form", clear_on_submit=True):
        st.subheader("2. Hazard Details & Documentation")

        col_a, col_b = st.columns(2)
        with col_a:
            category = st.selectbox(
                "Hazard Classification*",
                [
                    "Pothole",
                    "Surface Crack / Alligator Cracking",
                    "Open Drain / Manhole",
                    "Debris or Road Blockage",
                    "Traffic Light / Sign Failure",
                    "Streetlight Outage",
                ],
            )
            severity = st.select_slider(
                "Observed Severity*",
                options=["Low", "Medium", "High", "Critical"],
                value="Medium",
            )

        with col_b:
            address = st.text_input(
                "Street Address / Landmark*",
                placeholder="e.g. Opposite City Hospital, Main Street",
            )

        uploaded_file = st.file_uploader(
            "Attach Photographic Proof", type=["png", "jpg", "jpeg", "webp"]
        )
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Evidence Preview", width=250)

        description = st.text_area(
            "Operational Description*",
            placeholder="Describe dimensions, traffic impact, hazards to pedestrians...",
            height=100,
        )

        submitted = st.form_submit_button(
            "Submit Hazard Report", type="primary", use_container_width=True
        )

        if submitted:
            if not address or not description:
                st.error("Please fill in all required fields marked with *")
            elif not user_lat or not user_lon:
                st.error(
                    "GPS coordinates missing! Please capture your live location before submitting."
                )
            else:
                report_id = f"REP-{len(st.session_state.reports_db) + 1001}"
                p_scores = {"Low": 30, "Medium": 60, "High": 85, "Critical": 98}

                dept_map = {
                    "Pothole": "Roads & Maintenance",
                    "Surface Crack / Alligator Cracking": "Civic Infrastructure",
                    "Open Drain / Manhole": "Sanitation & Drainage",
                    "Debris or Road Blockage": "Public Works",
                    "Traffic Light / Sign Failure": "Traffic Engineering",
                    "Streetlight Outage": "Electrical Grid",
                }

                # Save new report directly to active state database
                new_report = {
                    "id": report_id,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "type": category,
                    "severity": severity,
                    "priority_score": p_scores[severity],
                    "dept": dept_map.get(category, "General Administration"),
                    "status": "Submitted",
                    "address": address,
                    "lat": user_lat,
                    "lon": user_lon,
                    "description": description,
                }

                st.session_state.reports_db.insert(0, new_report)
                st.success(
                    f"Report **{report_id}** successfully dispatched to **{new_report['dept']}**!"
                )
                st.balloons()

# ==========================================
# MODULE 2: ISSUE TRACKER & OPERATIONS
# ==========================================
elif nav_choice == "🛣️ Issue Tracker & Operations":
    st.header("Municipal Operations Dashboard")
    st.caption("Real-time management of active user-submitted tickets.")

    total_reps = len(st.session_state.reports_db)
    pending_reps = sum(
        1
        for r in st.session_state.reports_db
        if r["status"] in ["Submitted", "Under Review", "In Progress"]
    )
    resolved_reps = sum(
        1 for r in st.session_state.reports_db if r["status"] == "Resolved"
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Live Logged Tickets", total_reps)
    m2.metric("Active Queue", pending_reps)
    m3.metric("Resolved", resolved_reps)

    st.divider()

    if not st.session_state.reports_db:
        st.info(
            "No live reports logged yet. Go to 'Report Hazard' to submit the first issue."
        )
    else:
        for idx, report in enumerate(st.session_state.reports_db):
            with st.expander(
                f"**[{report['id']}] {report['type']}** — {report['address']} ({report['status']})"
            ):
                c1, c2, c3 = st.columns([2, 2, 2])
                with c1:
                    st.write(f"**Logged At:** {report['timestamp']}")
                    st.write(f"**Department:** {report['dept']}")
                    st.write(f"**Address:** {report['address']}")
                with c2:
                    st.write(f"**Severity:** {report['severity']}")
                    st.write(
                        f"**Live Coordinates:** {report['lat']:.4f}, {report['lon']:.4f}"
                    )
                with c3:
                    st.write(f"**Current Status:** `{report['status']}`")

                    if st.session_state.role in [
                        "Municipal Admin",
                        "Field Technician",
                    ]:
                        new_status = st.selectbox(
                            "Update Status",
                            ["Submitted", "Under Review", "In Progress", "Resolved"],
                            index=[
                                "Submitted",
                                "Under Review",
                                "In Progress",
                                "Resolved",
                            ].index(report["status"]),
                            key=f"status_{report['id']}_{idx}",
                        )
                        if new_status != report["status"]:
                            st.session_state.reports_db[idx][
                                "status"
                            ] = new_status
                            st.rerun()

                st.markdown("---")
                st.write(f"**Description:** {report['description']}")

# ==========================================
# MODULE 3: ANALYTICS & SPATIAL HEATMAP
# ==========================================
elif nav_choice == "📊 Analytics & Spatial Heatmap":
    st.header("Real-Time Spatial Analytics")

    if not st.session_state.reports_db:
        st.info("No spatial data available. Submit a hazard to render analytics.")
    else:
        df_reports = pd.DataFrame(st.session_state.reports_db)

        col_map, col_chart = st.columns([1.5, 1])
        with col_map:
            st.subheader("Live Spatial Coordinates Map")
            st.map(df_reports[["lat", "lon"]], zoom=12)

        with col_chart:
            st.subheader("Submissions by Classification")
            st.bar_chart(df_reports["type"].value_counts())
