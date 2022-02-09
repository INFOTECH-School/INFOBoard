"""
Helper functions and classes that don't need any configured state or django stuff loaded.
"""

from typing import Any, Protocol, TypeVar, Generic
from enum import Enum

class SeqMode(Enum):
    MERGE = 1
    COMBINE = 2
    OVERRIDE = 3

StructureType = TypeVar("StructureType", dict, list, set, tuple)

# def deepmerge(first: StructureType, second: StructureType) -> StructureType:
def deepmerge(first, second, sequence_mode=SeqMode.MERGE):
    """
    Deep merges dicts, lists, tuples and sets.

    Dicts are merged by keys. Lists and tuple are appended. Sets
    will be unionized. If types in a dict don't match, the value
    in the second dict overrides the value in the first one.

    :param first: the data to be merged into

    :param second: the data to merge into ``first``

    :raises TypeError: if the types of the arguments do not match.

    :returns: a new data structure of the same type as ``first`` and ``second``.
    """
    if type(first) is not type(second):
        return second
        # raise TypeError(
        #     f"can't merge: first ({type(first)}) and second ({type(second)}) "
        #     "arguments are not of the same type.")

    if isinstance(first, dict):
        out = first.copy()
        for key, value in second.items():
            if key in out:
                out[key] = deepmerge(out[key], value, sequence_mode)
            else:
                out[key] = value
        return out

    if isinstance(first, (list, tuple)):
        if sequence_mode == SeqMode.MERGE:
            max_len = max(len(first), len(second))
            out = []
            for i in range(max_len):
                try:
                    out[i] = deepmerge(first[i], second[i], sequence_mode)
                except IndexError:
                    pass
                try:
                    out[i] = first[i]
                except IndexError:
                    pass
                try:
                    out[i] = second[i]
                except IndexError:
                    pass

            return type(first)(out)

        if sequence_mode == SeqMode.COMBINE:
            return first + second

        if sequence_mode == SeqMode.OVERRIDE:
            return second

    if isinstance(first, set):
        return first.union(second)

    raise TypeError(f"unsupported type: {type(first)}")


ChainedObj = TypeVar('ChainedObj')

class Chain(Generic[ChainedObj]):
    """
    A class for optional chaining in Python.

    Contains a tree of ``dict`` s, ``list`` s and ``object`` s, that can be queried via
    ``__getitem__`` (``[...]``). The object contained in the class can be retrieved via
    ``.obj``.If any of the items or attributes in the getter chain contains ``None``,
    ``.obj`` will be None, too.
    """
    def __init__(self, obj: ChainedObj) -> None:
        self.obj = obj

    def get(self, key: Any, default=None):
        if isinstance(self.obj, dict):
            return Chain(self.obj.get(key, None))
        if isinstance(self.obj, (list, tuple)) \
        and 0 <= key < len(self.obj):
            return Chain(self.obj[key])
        if isinstance(key, str):
            return Chain(getattr(self.obj, key, None))
        return Chain(default)

    __getitem__ = get

class StrLike(Protocol):
    def __str__(self) -> str:
        ...
