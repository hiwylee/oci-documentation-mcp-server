cd /home/opc/mcpo
#uvx mcpo --port 8090 --api-key 'top-secret'   -- /home/opc/oci-documentation-mcp-server/.venv/bin/python /home/opc/oci-documentation-mcp-server/oci_documentation_mcp_server/server.py
uvx mcpo --port 8090 --api-key top-secret \
  -- /home/opc/oci-documentation-mcp-server/.venv/bin/python \
     /home/opc/oci-documentation-mcp-server/oci_documentation_mcp_server/server.py

