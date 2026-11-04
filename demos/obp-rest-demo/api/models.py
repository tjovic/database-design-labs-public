from pydantic import BaseModel
from typing import List


# =====================================================
# REQUEST MODELS
# =====================================================

class InvoiceItemRequest(BaseModel):
    productId: int
    quantity: int
    unitPrice: float


class InvoiceRequest(BaseModel):
    customerId: int
    date: str
    items: List[InvoiceItemRequest]


# =====================================================
# RESPONSE MODELS
# =====================================================

class CustomerResponse(BaseModel):
    customerId: int
    firstName: str
    lastName: str
    email: str


class InvoiceItemResponse(BaseModel):
    productId: int
    name: str
    quantity: int
    unitPrice: float


class InvoiceResponse(BaseModel):
    invoiceId: int
    date: str
    customer: CustomerResponse
    items: List[InvoiceItemResponse]

class InvoiceListResponse(BaseModel):
    invoiceId: int
    date: str
    customer: str
    total: float
