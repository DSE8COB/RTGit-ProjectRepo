import json
import os
import sys
import requests

CREATE_REVIEW_URL = (
    "https://ews-emea.api.bosch.com"
    "/reviewtool/create-task/t/v1/createReview/task/external/bbm/14"
)


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
