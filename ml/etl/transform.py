import pandas as pd
import numpy as np


def transform_bookings(df):

    if df.empty:
        return df

    df = df.copy()

    

    date_columns = [
        "booking_time",
        "start_time",
        "end_time",
        "cancellation_time"
    ]

    for column in date_columns:

        if column in df.columns:

            df[column] = pd.to_datetime(
                df[column],
                errors="coerce"
            )

   

    if "start_time" in df.columns:

        df = df[
            df["start_time"].notna()
        ]

    if "end_time" in df.columns:

        df = df[
            df["end_time"].notna()
        ]


    if (
        "start_time" in df.columns
        and
        "end_time" in df.columns
    ):

        df["duration_hours"] = (
            (
                df["end_time"]
                -
                df["start_time"]
            )
            .dt.total_seconds()
            / 3600
        )

        df = df[
            df["duration_hours"] > 0
        ]

    

    df["hour"] = (
        df["start_time"].dt.hour
    )

    df["day_of_week"] = (
        df["start_time"].dt.dayofweek
    )

    df["day"] = (
        df["start_time"].dt.day
    )

    df["month"] = (
        df["start_time"].dt.month
    )

    df["year"] = (
        df["start_time"].dt.year
    )


    df["is_weekend"] = (
        df["day_of_week"] >= 5
    ).astype(int)

    

    df["is_peak_hour"] = (
        df["hour"].between(17, 21)
    ).astype(int)

    

    if "amount" in df.columns:

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        )

        df["amount"] = (
            df["amount"].fillna(0)
        )

    

    categorical_columns = [
        "vehicle_type",
        "status",
        "payment_status"
    ]

    for column in categorical_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .astype(str)
                .str.lower()
                .str.strip()
            )

    return df