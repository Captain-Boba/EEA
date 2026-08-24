# Europa Overload

`Europa Overload` is an optional visual layer around the analytical Atlas. It is disabled by default and is not required for the map, rankings, time-series comparison, exports, or API.

## Image catalog and network behavior

The canonical local catalog is `web/wallpapers.json`. It contains 250 unique Wikimedia Commons images with stable machine-readable IDs, title, country, Commons filename, author, licence, and dimensions. The browser and server use this same file; array position and the random session order are never used as identities. Automated tests reject duplicate IDs, titles and files, countries outside the Atlas catalog, and invalid dimensions.

No postcard image is requested while the mode is disabled. After the user enables it, the browser derives the Wikimedia Commons image and source URLs from the local catalog and loads the images directly from Wikimedia infrastructure. The Atlas server neither proxies nor stores those image responses.

The enabled state is stored locally under `eea-europa-overload`. Disabling the mode removes its panels, observers, event handlers, and any open image detail view.

## Postcard stream

Postcards alternate along the left and right sides of the document and follow the page's natural scrolling rather than using a fixed parallax layer. The analytical application remains above them and the postcard stream does not change data, map focus, sorting, or comparison selection.

The current desktop implementation still uses capped postcard dimensions. A responsive sizing pass for 1920×1080 and 2560×1440 is an open beta-polish item; the existing implementation must not be described as resolution-adaptive until that visual acceptance has passed.

## Fullscreen gallery

Each available postcard is a mouse- and keyboard-operable control. Selecting it opens a viewport-sized modal detail view with:

- the uncropped image using `object-fit: contain`
- title and country
- author and licence
- a direct Wikimedia Commons source link
- previous and next controls, cyclic arrow-key navigation, and a `position / 250` indicator
- public vote totals, score, rank, and the browser's own current vote
- the local Europe star as the close control

The dialog traps keyboard focus, closes through the star, Escape, or the backdrop, locks background scrolling, and restores the previous scroll position and focus when closed. Reduced-motion preferences disable its transitions.

The gallery uses the same shuffled session order as the postcard stream. It preloads at most the active high-resolution image and its two direct neighbours; stream postcards use a smaller preview. A failed image does not prevent navigating to the next or previous image.

## Public voting and privacy

The thumb controls are public, server-side votes. One anonymous browser may hold one active vote per image: up is `+1`, down is `-1`; clicking the active direction clears it and switching direction replaces it. Old browser-local reactions are deliberately not transferred.

`Score = upvotes − downvotes`. Ranking is descending by score across all 250 catalog entries; equal scores share their rank. An entry displays, for example, `10 👍 · 5 👎 · Score +5 · Platz 18 von 250`.

Votes are kept in a separate SQLite database, default `data/community.sqlite3`, or the path in `EEA_COMMUNITY_DB`. `atlas.sqlite3` remains an exchangeable analytical snapshot and is never changed by voting. The community database enables WAL, a short busy timeout, and one uniqueness rule for `(wallpaper_id, browser_hash)`.

On the first vote the server sets an opaque cookie with `HttpOnly`, `SameSite=Lax`, and `Path=/`; HTTPS deployments additionally receive `Secure`. The database stores only a SHA-256 hash of that cookie value. It does not store IP addresses, browser fingerprints, or User-Agent history. Requests are small JSON bodies, same-origin requests are checked, and a per-browser in-memory rate limit reduces accidental duplicate clicks and simple click spam.

This is deliberately not a tamper-proof election system: users can clear site data or use multiple browsers. It is a lightweight public feedback mechanism without accounts.

## Hosting and recovery

Deploy the community database on a persistent writable volume and set `EEA_COMMUNITY_DB` to that volume's path. Back up `community.sqlite3` together with its WAL sidecars using a SQLite-aware backup or a brief application pause. If the voting API cannot be reached, the image gallery remains usable but voting controls are disabled and display a clear status message.
