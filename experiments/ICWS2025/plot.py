import pandas as pd
import os
import sys


def calculate_average(csv_filename):
    # Read the CSV file using pandas
    data = pd.read_csv(csv_filename)

    # Ensure there is only one column
    if data.shape[1] != 1:
        raise ValueError(f"CSV file '{csv_filename}' should have exactly one column.")

    # The column name will be the first (and only) column in the CSV file
    column_name = data.columns[0]

    # Calculate the average of the single column
    average = data[column_name].mean()

    return average


if __name__ == "__main__":
    # Check if the correct number of arguments is provided
    if len(sys.argv) != 2:
        print("Usage: python script.py <folder_path>")
        sys.exit(1)

    # The folder path passed as argument
    folder_path = sys.argv[1]

    try:
        # List all files in the folder
        files = os.listdir(folder_path)

        # Filter out CSV files
        csv_files = [f for f in files if f.endswith(".csv")]

        total_average = 0
        count = 0

        # Loop through each CSV file and calculate the average
        for csv_file in csv_files:
            csv_filepath = os.path.join(folder_path, csv_file)
            try:
                avg = calculate_average(csv_filepath)
                print(f"The average value in file '{csv_file}' is: {avg}")
                total_average += avg
                count += 1
            except Exception as e:
                print(f"Error processing file '{csv_file}': {e}")

        # Calculate the final average
        final_average = total_average / count if count > 0 else 0
        print(f"The final average from all files is: {final_average}")

    except Exception as e:
        print(f"Error: {e}")
