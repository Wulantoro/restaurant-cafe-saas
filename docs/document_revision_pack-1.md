# Document Revision Pack
## Restaurant & Café Management System

**Purpose:** Correct inconsistencies between PRD, BRD, and FRD without changing previously approved business decisions, and record the final resolutions for Business Clarifications (BD-001 through BD-010).

---

# PART A — PRD CORRECTIONS

## A1. Replace Section 5.2 — Menu Management

## 5.2 Menu Management

Menu management is centrally governed by the Central Admin. All outlets under the same business use the centrally managed menu and pricing configuration.

Responsibilities:

- Centralized menu category management.
- Centralized product and menu item management.
- Centralized product variant management.
- Centralized add-on and modifier management.
- Centralized product pricing configuration.
- Centralized recipe configuration, shared across all outlets under the same business (per BD-002).
- Outlet-level product availability management, subject to the policies defined by the Central Admin.
- Menu publication and deactivation.
- Preservation of historical product and pricing information used by existing transactions.

Business rules:

- Outlets must not independently modify centrally managed product definitions, recipes, or prices.
- An outlet may manage local product availability only when permitted by the central menu policy.
- Historical transactions must retain the product descriptions and prices recorded when the transaction was created.
- Changes to the central menu must not silently modify historical transactions.

## A2. Replace Section 6.1 B — Menu Foundation

### B. Menu Foundation

The MVP must support:

- Centralized menu category management.
- Centralized product management.
- Product variants.
- Add-ons and modifiers.
- Centralized product pricing.
- Centralized recipe and ingredient definitions shared across all outlets under the business (per BD-002).
- Outlet-level product availability, subject to central policy.
- Historical product and pricing snapshots for transactions.

Outlets must not independently modify centrally managed menu definitions, recipes, or prices.

## A3. Replace Section 6.2 — MVP Business Workflow

## 6.2 MVP Business Workflow

The MVP must support the following end-to-end workflow:

1. A business is registered on the platform.
2. The business profile and initial outlet are configured.
3. Employees are created and assigned roles and outlet permissions.
4. The Central Admin manages the centralized menu categories, products, variants, add-ons, recipes, and pricing.
5. Outlet product availability is configured according to the central menu policy.
6. Inventory Staff records incoming ingredients and confirms goods receiving.
7. A Waiter creates a dine-in or takeaway order.
8. The order is submitted to the kitchen.
9. The kitchen processes the order and updates individual item statuses.
10. The system manages ingredient reservations according to the inventory reservation rules.
11. Actual ingredient consumption is automatically confirmed based on standard recipes when items reach `READY`, with manual adjustments/waste recorded separately where applicable (per BD-003).
12. The cashier processes payment according to the payment timing configuration of the outlet.
13. The system records the transaction, payment allocations, and applicable financial snapshots.
14. The system updates operational and financial records.
15. The Business Owner or authorized Manager reviews operational reports.

The system must preserve data consistency across ordering, kitchen operations, inventory, purchasing, and payment workflows.

## A4. Replace Assumption 10 in Section 9 — Business Assumptions

Replace the existing assumption number 10 with:

10. All outlets within the same business use a centrally managed menu, recipe, and pricing configuration. Outlet-level product availability may differ when permitted by central menu policies.

Keep the other assumptions unchanged.

## A5. Add to Section 14 — Current Project Status

Add these items to the status table:

| Item | Status |
|---|---|
| Centralized menu and pricing policy | Approved in BRD v2.0.0 |
| Outlet-level product availability policy | Approved in BRD v2.0.0 |
| Payment timing configuration | Approved in BRD v2.0.0 |
| Inventory reservation and consumption policy | Approved in BRD v2.0.0 |
| Recipe ownership and sharing rules (BD-002) | Approved — Centralized per Business |
| Actual consumption confirmation process (BD-003) | Approved — Automated on READY + Manual Waste/Adjustment |
| Central Admin organizational scope (BD-001) | Approved — Tenant/Business-level Administrator |

---

# PART B — BRD CLARIFICATIONS

**Important:** Keep the ten approved business decisions in BRD v2.0.0 unchanged.

The following sections are additions to the existing BRD. They do not replace or reverse any approved decision.

