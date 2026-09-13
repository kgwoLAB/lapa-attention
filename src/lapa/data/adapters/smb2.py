from ..dataset import NativeDataset


def load(path):
    return NativeDataset(path, protocol="smb2")
