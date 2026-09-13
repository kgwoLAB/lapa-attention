from .sdpa import SDPABackend
from .rope import RoPEBackend
from .cope import CoPEBackend
from .tape import TAPEBackend


def make_attention(name):
    choices = {"sdpa": SDPABackend, "rope": RoPEBackend, "cope": CoPEBackend, "tape": TAPEBackend}
    if name not in choices:
        raise ValueError(f"unknown attention: {name}")
    return choices[name]()
