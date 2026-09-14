# Hive Coder Foundations

Hive Coder keeps Open Interpreter and Cua Driver outside the product source tree and integrates them behind Hive-owned adapters. `foundations.lock.json` freezes upstream identity and approved Windows x64 artifact metadata.

## Locked foundations

- Open Interpreter `0.0.43`, tag `rust-v0.0.43`, ACP over stdio as the primary boundary.
- Cua Driver `0.28.1`, tag `cua-driver-rs-v0.28.1`, MCP / JSON-RPC 2.0 over stdio as the primary boundary.

Full upstream repositories and binaries are not vendored by this increment. `--inventory-only` performs no external process execution. Normal doctor mode may execute only each discovered binary's pinned version command; it never downloads, installs, elevates privileges, clicks, types, or invokes computer-control tools.

```bash
python tools/foundations/verify_lock.py
python tools/foundations/doctor.py --inventory-only
python -m unittest discover -s tests -p "test_*.py"
```
