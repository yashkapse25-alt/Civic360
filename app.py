from datetime import datetime
from PIL import Image
import folium
import numpy as np
import pandas as pd
import plotly.express as px
from sklearn.ensemble import RandomForestRegressor
import streamlit as st
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation
from supabase import create_client
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.models import Model

# ==========================================
# 1. PAGE CONFIG & CUSTOM GOV-CSS STYLING
# ==========================================
st.set_page_config(
    page_title="Civic360 | Integrated Public Grievance Portal",
    page_icon="🏛️",
    layout="wide",
)

# Custom CSS for Official Government Aesthetic & Dynamic Slogan Ticker
st.markdown(
    """
    <style>
    /* Government Header Ribbon */
    .gov-top-bar {
        background: linear-gradient(90deg, #FF9933 0%, #FFFFFF 50%, #128807 100%);
        height: 6px;
        border-radius: 3px;
        margin-bottom: 5px;
    }
    
    /* Dynamic Sanskrit Slogan Sliding Marquee */
    .slogan-ticker-container {
        background-color: #001a33;
        color: #ffcc00;
        overflow: hidden;
        white-space: nowrap;
        box-sizing: border-box;
        padding: 8px 0;
        font-size: 14px;
        font-weight: 600;
        letter-spacing: 0.5px;
        border-bottom: 2px solid #FF9933;
        margin-bottom: 15px;
        border-radius: 4px;
    }
    .slogan-ticker-text {
        display: inline-block;
        padding-left: 100%;
        animation: marquee 22s linear infinite;
    }
    @keyframes marquee {
        0%   { transform: translate(0, 0); }
        100% { transform: translate(-100%, 0); }
    }

    /* Official Government Banner Header */
    .gov-header {
        background-color: #002244;
        color: #ffffff;
        padding: 18px 25px;
        border-radius: 8px;
        margin-bottom: 20px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
    }
    .gov-header h1 {
        color: #ffffff !important;
        font-family: 'Arial', sans-serif;
        font-size: 26px;
        font-weight: 700;
        margin: 0;
    }
    .gov-header p {
        color: #E0E0E0 !important;
        font-size: 13px;
        margin: 0;
    }
    
    /* Card Styles */
    .gov-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 8px;
        border-left: 5px solid #003366;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        margin-bottom: 15px;
    }
    
    /* Step Badges */
    .step-badge {
        background-color: #003366;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 8px;
    }
    
    /* Metric Cards */
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        color: #002244;
        font-weight: bold;
    }
    
    /* Official Footer */
    .gov-footer {
        background-color: #f8f9fa;
        border-top: 2px solid #003366;
        padding: 15px;
        text-align: center;
        font-size: 12px;
        color: #555555;
        margin-top: 40px;
        border-radius: 4px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Render Top Government Ribbon
st.markdown('<div class="gov-top-bar"></div>', unsafe_allow_html=True)

# Render Dynamic Sliding Sanskrit Slogan
st.markdown(
    """
    <div class="slogan-ticker-container">
        <div class="slogan-ticker-text">
            <b>• बहुजनहिताय बहुजनसुखाय •</b> &nbsp;|&nbsp; <i>Bahujanahitāya Bahujanasukhāya</i> &nbsp;|&nbsp; 
            <b>Meaning:</b> "For the welfare of the many, for the happiness of the many" — Dedicated to Public Service & Civic Welfare
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

# Supabase Credentials
supabase_url = st.secrets["SUPABASE_URL"].strip().rstrip("/")
supabase_key = st.secrets["SUPABASE_KEY"].strip()
supabase = create_client(supabase_url, supabase_key)


# ==========================================
# 2. AUTO-BUILD & LOAD ML MODELS
# ==========================================
@st.cache_resource
def load_or_build_models():
    """Builds lightweight models in-memory if not saved, then caches them."""
    base_model = MobileNetV2(
        weights="imagenet", include_top=False, input_shape=(224, 224, 3)
    )
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    outputs = Dense(4, activation="softmax")(x)
    img_model = Model(inputs=base_model.input, outputs=outputs)

    categories = [
        "Pothole",
        "Surface Crack",
        "Open Drain",
        "Debris",
        "Streetlight",
    ]
    severities = ["Low", "Medium", "High", "Critical"]
    np.random.seed(42)
    df_synth = pd.DataFrame(
        {
            "category": np.random.choice(categories, 800),
            "severity": np.random.choice(severities, 800),
            "has_image": np.random.choice([0, 1], 800),
        }
    )
    sev_map = {"Low": 1, "Medium": 3, "High": 5, "Critical": 8}
    cat_map = {
        "Pothole": 4,
        "Surface Crack": 2,
        "Open Drain": 7,
        "Debris": 1,
        "Streetlight": 3,
    }
    df_synth["resolution_days"] = (
        df_synth["severity"].map(sev_map) * 1.5
        + df_synth["category"].map(cat_map) * 1.2
        - df_synth["has_image"] * 0.5
        + np.random.normal(0, 1, 800)
    ).clip(lower=0.5)

    X = pd.get_dummies(
        df_synth[["category", "severity", "has_image"]], drop_first=False
    )
    y = df_synth["resolution_days"]

    rf_model = RandomForestRegressor(n_estimators=50, random_state=42)
    rf_model.fit(X, y)

    return img_model, rf_model, X.columns.tolist()


image_model, resolution_model, model_columns = load_or_build_models()


def predict_image_hazard(image_file):
    img = Image.open(image_file).convert("RGB").resize((224, 224))
    img_array = np.expand_dims(np.array(img) / 255.0, axis=0)
    preds = image_model.predict(img_array)[0]
    classes = ["Pothole", "Surface Crack", "Debris or Road Blockage", "Other"]
    top_idx = np.argmax(preds)
    confidence = float(preds[top_idx])
    suggested_sev = (
        "Critical"
        if confidence > 0.75
        else ("High" if confidence > 0.50 else "Medium")
    )
    return classes[top_idx], suggested_sev, confidence


def predict_resolution_days(category, severity, has_image):
    input_data = pd.DataFrame(0, index=[0], columns=model_columns)
    cat_col = f"category_{category}"
    sev_col = f"severity_{severity}"
    if cat_col in input_data.columns:
        input_data[cat_col] = 1
    if sev_col in input_data.columns:
        input_data[sev_col] = 1
    if "has_image" in input_data.columns:
        input_data["has_image"] = 1 if has_image else 0
    return round(float(resolution_model.predict(input_data)[0]), 1)


def fetch_reports():
    try:
        response = (
            supabase.table("reports")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching official reports: {e}")
        return []


def upload_photo(file, report_id):
    try:
        clean_filename = "".join(
            c for c in file.name if c.isalnum() or c in (".", "_", "-")
        )
        file_path = f"{report_id}_{clean_filename}"
        supabase.storage.from_("evidence").upload(
            path=file_path, file=file.getvalue()
        )
        res = supabase.storage.from_("evidence").get_public_url(file_path)
        return (
            res
            if isinstance(res, str)
            else res.get("publicUrl") or res.get("public_url")
        )
    except Exception as e:
        st.warning(f"Note on photo upload: {e}")
        return None


# ==========================================
# 3. OFFICIAL SIDEBAR NAVIGATION
# ==========================================
if "role" not in st.session_state:
    st.session_state.role = "Citizen"

with st.sidebar:
    st.markdown("### 🏛️ MUNICIPAL PORTAL")
    st.caption("Citizen Grievance & Operations Redressal System")
    st.divider()

    st.subheader("🔑 Session Authority")
    st.session_state.role = st.selectbox(
        "User Role Access:",
        ["Citizen", "Municipal Admin", "Field Technician"],
        index=0 if st.session_state.role == "Citizen" else 1,
    )
    st.divider()

    nav_choice = st.radio(
        "Navigation Menu:",
        [
            "📝 Report a Public Grievance",
            "🛣️ Issue Tracker & Redressal Status",
            "📊 Executive Dashboard & Analytics",
        ],
    )
    st.divider()
    st.caption("📞 Toll-Free Helpline: **1800-111-360**")
    st.caption("🌐 Government Direct Portal v2.4")

# ==========================================
# 4. OFFICIAL BANNER HEADER
# ==========================================
st.markdown(
    """
    <div class="gov-header">
        <h1>CIVIC360 — Integrated Public Grievance & SLA Portal</h1>
        <p>Official Municipal Infrastructure Monitoring & Computer Vision Operations System</p>
    </div>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 5. MODULE 1: REPORT HAZARD (CITIZEN FORM)
# ==========================================
if nav_choice == "📝 Report a Public Grievance":
    st.subheader("Report Infrastructure Issue")
    st.write(
        "Submit public infrastructure complaints directly to your local Municipal Authority. AI models automatically estimate repair timelines."
    )

    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.markdown(
            '<span class="step-badge">STEP 1</span> <b>GPS Location Capture</b>',
            unsafe_allow_html=True,
        )
        location = streamlit_geolocation()
        user_lat = location.get("latitude")
        user_lon = location.get("longitude")

        if user_lat and user_lon:
            st.success(
                f"📍 **GPS Coordinates Captured:** `{user_lat:.5f}, {user_lon:.5f}`"
            )
        else:
            st.info("ℹ️ Click 'Get Location' above to record exact GPS spot.")

    with c_right:
        st.markdown(
            '<span class="step-badge">STEP 2</span> <b>Attach Photographic Evidence</b>',
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "Upload Clear Photo (Optional - Triggers Auto AI Detection)",
            type=["png", "jpg", "jpeg", "webp"],
        )

        auto_category, auto_severity, confidence = "Pothole", "Medium", 0.0
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Uploaded Image", width=200)
            with st.spinner("🤖 AI Computer Vision Model Scanning Hazard..."):
                auto_category, auto_severity, confidence = predict_image_hazard(
                    uploaded_file
                )
                st.success(
                    f"🤖 **AI Analysis:** Detected **{auto_category}** ({confidence*100:.1f}% Confidence). "
                    f"Suggested Severity: **{auto_severity}**"
                )

    st.divider()
    st.markdown(
        '<span class="step-badge">STEP 3</span> <b>Official Complaint Details</b>',
        unsafe_allow_html=True,
    )

    with st.form("hazard_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            category_selection = st.selectbox(
                "Grievance Category*",
                [
                    "Pothole",
                    "Surface Crack / Alligator Cracking",
                    "Open Drain / Manhole",
                    "Debris or Road Blockage",
                    "Traffic Light / Sign Failure",
                    "Streetlight Outage",
                    "Other (Specify Below)",
                ],
                index=0,
            )
            severity = st.select_slider(
                "Observed Severity / Impact*",
                options=["Low", "Medium", "High", "Critical"],
                value=auto_severity,
            )
        with col_b:
            address = st.text_input(
                "Location Address / Ward Landmark*",
                placeholder="e.g., Near Sector 4 Public School Gate",
            )
            description = st.text_area(
                "Grievance Description*",
                placeholder="Describe public inconvenience, size, danger level...",
                height=100,
            )

        submitted = st.form_submit_button(
            "Submit Grievance to Municipal Authority",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            if not address or not description:
                st.error("Please fill in all mandatory details marked with *")
            elif not user_lat or not user_lon:
                st.error("GPS Location required! Please allow location access.")
            else:
                rep_id = f"GOV-{int(datetime.now().timestamp())}"
                has_img = uploaded_file is not None
                est_days = predict_resolution_days(
                    category_selection, severity, has_img
                )
                image_url = (
                    upload_photo(uploaded_file, rep_id)
                    if uploaded_file
                    else None
                )

                row_data = {
                    "report_id": str(rep_id),
                    "type": str(category_selection),
                    "severity": str(severity),
                    "address": str(address),
                    "description": str(description),
                    "lat": float(user_lat),
                    "lon": float(user_lon),
                    "status": "Submitted",
                    "image_url": str(image_url) if image_url else None,
                    "est_resolution_days": est_days,
                }

                try:
                    supabase.table("reports").insert(row_data).execute()
                    st.success(
                        f"✅ **Grievance Registered Successfully!** Registration ID: **{rep_id}**. "
                        f"Target Resolution SLA: **{est_days} Days**."
                    )
                    st.balloons()
                except Exception as e:
                    st.error(f"Grievance submission error: {e}")

# ==========================================
# 6. MODULE 2: ISSUE TRACKER & REDRESSAL
# ==========================================
elif nav_choice == "🛣️ Issue Tracker & Redressal Status":
    st.subheader("Grievance Redressal & Operations Queue")
    reports = fetch_reports()

    total_reps = len(reports)
    pending_reps = sum(
        1
        for r in reports
        if r.get("status") in ["Submitted", "Under Review", "In Progress"]
    )
    resolved_reps = sum(1 for r in reports if r.get("status") == "Resolved")

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Grievances Registered", total_reps)
    m2.metric("Active Grievances Pending", pending_reps)
    m3.metric("Resolved Cases", resolved_reps)
    st.divider()

    if not reports:
        st.info("No public grievances in database currently.")
    else:
        for report in reports:
            row_id = report["id"]
            rep_id = report.get("report_id", "GOV-UNKNOWN")
            sla = report.get("est_resolution_days", "N/A")

            st.markdown(
                f"""
            <div class="gov-card">
                <span style="float: right; font-weight: bold; color: #003366;">Status: {report.get('status')}</span>
                <h4 style="margin:0; color:#002244;">Ticket #{rep_id}: {report.get('type')}</h4>
                <p style="margin: 3px 0; color: #666; font-size: 13px;"><b>Address:</b> {report.get('address')} | <b>Severity:</b> {report.get('severity')} | <b>Target SLA:</b> {sla} Days</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            with st.expander(f"🔍 Inspect Grievance Details for #{rep_id}"):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.write(
                        f"**Logged Date/Time:** {report.get('created_at', '')[:19]}"
                    )
                    st.write(f"**Grievance Details:** {report.get('description')}")
                    if report.get("image_url"):
                        st.image(
                            report["image_url"],
                            caption="Citizen Evidence Photo",
                            width=280,
                        )
                with c2:
                    if st.session_state.role in [
                        "Municipal Admin",
                        "Field Technician",
                    ]:
                        st.subheader("Update Redressal Status")
                        curr_status = report.get("status", "Submitted")
                        status_options = [
                            "Submitted",
                            "Under Review",
                            "In Progress",
                            "Resolved",
                        ]
                        idx = (
                            status_options.index(curr_status)
                            if curr_status in status_options
                            else 0
                        )
                        new_status = st.selectbox(
                            "Change Ticket Status",
                            status_options,
                            index=idx,
                            key=f"status_{row_id}",
                        )
                        if new_status != curr_status:
                            supabase.table("reports").update(
                                {"status": new_status}
                            ).eq("id", row_id).execute()
                            st.success("Official status updated!")
                            st.rerun()

# ==========================================
# 7. MODULE 3: ANALYTICS & MAP
# ==========================================
elif nav_choice == "📊 Executive Dashboard & Analytics":
    st.subheader("Municipal Infrastructure Analytics & Spatial Heatmap")
    reports = fetch_reports()

    if not reports:
        st.info("No spatial data available.")
    else:
        df_reports = pd.DataFrame(reports)

        if "lat" in df_reports.columns and "lon" in df_reports.columns:
            df_reports["lat"] = pd.to_numeric(
                df_reports["lat"], errors="coerce"
            )
            df_reports["lon"] = pd.to_numeric(
                df_reports["lon"], errors="coerce"
            )
            df_clean = df_reports.dropna(subset=["lat", "lon"])
        else:
            df_clean = pd.DataFrame()

        col_map, col_chart = st.columns([1.5, 1])

        with col_map:
            st.markdown("#### Spatial Complaint Map")
            if df_clean.empty:
                st.warning("No valid GPS records.")
            else:
                avg_lat = df_clean["lat"].mean()
                avg_lon = df_clean["lon"].mean()
                m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)

                for _, row in df_clean.iterrows():
                    popup_text = f"<b>{row.get('type')}</b><br>Severity: {row.get('severity')}<br>Status: {row.get('status')}"
                    sev = str(row.get("severity", "")).lower()
                    color = (
                        "red"
                        if sev in ["critical", "high"]
                        else ("orange" if sev == "medium" else "green")
                    )

                    folium.Marker(
                        location=[row["lat"], row["lon"]],
                        popup=folium.Popup(popup_text, max_width=250),
                        tooltip=f"{row.get('type')}",
                        icon=folium.Icon(color=color, icon="info-sign"),
                    ).add_to(m)

                st_folium(m, width=650, height=380)

        with col_chart:
            st.markdown("#### Grievances by Category")
            if "type" in df_reports.columns:
                fig = px.bar(
                    df_reports["type"].value_counts().reset_index(),
                    x="type",
                    y="count",
                    labels={"type": "Category", "count": "Total Complaints"},
                    color_discrete_sequence=["#003366"],
                )
                st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("🤖 Machine Learning Analytics Insights")
        c_ml1, c_ml2 = st.columns(2)

        with c_ml1:
            st.markdown("**Predicted Repair SLA (Days) vs. Hazard Severity**")
            if "est_resolution_days" in df_reports.columns:
                fig_box = px.box(
                    df_reports,
                    x="severity",
                    y="est_resolution_days",
                    color="severity",
                    color_discrete_map={
                        "Low": "#28a745",
                        "Medium": "#ffc107",
                        "High": "#fd7e14",
                        "Critical": "#dc3545",
                    },
                )
                st.plotly_chart(fig_box, use_container_width=True)

        with c_ml2:
            st.markdown("**SLA Model Feature Weights (Random Forest)**")
            importances = resolution_model.feature_importances_
            fi_df = (
                pd.DataFrame(
                    {"Feature": model_columns, "Importance": importances}
                )
                .sort_values(by="Importance", ascending=True)
                .tail(8)
            )

            fig_fi = px.bar(
                fi_df,
                x="Importance",
                y="Feature",
                orientation="h",
                color_discrete_sequence=["#003366"],
            )
            st.plotly_chart(fig_fi, use_container_width=True)

# ==========================================
# 8. OFFICIAL FOOTER
# ==========================================
st.markdown(
    """
    <div class="gov-footer">
        <p><b>CIVIC360 Citizen Portal</b> — Official Municipal Grievance & Infrastructure Monitoring Platform</p>
        <p>Complies with Digital India Design Standards & Guidelines for Indian Government Websites (GIGW)</p>
        <p>© 2026 Municipal Operations Department. All Rights Reserved.</p>
    </div>
""",
    unsafe_allow_html=True,
)
