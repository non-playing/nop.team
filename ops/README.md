# Matrix public ingress (not deployed)

This repository is a static document root (`index.html`, `assets/`), not the
HostCreators vhost or webhook configuration. On 2026-10-02 both public
`https://nop.team/.well-known/matrix/client` and
`https://matrix.nop.team/_matrix/client/versions` returned 404. Responses had
`Server: nginx`; the 404 body looked Apache-generated, but that does **not**
prove `.htaccess` is enabled or that nginx will serve these new files. There
is no Traefik, Caddy, nginx or Apache configuration in this repository.

## Files in this branch

- `.well-known/matrix/client`: client discovery for Matrix IDs ending in
  `:nop.team`, pointing clients to `https://matrix.nop.team`.
- `.well-known/matrix/server`: federation delegation to `matrix.nop.team:443`.
  **Do not publish this file until public federation on that hostname works.**
- `.well-known/matrix/.htaccess`: best-effort Apache MIME and CORS headers for
  both extensionless JSON files; ignored when nginx directly serves them, or
  when the host disables Apache overrides. The HostCreators operator must
  ensure `Content-Type: application/json` and `Access-Control-Allow-Origin: *`
  on the client discovery response (and JSON MIME on server discovery).
- `ops/matrix.nop.team.nginx.example`: an **uninstalled** nginx `location`
  template for the HTTPS matrix subdomain, not part of the site's routing.
  It must be installed in the *hosting vhost configuration*, not the static
  document root. It proxies all paths, including `/_matrix`, `/_tuwunel`,
  `/.well-known/openid-configuration`, and the OIDC callback. Preserve the
  public Host and HTTPS forwarded scheme. If the real upstream is HTTPS,
  nginx must validate its certificate (supply a CA bundle if necessary).

## Dependency before any push/merge

A push may trigger a webhook that immediately copies **all** tracked files
(including hidden directories and the federation file) to the live document
root. We have not inspected the webhook, its target, hidden-file handling or
its deployment timing. Do not push this branch, merge it, or manually copy it
until the deploy behavior and the following ingress path are confirmed.
Even publishing only the client file before ingress works advertises an
unreachable homeserver; publishing the server file prematurely breaks
federation discovery for `nop.team`.

The Matrix Compose deployment on greninja binds Tuwunel to
`127.0.0.1:8008` **on greninja**, not HostCreators. Greninja public 80/443
are already used by NetBird; the public DNS for both names terminates at
HostCreators. A HostCreators-local `127.0.0.1` is a different machine and
will not reach greninja. Arrange an approved, authenticated and durable path
from the HostCreators proxy to Tuwunel (e.g. a tunnel terminating on the
hosting machine with forwarding to greninja's local listener, or another
operator-approved private route). Establish its **actual** scheme, address,
port, TLS trust, access controls and availability; no backend address or port
is supplied by this repository. On shared hosting, ask HostCreators whether
vhost-level nginx reverse proxy configuration and tunnel endpoints are
allowed; a user `.htaccess` cannot configure an nginx reverse proxy. The
hosting operator must install the snippet with the actual upstream URL,
configure HTTPS for `matrix.nop.team`, and ensure `nop.team` serves the
well-known files from the webhook's document root. Do not redirect the
`nop.team` well-known URLs to `matrix.nop.team`; serve them at the apex.

## Verification gate

Before publishing delegation, check from **outside** the private network:

```sh
curl -i https://matrix.nop.team/_matrix/client/versions
curl -i https://matrix.nop.team/_matrix/client/v3/login
curl -i https://matrix.nop.team/.well-known/openid-configuration
curl -i https://nop.team/.well-known/matrix/client
curl -i https://nop.team/.well-known/matrix/server
```

Require HTTPS 200 and valid Matrix/JSON output where appropriate, no 404 or
proxy error, the correct `m.homeserver.base_url` and `m.server`, JSON MIME,
and CORS on the client discovery endpoint. Test federation against
`matrix.nop.team:443` from outside, including TLS certificate and an
`/_matrix/federation/v1/version` request, **before** making server delegation
public. Verify OIDC callback in a real Pocket ID login afterwards; a local
nginx syntax test is not a public ingress or SSO test. Compare the webhook's
actual deployed tree to this branch before claiming deployment.
