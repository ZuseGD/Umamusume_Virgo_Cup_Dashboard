# update the relevant CM form_url with link when form is live/none when inactive
# update sheet_url with the exploded CSV link from Google Sheets when available use the previous event's link as placeholder if needed
CM_LIST = {
    "Virgo Cup (2025)": {
        "id": "cm5",
        "icon": "🏆",
        "sheet_url": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTR8Pa4QQVSNwepSe9dYnro3ZaVEpYQmBdZUzumuLL-U2IR3nKVh-_GbZeJHT2x9aCqnp7P-0hPm5Zd/pub?gid=221070242&single=true&output=csv",
        "parquet_file": "data/r2d2.parquet",
        "form_url": "https://forms.gle/eDPAs8u4RHPKbxEN8", 
        "status_msg": "Forms have closed for this event.",
        "guide_images": [
            "https://raw.githubusercontent.com/moomoocowsteam/canva/refs/heads/main/virgo.png"
        ]
    },
    "Libra Cup (2025)": {
        "id": "cm6",
        "icon": "⚖️",
        # Placeholder URL (You can update this when Libra data exists)
        "sheet_url": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTR8Pa4QQVSNwepSe9dYnro3ZaVEpYQmBdZUzumuLL-U2IR3nKVh-_GbZeJHT2x9aCqnp7P-0hPm5Zd/pub?gid=221070242&single=true&output=csv",
        "parquet_file": "libra.parquet" ,
        "form_url": None,
        "status_msg": "Forms have not started yet.",
        "guide_images": [
            "https://raw.githubusercontent.com/moomoocowsteam/canva/refs/heads/main/libra.png"
        ]
    }
}