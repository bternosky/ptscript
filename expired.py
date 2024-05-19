#!/usr/bin/env python3
# coding: utf-8
import argparse
import csv
import datetime
import pprint
from typing import Any, TypeAlias

RowType: TypeAlias = dict[str, Any]
PrescriptionType: TypeAlias = dict[str, datetime.date]
VisitRow: TypeAlias = dict[str, Any]
VisitType: TypeAlias = dict[str, list[VisitRow]]


def normalize_name(*, name: str) -> str:
    # Names have extraneous white space SOMETIMES like "LAST , FIRST" - so remove spaces
    # ALso remove commas and periods
    if name.startswith("XXBENDE"):
        breakpoint()
    normalized_name = name.encode("latin-1", "ignore").decode("latin-1")
    normalized_name = normalized_name.replace(" ", "")
    normalized_name = normalized_name.replace(",", "")
    normalized_name = normalized_name.replace(".", "")
    if normalized_name.startswith("BENDE"):
        print(f"{name=}, {normalized_name=}, normalized={[ord(x) for x in normalized_name]}")
    return normalized_name


def read_prescription_sheet(*, fname: str) -> PrescriptionType:
    found_headers: bool = False

    prescription_data: PrescriptionType = {}

    for line in csv.reader(open(fname, "r", encoding="utf-8")):  # noqa: SIM115
        line = [x.strip() for x in line]
        if not found_headers:
            if "PATIENT NAME" in line[0].upper():
                found_headers = True
                continue
            else:
                continue

        if line[0] == "":
            break

        if line[2] == "0000-00-00":
            appt_date = "0000-00-00"
        else:
            appt_date = datetime.datetime.strptime(line[2], "%Y-%m-%d").date()  # noqa: DTZ007

        normalized_name = normalize_name(name=line[0])
        prescription_data[normalized_name] = appt_date

    return prescription_data


def read_visit_sheet(*, fname: str) -> VisitType:
    visit_data: VisitType = {}

    headers: list[str] = []

    for ct, line in enumerate(csv.reader(open(fname, "r", encoding="utf-8"))):  # noqa: SIM115
        line = [x.strip() for x in line]
        if ct == 0:
            headers = [x.upper() for x in line]
            continue

        row_dict: VisitRow = dict(zip(headers, line))
        row_dict["APPOINTMENT DATE"] = datetime.datetime.strptime(row_dict["APPOINTMENT DATE"], "%m/%d/%Y").date()  # noqa: DTZ007

        # Noramlize the name to match prescription
        normalized_name = normalize_name(name=row_dict["PATIENT NAME"])
        visit_data.setdefault(normalized_name, []).append(row_dict)

    return visit_data


def write_row(*, csv_fp: Any, match_name: str, end_date: datetime.date, visits: VisitRow) -> None:
    for visit in visits:
        csv_fp.writerow(
            [
                visit["PATIENT NAME"],
                end_date,
                visit["CLINIC NAME"],
                visit["CASE TITLE"],
                visit["TREATING THERAPIST"],
                visit["CASE THERAPIST"],
                visit["APPOINTMENT TYPE"],
                visit["APPOINTMENT DATE"],
                visit["START TIME"],
                visit["END TIME"],
            ]
        )


def main() -> None:
    parser = argparse.ArgumentParser(prog="PTReport", description="Generate PT Report")
    parser.add_argument("-p", "--prescription", help="Prescription CSV file")
    parser.add_argument("-v", "--visit", help="Visit CSV file")
    args = parser.parse_args()

    prescription_data = read_prescription_sheet(fname=args.prescription)
    visit_data = read_visit_sheet(fname=args.visit)
    breakpoint()

    today = datetime.datetime.now()  # noqa: DT007
    csv_name = f'expired_prescription_{today.strftime("%Y%m%d")}.csv'
    csv_fp = csv.writer(open(csv_name, "w", encoding="utf-8"))  # noqa: SIM115
    csv_fp.writerow(
        [
            "Patient Name",
            "Rx End Date",
            "Clinic",
            "Case Title",
            "Treating Therapist",
            "Case Therapist",
            "Appointment Type",
            "Appointment Date",
            "Visit Status",
            "Start Time",
            "End Time",
        ]
    )
    for match_name, end_date in prescription_data.items():
        if match_name not in visit_data:
            continue

        write_row(csv_fp=csv_fp, match_name=match_name, end_date=end_date, visits=visit_data[match_name])


if __name__ == "__main__":
    main()
