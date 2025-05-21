import pandas as pd

# import numpy as np  # For np.nan
from pathlib import Path


def add_template_row_from_candle(
    candles_df: pd.DataFrame,
    template_df: pd.DataFrame,
    target_date_str: str,
    padding_for_max_cols=1.0,
    padding_for_min_cols=2.0,
):
    """
    Generates a new row for the template_dataframe based on a target candle
    from candles_dataframe.

    Args:
        candles_df (pd.DataFrame): DataFrame with candle data and indicators.
                                   Must have a 'date' column (datetime).
        template_df (pd.DataFrame): DataFrame with template parameters.
        target_date_str (str): The timestamp string for the target candle
                               (e.g., "2022-03-22T20:00:00Z").
        padding_for_max_cols (float): Value to ADD to the target indicator's value
                                      to set the threshold for 'max_' template columns.
                                      Condition: indicator < (target_value + padding_for_max_cols)
        padding_for_min_cols (float): Value to SUBTRACT from the target indicator's value
                                      to set the threshold for 'min_' template columns.
                                      Condition: indicator > (target_value - padding_for_min_cols)

    Returns:
        pd.DataFrame: A new template_dataframe with the generated row appended.
                      Returns the original template_df if target candle is not found.
    """
    try:
        # Convert target_date_str to Timestamp, assuming UTC if no tz specified
        # Pandas will infer timezone if present in string, otherwise naive.
        # If candles_df['date'] is timezone-aware, target_ts should also be.
        target_ts = pd.Timestamp(target_date_str)
    except ValueError:
        print(f"Error: Invalid target_date_str format: {target_date_str}")
        return template_df.copy()  # Return a copy to avoid modifying original on error

    if type(candles_df["date"].iloc[0]) is str:
        candles_df["date"] = pd.to_datetime(candles_df["date"])

    # Find the target candle
    target_candle_series = candles_df[candles_df["date"] == target_ts]
    if target_candle_series.empty:
        print(
            f"Warning: Target candle for date {target_date_str} not found in candles_dataframe."
        )
        return template_df.copy()  # Return a copy

    # If multiple candles match (should not happen with precise timestamp), take the first
    target_candle = target_candle_series.iloc[0]

    new_row_dict = {}

    # Handle special columns first
    new_row_dict["disabled"] = 0
    new_row_dict["sample_date"] = (
        target_ts  # Store as Timestamp, will be written to CSV as str
    )

    # Iterate over the columns of the *template_df* to decide what to populate
    for col_name in template_df.columns:
        if col_name in ["disabled", "sample_date"]:
            continue  # Already handled

        indicator_value_in_target = (
            pd.NA
        )  # Default to NA if not found or not applicable
        is_max = col_name.startswith("max_")
        is_min = col_name.startswith("min_")
        if not is_min and not is_max:
            print(
                f"Note: Column '{col_name}' in template_df doesn't follow 'max_' or 'min_' prefix. Setting to NA for new row."
            )
            continue

        indicator_name = col_name[4:]
        if indicator_name in target_candle.index and not pd.isna(
            target_candle[indicator_name]
        ):
            current_value = target_candle[indicator_name]
            correct_padding = padding_for_max_cols if is_max else -padding_for_min_cols
            if current_value < 0.1 and current_value > -0.1:
                correct_padding /= 10
            indicator_value_in_target = current_value + correct_padding

        new_row_dict[col_name] = indicator_value_in_target

    # Create a new DataFrame for the row, ensuring columns are in the same order as template_df
    new_row_df = pd.DataFrame([new_row_dict], columns=template_df.columns)

    # Append to a copy of the original template_df
    updated_template_df = pd.concat([template_df, new_row_df], ignore_index=True)

    return updated_template_df


candles_df = pd.read_csv(Path(__file__).parent / "bingx_btc_2024-12-05_2025-05-20.csv")
template_df = pd.read_csv(Path(__file__).parent / "btc_enter_params.csv")
output_df = add_template_row_from_candle(
    candles_df=candles_df,
    template_df=template_df,
    target_date_str="2025-03-22T20:00:00Z",
)
print(output_df)
