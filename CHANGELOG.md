# Changelog

## V2.2.1 Data Pipeline Stable

- Established modular reader, field detector, data model and exporter.
- Export is byte-for-byte pass-through in this validation stage.
- Added detection of image URL columns by name and cell content.
- Added diagnostics for embedded Excel image objects.
- Preserved the V1.3.2 image pipeline as a frozen, disconnected module.
- No AI or image optimization is executed in this version.
