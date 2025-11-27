# Umamusume Champion's Meeting Dashboard 🏆

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat&logo=plotly&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

### **Project Overview**

This is a comprehensive data analytics and visualization suite designed for the **Moomoocows Umamusume Community**. It aggregates player-submitted data from Google Forms (CSV) and OCR-scanned build data (Parquet) to provide deep insights into the "Champion's Meeting" (CM) meta.

The dashboard helps players understand what works by analyzing win rates against stats, skills, and team compositions.

**🔗 Live Dashboard:** [https://moomamusumedashboard.streamlit.app/]

---

### **✨ Key Features**

#### **1. 🌍 Global Overview**
* **Live Metrics:** Track total races, average win rates, and active trainer counts.
* **Leaderboards:** dynamic ranking of top trainers using a weighted score (Win Rate × Log Volume).
* **Economy Analysis:** Visualizes the "Pay-to-Win" factor by comparing win rates across spending tiers (F2P vs. Whales).

#### **2. 🔮 OCR Meta Analysis (New!)**
A powerful engine that links raw character build data (Stats/Skills) to actual race performance.
* **Stat Optimization:** Compare the average Speed, Power, and Guts of "Winning Builds" (Top 25% WR) vs. the global average.
* **Skill Lift:** Identifies "Meta Skills" by calculating which skills appear disproportionately often in winning decks.
* **Aptitude Impact:** Definitively answers whether **S-Rank** Distances or Turf aptitudes actually improve win rates.
* **Smart Matching:** Automatically maps OCR text (e.g., "[Summer] Maruzensky") to standardized game data.

#### **3. ⚔️ Team & Strategy**
* **Meta Compositions:** Identifies the strongest 3-Uma team combinations.
* **Style Analysis:** Break down win rates by running strategy (Runner, Leader, Betweener, Chaser).
* **Runaway Impact:** Analyzes the necessity of having a "Runaway" (Nigeru) to control the race pace.

#### **4. 📚 Interactive Guides**
* Integrated, high-resolution track guides and tier lists with zoom and pan capabilities.

---

### **🛠️ Technical Stack**

* **Core:** [Streamlit](https://streamlit.io/)
* **Visualization:** [Plotly Express](https://plotly.com/python/plotly-express/)
* **Data Manipulation:** [Pandas](https://pandas.pydata.org/) & [NumPy](https://numpy.org/)
* **Storage:** Google Sheets (CSV export) & Parquet (OCR data)


---

### **🚀 Installation & Usage**

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/ZuseGD/Umamusume_Virgo_Cup_Dashboard.git](https://github.com/ZuseGD/Umamusume_Virgo_Cup_Dashboard.git)
    cd Umamusume_Virgo_Cup_Dashboard
    ```

2.  **Create a virtual environment (Optional but recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Data:**
    * Ensure `cm_config.py` points to the correct Google Sheet CSV URL.
    * Place your OCR data file (e.g., `r2d2.parquet`) in the `data/` folder.

5.  **Run the dashboard:**
    ```bash
    streamlit run dashboard.py
    ```

---

### **📂 Project Structure**

```text
├── dashboard.py          # Main entry point
├── cm_config.py          # Configuration for different CM events (Virgo, Libra, etc.)
├── virgo_utils.py        # Helper functions for data cleaning and calculations
├── views/                # Page modules
│   ├── home.py           # Landing page & Leaderboards
│   ├── ocr.py            # Advanced Build Analysis (Stats/Skills)
│   ├── teams.py          # Team Comp & Strategy analysis
│   ├── umas.py           # Individual Character Tier Lists
│   └── resources.py      # Support Cards & Luck analysis
├── data/                 # Local data storage (Parquet files)
└── images/               # Static assets
```
---

### **📂 Credits**
Lead Developer: Zuse (@zusethegoose)
Data Team: Ryan4Numbers, Ramen, Cien, Vali
Community Unc: MooMooCows [https://www.youtube.com/@MooMooCows]
