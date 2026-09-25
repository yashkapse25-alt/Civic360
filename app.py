from datetime import datetime
import joblib
import numpy as np
from PIL import Image
import pandas as pd
import plotly.express as px
from sklearn.ensemble import RandomForestRegressor
import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from supabase import create_client
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.models import Model
from streamlit_folium import st_folium
import folium
# ==========================================
# 1. PAGE CONFIG & SUPABASE SETUP
# ==========================================
st.set_page_config(
    page_title="Civic360 | Live AI Municipal Operations",
    page_icon="🌀",
    layout="wide",
)

supabase_url = st.secrets["SUPABASE_URL"].strip().rstrip("/")
supabase_key = st.secrets["SUPABASE_KEY"].strip()
supabase = create_client(supabase_url, supabase_key)


# ==========================================
# 2. AUTO-BUILD & LOAD ML MODELS
# ==========================================
@st.cache_resource
def load_or_build_models():
    """Builds lightweight models in-memory if not saved, then caches them."""
    # 1. Build MobileNetV2 Image Model
    base_model = MobileNetV2(
        weights="imagenet", include_top=False, input_shape=(224, 224, 3)
    )
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    outputs = Dense(4, activation="softmax")(x)
    img_model = Model(inputs=base_model.input, outputs=outputs)

    # 2. Train Random Forest Resolution Model
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
        st.error(f"Error fetching reports: {e}")
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
        st.warning(f"Image upload note: {e}")
        return None


# ==========================================
# 3. SIDEBAR NAVIGATION
# ==========================================
if "role" not in st.session_state:
    st.session_state.role = "Citizen"

with st.sidebar:
    st.title("🌀 CIVIC360 AI")
    st.caption("Smart Municipal Operations Portal")
    st.divider()
    st.subheader("Access Control")
    st.session_state.role = st.selectbox(
        "Current Session Role:",
        ["Citizen", "Municipal Admin", "Field Technician"],
        index=0 if st.session_state.role == "Citizen" else 1,
    )
    st.divider()
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
# 4. MODULE 1: REPORT HAZARD (WITH AI)
# ==========================================
if nav_choice == "📷 Report Hazard":
    st.header("Report Infrastructure Issue")
    st.caption("AI-assisted verification powered by MobileNetV2 & Random Forest.")

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
            "⚠️ Location not captured yet. Grant permissions and click 'Get Location'."
        )

    st.divider()
    uploaded_file = st.file_uploader(
        "Attach Photographic Proof (Triggers AI Detection)",
        type=["png", "jpg", "jpeg", "webp"],
    )

    auto_category, auto_severity, confidence = "Pothole", "Medium", 0.0
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Verification Photo", width=250)
        with st.spinner("🤖 AI Engine Analyzing Hazard..."):
            auto_category, auto_severity, confidence = predict_image_hazard(
                uploaded_file
            )
            st.info(
                f"🤖 **AI Analysis Complete:** Detected **{auto_category}** "
                f"with **{confidence*100:.1f}% Confidence**. Suggested Severity: **{auto_severity}**"
            )

    with st.form("hazard_form", clear_on_submit=True):
        st.subheader("2. Hazard Details & Operational Data")
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
                index=0,
            )
            severity = st.select_slider(
                "Observed Severity*",
                options=["Low", "Medium", "High", "Critical"],
                value=auto_severity,
            )
        with col_b:
            address = st.text_input(
                "Street Address / Landmark*",
                placeholder="e.g. Opposite City Hospital",
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
            if not address or not description:
                st.error("Please fill in all required fields marked with *")
            elif not user_lat or not user_lon:
                st.error("GPS coordinates missing! Capture location first.")
            else:
                rep_id = f"REP-{int(datetime.now().timestamp())}"
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
                        f"✅ Report **{rep_id}** Submitted! ML Predicted Resolution SLA: **{est_days} Days**"
                    )
                    st.balloons()
                except Exception as e:
                    st.error(f"Database save error: {e}")

