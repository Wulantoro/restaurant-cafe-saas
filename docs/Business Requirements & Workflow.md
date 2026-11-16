# Business Requirements & Workflow
## Restaurant & Café Management System

**Document ID:** BRD-FOUNDATION-001  
**Version:** 2.0.0  
**Status:** Approved — Business Workflow Baseline  
**Document Type:** Business Requirements Document  
**Project:** Restaurant & Café Management System

---

# 1. Document Purpose

This document defines the business model, operational requirements, business actors, workflows, business rules, and exception-handling procedures for the Restaurant & Café Management System.

It establishes the approved business behavior that will guide functional requirements, system architecture, database design, API design, UI/UX design, and implementation planning.

This document follows the Product Vision & Scope document (PRD-FOUNDATION-001).

All approved business decisions are treated as authoritative requirements for subsequent project documentation.

# 2. Business Model

## 2.1 SaaS Multi-Tenant Model

The system operates as a Software-as-a-Service (SaaS) platform.

Each registered business operates as an independent tenant. Tenant data must remain isolated from other businesses.

The platform supports multiple restaurant and café businesses within a single application.

Each tenant manages its own:
- Business information.
- Outlets.
- Employees and access permissions.
- Operational activities.
- Orders and transactions.
- Inventory and purchasing.
- Suppliers.
- Reports and analytics.

## 2.2 Multi-Outlet Organization

A business may operate multiple outlets.

The organizational hierarchy is:

**SaaS Platform → Business (Tenant) → Outlets → Employees**

Each outlet has its own:
- Employees and outlet access assignments.
- Tables and operational activities.
- Orders and transactions.
- Inventory quantities.
- Kitchen operations.
- Cashier shifts.
- Goods receiving activities.

Certain configurations and master data are centrally managed at the business level and shared across outlets.

## 2.3 Centralized Business Management

The system uses centralized management for shared business data.

The following configurations are centrally managed:
- Menu master data.
- Product names and descriptions.
- Menu categories.
- Product variants and add-ons.
- Menu prices.
- Tax configuration.
- Service charge configuration.

Outlet-level operational data, including stock quantities, orders, and transactions, remains independently managed.

Payment timing is configurable independently for each outlet.

# 3. Business Actors

## 3.1 Central Administration

**Central Admin**

Responsible for managing shared business configurations and master data.

Responsibilities:
- Manage centralized menu information.
- Manage menu categories, products, variants, and add-ons.
- Manage centralized menu pricing.
- Configure tax rates and service charges.
- Publish changes to the business outlets.

Central Admin permissions must be separated from outlet-level operational permissions.

## 3.2 Business Owner

Responsible for overall business management.

Responsibilities:
- Manage business information.
- Oversee business operations.
- Monitor outlet performance.
- Review business reports.
- Manage authorized access and business policies.
- Authorize negative inventory configuration where permitted.

## 3.3 Business Manager

Responsible for supervising business or assigned outlet operations.

Responsibilities:
- Monitor inventory levels.
- Review replenishment requirements.
- Approve or reject purchase orders.
- Approve or reject refund requests.
- Approve order modifications requiring managerial authorization.
- Monitor operational performance.

## 3.4 Cashier

Responsible for payment and cashier operations.

Responsibilities:
- Process customer payments.
- Handle supported payment methods.
- Manage split payments.
- Generate transaction receipts.
- Submit refund requests.
- Manage assigned cashier shifts.

Cashiers cannot independently approve refund requests.

## 3.5 Waiter

Responsible for customer orders and table operations.

Responsibilities:
- Manage assigned tables.
- Create customer orders.
- Add items to existing orders.
- Submit orders to the kitchen.
- Request order modifications or cancellations.
- Monitor order preparation status.

## 3.6 Kitchen Staff

Responsible for food and beverage preparation.

Responsibilities:
- Receive kitchen orders.
- Manage preparation queues.
- Update preparation status.
- Confirm ingredient consumption.
- Report unused ingredients and waste.
- Notify relevant staff when orders are ready.

