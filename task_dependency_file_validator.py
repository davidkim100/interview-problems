"""
Task Dependency File Validator

Validate a CSV workflow file against the following schema:

    id,name,depends_on
    t1,Provision database,
    t2,Run migrations,t1
    t3,Seed data,t2
    t4,Start service,t3

Validation rules:
    Part 1 - Headers and column count:
        Header must be exactly: id, name, depends_on (in that order).
        Every data row must have exactly 3 fields.

    Part 2 - Non-empty values:
        id and name must be non-empty (whitespace-only counts as empty).
        depends_on may be empty (meaning no prerequisite).

    Part 3 - Referential integrity:
        Every non-empty depends_on must reference an id defined in the file.
        A task may not depend on itself.
        Duplicate ids are rejected.

    Part 4 - No cycles:
        The dependency graph must be acyclic.

Returns a topological ordering of task ids when the file is valid.
"""

import csv
import io
import pytest
from collections import defaultdict


def validate(csv_text: str) -> list[str]:
    """
    Validates a CSV-formatted workflow task file and returns a topological ordering.
    Raises ValueError with a descriptive message on any validation failure.
    """
    reader = csv.reader(io.StringIO(csv_text))
    header = next(reader)

    if header != ["id", "name", "depends_on"]:
        raise ValueError(
            f"headers do not match schema: expected ['id', 'name', 'depends_on'], got {header}"
        )

    tasks: dict[str, str] = {}
    deps: dict[str, str] = {}

    for row in reader:
        if len(row) != 3:
            raise ValueError(f"wrong column count on row: {row}")

        task_id, name, depends_on = row

        if task_id.strip() == "":
            raise ValueError(f"id is empty on row: {row}")
        if name.strip() == "":
            raise ValueError(f"name is empty for task '{task_id}'")
        if task_id in tasks:
            raise ValueError(f"duplicate id '{task_id}'")

        tasks[task_id] = name
        deps[task_id] = depends_on.strip()

    for task_id, dep in deps.items():
        if dep == "":
            continue
        if dep not in tasks:
            raise ValueError(f"task '{task_id}' depends on unknown task '{dep}'")
        if dep == task_id:
            raise ValueError(f"task '{task_id}' depends on itself")

    def dfs(node: str, visited: set, path: list) -> None:
        dep = deps[node]
        if dep == "":
            return
        if dep in path:
            cycle = " -> ".join(path + [dep])
            raise ValueError(f"circular dependency: {cycle}")
        if dep not in visited:
            visited.add(dep)
            dfs(dep, visited, path + [dep])

    for task_id in deps:
        dfs(task_id, set(), [task_id])

    # Topological sort (Kahn's algorithm)
    in_degree = {task_id: 0 for task_id in tasks}
    for task_id, dep in deps.items():
        if dep:
            in_degree[task_id] += 1

    queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
    order = []
    reverse_deps: dict[str, list[str]] = defaultdict(list)
    for task_id, dep in deps.items():
        if dep:
            reverse_deps[dep].append(task_id)

    while queue:
        node = queue.pop(0)
        order.append(node)
        for dependent in reverse_deps[node]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    return order


def test_validate_valid():
    valid_csv = "id,name,depends_on\nt1,Provision database,\nt2,Run migrations,t1\nt3,Seed data,t2\nt4,Start service,t3"
    assert validate(valid_csv) == ["t1", "t2", "t3", "t4"]


@pytest.mark.parametrize("csv_text,error_fragment", [
    ("id,name\nt1,Provision database", "headers do not match schema"),
    ("id,name,depends_on\nt1,Provision database", "wrong column count"),
    ("id,name,depends_on\nt1,,", "name is empty"),
    ("id,name,depends_on\nt1,Provision,\nt2,Migrate,t9", "unknown task"),
    ("id,name,depends_on\nt1,A,t3\nt2,B,t1\nt3,C,t2", "circular dependency"),
])
def test_validate_invalid(csv_text, error_fragment):
    with pytest.raises(ValueError, match=error_fragment):
        validate(csv_text)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
