import datetime
import glob
import re
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from . import config as app_config
from . import client as tx_client
from . import utils as tx_utils


def _get_processed_contributor_data():
    """
    Fetches and processes contributor data (translations, reviews, proofreads).
    Returns a list of dictionaries, each containing:
    {
        "user_id": str,
        "username": str,
        "role": str,
        "translated": int,
        "reviewed": int,
        "proofread": int,
        "total": int
    }
    """
    members = tx_client.get_team_members()
    users_details = {}
    for member in members:
        if member.user:
            users_details[member.user.id] = {
                "username": member.user.attributes.get("username", member.user.id),
                "role": member.attributes["role"],
            }
        else:
            # Fallback if user data is somehow missing, using member.id as key
            users_details[member.id] = {
                "username": "Unknown User",
                "role": member.attributes["role"],
            }

    translators = {user_id: 0 for user_id in users_details}
    reviewers = {user_id: 0 for user_id in users_details}
    proofreaders = {user_id: 0 for user_id in users_details}

    all_resources = tx_client.get_all_resources()
    for resource in all_resources:
        translations = tx_client.get_resource_translations(resource)
        for translation in translations:
            if (
                translation.relationships.get("translator")
                and translation.relationships["translator"]["data"]
            ):
                translator_id = translation.relationships["translator"]["data"]["id"]
                if translator_id in translators:
                    translators[translator_id] += 1
            if (
                translation.relationships.get("reviewer")
                and translation.relationships["reviewer"]["data"]
            ):
                reviewer_id = translation.relationships["reviewer"]["data"]["id"]
                if reviewer_id in reviewers:
                    reviewers[reviewer_id] += 1
            if (
                translation.relationships.get("proofreader")
                and translation.relationships["proofreader"]["data"]
            ):
                proofreader_id = translation.relationships["proofreader"]["data"]["id"]
                if proofreader_id in proofreaders:
                    proofreaders[proofreader_id] += 1

    processed_data = []
    for user_id, details in users_details.items():
        t = translators.get(user_id, 0)
        r = reviewers.get(user_id, 0)
        p = proofreaders.get(user_id, 0)
        total_contributions = t + r + p
        processed_data.append(
            {
                "user_id": user_id,
                "username": details["username"],
                "role": details["role"],
                "translated": t,
                "reviewed": r,
                "proofread": p,
                "total": total_contributions,
            }
        )
    return processed_data


class ReportGenerator:
    """Base class for report generators."""

    def __init__(self):
        pass

    def generate(self):
        raise NotImplementedError("Subclasses must implement the 'generate' method.")


class TxConfigReporter(ReportGenerator):
    """Generates the Transifex client configuration file (.tx/config)."""

    def generate(self) -> None:
        resources = tx_client.get_all_resources()
        output_path = Path(app_config.TX_CONFIG_PATH)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as fo:
            fo.writelines(("[main]\n", "host = https://www.transifex.com\n"))
            for resource in resources:
                path_obj = tx_utils.slug_to_file_path(resource.slug)

                fo.writelines(
                    (
                        f"\n[{app_config.PROJECT.id}:{resource.slug}]\n",
                        f"file_filter = {str(path_obj)}\n",
                        "type = PO\n",
                        "source_lang = en\n",
                        f"source_file = {str(path_obj)}\n",
                        f"trans.{app_config.LANG} = {str(path_obj)}\n",
                    )
                )
        print(f"Generated Transifex config at {output_path}")


