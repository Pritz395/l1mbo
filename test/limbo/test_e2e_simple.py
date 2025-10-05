"""Simple E2E test for Limbo server without mounting."""

import asyncio
import tempfile
import json
from pathlib import Path
import subprocess
import time
import sys

import pytest
from fastmcp import Client
from limbo.settings import ConfigManager, ServerConfig, LimboConfig


@pytest.mark.asyncio
@pytest.mark.integration
async def test_e2e_simple():
    """Test Limbo server basic functionality without mounting other servers."""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # 1. Create Limbo config directory
        limbo_dir = tmpdir / "limbo_test"
        limbo_dir.mkdir()
        config_dir = limbo_dir / ".limbo"
        config_dir.mkdir()

        # 2. Create empty config
        config = LimboConfig()
        config_path = config_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump({'servers': {}}, f, indent=2)

        # Create empty auth.json to prevent using default keys
        auth_path = config_dir / "auth.json"
        with open(auth_path, 'w') as f:
            json.dump({
                'bearer': {
                    'issuer': 'https://limbo.local',
                    'audience': 'test',
                    'key_path': str(tmpdir / 'nonexistent')
                }
            }, f)

        print(f"Config saved to: {config_path}")

        # 3. Start Limbo server as subprocess
        limbo_script = limbo_dir / "run_limbo.py"
        limbo_script.write_text(f'''
import sys
import os
sys.path.insert(0, "{Path.cwd()}")
os.chdir("{limbo_dir}")

from limbo.server.server import LimboServer
import asyncio

async def main():
    server = LimboServer("{config_path}")
    await server.setup()
    print("Limbo server started", flush=True)
    await server.mcp.run_http_async(host="localhost", port=54322)

asyncio.run(main())
''')

        # Start Limbo
        print("Starting Limbo server...")
        limbo_proc = subprocess.Popen(
            [sys.executable, str(limbo_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait for startup
        started = False
        for i in range(10):  # Try for up to 10 seconds
            if limbo_proc.poll() is not None:
                # Process ended
                stdout, stderr = limbo_proc.communicate()
                print(f"Limbo process ended with code {limbo_proc.returncode}")
                print(f"STDOUT:\n{stdout}")
                print(f"STDERR:\n{stderr}")
                pytest.fail(f"Limbo server failed to start: {stderr}")

            # Check if server is listening on the port
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 54322))
            sock.close()

            if result == 0:
                print("Server is listening on port 54322")
                started = True
                break

            time.sleep(1)

        if not started:
            pytest.fail("Limbo server didn't start listening on port 54322")

        try:
            # 4. Connect to Limbo as client
            print("\nConnecting to Limbo...")
            client = Client("http://localhost:54322/mcp/")

            # Use the client in async context
            async with client:
                tools = await client.list_tools()
                tool_names = [tool.name for tool in tools]
                print(f"\nAvailable tools: {tool_names}")

                # Verify Limbo's own tools are available
                assert "limbo_list_servers" in tool_names
                assert "limbo_add_server" in tool_names

                # Test listing servers (should be empty)
                result = await client.call_tool("limbo_list_servers", {})
                print(f"\nResult: {result}")

                # Parse the JSON response
                if hasattr(result, 'content') and result.content:
                    response_text = result.content[0].text
                else:
                    response_text = "{}"
                servers_data = json.loads(response_text)
                print(f"Parsed servers data: {servers_data}")

                assert servers_data["output"] == []

                print("\n✅ All tests passed!")

        finally:
            # Cleanup
            limbo_proc.terminate()
            limbo_proc.wait()


if __name__ == "__main__":
    asyncio.run(test_e2e_simple())
