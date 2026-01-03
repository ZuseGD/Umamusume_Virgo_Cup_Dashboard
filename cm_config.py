from decouple import config

# update the relevant CM form_url with link when form is live/none when inactive
# update sheet_url with the exploded CSV link from Google Sheets when available use the previous event's link as placeholder if needed
CM_LIST = {
    "Scorpio Cup (2025)": {
        "id": "Scorpio Cup (2025)",
        "icon": "🦀",
        "aptitude_dist": "Medium",   # Options: Sprint, Mile, Medium, Long
        "aptitude_surf": "Turf",   # Options: Turf, Dirt
        "sheet_url": config('SCORPIO_SHEET_URL', default=''),
        "is_multipart_parquet": False,
        "parquet_file": "libra.parquet" ,
        "finals_csv": None, 
        "finals_parquet": None,
        "form_url": 'https://forms.gle/BUUMNG1MYZesYUjy7',
        "status_msg": "Forms have not started yet.",
        "guide_images": [
            "https://raw.githubusercontent.com/moomoocowsteam/canva/refs/heads/main/scorpio.png"
        ]
    },
    "Libra Cup (2025)": {
        "id": "Libra Cup (2025)",
        "icon": "⚖️",
        "aptitude_dist": "Long",   # Options: Sprint, Mile, Medium, Long
        "aptitude_surf": "Turf",   # Options: Turf, Dirt
        # Placeholder URL (You can update this when Libra data exists)
        "sheet_url": config('LIBRA_SHEET_URL', default=''),
        "parquet_file": "libra.parquet" ,
        # New 3-Part Parquet Structure
        "is_multipart_parquet": True,
        "finals_parts": {
            "statsheet": "data/cm6_finals_statsheet_1.parquet",
            "podium": "data/cm6_finals_podium_1.parquet",
            "deck": "data/cm6_finals_deck_1.parquet"
        },
        # Backwards compatibility flags
        "finals_csv": "data/cm6_finals.csv",
        "finals_parquet": None,
        "form_url": 'https://forms.gle/BUUMNG1MYZesYUjy7',
        "status_msg": "Forms have closed for this event.",
        "guide_images": [
            "https://raw.githubusercontent.com/moomoocowsteam/canva/refs/heads/main/libra.png"
        ]
    },
    
    "Virgo Cup (2025)": {
        "id": "Virgo Cup (2025)",
        "icon": "🏆",
        "aptitude_dist": "Mile",   # Options: Sprint, Mile, Medium, Long
        "aptitude_surf": "Turf",   # Options: Turf, Dirt
        "sheet_url": config('VIRGO_SHEET_URL', default=''),
        "parquet_file": "data/1_virgo_prelims.parquet",

       # Legacy Finals Data
        "is_multipart_parquet": False,
        "finals_csv": "data/1_virgo_finals.csv", 
        "finals_parquet": "data/1_virgo_finals.parquet",

        "form_url": 'https://forms.gle/BUUMNG1MYZesYUjy7', 
        "status_msg": "Forms have closed for this event.",
        "guide_images": [
            "https://raw.githubusercontent.com/moomoocowsteam/canva/refs/heads/main/virgo.png"
        ]
    },
    
    
}