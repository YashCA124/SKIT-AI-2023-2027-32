import pandas as pd
import numpy as np


def check_missing_values(df):

    missing = df.isnull().sum()

    missing = missing[
        missing > 0
    ]

    return missing.to_dict()


def check_duplicates(df):

    if "booking_id" not in df.columns:
        return {
            "status": "skipped",
            "reason": "booking_id column not found"
        }

    duplicate_count = int(
        df["booking_id"].duplicated().sum()
    )

    return {
        "status": "passed"
        if duplicate_count == 0
        else "failed",

        "duplicate_count": duplicate_count
    }


def check_invalid_duration(df):

    if "duration_hours" not in df.columns:
        return {
            "status": "skipped"
        }

    invalid_count = int(
        (
            df["duration_hours"].isna()
            |
            (df["duration_hours"] <= 0)
        ).sum()
    )

    return {
        "status": "passed"
        if invalid_count == 0
        else "failed",

        "invalid_duration_count": invalid_count
    }


def check_negative_revenue(df):

    if "amount" not in df.columns:
        return {
            "status": "skipped"
        }

    invalid_count = int(
        (df["amount"] < 0).sum()
    )

    return {
        "status": "passed"
        if invalid_count == 0
        else "failed",

        "negative_revenue_count": invalid_count
    }


def check_invalid_timestamps(df):

    result = {
        "status": "passed",
        "invalid_start_time": 0,
        "invalid_end_time": 0
    }

    if "start_time" in df.columns:

        result["invalid_start_time"] = int(
            df["start_time"].isna().sum()
        )

    if "end_time" in df.columns:

        result["invalid_end_time"] = int(
            df["end_time"].isna().sum()
        )

    total_invalid = (
        result["invalid_start_time"]
        +
        result["invalid_end_time"]
    )

    if total_invalid > 0:
        result["status"] = "failed"

    return result


def check_valid_status(df):

    if "status" not in df.columns:
        return {
            "status": "skipped"
        }

    allowed_statuses = {
        "pending",
        "confirmed",
        "completed",
        "cancelled",
        "canceled"
    }

    values = set(
        df["status"]
        .dropna()
        .astype(str)
        .str.lower()
        .unique()
    )

    invalid_values = values - allowed_statuses

    return {
        "status": "passed"
        if len(invalid_values) == 0
        else "failed",

        "invalid_statuses": list(
            invalid_values
        )
    }

def check_vehicle_type(df):

    if "vehicle_type" not in df.columns:
        return {
            "status": "skipped"
        }

    allowed_types = {
        "car",
        "bike",
        "suv",
        "truck",
        "ev"
    }

    values = set(
        df["vehicle_type"]
        .dropna()
        .astype(str)
        .str.lower()
        .str.strip()
        .unique()
    )

    invalid_values = values - allowed_types

    return {
        "status": "passed"
        if len(invalid_values) == 0
        else "failed",

        "invalid_vehicle_types": list(
            invalid_values
        )
    }

def check_missing_booking_ids(df):

    if "booking_id" not in df.columns:
        return {
            "status": "failed",
            "reason": "booking_id column missing"
        }

    missing_count = int(
        df["booking_id"].isna().sum()
    )

    return {
        "status": "passed"
        if missing_count == 0
        else "failed",

        "missing_booking_id_count": missing_count
    }

def run_quality_checks(df):

    if df.empty:

        return {
            "overall_status": "NO_DATA",
            "row_count": 0,
            "checks": {}
        }

    checks = {

        "missing_values":
            check_missing_values(df),

        "duplicates":
            check_duplicates(df),

        "booking_ids":
            check_missing_booking_ids(df),

        "duration":
            check_invalid_duration(df),

        "revenue":
            check_negative_revenue(df),

        "timestamps":
            check_invalid_timestamps(df),

        "status":
            check_valid_status(df),

        "vehicle_type":
            check_vehicle_type(df)
    }

    failed_checks = []

    for name, result in checks.items():

        if isinstance(result, dict):

            if result.get("status") == "failed":
                failed_checks.append(name)

    return {

        "overall_status":
            "FAILED"
            if failed_checks
            else "PASSED",

        "row_count": len(df),

        "failed_checks":
            failed_checks,

        "checks":
            checks
    }