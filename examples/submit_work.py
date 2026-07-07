"""Example: Submit work to a Verdikta bounty."""

import sys
from verdikta_sdk import VerdiktaClient, VerdiktaAPIError

client = VerdiktaClient()

# Replace with an actual job ID
JOB_ID = sys.argv[1] if len(sys.argv) > 1 else "YOUR_JOB_ID"

# Files to submit (adjust paths as needed)
files = ["solution.py", "report.pdf"]

print(f"Job: {JOB_ID}")
print(f"Files: {files}\n")

# Step 1: Dry run
print("Running dry-run validation...")
try:
    validation = client.dry_run_submit(JOB_ID, files=files)
    print("  Validation result:", validation)
except VerdiktaAPIError as e:
    print(f"  Validation failed: {e}")
    sys.exit(1)

# Step 2: Actual submission
print("\nSubmitting...")
try:
    submission = client.submit(JOB_ID, files=files)
    print(f"  Submission ID: {submission.id}")
    print(f"  Status: {submission.status}")
except VerdiktaAPIError as e:
    print(f"  Submission failed: {e}")
    sys.exit(1)
