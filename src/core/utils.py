"""Shared helpers for fetching GitHub data and rendering the HTML report."""
import base64
import os
import platform
import requests
from colorama import Fore, Style
from requests.exceptions import HTTPError, RequestException


class colors:
    """ANSI color constants used for terminal output."""

    HEADER = Fore.MAGENTA
    BLUE = Fore.BLUE
    CYAN = Fore.CYAN
    GREEN = Fore.GREEN
    WARNING = Fore.YELLOW
    FAIL = Fore.RED
    RED = Fore.RED
    ENDC = Style.RESET_ALL
    BOLD = Style.BRIGHT


def clear():
    """Clear the terminal screen without spawning a shell."""
    if platform.system() == "Windows":
        print("\033[2J\033[H", end="")
    else:
        print("\033c", end="")


def get_auth_headers():
    """Return the Authorization header dict if a GitHub token is set."""
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def fetch_as_data_uri(url):
    """
    Fetch a remote image and return it as a base64 data URI.

    Embeds the image directly in the HTML file (needed when the page is served
    via file:// and WebKit would otherwise block external requests).
    """
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "image/svg+xml").split(";")[0].strip()
        encoded = base64.b64encode(resp.content).decode("ascii")
        return f"data:{content_type};base64,{encoded}"
    except (RequestException, ValueError, TypeError):
        return url  # fall back to original URL on any failure


def fetch_and_print_data(username):
    """Fetch the GitHub user profile and print each field to the terminal."""
    print(f"Fetching data for user: {colors.FAIL}{username}{colors.ENDC}")
    url = f"https://api.github.com/users/{username}"
    try:
        response = requests.get(url, headers=get_auth_headers(), timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"\n{colors.WARNING}User Data:{colors.ENDC}")
        for key, value in data.items():
            key = key.replace("_", " ").capitalize()
            print(f"{colors.CYAN}{key}:{colors.ENDC} {value}")

    except HTTPError as http_err:
        print(f"{colors.FAIL}HTTP error occurred: {http_err}{colors.ENDC}")
    except (RequestException, ValueError) as err:
        print(f"{colors.FAIL}Unexpected error: {err}{colors.ENDC}")


def show_events_and_graphs(urls):
    """Print a confirmation that graphs are available in the report."""
    print(
        f"\nGraphs available in Received Events [{colors.GREEN}✓{colors.ENDC}]"
    )


def generate_html_event_row(avatar, login, event_type, repo_name, repo_url, badge_class, action_text):
    """Return the HTML markup for a single received-event row."""
    return f"""
    <div class="event-row d-flex align-items-center shadow-sm">
        <img src="{avatar}" class="profile-picture me-3" alt="Avatar of {login}">
        <div>
            <a href="https://github.com/{login}" class="text-light fw-semibold">{login}</a>
            <p class="mb-1 {badge_class} small">{action_text}</p>
            <a class="repo-link" target="_blank" href="{repo_url}">{repo_name}</a>
        </div>
    </div>"""


def create_and_display_html_user_events(username, urls):
    """Build the user's HTML report from profile data and received events."""
    events_url = f"https://api.github.com/users/{username}/received_events"
    html_path = ".temp/index.html"

    print(f"Generating HTML report... [{colors.GREEN}✓{colors.ENDC}]\n")

    url = f"https://api.github.com/users/{username}"
    try:
        response = requests.get(url, headers=get_auth_headers(), timeout=10)
        response.raise_for_status()
        user_data = response.json()

        login = user_data.get("login", "")
        name = user_data.get("name", "")
        location = user_data.get("location", "")
        html_url = user_data.get("html_url", "")
        avatar_url = user_data.get("avatar_url", "")
        bio = user_data.get("bio", "")
        followers = user_data.get("followers", 0)
        following = user_data.get("following", 0)

    except HTTPError as http_err:
        print(f"{colors.FAIL}HTTP error occurred: {http_err}{colors.ENDC}")
        return
    except (RequestException, ValueError) as err:
        print(f"{colors.FAIL}Unexpected error: {err}{colors.ENDC}")
        return

    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    if os.path.exists(html_path):
        os.remove(html_path)

    try:
        response = requests.get(events_url, headers=get_auth_headers(), timeout=10)
        response.raise_for_status()
        events = response.json()

        with open(html_path, "w", encoding="utf_8") as f:
            f.write(f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>GitHubUserDataExtractor - Dashboard</title>
    <link rel="icon" href="https://quantumbytestudios.in/src/images/ClassicWhiteVeryBig.png" type="image/x-icon">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body {{
            background: linear-gradient(to bottom right, #0d1117, #1f2937);
            font-family: 'Inter', sans-serif;
            color: #e5e7eb;
            margin: 0;
            padding: 0;
        }}

        h1,
        h4 {{
            font-weight: 700;
        }}

        .event-row {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 1.2rem;
            margin-bottom: 1.2rem;
            backdrop-filter: blur(8px);
            transition: transform 0.2s ease;
        }}

        .event-row:hover {{
            transform: scale(1.02);
        }}

        .profile-picture {{
            border-radius: 50%;
            width: 128px;
            height: 128px;
            object-fit: cover;
        }}

        .repo-link {{
            color: #58a6ff;
            font-weight: 500;
        }}

        .repo-link:hover {{
            text-decoration: underline;
        }}

        .text-warning {{
            color: #facc15 !important;
        }}

        .text-success {{
            color: #34d399 !important;
        }}

        .dashboard-header {{
            text-align: center;
            margin-bottom: 3rem;
        }}

        .dashboard-header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }}

        .dashboard-header p {{
            color: #9ca3af;
        }}

        .graph-container img {{
            border-radius: 10px;
            margin-top: 1rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }}

        .container {{
            max-width: 900px;
        }}

        a {{
            text-decoration: none;
        }}

        hr {{
            border-color: #374151;
        }}
    </style>
