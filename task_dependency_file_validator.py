"""
Problem: Task Dependency File Validator
You are ingesting a CSV that defines tasks in a workflow.
Each task can declare another task it depends on.
Before the workflow runs, you must validate the file and reject it with a clear,
specific error if anything is wrong.

The expected schema is a header row followed by data rows:
id,name,depends_on
t1,Provision database,
t2,Run migrations,t1
t3,Seed data,t2
t4,Start service,t3

A row's depends_on may be empty, meaning the task has no prerequisite.
Before writing code, confirm with me: Should validation stop at the first error or collect all of them?
Are id values guaranteed unique? Is whitespace-only the same as empty? May a depends_on reference a task defined in a later row?
Part 1: Parse and confirm headers
Write validate(csv_text) that parses the CSV and confirms the header row is exactly id, name, depends_on, in that order. Reject a file with missing, extra, misnamed, or reordered headers, and reject any data row whose column count does not match the header.
# missing the depends_on column  ->  rejected, headers do not match schema
# a row with only two fields      ->  rejected, wrong column count on that row
Use the csv module rather than splitting on commas, so quoted fields containing commas (for example a name like "Backup, then archive") parse correctly.
Part 2: Validate non-empty values
Extend validate so that id and name must be non-empty (whitespace-only counts as empty). depends_on is allowed to be empty. Report which row and which column failed.
id,name,depends_on
t1,,                 ->  rejected, name is empty on row for t1
,Run migrations,t1   ->  rejected, id is empty
Part 3: Apply a cross-column rule
Add a referential-integrity rule: every non-empty depends_on value must match the id of some task defined in the file. A dependency on a task that does not exist is invalid.
id,name,depends_on
t1,Provision,
t2,Migrate,t9        ->  rejected, t2 depends on unknown task t9
Also reject a task that depends on itself (depends_on equals its own id), and decide how you handle a duplicate id.
Part 4: Detect circular dependencies
A valid workflow must be runnable in some order, which means the dependency graph cannot contain a cycle. Extend validate to build the dependency graph and reject the file if any cycle exists, naming the tasks involved.
id,name,depends_on
t1,A,t3
t2,B,t1
t3,C,t2              ->  rejected, circular dependency: t1 -> t3 -> t2 -> t1
Stretch, if time remains: when the file is valid, return a topological ordering of the tasks, which is the order the workflow could actually execute in.
"""

import csv
from collections import defaultdict

tasks: defaultdict = defaultdict()
deps: defaultdict = defaultdict()

with open("assets/task_dependency.csv", newline="") as csvfile:
    reader = csv.reader(csvfile, delimiter=",")
    header = next(reader)
    assert len(header) == 3
    assert (
        header[0] == "id" and header[1] == "name" and header[2] == "depends_on"
    )
    print(header)
    for row in reader:
        assert len(row) == 3
        assert row[0].replace(" ", "") != "" and row[1].replace(" ", "") != ""
        print(row)
        tasks[row[0]] = row[1]
        if row[0].replace(" ", "") != "":
            deps[row[0]] = row[2]
    print(tasks)
    print(deps)

    def dfs(node: str, visited: set):
        dep = deps[node]
        if dep == "":
            return True
        if dep not in visited:
            visited.add(dep)
            return dfs(dep, visited)
        return False

    for dep in deps.items():
        key, value = dep
        assert key != value
        if value.replace(" ", "") != "" and value not in deps:
            raise ValueError(f"dependency {value} does not exist")

    for dep in deps.items():
        key, value = dep
        valid = dfs(key, set())
        assert valid is True, "dependency has cyclical"


# missing the depends_on column  ->  rejected, headers do not match schema
# a row with only two fields      ->  rejected, wrong column count on that row
