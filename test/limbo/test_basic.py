"""Basic functionality tests for Limbo using pytest."""

import pytest
from fastmcp import Client
from limbo.server.server import LimboServer
import tempfile
from pathlib import Path


class TestLimboBasicFunctionality:
    """Test basic Limbo functionality."""

    @pytest.mark.asyncio
    async def test_basic_setup_and_tools(self, tmp_path):
        """Test Limbo setup and tool availability."""
        config_path = tmp_path / "config.json"
        server = LimboServer(config_path, enable_config_reload=False)

        async with server:
            expected_tools = ["limbo_list_servers", "limbo_add_server", "limbo_status", "limbo_check"]

            async with Client(server.mcp) as client:
                tools = await client.list_tools()
                tool_names = [tool.name for tool in tools]

                for tool in expected_tools:
                    assert tool in tool_names

    # list_tools was removed from the server
    # @pytest.mark.asyncio
    # async def test_limbo_list_tools(self):
    #     """Test Limbo list tools functionality."""
    #     server = LimboServer()
    #     await server.setup()
    #
    #     async with Client(server.mcp) as client:
    #         result = await client.call_tool("limbo_list_tools", {})
    #         assert len(result) > 0
    #         assert hasattr(result[0], 'text')
    #         assert isinstance(result[0].text, str)

    @pytest.mark.asyncio
    async def test_list_servers(self, tmp_path):
        """Test listing servers."""
        config_path = tmp_path / "config.json"
        server = LimboServer(config_path, enable_config_reload=False)

        async with server:
            async with Client(server.mcp) as client:
                result = await client.call_tool("limbo_list_servers", {})
                assert hasattr(result, 'content')
                assert len(result.content) > 0
                assert hasattr(result.content[0], 'text')
                assert isinstance(result.content[0].text, str)


class TestLimboServerManagement:
    """Test server management functionality."""

    @pytest.mark.asyncio
    async def test_add_server(self, tmp_path):
        """Test adding a server."""
        config_path = tmp_path / "config.json"
        server = LimboServer(config_path, enable_config_reload=False)

        import time
        unique_id = str(int(time.time()))

        async with server:
            async with Client(server.mcp) as client:
                server_name = f"testserver{unique_id}"
                result = await client.call_tool("limbo_add_server", {
                    "name": server_name,
                    "source": f"https://github.com/example/test-{unique_id}",
                    "prefix": "test",
                    "command": "echo test",
                    "enable": False  # Don't try to mount it
                })

                assert hasattr(result, 'content')
                assert len(result.content) > 0
                assert hasattr(result.content[0], 'text')

                list_result = await client.call_tool("limbo_list_servers", {})
                assert hasattr(list_result, 'content')
                assert len(list_result.content) > 0
                assert hasattr(list_result.content[0], 'text')
                assert server_name in list_result.content[0].text


class TestLimboServerSearch:
    """Test server search functionality."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_search_servers(self, tmp_path):
        """Test server search (requires internet)."""
        config_path = tmp_path / "config.json"
        server = LimboServer(config_path, enable_config_reload=False)

        async with server:
            async with Client(server.mcp) as client:
                try:
                    result = await client.call_tool("limbo_search_servers", {
                        "query": "filesystem",
                        "limit": 3
                    })
                    assert hasattr(result, 'content')
                    assert len(result.content) > 0
                    assert hasattr(result.content[0], 'text')
                except Exception as e:
                    pytest.skip(f"Search test failed (requires internet): {e}")