## 3.7 Inventory Staff

Responsible for inventory operations.

Responsibilities:
- Monitor ingredient quantities.
- Record stock receiving.
- Record inventory movements.
- Perform stock adjustments.
- Record waste.
- Conduct stock opname.
- Support inventory reconciliation.

## 3.8 Purchasing Staff

Responsible for procurement preparation.

Responsibilities:
- Monitor replenishment requirements.
- Select suppliers.
- Prepare purchase orders.
- Submit purchase orders for managerial approval.
- Track approved purchases.
- Coordinate supplier deliveries.

# 4. Business Requirements & Core Workflows

## 4.1 Business Registration & Outlet Setup

**Objective:** Allow businesses to establish their organization and operational outlets.

Workflow:
1. A business registers on the platform.
2. The system creates a tenant account.
3. The Business Owner configures business information.
4. The Business Owner creates one or more outlets.
5. Central business configurations are established.
6. Employees are invited or registered.
7. Employee access is assigned according to responsibilities.

Business rules:
- Every business must have an independent tenant identity.
- Every outlet belongs to exactly one business.
- Tenant data must not be accessible by another tenant.
- Employees must only access authorized business and outlet resources.

## 4.2 Employee & Access Management

**Objective:** Control employee access according to operational responsibilities.

Workflow:
1. An authorized administrator registers an employee.
2. The employee is assigned to the business.
3. The employee receives one or more operational roles or permissions.
4. Outlet access is assigned.
5. The employee can access authorized system functions.

Business rules:
- Access must be restricted by business and outlet scope.
- One employee may perform multiple operational responsibilities.
- Sensitive operations require appropriate permissions.
- Refund approval, purchase order approval, and inventory policy configuration require separate authorization.
- All permission changes must be recorded.

## 4.3 Centralized Menu Management

**Objective:** Maintain consistent menu information and pricing across all outlets.

Workflow:
1. Central Admin creates menu categories.
2. Central Admin creates products.
3. Central Admin configures product variants and add-ons.
4. Central Admin establishes menu prices.
5. Menu information is published to all outlets.
6. Outlets use the centrally managed menu during order creation.

Business rules:
- All outlets use the same centralized menu.
- All outlets use the same menu prices.
- Outlet staff cannot independently modify menu master data.
- Product names, descriptions, categories, variants, add-ons, and prices are controlled centrally.
- Outlet-specific menu and pricing overrides are not supported.
- Outlets may manage local menu availability when permitted by business policy, for example when ingredients are unavailable.
- Menu configuration changes must be recorded in an audit trail.
- Historical transactions must retain the product and price information applied when the transaction occurred.

## 4.4 Inventory Management

**Objective:** Maintain accurate ingredient quantities and track inventory movements.

Inventory management includes:
- Ingredient master data.
- On-hand stock.
- Reserved stock.
- Available stock.
- Stock receiving.
- Stock consumption.
- Stock adjustment.
- Waste recording.
- Stock opname.
- Inventory monitoring.

### 4.4.1 Inventory Quantity Model

The system distinguishes three inventory quantities:

**On-hand Stock:** Physical inventory currently recorded as available within the outlet's inventory records.

**Reserved Stock:** Inventory allocated to active orders but not yet confirmed as consumed.

**Available Stock:** Inventory that can still be allocated to new orders.

Calculation:

`Available Stock = On-hand Stock - Reserved Stock`

When ingredients are consumed, the system reduces both the physical on-hand quantity and the corresponding reservation quantity.

### 4.4.2 Inventory Reservation Workflow

1. A waiter submits an order to the kitchen.
2. The system identifies the ingredients required by the order recipes.
3. The system checks ingredient availability.
4. Required quantities are reserved for the order.
5. Reserved quantities are excluded from available stock.
6. Kitchen staff begin preparation.
7. Actual ingredient consumption is confirmed.
8. The system records consumption and reduces on-hand stock.
9. Any unused reservation is released when the order item is cancelled or otherwise no longer requires the ingredients.

