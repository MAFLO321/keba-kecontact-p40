# keba-kecontact-p40

Async Python client for the KEBA P40 / P40 Pro wallbox **local** REST API (v3.0.3).

> The P40 exposes a self-signed HTTPS endpoint on port 8443 with JWT auth.
> Pass an `aiohttp.ClientSession` configured to skip certificate verification.

```python
import aiohttp
from keba_kecontact_p40 import KebaP40Client

async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
    client = KebaP40Client("192.168.1.50", "my-password", session=session)
    await client.login()
    wallboxes = await client.get_wallboxes()
    print(wallboxes[0].serial_number, wallboxes[0].state)
```
