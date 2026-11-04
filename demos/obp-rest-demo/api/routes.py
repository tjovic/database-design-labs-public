from fastapi import APIRouter
import json

from fastapi.responses import RedirectResponse
from api.models import (
    InvoiceRequest,
    CustomerResponse,
    InvoiceResponse,
    InvoiceItemResponse,
    InvoiceListResponse
)
from api.database import get_invoices, get_connection
from api.database import get_customers

from api.database import get_invoice



router = APIRouter()


@router.get(
    "/",
    include_in_schema=False,
    summary="Home page"
)
def root():

    return RedirectResponse("/docs")



@router.post("/invoices", summary="Add invoice")
def add_invoice(invoice: InvoiceRequest):

    conn = get_connection()

    cursor = conn.cursor()

    json_data = json.dumps(invoice.model_dump())

    cursor.execute(

        "EXEC sp_AddInvoice ?",

        json_data

    )

    conn.commit()

    conn.close()

    return {

        "status": "Invoice saved successfully."

    }


@router.get(
    "/customers",
    response_model=list[CustomerResponse],
    summary="Get customers"
)
def customers():

    result = []

    for row in get_customers():

        result.append({

            "customerId": row.CustomerID,

            "firstName": row.FirstName,

            "lastName": row.LastName,

            "email": row.Email

        })

    return result




@router.get(
    "/invoices/{id}",
    response_model=InvoiceResponse,
    summary="Get invoice by ID"
)
def get_invoice_by_id(id: int):

    data = get_invoice(id)

    if len(data) == 0:
        return None

    first = data[0]

    invoice = {

        "invoiceId": first.InvoiceID,

        "date": str(first.Date),

        "customer": {

            "customerId": first.CustomerID,

            "firstName": first.FirstName,

            "lastName": first.LastName,

            "email": first.Email

        },

        "items": []

    }

    for row in data:

        invoice["items"].append(

            {

                "productId": row.ProductID,

                "name": row.Name,

                "quantity": row.Quantity,

                "unitPrice": float(row.UnitPrice)

            }

        )

    return invoice


@router.get(
    "/invoices",
    response_model=list[InvoiceListResponse],
    summary="Get all invoices"
)
def invoices():

    result = []

    for row in get_invoices():

        result.append(
            {
                "invoiceId": row.InvoiceID,
                "date": str(row.Date),
                "customer": f"{row.FirstName} {row.LastName}",
                "total": float(row.Total)
            }
        )

    return result



@router.put("/invoices/{id}", summary="Update invoice by ID")
def update_invoice(id: int, invoice: InvoiceRequest):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        "EXEC sp_UpdateInvoice ?, ?",
        id,
        json.dumps(invoice.model_dump())
    )

    conn.commit()
    conn.close()

    return {
        "status": "Invoice updated."
    }


@router.delete("/invoices/{id}", summary="Delete invoice by ID")
def delete_invoice(id: int):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        "EXEC sp_DeleteInvoice ?",
        id
    )

    conn.commit()
    conn.close()

    return {
        "status": "Invoice deleted."
    }