Business rules:
- Kitchen submission does not automatically mean that ingredients have been consumed.
- Reserved stock and consumed stock must be tracked separately.
- Stock availability must account for existing reservations.
- Ingredient consumption must be recorded according to actual usage or kitchen confirmation.
- Every stock movement must have a traceable transaction record.

### 4.4.3 Negative Inventory Policy

The default inventory policy is **Strict Inventory**.

Under Strict Inventory:
- The system must prevent new reservations when the required available stock is insufficient.
- Orders must not silently exceed available inventory.

An optional **Allow Negative Inventory** policy may be enabled when explicitly authorized.

Business rules:
- Strict Inventory is the default.
- Allow Negative Inventory is an optional policy.
- Only the Business Owner or an authorized Manager may enable this policy.
- Inventory exceptions must be visible and traceable.
- Negative inventory must not be treated as a normal operating condition.

### 4.4.4 Stock Adjustment & Waste

Inventory adjustments must record:
- Ingredient.
- Quantity.
- Adjustment type.
- Reason.
- Responsible employee.
- Timestamp.

Waste must be recorded separately from normal ingredient consumption.

Examples include:
- Spoiled ingredients.
- Damaged ingredients.
- Ingredients discarded during preparation.
- Food preparation errors.
- Unusable leftover ingredients.

The system must preserve inventory movement history.

## 4.5 Purchasing Management

**Objective:** Manage ingredient procurement and supplier deliveries with managerial oversight.

### 4.5.1 Purchase Order Workflow

1. Inventory levels are monitored.
2. Low-stock conditions are identified.
3. Purchasing Staff reviews replenishment requirements.
4. Purchasing Staff prepares a Purchase Order (PO).
5. The PO is submitted to a Manager.
6. The Manager reviews the requested items and quantities.
7. The Manager approves or rejects the PO.
8. An approved PO can be sent to the supplier.
9. The supplier delivers the requested goods.
10. Goods Receiving is performed.
11. Accepted quantities are recorded in inventory.
12. The purchase and receiving records are retained.

### 4.5.2 Approval-Based Purchasing

The system must implement mandatory Manager approval before a Purchase Order can be sent to a supplier.

Business rules:
- Purchasing Staff may prepare purchase orders.
- Purchasing Staff cannot approve their own purchase orders unless separately authorized under an explicitly defined policy.
- Manager approval is required before supplier submission.
- Rejected purchase orders must include a rejection reason.
- Approved purchase orders must retain approval information.
- Purchase order changes after approval must follow an appropriate review and approval process.
- Purchase order and receiving histories must be auditable.

### 4.5.3 Goods Receiving

Goods Receiving records the actual items and quantities received from suppliers.

Business rules:
- Stock increases only after receiving is confirmed.
- Received quantities must be recorded.
- Discrepancies between ordered and received quantities must be identifiable.
- Damaged or rejected goods must not be counted as accepted inventory.
- Receiving records must be traceable to their purchase orders.

## 4.6 Table & Order Management

**Objective:** Manage dine-in and takeaway orders.

Supported order types:
- Dine-in.
- Takeaway.

### 4.6.1 Dine-In Workflow

1. Waiter selects an available table.
2. Waiter creates an order.
3. Customer selects menu items.
4. Waiter submits the order to the kitchen.
5. The system creates a kitchen submission record.
6. Kitchen Staff processes the submitted items.
7. Additional items may be added while the order remains open.
8. The order proceeds to payment according to the outlet's payment policy.
9. The order is closed when the required payment and operational conditions are satisfied.

### 4.6.2 Single Active Order with Add Items

The system uses the **Single Active Order** model for dine-in tables.

Business rules:
- A table may have only one active order at a time.
- Additional customer requests must be added to the existing active order.
- Waiters may add items while the order remains open.
- Each item addition must retain its own creation timestamp.
- Each kitchen submission must retain its own submission record.
- Additional items must be sent to the kitchen without disrupting previously submitted items.
- All items remain associated with the same order and its consolidated bill.
- A new active order may be created after the previous order is properly closed.

