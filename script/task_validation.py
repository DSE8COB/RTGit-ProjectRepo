import requests
import sys
import os

# Arguments
pr_json = sys.argv[1]
repository = sys.argv[2]
pr_number = sys.argv[3]
task_id = sys.argv[4]

github_token = os.getenv("GITHUB_TOKEN")

url = "https://ews-emea.api.bosch.com/reviewtool/task-status/t/v1/reviewdetails/task/external/getAllTaskDetails"

headers = {
    "KeyId": "9bc39618-a714-4d87-aa6a-c4fd4985d9ba",
    "Content-Type": "application/json"
}

payload = [task_id]

try:
    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    print("Response:", data)

    if data.get("returnId") != 1:
        print("❌ API returned failure")
        sys.exit(1)

    task_details = data.get("taskDetail", [])

    if not task_details:
        print("❌ No task details found")
        sys.exit(1)

    phase_name = task_details[0].get("phaseName", "")

    print(f"Task Status: {phase_name}")

    if phase_name.lower() == "completed":

        comment_url = (
            f"https://api.github.com/repos/"
            f"{repository}/issues/{pr_number}/comments"
        )

        comment_headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json"
        }

        comment_payload = {
            "body": f"✅ Task completed successfully: {task_id}"
        }

        comment_response = requests.post(
            comment_url,
            headers=comment_headers,
            json=comment_payload,
            timeout=30
        )

        comment_response.raise_for_status()

        print(f"✅ Comment added for task {task_id}")
        sys.exit(0)

    elif phase_name.lower() == "inprogress":
        print(f"ℹ️ Task {task_id} is still in progress - please close the task")
        sys.exit(1)

    else:
        print(f"ℹ️ Task {task_id} is in status: {phase_name}")
        sys.exit(0)

except Exception as e:
    print("❌ ERROR:", str(e))
    sys.exit(1)