</head>
<body class="container py-5">
    <div class="dashboard-header">
        <h1>GitHub Activity Dashboard</h1>
        <p class="lead">Visual summary of recent contributions</p>
        <hr>
    </div>
    <div class="row">
    <div class="col-sm-12 col-md-12 col-lg-12">
        <h4 class="mb-4">User Profile</h4>
        <div class="row d-flex justify-content-center align-items-left my-5">
            <div class="col-2">
                <img src="{avatar_url}" class="profile-picture mb-3" alt="Avatar of {login}">
            </div>
            <div class="col-10">
                <h2 class="fw-bold">{name}</h2>
                <p class="text-white">
                    Username: {login} <br>
                    About: {bio} <br>
                    Followers: {followers}, Following: {following} <br>
                    Location: {location} 
                </p>
                <a href="{html_url}" class="btn btn-light" target="_blank">View Profile</a>
            </div>
        </div>
    </div>
    <div class="col-sm-12 col-md-8 col-lg-8">
    <h4 class="mb-4">Received Events</h4>""")

            for event in events:
                event_type = event.get("type")
                actor = event.get("actor", {})
                payload = event.get("payload", {})
                repo = event.get("repo", {})
                login = actor.get("login", "")
                avatar = actor.get("avatar_url", "")
                repo_name = repo.get("name", "")
                repo_url = f"https://github.com/{repo_name}"

                badge_class = ""
                action_text = ""

                if event_type == "ForkEvent":
                    badge_class = "text-danger"
                    action_text = "Forked a repository"
                    repo_url = payload.get("forkee", {}).get("html_url", "#")

                elif event_type == "WatchEvent":
                    badge_class = "text-warning"
                    action_text = "Watch/Starred a repository"

                elif event_type == "CreateEvent":
                    badge_class = "text-success"
                    action_text = "Created a repository"

                elif event_type == "PublicEvent":
                    badge_class = "text-primary"
                    action_text = "Published a repository"

                elif event_type == "ReleaseEvent":
                    badge_class = "text-primary"
                    action_text = "Released a repository"
                    repo_url = payload.get("release", {}).get("html_url", "#")

                if action_text:  # Only write if action_text is set
                    f.write(generate_html_event_row(
                        avatar, login, event_type, repo_name,
                        repo_url, badge_class, action_text))

            langs_src = fetch_as_data_uri(urls['mostUsedLanguages'])
            stats_src = fetch_as_data_uri(urls['githubStats'])
            streak_src = fetch_as_data_uri(urls['streakContributionsLS'])

            f.write(f"""</div>
    <div class="col-sm-12 col-md-4 col-lg-4">
        <h4 class="mb-4">Contribution Insights</h4>
        <div class="row justify-content-center align-items-left graph-container">
            <div class="col-12">
                <img class="img-fluid w-100" src="{langs_src}" alt="Top Languages">
                <img class="img-fluid w-100" src="{stats_src}" alt="GitHub Stats">
                <img class="img-fluid w-100" src="{streak_src}" alt="Streak Stats">
            </div>
        </div>
    </div>
    </div>
</body>
</html>
""")
    except HTTPError as http_err:
        print(f"{colors.FAIL}HTTP error occurred: {http_err}{colors.ENDC}")
    except (RequestException, OSError, ValueError) as err:
        print(f"{colors.FAIL}Unexpected error: {err}{colors.ENDC}")
