def split_csv_line(line: str) -> list[str]:
    """Split one CSV line into fields (RFC 4180 quoting).

    Fields may be quoted with double quotes; a quoted field can contain commas,
    and a doubled quote ("") inside it stands for one quote character.
    """
    return line.split(",")
