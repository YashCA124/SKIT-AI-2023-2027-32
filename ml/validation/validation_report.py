import json
import os

from datetime import datetime


def save_validation_report(
    quality_report,
    eda_report
):

    os.makedirs(
        "outputs/quality",
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    report = {

        "generated_at":
            datetime.now().isoformat(),

        "data_quality":
            quality_report,

        "eda":
            eda_report
    }

    path = (
        "outputs/quality/"
        f"quality_report_{timestamp}.json"
    )

    with open(
        path,
        "w"
    ) as file:

        json.dump(
            report,
            file,
            indent=4,
            default=str
        )

    return path