## B1. Add Section 5.1 — Centralized Menu Governance

### 5.1 Centralized Menu Governance

The menu, recipe, and pricing configuration is managed centrally by the Central Admin within the business (tenant) scope.

Business rules:

1. All outlets under the same business use the same centrally managed menu definitions, recipes, and prices.
2. Outlets cannot independently modify centrally managed menu categories, product definitions, variants, add-ons, recipes, or prices.
3. Outlet-level product availability may be managed locally when permitted by central menu policies.
4. Changes to menu definitions and prices must not alter historical transaction records.
5. Each transaction must preserve the product information and applicable price used at the time the order was created.

## B2. Add Section 5.2 — Inventory Reservation and Consumption Clarification

### 5.2 Inventory Reservation and Consumption Clarification

The inventory process must distinguish between on-hand stock, reserved stock, and actual consumption.

The following rules apply:

1. When an order is submitted to the kitchen, the system checks the required ingredients based on the centralized recipe.
2. Required quantities are reserved for the submitted order items.
3. Reserved quantities are not immediately treated as consumed stock.
4. On-hand stock is reduced automatically based on standard recipe quantities when the kitchen item status transitions to `READY` (per BD-003).
5. Unused reservations must be released when the corresponding order items are cancelled prior to completion.
6. Ingredients already confirmed as consumed (`READY` or `SERVED`) must remain recorded as consumed.
7. Any preparation variances, spoilage, or errors must be recorded separately as waste or stock adjustments.
8. Available stock is calculated as:

   `Available Stock = On-hand Stock - Reserved Stock`

9. Changes or cancellations during `PREPARING` require Manager approval (per modification request batch).
10. `READY` and `SERVED` items cannot be modified or cancelled through the normal workflow.

## B3. Add Section 7.1 — Approved Business Clarifications (BD-001 to BD-010)

### 7.1 Approved Business Clarifications

The following ten business clarifications have been analyzed and approved as binding specifications for technical architecture, database design, API design, and implementation:

| ID | Topic | Approved Decision & Specification |
|---|---|---|
| BD-001 | Central Admin authority | **Tenant/Business-Level Role:** Central Admin operates strictly within a single registered Business (Tenant) to manage shared master data (menus, recipes, pricing, taxes, service charges). Platform-level SaaS administration is completely separate to preserve strict tenant isolation. |
| BD-002 | Recipe ownership | **Centralized Recipes:** Recipes and ingredient compositions are centrally defined and managed by the Central Admin at the Business level and shared across all outlets, ensuring consistent product standards and accurate consolidated food cost reporting. Stock deductions still occur per outlet. |
| BD-003 | Actual consumption confirmation | **Automated on `READY` + Manual Variance:** Actual ingredient consumption is automatically confirmed and deducted from `On-hand Stock` based on standard recipe quantities when a kitchen item transitions to `READY`. Any over-usage, spoilage, or preparation errors are recorded manually via separate Waste or Stock Adjustment workflows. |
| BD-004 | Order closure | **Dual-Condition Closure (`PAID` + All `SERVED`):** An order transitions to `CLOSED` only when its payment balance reaches zero (`PAID`) **AND** all non-cancelled items in the order have reached `SERVED`. This applies consistently across both *Pay Before Serving* and *Pay After Serving* policies so tables are never released prematurely. |
| BD-005 | Void and refund | **Pre-Payment vs. Post-Payment:** **Void** cancels unpaid items/orders (`UNPAID`), authorized by Waiter/Cashier when `PENDING` or requiring Manager approval when `PREPARING`. **Refund** returns funds on settled/partially settled transactions (`PARTIALLY_PAID` or `PAID`), initiated by Cashier with a mandatory reason and strictly requiring Manager approval. |
| BD-006 | Approved PO changes | **Immutable Approved PO:** Once approved by a Manager, a Purchase Order's items and prices are locked. Modifications require cancelling the PO (if no goods have been received) and issuing a revised PO through the standard Manager approval workflow. Delivery quantity differences are handled in Goods Receiving as partial receiving or discrepancies. |
| BD-007 | Negative inventory and reservations | **Full Reservation with Exception Flag:** When *Allow Negative Inventory* is enabled, the system still reserves the full required recipe quantities even if `Available Stock` drops below zero (`Available = On-hand - Reserved`). The transaction is flagged as an inventory exception in the audit trail to track exact replenishment deficits. |
| BD-008 | Split bill allocation | **Item-Level vs. Order-Level Calculation:** For **Split by Items**, each split calculates its subtotal from selected items, applies item/proportional discounts, and recalculates tax and service charge per split, assigning any rounding remainder to the final split. For **Split Equally**, discounts, tax, and service charge are calculated on the full order total first, then divided equally with any rounding remainder assigned to the first or final payment portion. |
| BD-009 | Refund limits | **Net Paid Cap & Partial Support:** Cumulative refunds for a transaction cannot exceed the net amount actually collected (`Total Paid - Total Previously Refunded`). Partial refunds are supported either by specific dollar/currency amount or by selecting specific paid items (including their proportional tax and service charge). |
| BD-010 | Modification approval scope | **Batch Request, Item-Level Execution:** Manager approval is requested and granted at the **Modification Request Batch** level (allowing multiple `PREPARING` items to be submitted with a single justification), while the system logs audit trails, updates kitchen statuses, and recalculates ingredient reservations individually per item. |

