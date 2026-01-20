from dataclasses import dataclass, field
from typing import Iterable, List
from teracontrol.core.data import DataAtom


@dataclass
class Record:
    atoms: List[DataAtom] = field(default_factory=list)

    def append(self, atom: DataAtom) -> None:
        self.atoms.append(atom)

    def __len__(self) -> int:
        return len(self.atoms)
    
    def __iter__(self) -> Iterable[DataAtom]:
        return iter(self.atoms)

    def __getitem__(self, index: int) -> DataAtom:
        return self.atoms[index]