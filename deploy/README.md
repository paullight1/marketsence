# MarketSense production network boundary

MarketSense uses two independent SSRF controls in production:

1. **Application allowlist and DNS validation.** `SCRAPE_ALLOWED_DOMAINS` is mandatory in production. Entries are bare hostnames such as `example.com`; schemes, paths, ports, and wildcard syntax are rejected. Every initial target and HTTP redirect is revalidated, and DNS answers must contain only globally routable addresses.
2. **Infrastructure egress policy.** `deploy/kubernetes/network-policy.yaml` selects MarketSense API/worker pods and denies unrestricted egress. Generic web traffic can use TCP 80/443 only while private, loopback, link-local, metadata and reserved IPv4 blocks are excluded.

The example also permits cluster DNS and MarketSense-labelled in-cluster PostgreSQL/Redis pods. If PostgreSQL, Redis, or a private S3-compatible endpoint is supplied through private VPC addresses instead, add narrowly scoped `ipBlock`/port rules for those exact approved networks; do not remove the private-range exclusions from the generic web rule.

For dual-stack Kubernetes clusters, enforce equivalent IPv6 controls in the CNI/firewall layer (`::1/128`, `fc00::/7`, `fe80::/10`, multicast/reserved ranges) and test them before enabling IPv6 egress. Kubernetes NetworkPolicy behavior for IPv6 `ipBlock` rules is CNI-dependent, so this repository does not claim a portable dual-stack rule.

Browser scraping remains disabled by default. If enabled, every `BROWSER_SCRAPE_ALLOWED_DOMAINS` entry must also fall within `SCRAPE_ALLOWED_DOMAINS`.
