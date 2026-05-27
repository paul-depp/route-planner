import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

st.set_page_config(page_title="Route Planner", layout="centered")
st.title("Route Planner - Address Mapper")

if "locations" not in st.session_state:
    st.session_state.locations = []

# ===================== CACHED GEOCODING =====================
@st.cache_data(show_spinner=False, ttl=3600)  # Cache results for 1 hour
def geocode_address(address: str):
    """Geocode a single address. Results are cached to reduce API calls and avoid rate limits."""
    try:
        geolocator = Nominatim(user_agent="csv-mapper-v4-streamlit", timeout=8)
        result = geolocator.geocode(address)
        if result:
            return {"lat": result.latitude, "lon": result.longitude}
        return None
    except Exception:
        return None


# ===================== TABS =====================
tab1, tab2 = st.tabs(["📁 Upload CSV / Excel", "✍️ Enter Addresses Manually"])

# ===================== TAB 1: Upload =====================
with tab1:
    st.markdown("""
    ### Recommended CSV / Excel Format (works worldwide)

    **Best option:** One column called **Full Address** containing the complete address.  
    This works best internationally.

    **Also supported:** Separate columns for Address + City + State/Province + Postal Code  
    (The app will automatically combine them)

    **You can also include a Name column** — it will appear when you hover over points on the map.

    **Example of ideal format:**
    ```
    Name,Full Address
    Union Station,1701 Wynkoop St, Denver, CO 80202, USA
    Red Rocks Amphitheatre,18300 W Alameda Pkwy, Morrison, CO 80465, USA
    ```

    **Note:** The free geocoding service (Nominatim) can be slow or temporarily unavailable on Streamlit Cloud. 
    If it fails, try again in a minute or use fewer addresses.
    """)

    uploaded_file = st.file_uploader("Upload your CSV or Excel file", type=["csv", "xlsx"])

    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        total_rows = len(df)
        st.write(f"**Preview of your uploaded file** — {total_rows} addresses found")

        # Show full dataframe with scrolling (much better UX than head(8))
        st.dataframe(df, use_container_width=True, height=320)

        # Smart column detection
        cols_lower = {c.lower().strip(): c for c in df.columns}

        name_col = next((orig for key, orig in cols_lower.items() 
                        if any(x in key for x in ['name', 'stop', 'customer', 'client'])), None)
        address_col = next((orig for key, orig in cols_lower.items() 
                           if any(x in key for x in ['address', 'street', 'full address', 'location'])), None)
        city_col = next((orig for key, orig in cols_lower.items() if 'city' in key), None)
        state_col = next((orig for key, orig in cols_lower.items() 
                          if any(x in key for x in ['state', 'province'])), None)
        zip_col = next((orig for key, orig in cols_lower.items() 
                        if any(x in key for x in ['zip', 'postal', 'cep', 'postcode'])), None)
        country_col = next((orig for key, orig in cols_lower.items() if 'country' in key), None)

        # Auto-combine separate address columns into one
        if address_col and (city_col or state_col):
            def build_full_address(row):
                parts = []
                for col in [address_col, city_col, state_col, zip_col, country_col]:
                    if col and pd.notna(row.get(col)):
                        val = str(row[col]).replace('.0', '').strip()  # Fix float zip issue
                        if val:
                            parts.append(val)
                return ", ".join(parts)

            df['Full Address'] = df.apply(build_full_address, axis=1)
            address_col = 'Full Address'
            st.info("Detected separate address columns → automatically combined them into a full address.")

        if address_col is None:
            address_col = st.selectbox("Which column contains the addresses?", df.columns)

        if st.button("Plot Addresses on Map", key="upload_btn"):
            with st.spinner("Geocoding addresses... (this can take 15–60 seconds)"):
                new_locations = []
                failed = []

                for idx, row in df.iterrows():
                    name_val = str(row[name_col]).strip() if name_col and pd.notna(row.get(name_col)) else ""
                    addr_val = str(row[address_col]).replace('.0', '').strip() if address_col and pd.notna(row.get(address_col)) else ""

                    if not addr_val:
                        continue

                    result = geocode_address(addr_val)

                    if result:
                        new_locations.append({
                            "name": name_val,
                            "address": addr_val,
                            "lat": result["lat"],
                            "lon": result["lon"]
                        })
                    else:
                        failed.append(addr_val)

                st.session_state.locations = new_locations

                if new_locations:
                    st.success(f"Successfully plotted {len(new_locations)} addresses!")
                else:
                    st.error("No addresses could be geocoded. The free service is currently overloaded or blocking requests from Streamlit Cloud. Try again in a minute.")

                if failed:
                    st.warning(f"Failed to geocode {len(failed)} addresses. Try again later or reduce the number of addresses.")

# ===================== TAB 2: Manual Entry =====================
with tab2:
    st.write("Add addresses one by one:")

    col1, col2 = st.columns([3, 2])
    with col1:
        manual_address = st.text_input("Full Address", placeholder="1701 Wynkoop St, Denver, CO 80202, USA")
    with col2:
        manual_name = st.text_input("Name / Label (optional)")

    if st.button("Add Address", key="manual_add"):
        if manual_address.strip():
            st.session_state.locations.append({
                "name": manual_name.strip(),
                "address": manual_address.strip(),
                "lat": None,
                "lon": None
            })
            st.success(f"Added: {manual_address}")
        else:
            st.warning("Please enter an address.")

    if st.session_state.locations:
        st.write("**Current addresses in list:**")
        for i, loc in enumerate(st.session_state.locations, 1):
            display = f"{loc['name']} — {loc['address']}" if loc['name'] else loc['address']
            st.write(f"{i}. {display}")

    if st.button("Plot All on Map", key="manual_plot_btn"):
        with st.spinner("Geocoding addresses..."):
            for loc in st.session_state.locations:
                if loc["lat"] is None:
                    result = geocode_address(loc["address"])
                    if result:
                        loc["lat"] = result["lat"]
                        loc["lon"] = result["lon"]

            st.session_state.locations = [loc for loc in st.session_state.locations if loc["lat"] is not None]
            st.success("Map updated!")

# ===================== MAP DISPLAY =====================
if st.session_state.locations:
    st.divider()
    st.subheader("Map View")

    valid = [loc for loc in st.session_state.locations if loc["lat"]]

    if valid:
        first = valid[0]
        m = folium.Map(location=[first["lat"], first["lon"]], zoom_start=11)

        for loc in valid:
            label = f"{loc['name']} — {loc['address']}" if loc['name'] else loc['address']
            folium.CircleMarker(
                location=[loc["lat"], loc["lon"]],
                radius=7,
                color="#2E86AB",
                fill=True,
                fill_color="#2E86AB",
                fill_opacity=0.85,
                popup=label,
                tooltip=label
            ).add_to(m)

        st_folium(m, width=900, height=550)

        if st.button("Clear Map", type="secondary"):
            st.session_state.locations = []
            st.rerun()
    else:
        st.info("No addresses have been successfully geocoded yet.")
