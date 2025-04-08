import boto3
import random

bucket_name = "<bucket_id>"
prefix = "refined/reporting/"
sample_limit = 5000  # How many real files to sample

s3 = boto3.client('s3')
paginator = s3.get_paginator('list_objects_v2')

sample_sizes = []
total_file_count = 0

print(f"Scanning all objects under s3://{bucket_name}/{prefix}")

for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
    for obj in page.get('Contents', []):
        key = obj['Key']
        size = obj['Size']

        # Skip folder-like placeholders
        if key.endswith('/') or size == 0:
            continue

        # Count every real file
        total_file_count += 1

        # Sampling (randomized or first N)
        if len(sample_sizes) < sample_limit:
            sample_sizes.append(size)
        else:
            # Reservoir sampling for better randomness
            i = random.randint(0, total_file_count - 1)
            if i < sample_limit:
                sample_sizes[i] = size

# Estimate
if sample_sizes:
    avg_sample_size = sum(sample_sizes) / len(sample_sizes)
    estimated_total_bytes = avg_sample_size * total_file_count
    estimated_total_tb = estimated_total_bytes / (1024 ** 4)

    print("\n=== Results ===")
    print(f"Sample size: {len(sample_sizes)}")
    print(f"Total real file count: {total_file_count}")
    print(f"Avg file size (sample): {avg_sample_size:.2f} bytes")
    print(f"Estimated total size: {estimated_total_bytes:.2f} bytes ({estimated_total_tb:.3f} TB)")
else:
    print("No real files found.")

