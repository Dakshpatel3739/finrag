/* FinRAG UI kit — shared icons (lucide-style, 24px stroke grid).
   Loaded as a Babel script; components are published on window. */
(function () {
  const S = (paths, props = {}) => (p) => (
    <svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor"
         strokeWidth={props.sw || 1.9} strokeLinecap="round" strokeLinejoin="round" {...p}>
      {paths}
    </svg>
  );

  const Icons = {
    Search:   S(<><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></>),
    Send:     S(<><path d="M4 12l16-8-6 16-3-6-7-2z"/></>),
    ArrowUp:  S(<><path d="M12 19V5M6 11l6-6 6 6"/></>, { sw: 2.2 }),
    Plus:     S(<><path d="M12 5v14M5 12h14"/></>, { sw: 2.1 }),
    Doc:      S(<><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/></>),
    DocSearch:S(<><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h6"/><path d="M14 3v5h5"/><circle cx="17" cy="16" r="3"/><path d="M21.5 20.5L19 18"/></>),
    Lock:     S(<><rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></>),
    Shield:   S(<><path d="M12 3l7 3v6c0 4-3 6.5-7 9-4-2.5-7-5-7-9V6z"/></>),
    ShieldCheck: S(<><path d="M12 3l7 3v6c0 4-3 6.5-7 9-4-2.5-7-5-7-9V6z"/><path d="M9 12l2 2 4-4"/></>),
    Check:    S(<><path d="M5 12.5l4.5 4.5L19 7"/></>, { sw: 2.3 }),
    Copy:     S(<><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></>),
    Logout:   S(<><path d="M9 21H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/></>),
    Chevron:  S(<><path d="M6 9l6 6 6-6"/></>, { sw: 2 }),
    Sparkle:  S(<><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/></>),
    Mail:     S(<><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></>),
    Eye:      S(<><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></>),
    Alert:    S(<><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></>),
    Info:     S(<><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></>),
    Filter:   S(<><path d="M3 5h18l-7 8v5l-4 2v-7z"/></>),
    Layers:   S(<><path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/></>),
    Upload:   S(<><path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/><path d="M12 15V4M7 9l5-5 5 5"/></>, { sw: 2 }),
    Ask:      S(<><path d="M21 11.5a8.4 8.4 0 0 1-8.5 8.5 8.6 8.6 0 0 1-3.9-.9L3 21l1.9-5.6A8.4 8.4 0 0 1 4 11.5 8.5 8.5 0 0 1 12.5 3 8.4 8.4 0 0 1 21 11.5z"/></>),
    Users:    S(<><circle cx="9" cy="8" r="3.2"/><path d="M3 20a6 6 0 0 1 12 0"/><path d="M16 5.2a3.2 3.2 0 0 1 0 5.6M21 20a6 6 0 0 0-4-5.6"/></>),
    Trash:    S(<><path d="M4 7h16M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2M6 7l1 13a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-13"/></>),
    Dots:     S(<><circle cx="5" cy="12" r="1.4" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none"/><circle cx="19" cy="12" r="1.4" fill="currentColor" stroke="none"/></>),
    Calendar: S(<><rect x="4" y="5" width="16" height="16" rx="2"/><path d="M4 9h16M8 3v4M16 3v4"/></>),
    Building: S(<><rect x="5" y="3" width="14" height="18" rx="1.5"/><path d="M9 7h2M13 7h2M9 11h2M13 11h2M9 15h2M13 15h2"/></>),
    Clock:    S(<><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>),
    X:        S(<><path d="M6 6l12 12M18 6L6 18"/></>, { sw: 2.1 }),
    ChevRight:S(<><path d="M9 6l6 6-6 6"/></>, { sw: 2 }),
    Pages:    S(<><path d="M8 3h8a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/><path d="M9 8h6M9 12h6M9 16h3"/></>),
  };

  window.Icons = Icons;
})();
