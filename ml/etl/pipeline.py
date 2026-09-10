import os

from extract import (
    fetch_bookings,
    save_raw_data
)

from transform import (
    transform_bookings
)

from aggregate import (
    aggregate_booking_data
)

from config import (
    BOOKINGS_ENDPOINT,
    RAW_DATA_PATH,
    PROCESSED_DATA_PATH,
    AGGREGATED_DATA_PATH
)


def run_pipeline():

    print("Starting ETL pipeline...")

    

    print("Fetching booking data...")

    bookings = fetch_bookings(
        BOOKINGS_ENDPOINT
    )

    print(
        f"Fetched {len(bookings)} bookings"
    )


    raw_df = save_raw_data(
        bookings,
        RAW_DATA_PATH
    )

    

    print("Transforming data...")

    transformed_df = transform_bookings(
        raw_df
    )

   

    os.makedirs(
        os.path.dirname(
            PROCESSED_DATA_PATH
        ),
        exist_ok=True
    )

    transformed_df.to_csv(
        PROCESSED_DATA_PATH,
        index=False
    )

    

    print("Aggregating booking data...")

    aggregated_df = aggregate_booking_data(
        transformed_df
    )

    \

    aggregated_df.to_csv(
        AGGREGATED_DATA_PATH,
        index=False
    )

    print(
        "ETL pipeline completed successfully."
    )

    print(
        f"Processed rows: "
        f"{len(transformed_df)}"
    )

    print(
        f"Aggregated rows: "
        f"{len(aggregated_df)}"
    )


if __name__ == "__main__":
    run_pipeline()