import os
import json
from datetime import datetime

from scheduler.celery_app import app

from validation.quality_check import (
    run_quality_checks
)

from validation.eda_monitor import (
    generate_eda_summary
)

from validation.validation_report import (
    save_validation_report
)

from etl.extract import (
    fetch_bookings,
    save_raw_data
)

from etl.transform import (
    transform_bookings
)

from etl.aggregate import (
    aggregate_booking_data
)

from analytics.analytics import (
    generate_analytics
)

from config import (
    BOOKINGS_ENDPOINT,
    RAW_DATA_PATH,
    PROCESSED_DATA_PATH,
    AGGREGATED_DATA_PATH
)


@app.task
def run_analytics():

    print("Starting scheduled analytics...")

    # -----------------------------------------
    # 1. Extract
    # -----------------------------------------

    bookings = fetch_bookings(
        BOOKINGS_ENDPOINT
    )

    print(
        f"Fetched {len(bookings)} bookings"
    )

    # -----------------------------------------
    # 2. Save raw data
    # -----------------------------------------

    raw_df = save_raw_data(
        bookings,
        RAW_DATA_PATH
    )

    # -----------------------------------------
    # 3. Transform
    # -----------------------------------------

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

    # -----------------------------------------
    # 4. Aggregate
    # -----------------------------------------

    aggregated_df = (
        aggregate_booking_data(
            transformed_df
        )
    )

    aggregated_df.to_csv(
        AGGREGATED_DATA_PATH,
        index=False
    )

    # -----------------------------------------
    # 5. Analytics
    # -----------------------------------------

    analytics = generate_analytics(
        transformed_df
    )


    if quality_report["overall_status"] == "FAILED":

        print(
        "WARNING: Data quality checks failed."
        )

        print(
        "Failed checks:",
        quality_report["failed_checks"]
        )

    

    # -----------------------------------------
    # 4. DATA QUALITY VALIDATION
    # -----------------------------------------

    print(
        "Running data quality checks..."
    )

    quality_report = run_quality_checks(
        transformed_df
    )

    # -----------------------------------------
    # 5. EDA MONITORING
    # -----------------------------------------

    print(
        "Generating EDA monitoring report..."
    )

    eda_report = generate_eda_summary(
        transformed_df
    )

    # -----------------------------------------
    # 6. SAVE QUALITY REPORT
    # -----------------------------------------

    report_path = save_validation_report(
        quality_report,
        eda_report
    )

    print(
        f"Quality report saved to: "
        f"{report_path}"
    )
    


    

    # -----------------------------------------
    # 6. Save analytics
    # -----------------------------------------

    output_directory = (
        "outputs/analytics"
    )

    os.makedirs(
        output_directory,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_file = (
        f"{output_directory}/"
        f"analytics_{timestamp}.json"
    )

    with open(
        output_file,
        "w"
    ) as file:

        json.dump(
            analytics,
            file,
            indent=4
        )

    print(
        "Scheduled analytics completed."
    )

    return analytics


































































































































































#