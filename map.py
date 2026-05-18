import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

st.set_page_config(page_title="Route Planner", layout="centered")
st.title("Route Planner - Address Mapper")

# Session state
if "locations" not in st.session_state:
    st.session_state.locations = []

# ===================== TABS =====================
tab1, tab2 = st.tabs(["📁 Upload CSV / Excel", "✍️ Enter Addresses Manually"])

# ===================== TAB 1: Upload =====================
with tab1:
    st.markdown("""
    ### Recommended CSV / Excel Format (works worldwide)

    **Best option:** One column containing the **full address**  
    (This works best for addresses outside the United States)

    **Also supported:** Separate columns for Address + City + State/Province + Postal Code  
    (The app will automatically combine them)

    **You can also include a Name column** — it will appear when you hover over points on the map.

    **Example of ideal format:**
    ```
    Name,Full Address
    Union Station,1701 Wynkoop St, Denver, CO 80202, USA
    Red Rocks Amphitheatre,18300 W Alameda Pkwy, Morrison, CO 80465, USA
    ```

    The more complete the address you provide, the better the results will be.
    """)

    uploaded_file = st.file_uploader(
        "Upload your CSV or Excel file", 
        type=["csv", "xlsx"]
    )

    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.write("**Preview of your uploaded file:**")
        st.dataframe(df.head(8))

        # === Smart column detection ===
        cols_lower = {c.lower().strip(): c for c in df.columns}

        name_col = None
        address_col = None
        city_col = None
        state_col = None
        zip_col = None
        country_col = None

        for key, original in cols_lower.items():
            if not name_col and any(x in key for x in ['name', 'location name', 'stop', 'customer', 'client']):
                name_col = original
            if not address_col and any(x in key for x in ['address', 'street', 'full address', 'location']):
                address_col = original
            if not city_col and 'city' in key:
                city_col = original
            if not state_col and any(x in key for x in ['state', 'province', 'st']):
                state_col = original
            if not zip_col and any(x in key for x in ['zip', 'postal', 'cep', 'postcode']):
                zip_col = original
            if not country_col and any(x in key for x in ['country', 'nation']):
                country_col = original

        # If we have separate Address + City + State, combine them automatically
        if address_col and (city_col or state_col):
            def build_full_address(row):
                parts = []
                if address_col and pd.notna(row.get(address_col)):
                    parts.append(str(row[address_col]).strip())
                if city_col and pd.notna(row.get(city_col)):
                    parts.append(str(row[city_col]).strip())
                if state_col and pd.notna(row.get(state_col)):
                    parts.append(str(row[state_col]).strip())
                if zip_col and pd.notna(row.get(zip_col)):
                    parts.append(str(row[zip_col]).strip())
                if country_col and pd.notna(row.get(country_col)):
                    parts.append(str(row[country_col]).strip())
                return ", ".join(parts)

            df['Full Address'] = df.apply(build_full_address, axis=1)
            address_col = 'Full Address'
            st.info("Detected separate address columns → automatically combined them into a full address.")

        if address_col is None:
            st.warning("Couldn't automatically detect an address column.")
            address_col = st.selectbox("Which column contains the addresses?", df.columns)

        if st.button("Plot Addresses on Map", key="upload_btn"):
            with st.spinner("Geocoding addresses... (this can take 10–30 seconds)"):
                geolocator = Nominatim(user_agent="route_planner_v7")
                geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.1)

                new_locations = []

                for idx, row in df.iterrows():
                    # Get name if available
                    name_val = ""
                    if name_col and pd.notna(row.get(name_col)):
                        name_val = str(row[name_col]).strip()

                    # Get address
                    addr_val = ""
                    if address_col and pd.notna(row.get(address_col)):
                        addr_val = str(row[address_col]).strip()

                    if not addr_val:
                        continue

                    try:
                        result = geocode(addr_val)
                        if result:
                            new_locations.append({
                                "name": name_val,
                                "address": addr_val,
                                "lat": result.latitude,
                                "lon": result.longitude
                            })
                    except Exception as e:
                        st.warning(f"Could not geocode: {addr_val}")

                st.session_state.locations = new_locations
                st.success(f"Successfully plotted {len(new_locations)} addresses!")

