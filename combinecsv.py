import pandas as pd
import glob

# Path to your folder
csv_files = glob.glob("/home/user/Csv/*.csv")

# Combine all CSVs
df_list = []
for file in csv_files:
    region_name = file.split("/")[-1].split("_")[0]  # Extract region from filename
    df = pd.read_csv(file)
    df['region'] = region_name
    df_list.append(df)

combined_df = pd.concat(df_list, ignore_index=True)

# Save final combined dataset
combined_df.to_csv("global_fire_testing_data.csv", index=False)