Takeaway orders are managed as individual orders and are not subject to the dine-in table concurrency rule.

### 4.6.3 Order Modification & Cancellation

The system implements **Controlled Modification**.

| Kitchen Status | Modification / Cancellation Rule |
|---|---|
| PENDING | Waiter may modify or cancel the item |
| PREPARING | Manager approval is required |
| READY | Cannot be modified or cancelled through the normal workflow |
| SERVED | Cannot be modified or cancelled through the normal workflow |

Business rules:
- Changes must be communicated to the kitchen.
- A modification must preserve the original order history.
- The system must record the reason, requesting employee, approving employee where applicable, and timestamp.
- Ingredient reservations must be recalculated after an approved change.
- Ingredients already consumed must not be automatically returned to available stock.
- Unused reserved ingredients must be released.
- Waste must be recorded separately.
- Changes affecting transaction amounts must update the applicable order balance.
- The system must preserve the relationship between original and replacement order items.

Exceptions involving READY or SERVED items must be handled through separately authorized operational or financial procedures rather than silently modifying completed kitchen records.

## 4.7 Kitchen Operations

**Objective:** Provide kitchen staff with an organized preparation queue.

Kitchen item statuses:
- PENDING
- PREPARING
- READY
- SERVED
- CANCELLED

Workflow:
1. Kitchen receives a submitted order item.
2. The item enters the PENDING queue.
3. Kitchen Staff begins preparation.
4. The item changes to PREPARING.
5. Actual ingredient usage is confirmed.
6. The item changes to READY when preparation is complete.
7. The item changes to SERVED after delivery to the customer.

Business rules:
- Kitchen submissions must be identifiable by order and submission batch.
- Additional items must appear as new kitchen work without overwriting previous submissions.
- Kitchen status changes must be recorded.
- Kitchen Staff must be able to identify approved order changes and cancellations.
- Actual ingredient consumption must be traceable.
- Waste must be recorded separately.
- Kitchen status must remain synchronized with the corresponding order item.

## 4.8 Point of Sale & Payment Management

**Objective:** Process customer payments and manage financial transactions.

Supported payment capabilities:
- Cash payment.
- Manual non-cash payment recording.
- Split payment.
- Discounts.
- Taxes.
- Service charges.
- Receipts.
- Refund requests and approvals.

### 4.8.1 Payment Timing

The system supports two payment timing policies:

**Pay Before Serving**
- Payment is required before food or beverages are served.

**Pay After Serving**
- Payment is collected after food or beverages have been served, according to outlet operations.

Business rules:
- Each outlet independently configures its payment timing policy.
- A tenant may operate different payment policies across its outlets.
- The system must enforce the selected outlet policy.
- Payment timing must not be confused with kitchen preparation or inventory reservation timing.

### 4.8.2 Centralized Tax & Service Charge

Tax and service charge configurations are centrally managed.

Business rules:
- Central Admin manages tax and service charge settings.
- All outlets use the same configuration.
- Outlets cannot independently override these settings.
- Configuration changes apply to the business outlets.
- Each transaction must preserve a snapshot of the applicable rates and calculated amounts.
- Historical receipts and transactions must not change when future configurations are updated.

### 4.8.3 Split Bill

The system supports two split bill methods.

**Split by Items**
- Customers pay for selected items.
- Each item allocation must be traceable.
- The system must prevent an item from being charged multiple times.

**Split Equally**
- The total bill is divided equally among the specified number of customers or payment portions.
- Rounding differences must be handled without changing the total payable amount.

Business rules:
- A single order may have multiple payment portions.
- Partial payments must be supported.
- Total allocated payments must reconcile with the order's payable amount.
- The system must prevent duplicate collection.
- Remaining balances must be visible.
- An order must not be considered fully paid until its payable balance reaches zero.

### 4.8.4 Refund Approval

The system implements **Approval-Based Refund**.

