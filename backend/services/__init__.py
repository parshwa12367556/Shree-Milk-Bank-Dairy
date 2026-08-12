"""
Smart Dairy ERP — Service Layer
===============================
Reusable business logic shared across role modules. The Flask route
handlers stay thin; the source-of-truth business rules (pricing, ledger,
payment finalization) live here so ADMIN / BRANCH_OPERATOR / FARMER
modules never duplicate them.
"""
