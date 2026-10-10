import pandas as pd


def generate_eda_summary(df):

    if df.empty:

        return {
            "status": "NO_DATA"
        }

    summary = {

        "row_count":
            int(len(df)),

        "column_count":
            int(len(df.columns)),

        "columns":
            list(df.columns),

        "missing_values":
            df.isnull().sum().to_dict(),

        "unique_users":
            int(
                df["user_id"].nunique()
            )
            if "user_id" in df.columns
            else None,

        "unique_parking_lots":
            int(
                df["parking_lot_id"].nunique()
            )
            if "parking_lot_id" in df.columns
            else None
    }

    if "amount" in df.columns:

        summary["revenue"] = {

            "total":
                float(df["amount"].sum()),

            "average":
                float(df["amount"].mean()),

            "minimum":
                float(df["amount"].min()),

            "maximum":
                float(df["amount"].max())
        }

    if "duration_hours" in df.columns:

        summary["duration"] = {

            "average":
                float(
                    df["duration_hours"].mean()
                ),

            "minimum":
                float(
                    df["duration_hours"].min()
                ),

            "maximum":
                float(
                    df["duration_hours"].max()
                )
        }

    if "hour" in df.columns:

        summary["booking_by_hour"] = (
            df["hour"]
            .value_counts()
            .sort_index()
            .to_dict()
        )

    if "vehicle_type" in df.columns:

        summary["vehicle_distribution"] = (
            df["vehicle_type"]
            .value_counts()
            .to_dict()
        )

    if "status" in df.columns:

        summary["booking_status_distribution"] = (
            df["status"]
            .value_counts()
            .to_dict()
        )

    return summary
def generate_hourly_demand(df):

    if df.empty:
        return []

    if "hour" not in df.columns:
        return []

    if "parking_lot_id" not in df.columns:
        return []

    hourly = (
        df.groupby(
            [
                "parking_lot_id",
                "day_of_week",
                "hour"
            ]
        )
        .size()
        .reset_index(
            name="booking_count"
        )
    )

    return hourly.to_dict(
        orient="records"
    )