import random
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Civic360 - Local Civic Issues Reporting System",
    page_icon="🌀",
    layout="wide",
)

# Initialize Session State for Reports and Role
if "role" not in st.session_state:
    st.session_state.role = "Citizen"

if "reports" not in st.session_state:
    st.session_state.reports = [
        {
            "id": "#REP-4102",
            "type": "Pothole",
            "priority": "High (88/100)",
            "dept": "Roads & Maintenance",
            "status": "Under Review",
        },
        {
            "id": "#REP-4091",
            "type": "Surface Crack",
            "priority": "Low (32/100)",
            "dept": "Civic Infrastructure",
            "status": "Resolved",
        },
    ]

# Sidebar Setup
st.sidebar.title("🌀 CIVIC360")
st.sidebar.caption("See It. Report It. Track It. Fix It.")
st.sidebar.divider()

# Role Selector
selected_role = st.sidebar.selectbox(
    "Select User Role:",
    ["Citizen", "Municipal Admin"],
    index=0 if st.session_state.role == "Citizen" else 1,
)
st.session_state.role = selected_role

# Navigation Menu
nav_choice = st.sidebar.radio(
    "Navigation",
    [
        "📷 Report Hazard",
        "🛣️ Track Reports",
        "📊 Analytics & Map",
        "🧠 AI Vision Inspection",
    ],
)

st.sidebar.divider()

# Live Updates Sidebar Panel
st.sidebar.subheader("Live Updates")
st.sidebar.info("**#REP-4091:** Status updated to **Resolved**.")
st.sidebar.warning("**#REP-4102:** Duplicate report detected nearby.")

# ==========================================
# PAGE 1: REPORT HAZARD
# ==========================================
if nav_choice == "📷 Report Hazard":
    st.header("Submit a New Road Hazard")
    st.caption(
        "Upload an image and capture GPS locations to alert local authorities."
    )

    with st.form("hazard_form", clear_on_submit=True):
        uploaded_file = st.file_uploader(
            "Upload Photo", type=["png", "jpg", "jpeg", "webp"]
        )
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Image Preview", width=300)

        col1, col2 = st.columns(2)

        with col1:
            category = st.selectbox(
                "Hazard Type*",
                [
                    "Pothole",
                    "Surface Crack / Alligator Cracking",
                    "Open Drain / Manhole",
                    "Debris or Blockage",
                ],
            )

        with col2:
            gps_location = st.text_input(
                "Location / GPS Tag*", value="18.5204° N, 73.8567° E"
            )

        description = st.text_area(
            "Description & Context",
            placeholder="Provide extra context (e.g., depth of pothole, near traffic intersection)...",
        )

        submitted = st.form_submit_button(
            "Submit Report", type="primary", use_container_width=True
        )

        if submitted:
            new_id = f"#REP-{random.randint(1000, 9999)}"
            new_report = {
                "id": new_id,
                "type": category,
                "priority": "Medium (65/100)",
                "dept": "Automated Route",
                "status": "Submitted",
            }
            st.session_state.reports.insert(0, new_report)
            st.success(
                f"Report **{new_id}** successfully logged and passed to AI Pipeline!"
            )


# ==========================================
# PAGE 2: TRACK REPORTS
# ==========================================
elif nav_choice == "🛣️ Track Reports":
    st.header("Track & Manage Complaints")
    st.caption(
        "View live status updates, assigned priority, and duplicate detections."
    )

    if st.session_state.role == "Municipal Admin":
        st.warning(
            "🔓 **Admin Controls Active:** You can permanently delete resolved or invalid reports from the active list."
        )

    st.subheader("Active Reports")

    # Display reports list
    if not st.session_state.reports:
        st.info("No active reports found.")
    else:
        for idx, report in enumerate(st.session_state.reports):
            with st.container(border=True):
                col_id, col_type, col_prio, col_dept, col_status, col_action = (
                    st.columns([1.5, 2, 2, 2, 1.5, 1.5])
                )

                col_id.markdown(f"**{report['id']}**")
                col_type.write(report["type"])
                col_prio.write(f"`{report['priority']}`")
                col_dept.write(report["dept"])

                # Status styling badge
                if report["status"] == "Resolved":
                    col_status.success(report["status"])
                elif report["status"] == "Under Review":
                    col_status.warning(report["status"])
                else:
                    col_status.info(report["status"])

                # Admin-only Deletion Action
                if st.session_state.role == "Municipal Admin":
                    if col_action.button(
                        "🗑️ Remove", key=f"del_{report['id']}_{idx}"
                    ):
                        st.session_state.reports.pop(idx)
                        st.toast(
                            f"Removed report {report['id']}", icon="🗑️"
                        )
                        st.rerun()
                else:
                    col_action.button(
                        "Details", key=f"view_{report['id']}_{idx}"
                    )


# ==========================================
# PAGE 3: ANALYTICS & MAP
# ==========================================
elif nav_choice == "📊 Analytics & Map":
    st.header("Analytics & Spatial Heatmap")
    st.caption(
        "Aggregated statistics for data-driven municipal repair decisions."
    )

    # Key Performance Indicators
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Reports", len(st.session_state.reports) + 1246)
    kpi2.metric("Pending Repairs", "84")
    kpi3.metric("Resolution Rate", "93.2%")

    st.divider()
    st.subheader("Spatial Map Overlay")

    # Sample geographical coordinates centered near Pune / Maharashtra
    map_data = pd.DataFrame(
        {
            "lat": [18.5204, 18.5304, 18.5104, 18.5250],
            "lon": [73.8567, 73.8467, 73.8667, 73.8500],
        }
    )

    st.map(map_data, zoom=12)


# ==========================================
# PAGE 4: AI VISION INSPECTION
# ==========================================
elif nav_choice == "🧠 AI Vision Inspection":
    st.header("AI Vision: Road Surface Analysis")
    st.caption("MODEL: ResNet/YOLO Hazard Detector v2.1")

    col_visual, col_metrics = st.columns([2, 1])

    with col_visual:
        st.subheader("Live Inference Workspace")
        st.info("🎯 **Detected Bounding Boxes:**")
        st.code(
            """
[BOX 1] Pothole Detected    | Confidence: 94.1% | Severity: High
[BOX 2] Surface Cracking   | Confidence: 81.3% | Severity: Medium
        """,
            language="text",
        )

    with col_metrics:
        st.subheader("Model Metrics")
        st.metric("Model Accuracy", "96.7%")
        st.metric("Precision", "94.1%")
        st.metric("Recall", "92.5%")

        st.divider()
        st.warning(
            "**Recommended Action:**\nPriority Level 2 -> Route directly to Highways Dept."
        )
