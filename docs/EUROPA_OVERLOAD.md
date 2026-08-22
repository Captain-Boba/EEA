# Europa Overload

`Europa Overload` is an optional visual layer around the analytical Atlas. It is disabled by default and is not required for the map, rankings, time-series comparison, exports, or API.

## Image catalog and network behavior

The local manifest in `web/wallpapers.js` contains 250 unique Wikimedia Commons images. Every entry records a title, one or more of the 31 Atlas countries, the Commons filename, author, and licence. Automated tests reject duplicate titles and files, countries outside the Atlas catalog, and explicitly removed images.

No postcard image is requested while the mode is disabled. After the user enables it, the browser derives the Wikimedia Commons image and source URLs from the local manifest and loads the images directly from Wikimedia infrastructure. The Atlas server neither proxies nor stores those image responses.

The enabled state is stored locally under `eea-europa-overload`. Disabling the mode removes its panels, observers, event handlers, and any open image detail view.

## Postcard stream

Postcards alternate along the left and right sides of the document and follow the page's natural scrolling rather than using a fixed parallax layer. The analytical application remains above them and the postcard stream does not change data, map focus, sorting, or comparison selection.

The current desktop implementation still uses capped postcard dimensions. A responsive sizing pass for 1920×1080 and 2560×1440 is an open beta-polish item; the existing implementation must not be described as resolution-adaptive until that visual acceptance has passed.

## Fullscreen detail view

Each available postcard is a mouse- and keyboard-operable control. Selecting it opens a viewport-sized modal detail view with:

- the uncropped image using `object-fit: contain`
- title and country
- author and licence
- a direct Wikimedia Commons source link
- private Like and Dislike controls
- the local Europe star as the close control

The dialog traps keyboard focus, closes through the star, Escape, or the backdrop, locks background scrolling, and restores the previous scroll position and focus when closed. Reduced-motion preferences disable its transitions.

Images that fail to load are not opened as functioning postcards.

## Local reactions and privacy

Like and Dislike are mutually exclusive per image and can be cleared by selecting the active reaction again. They are stored as a small JSON object in browser `localStorage` under `eea-europa-overload-reactions`.

These reactions:

- are not public votes
- do not display aggregate counts
- are not transmitted to the Atlas server
- do not require an account
- may disappear when the browser's site data is cleared

Storage failures in restricted browsing modes are ignored so that the Atlas and the image detail view remain usable.