---

# PART C — FRD CORRECTIONS

## C1. Replace FR-03 Menu & Product Management

## FR-03 Menu & Product Management

| ID | Requirement | Priority |
|---|---|---|
| FR-016 | The system shall allow the Central Admin to manage menu categories centrally within the business tenant. | MUST |
| FR-017 | The system shall allow the Central Admin to manage food and beverage product definitions centrally. | MUST |
| FR-018 | The system shall support product variants within the centralized menu configuration. | MUST |
| FR-019 | The system shall support add-ons and modifiers within the centralized menu configuration. | MUST |
| FR-020 | The system shall allow the Central Admin to configure product prices centrally for all outlets under the same business. | MUST |
| FR-021 | The system shall allow outlet-level product availability management only within the policies defined by the Central Admin. | MUST |
| FR-022 | The system shall allow the Central Admin to configure centralized recipes shared across all outlets under the business (per BD-002). | MUST |
| FR-023 | The system shall allow products to be deactivated without deleting historical transaction records. | MUST |

## C2. Replace FR-04 Table & Order Management

## FR-04 Table & Order Management

| ID | Requirement | Priority |
|---|---|---|
| FR-024 | The system shall provide table management for each outlet. | MUST |
| FR-025 | The system shall display table availability and occupancy status. | MUST |
| FR-026 | The system shall support dine-in orders. | MUST |
| FR-027 | The system shall support takeaway orders. | MUST |
| FR-028 | The system shall allow authorized users to add products to an order. | MUST |
| FR-029 | The system shall support product variants and add-ons in order items. | MUST |
| FR-030 | The system shall support special instructions for individual order items. | MUST |
| FR-031 | The system shall calculate order subtotals automatically. | MUST |
| FR-032 | The system shall support adding items to the single active dine-in order associated with a table. Each addition shall have its own timestamp and kitchen submission record. | MUST |
| FR-033 | The system shall enforce the approved order modification and cancellation rules based on item preparation status, supporting batch modification requests with item-level processing (per BD-010). | MUST |
| FR-034 | The system shall maintain an order modification history containing the reason, requester, approver when applicable, and timestamp. | MUST |
| FR-035 | The system shall preserve product descriptions and applicable prices as transaction snapshots. | MUST |
| FR-035A | The system shall transition an order to `CLOSED` only when payment status is `PAID` and all non-cancelled items have reached `SERVED` (per BD-004). | MUST |

## C3. Replace FR-05 Kitchen Operations

## FR-05 Kitchen Operations

| ID | Requirement | Priority |
|---|---|---|
| FR-036 | The system shall send submitted order items to the kitchen queue. | MUST |
| FR-037 | The system shall display kitchen queues according to outlet. | MUST |
| FR-038 | The system shall display order item details, quantities, and special instructions. | MUST |
| FR-039 | The system shall support the item statuses PENDING, PREPARING, READY, SERVED, and CANCELLED. | MUST |
| FR-040 | The system shall allow authorized kitchen staff to update individual item preparation statuses. | MUST |
| FR-041 | The system shall support partial completion when items belonging to the same order are completed at different times. | MUST |
| FR-042 | The system shall record kitchen status changes and notify relevant operational users when an order item is ready. | MUST |

