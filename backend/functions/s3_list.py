import boto3
from collections import defaultdict
import random

bucket = "<bucket_id>"
prefix = "refined/"
sample_limit_per_folder = 1000

s3 = boto3.client('s3')
paginator = s3.get_paginator('list_objects_v2')

# Get top-level folders
def get_top_folders():
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter='/')
    return [cp['Prefix'] for cp in response.get('CommonPrefixes', [])]

folder_estimates = {}

folders = get_top_folders()

for folder_prefix in folders:
    print(f"Sampling from: {folder_prefix}")
    sizes = []
    page_iterator = paginator.paginate(Bucket=bucket, Prefix=folder_prefix)

    for page in page_iterator:
        contents = page.get('Contents', [])
        for obj in contents:
            sizes.append(obj['Size'])
            if len(sizes) >= sample_limit_per_folder:
                break
        if len(sizes) >= sample_limit_per_folder:
            break

    if sizes:
        avg_size = sum(sizes) / len(sizes)
        estimated_total = avg_size * page['KeyCount']  # Use key count as rough object count
        folder_estimates[folder_prefix] = {
            "sampled_objects": len(sizes),
            "avg_object_size_bytes": avg_size,
            "estimated_total_size_bytes": estimated_total
        }
    else:
        folder_estimates[folder_prefix] = {
            "sampled_objects": 0,
            "avg_object_size_bytes": 0,
            "estimated_total_size_bytes": 0
        }

# Output
for folder, stats in folder_estimates.items():
    print(f"{folder} -> {stats}")

