from __future__ import annotations

from dataclasses import asdict, dataclass, field

PARTITIONING = ("none", "hash", "range")
MODES = ("sync", "async")
PATHS = ("both", "read", "write")
PROTOCOLS = ("", "HTTP", "gRPC", "TCP", "UDP", "UDP multicast", "FIX", "WebSocket", "IPC")


@dataclass
class Block:
    id: str
    component: str
    name: str = ""
    technology: str = ""
    instances: int = 1
    replication_factor: int = 1
    partitioning: str = "none"
    partition_key: str = ""
    note: str = ""
    extras: dict[str, str] = field(default_factory=dict)
    x: float = 0.0
    y: float = 0.0


@dataclass
class Connection:
    id: str
    source: str
    target: str
    mode: str = "sync"
    protocol: str = ""
    path: str = "both"
    label: str = ""


@dataclass
class Design:
    blocks: list[Block] = field(default_factory=list)
    connections: list[Connection] = field(default_factory=list)

    def block(self, block_id: str) -> Block | None:
        return next((b for b in self.blocks if b.id == block_id), None)

    def connection(self, connection_id: str) -> Connection | None:
        return next((c for c in self.connections if c.id == connection_id), None)

    def add_block(self, component: str, name: str = "", x: float = 0.0, y: float = 0.0) -> Block:
        block = Block(id=self._next_id("b", (b.id for b in self.blocks)), component=component, name=name, x=x, y=y)
        self.blocks.append(block)
        return block

    def connect(self, source: str, target: str) -> Connection | None:
        if source == target or self.block(source) is None or self.block(target) is None:
            return None
        if any(c.source == source and c.target == target for c in self.connections):
            return None
        connection = Connection(id=self._next_id("c", (c.id for c in self.connections)), source=source, target=target)
        self.connections.append(connection)
        return connection

    def remove_block(self, block_id: str) -> None:
        self.blocks = [b for b in self.blocks if b.id != block_id]
        self.connections = [c for c in self.connections if block_id not in (c.source, c.target)]

    def remove_connection(self, connection_id: str) -> None:
        self.connections = [c for c in self.connections if c.id != connection_id]

    def is_empty(self) -> bool:
        return not self.blocks

    def to_dict(self) -> dict:
        return {
            "blocks": [asdict(b) for b in self.blocks],
            "connections": [
                {"id": c.id, "from": c.source, "to": c.target, "mode": c.mode,
                 "protocol": c.protocol, "path": c.path, "label": c.label}
                for c in self.connections
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Design:
        design = cls()
        for raw in data.get("blocks", []):
            design.blocks.append(Block(**raw))
        for index, raw in enumerate(data.get("connections", []), start=1):
            raw = dict(raw)
            source, target = raw.pop("from"), raw.pop("to")
            raw.setdefault("id", f"c{index}")
            for end in (source, target):
                if design.block(end) is None:
                    raise ValueError(f"connection refers to unknown block {end!r}")
            design.connections.append(Connection(source=source, target=target, **raw))
        return design

    @staticmethod
    def _next_id(prefix: str, existing) -> str:
        taken = set(existing)
        number = len(taken) + 1
        while f"{prefix}{number}" in taken:
            number += 1
        return f"{prefix}{number}"
