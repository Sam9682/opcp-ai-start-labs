/**
 * ApiDiscovery - Locates the LMS SCORM 1.2 adapter object named `API`
 * by walking parent and opener frame chains.
 *
 * All property access is wrapped in try/catch to tolerate cross-origin
 * frame access errors: discovery returns `null` rather than throwing.
 * The functions are pure over an injectable start window so they can be
 * driven by mock window graphs in tests.
 *
 * Validates: Requirements 6.1, 6.2
 */

/**
 * Maximum number of windows to inspect when walking a chain.
 * Guards against infinite loops in self-referential / cyclic window graphs
 * and detached frames.
 * @type {number}
 */
const MAX_DEPTH = 20;

/**
 * Walk a window's `.parent` chain looking for a window exposing `API`.
 *
 * Starts at `startWin` itself, then follows `.parent` upward until a window
 * exposing `API` is found, the top window is reached (a window whose parent
 * is itself), or MAX_DEPTH windows have been inspected. Every property access
 * is wrapped in try/catch so cross-origin access errors return `null` rather
 * than throwing.
 *
 * @param {Window} startWin - The window to begin the parent-walk from
 * @returns {object|null} The LMS API object, or `null` if not found
 */
export function findApiInChain(startWin) {
  let win = startWin;
  let depth = 0;

  while (win != null && depth < MAX_DEPTH) {
    // Does this window expose `API`?
    try {
      if (win.API != null) {
        return win.API;
      }
    } catch {
      // Cross-origin access: treat as "not here" and keep walking.
    }

    // Advance to the parent. The top window's parent is itself.
    let parent;
    try {
      parent = win.parent;
    } catch {
      // Cross-origin access to .parent: cannot walk further.
      return null;
    }

    if (parent == null || parent === win) {
      // Reached the top window.
      break;
    }

    win = parent;
    depth += 1;
  }

  return null;
}

/**
 * Discover the LMS API: parent chain first (Req 6.1), then opener chain (Req 6.2).
 *
 * 1. Walk `win` then `win.parent` upward until `API` is found or the top
 *    window / MAX_DEPTH is reached.
 * 2. If not found and `win.opener` exists, repeat the parent-walk starting
 *    from `win.opener`.
 * 3. Return the first `API` found, else `null`.
 *
 * @param {Window} [win=window] - The window to begin discovery from
 * @returns {object|null} The LMS API object, or `null` if not found
 */
export function discoverApi(win = window) {
  if (win == null) {
    return null;
  }

  // 1. Parent chain.
  const fromParent = findApiInChain(win);
  if (fromParent != null) {
    return fromParent;
  }

  // 2. Opener chain.
  let opener;
  try {
    opener = win.opener;
  } catch {
    // Cross-origin access to .opener: nothing more to search.
    return null;
  }

  if (opener != null && opener !== win) {
    const fromOpener = findApiInChain(opener);
    if (fromOpener != null) {
      return fromOpener;
    }
  }

  return null;
}
