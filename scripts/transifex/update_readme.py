import os
import re
import glob
from datetime import datetime

# Calculate the path to the repository root (2 levels up from this script)
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
README_PATH = os.path.join(REPO_ROOT, "README.md")
contributors_dir = os.path.join(REPO_ROOT, "reports", "contributors")
progress_dir = os.path.join(REPO_ROOT, "reports", "progress")


def find_latest_image(directory):
    """Find the latest image file in the given directory based on filename."""
    pattern = os.path.join(directory, "*.png")
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort the files by name (which should sort by date if the format is consistent)
    latest_file = sorted(files)[-1]
    # Return the path relative to the REPO_ROOT
    return os.path.relpath(latest_file, REPO_ROOT).replace("\\", "/")


def update_readme():
    """Update the README.md file with the latest report images."""
    today = datetime.now().strftime("%Y-%m-%d")
    latest_contributors_img = find_latest_image(contributors_dir)
    latest_progress_img = find_latest_image(progress_dir)

    # Check if both image files exist
    if not latest_contributors_img or not latest_progress_img:
        print("Warning: One or both image files not found.")
        if latest_contributors_img:
            print(f"Found contributors image: {latest_contributors_img}")
        if latest_progress_img:
            print(f"Found progress image: {latest_progress_img}")
        return False

    # Read the current README content
    with open(README_PATH, "r", encoding="utf-8") as file:
        content = file.read()

    # Define the stats section
    stats_section = f"""## آمار ترجمه

### مشارکت‌های این هفته کاربران

![مشارکت‌های این هفته کاربران]({latest_contributors_img})

(به‌روزرسانی: {today})

### پیشرفت ترجمه

![پیشرفت ترجمه]({latest_progress_img})

(به‌روزرسانی: {today})"""

    # Check if stats section already exists with markers
    if "<!-- STATS_START -->" in content and "<!-- STATS_END -->" in content:
        # Replace the existing stats section between markers
        pattern = r"<!-- STATS_START -->.*?<!-- STATS_END -->"
        updated_content = re.sub(
            pattern,
            f"<!-- STATS_START -->\n{stats_section}\n<!-- STATS_END -->",
            content,
            flags=re.DOTALL,
        )
    elif "## آمار ترجمه" in content:
        # If old format exists without markers, replace that section
        pattern = r"## آمار ترجمه.*?(?=\n##|\Z)"
        updated_content = re.sub(
            pattern,
            f"<!-- STATS_START -->\n{stats_section}\n<!-- STATS_END -->",
            content,
            flags=re.DOTALL,
        )
    else:
        # Append the stats section to the end of the README
        updated_content = (
            content
            + "\n\n<!-- STATS_START -->\n"
            + stats_section
            + "\n<!-- STATS_END -->"
        )

    # Write the updated content back to the README
    with open(README_PATH, "w", encoding="utf-8") as file:
        file.write(updated_content)

    print(f"README.md updated successfully with:")
    print(f"- Contributors image: {latest_contributors_img}")
    print(f"- Progress image: {latest_progress_img}")
    print(f"- Update date: {today}")
    return True


if __name__ == "__main__":
    update_readme()