## C4. Replace FR-06 Point of Sale & Payment

## FR-06 Point of Sale & Payment

| ID | Requirement | Priority |
|---|---|---|
| FR-043 | The system shall provide a cashier interface for processing order payments. | MUST |
| FR-044 | The system shall automatically calculate order totals, including applicable discounts, taxes, and service charges. | MUST |
| FR-045 | The system shall apply centrally managed tax and service charge configurations. | MUST |
| FR-046 | The system shall support discounts subject to the required authorization. | MUST |
| FR-047 | The system shall support cash payments. | MUST |
| FR-048 | The system shall support manual recording of non-cash payments. | MUST |
| FR-049 | The system shall support split bills using both Split by Items and Split Equally methods, applying the approved tax, discount, and rounding allocation rules (per BD-008). | MUST |
| FR-050 | The system shall record each payment method, amount, payment time, and associated transaction. | MUST |
| FR-051 | The system shall support UNPAID, PARTIALLY_PAID, PAID, and REFUNDED payment states. | MUST |
| FR-052 | The system shall generate transaction receipts. | MUST |
| FR-053 | The system shall distinguish pre-payment voids from post-payment refunds, requiring Manager approval for refunds and capping cumulative refunds at net paid amounts (per BD-005, BD-009). | MUST |
| FR-054 | The system shall prevent duplicate payment processing for the same payment obligation. | MUST |
| FR-055 | The system shall preserve snapshots of product prices, discounts, tax rates, tax amounts, service charge rates, and service charge amounts used in each transaction. | MUST |

Additional payment requirements:

1. Each outlet shall independently configure its payment timing as either Pay Before Serving or Pay After Serving.
2. The system shall support partial payments and outstanding balances.
3. Payment allocations must reconcile with the total amount payable.
4. Rounding during split payment must not change the total amount payable and shall be assigned to the designated split portion (per BD-008).
5. The system must prevent duplicate collection for the same payment obligation.
6. Historical transactions must retain their original tax and service charge snapshots even when central configurations change.
7. Partial refunds by amount or by item shall be supported up to the remaining refundable paid balance (per BD-009).

## C5. Replace FR-08 Inventory Management

## FR-08 Inventory Management

| ID | Requirement | Priority |
|---|---|---|
| FR-063 | The system shall provide raw material and ingredient management. | MUST |
| FR-064 | The system shall support measurement units for ingredients. | MUST |
| FR-065 | The system shall maintain inventory records independently for each outlet. | MUST |
| FR-066 | The system shall record confirmed stock receiving activities. | MUST |
| FR-067 | The system shall reserve ingredient quantities when submitted order items enter the kitchen workflow, based on centralized recipes, recording full reservations with exception flags when negative inventory is authorized (per BD-007). | MUST |
| FR-068 | The system shall automatically confirm ingredient consumption and reduce on-hand stock based on standard recipes when kitchen items reach `READY` (per BD-003). | MUST |
| FR-069 | The system shall release unused ingredient reservations when the corresponding order items are cancelled prior to `READY`. | MUST |
| FR-070 | The system shall record waste separately from normal ingredient consumption. | MUST |
| FR-071 | The system shall support stock adjustments and stock opname. | MUST |
| FR-072 | The system shall maintain an auditable history of inventory movements and provide stock availability information. | MUST |

Additional inventory requirements:

1. The system shall distinguish on-hand stock from reserved stock.
2. Available stock shall be calculated as on-hand stock minus reserved stock.
3. Confirmed consumption (at `READY`) must not be reversed automatically when an order is subsequently cancelled.
4. Order modifications and cancellations during `PREPARING` must follow the Manager approval workflow.
5. `READY` and `SERVED` items cannot be cancelled through the normal workflow.
6. The system shall use Strict Inventory as the default inventory policy.
7. Allow Negative Inventory may be activated only by the Business Owner or an authorized Manager.
8. When Allow Negative Inventory is active, reservations proceed normally into negative available balances while generating an inventory exception audit record (per BD-007).

## C6. Replace FR-09 Purchasing Management

