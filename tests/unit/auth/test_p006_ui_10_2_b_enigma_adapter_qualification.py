from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from backend.auth.enigma_catalogue_admission.contracts import EnigmaSourceSpec
from backend.auth.enigma_catalogue_admission.postgresql import PostgreSQLEnigmaCatalogueAdmission
from backend.auth.enigma_catalogue_admission.source import EXPECTED_HEADER, qualify_source_bytes


def _word(index: int, length: int, salt: int = 0) -> str:
    value = index + salt
    chars = []
    for _ in range(length):
        chars.append(chr(ord("A") + value % 26))
        value //= 26
    return "".join(reversed(chars))


def _qualified(length: int):
    lines = [",".join(EXPECTED_HEADER)]
    index = 0
    for day in range(1, 32):
        for period in ("Morning", "Noon", "Evening"):
            words = (_word(index, length), _word(index, length, 1000), _word(index, length, 2000))
            lines.append(f"{day},{period},{words[0]},{words[1]},{words[2]},TOKEN{index}")
            index += 1
    raw = ("\n".join(lines) + "\n").encode("ascii")
    path = Path(f"development/auth/private/enigma/enigma_words_{length}.csv")
    spec = EnigmaSourceSpec(
        length,
        path,
        path.as_posix(),
        sha256(raw).hexdigest(),
        f"enigma:catalogue:test:{length}:v1",
    )
    return qualify_source_bytes(spec, raw)


class Tx:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        self.snapshot = deepcopy(self.connection.state)
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self.connection.state = self.snapshot
            self.connection.rollbacks += 1
        else:
            self.connection.commits += 1
        return False


class Cursor:
    def __init__(self, connection):
        self.connection = connection
        self.current = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, statement, params=None):
        sql = " ".join(str(statement).split())
        state = self.connection.state
        if sql.startswith("INSERT INTO nexilabs_auth.enigma_profile ("):
            profile_id, reference = params
            state["profiles"][profile_id] = {"state": "ACTIVE", "reference": reference}
            self.current = None
            return
        if sql.startswith("INSERT INTO nexilabs_auth.enigma_profile_catalogue ("):
            profile_id, length, catalogue_id = params
            state["bindings"][(profile_id, int(length))] = catalogue_id
            self.current = None
            return
        if "FROM nexilabs_auth.enigma_profile_catalogue AS epc" in sql:
            profile_id, length, day, period = params
            catalogue_id = state["bindings"].get((profile_id, int(length)))
            profile = state["profiles"].get(profile_id)
            catalogue = state["catalogues"].get(catalogue_id)
            entry = state["entries"].get((catalogue_id, int(day), str(period)))
            if not profile or profile["state"] != "ACTIVE" or not catalogue or catalogue["state"] != "ACTIVE" or not entry:
                self.current = None
                return
            self.current = (
                catalogue_id,
                profile_id,
                int(length),
                int(day),
                str(period),
                entry[0],
                entry[1],
                entry[2],
            )
            return
        if sql.startswith("SELECT COUNT(*) FROM nexilabs_auth.enigma_profile WHERE profile_id = %s"):
            self.current = (1 if params[0] in state["profiles"] else 0,)
            return
        if sql.startswith("SELECT COUNT(*) FROM nexilabs_auth.enigma_profile_catalogue WHERE profile_id = %s"):
            self.current = (sum(1 for pid, _ in state["bindings"] if pid == params[0]),)
            return
        raise AssertionError(f"unexpected SQL: {sql}")

    def fetchone(self):
        return self.current


class Connection:
    def __init__(self, sources):
        self.state = {
            "profiles": {},
            "bindings": {},
            "catalogues": {},
            "entries": {},
        }
        for source in sources:
            self.state["catalogues"][source.spec.catalogue_id] = {
                "state": "ACTIVE",
                "word_length": source.spec.word_length,
            }
            for row in source.rows:
                self.state["entries"][(source.spec.catalogue_id, row.day_of_month, row.period)] = row.words
        self.rollbacks = 0
        self.commits = 0

    def cursor(self):
        return Cursor(self)

    def transaction(self):
        return Tx(self)


class Pool:
    def __init__(self, connection):
        self.connection_object = connection

    @contextmanager
    def connection(self, read_only=False):
        yield self.connection_object


def test_controlled_adapter_qualification_uses_no_real_principal_and_rolls_back_profile_binding() -> None:
    sources = tuple(_qualified(length) for length in (3, 4, 5))
    connection = Connection(sources)
    receipt = PostgreSQLEnigmaCatalogueAdmission(Pool(connection)).qualify_read_adapter(sources)

    assert receipt.qualified_word_lengths == (3, 4, 5)
    assert receipt.cleanup_proven is True
    assert connection.state["profiles"] == {}
    assert connection.state["bindings"] == {}
    assert connection.rollbacks == 1
    assert connection.commits == 0
