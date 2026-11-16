# Product Vision & Scope
## Restaurant & Café Management System

**Document ID:** PRD-FOUNDATION-001  
**Version:** 1.0.0  
**Status:** Approved — Product Foundation  
**Project Type:** Personal Software Project  
**Product Model:** SaaS Multi-Tenant  
**Target Industry:** Restaurant & Café  
**Target Market:** Micro and Small Businesses  

---

# 1. Product Overview

Restaurant & Café Management System is a multi-tenant SaaS platform designed to help restaurant and café businesses manage their daily operations through an integrated digital system.

The platform connects essential business processes, including business management, menu management, table management, ordering, point of sale, kitchen operations, inventory, purchasing, and business reporting.

The system supports businesses operating from a single outlet or multiple outlets, with centralized business management and controlled access for employees.

The product is intended to serve both independent restaurants and cafés.

# 2. Product Vision

To build an integrated restaurant and café management platform that simplifies daily operations, connects business workflows, and provides business owners with reliable operational and financial insights.

### Product Mission

To provide restaurant and café businesses with a practical digital platform that reduces manual operational work, improves business visibility, and maintains consistent information across their business activities.

### Core Product Principles

1. **Operational Integration**

   All core modules must work together through consistent business data and workflows.

2. **Data Reliability**

   Business reports must be derived from recorded transactions and operational activities.

3. **Role-Based Experience**

   Users should access only the features and information relevant to their responsibilities.

4. **Multi-Tenant Isolation**

   Each business must have independent data and configuration.

5. **Multi-Outlet Support**

   Businesses must be able to manage multiple outlets without duplicating their entire business setup.

6. **Scalable Product Architecture**

   The system should support future business growth and additional operational capabilities.

# 3. Target Users

The primary target market consists of micro and small restaurant and café businesses.

### Business Profiles

- Independent restaurants.
- Independent cafés and coffee shops.
- Small restaurant groups.
- Café businesses operating multiple outlets.
- Food and beverage businesses with dine-in, takeaway, or both.

### System User Roles

| Role | Primary Responsibility |
|---|---|
| Business Owner | Business configuration and overall performance |
| Business Manager | Outlet operations and employee supervision |
| Cashier | Orders, checkout, and payment processing |
| Waiter | Table and customer order management |
| Kitchen Staff | Food and beverage preparation |
| Inventory Staff | Stock monitoring and inventory operations |
| Purchasing Staff | Supplier and procurement operations |

A single employee may have multiple permissions or responsibilities depending on business configuration.

The authorization model must support role-based permissions and outlet-level access restrictions.

# 4. Business Model and Organizational Structure

## 4.1 SaaS Multi-Tenant Model

The platform serves multiple independent businesses.

Each registered business represents an independent tenant.

A tenant owns its:

- Business profile.
- Outlets.
- Employees and access permissions.
- Menus and products.
- Inventory records.
- Orders and transactions.
- Suppliers and purchasing records.
- Operational reports.

Data belonging to one tenant must never be accessible to another tenant without explicit authorization.

## 4.2 Multi-Outlet Structure

A business may operate one or more outlets.

Organizational structure:

Platform
- Business A
  - Outlet A1
  - Outlet A2
  - Outlet A3
- Business B
  - Outlet B1
  - Outlet B2
- Business C
  - Outlet C1

Each outlet may have its own:

- Tables and seating configuration.
- Employees and assigned permissions.
- Inventory and stock movements.
- Orders and transactions.
- Operational activities.

Business-level settings and shared master data must be designed to support centralized management.

## 4.3 Platform Support

The product targets three usage environments:

1. **Web Application:** business owners and managers, including centralized administration and reporting.
2. **Tablet Interface:** cashier, waiter, and kitchen workflows.
3. **Native Mobile Application:** operational access for employees and business owners.

The initial technical implementation may be delivered in phases, but multi-platform support remains part of the product vision.

# 5. Product Scope

The system is organized into eight primary functional domains.

## 5.1 Business and Access Management

Responsibilities:

- Business registration and configuration.
- Outlet management.
- Employee management.
- Role and permission management.
- User-to-outlet assignment.
- Authentication and session management.

## 5.2 Menu Management

Responsibilities:

