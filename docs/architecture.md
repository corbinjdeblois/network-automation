# Architecture

## Project Overview

The Network Automation Platform is a modular system designed
to automate network operations, provide visibility into
infrastructure, and reduce manual administrative effort.

The platform is being developed in phases.

Phase 1 establishes the foundational Device Connectivity Layer.

---

## Phase 1 Architecture

+----------------------------+
| Supported Network Devices  |
+-------------+--------------+
              |
              | SSH/API
              |
              v
+----------------------------+
| Device Connectivity Layer  |
+-------------+--------------+
              |
              |
              v
+----------------------------+
| Standardized JSON Output   |
+----------------------------+

---

## Components

### Network Devices

Supported infrastructure vendors.

Initial target:

- Cisco
- Ubiquiti

Future support:

- Juniper
- Aruba
- Fortinet

---

### Device Connectivity Layer

Responsibilities:

- Authentication
- Session Establishment
- Command Execution
- Data Collection
- Error Handling

Restrictions:

- Read-only operations only
- No configuration changes

---

### Output Layer

Raw vendor-specific data is normalized into
a common structure.

Example:

```json
{
  "hostname": "SW01",
  "vendor": "Cisco",
  "version": "17.9.4"
}