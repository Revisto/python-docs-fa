import os
from pathlib import Path
from transifex.api import transifex_api

# Transifex API Authentication
TRANSIFEX_AUTH_TOKEN = os.getenv("TRANSIFEX_API_TOKEN")
if not TRANSIFEX_AUTH_TOKEN:
    raise ValueError("TRANSIFEX_API_TOKEN environment variable not set.")
transifex_api.setup(auth=TRANSIFEX_AUTH_TOKEN)

# Language and Project Configuration
LANG = "fa"
ORGANISATION_ID = "o:python-doc"
PROJECT_ID = "o:python-doc:p:python-newest"
LANGUAGE_ID = f"l:{LANG}"

try:
    ORGANISATION = transifex_api.Organization.get(id=ORGANISATION_ID)
    PROJECT = transifex_api.Project.get(id=PROJECT_ID)
    LANGUAGE = transifex_api.Language.get(id=LANGUAGE_ID)
except Exception as e:
    print(f"Error initializing Transifex API objects: {e}")
    raise

# Calculate the project root (assuming config.py is in scripts/transifex/)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Resource Mapping
RESOURCE_NAME_MAP = {"glossary_": "glossary"}

# Output file paths
TX_CONFIG_PATH = PROJECT_ROOT / ".tx/config"
RESOURCE_STATS_MD_PATH = PROJECT_ROOT / "RESOURCE.md"
TEAM_STATS_MD_PATH = PROJECT_ROOT / "TEAM.md"
CONTRIBUTOR_CHART_DIR = PROJECT_ROOT / "reports"
CONTRIBUTOR_CHART_FILENAME_PREFIX = "contributor_stats_"

# README Update Configuration
README_PATH = PROJECT_ROOT / "README.md"
README_STATS_START_MARKER = "<!-- STATS_START -->"
README_STATS_END_MARKER = "<!-- STATS_END -->"
README_CONTRIBUTORS_HEADER = "مشارکت‌های کاربران"
README_PROGRESS_HEADER = "پیشرفت کلی ترجمه"
README_UPDATED_ON = "به‌روزرسانی"

CHART_PASTEL_COLORS = [
    "#A6C7E8",  # Pastel blue
    "#B5EAD7",  # Pastel green
    "#FFDFD3",  # Pastel pink
    "#FFF1AC",  # Pastel yellow
    "#E2D1F9",  # Pastel lavender
    "#FFD7BA",  # Pastel orange
    "#FFABAB",  # Pastel coral
    "#C7F0DB",  # Pastel mint
    "#FFDAC1",  # Pastel peach
    "#C7CEEA",  # Pastel sky blue
]

REPORT_HEADERS = {
    "resource_stats": {
        "file": "File",
        "translated": "Translated",
        "reviewed": "Reviewed",
        "proofread": "Proofread",
        "alignment": "|:-----|:-----------:|:-----------:|:-----------:|\n",
    },
    "team_stats": {
        "user": "User",
        "role": "Role",
        "translated_count": "Translated Count",
        "reviewed_count": "Reviewed Count",
        "proofread_count": "Proofread Count",
        "alignment": "|:-----|:------:|:------------------:|:-------------------:|:----------------------:|\n",
    },
    "contributor_chart": {
        "title_base": "User Contributions",
        "title_top_n_suffix": " (Top {top_n})",
        "xlabel_username": "Username",
        "ylabel_total_contributions": "Total Contributions",
    },
}