- Menu categories.
- Products and menu items.
- Product variants.
- Add-ons and toppings.
- Pricing configuration.
- Product availability.
- Recipe definitions and ingredients.

## 5.3 Table and Order Management

Responsibilities:

- Table management.
- Table status.
- Dine-in orders.
- Takeaway orders.
- Order modifications.
- Order cancellation.
- Order status tracking.

## 5.4 Point of Sale

Responsibilities:

- Checkout processing.
- Payment recording.
- Multiple payment methods.
- Discounts.
- Taxes and service charges.
- Split bills.
- Refund and void handling with appropriate permissions.
- Cashier shift management.

## 5.5 Kitchen Operations

Responsibilities:

- Kitchen order receiving.
- Preparation queues.
- Order prioritization.
- Item preparation status.
- Completed order notification.
- Preparation time monitoring.

## 5.6 Inventory Management

Responsibilities:

- Raw material management.
- Units of measurement.
- Stock receiving.
- Stock movements.
- Recipe-based ingredient consumption.
- Stock adjustments.
- Waste recording.
- Stock opname.
- Inventory reporting.

## 5.7 Purchasing Management

Responsibilities:

- Supplier management.
- Purchase orders.
- Goods receiving.
- Purchase records.
- Purchase cost history.
- Purchasing status tracking.

## 5.8 Reports and Analytics

Responsibilities:

- Sales reports.
- Transaction reports.
- Menu performance.
- Inventory reports.
- Food cost reports.
- Waste reports.
- Outlet performance.
- Business-level performance summaries.

# 6. MVP Definition

The MVP must demonstrate one complete and reliable restaurant or café operational workflow.

The objective is not to implement every possible restaurant feature. The objective is to establish a working integrated system.

## 6.1 MVP Functional Scope

### A. Business Foundation

- Tenant registration and business configuration.
- Outlet creation and management.
- User management.
- Authentication.
- Role-based access control.
- Outlet-level access control.

### B. Menu Foundation

- Menu category management.
- Product management.
- Product variants.
- Add-on configuration.
- Recipe and ingredient definitions.
- Product pricing.

### C. Ordering

- Table management.
- Dine-in ordering.
- Takeaway ordering.
- Order item management.
- Order status management.
- Order cancellation with authorization.

### D. Point of Sale

- Checkout.
- Cash payments.
- Non-cash payment recording.
- Split payment.
- Discount handling.
- Tax and service charge calculation.
- Receipt generation.

Actual payment gateway integration is not required for the initial MVP. External payment transactions may be recorded manually.

### E. Kitchen

- Kitchen order queue.
- Order item preparation status.
- Preparation completion.
- Order completion tracking.

### F. Inventory

- Ingredient master data.
- Stock receiving.
- Recipe-based stock deduction.
- Stock movement history.
- Manual stock adjustment.
- Waste recording.
- Basic stock monitoring.

### G. Purchasing

- Supplier management.
- Basic purchase order creation.
- Goods receiving.
- Inventory updates after receiving.

### H. Reporting

- Daily sales report.
- Order report.
- Payment report.
- Best-selling menu report.
- Basic ingredient stock report.
- Basic food cost report.

## 6.2 MVP Business Workflow

The MVP must support the following end-to-end workflow:

1. A business owner registers a business.
2. The owner creates one or more outlets.
3. The owner configures employees and permissions.
4. The manager creates menu categories and menu items.
5. Recipes and ingredient requirements are configured.
6. Inventory staff records incoming ingredients.
7. A waiter creates a customer order.
8. The order is sent to the kitchen.
9. Kitchen staff prepares and completes the order.
10. The cashier processes checkout and payment.
11. The system records the completed transaction.
12. Ingredient consumption is reflected in inventory.
13. The owner or manager reviews business reports.

The system must preserve data consistency throughout this workflow.

## 6.3 MVP Non-Functional Requirements

- Secure authentication and authorization.
- Strict tenant data isolation.
- Outlet-level access restrictions.
- Consistent database transactions.
- Input validation.
- Structured application logging.
- Centralized error handling.
- API documentation.
- Automated testing.
- Database migration management.
- Containerized deployment.
- Health monitoring.
- Graceful application shutdown.

# 7. Post-MVP Scope

