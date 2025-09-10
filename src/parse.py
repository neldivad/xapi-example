import re
from typing import Optional
import pandas as pd

def extract_first_username(text, custom_message: Optional[str] = None):
    """
    Extract the first @username from tweet text.
    Returns the username without the @ symbol, or None if no username found.

    If username None, in practice, this is a result of a thread to your own original post. 
    """
    if not isinstance(text, str):
        return None
    
    # Find all @usernames in the text
    usernames = re.findall(r'@(\w+)', text)

    if usernames: 
        return usernames[0]
    else:
        # No username found. Usually a result of a thread to your own original post. 
        print(f"No username found in text: {text}")
        return custom_message



# Engagement classification
def classify_by_engagement_quantile(df, username_col, target_col, bins=5):
    """
    Classify users into quantile-based engagement categories.
    
    Parameters:
    - df: DataFrame with engagement stats
    - username_col: Column name for usernames
    - target_col: Column name for engagement metric to classify by
    - bins: Number of quantile bins (3-10)
    """
    # Create quantile-based bins
    df[f'{target_col}_category'] = pd.qcut(
        df[target_col], 
        q=bins, 
        labels=[f'Q{i+1}' for i in range(bins)],
        duplicates='drop'  # Handle duplicate values
    )
    
    # Create more descriptive labels
    category_mapping = {
        f'Q{i+1}': f'Q{i+1}' for i in range(bins)
    }
    
    df[f'{target_col}_category'] = df[f'{target_col}_category'].map(category_mapping)
    return df


def classify_by_cumsum_auto(df, username_col, target_col, n_categories=4):
    """
    Automatically classify users by cumulative sum with smart percentiles.

    Quantile based classification is not as accurate as cumulative sum based classification for power distribution. 

    Instead of finding breakpoints by percentiles, we can find breakpoints by cumulative sum for a target metric 
    
    EG: 50% of total views as t1, 80% of total views as t2, 100% of total views as t3
    
    Parameters:
    - df: DataFrame with engagement stats
    - username_col: Column name for usernames
    - target_col: Column name for engagement metric to classify by
    - n_categories: Number of categories to create
    """
    # Sort by target column in descending order
    df_sorted = df.sort_values(target_col, ascending=False).copy()
    
    # Calculate cumulative sum and percentage
    df_sorted['cumsum'] = df_sorted[target_col].cumsum()
    total_sum = df_sorted[target_col].sum()
    df_sorted['cumsum_percent'] = df_sorted['cumsum'] / total_sum
    
    # Find natural breakpoints (where cumulative percentage changes significantly)
    if n_categories == 3:
        percentiles = [0.5, 0.8, 1.0]  # Top 50%, 50-80%, 80-100%
    elif n_categories == 4:
        percentiles = [0.2, 0.5, 0.8, 1.0]  # Top 20%, 20-50%, 50-80%, 80-100%
    elif n_categories == 5:
        percentiles = [0.1, 0.3, 0.6, 0.85, 1.0]  # Top 10%, 10-30%, 30-60%, 60-85%, 85-100%
    else:
        # Create evenly spaced percentiles
        percentiles = [i/n_categories for i in range(1, n_categories+1)]
    
    # Create conditions and labels
    conditions = []
    labels = []
    
    for i, percentile in enumerate(percentiles):
        if i == 0:
            conditions.append(df_sorted['cumsum_percent'] <= percentile)
            labels.append(f'Top-{int(percentile*100)}%')
        else:
            prev_percentile = percentiles[i-1]
            conditions.append(
                (df_sorted['cumsum_percent'] > prev_percentile) & 
                (df_sorted['cumsum_percent'] <= percentile)
            )
            labels.append(f'{int(prev_percentile*100)}%-{int(percentile*100)}%')
    
    # Apply classification
    df_sorted[f'{target_col}_category'] = np.select(conditions, labels, default='Bottom')
    
    return df_sorted