# ===================== TAB 2: Manual Entry =====================
with tab2:
    st.markdown("""
    **Enter addresses manually**

    For best international support, enter the **complete address** in one line.
    The **Name** field is optional but recommended — it will show when hovering over the point on the map.
    """)

    # === Primary: Full Address input (recommended for international use) ===
    full_address_input = st.text_input(
        "Full Address",
        placeholder="1701 Wynkoop St, Denver, CO 80202, USA",
        help="Enter the complete address. This works best worldwide."
    )

    man_name = st.text_input("Name / Label (optional)", placeholder="e.g. Union Station")

    if st.button("Add Address", key="manual_add"):
        if full_address_input.strip():
            st.session_state.locations.append({
                "name": man_name.strip(),
                "address": full_address_input.strip(),
                "lat": None,
                "lon": None
            })
            display_text = f"{man_name} — {full_address_input}" if man_name else full_address_input
            st.success(f"Added: {display_text}")
        else:
            st.warning("Please enter a full address.")

    # Optional: Advanced broken-out fields (collapsed)
    with st.expander("Advanced: Enter by separate fields (US-style)"):
        col1, col2 = st.columns(2)
        with col1:
            adv_name = st.text_input("Name (optional)", key="adv_name")
            adv_street = st.text_input("Street Address", key="adv_street")
        with col2:
            adv_city = st.text_input("City", key="adv_city")
            adv_state = st.text_input("State / Province", key="adv_state")
            adv_zip = st.text_input("Postal Code", key="adv_zip")

        if st.button("Add using separate fields", key="adv_add"):
            if adv_street and adv_city:
                parts = [adv_street.strip(), adv_city.strip()]
                if adv_state:
                    parts.append(adv_state.strip())
                if adv_zip:
                    parts.append(adv_zip.strip())
                full = ", ".join(parts)

                st.session_state.locations.append({
                    "name": adv_name.strip(),
                    "address": full,
                    "lat": None,
                    "lon": None
                })
                display_text = f"{adv_name} — {full}" if adv_name else full
                st.success(f"Added: {display_text}")
            else:
                st.warning("Street and City are required when using separate fields.")

    # Show current list
    if st.session_state.locations:
        st.write("**Addresses added so far:**")
        for i, loc in enumerate(st.session_state.locations, 1):
            name_part = loc.get("name", "")
            addr_part = loc.get("address", "")
            if name_part:
                st.write(f"{i}. **{name_part}** — {addr_part}")
            else:
                st.write(f"{i}. {addr_part}")

    if st.button("Plot All on Map", key="manual_plot_btn"):
        with st.spinner("Geocoding addresses..."):
            geolocator = Nominatim(user_agent="route_planner_v7")
            geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.1)

            for loc in st.session_state.locations:
                if loc["lat"] is None:
                    try:
                        res = geocode(loc["address"])
                        if res:
                            loc["lat"] = res.latitude
                            loc["lon"] = res.longitude
                    except:
                        pass

            st.session_state.locations = [loc for loc in st.session_state.locations if loc["lat"]]
            st.success("Map updated!")

# ===================== MAP DISPLAY =====================
if st.session_state.locations:
    st.divider()
    st.subheader("Map View")

    valid = [loc for loc in st.session_state.locations if loc.get("lat")]

    if valid:
        first = valid[0]
        m = folium.Map(location=[first["lat"], first["lon"]], zoom_start=11)

        for loc in valid:
            name = loc.get("name", "").strip()
            address = loc.get("address", "")

            if name:
                tooltip_text = f"{name} — {address}"
                popup_html = f"<b>{name}</b><br>{address}"
            else:
                tooltip_text = address
                popup_html = address

            folium.CircleMarker(
                location=[loc["lat"], loc["lon"]],
                radius=7,
                color="#2E86AB",
                fill=True,
                fill_color="#2E86AB",
                fill_opacity=0.85,
                popup=popup_html,
                tooltip=tooltip_text
            ).add_to(m)

        st_folium(m, width=900, height=550)

        if st.button("Clear Map", type="secondary"):
            st.session_state.locations = []
            st.rerun()
    else:
        st.info("No addresses have been successfully geocoded yet.")
