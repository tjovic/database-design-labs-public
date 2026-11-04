# LAB 09 – REST API and SQL Server

## Topic

Demonstration of how a modern application communicates with a SQL Server database.

The project serves as motivation for the material on XML and storage of complex data.

---

# Goals

After the demonstration, students should understand:

* the relational model
* the 1:N relationship
* hierarchical JSON
* stored procedures
* OPENJSON
* REST API
* ON DELETE CASCADE

Emphasize that REST is only a tool for demonstration. The focus of the lab remains on SQL Server.

---

# Preparation before the lab

## Start SQL Server

## In SSMS run

```
02_SeedData.sql
```

## Start the REST API

```bash
uvicorn api.app:app --reload
```

## Open

```
http://localhost:8000/docs
```

Also open SSMS.

---

# Demonstration

## 1. GET /customers

Explain:

* REST endpoint
* JSON response
* data comes from SQL Server
* FastAPI does not know about the Customer table, it only calls the procedure

---

## 2. GET /invoices

Show the list of invoices.

Explain:

* one invoice
* one customer
* total amount

Ask the students:

> What do you expect GET /invoices/{id} to return?

---

## 3. GET /invoices/{id}

Call a single invoice.

Explain:

In SQL Server there are four tables:

* Customer
* Invoice
* InvoiceItem
* Product

But REST returns a single object.

Show:

* the customer
* the items
* the products

Emphasize:

Relational model

↓

Hierarchical JSON

---

## 4. SSMS

Show

```sql
SELECT *
FROM Invoice;
```

and

```sql
SELECT *
FROM InvoiceItem;
```

Ask:

> How many tables does this JSON use?

---

## 5. POST /invoices

Send:

```json
{
  "customerId": 1,
  "date": "2025-06-27",
  "items": [
    {
      "productId": 1,
      "quantity": 2,
      "unitPrice": 1450
    },
    {
      "productId": 2,
      "quantity": 1,
      "unitPrice": 109
    }
  ]
}
```

Explain:

Swagger

↓

FastAPI

↓

Stored Procedure

↓

OPENJSON

↓

INSERT

↓

COMMIT

---

## 6. SSMS

Run again:

```sql
SELECT *
FROM Invoice;

SELECT *
FROM InvoiceItem;
```

Show the new invoice.

Show the new items.

Explain:

One JSON document

↓

multiple INSERT statements

---

## 7. PUT /invoices/{id}

Change the date or the customer.

Show that only the invoice header is changed.

Explain:

We do not touch the items.

---

## 8. DELETE /invoices/{id}

Delete the invoice.

Run again:

```sql
SELECT *
FROM Invoice;

SELECT *
FROM InvoiceItem;
```

Ask the students:

> Who deleted the items?

Explain:

```
ON DELETE CASCADE
```

---

# Closing part

Show the same JSON.

Explain:

This is the way the same problem is most commonly solved today.

---

# Connection to XML

Ask the students:

> How would we send the same invoice to SQL Server ten or more years ago?

Show XML.

Explain:

JSON and XML solve the same problem.

The difference is in the format.

In the rest of the lab, show:

* the XML type
* nodes()
* value()

Emphasize that XML will still be encountered in existing business systems and integrations.

---

# Questions for students

1. Why are the invoice and the items not in the same table?

2. Why do we store the price on the invoice item?

3. Why do we use stored procedures?

4. What does OPENJSON do?

5. What would happen if there were no ON DELETE CASCADE?

6. Why does REST return a single object, while SQL Server uses four tables?

7. How would you solve the same problem using XML?

---

# Closing message

The relational model and hierarchical JSON are not competitors.

The relational model is used to store data.

JSON is used to exchange data between applications.

XML solves the same problem as JSON and that is why it is important to understand both approaches.
