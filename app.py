# ==========================================
# MODULE 1: REPORT HAZARD (LIVE GPS + CUSTOM HAZARD)
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
            # Preset categories + "Other" option
            category_selection = st.selectbox(
                "Hazard Classification*",
                [
                    "Pothole",
                    "Surface Crack / Alligator Cracking",
                    "Open Drain / Manhole",
                    "Debris or Road Blockage",
                    "Traffic Light / Sign Failure",
                    "Streetlight Outage",
                    "Other (Specify Below)",  # Custom hazard trigger
                ],
            )

            # Dynamic field for custom hazard input
            custom_category = ""
            if category_selection == "Other (Specify Below)":
                custom_category = st.text_input(
                    "Custom Hazard Type*",
                    placeholder="e.g. Water Main Leak, Fallen Tree Branch",
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
            # Determine final category label
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

                # Save new report directly to active database
                new_report = {
                    "id": report_id,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "type": final_category,
                    "severity": severity,
                    "priority_score": p_scores[severity],
                    "dept": dept_map.get(
                        final_category, "General Administration"
                    ),
                    "status": "Submitted",
                    "address": address,
                    "lat": user_lat,
                    "lon": user_lon,
                    "description": description,
                }

                st.session_state.reports_db.insert(0, new_report)
                st.success(
                    f"Report **{report_id}** ({final_category}) successfully dispatched to **{new_report['dept']}**!"
                )
                st.balloons()
