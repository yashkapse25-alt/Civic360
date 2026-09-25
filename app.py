import base64
from datetime import datetime, timedelta
import io
import json
import re
import streamlit as st

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="CIVIC360 — Integrated Public Grievance & SLA Portal",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Helper function to convert local image to Base64
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception:
        return ""


# Custom CSS Styling
st.markdown(
    """
    <style>
    /* Government Tri-Color Bar Header */
    .gov-top-bar {
        height: 5px;
        background: linear-gradient(90deg, #FF9933 0%, #FFFFFF 50%, #138808 100%);
        border-radius: 3px;
        margin-bottom: 8px;
    }

    /* Sanskrit Ticker Styling */
    .slogan-ticker-container {
        width: 100%;
        background-color: #001f3f;
        color: #FFCC00;
        padding: 8px 12px;
        border-radius: 4px;
        overflow: hidden;
        white-space: nowrap;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .slogan-ticker-text {
        display: inline-block;
        font-family: 'Georgia', serif;
        font-size: 14px;
        animation: marquee 22s linear infinite;
    }
    
    @keyframes marquee {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }

    /* Main Title Box Styling */
    .title-box {
        background: linear-gradient(135deg, #001f3f 0%, #003366 100%);
        color: white;
        padding: 24px;
        border-radius: 8px;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .title-box h1 {
        color: #FFFFFF !important;
        margin: 0;
        font-size: 28px;
        font-weight: 700;
    }

    .title-box p {
        color: #E0E0E0 !important;
        margin-top: 8px;
        font-size: 14px;
    }

    /* Custom Metric Cards */
    .metric-card {
        background-color: #f8f9fa;
        border-left: 4px solid #003366;
        padding: 15px;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    .badge-step {
        background-color: #003366;
        color: white;
        font-weight: bold;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 12px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Convert namaste.png to base64 inline string
img_b64 = get_base64_image("namaste.png")
img_src = (
    f"data:image/png;base64,{img_b64}"
    if img_b64
    else "https://cdn-icons-png.flaticon.com/512/7581/7581561.png"
)

# Render Top Centered Header with Namaste Custom Images & Centered Greeting
top_header_html = f"""
<div style="background-color: #001f3f; color: #ffffff; padding: 12px 20px; border-radius: 6px; display: flex; justify-content: center; align-items: center; gap: 16px; margin-bottom: 6px; box-shadow: 0 2px 6px rgba(0,0,0,0.15);">
    <img src="{img_src}" width="38" height="38" style="border-radius: 50%; vertical-align: middle; object-fit: contain;"/>
    <span style="font-size: 18px; font-weight: 700; color: #FFCC00; letter-spacing: 1px; text-align: center;">
        WELCOME || सुस्वागतम्
    </span>
    <img src="{img_src}" width="38" height="38" style="border-radius: 50%; vertical-align: middle; object-fit: contain;"/>
</div>

<!-- Government Tri-Color Line -->
<div class="gov-top-bar"></div>

<!-- Sanskrit Marquee Ticker -->
<div class="slogan-ticker-container">
    <div class="slogan-ticker-text">
        <b>• बहुजनहिताय बहुजनसुखाय •</b> &nbsp;|&nbsp; <i>Bahujanahitāya Bahujanasukhāya</i> &nbsp;|&nbsp; 
        <b>Meaning:</b> "For the welfare of the many, for the happiness of the many" — Dedicated to Public Service & Civic Welfare
    </div>
</div>
"""

st.markdown(top_header_html, unsafe_allow_html=True)

# Main Title Block
st.markdown(
    """
    <div class="title-box">
        <h1>CIVIC360 — Integrated Public Grievance & SLA Portal</h1>
        <p>Official Municipal Infrastructure Monitoring & Computer Vision Operations System</p>
    </div>
""",
    unsafe_allow_html=True,
)

# Sidebar - Quick Navigation & Govt Portal Links
st.sidebar.title("🏛️ Civic Portal Navigation")
app_mode = st.sidebar.radio(
    "Select Module",
    [
        "Submit Public Grievance",
        "Track Complaint Status",
        "Municipal SLA Dashboard",
    ],
)

st.sidebar.markdown("---")
st.sidebar.subheader("📌 Emergency Helpline")
st.sidebar.info("📞 Municipal Helpline: **1800-11-2024**\n\n🚨 Disaster Cell: **108**")

# Category SLA Estimates Mapping (in Days)
SLA_MAPPING = {
    "Potholes & Road Damage": {
        "days": 3,
        "dept": "Public Works Department (PWD)",
    },
    "Garbage & Waste Accumulation": {
        "days": 1,
        "dept": "Solid Waste Management (SWM)",
    },
    "Streetlight Failure": {"days": 2, "dept": "Electrical Engineering Dept"},
    "Water Supply Leakage / Contamination": {
        "days": 2,
        "dept": "Water Supply & Drainage Dept",
    },
    "Open Manhole / Drainage Issue": {
        "days": 1,
        "dept": "Sewerage Operations Dept",
    },
    "Illegal Hoardings / Encroachment": {
        "days": 5,
        "dept": "Encroachment Removal Cell",
    },
    "Damaged Park / Public Infrastructure": {
        "days": 7,
        "dept": "Garden & Parks Dept",
    },
    "Other Municipal Issue": {
        "days": 4,
        "dept": "General Grievance Cell",
    },
}

# Session state initialization for mock database
if "complaints_db" not in st.session_state:
    st.session_state["complaints_db"] = [
        {
            "id": "C360-1001",
            "category": "Potholes & Road Damage",
            "desc": "Deep pothole near main crossroads causing traffic slowdown.",
            "location": "18.6298, 73.7997",
            "status": "In Progress",
            "dept": "Public Works Department (PWD)",
            "submitted_on": (datetime.now() - timedelta(days=1)).strftime(
                "%Y-%m-%d %H:%M"
            ),
            "expected_sla": (datetime.now() + timedelta(days=2)).strftime(
                "%Y-%m-%d"
            ),
        },
        {
            "id": "C360-1002",
            "category": "Streetlight Failure",
            "desc": "Dark stretch of streetlights out for 3 consecutive days.",
            "location": "18.6185, 73.8034",
            "status": "Resolved",
            "dept": "Electrical Engineering Dept",
            "submitted_on": (datetime.now() - timedelta(days=3)).strftime(
                "%Y-%m-%d %H:%M"
            ),
            "expected_sla": (datetime.now() - timedelta(days=1)).strftime(
                "%Y-%m-%d"
            ),
        },
    ]

# -------------------- MODULE 1: SUBMIT GRIEVANCE --------------------
if app_mode == "Submit Public Grievance":
    st.subheader("Report Infrastructure Issue")
    st.write(
        "Submit public infrastructure complaints directly to your local Municipal Authority. AI models automatically estimate repair timelines."
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(
            '<span class="badge-step">STEP 1</span> <b>GPS Location Capture</b>',
            unsafe_allow_html=True,
        )
        location_btn = st.button("📍 Capture My GPS Location")

        if location_btn:
            # Simulated GPS coordinates for Pimpri-Chinchwad / Pune Municipal Region
            st.session_state["lat"] = 18.6298
            st.session_state["lon"] = 73.7997
            st.success("✅ Coordinates Captured: Lat 18.6298, Lon 73.7997")
        else:
            st.info("Click 'Get Location' above to record exact GPS spot.")

        if "lat" in st.session_state:
            st.map({"lat": [st.session_state["lat"]], "lon": [st.session_state["lon"]]})

    with col2:
        st.markdown(
            '<span class="badge-step">STEP 2</span> <b>Attach Photographic Evidence</b>',
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "Upload Clear Photo (Optional - Triggers Auto AI Detection)",
            type=["png", "jpg", "jpeg", "webp"],
        )

        detected_category = None
        if uploaded_file is not None:
            st.image(
                uploaded_file,
                caption="Uploaded Infrastructure Snapshot",
                use_container_width=True,
            )

            # Simulated AI Detection Logic based on file name or generic fallback
            fname = uploaded_file.name.lower()
            if any(k in fname for k in ["pothole", "road", "crack"]):
                detected_category = "Potholes & Road Damage"
            elif any(k in fname for k in ["garbage", "trash", "waste"]):
                detected_category = "Garbage & Waste Accumulation"
            elif any(k in fname for k in ["light", "lamp", "pole"]):
                detected_category = "Streetlight Failure"
            elif any(k in fname for k in ["water", "leak", "pipe"]):
                detected_category = "Water Supply Leakage / Contamination"
            elif any(k in fname for k in ["manhole", "drain", "sewer"]):
                detected_category = "Open Manhole / Drainage Issue"
            else:
                detected_category = "Potholes & Road Damage"

            st.success(
                f"🤖 **AI Auto-Detection:** Issue identified as **'{detected_category}'**"
            )

    st.markdown("---")
    st.markdown(
        '<span class="badge-step">STEP 3</span> <b>Grievance Details & Submission</b>',
        unsafe_allow_html=True,
    )

    with st.form("grievance_form"):
        categories = list(SLA_MAPPING.keys())
        default_index = (
            categories.index(detected_category) if detected_category else 0
        )

        issue_type = st.selectbox(
            "Select Problem Category", categories, index=default_index
        )
        description = st.text_area(
            "Describe the issue in detail",
            placeholder="Provide landmark details, urgency, or specific civic concern...",
        )

        col_a, col_b = st.columns(2)
        with col_a:
            citizen_name = st.text_input("Full Name")
        with col_b:
            citizen_phone = st.text_input(
                "Mobile Number (For Resolution SMS Alerts)"
            )

        submit_btn = st.form_submit_button("🚀 Submit Grievance to Municipal Portal")

    if submit_btn:
        if not description or not citizen_name:
            st.error(
                "⚠️ Please fill in all required fields (Name and Description)."
            )
        else:
            complaint_id = f"C360-{1001 + len(st.session_state['complaints_db'])}"
            sla_info = SLA_MAPPING[issue_type]
            expected_date = (
                datetime.now() + timedelta(days=sla_info["days"])
            ).strftime("%Y-%m-%d")

            new_record = {
                "id": complaint_id,
                "category": issue_type,
                "desc": description,
                "location": f"{st.session_state.get('lat', 18.6298)}, {st.session_state.get('lon', 73.7997)}",
                "status": "Registered",
                "dept": sla_info["dept"],
                "submitted_on": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "expected_sla": expected_date,
            }

            st.session_state["complaints_db"].append(new_record)

            st.balloons()
            st.success(f"🎉 **Grievance Registered Successfully!**")
            st.markdown(
                f"""
                ### 📋 Registration Summary Receipt
                * **Complaint Ticket ID:** `{complaint_id}`
                * **Assigned Department:** {sla_info['dept']}
                * **Target Resolution Timeline (SLA):** **{sla_info['days']} Days** (Target: `{expected_date}`)
                * **Status:** `Registered / Dispatched to Field Engineer`
            """
            )

# -------------------- MODULE 2: TRACK COMPLAINT --------------------
elif app_mode == "Track Complaint Status":
    st.subheader("🔍 Track Your Grievance Status")
    st.write(
        "Enter your unique **Ticket ID** (e.g., `C360-1001`) to view live field updates."
    )

    search_id = st.text_input(
        "Enter Ticket ID", value="C360-1001", placeholder="C360-XXXX"
    )

    if st.button("Search Status"):
        record = next(
            (
                item
                for item in st.session_state["complaints_db"]
                if item["id"].strip().upper() == search_id.strip().upper()
            ),
            None,
        )

        if record:
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"### Ticket ID: `{record['id']}`")
                st.write(f"**Category:** {record['category']}")
                st.write(f"**Assigned Dept:** {record['dept']}")
                st.write(f"**Submitted Date:** {record['submitted_on']}")
                st.write(f"**Target SLA Date:** `{record['expected_sla']}`")

            with col2:
                status_color = (
                    "🟢"
                    if record["status"] == "Resolved"
                    else ("🟡" if record["status"] == "In Progress" else "🔵")
                )
                st.markdown(f"### Current Status: {status_color} {record['status']}")
                st.info(f"**Issue Summary:** {record['desc']}")
                st.write(f"**Coordinates:** {record['location']}")

            # Progress Bar Simulation
            progress_map = {"Registered": 25, "In Progress": 65, "Resolved": 100}
            st.progress(progress_map.get(record["status"], 10))
        else:
            st.error(
                f"❌ No complaint found matching ID `{search_id}`. Please check the ticket number."
            )

# -------------------- MODULE 3: SLA DASHBOARD --------------------
elif app_mode == "Municipal SLA Dashboard":
    st.subheader("📊 Municipal Authority SLA Compliance Dashboard")
    st.write(
        "Real-time governance analytics monitoring department resolution speeds and SLA adherence."
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Grievances", len(st.session_state["complaints_db"]))
    col2.metric("In Progress", 1)
    col3.metric("Resolved Within SLA", 1)
    col4.metric("Overall SLA Compliance", "94.8%")

    st.markdown("---")
    st.subheader("📋 Registered Grievances Master Record")

    # Display complaints table
    st.dataframe(
        st.session_state["complaints_db"],
        use_container_width=True,
        hide_index=True,
    )
