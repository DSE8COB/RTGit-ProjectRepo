import json
import os
import sys
import requests

CREATE_REVIEW_URL = (
    "https://ews-emea.api.bosch.com/reviewtool/create-task/d/v1/createReview/task/bbm/14"
)


def get_public_email(username, github_token):
    try:
        response = requests.get(
            f"https://api.github.com/users/{username}",
            headers={
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github+json"
            },
            timeout=30
        )

        response.raise_for_status()

        user = response.json()

        print(f"\n===== GitHub User Data for {username} =====")
        print(json.dumps(user, indent=2))
        print("==========================================\n")

        return user.get("email")

    except Exception as ex:
        print(f"Unable to fetch email for {username}: {str(ex)}")
        return None


def add_comment(repo, pr_number, github_token, message):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"

    headers = {
        "Authorization": f"token {github_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        url,
        headers=headers,
        json={"body": message}
    )

    if response.status_code != 201:
        print(f"Failed to add PR comment: {response.status_code}")
        print(response.text)


def main():

    pr = json.loads(sys.argv[1])
    repo = sys.argv[2]
    pr_number = sys.argv[3]

    github_token = os.environ["GITHUB_TOKEN"]

    pr_title = pr["title"]
    pr_url = pr["html_url"]

    author = pr["user"]["login"]

    author_email = get_public_email(
        author,
        github_token
    )

    print(f"Author Login : {author}")
    print(f"Author Email : {author_email}")

    reviewers = []

    for reviewer in pr.get("requested_reviewers", []):

        reviewer_login = reviewer["login"]

        reviewer_email = get_public_email(
            reviewer_login,
            github_token
        )

        print(f"Reviewer Login : {reviewer_login}")
        print(f"Reviewer Email : {reviewer_email}")

        reviewers.append({
            "reviewerSubRole": "Approver",
            "userNTID": reviewer_login,
            "emailId": reviewer_email
        })

    if len(reviewers) == 0:
        add_comment(
            repo,
            pr_number,
            github_token,
            "⚠️ Review task not created because no reviewers are assigned yet."
        )
        return

    payload = {
        "taskName": pr_title,
        "remarks": "Created automatically from GitHub PR",
        "checklist": {
            "Ids": [],
            "tags": ["newTag", "addednewtag1"],
            "usage": "AND"
        },
        "reviewType": {
            "Ids": [],
            "tags": ["T1", "testtags_list"],
            "usage": "OR"
        },
        "author": {
            "userNTID": author,
            "emailId": author_email
        },
        "reviewRoles": reviewers,
        "taskLinks": [
            pr_url
        ],
        "gitOneReviewerApprovalSufficient": "Y"
    }

    print("Payload:")
    print(json.dumps(payload, indent=2))

    try:

        response = requests.post(
            CREATE_REVIEW_URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "KeyId": "9bc39618-a714-4d87-aa6a-c4fd4985d9ba"
            },
            timeout=60
        )

        print("Status Code:", response.status_code)
        print("Response:", response.text)

        response.raise_for_status()

        result = response.json()

        if result.get("returnId") in (1, 2):

            task_id = result.get("taskIdStr", "")

            add_comment(
                repo,
                pr_number,
                github_token,
                f"✅ Review task created successfully: {task_id}"
            )

        else:

            error = (
                result.get("returnErrorMsg")
                or result.get("returnMsg")
                or "Unknown Error"
            )

            add_comment(
                repo,
                pr_number,
                github_token,
                f"❌ Review task creation failed.\n\n{error}"
            )

    except Exception as ex:

        add_comment(
            repo,
            pr_number,
            github_token,
            f"❌ Review task creation failed.\n\n{str(ex)}"
        )

        raise


if __name__ == "__main__":
    main()
