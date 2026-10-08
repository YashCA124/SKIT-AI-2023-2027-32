import pandas as pd


REQUIRED_COLUMNS = {
    "booking_id",
    "user_id",
    "parking_lot_id",
    "start_time",
    "end_time",
    "amount",
    "status"
}


OPTIONAL_COLUMNS = {
    "booking_time",
    "vehicle_type",
    "payment_status",
    "cancellation_time"
}


def validate_schema(df):

    actual_columns = set(df.columns)

    missing_columns = (
        REQUIRED_COLUMNS - actual_columns
    )

    unexpected_columns = (
        actual_columns
        - REQUIRED_COLUMNS
        - OPTIONAL_COLUMNS
    )

    return {
        "status":
            "passed"
            if not missing_columns
            else "failed",

        "missing_required_columns":
            sorted(list(missing_columns)),

        "unexpected_columns":
            sorted(list(unexpected_columns)),

        "column_count":
            len(actual_columns)
    }