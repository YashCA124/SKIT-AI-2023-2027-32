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

    required_columns = group_columns + [
        "booking_id",
        "user_id",
        "amount",
        "duration_hours",
    ]
    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]
    if missing_columns:
        raise ValueError(
            f"Missing columns for booking aggregation: {missing_columns}"
        )

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