"""End-to-end test for Limbo server mounting."""

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
async def test_e2e_mounting():
    """Test Limbo with real server mounting end-to-end."""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # 1. Create a simple test MCP server
        calc_dir = tmpdir / "calculator_server"
        calc_dir.mkdir()

        calc_server = calc_dir / "server.py"
        calc_server.write_text('''
from fastmcp import FastMCP

mcp = FastMCP("calculator")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@mcp.tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

if __name__ == "__main__":
    mcp.run()
''')

        # 2. Create Limbo config
        limbo_dir = tmpdir / "limbo_test"
        limbo_dir.mkdir()
        config_dir = limbo_dir / ".limbo"
        config_dir.mkdir()

        config = LimboConfig()

        # Add calculator server (no sources anymore)
        server = ServerConfig(
            name="calc",
            source=f"file://{calc_dir}",
            prefix="calc",  # Explicit prefix
            command="python",
            args=["server.py"],
            cwd=str(calc_dir)
        )
        config.add_server(server)

        # Save config
        config_path = config_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump({
                'servers': {s.name: s.model_dump(mode="json") for s in config.servers.values()}
            }, f, indent=2)

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
    await server.mcp.run_http_async(host="localhost", port=54321)

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

        # Wait for startup and check if process started
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
            result = sock.connect_ex(('localhost', 54321))
            sock.close()

            if result == 0:
                print("Server is listening on port 54321")
                started = True
                break

            time.sleep(1)

        if not started:
            # Get any output so far
            stdout, stderr = limbo_proc.communicate(timeout=1)
            print(f"Server didn't start in time. STDOUT:\n{stdout}")
            print(f"STDERR:\n{stderr}")
            pytest.fail("Limbo server didn't start listening on port 54321")

        try:
            # 4. Connect to Limbo as client
            print("\nConnecting to Limbo...")
            client = Client("http://localhost:54321/mcp/")

            # Use the client in async context
            async with client:
                tools = await client.list_tools()
                tool_names = [tool.name for tool in tools]
                print(f"\nAvailable tools: {tool_names}")

                # Verify calculator tools are mounted with prefix
                assert "calc_add" in tool_names
                assert "calc_multiply" in tool_names

                # Test calling a mounted tool
                result = await client.call_tool("calc_add", {"a": 5, "b": 3})
                print(f"\ncalc_add(5, 3) = {result}")
                # Parse the result - calculator returns CallToolResult
                if hasattr(result, 'content') and result.content:
                    result_text = result.content[0].text
                    assert result_text == "8"
                else:
                    assert False, f"Unexpected result format: {result}"

                result = await client.call_tool("calc_multiply", {"a": 4, "b": 7})
                print(f"calc_multiply(4, 7) = {result}")
                if hasattr(result, 'content') and result.content:
                    result_text = result.content[0].text
                    assert result_text == "28"
                else:
                    assert False, f"Unexpected result format: {result}"

                # Test Limbo's own tools
                assert "limbo_list_servers" in tool_names
                servers_result = await client.call_tool("limbo_list_servers", {})
                print(f"\nServers: {servers_result}")
                if isinstance(servers_result, list) and servers_result:
                    servers_text = servers_result[0].text
                    servers_data = json.loads(servers_text)
                    print(f"Servers data: {servers_data}")
                    assert len(servers_data["output"]) == 1
                    assert servers_data["output"][0]["name"] == "calc"

                print("\n✅ All tests passed!")

        finally:
            # Cleanup
            limbo_proc.terminate()
            limbo_proc.wait()


if __name__ == "__main__":
    asyncio.run(test_e2e_mounting())
