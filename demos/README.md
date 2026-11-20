# Live Demos

This folder holds two optional, self-contained demo applications that
pair with [Lab 8 – Complex Parameters](../labs/lab08-complex-parameters.md).
Neither is required to complete the lab or its exercises — Lab 8 teaches
every concept in pure T-SQL. These demos exist for instructors or
curious students who want to see the same ideas acted out against a
real running application.

Each demo uses its **own dedicated database**, entirely separate from
`AdventureWorksENG`. Setting one up does not affect the training
database used by the rest of the course.

> [!WARNING]
> Both applications are teaching aids, not production software. One of
> them is **intentionally vulnerable** to SQL injection. Run them only
> on your own machine, against your own local SQL Server instance.
> Never expose either application to a public network.

---

## [cyber-lab/](cyber-lab/) — SQL Injection, Live

Pairs with **Lab 8, Section 2** (Method 1 — Client-Side Query Building).

A FastAPI application with two pages, each offering a vulnerable (string
concatenation) and a secure (parameterized) path. The **login** page
answers only *welcome* or *wrong password*, like a real one, and shows
that data leaks anyway — through the welcome text (`UNION`), through SQL
error messages, and through blind yes/no injection. The **search** page
returns a table of products, where a `UNION SELECT` quietly adds rows
from `Users` and `CreditCards`. Every payload is a one-click button; run
each against the secure path and watch it do nothing.

See [cyber-lab/README.md](cyber-lab/README.md) for setup, and
[cyber-lab/lab.md](cyber-lab/lab.md) for a guided, click-by-click
classroom walkthrough of each payload.

---

## [obp-rest-demo/](obp-rest-demo/) — JSON, REST, and Stored Procedures, Live

Pairs with **Lab 8, Section 5** (Method 4 — JSON Parameters).

A small FastAPI invoicing API. `POST /invoices` accepts the exact JSON
shape taught in the lab — a customer, a date, and an array of line
items — and forwards it unchanged to a stored procedure that shreds it
with `OPENJSON` and inserts the header and items atomically. Confirms,
end to end, that "a REST client sends JSON, a stored procedure turns it
into rows" is not just a classroom exercise — it is how real systems
are built.

See [obp-rest-demo/README.md](obp-rest-demo/README.md) for setup,
[obp-rest-demo/api/lab.md](obp-rest-demo/api/lab.md) for a guided,
click-by-click classroom walkthrough, and
[obp-rest-demo/how-it-works.md](obp-rest-demo/how-it-works.md) for
optional reading on how the application works, with links to Labs 7,
8, and 9.

---

## Why these aren't part of the lab itself

Lab 8 is self-contained in T-SQL so it can be completed without
installing Python, a web server, or a second SQL Server database. These
demos require more setup (a Python environment, `pip install`, a
running `uvicorn` process) and exist purely to make the two most
abstract ideas in the lab — "an attacker can inject SQL through a text
box" and "a REST API is just another caller of a stored procedure" —
visible and clickable rather than theoretical.
