import boto3
import re

bucket_name = "<bucket_id>"
base_prefix = "refined/reporting/"
max_sample = 5000  # set to None for full scan

s3 = boto3.client('s3')
paginator = s3.get_paginator('list_objects_v2')

# Only consider real files (skip folders or 0-byte keys that are placeholders)
def is_real_file(key, size):
    return not key.endswith('/') and size > 0

object_sizes = []
total_object_count = 0

for page in paginator.paginate(Bucket=bucket_name, Prefix=base_prefix):
    for obj in page.get('Contents', []):
        key = obj['Key']
        size = obj['Size']

        if is_real_file(key, size):
            object_sizes.append(size)
            total_object_count += 1

            # Limit if sampling
            if max_sample and len(object_sizes) >= max_sample:
                break
    if max_sample and len(object_sizes) >= max_sample:
        break

# Calculate stats
if object_sizes:
    avg_size = sum(object_sizes) / len(object_sizes)
    estimated_total_bytes = avg_size * total_object_count
    estimated_total_tb = estimated_total_bytes / (1024 ** 4)

    print(f"Scanned {len(object_sizes)} real files (out of {total_object_count} total)")
    print(f"Avg size: {avg_size:.2f} bytes")
    print(f"Estimated total size: {estimated_total_tb:.3f} TB")
else:
    print("No real data files found.")

