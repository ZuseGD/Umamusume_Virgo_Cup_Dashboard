from decouple import config

# update the relevant CM form_url with link when form is live/none when inactive
# update sheet_url with the exploded CSV link from Google Sheets when available use the previous event's link as placeholder if needed
CM_LIST = {
    "Virgo Cup (2025)": {
        "id": "cm5",
        "icon": "🏆",
        "sheet_url": config('VIRGO_SHEET_URL', default=''),
        "parquet_file": "data/1_virgo_prelims.parquet",

        # FINALS DATA (New)
        "finals_csv": "data/1_virgo_finals.csv", 
        "finals_parquet": "data/1_virgo_finals.parquet",

        "form_url": None, 
        "status_msg": "Forms have closed for this event.",
        "guide_images": [
            "https://raw.githubusercontent.com/moomoocowsteam/canva/refs/heads/main/virgo.png"
        ]
    },
    "Libra Cup (2025)": {
        "id": "cm6",
        "icon": "⚖️",
        # Placeholder URL (You can update this when Libra data exists)
        "sheet_url": config('VIRGO_SHEET_URL', default=''),
        "parquet_file": "libra.parquet" ,
        "finals_csv": None, 
        "finals_parquet": None,
        "form_url": None,
        "status_msg": "Forms have not started yet.",
        "guide_images": [
            "https://raw.githubusercontent.com/moomoocowsteam/canva/refs/heads/main/libra.png"
        ]
    }
}