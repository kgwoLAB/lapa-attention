from ..dataset import NativeDataset


def load(path):
    """Read preserved DNS records; does not parse/relabel raw captures."""
    return NativeDataset(path, protocol="dns")
