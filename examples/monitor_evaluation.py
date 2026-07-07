"""Example: Monitor submission evaluation status."""

import sys
import time
from verdikta_sdk import VerdiktaClient, NotFoundError, VerdiktaAPIError

client = VerdiktaClient()

JOB_ID = sys.argv[1] if len(sys.argv) > 1 else "YOUR_JOB_ID"
SUBMISSION_ID = sys.argv[2] if len(sys.argv) > 2 else "YOUR_SUBMISSION_ID"

print(f"Monitoring submission {SUBMISSION_ID} for job {JOB_ID}\n")

# List all submissions for the job
submissions = client.list_submissions(JOB_ID)
print(f"Total submissions: {len(submissions)}")
for sub in submissions:
    print(f"  [{sub.id}] status={sub.status}")
print()

# Poll for evaluation
print("Waiting for evaluation...")
while True:
    try:
        evaluation = client.get_evaluation(JOB_ID, SUBMISSION_ID)
        print(f"\n✓ Evaluation complete!")
        print(f"  Score:  {evaluation.score}")
        print(f"  Passed: {evaluation.passed}")
        print(f"  Feedback: {evaluation.feedback}")
        if evaluation.criteria:
            print("  Criteria:")
            for c in evaluation.criteria:
                print(f"    - {c}")
        break
    except NotFoundError:
        print("  Not ready yet, retrying in 30s...")
        time.sleep(30)
    except VerdiktaAPIError as e:
        print(f"  Error: {e}")
        sys.exit(1)