## FR-09 Purchasing Management

| ID | Requirement | Priority |
|---|---|---|
| FR-073 | The system shall provide supplier management. | MUST |
| FR-074 | The system shall allow Purchasing Staff to create purchase orders. | MUST |
| FR-075 | The system shall require Manager approval before a purchase order can be submitted to a supplier. | MUST |
| FR-076 | The system shall record goods receiving activities after receiving confirmation. | MUST |
| FR-077 | The system shall support partial goods receiving. | MUST |
| FR-078 | The system shall update inventory based on the actual accepted quantity of received goods. | MUST |
| FR-079 | The system shall maintain purchase order history, including preparation, approval, rejection, submission, cancellation, and receiving records. | MUST |

Additional purchasing requirements:

1. A purchase order must not be submitted to a supplier before Manager approval.
2. A rejected purchase order must include a rejection reason.
3. Approved purchase orders are immutable regarding items and prices; modifications require cancelling the unreceived PO and creating a revised PO for Manager approval (per BD-006).
4. Inventory must not be increased merely because a purchase order has been created or approved.
5. Inventory must be updated only after the actual accepted quantity has been confirmed during goods receiving.
6. Partial receiving must preserve the quantities ordered, received, accepted, rejected, and outstanding where applicable.

## C7. Replace FR-11 Audit & Activity History

## FR-11 Audit & Activity History

| ID | Requirement | Priority |
|---|---|---|
| FR-091 | The system shall record important user activities. | MUST |
| FR-092 | The system shall record changes to important business data. | MUST |
| FR-093 | Audit records shall include the actor, timestamp, action type, and affected resource. | MUST |
| FR-094 | Sensitive operations shall record the reason and relevant approval information, including requester and approver when applicable. | MUST |
| FR-095 | The system shall allow authorized users to access relevant activity history. | SHOULD |

Audit records should cover at least:

- Order creation and item additions.
- Order modification and cancellation requests (batch and item-level).
- Manager approval and rejection.
- Kitchen status changes.
- Ingredient reservation, release, negative inventory exceptions, and consumption confirmation.
- Waste recording.
- Stock receiving and adjustment.
- Purchase order creation, approval, rejection, cancellation, and receiving.
- Payment creation and payment allocation.
- Void actions and refund requests, approval, rejection, and processing.
- Central menu, recipe, and pricing changes.
- Tax and service charge configuration changes.
- Employee and permission changes.

---

# PART D — NON-FUNCTIONAL REQUIREMENT IMPROVEMENTS

Replace the corresponding NFR rows with the following more testable requirements.

## D1. Security

| ID | Requirement |
|---|---|
| NFR-001 | All application-to-backend communication shall use HTTPS in production environments. |
| NFR-002 | Passwords shall be stored using an approved secure password hashing algorithm. |
| NFR-003 | Every business-owned data access shall enforce tenant isolation. A user from one tenant must not access another tenant's data by changing identifiers or request parameters. |
| NFR-004 | Authorization shall be enforced by the backend for every protected operation. |
| NFR-005 | Secrets and credentials shall not be committed to source control. |
| NFR-006 | User input shall be validated on the backend before processing or persistence. |
| NFR-007 | Sensitive business operations shall generate auditable records. |

## D2. Performance

| ID | Requirement |
|---|---|
| NFR-008 | Under the defined MVP performance test workload, 95% of normal operational API requests shall complete within 500 ms, excluding external network dependencies. |
| NFR-009 | List endpoints shall support pagination and bounded result sizes. |
| NFR-010 | Reporting queries shall not cause unacceptable delays to operational transaction processing under the defined test workload. |
| NFR-011 | Database queries used by frequently accessed operational endpoints shall be reviewed and tested for appropriate indexing and query efficiency. |

The actual concurrent-user count, dataset size, and test environment must be documented in the performance test plan before this target is treated as a verified performance commitment.

## D3. Reliability & Data Integrity