class ResourceStatsMarkdownReporter(ReportGenerator):
    """Generates a Markdown file with resource translation statistics."""

    def generate(self) -> None:
        stats = tx_client.get_resource_language_stats()
        output_path = Path(app_config.RESOURCE_STATS_MD_PATH)

        headers_conf = app_config.REPORT_HEADERS["resource_stats"]
        header_line = f"| {headers_conf['file']} | {headers_conf['translated']} | {headers_conf['reviewed']} | {headers_conf['proofread']} |\n"
        alignment_line = headers_conf["alignment"]

        rows_data = []
        for stat in stats:
            resource_id_str = stat.relationships["resource"]["data"]["id"]
            resource_slug = resource_id_str.split(":")[-1]
            file_name = tx_utils.slug_to_file_path(resource_slug)

            total_words = stat.attributes["total_words"]
            if total_words == 0:
                translated_pct, reviewed_pct, proofread_pct = 0.0, 0.0, 0.0
            else:
                translated_pct = round(
                    100 * stat.attributes["translated_words"] / total_words, 1
                )
                reviewed_pct = round(
                    100 * stat.attributes["reviewed_words"] / total_words, 1
                )
                proofread_pct = round(
                    100 * stat.attributes["proofread_words"] / total_words, 1
                )
            rows_data.append((file_name, translated_pct, reviewed_pct, proofread_pct))

        # Sort: first by reviewed_pct (desc), then by translated_pct (desc)
        rows_sorted = sorted(
            rows_data,
            key=lambda row: (
                row[2],
                row[1],
            ),  # row[2]=reviewed_pct, row[1]=translated_pct
            reverse=True,
        )

        with open(output_path, "w", encoding="utf-8") as fo:
            fo.writelines((header_line, alignment_line))
            for file_name, translated_pct, reviewed_pct, proofread_pct in rows_sorted:
                fo.writelines(
                    f"| {file_name} | {translated_pct}% | {reviewed_pct}% | {proofread_pct}% |\n"
                )
        print(f"Generated resource stats at {output_path}")


class TeamStatsMarkdownReporter(ReportGenerator):
    """Generates a Markdown file with team contribution statistics."""

    def generate(self) -> None:
        contributor_data = _get_processed_contributor_data()

        output_path = Path(app_config.TEAM_STATS_MD_PATH)
        headers_conf = app_config.REPORT_HEADERS["team_stats"]
        header_line = f"| {headers_conf['user']} | {headers_conf['role']} | {headers_conf['translated_count']} | {headers_conf['reviewed_count']} | {headers_conf['proofread_count']} |\n"
        alignment_line = headers_conf["alignment"]

        # Sort by total contributions (descending)
        rows_sorted = sorted(contributor_data, key=lambda x: x["total"], reverse=True)

        with open(output_path, "w", encoding="utf-8") as fo:
            fo.writelines((header_line, alignment_line))
            for contributor in rows_sorted:
                fo.writelines(
                    f"| {contributor['username']} | {contributor['role']} | {contributor['translated']} | {contributor['reviewed']} | {contributor['proofread']} |\n"
                )
        print(f"Generated team stats at {output_path}")


class ContributorChartReporter(ReportGenerator):
    """Generates a bar chart of user contributions."""

    def __init__(self, top_n=10):
        super().__init__()
        self.top_n = top_n

    def generate(self) -> None:
        contributor_data = _get_processed_contributor_data()
        chart_data = [c for c in contributor_data if c["total"] > 0]
        sorted_contributions = sorted(
            chart_data, key=lambda x: x["total"], reverse=True
        )

        if self.top_n and len(sorted_contributions) > self.top_n:
            sorted_contributions = sorted_contributions[: self.top_n]

        if not sorted_contributions:
            print("No contributor data to generate chart.")
            return

        usernames = [item["username"] for item in sorted_contributions]
        totals = [item["total"] for item in sorted_contributions]
        bar_colors = [
            app_config.CHART_PASTEL_COLORS[i % len(app_config.CHART_PASTEL_COLORS)]
            for i in range(len(usernames))
        ]

        plt.figure(figsize=(12, 7))
        bars = plt.bar(usernames, totals, color=bar_colors)

        chart_labels = app_config.REPORT_HEADERS["contributor_chart"]
        chart_title = chart_labels["title_base"]
        if self.top_n:
            chart_title += chart_labels["title_top_n_suffix"].format(top_n=self.top_n)

        plt.title(chart_title)
        plt.xlabel(chart_labels["xlabel_username"])
        plt.ylabel(chart_labels["ylabel_total_contributions"])
        plt.xticks(rotation=45, ha="right")

        if mticker:
            plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        plt.grid(axis="y", linestyle="--", alpha=0.7)

        for bar in bars:
            height = bar.get_height()
            if height > 0:
                plt.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 0.1,
                    f"{int(height)}",
                    ha="center",
                    fontweight="bold",
                )
        plt.tight_layout()

        chart_dir = Path(app_config.CONTRIBUTOR_CHART_DIR)
        chart_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y_%m_%d")
        filename = (
            chart_dir / f"{app_config.CONTRIBUTOR_CHART_FILENAME_PREFIX}{timestamp}.png"
        )

        plt.savefig(filename)
        plt.close()
        print(f"Saved user contributions chart to {filename}")