# ==========================================
# 5. MODULE 2: ISSUE TRACKER & OPERATIONS
# ==========================================
elif nav_choice == "🛣️ Issue Tracker & Operations":
    st.header("Municipal Operations Dashboard")
    reports = fetch_reports()

    total_reps = len(reports)
    pending_reps = sum(
        1
        for r in reports
        if r.get("status") in ["Submitted", "Under Review", "In Progress"]
    )
    resolved_reps = sum(1 for r in reports if r.get("status") == "Resolved")

    m1, m2, m3 = st.columns(3)
    m1.metric("Live Logged Tickets", total_reps)
    m2.metric("Active Queue", pending_reps)
    m3.metric("Resolved", resolved_reps)
    st.divider()

    if not reports:
        st.info("No live reports in database yet.")
    else:
        for report in reports:
            row_id = report["id"]
            rep_id = report.get("report_id", "REP-UNKNOWN")
            sla = report.get("est_resolution_days", "N/A")

            with st.expander(
                f"**[{rep_id}] {report.get('type')}** — {report.get('address')} | SLA: {sla} Days ({report.get('status')})"
            ):
                c1, c2, c3 = st.columns([2, 2, 2])
                with c1:
                    st.write(f"**Logged At:** {report.get('created_at', '')[:16]}")
                    st.write(f"**Address:** {report.get('address')}")
                with c2:
                    st.write(f"**Severity:** {report.get('severity')}")
                    st.write(f"**Predicted Repair Time:** `{sla} Days`")
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
                        idx = (
                            status_options.index(curr_status)
                            if curr_status in status_options
                            else 0
                        )
                        new_status = st.selectbox(
                            "Update Status",
                            status_options,
                            index=idx,
                            key=f"status_{row_id}",
                        )
                        if new_status != curr_status:
                            supabase.table("reports").update(
                                {"status": new_status}
                            ).eq("id", row_id).execute()
                            st.success("Status updated!")
                            st.rerun()

                st.markdown("---")
                st.write(f"**Description:** {report.get('description')}")
                if report.get("image_url"):
                    st.image(
                        report["image_url"],
                        caption="Cloud Evidence Photo",
                        width=300,
                    )

# ==========================================
# 6. MODULE 3: ANALYTICS & VISUALIZATION
# ==========================================
elif nav_choice == "📊 Analytics & Spatial Heatmap":
    st.header("Real-Time Analytics & ML Insights")
    reports = fetch_reports()

    if not reports:
        st.info("No spatial data available in database.")
    else:
        df_reports = pd.DataFrame(reports)

        # ----------------------------------------------------
        # DATA CLEANING: Ensure lat/lon exist and are numeric
        # ----------------------------------------------------
        if "lat" in df_reports.columns and "lon" in df_reports.columns:
            df_reports["lat"] = pd.to_numeric(df_reports["lat"], errors="coerce")
            df_reports["lon"] = pd.to_numeric(df_reports["lon"], errors="coerce")
            df_clean = df_reports.dropna(subset=["lat", "lon"])
        else:
            df_clean = pd.DataFrame()

        col_map, col_chart = st.columns([1.5, 1])

        with col_map:
            st.subheader("Live Spatial Coordinates Map")
            if df_clean.empty:
                st.warning("⚠️ No valid GPS coordinates available in database records.")
            else:
                # Center map around average coordinates
                avg_lat = df_clean["lat"].mean()
                avg_lon = df_clean["lon"].mean()

                m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)

                # Add interactive markers for each report
                for _, row in df_clean.iterrows():
                    popup_text = f"<b>{row.get('type', 'Hazard')}</b><br>Severity: {row.get('severity', 'N/A')}<br>Status: {row.get('status', 'N/A')}"
                    
                    # Color-code pin based on severity
                    sev = str(row.get("severity", "")).lower()
                    color = "red" if sev in ["critical", "high"] else ("orange" if sev == "medium" else "green")

                    folium.Marker(
                        location=[row["lat"], row["lon"]],
                        popup=folium.Popup(popup_text, max_width=250),
                        tooltip=f"{row.get('type')} ({row.get('severity')})",
                        icon=folium.Icon(color=color, icon="info-sign")
                    ).add_to(m)

                st_folium(m, width=650, height=400)

        with col_chart:
            st.subheader("Submissions by Classification")
            if "type" in df_reports.columns:
                fig = px.bar(
                    df_reports["type"].value_counts().reset_index(),
                    x="type",
                    y="count",
                    labels={"type": "Hazard Type", "count": "Report Count"},
                    color="count",
                    color_continuous_scale="Viridis",
                )
                st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # ML Insights Section
        st.subheader("🤖 Machine Learning Model Insights")
        c_ml1, c_ml2 = st.columns(2)

        with c_ml1:
            st.markdown("**Resolution SLA Distribution by Hazard Severity**")
            if "est_resolution_days" in df_reports.columns:
                fig_box = px.box(
                    df_reports,
                    x="severity",
                    y="est_resolution_days",
                    color="severity",
                    points="all",
                )
                st.plotly_chart(fig_box, use_container_width=True)

        with c_ml2:
            st.markdown("**Model Feature Importance (Random Forest)**")
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
                color="Importance",
            )
            st.plotly_chart(fig_fi, use_container_width=True)
