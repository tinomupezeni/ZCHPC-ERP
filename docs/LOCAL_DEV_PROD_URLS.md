## Local Development and Production API URLs

The frontend uses different API base URLs depending on the environment.

### Local Development

For local development, the frontend should communicate with the locally running Django backend:

```text
Frontend: http://localhost:8080
Backend:  http://127.0.0.1:8000
API:      http://127.0.0.1:8000/api/v2/
````

The local API URL is documented in `.env.example`:

```env
VITE_API_URL=http://localhost:8000
```

When running the frontend locally, developers should ensure that
`VITE_API_URL` is set to the local backend URL.

After changing the environment variable, restart the Vite development
server so that the updated configuration is loaded.

### Production

Production uses the deployed backend:

```text
API: https://zchpcerp.zchpc.ac.zw/api/v2/
```

The production frontend configuration is defined separately from local
development configuration.

The production API URL must not be copied into a local development
environment unless there is an explicit reason to test against the
deployed backend.

### Verifying the Active API URL

When troubleshooting authentication or API requests, verify the
**Request URL** in the browser's Developer Tools:

1. Open Developer Tools.
2. Select the **Network** tab.
3. Perform the API operation, such as logging in.
4. Locate the request to `/auth/token/`.
5. Check the **Request URL**.

For local development, the request should resolve to:

```text
http://127.0.0.1:8000/api/v2/auth/token/
```

or the configured local backend address.

For production, it should resolve to:

```text
https://zchpcerp.zchpc.ac.zw/api/v2/auth/token/
```

If a local frontend unexpectedly sends requests to the production
backend, check the frontend environment configuration and restart the
Vite development server after making changes.

### Important

Do not commit local `.env` files containing environment-specific
configuration or secrets. Use `.env.example` to document the expected
configuration without exposing sensitive values.

