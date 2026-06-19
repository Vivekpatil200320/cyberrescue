# CyberRescue

A locally-hosted MCP server that gives Claude real tools to debug Docker containers.

Full documentation (installation, usage, demo) is written in Phase 6.

## Future Enhancements

- Standalone binary packaging (PyInstaller/Nuitka) for zero-Python-install distribution
- Streaming log reads for very large logs (currently buffers full log before truncating)
- Optional SQLite audit log for compliance use cases