| ID | Requirement |
|---|---|
| NFR-012 | Financial transactions shall preserve consistent totals between order amounts, payment allocations, refunds, and outstanding balances. |
| NFR-013 | Related order, payment, inventory reservation, stock movement, and approval changes shall use appropriate database transaction boundaries. |
| NFR-014 | Critical operations shall prevent duplicate processing when the same request is submitted repeatedly. |
| NFR-015 | Concurrent modifications to the same order, payment obligation, or inventory balance shall be handled without silently overwriting valid changes. |
| NFR-016 | The system shall provide documented database backup and recovery procedures. Recovery Point Objective (RPO) and Recovery Time Objective (RTO) shall be defined before production deployment. |

## D4. Scalability

| ID | Requirement |
|---|---|
| NFR-017 | The data model and application shall support multiple independent tenants and multiple outlets per tenant. |
| NFR-018 | The system shall support increasing numbers of users, orders, payments, and inventory movements without requiring changes to the core business model. |
| NFR-019 | Application modules shall have clear responsibilities and boundaries to support incremental development and future scaling. |

## D5. Maintainability

| ID | Requirement |
|---|---|
| NFR-020 | Source code shall follow a documented modular structure and consistent coding conventions. |
| NFR-021 | API endpoints shall be documented using a consistent API specification. |
| NFR-022 | Database schema changes shall be managed through version-controlled migrations. |
| NFR-023 | Automated tests shall cover critical business rules, authorization boundaries, data integrity, and primary user workflows. |
| NFR-024 | The application shall use centralized error handling and consistent error response structures. |
| NFR-025 | The application shall produce structured logs containing sufficient context for troubleshooting without exposing sensitive data. |

## D6. Availability & Observability

| ID | Requirement |
|---|---|
| NFR-026 | The backend shall provide a health endpoint that indicates application availability and a separate readiness check for required dependencies where applicable. |
| NFR-027 | Application errors and failed critical operations shall be logged with sufficient diagnostic context. |
| NFR-028 | The application shall support graceful shutdown and termination of active resources. |
| NFR-029 | The application shall expose sufficient operational information to monitor application health, database connectivity, and critical failures. |

## D7. Compatibility & Deployment

| ID | Requirement |
|---|---|
| NFR-030 | The web application shall support currently maintained versions of major modern browsers. |
| NFR-031 | The MVP web interface shall be responsive and usable on desktop and tablet screen sizes. |
| NFR-032 | The application shall support containerized deployment using Docker. |
| NFR-033 | GitHub Actions shall execute automated tests and build verification for relevant code changes. |
| NFR-034 | Development, testing, and production environments shall use separate configuration and secret management. |

Native mobile application implementation is not an MVP deployment requirement. Native mobile support remains part of the broader product direction and will be addressed in a later implementation phase.

---

# PART E — REPLACE FRD SECTION 5: ACCEPTANCE CRITERIA

# 5. Acceptance Criteria

The MVP shall be accepted when the following conditions are demonstrably satisfied.

## 5.1 Business and Access Management

1. A user can register a business and create its initial outlet.
2. A business can operate multiple outlets.
3. Employees can be assigned roles and outlet-level permissions.
4. Users cannot access resources belonging to another tenant.
5. Users cannot perform operations outside their assigned permissions.

## 5.2 Menu Management

6. Centralized menu categories, products, and recipes can be managed by the authorized Central Admin within the tenant.
7. All outlets under the same business use centrally managed product definitions, recipes, and prices.
8. Outlet-level product availability follows the central menu policy.
9. Historical transactions retain their original product and price information.

## 5.3 Ordering and Kitchen

10. Users can create dine-in and takeaway orders.
11. Each table can have only one active dine-in order.
12. Additional items can be added to an active table order.
13. Each item addition generates its own kitchen submission record and timestamp.
14. Order modifications and cancellations follow the approved status-based authorization rules, supporting batch approvals with item-level execution.
15. Kitchen staff can update item preparation statuses independently.
16. Partial kitchen completion is supported.
17. Orders transition to `CLOSED` only when both `PAID` and all non-cancelled items are `SERVED`.

## 5.4 POS and Payment

18. Each outlet can use either Pay Before Serving or Pay After Serving.
19. Cashiers can record cash and manual non-cash payments.
20. Split bills support Split by Items and Split Equally with accurate discount, tax, service charge, and rounding allocation.
21. Partial payments and outstanding balances are recorded accurately.
22. Payment allocations reconcile with the amount payable.
23. The system prevents duplicate payment processing.
24. Tax and service charge values are calculated using centrally managed configurations.
25. Historical transactions retain their original financial snapshots.
26. Pre-payment voids and post-payment refunds follow their respective authorization workflows, with refunds requiring Manager approval and capped at net paid amounts.

