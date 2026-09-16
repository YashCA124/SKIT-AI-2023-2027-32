def generate_analytics(df):

    if df.empty:
        return {
            "status": "no_data",
            "message": "No booking data available yet.",
            "total_bookings": 0,
            "total_revenue": 0,
            "average_booking_value": 0,
            "average_duration": 0,
            "peak_hours": [],
            "parking_lots": []
        }

    return {
        "status": "success",

        "total_bookings": int(
            len(df)
        ),

        "total_revenue": round(
            df["amount"].sum(),
            2
        ),

        "average_booking_value": round(
            df["amount"].mean(),
            2
        ),

        "average_duration": round(
            df["duration_hours"].mean(),
            2
        ),

        "peak_hours": get_peak_hours(df),

        "parking_lots": get_lot_analytics(df)
    }


def get_peak_hours(df):

    if df.empty:
        return []

    peak = (
        df.groupby("hour")
        .size()
        .sort_values(
            ascending=False
        )
        .head(5)
    )

    result = []

    for hour, bookings in peak.items():

        result.append({
            "hour": int(hour),
            "booking_count": int(bookings)
        })

    return result


def get_lot_analytics(df):

    if df.empty:
        return []

    result = (
        df.groupby("parking_lot_id")
        .agg(
            bookings=("booking_id", "count"),
            revenue=("amount", "sum"),
            average_duration=(
                "duration_hours",
                "mean"
            )
        )
        .reset_index()
    )

    result["revenue"] = result[
        "revenue"
    ].round(2)

    result["average_duration"] = result[
        "average_duration"
    ].round(2)

    return result.to_dict(
        orient="records"
    )