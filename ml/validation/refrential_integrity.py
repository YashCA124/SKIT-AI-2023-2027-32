def check_referential_integrity(
    bookings,
    valid_users=None,
    valid_parking_lots=None
):

    errors = []

    if valid_users is not None:

        invalid_users = bookings[
            ~bookings["user_id"].isin(valid_users)
        ]

        if not invalid_users.empty:

            errors.append({
                "type": "invalid_user_id",
                "count": len(invalid_users)
            })

    if valid_parking_lots is not None:

        invalid_lots = bookings[
            ~bookings["parking_lot_id"]
            .isin(valid_parking_lots)
        ]

        if not invalid_lots.empty:

            errors.append({
                "type": "invalid_parking_lot_id",
                "count": len(invalid_lots)
            })

    return {
        "status":
            "passed"
            if not errors
            else "failed",

        "errors": errors
    }