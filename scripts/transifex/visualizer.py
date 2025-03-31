import json
import os
import requests
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from datetime import datetime, timedelta
import collections
import sys

# Calculate the path to the repository root (2 levels up from this script)
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
COOKIE_FILE = "transifex_cookies.json"
FA_STRINGS_URL = (
    "https://app.transifex.com/_/editor/ajax/python-doc/python-newest/string/$/fa/ids/"
)
REFERER_URL = "https://app.transifex.com/python-doc/python-newest/translate/"
STRING_HISTORY_URL = "https://app.transifex.com/_/editor/ajax/python-doc/python-newest/history/fa/{string_id}/"

# Output directory is now at repo root
OUTPUT_DIR = os.path.join(REPO_ROOT, "reports")
PASTEL_COLORS = [
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


def ensure_output_dir():
    """Ensure the output directory exists."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    if not os.path.exists(os.path.join(OUTPUT_DIR, "contributors")):
        os.makedirs(os.path.join(OUTPUT_DIR, "contributors"))
    if not os.path.exists(os.path.join(OUTPUT_DIR, "progress")):
        os.makedirs(os.path.join(OUTPUT_DIR, "progress"))


def generate_timestamp():
    """Generate a timestamp string for filenames."""
    return datetime.now().strftime("%Y-%m-%d")


def load_cookies_from_file():
    """Load cookies from file."""
    with open(COOKIE_FILE, "r") as f:
        cookies = json.load(f)
    # Create dictionary format for easy access
    cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}

    # Create cookie string for header
    cookie_str = "; ".join(
        [f"{cookie['name']}={cookie['value']}" for cookie in cookies]
    )

    return cookie_dict, cookie_str


def get_transifex_headers():
    """Generate headers required for Transifex API requests."""
    cookie_dict, cookie_str = load_cookies_from_file()
    headers = {
        "x-csrftoken": cookie_dict.get("csrftoken", ""),
        "Cookie": cookie_str,
        "referer": REFERER_URL,
    }
    return headers


def _fetch_strings_list(body):
    """Fetch string IDs from Transifex API."""
    headers = get_transifex_headers()

    response = requests.post(FA_STRINGS_URL, headers=headers, json=body)
    if response.ok:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        response.raise_for_status()


def fetch_reviewed_strings():
    """Fetch all reviewed string IDs."""
    body = {"escape": False, "reviewed": "yes", "s": "translation_updated:desc"}
    return _fetch_strings_list(body)


def fetch_unreviewed_strings():
    """Fetch all unreviewed string IDs."""
    body = {"escape": False, "reviewed": "no", "s": "translation_updated:desc"}
    return _fetch_strings_list(body)


def fetch_all_strings():
    """Fetch all string IDs."""
    body = {"escape": False}
    return _fetch_strings_list(body)


def get_string_translation_history(string_id):
    """Fetch the translation history for a specific string."""
    headers = get_transifex_headers()
    url = STRING_HISTORY_URL.format(string_id=string_id)
    response = requests.get(url, headers=headers)
    if response.ok:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        response.raise_for_status()


def get_user_contributions(days=7):
    """
    Analyze contributions for both reviewed and unreviewed strings within the last N days.
    Takes advantage of the pre-sorted string lists to optimize performance.

    Args:
        days: Number of days to look back (default: 7)

    Returns:
        Counter object with username keys and contribution count values
    """
    user_contributions = collections.Counter()
    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

    # Process both reviewed and unreviewed strings
    for category, fetch_function in [
        ("reviewed", fetch_reviewed_strings),
        ("unreviewed", fetch_unreviewed_strings),
    ]:
        strings = fetch_function()[:100]
        print(f"Processing {category} strings (sorted by most recently updated)...")
        stop_processing = False

        for i, string_id in enumerate(strings):
            try:
                history = get_string_translation_history(string_id)

                # Get the Persian translation entries
                fa_entries = [
                    entry
                    for entry in history.get("data", [])
                    if entry.get("lang_code") == "fa"
                ]

                # If there are no Persian translations or the most recent one is too old,
                # we can stop processing since all following strings will be older
                if (
                    not fa_entries
                    or fa_entries[0].get("creation_date", "") < cutoff_date
                ):
                    print(
                        f"Reached entries older than {days} days. Stopping at {category} string {i+1}/{len(strings)}."
                    )
                    stop_processing = True
                    break

                # Process translation history entries that are within timeframe
                for entry in fa_entries:
                    if entry.get("creation_date", "") >= cutoff_date:
                        user_contributions[entry.get("username", "unknown")] += 1
                    else:
                        # Once we find an entry that's too old, we can skip the rest
                        break

                # Show progress
                if i % 20 == 0 and i > 0:
                    print(f"Processed {i}/{len(strings)} {category} strings...")

            except Exception as e:
                print(f"Error processing {category} string {string_id}: {e}")

            if stop_processing:
                break

    return user_contributions


def visualize_user_contributions(days=7, top_n=None):
    """
    Visualize user contributions using a bar chart with pastel colors
    and save to a file.

    Args:
        days: Number of days the data covers (for title)
        top_n: Optional limit to show only the top N contributors
    """

    contributions = get_user_contributions(days)

    # Sort contributions by count (descending)
    sorted_contributions = sorted(
        contributions.items(), key=lambda x: x[1], reverse=True
    )

    # Limit to top_n if specified
    if top_n and len(sorted_contributions) > top_n:
        sorted_contributions = sorted_contributions[:top_n]

    usernames = [item[0] for item in sorted_contributions]
    counts = [item[1] for item in sorted_contributions]

    # Assign different pastel colors to each bar (cycling if more bars than colors)
    bar_colors = [PASTEL_COLORS[i % len(PASTEL_COLORS)] for i in range(len(usernames))]

    plt.figure(figsize=(12, 6))
    bars = plt.bar(usernames, counts, color=bar_colors)
    plt.title(f"User Contributions (Last {days} Days)")
    plt.xlabel("Username")
    plt.ylabel("Number of Contributions")
    plt.xticks(rotation=45, ha="right")

    # Force y-axis to use integer ticks only
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))

    plt.grid(axis="y", linestyle="--", alpha=0.7)

    # Add count labels on top of each bar with integer values
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.1,  # Small offset above bar
            f"{int(height)}",  # Ensure integer display
            ha="center",
            fontweight="bold",
        )

    plt.tight_layout()

    # Create directory structure
    ensure_output_dir()

    # Save the visualization
    timestamp = generate_timestamp()
    contributors_dir = os.path.join(OUTPUT_DIR, "contributors")
    filename = os.path.join(contributors_dir, f"{timestamp}.png")
    plt.savefig(filename)
    plt.close()
    print(f"Saved user contributions chart to {filename}")

    # Print the results
    print("\nUser contributions summary:")
    for username, count in sorted_contributions:
        print(f"{username}: {count}")

    return filename


def visualize_string_counts():
    """
    Visualize the counts of reviewed, unreviewed, and total strings using pastel colors
    and save to a file.
    """
    # Fetch string counts
    reviewed_count = len(fetch_reviewed_strings())
    unreviewed_count = len(fetch_unreviewed_strings())
    total_count = len(fetch_all_strings())

    # Print counts
    print(f"There are {reviewed_count} reviewed strings.")
    print(f"There are {unreviewed_count} unreviewed strings.")
    print(f"There are {total_count} strings in total.")

    # Create bar chart with pastel colors
    categories = ["Reviewed", "Unreviewed", "Total"]
    counts = [reviewed_count, unreviewed_count, total_count]
    pastel_colors = [
        PASTEL_COLORS[1],
        PASTEL_COLORS[5],
        PASTEL_COLORS[0],
    ]  # Green, Orange, Blue pastels

    plt.figure(figsize=(10, 6))
    bars = plt.bar(categories, counts, color=pastel_colors)
    plt.title("Translation String Counts")
    plt.ylabel("Number of Strings")
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    # Add count labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.1 * max(counts),
            f"{int(height):,}",
            ha="center",
            fontweight="bold",
        )

    # Add percentage of reviewed/unreviewed to total
    reviewed_pct = (reviewed_count / total_count) * 100 if total_count > 0 else 0
    unreviewed_pct = (unreviewed_count / total_count) * 100 if total_count > 0 else 0

    # Use dark text for better readability on pastel backgrounds
    plt.text(
        0,
        reviewed_count / 2,
        f"{reviewed_pct:.1f}%",
        ha="center",
        color="#333333",
        fontweight="bold",
    )
    plt.text(
        1,
        unreviewed_count / 2,
        f"{unreviewed_pct:.1f}%",
        ha="center",
        color="#333333",
        fontweight="bold",
    )

    plt.tight_layout()

    # Save the visualization
    ensure_output_dir()
    timestamp = generate_timestamp()
    progress_dir = os.path.join(OUTPUT_DIR, "progress")
    filename = os.path.join(progress_dir, f"{timestamp}.png")
    plt.savefig(filename)
    plt.close()
    print(f"Saved string counts chart to {filename}")

    return filename