The following capabilities are reserved for subsequent development phases.

- Advanced reservation management.
- Customer loyalty programs.
- Customer relationship management.
- Online ordering portal.
- Delivery platform integrations.
- QR-code ordering.
- Payment gateway integrations.
- Advanced multi-outlet inventory transfers.
- Advanced financial accounting.
- Employee attendance and payroll.
- Advanced analytics.
- Sales forecasting.
- Native mobile application expansion.
- Offline-first operation and synchronization.

Native mobile support remains a product requirement. The exact MVP rollout and mobile technology will be decided during technical planning.

# 8. Out of Scope

The following are explicitly excluded from the initial product direction:

- Full enterprise ERP.
- Manufacturing management for food factories.
- General-purpose accounting software.
- Payroll and human resources management.
- Marketplace development.
- Food delivery fleet management.
- Hardware manufacturing.
- IoT device management.

These exclusions help maintain a clear product identity and manageable implementation scope.

# 9. Business Assumptions

The initial product discovery is based on the following assumptions.

1. Restaurants and cafés need connected operational workflows.
2. Business owners need visibility into sales, inventory, and operating performance.
3. Businesses may operate one or multiple outlets.
4. Different employees require different permissions.
5. Menu recipes can be used to estimate ingredient consumption.
6. Stock movements must be traceable.
7. Completed sales transactions should be linked to operational and financial reports.
8. Businesses may use different payment methods.
9. The system must accommodate both dine-in and takeaway operations.
10. Businesses may have different menu configurations and operational procedures.

These assumptions must be validated during development and testing.

# 10. Product Success Criteria

The MVP will be considered functionally successful when:

1. Multiple businesses can use the same platform independently.
2. Tenant data cannot be accessed across unauthorized business boundaries.
3. A business can operate multiple outlets.
4. Users can be assigned different roles and permissions.
5. A customer order can move through the complete ordering and kitchen workflow.
6. Orders can be checked out and paid successfully.
7. Completed transactions are recorded accurately.
8. Inventory consumption is recorded consistently.
9. Managers can retrieve basic operational reports.
10. Critical business workflows have automated test coverage.

# 11. Technical Direction

The technology stack has been selected.

| Layer | Technology |
|---|---|
| Backend | Python |
| Backend Framework | FastAPI |
| Database | PostgreSQL |
| Frontend Web | Next.js |
| Frontend Language | TypeScript |
| Deployment | Docker |
| Automated Testing | Pytest |
| CI/CD | GitHub Actions |
| Source Control | GitHub |

Detailed architectural decisions, database design, API contracts, and mobile implementation technologies will be documented separately.

# 12. Project Development Principles

The project will be developed incrementally.

- Product requirements must be documented before implementation.
- Each functional module must have clearly defined responsibilities.
- Business rules must be documented and tested.
- Database changes must use version-controlled migrations.
- API contracts must be consistent.
- Reusable functionality must be centralized.
- Avoid unnecessary abstraction and premature optimization.
- Every important workflow must have automated tests.
- Implementation changes must be reviewed before acceptance.
- AI coding assistant outputs must be evaluated rather than accepted automatically.

# 13. Assessment Considerations

This project is intended to serve as a personally owned software development project and a practical environment for evaluating AI coding assistants.

The development process should preserve:

- Git commit history.
- Documented requirements.
- Implementation plans.
- Test results.
- Code review decisions.
- AI coding assistant comparison notes.
- Technical decisions and their rationale.

No employer-owned source code, confidential information, credentials, or personal data should be included in the project or AI coding sessions.

# 14. Current Project Status

| Item | Status |
|---|---|
| Product vision | Approved |
| Product model | SaaS Multi-Tenant |
| Organizational model | Multi-Outlet |
| Platform direction | Web, Tablet, Native Mobile |
| Target industry | Restaurant and Café |
| Product scope | Approved |
| MVP scope | Approved as initial baseline |
| Business assumptions | Documented, pending validation |
| Database architecture | Not started |
| API architecture | Not started |
| UI/UX specification | Not started |
| Implementation | Not started |

---

**Document Status:** Approved — Foundation Baseline 1.0.0

**Next Document:** Product Requirements Document (PRD)

**Next Development Step:** Detailed functional requirements and business workflow specification.