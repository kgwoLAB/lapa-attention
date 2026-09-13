import hashlib

PROTOCOLS = ("dns", "modbus", "tls", "smb2")


def validate_record(row):
    raw = bytes.fromhex(row["data_hex"])
    if not raw or len(raw) != row["byte_length"]:
        raise ValueError("invalid native byte length")
    if hashlib.sha256(raw).hexdigest() != row["raw_sha256"]:
        raise ValueError("raw byte checksum mismatch")
    if row["protocol"] not in PROTOCOLS:
        raise ValueError("native field dataset supports DNS/Modbus/TLS/SMB2")
    for field in row["fields"]:
        if not 0 <= field["start"] < field["end"] <= len(raw):
            raise ValueError("field outside native message")
        if field["target"] is not None and not 0 <= field["target"] <= len(raw):
            raise ValueError("target outside native message")
    return row


def select_program(field, protocol, bank):
    """Label construction ONLY. Never called by a model forward."""
    width = field["end"] - field["start"]
    if protocol == "smb2":
        base = "offset_with_next_length" if field["semantic"] == "OFFSET" else "previous_offset_plus_length"
        endian, mask = "little", None
    else:
        base = "packet_absolute" if field["semantic"] == "POINTER" else "field_end_forward"
        endian = "big"
        mask = 0x3fff if field["semantic"] == "POINTER" else None
    matches = [i for i, p in enumerate(bank.programs) if p.width == width and p.endian == endian and p.base == base and p.mask == mask and not p.signed]
    if len(matches) != 1:
        raise ValueError(f"ambiguous or unsupported annotated program: {protocol}/{field['relation']}")
    return matches[0]
