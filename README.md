# Route Planner - Address Mapper

A simple, clean Streamlit web app that lets users upload a list of addresses (or enter them manually) and instantly see them plotted on an interactive map. Built as a portfolio project to demonstrate practical Python + GIS skills.

The app is intentionally designed to be **very easy to use** — especially for small business owners who may not be comfortable with spreadsheets or complex software.

---

## What It Does

- Upload a CSV or Excel file containing addresses → automatically geocodes them and plots them on a map
- Manually enter addresses one by one (supports both a simple "Full Address" field and traditional broken-out fields)
- Shows clean **solid blue markers** on an interactive map
- Displays the **Name** (if provided) when hovering over or clicking a point
- Works reasonably well internationally by recommending a single "Full Address" column
- Built with session state so the map persists as you interact with the app

---

## Tech Stack

- **Python**
- **Streamlit** (UI)
- **pandas** (data handling)
- **folium + streamlit-folium** (interactive maps)
- **geopy** (geocoding via Nominatim / OpenStreetMap)

---

## How to Run Locally

1. Clone or download this folder
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate          # Mac / Linux
   # OR
   venv\Scripts\activate             # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the app:
   ```bash
   streamlit run map.py
   ```

The app will open in your browser at `http://localhost:8501`

---

## How to Use

### Upload Tab (Recommended for lists)

1. Prepare a CSV or Excel file with your addresses.
2. Upload it using the file uploader.
3. The app will try to automatically detect your address column(s).
4. Click **"Plot Addresses on Map"**.

**Recommended CSV format (most flexible):**

| Name (optional) | Full Address                          |
|-----------------|---------------------------------------|
| Union Station   | 1701 Wynkoop St, Denver, CO 80202     |
| Red Rocks       | 18300 W Alameda Pkwy, Morrison, CO 80465 |

You can also use separate columns and the app will combine them:

`Name, Address, City, State, Zip`

The app is smart enough to handle both styles.

### Manual Entry Tab

- Use the main **Full Address** field for quickest entry (works best internationally).
- Or expand **"Advanced: Enter by separate fields (US-style)"** if you prefer breaking it out.
- Click **Add Address** to add it to the list.
- Click **Plot All on Map** when you're ready.

---

## Current Features

- Clean, minimal interface
- Supports CSV and Excel uploads
- Smart column detection (handles full address or split columns)
- Manual address entry with name support
- Interactive map with solid blue markers
- Name appears on hover (tooltip) and click (popup)
- Session state so the map doesn't disappear
- Clear Map button
- Basic error handling and user feedback
- International-friendly design (Full Address recommended)

---

## Future Plans / Roadmap

- Numbered markers on the map
- Download geocoded results as CSV
- Route optimization (using Google OR-Tools)
- Multiple route splitting for crews/vehicles
- User accounts + Stripe payments (Pro tier)
- Better mobile experience
- Dark mode / improved styling

---

## Notes for Portfolio Use

This project demonstrates:

- Practical use of Streamlit for rapid web app development
- Working with real-world messy data (address parsing)
- Geocoding and mapping libraries
- Clean UI/UX thinking for non-technical users
- Session state management in Streamlit
- Building something with future monetization potential

---

## License

This is a personal/portfolio project. Feel free to use the code as reference or starting point for your own projects.

---

Built with ❤️ by Paul Depperschmidt (2026)