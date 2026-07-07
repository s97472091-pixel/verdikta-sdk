"""Example: Discover open bounties on Verdikta."""

from verdikta_sdk import VerdiktaClient

# Uses VERDIKTA_API_KEY env var by default
client = VerdiktaClient()

print("=== Open bounties ===")
jobs = client.list_jobs(status="open", limit=20)
for job in jobs:
    print(f"  [{job.id}] {job.title}")
    print(f"    Bounty: ${job.bounty_usd}  |  Hours left: {job.hours_left}")
    print(f"    Type: {job.work_product_type}")
    print()

print(f"Total: {len(jobs)} bounties\n")

print("=== High-value bounties (> $500) ===")
high_value = client.list_jobs(status="open", min_bounty_usd=500)
for job in high_value:
    print(f"  ${job.bounty_usd} — {job.title}")

print("\n=== Search for 'python' ===")
python_jobs = client.list_jobs(search="python", status="open")
for job in python_jobs:
    print(f"  {job.title} (${job.bounty_usd})")
