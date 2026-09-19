# Refunds Policy

## 1. Refund Processing Timelines
- Once an authorized return arrives at our distribution warehouse and passes inspection, refunds are processed within **5 to 7 business days**.
- Refunds are always credited back to the original payment method (Credit Card, Debit Card, UPI, Net Banking). Cash on Delivery (COD) orders require the customer to provide verified bank account details.

## 2. Order Cancellation Prior to Shipping
- If a customer cancels an order before it has been dispatched from the warehouse, a full 100% refund is initiated within 24 hours.

## 3. Expedited Shipping Charges
- Standard or expedited shipping fees paid at checkout are non-refundable unless the shipment was delayed beyond our guaranteed delivery SLA or canceled due to our operational error.

## 4. Late or Missing Refunds
- If a customer reports that a refund was issued more than 7 business days ago but has not appeared in their bank statement, the issue must be escalated to the billing operations team (`ESCALATE_TO_BILLING`) with the bank transaction reference number (ARN/UTR).

## 5. Decision Outcomes
- **APPROVE_REFUND**: When inspection is complete or pre-shipment cancellation is requested.
- **REJECT_REFUND**: For claims requesting refund of non-refundable express shipping charges or unauthorized chargebacks.
- **ESCALATE_TO_BILLING**: When a refund is delayed beyond the 7 business day processing window.
- **NEEDS_MORE_INFORMATION**: When customer asks about refund status without specifying an order ID or transaction ID.
