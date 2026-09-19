# Shipping and Delivery Policy

## 1. Shipping Methods and Delivery SLAs
- **Standard Delivery**: 3 to 5 business days across metro cities; up to 7 business days for remote pin codes.
- **Express / Next-Day Delivery**: Guaranteed delivery within 1 to 2 business days. If delivery exceeds this window due to carrier delays, express shipping charges are refunded upon request.

## 2. Address Modifications and Rerouting
- Address modifications are permitted only within **2 hours** of order placement and strictly prior to warehouse dispatch.
- Once a package has shipped and tracking number is generated, address modifications or destination rerouting cannot be fulfilled (`REJECT_REROUTE`).

## 3. Lost in Transit & Extended Delays
- If a package has not been delivered within **10 business days** from dispatch and carrier tracking shows no scan updates for at least 5 days, the package is declared lost in transit.
- For lost packages, the customer is entitled to an immediate free priority replacement or full refund (`APPROVE_LOST_TRANSIT_CLAIM`).

## 4. Tracking Inquiries
- For packages in transit within normal delivery SLA timelines, provide tracking status updates (`PROVIDE_TRACKING_INFO`).

## 5. Decision Outcomes
- **PROVIDE_TRACKING_INFO**: Order is within normal transit SLA and on schedule.
- **APPROVE_LOST_TRANSIT_CLAIM**: Package missing or without scan for 10+ business days.
- **REJECT_REROUTE**: Customer requests delivery address change after package has already dispatched.
- **NEEDS_MORE_INFORMATION**: Missing order number or tracking number.
