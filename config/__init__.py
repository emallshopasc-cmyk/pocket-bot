# Config paketi

import sys
try:
    import websockets
    if not hasattr(websockets, 'asyncio'):
        import types
        _asyncio_mod = types.ModuleType('asyncio')
        _client_mod = types.ModuleType('client')
        _client_mod.connect = websockets.connect
        _asyncio_mod.client = _client_mod
        websockets.asyncio = _asyncio_mod
        sys.modules['websockets.asyncio'] = _asyncio_mod
        sys.modules['websockets.asyncio.client'] = _client_mod
except Exception:
    pass
