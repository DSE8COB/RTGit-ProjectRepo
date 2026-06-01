import json
import os
import sys
import requests

CREATE_REVIEW_URL = (
    "https://rb-bbm-rtool-t0-dev-fw-gway.apps.intranet.bosch.com"
    "/createReview/task/bbm/14"
)


def add_comment(repo, pr_number, github_token, message):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json"
    }

    requests.post(
        url,
        headers=headers,
        json={"body": message}
    ).raise_for_status()


def main():

    pr = json.loads(sys.argv[1])
    repo = sys.argv[2]
    pr_number = sys.argv[3]

    github_token = os.environ["GITHUB_TOKEN"]

    pr_title = pr["title"]
    pr_url = pr["html_url"]

    author = pr["user"]["login"]

    reviewers = []

    for reviewer in pr.get("requested_reviewers", []):
        reviewers.append({
            "reviewerSubRole": "Approver",
            "userNTID": reviewer["login"]
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
            "checklistIds": [],
            "tags": ["newTag", "addednewtag1"],
            "usage": "AND"
        },
        "reviewType": {
            "reviewTypeIds": [],
            "tags": ["T1", "testtags_list"],
            "usage": "OR"
        },
        "author": {
            "userNTID": author
        },
        "reviewRoles": reviewers,
        "taskLinks": [
            pr_url
        ]
    }

    try:

        response = requests.post(
            CREATE_REVIEW_URL,
            json=payload,
            headers={
                "Content-Type": "application/json"
            },
            timeout=60
        )

        response.raise_for_status()

        result = response.json()

        if result.get("returnId") == 1:

            task_id = result.get("taskIdStr", "")

            add_comment(
                repo,
                pr_number,
                github_token,
                f"✅ Review task created successfully: {task_id}"
            )

        else:

            error = result.get(
                "returnErrorMsg",
                result.get("returnMsg", "Unknown error")
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


if __name__ == "__main__":
    main()
