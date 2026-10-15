import pandas as pd
import numpy as np


def detect_iqr_outliers(
    df,
    column
):

    if column not in df.columns:
        return {
            "status": "skipped"
        }

    values = pd.to_numeric(
        df[column],
        errors="coerce"
    ).dropna()

    if values.empty:
        return {
            "status": "skipped"
        }

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)

    iqr = q3 - q1

    lower_bound = (
        q1 - 1.5 * iqr
    )

    upper_bound = (
        q3 + 1.5 * iqr
    )

    outliers = values[
        (values < lower_bound)
        |
        (values > upper_bound)
    ]

    return {
        "status": "passed",

        "outlier_count": int(
            len(outliers)
        ),

        "lower_bound": float(
            lower_bound
        ),

        "upper_bound": float(
            upper_bound
        )
    }












def detect_numeric_anomalies(df):

    return {

        "revenue":
            detect_iqr_outliers(
                df,
                "amount"
            ),

        "duration":
            detect_iqr_outliers(
                df,
                "duration_hours"
            )
    }



def check_duplicate_records(df):

    exact_duplicates = int(
        df.duplicated().sum()
    )

    booking_duplicates = 0

    if "booking_id" in df.columns:

        booking_duplicates = int(
            df["booking_id"]
            .duplicated()
            .sum()
        )

    return {

        "status":
            "passed"
            if (
                exact_duplicates == 0
                and
                booking_duplicates == 0
            )
            else "failed",

        "exact_duplicates":
            exact_duplicates,

        "booking_id_duplicates":
            booking_duplicates
    }





















































































































































































#