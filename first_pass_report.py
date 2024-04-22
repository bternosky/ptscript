#!/usr/bin/env python3
# coding: utf-8
import argparse
import csv
import datetime
from typing import Any, TypeAlias

RowType: TypeAlias = dict[str, Any]
ApptType: TypeAlias = dict[datetime.date, RowType]
# { normalized_name: { appt date: {RowType} } }
MainType: TypeAlias = dict[str, ApptType]
LeadType: TypeAlias = dict[str, ApptType]


TODAY = datetime.datetime.now().date()  # noqa: DTZ005


def get_appt_date_as_date(appt_str: str) -> datetime.date:
    return datetime.datetime.strptime(appt_str, "%m/%d/%Y").date()  # noqa: DTZ007


def normalize_name(name: str) -> str:
    return name.upper().encode("ascii", "ignore").decode("ascii").replace(",", " ")


def read_main_sheet(*, fname: str) -> MainType:
    headers: list[str] = []
    data: MainType = {}  # { normalized_name: { appt date: [ {}, ... ] } }

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

        # compute "normalized_name"
        # In sheet it is usually: Last, First -OR- Last, First Mi
        normalized_name = normalize_name(name=row_dict["PATIENT NAME"])

        dd = data.setdefault(normalized_name, {})
        if appt_date in dd:
            print(
                f'ERROR: Duplicate entry for patient: {row_dict["PATIENT NAME"]} with date: {appt_date}'
            )
            continue
        dd[appt_date] = row_dict

    return data


def read_lead_sheet(*, fname: str) -> LeadType:
    headers: list[str] = []
    data: LeadType = {}  # { normalized_name: { appt date: [ {}, ... ] } }

    for ct, line in enumerate(
        csv.reader(open(fname, "r", encoding="utf-8"))  # noqa: SIM115
    ):  # noqa: SIM115
        line = [x.strip() for x in line]
        if ct == 0:
            headers = [x.upper() for x in line]
            continue
        row_dict: dict[str, Any] = dict(zip(headers, line))
        appt_date = get_appt_date_as_date(appt_str=row_dict["APPT DATE"])
        row_dict["APPT DATE AS DATE"] = appt_date

        # Add row num to the dict
        row_dict["ROW_NUM"] = ct + 1

        # compute "normalized_name"
        # In sheet it is usually: First Last (with no MI)
        original_name = row_dict["PATIENT NAME"]
        lead_parts = row_dict["PATIENT NAME"].split(" ")
        normalized_name = str(f'{lead_parts[-1]} {" ".join(lead_parts[:-1])}')
        patient_name = normalize_name(name=normalized_name)

        dd = data.setdefault(patient_name, {})
        if appt_date in dd:
            print(
                f"ERROR: Duplicate entry for patient: {original_name} with date: {appt_date}"
            )
            continue
        dd[appt_date] = row_dict

    return data


def write_row(*, csv_fp: Any, row: RowType, comment: str) -> None:
    csv_fp.writerow(
        [
            row["PATIENT NAME"],
            row["CASE TITLE"],
            row["TREATING THERAPIST"],
            row["CASE THERAPIST"],
            row["APPOINTMENT TYPE"],
            row["APPOINTMENT DATE"],
            row["ROW_NUM"],
            comment,
        ]
    )


def process(*, main_values: ApptType, lead_values: ApptType, csv_fp: Any) -> None:
    # We matched. Ignore main/lead appts that match date. Only show those in future
    print(f"{main_values}, {lead_values}")
    for main_appt_date, main_row in sorted(main_values.items()):
        if main_appt_date not in lead_values:
            # We write to CSV if date in future is within now + 14 days AND
            # visit status from main is NOT cancelled
            if main_row["VISIT STATUS"].upper() == "CANCELLED":
                continue
            if main_row["APPT DATE AS DATE"] > TODAY + datetime.timedelta(days=14):
                continue
            write_row(
                csv_fp=csv_fp,
                row=main_row,
                comment=f"Patient matched but this date did not {main_appt_date}",
            )


def write_data(  # noqa: CCR001
    *, main_data: MainType, lead_data: LeadType, csv_fp: Any
) -> None:

    for main_name in main_data:
        # Patient Names vary across sheets, but is the most import piece of data for
        # linkage between the two sheets
        print(f"Testing main name: {main_name}")
        if main_name in lead_data:
            print("\tExact name match in lead")
            process(
                csv_fp=csv_fp,
                main_values=main_data[main_name],
                lead_values=lead_data[main_name],
            )
            continue

        matches: list[str] = []
        for key in lead_data:
            if main_name.startswith(key):
                matches.append(key)

        if len(matches) == 1:
            print("\tLeading match")
            process(
                csv_fp=csv_fp,
                main_values=main_data[main_name],
                lead_values=lead_data[matches[0]],
            )
            continue

        print(f"\t{len(matches)} matches")
        for _appt_date, row in main_data[main_name].items():
            # We write to CSV if date in future is within now + 7 days AND
            # visit status from main is NOT cancelled
            if row["VISIT STATUS"].upper() == "CANCELLED":
                continue
            if row["APPT DATE AS DATE"] > TODAY + datetime.timedelta(days=7):
                continue
            write_row(
                csv_fp=csv_fp,
                row=row,
                comment=f"ERROR: {len(matches)} found in LeadSheet",
            )


def main() -> None:
    parser = argparse.ArgumentParser(prog="PTReport", description="Generate PT Report")
    parser.add_argument("mainsheet")
    parser.add_argument("leadsheet")
    args = parser.parse_args()

    main_data = read_main_sheet(fname=args.mainsheet)
    lead_data = read_lead_sheet(fname=args.leadsheet)

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
            "ROW NUMBER",
            "COMMENT",
        ]
    )
    write_data(main_data=main_data, lead_data=lead_data, csv_fp=csv_fp)


if __name__ == "__main__":
    main()
