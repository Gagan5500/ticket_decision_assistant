# Returns Policy

## 1. Return Eligibility Window
- Customers can initiate a return within **7 calendar days** from the date of confirmed delivery.
- Return requests submitted after 7 days will be rejected (`REJECT_RETURN`) under the standard policy.

## 2. Product Condition Requirements
- Returned merchandise must be in new, unwashed, unworn condition with original tags, accessories, warranty cards, and packaging intact.
- Items showing signs of wear, makeup stains, perfume odor, or detached tags will be rejected upon inspection.

## 3. Non-Returnable & Final Sale Items
- The following categories cannot be returned under any circumstances:
  - Items explicitly tagged as "Final Sale" or clearance discounts exceeding 50%.
  - Personal hygiene items, intimate apparel, and cosmetics.
  - Perishable items, flowers, and edible goods.
  - Downloadable software products, activation codes, or gift vouchers.

## 4. Return Fee & Process
- Return shipping is free if the return is due to warehouse error or defective item.
- For buyer's remorse (e.g., changed mind, wrong size ordered by mistake), a standard reverse logistics fee of ₹100 is deducted from the refund unless the user is a Premium VIP member.

## 5. Decision Outcomes
- **APPROVE_RETURN**: When the return request is within 7 days, item is eligible, and condition meets standards.
- **REJECT_RETURN**: When the return window has expired (>7 days) or the item belongs to a non-returnable category.
- **NEEDS_MORE_INFORMATION**: When order number, delivery date, or item category is omitted from the request.