class ReadmeUpdaterReporter(ReportGenerator):
    """Updates the README.md file with the latest statistics chart."""

    def _find_latest_chart(self) -> str | None:
        """Finds the latest contributor chart image."""
        chart_dir = Path(app_config.CONTRIBUTOR_CHART_DIR)
        pattern = str(
            chart_dir / f"{app_config.CONTRIBUTOR_CHART_FILENAME_PREFIX}*.png"
        )
        files = glob.glob(pattern)
        if not files:
            return None

        # Sort files by name (timestamp ensures latest is last)
        latest_file_path = Path(sorted(files)[-1])
        # Return path relative to the project root
        relative_path = latest_file_path.relative_to(app_config.PROJECT_ROOT)
        return relative_path.as_posix()

    def generate(self) -> None:
        readme_path = app_config.README_PATH
        print(f"Updating README.md at {readme_path}")
        if not readme_path.exists():
            print(f"Error: README.md not found at {readme_path}")
            return

        latest_chart_path = self._find_latest_chart()
        if not latest_chart_path:
            print("Warning: No contributor chart found to update README.")
            return

        today_display = datetime.datetime.now().strftime("%Y-%m-%d")

        stats_section_content = (
            f"### {app_config.README_CONTRIBUTORS_HEADER}\n"
            f"![{app_config.README_CONTRIBUTORS_HEADER}]({latest_chart_path})\n"
            f"({app_config.README_UPDATED_ON}: {today_display})"
        )

        full_replacement_text = (
            f"{app_config.README_STATS_START_MARKER}\n"
            f"{stats_section_content}\n"
            f"{app_config.README_STATS_END_MARKER}"
        )

        with open(readme_path, "r+", encoding="utf-8") as f:
            content = f.read()

            # Pattern to find the section between markers
            pattern = re.compile(
                f"{re.escape(app_config.README_STATS_START_MARKER)}.*?{re.escape(app_config.README_STATS_END_MARKER)}",
                re.DOTALL,
            )

            if pattern.search(content):
                updated_content = pattern.sub(full_replacement_text, content)
            else:
                print(
                    f"Warning: Markers {app_config.README_STATS_START_MARKER} not found. Appending stats section."
                )
                updated_content = content.rstrip() + "\n\n" + full_replacement_text

            f.seek(0)
            f.write(updated_content)
            f.truncate()
        print(
            f"README.md updated successfully at {readme_path} with chart {latest_chart_path}"
        )


class CombinedStatsReporter(ReportGenerator):
    """Generates all reports in a single run"""

    def generate(self) -> None:
        print("Generating all reports in a single run...")

        # Generate resource stats
        resource_reporter = ResourceStatsMarkdownReporter()
        resource_reporter.generate()

        # Generate team stats
        team_reporter = TeamStatsMarkdownReporter()
        team_reporter.generate()

        # Generate contributor chart
        chart_reporter = ContributorChartReporter()
        chart_reporter.generate()

        # Update README with latest stats
        readme_reporter = ReadmeUpdaterReporter()
        readme_reporter.generate()

        print("All reports generated successfully!")


# Mapping commands to reporter classes
REPORTERS = {
    "recreate-config": TxConfigReporter,
    "recreate-resource-stats": ResourceStatsMarkdownReporter,
    "recreate-team-stats": TeamStatsMarkdownReporter,
    "generate-contributor-chart": ContributorChartReporter,
    "update-readme": ReadmeUpdaterReporter,
    "generate-all-stats": CombinedStatsReporter,
}