Workflow:
1. Customer requests a refund.
2. Cashier reviews the original transaction.
3. Cashier submits a refund request with a clear reason.
4. Manager reviews the original transaction and the refund justification.
5. Manager approves or rejects the request.
6. An approved refund is processed.
7. The refund transaction is recorded.

Business rules:
- Cashiers cannot independently approve refunds.
- Manager approval is mandatory.
- Refund requests must reference the original transaction.
- Refund requests must include a reason and requested amount.
- Rejected requests must include a rejection reason.
- Refund records must include the amount, reason, requester, approver, and timestamps.
- Refund processing must prevent duplicate refunds and amounts exceeding the eligible refundable balance.
- Original transaction history must remain intact.

## 4.9 Cashier Shift Management

**Objective:** Track cashier operational shifts and cash accountability.

Workflow:
1. Cashier opens a shift.
2. Opening cash balance is recorded.
3. Transactions are processed during the shift.
4. Cash movements are recorded where applicable.
5. Cashier closes the shift.
6. Actual cash is counted.
7. Expected and actual balances are compared.
8. Differences are recorded for review.

Business rules:
- Cash transactions must be associated with the responsible cashier and shift.
- Shift closing must preserve transaction summaries.
- Cash discrepancies must be identifiable.
- Shift records must not be silently overwritten.

## 4.10 Reports & Analytics

**Objective:** Provide business owners and managers with operational and financial visibility.

MVP reports include:
- Daily sales.
- Order summaries.
- Payment summaries.
- Best-selling menu items.
- Inventory quantities.
- Low-stock ingredients.
- Purchase summaries.
- Basic food cost information.

Business rules:
- Reports must respect tenant and outlet access boundaries.
- Users must only see authorized business data.
- Multi-outlet businesses must be able to review outlet-level information.
- Business-level summaries must aggregate authorized outlet data consistently.
- Historical reports must remain consistent with recorded transaction and inventory histories.

## 4.11 Audit & Activity History

The system must retain an audit trail for sensitive and operationally important activities.

Activities include:
- User and permission changes.
- Centralized menu changes.
- Pricing changes.
- Tax and service charge configuration changes.
- Order modifications and cancellations.
- Inventory reservations and releases.
- Ingredient consumption.
- Waste and stock adjustments.
- Purchase order creation and approval.
- Goods receiving.
- Refund requests and decisions.
- Payment and shift operations.

Audit records should identify:
- Action performed.
- Related business entity.
- Responsible user.
- Timestamp.
- Previous and new values where applicable.
- Reason or justification where required.

Audit history must not be silently altered by ordinary operational users.

# 5. Integrated End-to-End Business Workflow

The following workflow represents the main operational lifecycle of a restaurant or café.

1. Business registers and establishes its outlets.
2. Central Admin configures the shared menu, prices, tax, and service charge.
3. Employees are registered and receive authorized access.
4. Inventory Staff records initial stock.
5. The system monitors ingredient availability.
6. When stock becomes low, Purchasing Staff prepares a replenishment PO.
7. Manager reviews and approves the PO.
8. Supplier delivers the goods.
9. Inventory Staff confirms Goods Receiving.
10. Stock quantities are updated.
11. Waiter creates a dine-in or takeaway order.
12. Waiter submits order items to the kitchen.
13. The system checks ingredient availability and reserves required quantities.
14. Kitchen Staff prepares the order.
15. Actual ingredient consumption is confirmed and recorded.
16. Additional items may be added to an active dine-in order.
17. Approved modifications or cancellations update the relevant reservations and inventory records.
18. Kitchen Staff marks completed items as READY and subsequently SERVED.
19. Cashier processes payment according to the outlet's payment timing policy.
20. Customers may pay using a single payment or supported split bill methods.
21. If a refund is requested, Cashier submits it for Manager approval.
22. Transactions and inventory movements are recorded.
23. Business Owner and Managers review operational and financial reports.

# 6. Consolidated Business Rules

The following rules are mandatory for the MVP business baseline.

