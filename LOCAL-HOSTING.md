# Show the Northstowe map to other people

The production app runs on this computer. Cloudflare Tunnel can give it an HTTPS link that works from elsewhere, including mobile data. No router configuration or Cloudflare account is needed for this temporary demonstration link.

## Start and share

Open PowerShell in this folder and run:

```powershell
.\Start-Northstowe.ps1 -Share
```

The script prints the local address and the external link. The external link is also saved in `.local-runtime/share-url.txt`. Copy that link into an invitation or open it on another device. Starting again while the recorded tunnel is running returns the same link.

Local address: **http://localhost:4173/**. This address only works on this computer. The HTTPS sharing link works from other networks. Starting without `-Share` starts only the local app; it does not stop an already running tunnel.

Keep the computer awake, powered on and connected to the internet while showing the map. After sharing is stopped/restarted, the temporary URL changes. This is a demonstration setup; a permanent address and reliable unattended hosting can be arranged separately. Quick Tunnels have no uptime guarantee and a 200-concurrent-request limit. [Cloudflare Quick Tunnel documentation](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/).

## Stop

```powershell
.\Stop-Northstowe.ps1
```

This stops only the recorded map server and tunnel after checking their process identity. It does not stop other local websites.

## Update after editing

With Node.js 22.13+ and pnpm available:

```powershell
.\Stop-Northstowe.ps1
pnpm run test:map
pnpm exec tsc --noEmit
pnpm run local:build
.\Start-Northstowe.ps1 -Share
```

The independent Vite build uses the same React map and public data as the Sites version. `pnpm run build` remains the separate Sites build. The public app serves only `local-dist/`; source code, research downloads and the private `email-drafts/` review pack are outside that directory. No email-sending facility is included. Anyone who has the external link can read the map and its public-source data.

Cloudflare Tunnel 2026.9.1 is downloaded from the [official release](https://github.com/cloudflare/cloudflared/releases/tag/2026.9.1) into `.local-runtime/` and checked against its published SHA-256. It is not installed as a Windows service. Logs and process records stay in that ignored directory. Leaflet requests the basemap from OpenStreetMap; an internet connection is required for basemap tiles.

The source snapshot is dated 12 September 2026. Older maintenance evidence remains explicitly labelled in the map. The parish boundary is complete, but exact ownership, handovers and bin contracts are still being confirmed.
