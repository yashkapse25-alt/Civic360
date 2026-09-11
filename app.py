import os
import random
from datetime import datetime
import pandas as pd
import streamlit as st

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Civic360 | Municipal Operations & Citizen Reporting",
    page_icon="🌀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished production UI
st.markdown(
    """
    <style>
        .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
        .metric-card {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .stBadge { font-weight: 600; }
        div[data-testid="stSidebarNav"] { padding-top: 10px; }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# MOCK DATABASE / STATE INITIALIZATION
# ==========================================
if "reports_db" not in st.session_state:
    st.session_state.reports_db = [
        {
            "id": "REP-4102",
            "timestamp": "2026-03-10 09:15",
            "type": "Pothole",
            "severity": "High",
            "priority_score": 88,
            "dept": "Roads & Maintenance",
            "status": "Under Review",
            "address": "MG Road, Near Central Mall",
            "lat": 18.5204,
            "lon": 73.8567,
            "description": "Deep pothole causing vehicle slowdowns and safety hazards.",
        },
        {
            "id": "REP-4091",
            "timestamp": "2026-03-08 14:22",
            "type": "Surface Crack",
            "severity": "Low",
            "priority_score": 32,
            "dept": "Civic Infrastructure",
            "status": "Resolved",
            "address": "FC Road, Block B",
            "lat": 18.5304,
            "lon": 73.8467,
            "description": "Minor longitudinal cracking along the shoulder.",
        },
        {
            "id": "REP-4085",
            "timestamp": "2026-03-07 11:05",
            "type": "Open Drain / Manhole",
            "severity": "Critical",
            "priority_score": 95,
            "dept": "Sanitation & Drainage",
            "status": "In Progress",
            "address": "Koregaon Park, Lane 5",
            "lat": 18.5104,
            "lon": 73.8667,
            "description": "Missing manhole cover near pedestrian walkway.",
        },
    ]

if "role" not in st.session_state:
    st.session_state.role = "Citizen"

# ==========================================
# SIDEBAR & GLOBAL NAVIGATION
# ==========================================
with st.sidebar:
    st.title("🌀 CIVIC360")
    st.caption("Enterprise Civic Infrastructure Management")
    st.divider()

    # User Role Management
    st.subheader("Access Control")
    selected_role = st.selectbox(
        "Current Session Role:",
        ["Citizen", "Municipal Admin", "Field Technician"],
        index=0 if st.session_state.role == "Citizen" else 1,
    )
    st.session_state.role = selected_role

    st.divider()

    # Module Navigation
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

    st.divider()

    # System Status Panel
    st.caption("SYSTEM BROADCASTS")
    st.info("**#REP-4085:** Field team dispatched to Koregaon Park.")
    st.success("**#REP-4091:** Marked as Resolved by Roads Dept.")


# ==========================================
# MODULE 1: REPORT HAZARD
# ==========================================
if nav_choice == "📷 Report Hazard":
    st.header("Report Infrastructure Issue")
    st.caption(
        "Submit geo-tagged infrastructure issues directly to municipal dispatch."
    )

    with st.form("hazard_submission_form", clear_on_submit=True):
        st.subheader("1. Incident Details")

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
            col_lat, col_lon = st.columns(2)
            with col_lat:
                lat = st.number_input(
                    "Latitude", value=18.5204, format="%.4f"
                )
            with col_lon:
                lon = st.number_input(
                    "Longitude", value=73.8567, format="%.4f"
                )

        st.subheader("2. Evidence & Documentation")
        uploaded_file = st.file_uploader(
            "Attach Photographic Proof",
            type=["png", "jpg", "jpeg", "webp"],
            help="High-resolution photos assist automated routing engines.",
        )
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Evidence Preview", width=250)

        description = st.text_area(
            "Detailed Operational Description*",
            placeholder="Describe dimensions, traffic impact, hazards to pedestrians, etc...",
            height=100,
        )

        submitted = st.form_submit_button(
            "Submit Hazard Report", type="primary", use_container_width=True
        )

        if submitted:
            if not address or not description:
                st.error("Please fill in all required fields marked with *")
            else:
                new_id = f"REP-{random.randint(5000, 9999)}"
                p_scores = {"Low": 30, "Medium": 60, "High": 85, "Critical": 98}

                # Auto-assign department based on classification
                dept_map = {
                    "Pothole": "Roads & Maintenance",
                    "Surface Crack / Alligator Cracking": "Civic Infrastructure",
                    "Open Drain / Manhole": "Sanitation & Drainage",
                    "Debris or Road Blockage": "Public Works",
                    "Traffic Light / Sign Failure": "Traffic Engineering",
                    "Streetlight Outage": "Electrical Grid",
                }

                new_report = {
                    "id": new_id,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "type": category,
                    "severity": severity,
                    "priority_score": p_scores[severity],
                    "dept": dept_map.get(category, "General Administration"),
                    "status": "Submitted",
                    "address": address,
                    "lat": lat,
                    "lon": lon,
                    "description": description,
                }

                st.session_state.reports_db.insert(0, new_report)
                st.success(
                    f"Report **{new_id}** recorded and dispatched to **{new_report['dept']}**!"
                )
                st.balloons()


# ==========================================
# MODULE 2: ISSUE TRACKER & OPERATIONS
# ==========================================
elif nav_choice == "🛣️ Issue Tracker & Operations":
    st.header("Municipal Operations Dashboard")
    st.caption("Manage ticket workflows, updates, and assignments.")

    # Top Metrics Bar
    m1, m2, m3, m4 = st.columns(4)
    total_reps = len(st.session_state.reports_db)
    pending_reps = sum(
        1
        for r in st.session_state.reports_db
        if r["status"] in ["Submitted", "Under Review", "In Progress"]
    )
    resolved_reps = sum(
        1 for r in st.session_state.reports_db if r["status"] == "Resolved"
    )

    m1.metric("Total Tickets", total_reps)
    m2.metric("Active Queue", pending_reps)
    m3.metric("Resolved", resolved_reps)
    m4.metric(
        "SLA Compliance Rate",
        f"{(resolved_reps/total_reps*100 if total_reps else 100):.1f}%",
    )

    st.divider()

    # Operational Control Bar (Filtering & Search)
    col_filter1, col_filter2, col_filter3 = st.columns([2, 1.5, 1.5])
    with col_filter1:
        search_query = st.text_input(
            "🔍 Search Reports", placeholder="Search ID, location, or type..."
        )
    with col_filter2:
        status_filter = st.selectbox(
            "Filter by Status:",
            ["All Statuses", "Submitted", "Under Review", "In Progress", "Resolved"],
        )
    with col_filter3:
        sort_order = st.selectbox(
            "Sort Order:", ["Newest First", "Highest Priority", "Lowest Priority"]
        )

    # Filter Application
    filtered_db = st.session_state.reports_db.copy()

    if status_filter != "All Statuses":
        filtered_db = [r for r in filtered_db if r["status"] == status_filter]

    if search_query:
        query = search_query.lower()
        filtered_db = [
            r
            for r in filtered_db
            if query in r["id"].lower()
            or query in r["address"].lower()
            or query in r["type"].lower()
        ]

    if sort_order == "Highest Priority":
        filtered_db.sort(key=lambda x: x["priority_score"], reverse=True)
    elif sort_order == "Lowest Priority":
        filtered_db.sort(key=lambda x: x["priority_score"])

    st.subheader(f"Tickets Queue ({len(filtered_db)})")

    if not filtered_db:
        st.info("No reports match your current filter parameters.")
    else:
        for idx, report in enumerate(filtered_db):
            with st.expander(
                f"**[{report['id']}] {report['type']}** — {report['address']} ({report['status']})"
            ):
                c1, c2, c3 = st.columns([2, 2, 2])

                with c1:
                    st.write(f"**Logged At:** {report['timestamp']}")
                    st.write(f"**Assigned Dept:** {report['dept']}")
                    st.write(f"**Address:** {report['address']}")

                with c2:
                    st.write(f"**Severity:** {report['severity']}")
                    st.write(
                        f"**Priority Rating:** {report['priority_score']}/100"
                    )
                    st.write(f"**Coordinates:** {report['lat']}, {report['lon']}")

                with c3:
                    st.write(f"**Current Status:** `{report['status']}`")

                    # Operational Actions for Admins / Technicians
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
                            key=f"status_select_{report['id']}_{idx}",
                        )

                        if new_status != report["status"]:
                            # Find index in main session state and update
                            main_idx = next(
                                i
                                for i, r in enumerate(st.session_state.reports_db)
                                if r["id"] == report["id"]
                            )
                            st.session_state.reports_db[main_idx][
                                "status"
                            ] = new_status
                            st.success(
                                f"Updated {report['id']} status to {new_status}"
                            )
                            st.rerun()

                        if (
                            st.session_state.role == "Municipal Admin"
                            and st.button(
                                "🗑️ Delete Record",
                                key=f"del_{report['id']}_{idx}",
                                type="secondary",
                            )
                        ):
                            st.session_state.reports_db = [
                                r
                                for r in st.session_state.reports_db
                                if r["id"] != report["id"]
                            ]
                            st.toast(
                                f"Deleted record {report['id']}", icon="🗑️"
                            )
                            st.rerun()

                st.markdown("---")
                st.write(f"**Description:** {report['description']}")


# ==========================================
# MODULE 3: ANALYTICS & SPATIAL HEATMAP
# ==========================================
elif nav_choice == "📊 Analytics & Spatial Heatmap":
    st.header("Municipal Analytics & Geospatial Dashboard")
    st.caption("Data-driven insights for resource allocation and city planning.")

    df_reports = pd.DataFrame(st.session_state.reports_db)

    # Historical Baseline Data (Simulating large-scale historical records)
    historical_total = 1246 + len(df_reports)
    historical_resolved_rate = 93.2
    avg_resolution_days = 2.4

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Lifetime Reports Logged", historical_total, delta="+14 this week")
    kpi2.metric("Overall Resolution Rate", f"{historical_resolved_rate}%", delta="+0.4%")
    kpi3.metric("Avg Repair Turnaround", f"{avg_resolution_days} Days", delta="-0.3 days")
    kpi4.metric(
        "Active High-Risk Hotspots",
        len(df_reports[df_reports["severity"] == "Critical"]),
    )

    st.divider()

    chart_col, map_col = st.columns([1, 1.2])

    with chart_col:
        st.subheader("Reports by Infrastructure Category")
        if not df_reports.empty:
            type_counts = df_reports["type"].value_counts()
            st.bar_chart(type_counts)
        else:
            st.info("No data available for charting.")

        st.subheader("Departmental Distribution")
        if not df_reports.empty:
            dept_counts = (
                df_reports["dept"].value_counts().reset_index()
            )
            dept_counts.columns = ["Department", "Tickets"]
            st.dataframe(dept_counts, use_container_width=True, hide_index=True)

    with map_col:
        st.subheader("Spatial Hazard Distribution Map")
        if not df_reports.empty:
            map_data = df_reports[["lat", "lon"]].dropna()
            st.map(map_data, zoom=12, use_container_width=True)
        else:
            st.info("No spatial data available.")

    st.divider()

    # Data Export Capability
    st.subheader("Export Municipal Data")
    if not df_reports.empty:
        csv_data = df_reports.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Active Data Report (CSV)",
            data=csv_data,
            file_name=f"civic360_export_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
