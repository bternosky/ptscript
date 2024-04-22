#!/usr/bin/env python3
# coding: utf-8
import argparse
import csv
import datetime
from typing import Any, TypeAlias

RowType: TypeAlias = dict[str, Any]
MainType: TypeAlias = dict[str, list[RowType]]


TODAY = datetime.datetime.now().date()  # noqa: DTZ005


def get_appt_date_as_date(appt_str: str) -> datetime.date:
    return datetime.datetime.strptime(appt_str, "%m/%d/%Y").date()  # noqa: DTZ007


def read_main_sheet(*, fname: str) -> MainType:
    headers: list[str] = []
    data: MainType = {}

    has_been_seen: dict[tuple[str, datetime.date], bool] = {}

    for ct, line in enumerate(
        csv.reader(open(fname, "r", encoding="utf-8"))  # noqa: SIM115
    ):  # noqa: SSIM115
        line = [x.strip() for x in line]
        if ct == 0:
            headers = [x.upper() for x in line]
            continue

        row_dict: dict[str, Any] = dict(zip(headers, line))
        appt_date = get_appt_date_as_date(appt_str=row_dict["APPOINTMENT DATE"])
        row_dict["APPT DATE AS DATE"] = appt_date

        # Add row num to the dict
        row_dict["ROW_NUM"] = ct + 1

        key = (row_dict["PATIENT NAME"], row_dict["APPT DATE AS DATE"])
        if key in has_been_seen:
            print(
                f'ERROR: Duplicate entry for patient: {row_dict["PATIENT NAME"]} with date: {appt_date}'
            )
            continue

        has_been_seen[key] = True
        data.setdefault(row_dict["PATIENT NAME"], []).append(row_dict)

    return data


def write_row(*, csv_fp: Any, row: RowType) -> None:
    csv_fp.writerow(
        [
            row["PATIENT NAME"],
            row["CASE TITLE"],
            row["TREATING THERAPIST"],
            row["CASE THERAPIST"],
            row["APPOINTMENT TYPE"],
            row["APPOINTMENT DATE"],
        ]
    )


def process_data(*, main_data: MainType, csv_fp: Any) -> None:
    output_rows: list[RowType] = []

    # We matched. Ignore main/lead appts that match date. Only show those in future
    for _patient_name, rows in sorted(main_data.items()):
        past_appt: RowType | None = None
        has_appt_next_week = False

        for row in sorted(rows, key=lambda x: x["APPT DATE AS DATE"]):
            # Skip any date in the past
            if row["APPT DATE AS DATE"] < TODAY:
                past_appt = row
                continue

            has_appt_next_week = True

        if past_appt and not has_appt_next_week:
            output_rows.append(past_appt)

    for row in sorted(
        output_rows, key=lambda x: (x["PATIENT NAME"], x["APPT DATE AS DATE"])
    ):
        write_row(csv_fp=csv_fp, row=row)


def main() -> None:
    parser = argparse.ArgumentParser(prog="PTReport", description="Generate PT Report")
    parser.add_argument("mainsheet")
    args = parser.parse_args()

    main_data = read_main_sheet(fname=args.mainsheet)

    csv_name = f'output_{TODAY.strftime("%Y%m%d")}.csv'
    csv_fp = csv.writer(open(csv_name, "w", encoding="utf-8"))  # noqa: SIM115
    csv_fp.writerow(
        [
            "Patient Name",
            "Case Title",
            "Treating Therapist",
            "Case Therapist",
            "Appointment Type",
            "Appointment Date",
        ]
    )
    process_data(main_data=main_data, csv_fp=csv_fp)


if __name__ == "__main__":
    main()
