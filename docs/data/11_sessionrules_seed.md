# SessionRules Seed (MVP)

## Goal
Provide minimal but explicit close-time rules for venues in the MVP universe.

---

## Initial rules (indicative)

### XNYS
- timezone_local: America/New_York
- regular_close_local: 16:00

### XNAS
- timezone_local: America/New_York
- regular_close_local: 16:00

### XLON
- timezone_local: Europe/London
- regular_close_local: 16:30

### XPAR
- timezone_local: Europe/Paris
- regular_close_local: 17:30

### XETR
- timezone_local: Europe/Berlin
- regular_close_local: 17:30

### XTKS
- timezone_local: Asia/Tokyo
- regular_close_local: 15:00

---

## Notes
- Early closes ignored in MVP; calendar conflicts will be flagged.
- Rules stored as versioned YAML with hash recorded in registry.
