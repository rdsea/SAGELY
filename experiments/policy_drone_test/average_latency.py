import csv
import sys

# Check if the file path is provided as an argument
if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <csv_file_path>")
    sys.exit(1)

csv_file = sys.argv[1]

try:
    total_sum = 0
    count = 0
    error = 0

    with open(csv_file) as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row

        for row in reader:
            if row:  # Ensure the row is not empty
                if row[0] != "inf":
                    try:
                        total_sum += float(
                            row[0]
                        )  # Assuming latency values are in the second column
                        count += 1
                    except ValueError:
                        print(f"Skipping invalid data: {row[0]}")
                elif row[0] == "inf":
                    error += 1

    # Calculate the average
    if count > 0:
        average_latency = total_sum / count
        print(f"Average Latency: {average_latency:.4f} seconds")
        print(f"Error percentage:  {error}%")
    else:
        print("No valid latency values found.")

except FileNotFoundError:
    print(f"Error: File '{csv_file}' not found!")
    sys.exit(1)