## 5.5 Inventory

27. Submitting an order to the kitchen creates the applicable ingredient reservations based on centralized recipes.
28. Reserved stock is not immediately treated as consumed stock.
29. Actual consumption reduces on-hand stock automatically when items reach `READY`.
30. Unused reservations are released when corresponding order items are cancelled prior to `READY`.
31. Confirmed consumption remains recorded even if the order is subsequently cancelled.
32. Waste is recorded separately from normal consumption.
33. Strict Inventory is the default policy.
34. Allow Negative Inventory can only be activated by an authorized Business Owner or Manager, logging inventory exceptions when reservations exceed available stock.
35. Inventory movements are traceable through their history.

## 5.6 Purchasing

36. Purchasing Staff can prepare purchase orders.
37. A Manager must approve a purchase order before supplier submission.
38. Approved POs are immutable; changes require PO cancellation and re-issuance for Manager approval.
39. Rejected purchase orders contain a rejection reason.
40. Goods receiving supports partial quantities.
41. Inventory changes only after actual accepted goods have been confirmed.

## 5.7 Reports and Audit

42. Authorized users can view outlet-level reports.
43. Authorized users can view consolidated business-level reports.
44. Reports preserve the outlet identity of their source records.
45. Sensitive operations generate appropriate audit records.
46. Automated tests verify the primary workflows and critical failure conditions.

---

# PART F — REPLACE FRD SECTION 6: REQUIREMENTS TRACEABILITY

# 6. Requirements Traceability

Every functional and non-functional requirement shall be traceable throughout the development lifecycle.

Each requirement should be linked to:

- Its originating business requirement or workflow.
- Its responsible application module.
- Related database entities and constraints.
- Related API endpoints.
- Related UI screens or interactions.
- Related automated test cases.
- Its implementation status.

Requirement identifiers shall remain stable across architecture, database design, API specification, implementation, and testing.

A requirement shall not be marked as completed solely because its API or UI has been implemented. Its relevant business rules and acceptance criteria must also be verified.

---

# PART G — REPLACE FRD SECTION 7: OPEN DECISIONS

# 7. Open Decisions

All core business decisions (1–10 in BRD v2.0.0) and all detailed business clarifications (`BD-001` through `BD-010`) have been resolved and approved:

1. Payment timing supports Pay Before Serving and Pay After Serving, configurable independently per outlet.
2. Strict Inventory is the default, while Allow Negative Inventory is optional and requires authorized activation (reserving full quantities with exception logging per `BD-007`).
3. Order modification follows the approved status-based Controlled Modification policy, with batch Manager approval and item-level execution during `PREPARING` (`BD-010`).
4. Each table supports a Single Active Order with Add Items, closing only when `PAID` and all non-cancelled items are `SERVED` (`BD-004`).
5. Menu, recipes (`BD-002`), and pricing are centrally managed by a tenant-scoped Central Admin (`BD-001`) without outlet-level overrides.
6. Purchase orders require Manager approval before supplier submission and are immutable once approved (`BD-006`).
7. Pre-payment voids are separated from post-payment refunds (`BD-005`), with refunds requiring Manager approval and capped at net paid amounts (`BD-009`).
8. Tax and service charge configurations are centrally managed.
9. Split bills support Split by Items and Split Equally with defined tax, discount, and rounding allocation rules (`BD-008`).
10. Inventory follows reservation-first upon kitchen submission and automated consumption deduction upon `READY` status (`BD-003`).

**Open Decisions Count:** 0 (All baseline requirements are locked for technical design).

---

# PART H — REPLACE FRD SECTION 8: STATUS

# 8. Status

**Current Status:** Approved — Requirements Baseline Complete.

The functional and non-functional requirements have been fully aligned with BRD v2.0.0, and all ten business clarifications (`BD-001` through `BD-010`) have been resolved and incorporated.

The requirements baseline is now locked and ready for technical architecture, database modeling, and API specification.

**Next Document:** System Architecture Document (SAD).