| ID | Business Rule |
|---|---|
| BR-001 | Each business operates within an isolated tenant boundary. |
| BR-002 | Each outlet belongs to one business. |
| BR-003 | Users may only access authorized business and outlet resources. |
| BR-004 | Central Admin manages shared menu master data and pricing. |
| BR-005 | All outlets use the same centralized menu and prices. |
| BR-006 | Tax and service charge configurations are centrally managed. |
| BR-007 | Historical transactions preserve applicable pricing and configuration snapshots. |
| BR-008 | Payment timing is configurable independently per outlet. |
| BR-009 | Each dine-in table may have only one active order. |
| BR-010 | Additional items must be added to the existing active table order. |
| BR-011 | Every kitchen submission must retain its own traceable record. |
| BR-012 | Order modifications follow the approved kitchen-status rules. |
| BR-013 | Manager approval is required for modifications or cancellations during PREPARING. |
| BR-014 | READY and SERVED items cannot be cancelled through the normal workflow. |
| BR-015 | Strict Inventory is the default inventory policy. |
| BR-016 | Allow Negative Inventory requires authorized activation. |
| BR-017 | Kitchen submission creates ingredient reservations, not automatic consumption. |
| BR-018 | Physical stock is reduced according to actual ingredient consumption. |
| BR-019 | Unused reservations must be released when no longer required. |
| BR-020 | Waste must be recorded separately. |
| BR-021 | Purchase Orders require Manager approval before supplier submission. |
| BR-022 | Goods Receiving updates inventory only after confirmation. |
| BR-023 | Refunds require Manager approval. |
| BR-024 | Refund requests must include a clear reason and reference the original transaction. |
| BR-025 | Split Bill supports Split by Items and Split Equally. |
| BR-026 | Payment allocations must reconcile with the payable transaction amount. |
| BR-027 | Sensitive activities must be recorded in an audit trail. |
| BR-028 | Financial and inventory histories must remain traceable. |

# 7. Exception Handling

The system must account for operational situations that may occur during normal business activities.

| Scenario | Expected System Behavior |
|---|---|
| Ingredient stock is insufficient | Reject reservation under Strict Inventory; apply the authorized negative inventory policy only when enabled. |
| Order is cancelled before preparation | Release unused ingredient reservations. |
| Order is cancelled during preparation | Record consumed ingredients, release unused reservations, and record waste where applicable. |
| Customer changes an item during preparation | Require Manager approval and recalculate ingredient reservations. |
| Customer requests a change after an item is READY or SERVED | Do not modify the completed kitchen record through the normal workflow. |
| Additional items are ordered at an occupied table | Add items to the existing active order and create new kitchen submission records. |
| Purchase Order is rejected | Preserve rejection reason and prevent supplier submission. |
| Supplier delivers fewer items than ordered | Record actual accepted quantities and receiving discrepancies. |
| Refund request is rejected | Preserve the rejection reason and do not process the refund. |
| Partial payment is made | Preserve the outstanding balance and payment history. |
| A menu or tax configuration changes | Preserve historical transaction snapshots. |
| A user attempts unauthorized approval | Reject the action and record the security event where appropriate. |

# 8. MVP Business Scope

The MVP must support the following business capabilities.

## 8.1 Included

- SaaS tenant and business management.
- Multi-outlet organization.
- Employee and access management.
- Centralized menu and pricing.
- Centralized tax and service charge.
- Dine-in and takeaway orders.
- Single Active Order with Add Items.
- Kitchen order queue and preparation status.
- Controlled order modification and cancellation.
- Inventory reservation and actual consumption tracking.
- Negative inventory policy control.
- Stock receiving, adjustments, waste, and stock opname.
- Supplier management.
- Approval-Based Purchasing.
- Goods Receiving.
- POS and manual payment recording.
- Pay Before Serving and Pay After Serving.
- Split Bill by Items and Split Equally.
- Approval-Based Refund.
- Cashier shift management.
- Basic reports and analytics.
- Audit and activity history.

## 8.2 Excluded from MVP

