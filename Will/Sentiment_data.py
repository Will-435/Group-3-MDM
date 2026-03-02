import pandas as pd
import numpy as np

CLEAN_PATH = "TB-2/clean_data.csv"
TARGET_TITLE = "% who feel safe in their local area after dark"
PATH = 'TB-2/Sentiment.csv'


def open_file(file_path):
    
    file = pd.read_csv(file_path)
    df = pd.DataFrame(file)

    df_1 = df[df['Public_Title'] == '% who feel safe in their local area after dark']
    df_2 = df_1[df_1['Year'] == 2024]
    # df_2.to_csv('TB-2/clean_data.csv', index = False)

    print(df_2)
    print('\n', f'The number of records is: {df_2.shape[0]}')
    print('\n', f'the number of question sasked was : {df['Public_Title'].nunique()}')

    # print(clean_df)
    # print('\n ', clean_df.size)
    # print('\n', f'The number of wards is: {df['Ward_name'].unique()}')

    return df_2


df = pd.read_csv(CLEAN_PATH)

recent_year = df["Year"]

# Filter to the target indicator and real wards only
# (Your file also contains non-ward group rows where Ward_name is NaN)
required_cols = {"Public_Title", "Ward_name", "Ward_Group_Statistic", "Standard_Error_1", "Bristol_average"}
missing = required_cols - set(df.columns)
if missing:
    raise ValueError(f"Missing required columns: {sorted(missing)}")

d = df[df["Public_Title"].astype(str).str.strip() == TARGET_TITLE].copy()
d = d[d["Ward_name"].notna()].copy()

if d.empty:
    raise ValueError(f"No ward rows found for Public_Title == '{TARGET_TITLE}' in year {recent_year}.")

# Extract point estimates + SEs
p_hat = d["Ward_Group_Statistic"].astype(float).to_numpy()
se = d["Standard_Error_1"].astype(float).to_numpy()

# Use the city-wide Bristol average for this indicator as the prior mean (mu)
mu = float(d["Bristol_average"].iloc[0])

tau2 = float(np.var(p_hat, ddof=1) - np.mean(se ** 2))
tau2 = max(0.0, tau2)

# Shrinkage weights and shrunk estimates
# w_i = tau^2 / (tau^2 + SE_i^2)
# p_tilde_i = w_i * p_hat_i + (1 - w_i) * mu
if tau2 == 0.0:
    # No detectable between-ward variation beyond sampling noise; everyone shrinks to mu.
    w = np.zeros_like(se)
    p_tilde = np.full_like(p_hat, fill_value=mu, dtype=float)
else:
    w = tau2 / (tau2 + se ** 2)
    p_tilde = w * p_hat + (1 - w) * mu

# -----------------------------
# Build output + rank worst -> best (lowest shrunk safety -> highest)
# -----------------------------
out = d[["Ward_name", "Ward_Group_Statistic", "Standard_Error_1"]].copy()
out["shrunk_estimate"] = p_tilde
out["weight_w"] = w
out["year"] = recent_year

out = out.sort_values("shrunk_estimate", ascending=True).reset_index(drop=True)

# Final ordered list of wards (worst -> best sentiment)
ward_ranking = out["Ward_name"].tolist()

print(f"mu (Bristol average): {mu}")
print(f"tau^2 (between-ward variance): {tau2:.4f}")
print("\nWorst -> Best wards (by shrunk estimate):")
for i, ward in enumerate(ward_ranking, start=1):
    print(f"{i:02d}. {ward}")


df = open_file(PATH)
