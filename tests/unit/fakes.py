"""In-memory stand-ins for the repositories, so services are tested without Flask nor a database."""

import copy


class FakeRepo:
    """Same methods as powererp.store.Store, on a list. Keys compared ignoring case, like the tables."""

    def __init__(self, rows=(), keys=("cCode",)):
        self.rows = [copy.deepcopy(r) for r in rows]
        self.keys = keys

    def _match(self, r, values, ci=True):
        norm = (lambda v: str(v).lower()) if ci else str
        return all(norm(r.get(k)) == norm(v) for k, v in zip(self.keys, values, strict=True))

    def all(self, lines=True, where=None):
        return copy.deepcopy(self.rows)

    def get(self, *values, ci=True):
        return next((copy.deepcopy(r) for r in self.rows if self._match(r, values, ci)), None)

    def insert(self, row):
        self.rows.append(copy.deepcopy(row))
        return row

    def update(self, row, key_values=None):
        keys = key_values if key_values is not None else [row[k] for k in self.keys]
        i = next(i for i, r in enumerate(self.rows) if self._match(r, keys))
        self.rows[i] = copy.deepcopy(row)
        return row

    def delete(self, row):
        self.rows = [r for r in self.rows if not self._match(r, [row[k] for k in self.keys])]

    def count(self, where=None):
        return len(self.rows)