The following capabilities are deferred to post-MVP:
- Online customer ordering portal.
- Reservation management.
- Customer loyalty programs.
- Advanced CRM.
- QR-based customer ordering.
- Third-party delivery integrations.
- Online payment gateway integrations.
- Advanced accounting integration.
- Employee attendance and payroll.
- Advanced forecasting and analytics.
- Offline-first synchronization.
- Advanced inventory transfers between outlets.
- Automated supplier integrations.

# 9. Business Assumptions & Constraints

The following assumptions guide the business baseline and may be refined during detailed design.

1. Each business operates independently as a SaaS tenant.
2. A business may operate one or multiple outlets.
3. Centralized menu, pricing, tax, and service charge are shared across all outlets.
4. Payment timing may differ between outlets.
5. Outlet inventory quantities are managed independently.
6. Inventory quantities are based on ingredient-level records and recipe requirements.
7. Recipe quantities represent standard ingredient requirements; actual consumption may require reconciliation.
8. Manual non-cash payment recording is included in the MVP; automated payment gateway integration is deferred.
9. Manager approval is mandatory for purchase orders and refunds.
10. Operational roles and permissions must be configurable without violating the required approval controls.
11. The platform must support web, tablet, and native mobile experiences, with implementation rollout determined during implementation planning.

# 10. Business Completion Criteria

The business workflow baseline is considered complete when the system design can demonstrate:

1. Independent tenant data isolation.
2. Multiple outlets under one business.
3. Centralized menu and pricing across outlets.
4. Centralized tax and service charge configuration.
5. Independent outlet payment timing policies.
6. Employee access and operational authorization.
7. Dine-in and takeaway order creation.
8. Single Active Order with Add Items.
9. Kitchen status tracking and controlled order modifications.
10. Inventory reservation and actual ingredient consumption.
11. Correct handling of unused reservations and waste.
12. Manager-approved purchasing and receiving.
13. POS payment and both split bill methods.
14. Manager-approved refunds.
15. Cashier shift reconciliation.
16. Operational and financial reporting.
17. Traceable audit history.

# 11. Approved Business Decisions

The following ten decisions were explicitly reviewed and approved during product discovery and business workflow discussions.

| No. | Decision Area | Approved Decision |
|---|---|---|
| 01 | Payment Timing | Support Pay Before Serving and Pay After Serving, configurable independently per outlet. |
| 02 | Negative Inventory | Strict Inventory by default; Allow Negative Inventory is optional and requires authorized activation. |
| 03 | Order Modification | Controlled Modification based on kitchen status, with Manager approval during PREPARING. |
| 04 | Table Order | Single Active Order with Add Items. |
| 05 | Menu Management | Centralized Menu and Pricing managed by Central Admin. |
| 06 | Purchasing | Approval-Based Purchasing; Manager approval is mandatory before supplier submission. |
| 07 | Refund | Approval-Based Refund; Manager approval is mandatory before processing. |
| 08 | Tax & Service Charge | Centralized Configuration shared across outlets. |
| 09 | Split Bill | Support both Split by Items and Split Equally. |
| 10 | Inventory Deduction | Reserve ingredients upon kitchen submission; reduce physical stock only when actual consumption is confirmed. |

These decisions are the approved business baseline and must not be contradicted by subsequent technical designs without an explicit product decision.

# 12. Relationship to Subsequent Documents

This BRD is the business reference for the following project documents:

1. Functional & Non-Functional Requirements (FRD).
2. System Architecture Document.
3. Database Design Document.
4. API Design Document.
5. UI/UX Design Specification.
6. Implementation Plan.
7. Test Strategy and Test Cases.

Any requirement or technical design that conflicts with this document must be reviewed and reconciled before implementation.

# 13. Document Approval

**Document ID:** BRD-FOUNDATION-001  
**Version:** 2.0.0  
**Status:** Approved — Business Workflow Baseline

The business model, core workflows, and ten business decisions have been established as the approved baseline for subsequent system design.

Detailed technical implementation, database structures, API contracts, and UI behavior will be defined in their respective documents.

**End of Document**
