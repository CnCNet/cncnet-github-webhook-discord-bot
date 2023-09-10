from flask import Flask, request, jsonify, abort
from decouple import config
import hmac
import hashlib  # Import hashlib for SHA-1 hashing
import requests
import os
import json

app = Flask(__name__)

# Retrieve the Discord webhook URL from the .env file
discord_webhook_url = config('DISCORD_WEBHOOK_URL')
github_webhook_secret = config('GITHUB_WEBHOOK_SECRET')

@app.route('/github-webhook', methods=['POST'])
def github_webhook():
    try:
        # Get the request signature from the headers
        signature = request.headers.get('X-Hub-Signature')

        # Verify that the signature exists
        if not signature:
            return 'Signature not provided', 400

        # Get the raw request data
        request_data = request.data

        # Calculate the expected signature using the secret
        expected_signature = 'sha1=' + hmac.new(github_webhook_secret.encode(), request_data, hashlib.sha1).hexdigest()

        # Compare the expected signature with the received signature
        if not hmac.compare_digest(signature, expected_signature):
            return 'Signature mismatch', 401

        payload = request.json

        # Check if the repository is public
        if 'repository' in payload and not payload['repository']['private']:
            # Process GitHub webhook events for public repositories
            event_type = request.headers.get('X-GitHub-Event')
            if event_type == 'push':
                handle_push_event(payload)
            elif event_type == 'pull_request':
                handle_pull_request_event(payload)
            elif event_type == 'issues':
                handle_issues_event(payload)
            elif event_type == 'fork':
                handle_forks_event(payload)
            elif event_type == 'star':
                handle_star_event(payload)

        return '', 200
    except Exception as e:
        return str(e), 500

def handle_push_event(payload):
    send_discord_notification("push", payload)

def handle_pull_request_event(payload):
    send_discord_notification("pull_request", payload)

def handle_issues_event(payload):
    send_discord_notification("issues", payload)

def handle_forks_event(payload):
    send_discord_notification("forks", payload)

def handle_star_event(payload):
    send_discord_notification("star", payload)

def send_discord_notification(event_type, payload):
    # Extract relevant information from the payload
    repository_name = payload['repository']['full_name']
    sender_login = payload['sender']['login']
    sender_profile_url = payload['sender']['html_url']

    # Get the base URL for the GitHub repository
    repo_url = payload['repository']['html_url']

    sender_name_with_link = f"[**{sender_login}**]({sender_profile_url})"
    repo_name_with_link = f"[**{repository_name}**]({repo_url})"
    event_url = ""  # Initialize event_url to an empty string
    event_title = ""  # Initialize event_title to an empty string

    # Create a custom embed title and event title based on the event type
    if event_type == 'push':
        action = "pushed"
        branch = payload['ref'].split('/')[-1]  # Extract the branch name from the ref
        event_url = f"{repo_url}/commits"
        event_title = f"Pushed to branch: {branch}"

    elif event_type == 'pull_request':
        action = payload['action']
        pr_number = payload['pull_request']['number']
        pr_title = payload['pull_request']['title']
        event_url = f"{repo_url}/pull/{pr_number}"
        event_title = f"Pull request {action}: {pr_title}"

    elif event_type == 'issues':
        action = payload['action']
        issue_number = payload['issue']['number']
        issue_title = payload['issue']['title']
        event_url = f"{repo_url}/issues/{issue_number}"
        event_title = f"Issue {action}: {issue_title}"

    elif event_type == 'forks':
        action = "forked"
        event_url = repo_url
        event_title = f"Forked repository: {repository_name}"

    elif event_type == 'star':
        action = "starred"
        event_url = repo_url
        event_title = f"Starred repository: {repository_name}"

    else:
        action = event_type

    # Fetch the repository description from the GitHub API
    repo_description = get_repository_description(repository_name)

    # Create a custom embed
    embed = {
        "title": "",
        "color": int("00ff8a", 16),
        "fields": [
            {
                "name": "",
                "value": f"{sender_name_with_link} - [**{event_title}**]({event_url})",
                "inline": False
            },
            {
                "name": "Project",
                "value": repo_name_with_link,
                "inline": False
            },
            {
                "name": "Project Description",
                "value": repo_description,
                "inline": False
            },
        ],
        "author": {
            "name": sender_login,
            "url": sender_profile_url,
            "icon_url": payload['sender']['avatar_url']  # Include the author's avatar URL
        }
    }

    # Construct the Discord message payload with the custom embed
    payload = {
        "embeds": [embed]  # List of custom embeds
    }

    # Use the organization's logo URL as the avatar URL
    org_logo_url = 'https://avatars.githubusercontent.com/u/11489929?s=64&v=4'  # Replace with the actual organization logo URL

    # Construct the message data with the organization's logo URL as the avatar URL
    data = {
        'avatar_url': org_logo_url,  # Set the organization's logo as the avatar URL
    }

    # Send the formatted message with the custom embed to the Discord webhook
    response = requests.post(discord_webhook_url, json={**payload, **data})

    # Check the response status code (optional)
    if response.status_code == 204:
        print("Discord notification with custom embed sent successfully")
    else:
        print("Failed to send Discord notification")


def get_repository_description(repo_full_name):
    # Make a GET request to the GitHub API to fetch the repository description
    github_api_url = f"https://api.github.com/repos/{repo_full_name}"
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(github_api_url, headers=headers)

    if response.status_code == 200:
        data = json.loads(response.text)
        return data['description']
    else:
        return "No description available"  # Return a default value if description is not found



if __name__ == '__main__':
    # Use environment variables for configuration
    port = int(os.environ.get('PORT', 80))
    app.run(debug=True, host='0.0.0.0', port=port)
