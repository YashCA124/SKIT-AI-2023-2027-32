import pandas as pd


def aggregate_booking_data(df):

    if df.empty:
        return pd.DataFrame()

    group_columns = [
        "parking_lot_id",
        "year",
        "month",
        "day",
        "day_of_week",
        "hour",
        "is_weekend"
    ]

    # Only use columns that actually exist
    group_columns = [
        col for col in group_columns
        if col in df.columns
    ]

    aggregated = (
        df
        .groupby(group_columns)
        .agg(
            booking_count=(
                "booking_id",
                "count"
            ),

            unique_users=(
                "user_id",
                "nunique"
            ),

            total_revenue=(
                "amount",
                "sum"
            ),

            average_booking_value=(
                "amount",
                "mean"
            ),

            average_duration=(
                "duration_hours",
                "mean"
            )
        )
        .reset_index()
    )

    return aggregated