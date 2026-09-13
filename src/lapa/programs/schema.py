from dataclasses import asdict, dataclass

BASES = ("packet_absolute", "field_end_forward", "field_start_backward", "field_start_forward",
         "previous_offset_plus_length", "offset_with_next_length")


@dataclass(frozen=True)
class Program:
    width: int
    endian: str = "big"
    base: str = "packet_absolute"
    signed: bool = False
    mask: int | None = None
    shift: int = 0
    scale: int = 1
    bias: int = 0
    guard_mask: int = 0
    guard_value: int = 0

    def __post_init__(self):
        if self.width not in (1, 2, 3, 4) or self.endian not in ("big", "little") or self.base not in BASES:
            raise ValueError("invalid program width, endian or base")
        limit = (1 << (8 * self.width)) - 1
        if self.mask is not None and not 0 <= self.mask <= limit:
            raise ValueError("mask exceeds field width")
        if self.signed and self.mask is not None:
            raise ValueError("signed/masked combination is undefined")
        if not 0 <= self.shift < 8 * self.width or not 0 <= self.guard_mask <= limit or self.guard_value & ~self.guard_mask:
            raise ValueError("invalid shift or guard")
        if self.base in BASES[4:] and (self.signed or self.mask is not None or self.width not in (2, 4)):
            raise ValueError("adjacent operations require unsigned 2/4-byte fields")

    def axis_values(self):
        return {"width": str(self.width), "endian": self.endian if self.width > 1 else "big",
                "sign": "signed" if self.signed else "unsigned", "base": self.base,
                "mask": "none" if self.mask is None else f"{self.mask:x}"}

    def to_dict(self):
        return asdict(self)

    @property
    def semantic(self):
        if self.mask is not None:
            return "POINTER"
        if self.base in ("field_end_forward", "previous_offset_plus_length"):
            return "LENGTH"
        if self.base in ("packet_absolute", "offset_with_next_length"):
            return "OFFSET"
        return "OTHER"
