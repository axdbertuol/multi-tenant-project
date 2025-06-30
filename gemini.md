This is a multi-tenant system built with Domain-Driven Design (DDD) principles. It appears to be a FastAPI application.

The project is divided into four main **Bounded Contexts**:

1.  **User**: Manages users, authentication (JWT), and sessions.
2.  **Organization**: Handles organizations, members, and multi-tenant configurations.
3.  **Authorization**: Implements a hybrid Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC) system for fine-grained permissions.
4.  **Plans**: Manages customizable subscription plans and resources (like different chat types).

Each of these contexts is structured into the following layers, typical of DDD:

*   **Domain**: Contains the core business logic, including entities, value objects, and domain services.
*   **Application**: Orchestrates the domain logic with use cases and Data Transfer Objects (DTOs).
*   **Infrastructure**: Handles technical concerns like database interactions (using SQLAlchemy), repositories, and unit of work patterns.
*   **Presentation**: Exposes the functionality via a FastAPI-based RESTful API.

Key features of the system include:

*   **Multi-tenancy**: Data is isolated by `organization_id`.
*   **Hybrid Authorization**: Combines roles and dynamic policies for flexible access control.
*   **Customizable Plans**: Organizations can subscribe to different plans that unlock various features and resources.
*   **Clean Architecture**: The separation of concerns into layers and bounded contexts makes the system modular and maintainable.
