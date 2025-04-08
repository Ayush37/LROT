import boto3
from collections import defaultdict
import re

bucket_name = "<bucket_id>"
prefix = "refined/"
sample_limit = 1000  # Number of real files to sample per folder

s3 = boto3.client('s3')
paginator = s3.get_paginator('list_objects_v2')

# Regex for file-like keys (skip folders)
file_pattern = re.compile(r'.+\.(csv|parquet|json|txt|gz|orc|avro)$', re.IGNORECASE)

folder_estimates = {}

def sample_files(prefix):
    sizes = []
    total_keys_seen = 0
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            size = obj['Size']
            total_keys_seen += 1

            if not key.endswith('/') and size > 0 and file_pattern.match(key.split('/')[-1]):
                sizes.append(size)

            if len(sizes) >= sample_limit:
                break
        if len(sizes) >= sample_limit:
            break

    return sizes, total_keys_seen

def get_top_level_folders():
    resp = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix, Delimiter='/')
    return [cp['Prefix'] for cp in resp.get('CommonPrefixes', [])]

# Main logic
folders = get_top_level_folders()

for folder in folders:
    print(f"Sampling files from {folder}")
    sizes, total_keys = sample_files(folder)

    if sizes:
        avg_size = sum(sizes) / len(sizes)
        estimated_total_bytes = avg_size * total_keys
        estimated_total_tb = estimated_total_bytes / (1024 ** 4)
    else:
        avg_size = 0
        estimated_total_bytes = 0
        estimated_total_tb = 0

    folder_estimates[folder] = {
        "sampled_files": len(sizes),
        "total_keys_seen": total_keys,
        "avg_file_size_bytes": avg_size,
        "estimated_total_size_bytes": estimated_total_bytes,
        "estimated_total_size_tb": estimated_total_tb
    }

# Output the results
print("\n=== Folder Size Estimates ===")
for folder, stats in folder_estimates.items():
    print(f"{folder}: {stats['estimated_total_size_tb']:.3f} TB (sampled {stats['sampled_files']} files)")

