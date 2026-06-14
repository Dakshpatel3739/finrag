/* @ds-bundle: {"format":3,"namespace":"FinRAGDesignSystem_2f3924","components":[{"name":"AccessBadge","sourcePath":"components/citation/AccessBadge.jsx"},{"name":"Citation","sourcePath":"components/citation/Citation.jsx"},{"name":"ConfidenceMeter","sourcePath":"components/citation/ConfidenceMeter.jsx"},{"name":"SourceCard","sourcePath":"components/citation/SourceCard.jsx"},{"name":"Avatar","sourcePath":"components/core/Avatar.jsx"},{"name":"Badge","sourcePath":"components/core/Badge.jsx"},{"name":"Button","sourcePath":"components/core/Button.jsx"},{"name":"IconButton","sourcePath":"components/core/IconButton.jsx"},{"name":"Spinner","sourcePath":"components/core/Spinner.jsx"},{"name":"Card","sourcePath":"components/data/Card.jsx"},{"name":"ProgressBar","sourcePath":"components/data/ProgressBar.jsx"},{"name":"StatTile","sourcePath":"components/data/StatTile.jsx"},{"name":"Tabs","sourcePath":"components/data/Tabs.jsx"},{"name":"Banner","sourcePath":"components/feedback/Banner.jsx"},{"name":"EmptyState","sourcePath":"components/feedback/EmptyState.jsx"},{"name":"Toast","sourcePath":"components/feedback/Toast.jsx"},{"name":"Tooltip","sourcePath":"components/feedback/Tooltip.jsx"},{"name":"Checkbox","sourcePath":"components/forms/Checkbox.jsx"},{"name":"Field","sourcePath":"components/forms/Field.jsx"},{"name":"Input","sourcePath":"components/forms/Input.jsx"},{"name":"Select","sourcePath":"components/forms/Select.jsx"},{"name":"Switch","sourcePath":"components/forms/Switch.jsx"},{"name":"Textarea","sourcePath":"components/forms/Textarea.jsx"}],"sourceHashes":{"components/citation/AccessBadge.jsx":"c6a5e326ff84","components/citation/Citation.jsx":"e33051e3b605","components/citation/ConfidenceMeter.jsx":"e2c2b75c6ef9","components/citation/SourceCard.jsx":"9c0ee9173635","components/core/Avatar.jsx":"c2d843e69528","components/core/Badge.jsx":"b463c36a9ee6","components/core/Button.jsx":"ac3f0fde5333","components/core/IconButton.jsx":"d49a3a816e70","components/core/Spinner.jsx":"c14d0f727558","components/data/Card.jsx":"cbd0f9acaf73","components/data/ProgressBar.jsx":"c38d27790b44","components/data/StatTile.jsx":"7ddb6b696ad6","components/data/Tabs.jsx":"fce654cc270a","components/feedback/Banner.jsx":"13d57d12286b","components/feedback/EmptyState.jsx":"ea161af65d60","components/feedback/Toast.jsx":"5ef3197a4bd4","components/feedback/Tooltip.jsx":"26e061809b0a","components/forms/Checkbox.jsx":"e167ab850376","components/forms/Field.jsx":"d202ef1f31d5","components/forms/Input.jsx":"f0b62c4b2cb1","components/forms/Select.jsx":"3ae6450d0195","components/forms/Switch.jsx":"c122fd2ba445","components/forms/Textarea.jsx":"6b299e75165e","ui_kits/finrag-app/AdminScreen.jsx":"c9a4e9c5970c","ui_kits/finrag-app/AppHeader.jsx":"0dec27c80856","ui_kits/finrag-app/DocumentsScreen.jsx":"2283fb0116cf","ui_kits/finrag-app/Icons.jsx":"9effee6624b2","ui_kits/finrag-app/LoginScreen.jsx":"755316c75b85","ui_kits/finrag-app/NavSidebar.jsx":"445f65fd64ef","ui_kits/finrag-app/QueryScreen.jsx":"799399372f33","ui_kits/finrag-app/api.js":"b3af6f5eed86","ui_kits/finrag-app/config.js":"c3422f39d274","ui_kits/finrag-app/mockData.js":"1126cb096e50"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.FinRAGDesignSystem_2f3924 = window.FinRAGDesignSystem_2f3924 || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/citation/AccessBadge.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const LockIcon = () => /*#__PURE__*/React.createElement("svg", {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: "2.2",
  strokeLinecap: "round",
  strokeLinejoin: "round"
}, /*#__PURE__*/React.createElement("rect", {
  x: "5",
  y: "11",
  width: "14",
  height: "9",
  rx: "2"
}), /*#__PURE__*/React.createElement("path", {
  d: "M8 11V8a4 4 0 0 1 8 0v3"
}));
const CheckIcon = () => /*#__PURE__*/React.createElement("svg", {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: "2.4",
  strokeLinecap: "round",
  strokeLinejoin: "round"
}, /*#__PURE__*/React.createElement("path", {
  d: "M5 12.5l4.5 4.5L19 7"
}));
const ShieldIcon = () => /*#__PURE__*/React.createElement("svg", {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: "2.2",
  strokeLinecap: "round",
  strokeLinejoin: "round"
}, /*#__PURE__*/React.createElement("path", {
  d: "M12 3l7 3v6c0 4-3 6.5-7 9-4-2.5-7-5-7-9V6z"
}));
const PRESET = {
  granted: {
    icon: /*#__PURE__*/React.createElement(CheckIcon, null),
    label: 'Authorized'
  },
  restricted: {
    icon: /*#__PURE__*/React.createElement(LockIcon, null),
    label: 'Restricted'
  },
  confidential: {
    icon: /*#__PURE__*/React.createElement(ShieldIcon, null),
    label: 'Confidential'
  }
};

/**
 * Chunk-level role-based access indicator. Use `level="role"` with a `role`
 * prop to show which role a chunk is scoped to.
 */
function AccessBadge({
  level = 'granted',
  role,
  className = '',
  children,
  ...rest
}) {
  const cls = ['fr-access', `fr-access--${level}`, className].filter(Boolean).join(' ');
  if (level === 'role') {
    return /*#__PURE__*/React.createElement("span", _extends({
      className: cls
    }, rest), children ?? role);
  }
  const preset = PRESET[level] || PRESET.granted;
  return /*#__PURE__*/React.createElement("span", _extends({
    className: cls
  }, rest), preset.icon, children ?? preset.label);
}
Object.assign(__ds_scope, { AccessBadge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/citation/AccessBadge.jsx", error: String((e && e.message) || e) }); }

// components/citation/Citation.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Inline citation reference chip. Anchors a claim in an answer to its source chunk.
 * Render inside answer text, immediately after the clause it grounds.
 *
 * GROUNDED-ONLY: every Citation must map to a real source. There is no
 * ungrounded / model-only variant — if a claim can't be cited, it isn't shown.
 */
function Citation({
  index,
  active = false,
  className = '',
  children,
  ...rest
}) {
  const cls = ['fr-cite', active ? 'fr-cite--active' : '', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("button", _extends({
    type: "button",
    className: cls,
    "aria-label": `Source ${index ?? children}`
  }, rest), children ?? index);
}
Object.assign(__ds_scope, { Citation });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/citation/Citation.jsx", error: String((e && e.message) || e) }); }

// components/citation/ConfidenceMeter.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
function levelFor(value) {
  if (value >= 0.8) return 'high';
  if (value >= 0.5) return 'medium';
  return 'low';
}

/**
 * Groundedness / confidence meter for an answer. `value` is 0–1.
 */
function ConfidenceMeter({
  value = 0,
  label = 'Grounding',
  className = '',
  ...rest
}) {
  const v = Math.max(0, Math.min(1, value));
  const level = levelFor(v);
  const cls = ['fr-confidence', `fr-confidence--${level}`, className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("div", _extends({
    className: cls
  }, rest), /*#__PURE__*/React.createElement("div", {
    className: "fr-confidence__head"
  }, /*#__PURE__*/React.createElement("span", {
    className: "fr-confidence__label"
  }, label), /*#__PURE__*/React.createElement("span", {
    className: "fr-confidence__pct"
  }, Math.round(v * 100), "%")), /*#__PURE__*/React.createElement("div", {
    className: "fr-confidence__bar"
  }, /*#__PURE__*/React.createElement("div", {
    className: "fr-confidence__fill",
    style: {
      width: `${v * 100}%`
    }
  })));
}
Object.assign(__ds_scope, { ConfidenceMeter });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/citation/ConfidenceMeter.jsx", error: String((e && e.message) || e) }); }

// components/citation/SourceCard.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * A retrieved source chunk shown in the evidence panel beside a cited answer.
 *
 * INVARIANT: only authorized chunks are ever passed to this component. Unauthorized
 * content never enters the answer context, so it is never rendered here — not even as
 * a redacted placeholder (a placeholder would itself reveal that restricted content
 * exists). There is no `locked` state by design.
 */
function SourceCard({
  refIndex,
  docName,
  page,
  excerpt,
  score,
  access,
  role,
  active = false,
  onClick,
  className = '',
  ...rest
}) {
  const cls = ['fr-source', onClick ? 'fr-source--interactive' : '', active ? 'fr-source--active' : '', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("div", _extends({
    className: cls,
    onClick: onClick
  }, rest), /*#__PURE__*/React.createElement("div", {
    className: "fr-source__head"
  }, /*#__PURE__*/React.createElement("span", {
    className: "fr-source__ref"
  }, refIndex), /*#__PURE__*/React.createElement("span", {
    className: "fr-source__doc",
    title: docName
  }, docName), /*#__PURE__*/React.createElement("span", {
    className: "fr-source__meta"
  }, page != null && /*#__PURE__*/React.createElement("span", null, "p.", page), score != null && /*#__PURE__*/React.createElement("span", null, Math.round(score * 100), "%"))), /*#__PURE__*/React.createElement("div", {
    className: "fr-source__excerpt",
    dangerouslySetInnerHTML: typeof excerpt === 'string' ? {
      __html: excerpt
    } : undefined
  }, typeof excerpt === 'string' ? undefined : excerpt), /*#__PURE__*/React.createElement("div", {
    className: "fr-source__foot"
  }, access && /*#__PURE__*/React.createElement(__ds_scope.AccessBadge, {
    level: access,
    role: role
  })));
}
Object.assign(__ds_scope, { SourceCard });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/citation/SourceCard.jsx", error: String((e && e.message) || e) }); }

// components/core/Avatar.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
function initials(name = '') {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return '';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/**
 * User / entity avatar. Shows an image when `src` is set, otherwise initials from `name`.
 */
function Avatar({
  name = '',
  src,
  size = 'md',
  accent = false,
  square = false,
  className = '',
  ...rest
}) {
  const cls = ['fr-avatar', `fr-avatar--${size}`, accent ? 'fr-avatar--accent' : '', square ? 'fr-avatar--square' : '', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("span", _extends({
    className: cls,
    title: name || undefined
  }, rest), src ? /*#__PURE__*/React.createElement("img", {
    src: src,
    alt: name
  }) : initials(name));
}
Object.assign(__ds_scope, { Avatar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Avatar.jsx", error: String((e && e.message) || e) }); }

// components/core/Badge.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Compact status / label chip. Verified variant carries the grounding signal.
 */
function Badge({
  variant = 'neutral',
  dot = false,
  mono = false,
  className = '',
  children,
  ...rest
}) {
  const cls = ['fr-badge', `fr-badge--${variant}`, dot ? 'fr-badge--dot' : '', mono ? 'fr-badge--mono' : '', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("span", _extends({
    className: cls
  }, rest), children);
}
Object.assign(__ds_scope, { Badge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Badge.jsx", error: String((e && e.message) || e) }); }

// components/core/IconButton.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Square icon-only button for toolbars and dense controls.
 * Always pass `label` for accessibility.
 */
function IconButton({
  variant = 'ghost',
  size = 'md',
  label,
  disabled = false,
  className = '',
  children,
  ...rest
}) {
  const cls = ['fr-iconbtn', `fr-iconbtn--${variant}`, `fr-iconbtn--${size}`, className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("button", _extends({
    type: "button",
    className: cls,
    disabled: disabled,
    "aria-label": label,
    title: label
  }, rest), children);
}
Object.assign(__ds_scope, { IconButton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/IconButton.jsx", error: String((e && e.message) || e) }); }

// components/core/Spinner.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/** Indeterminate loading spinner. */
function Spinner({
  size = 'md',
  onAccent = false,
  className = '',
  ...rest
}) {
  const cls = ['fr-spinner', `fr-spinner--${size}`, onAccent ? 'fr-spinner--onaccent' : '', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("span", _extends({
    className: cls,
    role: "status",
    "aria-label": "Loading"
  }, rest));
}
Object.assign(__ds_scope, { Spinner });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Spinner.jsx", error: String((e && e.message) || e) }); }

// components/core/Button.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * FinRAG primary action button. Token-driven, five variants, three sizes.
 */
function Button({
  variant = 'primary',
  size = 'md',
  leftIcon,
  rightIcon,
  loading = false,
  block = false,
  disabled = false,
  type = 'button',
  className = '',
  children,
  ...rest
}) {
  const cls = ['fr-btn', `fr-btn--${variant}`, `fr-btn--${size}`, block ? 'fr-btn--block' : '', className].filter(Boolean).join(' ');
  const isDisabled = disabled || loading;
  return /*#__PURE__*/React.createElement("button", _extends({
    type: type,
    className: cls,
    disabled: isDisabled,
    "aria-busy": loading || undefined
  }, rest), loading ? /*#__PURE__*/React.createElement(__ds_scope.Spinner, {
    size: "sm",
    onAccent: variant === 'primary' || variant === 'danger'
  }) : leftIcon && /*#__PURE__*/React.createElement("span", {
    className: "fr-btn__icon",
    "aria-hidden": "true"
  }, leftIcon), children && /*#__PURE__*/React.createElement("span", null, children), !loading && rightIcon && /*#__PURE__*/React.createElement("span", {
    className: "fr-btn__icon",
    "aria-hidden": "true"
  }, rightIcon));
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Button.jsx", error: String((e && e.message) || e) }); }

// components/data/Card.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Surface container. Optional `title`/`headerRight` render a header row;
 * `footer` renders a footer row. Body holds `children`.
 */
function Card({
  title,
  headerRight,
  footer,
  variant = 'default',
  padding = 'md',
  interactive = false,
  selected = false,
  className = '',
  children,
  ...rest
}) {
  const cls = ['fr-card', variant !== 'default' ? `fr-card--${variant}` : '', padding !== 'md' ? `fr-card--pad-${padding}` : '', interactive ? 'fr-card--interactive' : '', selected ? 'fr-card--selected' : '', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("div", _extends({
    className: cls
  }, rest), (title || headerRight) && /*#__PURE__*/React.createElement("div", {
    className: "fr-card__header"
  }, title && /*#__PURE__*/React.createElement("span", {
    className: "fr-card__title"
  }, title), headerRight && /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 'auto',
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6
    }
  }, headerRight)), /*#__PURE__*/React.createElement("div", {
    className: "fr-card__body"
  }, children), footer && /*#__PURE__*/React.createElement("div", {
    className: "fr-card__footer"
  }, footer));
}
Object.assign(__ds_scope, { Card });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/Card.jsx", error: String((e && e.message) || e) }); }

// components/data/ProgressBar.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/** Linear progress / meter. `value` is 0–1. Set `indeterminate` for unknown progress. */
function ProgressBar({
  value = 0,
  variant = 'default',
  label,
  showValue = false,
  indeterminate = false,
  className = '',
  ...rest
}) {
  const v = Math.max(0, Math.min(1, value));
  const cls = ['fr-progress', variant !== 'default' ? `fr-progress--${variant}` : '', indeterminate ? 'fr-progress--indeterminate' : '', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("div", _extends({
    className: cls
  }, rest), (label || showValue) && /*#__PURE__*/React.createElement("div", {
    className: "fr-progress__head"
  }, label && /*#__PURE__*/React.createElement("span", {
    className: "fr-progress__label"
  }, label), showValue && !indeterminate && /*#__PURE__*/React.createElement("span", {
    className: "fr-progress__value"
  }, Math.round(v * 100), "%")), /*#__PURE__*/React.createElement("div", {
    className: "fr-progress__track"
  }, /*#__PURE__*/React.createElement("div", {
    className: "fr-progress__fill",
    style: {
      width: indeterminate ? undefined : `${v * 100}%`
    }
  })));
}
Object.assign(__ds_scope, { ProgressBar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/ProgressBar.jsx", error: String((e && e.message) || e) }); }

// components/data/StatTile.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/** Compact KPI tile: uppercase label, monospace figure, optional delta + meta. */
function StatTile({
  label,
  value,
  delta,
  deltaDir,
  meta,
  className = '',
  ...rest
}) {
  const cls = ['fr-stat', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("div", _extends({
    className: cls
  }, rest), label && /*#__PURE__*/React.createElement("span", {
    className: "fr-stat__label"
  }, label), /*#__PURE__*/React.createElement("span", {
    className: "fr-stat__value"
  }, value), (delta != null || meta) && /*#__PURE__*/React.createElement("span", {
    className: "fr-stat__meta"
  }, delta != null && /*#__PURE__*/React.createElement("span", {
    className: deltaDir === 'down' ? 'fr-stat__delta--down' : 'fr-stat__delta--up'
  }, deltaDir === 'down' ? '▾' : '▴', " ", delta), meta && /*#__PURE__*/React.createElement("span", null, meta)));
}
Object.assign(__ds_scope, { StatTile });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/StatTile.jsx", error: String((e && e.message) || e) }); }

// components/data/Tabs.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/** Horizontal tab bar. Controlled via `value`/`onChange`. */
function Tabs({
  items = [],
  value,
  onChange,
  className = '',
  ...rest
}) {
  const cls = ['fr-tabs', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("div", _extends({
    className: cls,
    role: "tablist"
  }, rest), items.map(it => {
    const active = it.id === value;
    return /*#__PURE__*/React.createElement("button", {
      key: it.id,
      type: "button",
      role: "tab",
      "aria-selected": active,
      className: ['fr-tab', active ? 'fr-tab--active' : ''].filter(Boolean).join(' '),
      onClick: () => onChange && onChange(it.id)
    }, it.icon && /*#__PURE__*/React.createElement("span", {
      style: {
        display: 'inline-flex',
        width: 15,
        height: 15
      }
    }, it.icon), it.label, it.count != null && /*#__PURE__*/React.createElement("span", {
      className: "fr-tab__count"
    }, it.count));
  }));
}
Object.assign(__ds_scope, { Tabs });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/Tabs.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Banner.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const ICONS = {
  info: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("circle", {
    cx: "12",
    cy: "12",
    r: "9"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M12 11v5M12 8h.01"
  })),
  verified: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M12 3l7 3v6c0 4-3 6.5-7 9-4-2.5-7-5-7-9V6z"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M9 12l2 2 4-4"
  })),
  warning: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M10.3 3.8 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.8a2 2 0 0 0-3.4 0z"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M12 9v4M12 17h.01"
  })),
  danger: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("circle", {
    cx: "12",
    cy: "12",
    r: "9"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M15 9l-6 6M9 9l6 6"
  }))
};
const Close = () => /*#__PURE__*/React.createElement("svg", {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: "2",
  strokeLinecap: "round"
}, /*#__PURE__*/React.createElement("path", {
  d: "M6 6l12 12M18 6L6 18"
}));

/**
 * Inline contextual alert. Use within content flow (not transient — that's Toast).
 */
function Banner({
  variant = 'info',
  title,
  icon,
  onClose,
  className = '',
  children,
  ...rest
}) {
  const cls = ['fr-banner', `fr-banner--${variant}`, className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("div", _extends({
    className: cls,
    role: "status"
  }, rest), /*#__PURE__*/React.createElement("span", {
    className: "fr-banner__icon",
    "aria-hidden": "true"
  }, icon || ICONS[variant]), /*#__PURE__*/React.createElement("div", {
    className: "fr-banner__body"
  }, title && /*#__PURE__*/React.createElement("span", {
    className: "fr-banner__title"
  }, title), children && /*#__PURE__*/React.createElement("span", null, children)), onClose && /*#__PURE__*/React.createElement("span", {
    className: "fr-banner__close"
  }, /*#__PURE__*/React.createElement(__ds_scope.IconButton, {
    size: "sm",
    label: "Dismiss",
    onClick: onClose
  }, /*#__PURE__*/React.createElement(Close, null))));
}
Object.assign(__ds_scope, { Banner });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Banner.jsx", error: String((e && e.message) || e) }); }

// components/feedback/EmptyState.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/** Centered empty / zero-state with icon, message and optional actions. */
function EmptyState({
  icon,
  title,
  description,
  actions,
  className = '',
  ...rest
}) {
  const cls = ['fr-empty', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("div", _extends({
    className: cls
  }, rest), icon && /*#__PURE__*/React.createElement("span", {
    className: "fr-empty__icon",
    "aria-hidden": "true"
  }, icon), title && /*#__PURE__*/React.createElement("div", {
    className: "fr-empty__title"
  }, title), description && /*#__PURE__*/React.createElement("p", {
    className: "fr-empty__desc"
  }, description), actions && /*#__PURE__*/React.createElement("div", {
    className: "fr-empty__actions"
  }, actions));
}
Object.assign(__ds_scope, { EmptyState });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/EmptyState.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Toast.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const ICONS = {
  verified: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("circle", {
    cx: "12",
    cy: "12",
    r: "9"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M8 12l3 3 5-6"
  })),
  info: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("circle", {
    cx: "12",
    cy: "12",
    r: "9"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M12 11v5M12 8h.01"
  })),
  danger: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("circle", {
    cx: "12",
    cy: "12",
    r: "9"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M15 9l-6 6M9 9l6 6"
  }))
};
const Close = () => /*#__PURE__*/React.createElement("svg", {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: "2",
  strokeLinecap: "round"
}, /*#__PURE__*/React.createElement("path", {
  d: "M6 6l12 12M18 6L6 18"
}));

/** Transient notification. Render inside a fixed-position stack. */
function Toast({
  variant = 'info',
  title,
  onClose,
  className = '',
  children,
  ...rest
}) {
  const cls = ['fr-toast', `fr-toast--${variant}`, className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("div", _extends({
    className: cls,
    role: "status"
  }, rest), /*#__PURE__*/React.createElement("span", {
    className: "fr-toast__icon",
    "aria-hidden": "true"
  }, ICONS[variant]), /*#__PURE__*/React.createElement("div", {
    className: "fr-toast__body"
  }, title && /*#__PURE__*/React.createElement("span", {
    className: "fr-toast__title"
  }, title), children && /*#__PURE__*/React.createElement("span", {
    className: "fr-toast__desc"
  }, children)), onClose && /*#__PURE__*/React.createElement("span", {
    className: "fr-toast__close"
  }, /*#__PURE__*/React.createElement(__ds_scope.IconButton, {
    size: "sm",
    label: "Dismiss",
    onClick: onClose
  }, /*#__PURE__*/React.createElement(Close, null))));
}
Object.assign(__ds_scope, { Toast });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Toast.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Tooltip.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/** Hover/focus tooltip. Wraps its trigger child; label appears above. */
function Tooltip({
  label,
  className = '',
  children,
  ...rest
}) {
  const cls = ['fr-tooltip-wrap', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("span", _extends({
    className: cls
  }, rest), children, /*#__PURE__*/React.createElement("span", {
    className: "fr-tooltip",
    role: "tooltip"
  }, label));
}
Object.assign(__ds_scope, { Tooltip });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Tooltip.jsx", error: String((e && e.message) || e) }); }

// components/forms/Checkbox.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/** Controlled checkbox with label. */
function Checkbox({
  checked = false,
  disabled = false,
  label,
  onChange,
  className = '',
  ...rest
}) {
  const cls = ['fr-check', checked ? 'fr-check--checked' : '', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("label", {
    className: cls,
    "aria-disabled": disabled || undefined
  }, /*#__PURE__*/React.createElement("input", _extends({
    type: "checkbox",
    checked: checked,
    disabled: disabled,
    onChange: onChange,
    style: {
      position: 'absolute',
      opacity: 0,
      width: 0,
      height: 0
    }
  }, rest)), /*#__PURE__*/React.createElement("span", {
    className: "fr-check__box",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "3",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M5 12.5l4.5 4.5L19 7"
  }))), label && /*#__PURE__*/React.createElement("span", {
    className: "fr-check__label"
  }, label));
}
Object.assign(__ds_scope, { Checkbox });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Checkbox.jsx", error: String((e && e.message) || e) }); }

// components/forms/Field.jsx
try { (() => {
/**
 * Labeled field wrapper. Composes a label, optional hint, control, and error message.
 */
function Field({
  label,
  hint,
  error,
  required = false,
  htmlFor,
  className = '',
  children
}) {
  const cls = ['fr-field', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("div", {
    className: cls
  }, label && /*#__PURE__*/React.createElement("label", {
    className: "fr-field__label",
    htmlFor: htmlFor
  }, label, required && /*#__PURE__*/React.createElement("span", {
    className: "fr-field__req",
    "aria-hidden": "true"
  }, "*")), children, error ? /*#__PURE__*/React.createElement("span", {
    className: "fr-field__error"
  }, error) : hint && /*#__PURE__*/React.createElement("span", {
    className: "fr-field__hint"
  }, hint));
}
Object.assign(__ds_scope, { Field });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Field.jsx", error: String((e && e.message) || e) }); }

// components/forms/Input.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Text input. Supports a leading icon, invalid state, sizes and mono (for ids/figures).
 */
function Input({
  size = 'md',
  invalid = false,
  mono = false,
  icon,
  className = '',
  ...rest
}) {
  const cls = ['fr-input', size !== 'md' ? `fr-input--${size}` : '', invalid ? 'fr-input--invalid' : '', mono ? 'fr-input--mono' : '', className].filter(Boolean).join(' ');
  const input = /*#__PURE__*/React.createElement("input", _extends({
    className: cls,
    "aria-invalid": invalid || undefined
  }, rest));
  if (!icon) return input;
  return /*#__PURE__*/React.createElement("span", {
    className: "fr-input-group"
  }, /*#__PURE__*/React.createElement("span", {
    className: "fr-input-group__icon",
    "aria-hidden": "true"
  }, icon), input);
}
Object.assign(__ds_scope, { Input });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Input.jsx", error: String((e && e.message) || e) }); }

// components/forms/Select.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/** Native select with FinRAG styling and a custom chevron. */
function Select({
  invalid = false,
  className = '',
  children,
  ...rest
}) {
  const cls = ['fr-select', invalid ? 'fr-input--invalid' : '', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("span", {
    className: "fr-select-wrap"
  }, /*#__PURE__*/React.createElement("select", _extends({
    className: cls,
    "aria-invalid": invalid || undefined
  }, rest), children), /*#__PURE__*/React.createElement("span", {
    className: "fr-select-wrap__chevron",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    width: "16",
    height: "16"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M6 9l6 6 6-6"
  }))));
}
Object.assign(__ds_scope, { Select });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Select.jsx", error: String((e && e.message) || e) }); }

// components/forms/Switch.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/** Controlled toggle switch with optional label. */
function Switch({
  checked = false,
  disabled = false,
  label,
  onChange,
  className = '',
  ...rest
}) {
  const cls = ['fr-switch', checked ? 'fr-switch--on' : '', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("label", {
    className: cls,
    "aria-disabled": disabled || undefined
  }, /*#__PURE__*/React.createElement("input", _extends({
    type: "checkbox",
    role: "switch",
    checked: checked,
    disabled: disabled,
    onChange: onChange,
    style: {
      position: 'absolute',
      opacity: 0,
      width: 0,
      height: 0
    }
  }, rest)), /*#__PURE__*/React.createElement("span", {
    className: "fr-switch__track",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("span", {
    className: "fr-switch__thumb"
  })), label && /*#__PURE__*/React.createElement("span", {
    className: "fr-switch__label"
  }, label));
}
Object.assign(__ds_scope, { Switch });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Switch.jsx", error: String((e && e.message) || e) }); }

// components/forms/Textarea.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/** Multi-line text input. Vertically resizable. */
function Textarea({
  invalid = false,
  className = '',
  rows = 3,
  ...rest
}) {
  const cls = ['fr-input', invalid ? 'fr-input--invalid' : '', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("textarea", _extends({
    className: cls,
    rows: rows,
    "aria-invalid": invalid || undefined
  }, rest));
}
Object.assign(__ds_scope, { Textarea });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Textarea.jsx", error: String((e && e.message) || e) }); }

// ui_kits/finrag-app/AdminScreen.jsx
try { (() => {
/* FinRAG UI kit — Screen 4: Owner-only access control.
   Configures which ROLES may retrieve each document section. This is
   POLICY configuration — it shows who is permitted, never the withheld
   content itself. Sections below a role's threshold are never retrieved
   for that role (and never revealed to exist in an answer). */
(function () {
  const DS = window.FinRAGDesignSystem_2f3924;
  const {
    Button,
    IconButton,
    Badge,
    Avatar,
    Select,
    Banner,
    AccessBadge,
    Tooltip
  } = DS;
  const I = window.Icons;
  const FX = window.FINRAG_FIXTURES;
  const TIER = {
    public: {
      access: 'granted',
      label: 'Public'
    },
    internal: {
      access: 'role',
      label: 'Internal'
    },
    restricted: {
      access: 'restricted',
      label: 'Restricted'
    }
  };
  const ROLE_LABEL = {
    owner: 'Owner',
    finance: 'Finance',
    hr: 'HR',
    employee: 'Employee'
  };
  function rolesForTier(tier) {
    return FX.sensitivityAccess[tier] || FX.sensitivityAccess.public;
  }

  /* ---- Members table -------------------------------------------- */
  function MembersCard({
    session
  }) {
    const [members, setMembers] = React.useState(FX.members);
    function changeRole(id, role) {
      setMembers(m => m.map(u => u.id === id ? {
        ...u,
        role
      } : u));
    }
    return /*#__PURE__*/React.createElement("section", {
      style: ad.card
    }, /*#__PURE__*/React.createElement("div", {
      style: ad.cardHead
    }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h2", {
      style: ad.cardTitle
    }, "Members"), /*#__PURE__*/React.createElement("p", {
      style: ad.cardSub
    }, "A member\u2019s role determines which document sections they can retrieve. Only ", /*#__PURE__*/React.createElement("strong", null, "owner"), " and ", /*#__PURE__*/React.createElement("strong", null, "finance"), " can retrieve restricted sections.")), /*#__PURE__*/React.createElement(Button, {
      variant: "secondary",
      size: "sm",
      leftIcon: /*#__PURE__*/React.createElement(I.Plus, null)
    }, "Invite member")), /*#__PURE__*/React.createElement("div", {
      style: ad.memberTable
    }, members.map(u => {
      const isSelf = u.email === session.email;
      return /*#__PURE__*/React.createElement("div", {
        key: u.id,
        style: ad.memberRow
      }, /*#__PURE__*/React.createElement("div", {
        style: ad.memberId
      }, /*#__PURE__*/React.createElement(Avatar, {
        name: u.name,
        size: "md",
        accent: u.role === 'owner'
      }), /*#__PURE__*/React.createElement("div", {
        style: {
          minWidth: 0
        }
      }, /*#__PURE__*/React.createElement("div", {
        style: ad.memberName
      }, u.name, isSelf && /*#__PURE__*/React.createElement("span", {
        style: ad.youTag
      }, "You")), /*#__PURE__*/React.createElement("div", {
        style: ad.memberEmail
      }, u.email))), /*#__PURE__*/React.createElement("div", {
        style: ad.memberLast
      }, "Active ", new Date(u.lastActive + 'T00:00:00').toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
      })), /*#__PURE__*/React.createElement("div", {
        style: {
          width: 150
        }
      }, /*#__PURE__*/React.createElement(Select, {
        value: u.role,
        disabled: isSelf,
        onChange: e => changeRole(u.id, e.target.value)
      }, FX.roles.map(r => /*#__PURE__*/React.createElement("option", {
        key: r,
        value: r
      }, ROLE_LABEL[r])))), /*#__PURE__*/React.createElement("div", {
        style: {
          display: 'flex',
          justifyContent: 'flex-end'
        }
      }, /*#__PURE__*/React.createElement(IconButton, {
        variant: "ghost",
        label: "Member options",
        disabled: isSelf
      }, /*#__PURE__*/React.createElement(I.Dots, null))));
    })));
  }

  /* ---- Section access matrix ------------------------------------ */
  function MatrixCard() {
    const [sections, setSections] = React.useState(FX.sections);
    function setTier(id, sensitivity) {
      setSections(s => s.map(sec => sec.id === id ? {
        ...sec,
        sensitivity
      } : sec));
    }
    return /*#__PURE__*/React.createElement("section", {
      style: ad.card
    }, /*#__PURE__*/React.createElement("div", {
      style: ad.cardHead
    }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h2", {
      style: ad.cardTitle
    }, "Section access policy"), /*#__PURE__*/React.createElement("p", {
      style: ad.cardSub
    }, "Set the sensitivity of each document section. Public and internal sections are retrievable by all roles; restricted sections are retrievable by owner and finance only \u2014 hr and employee can never see, or learn of, restricted content."))), /*#__PURE__*/React.createElement("div", {
      style: ad.matrixHead
    }, /*#__PURE__*/React.createElement("span", {
      style: ad.colSection
    }, "Document section"), FX.roles.map(r => /*#__PURE__*/React.createElement("span", {
      key: r,
      style: ad.colRole
    }, ROLE_LABEL[r])), /*#__PURE__*/React.createElement("span", {
      style: ad.colMin
    }, "Sensitivity")), sections.map(sec => {
      const allowed = rolesForTier(sec.sensitivity);
      const tier = TIER[sec.sensitivity] || TIER.public;
      return /*#__PURE__*/React.createElement("div", {
        key: sec.id,
        style: ad.matrixRow
      }, /*#__PURE__*/React.createElement("div", {
        style: ad.colSection
      }, /*#__PURE__*/React.createElement("div", {
        style: ad.secLabelRow
      }, /*#__PURE__*/React.createElement("span", {
        style: ad.secLabel
      }, sec.label), sec.sensitivity === 'public' ? /*#__PURE__*/React.createElement(Badge, {
        variant: "neutral"
      }, tier.label) : /*#__PURE__*/React.createElement(AccessBadge, {
        level: tier.access,
        role: tier.label
      }, tier.label)), /*#__PURE__*/React.createElement("div", {
        style: ad.secDetail
      }, sec.detail)), FX.roles.map(r => {
        const ok = allowed.includes(r);
        return /*#__PURE__*/React.createElement("span", {
          key: r,
          style: ad.colRole
        }, ok ? /*#__PURE__*/React.createElement("span", {
          style: ad.cellOk,
          title: `${ROLE_LABEL[r]} can retrieve this section`
        }, /*#__PURE__*/React.createElement(I.Check, null)) : /*#__PURE__*/React.createElement("span", {
          style: ad.cellNo,
          title: `${ROLE_LABEL[r]} cannot retrieve this section`
        }, /*#__PURE__*/React.createElement(I.Lock, null)));
      }), /*#__PURE__*/React.createElement("div", {
        style: ad.colMin
      }, /*#__PURE__*/React.createElement(Select, {
        value: sec.sensitivity,
        onChange: e => setTier(sec.id, e.target.value)
      }, FX.sensitivityTiers.map(t => /*#__PURE__*/React.createElement("option", {
        key: t,
        value: t
      }, TIER[t].label)))));
    }), /*#__PURE__*/React.createElement("div", {
      style: ad.matrixFoot
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: ad.cellOk
    }, /*#__PURE__*/React.createElement(I.Check, null)), " Can retrieve"), /*#__PURE__*/React.createElement("span", {
      style: {
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: ad.cellNo
    }, /*#__PURE__*/React.createElement(I.Lock, null)), " Never retrieved or revealed")));
  }
  function AdminScreen({
    session
  }) {
    if (session.role !== 'owner') {
      return /*#__PURE__*/React.createElement("div", {
        style: ad.screen
      }, /*#__PURE__*/React.createElement("div", {
        style: {
          ...ad.inner,
          maxWidth: 520
        }
      }, /*#__PURE__*/React.createElement(Banner, {
        variant: "info",
        title: "Owner access required"
      }, "Access control is managed by workspace owners. Ask an owner if you need a section opened up for your role.")));
    }
    return /*#__PURE__*/React.createElement("div", {
      style: ad.screen
    }, /*#__PURE__*/React.createElement("div", {
      style: ad.inner
    }, /*#__PURE__*/React.createElement("div", {
      style: ad.head
    }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h1", {
      style: ad.title
    }, "Access control"), /*#__PURE__*/React.createElement("p", {
      style: ad.subtitle
    }, "Govern which roles can retrieve each document section across the workspace.")), /*#__PURE__*/React.createElement(Button, {
      variant: "primary",
      leftIcon: /*#__PURE__*/React.createElement(I.ShieldCheck, null)
    }, "Save policy")), /*#__PURE__*/React.createElement(Banner, {
      variant: "verified",
      title: "How access shapes answers",
      className: ""
    }, "Retrieval respects these rules at the chunk level. Sections above a member\u2019s role are never added to a query\u2019s context \u2014 and are never hinted at in an answer. There is no \u201Crestricted\u201D placeholder: for an unauthorized role, the content simply isn\u2019t there."), /*#__PURE__*/React.createElement("div", {
      style: {
        height: 20
      }
    }), /*#__PURE__*/React.createElement(MembersCard, {
      session: session
    }), /*#__PURE__*/React.createElement("div", {
      style: {
        height: 16
      }
    }), /*#__PURE__*/React.createElement(MatrixCard, null)));
  }
  const ad = {
    screen: {
      flex: 1,
      overflowY: 'auto',
      background: 'var(--surface-page)'
    },
    inner: {
      maxWidth: 'var(--container-max)',
      margin: '0 auto',
      padding: '28px 32px 48px'
    },
    head: {
      display: 'flex',
      alignItems: 'flex-start',
      justifyContent: 'space-between',
      gap: 24,
      marginBottom: 20
    },
    title: {
      fontSize: 'var(--text-2xl)',
      fontWeight: 600,
      letterSpacing: 'var(--tracking-snug)'
    },
    subtitle: {
      fontSize: 'var(--text-sm)',
      color: 'var(--text-secondary)',
      marginTop: 5
    },
    card: {
      background: 'var(--surface-card)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-lg)',
      overflow: 'hidden'
    },
    cardHead: {
      display: 'flex',
      alignItems: 'flex-start',
      justifyContent: 'space-between',
      gap: 20,
      padding: '18px 20px',
      borderBottom: '1px solid var(--border-subtle)'
    },
    cardTitle: {
      fontSize: 'var(--text-lg)',
      fontWeight: 600,
      letterSpacing: 'var(--tracking-snug)'
    },
    cardSub: {
      fontSize: 'var(--text-sm)',
      color: 'var(--text-secondary)',
      marginTop: 4,
      maxWidth: 560,
      lineHeight: 1.5
    },
    /* members */
    memberTable: {
      display: 'flex',
      flexDirection: 'column'
    },
    memberRow: {
      display: 'grid',
      gridTemplateColumns: 'minmax(0,1fr) 140px 150px 44px',
      gap: 16,
      alignItems: 'center',
      padding: '12px 20px',
      borderBottom: '1px solid var(--border-subtle)'
    },
    memberId: {
      display: 'flex',
      alignItems: 'center',
      gap: 11,
      minWidth: 0
    },
    memberName: {
      fontSize: 'var(--text-sm)',
      fontWeight: 600,
      color: 'var(--text-primary)',
      display: 'flex',
      alignItems: 'center',
      gap: 8
    },
    youTag: {
      fontSize: 'var(--text-2xs)',
      fontWeight: 600,
      color: 'var(--accent-text)',
      background: 'var(--accent-soft)',
      border: '1px solid var(--accent-soft-bd)',
      borderRadius: 'var(--radius-xs)',
      padding: '0 5px',
      letterSpacing: 'var(--tracking-wide)'
    },
    memberEmail: {
      fontSize: 'var(--text-xs)',
      color: 'var(--text-tertiary)',
      fontFamily: 'var(--font-mono)'
    },
    memberLast: {
      fontSize: 'var(--text-xs)',
      color: 'var(--text-secondary)'
    },
    /* matrix */
    matrixHead: {
      display: 'grid',
      gridTemplateColumns: 'minmax(0,1fr) repeat(4, 64px) 150px',
      gap: 12,
      alignItems: 'center',
      padding: '10px 20px',
      background: 'var(--surface-sunken)',
      borderBottom: '1px solid var(--border-subtle)',
      fontSize: 'var(--text-2xs)',
      fontWeight: 600,
      letterSpacing: 'var(--tracking-caps)',
      textTransform: 'uppercase',
      color: 'var(--text-tertiary)'
    },
    matrixRow: {
      display: 'grid',
      gridTemplateColumns: 'minmax(0,1fr) repeat(4, 64px) 150px',
      gap: 12,
      alignItems: 'center',
      padding: '14px 20px',
      borderBottom: '1px solid var(--border-subtle)'
    },
    colSection: {
      minWidth: 0
    },
    colRole: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      textAlign: 'center'
    },
    colMin: {
      display: 'flex',
      justifyContent: 'flex-end'
    },
    secLabelRow: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      flexWrap: 'wrap'
    },
    secLabel: {
      fontSize: 'var(--text-sm)',
      fontWeight: 600,
      color: 'var(--text-primary)'
    },
    secDetail: {
      fontSize: 'var(--text-xs)',
      color: 'var(--text-tertiary)',
      marginTop: 3
    },
    cellOk: {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: 22,
      height: 22,
      borderRadius: 'var(--radius-xs)',
      background: 'var(--verified-soft)',
      color: 'var(--verified)',
      fontSize: 14,
      border: '1px solid var(--verified-soft-bd)'
    },
    cellNo: {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: 22,
      height: 22,
      borderRadius: 'var(--radius-xs)',
      background: 'var(--surface-sunken)',
      color: 'var(--text-disabled)',
      fontSize: 12,
      border: '1px solid var(--border-subtle)'
    },
    matrixFoot: {
      display: 'flex',
      gap: 20,
      padding: '12px 20px',
      fontSize: 'var(--text-xs)',
      color: 'var(--text-secondary)'
    }
  };
  window.AdminScreen = AdminScreen;
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/finrag-app/AdminScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/finrag-app/AppHeader.jsx
try { (() => {
/* FinRAG UI kit — application header with workspace + role indicator. */
(function () {
  const DS = window.FinRAGDesignSystem_2f3924;
  const {
    IconButton,
    Avatar,
    Tooltip
  } = DS;
  const I = window.Icons;
  function AppHeader({
    role = 'finance',
    email = '',
    workspace = 'Acme Treasury',
    onSignOut
  }) {
    const ROLE_LABEL = {
      owner: 'Owner',
      finance: 'Finance',
      hr: 'HR',
      employee: 'Employee'
    };
    const roleLabel = ROLE_LABEL[role] || role;
    return /*#__PURE__*/React.createElement("header", {
      style: hdr.bar
    }, /*#__PURE__*/React.createElement("div", {
      style: hdr.left
    }, /*#__PURE__*/React.createElement("img", {
      src: "../../assets/logo-wordmark.svg",
      alt: "FinRAG",
      height: "22",
      style: {
        display: 'block'
      }
    }), /*#__PURE__*/React.createElement("span", {
      style: hdr.divider
    }), /*#__PURE__*/React.createElement("button", {
      type: "button",
      style: hdr.workspace
    }, /*#__PURE__*/React.createElement("span", {
      style: hdr.wsAvatar
    }, workspace.slice(0, 1)), /*#__PURE__*/React.createElement("span", {
      style: hdr.wsName
    }, workspace), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 14,
        color: 'var(--text-tertiary)',
        display: 'inline-flex'
      }
    }, /*#__PURE__*/React.createElement(I.Chevron, null)))), /*#__PURE__*/React.createElement("div", {
      style: hdr.right
    }, /*#__PURE__*/React.createElement(Tooltip, {
      label: `Your role determines which document sections you can see`
    }, /*#__PURE__*/React.createElement("span", {
      style: hdr.role
    }, /*#__PURE__*/React.createElement("span", {
      style: hdr.roleDot
    }), "Signed in as ", /*#__PURE__*/React.createElement("strong", {
      style: hdr.roleName
    }, roleLabel))), /*#__PURE__*/React.createElement(Avatar, {
      name: email || role,
      size: "sm",
      accent: true
    }), /*#__PURE__*/React.createElement(IconButton, {
      variant: "ghost",
      label: "Sign out",
      onClick: onSignOut
    }, /*#__PURE__*/React.createElement(I.Logout, null))));
  }
  const hdr = {
    bar: {
      height: 'var(--topbar-height)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 16px',
      background: 'var(--surface-card)',
      borderBottom: '1px solid var(--border-subtle)',
      position: 'sticky',
      top: 0,
      zIndex: 'var(--z-sticky)'
    },
    left: {
      display: 'flex',
      alignItems: 'center',
      gap: 12
    },
    divider: {
      width: 1,
      height: 22,
      background: 'var(--border-default)'
    },
    workspace: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 8,
      background: 'none',
      border: '1px solid transparent',
      borderRadius: 'var(--radius-sm)',
      cursor: 'pointer',
      padding: '5px 8px',
      font: 'inherit'
    },
    wsAvatar: {
      width: 20,
      height: 20,
      borderRadius: 'var(--radius-xs)',
      background: 'var(--slate-900)',
      color: '#fff',
      fontSize: 11,
      fontWeight: 600,
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center'
    },
    wsName: {
      fontSize: 'var(--text-sm)',
      fontWeight: 600,
      color: 'var(--text-primary)'
    },
    right: {
      display: 'flex',
      alignItems: 'center',
      gap: 10
    },
    role: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 7,
      fontSize: 'var(--text-sm)',
      color: 'var(--text-secondary)',
      padding: '5px 10px',
      borderRadius: 'var(--radius-pill)',
      background: 'var(--surface-sunken)',
      border: '1px solid var(--border-subtle)',
      cursor: 'default',
      whiteSpace: 'nowrap'
    },
    roleDot: {
      width: 7,
      height: 7,
      borderRadius: '50%',
      background: 'var(--verified)'
    },
    roleName: {
      color: 'var(--text-primary)',
      fontWeight: 600
    }
  };
  window.AppHeader = AppHeader;
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/finrag-app/AppHeader.jsx", error: String((e && e.message) || e) }); }

// ui_kits/finrag-app/DocumentsScreen.jsx
try { (() => {
/* FinRAG UI kit — Screen 3: Document library / dashboard.
   List of indexed filings with status, metadata, search, filter,
   upload, and empty states. Composes DS primitives. */
(function () {
  const DS = window.FinRAGDesignSystem_2f3924;
  const {
    Button,
    IconButton,
    Badge,
    Avatar,
    StatTile,
    Input,
    EmptyState,
    ProgressBar,
    Tooltip
  } = DS;
  const I = window.Icons;
  const FX = window.FINRAG_FIXTURES;
  const STATUS = {
    indexed: {
      variant: 'verified',
      label: 'Indexed',
      dot: true
    },
    processing: {
      variant: 'accent',
      label: 'Processing',
      dot: true
    },
    failed: {
      variant: 'danger',
      label: 'Failed',
      dot: true
    }
  };
  const TABS = [{
    id: 'all',
    label: 'All'
  }, {
    id: 'indexed',
    label: 'Indexed'
  }, {
    id: 'processing',
    label: 'Processing'
  }, {
    id: 'failed',
    label: 'Needs attention'
  }];
  function fmtDate(s) {
    const d = new Date(s + 'T00:00:00');
    return d.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  }
  function DocRow({
    doc
  }) {
    const st = STATUS[doc.status] || STATUS.indexed;
    return /*#__PURE__*/React.createElement("div", {
      style: ds.row
    }, /*#__PURE__*/React.createElement("div", {
      style: ds.cellName
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        ...ds.fileIcon,
        ...(doc.status === 'failed' ? ds.fileIconFail : null)
      }
    }, /*#__PURE__*/React.createElement(I.Doc, null)), /*#__PURE__*/React.createElement("div", {
      style: {
        minWidth: 0
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: ds.fileName,
      title: doc.name
    }, doc.name), /*#__PURE__*/React.createElement("div", {
      style: ds.fileMeta
    }, /*#__PURE__*/React.createElement("span", {
      className: "num"
    }, doc.id), /*#__PURE__*/React.createElement("span", {
      style: ds.metaDot
    }), /*#__PURE__*/React.createElement("span", null, doc.kind), /*#__PURE__*/React.createElement("span", {
      style: ds.metaDot
    }), /*#__PURE__*/React.createElement("span", null, doc.fiscalYear)), doc.status === 'failed' && doc.error && /*#__PURE__*/React.createElement("div", {
      style: ds.errLine
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 12,
        display: 'inline-flex'
      }
    }, /*#__PURE__*/React.createElement(I.Alert, null)), doc.error))), /*#__PURE__*/React.createElement("div", {
      style: ds.cellStatus
    }, doc.status === 'processing' ? /*#__PURE__*/React.createElement("div", {
      style: {
        width: 132
      }
    }, /*#__PURE__*/React.createElement(ProgressBar, {
      value: doc.progress,
      indeterminate: false
    }), /*#__PURE__*/React.createElement("span", {
      style: ds.procLabel
    }, "Indexing \xB7 ", Math.round((doc.progress || 0) * 100), "%")) : /*#__PURE__*/React.createElement(Badge, {
      variant: st.variant,
      dot: st.dot
    }, st.label)), /*#__PURE__*/React.createElement("div", {
      style: ds.cellNum
    }, /*#__PURE__*/React.createElement("span", {
      className: "num",
      style: ds.numVal
    }, doc.chunks ? doc.chunks.toLocaleString() : '—'), /*#__PURE__*/React.createElement("span", {
      style: ds.numLabel
    }, "chunks \xB7 ", doc.pages, " pp")), /*#__PURE__*/React.createElement("div", {
      style: ds.cellDate
    }, /*#__PURE__*/React.createElement("span", {
      style: ds.dateVal
    }, fmtDate(doc.uploaded)), /*#__PURE__*/React.createElement("span", {
      style: ds.ownerRow
    }, /*#__PURE__*/React.createElement(Avatar, {
      name: doc.owner,
      size: "xs"
    }), " ", doc.owner.split(' ')[0])), /*#__PURE__*/React.createElement("div", {
      style: ds.cellActions
    }, doc.status === 'failed' ? /*#__PURE__*/React.createElement(Button, {
      variant: "secondary",
      size: "sm",
      leftIcon: /*#__PURE__*/React.createElement(I.Upload, null)
    }, "Re-upload") : /*#__PURE__*/React.createElement(Tooltip, {
      label: "Ask about this document"
    }, /*#__PURE__*/React.createElement(IconButton, {
      variant: "ghost",
      label: "Ask"
    }, /*#__PURE__*/React.createElement(I.Ask, null))), /*#__PURE__*/React.createElement(IconButton, {
      variant: "ghost",
      label: "More"
    }, /*#__PURE__*/React.createElement(I.Dots, null))));
  }
  function DocumentsScreen() {
    const [tab, setTab] = React.useState('all');
    const [q, setQ] = React.useState('');
    const stats = FX.documentStats;
    const filtered = FX.documents.filter(d => {
      const matchTab = tab === 'all' ? true : tab === 'failed' ? d.status === 'failed' : d.status === tab;
      const matchQ = !q.trim() || (d.name + ' ' + d.kind + ' ' + d.fiscalYear + ' ' + d.id).toLowerCase().includes(q.toLowerCase());
      return matchTab && matchQ;
    });
    const counts = {
      all: FX.documents.length,
      indexed: FX.documents.filter(d => d.status === 'indexed').length,
      processing: FX.documents.filter(d => d.status === 'processing').length,
      failed: FX.documents.filter(d => d.status === 'failed').length
    };
    return /*#__PURE__*/React.createElement("div", {
      style: ds.screen
    }, /*#__PURE__*/React.createElement("div", {
      style: ds.inner
    }, /*#__PURE__*/React.createElement("div", {
      style: ds.head
    }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h1", {
      style: ds.title
    }, "Documents"), /*#__PURE__*/React.createElement("p", {
      style: ds.subtitle
    }, "Filings and reports indexed for grounded retrieval.")), /*#__PURE__*/React.createElement("div", {
      style: ds.headActions
    }, /*#__PURE__*/React.createElement(Button, {
      variant: "secondary",
      leftIcon: /*#__PURE__*/React.createElement(I.Filter, null)
    }, "Filter"), /*#__PURE__*/React.createElement(Button, {
      variant: "primary",
      leftIcon: /*#__PURE__*/React.createElement(I.Upload, null)
    }, "Upload document"))), /*#__PURE__*/React.createElement("div", {
      style: ds.stats
    }, /*#__PURE__*/React.createElement(StatTile, {
      label: "Documents",
      value: String(stats.total)
    }), /*#__PURE__*/React.createElement(StatTile, {
      label: "Indexed",
      value: String(stats.indexed),
      meta: /*#__PURE__*/React.createElement("span", {
        style: {
          color: 'var(--verified-text)'
        }
      }, "Ready to query")
    }), /*#__PURE__*/React.createElement(StatTile, {
      label: "Total chunks",
      value: stats.chunks.toLocaleString()
    }), /*#__PURE__*/React.createElement(StatTile, {
      label: "Processing",
      value: String(stats.processing),
      meta: "\u2248 2 min remaining"
    })), /*#__PURE__*/React.createElement("div", {
      style: ds.toolbar
    }, /*#__PURE__*/React.createElement("div", {
      className: "fr-tabs",
      style: {
        border: 'none'
      }
    }, TABS.map(t => /*#__PURE__*/React.createElement("button", {
      key: t.id,
      className: 'fr-tab' + (tab === t.id ? ' fr-tab--active' : ''),
      onClick: () => setTab(t.id)
    }, t.label, /*#__PURE__*/React.createElement("span", {
      className: "fr-tab__count"
    }, counts[t.id])))), /*#__PURE__*/React.createElement("div", {
      style: {
        width: 260
      }
    }, /*#__PURE__*/React.createElement(Input, {
      icon: /*#__PURE__*/React.createElement(I.Search, null),
      placeholder: "Search documents\u2026",
      value: q,
      onChange: e => setQ(e.target.value)
    }))), /*#__PURE__*/React.createElement("div", {
      style: ds.tableWrap
    }, /*#__PURE__*/React.createElement("div", {
      style: ds.table
    }, /*#__PURE__*/React.createElement("div", {
      style: ds.theadRow
    }, /*#__PURE__*/React.createElement("span", {
      style: ds.cellName
    }, "Document"), /*#__PURE__*/React.createElement("span", {
      style: ds.cellStatus
    }, "Status"), /*#__PURE__*/React.createElement("span", {
      style: ds.cellNum
    }, "Indexed"), /*#__PURE__*/React.createElement("span", {
      style: ds.cellDate
    }, "Uploaded"), /*#__PURE__*/React.createElement("span", {
      style: ds.cellActions
    })), filtered.length === 0 ? /*#__PURE__*/React.createElement(EmptyState, {
      icon: /*#__PURE__*/React.createElement(I.DocSearch, null),
      title: q ? 'No documents match your search' : 'Nothing here yet',
      description: q ? 'Try a different filename, year or document type.' : 'Upload a filing to start asking grounded questions.',
      actions: q ? /*#__PURE__*/React.createElement(Button, {
        variant: "secondary",
        size: "sm",
        onClick: () => setQ('')
      }, "Clear search") : /*#__PURE__*/React.createElement(Button, {
        variant: "primary",
        size: "sm",
        leftIcon: /*#__PURE__*/React.createElement(I.Upload, null)
      }, "Upload document")
    }) : filtered.map(d => /*#__PURE__*/React.createElement(DocRow, {
      key: d.id,
      doc: d
    }))))));
  }
  const ds = {
    screen: {
      flex: 1,
      overflowY: 'auto',
      background: 'var(--surface-page)'
    },
    inner: {
      maxWidth: 'var(--container-max)',
      margin: '0 auto',
      padding: '28px 32px 48px'
    },
    head: {
      display: 'flex',
      alignItems: 'flex-start',
      justifyContent: 'space-between',
      gap: 24,
      marginBottom: 22
    },
    title: {
      fontSize: 'var(--text-2xl)',
      fontWeight: 600,
      letterSpacing: 'var(--tracking-snug)'
    },
    subtitle: {
      fontSize: 'var(--text-sm)',
      color: 'var(--text-secondary)',
      marginTop: 5
    },
    headActions: {
      display: 'flex',
      gap: 8,
      flex: 'none'
    },
    stats: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
      gap: 12,
      marginBottom: 24
    },
    toolbar: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 16,
      marginBottom: 14,
      borderBottom: '1px solid var(--border-subtle)',
      paddingBottom: 12
    },
    table: {
      background: 'var(--surface-card)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-lg)',
      overflow: 'hidden',
      minWidth: 720
    },
    tableWrap: {
      overflowX: 'auto',
      borderRadius: 'var(--radius-lg)'
    },
    theadRow: {
      display: 'grid',
      gridTemplateColumns: 'minmax(200px,1fr) 132px 116px 140px 96px',
      gap: 14,
      padding: '10px 18px',
      borderBottom: '1px solid var(--border-subtle)',
      background: 'var(--surface-sunken)',
      fontSize: 'var(--text-2xs)',
      fontWeight: 600,
      letterSpacing: 'var(--tracking-caps)',
      textTransform: 'uppercase',
      color: 'var(--text-tertiary)'
    },
    row: {
      display: 'grid',
      gridTemplateColumns: 'minmax(200px,1fr) 132px 116px 140px 96px',
      gap: 14,
      padding: '14px 18px',
      borderBottom: '1px solid var(--border-subtle)',
      alignItems: 'center',
      transition: 'background .12s'
    },
    cellName: {
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      minWidth: 0
    },
    fileIcon: {
      width: 36,
      height: 36,
      flex: 'none',
      borderRadius: 'var(--radius-sm)',
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: 18,
      background: 'var(--accent-soft)',
      color: 'var(--accent)',
      border: '1px solid var(--accent-soft-bd)'
    },
    fileIconFail: {
      background: 'var(--danger-soft)',
      color: 'var(--danger)',
      borderColor: 'var(--danger-soft-bd)'
    },
    fileName: {
      fontSize: 'var(--text-sm)',
      fontWeight: 600,
      color: 'var(--text-primary)',
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis'
    },
    fileMeta: {
      display: 'flex',
      alignItems: 'center',
      gap: 7,
      fontSize: 'var(--text-xs)',
      color: 'var(--text-tertiary)',
      marginTop: 2
    },
    metaDot: {
      width: 3,
      height: 3,
      borderRadius: '50%',
      background: 'var(--border-strong)'
    },
    errLine: {
      display: 'flex',
      alignItems: 'center',
      gap: 5,
      marginTop: 5,
      fontSize: 'var(--text-xs)',
      color: 'var(--danger-text)'
    },
    cellStatus: {
      display: 'flex',
      alignItems: 'center'
    },
    procLabel: {
      display: 'block',
      marginTop: 5,
      fontSize: 'var(--text-2xs)',
      color: 'var(--text-tertiary)',
      fontFamily: 'var(--font-mono)'
    },
    cellNum: {
      display: 'flex',
      flexDirection: 'column',
      gap: 1
    },
    numVal: {
      fontSize: 'var(--text-sm)',
      color: 'var(--text-primary)',
      fontWeight: 500
    },
    numLabel: {
      fontSize: 'var(--text-2xs)',
      color: 'var(--text-tertiary)'
    },
    cellDate: {
      display: 'flex',
      flexDirection: 'column',
      gap: 4
    },
    dateVal: {
      fontSize: 'var(--text-sm)',
      color: 'var(--text-primary)'
    },
    ownerRow: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      fontSize: 'var(--text-xs)',
      color: 'var(--text-secondary)'
    },
    cellActions: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'flex-end',
      gap: 4
    }
  };
  window.DocumentsScreen = DocumentsScreen;
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/finrag-app/DocumentsScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/finrag-app/Icons.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/* FinRAG UI kit — shared icons (lucide-style, 24px stroke grid).
   Loaded as a Babel script; components are published on window. */
(function () {
  const S = (paths, props = {}) => p => /*#__PURE__*/React.createElement("svg", _extends({
    viewBox: "0 0 24 24",
    width: "1em",
    height: "1em",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: props.sw || 1.9,
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, p), paths);
  const Icons = {
    Search: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("circle", {
      cx: "11",
      cy: "11",
      r: "7"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M21 21l-4.3-4.3"
    }))),
    Send: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M4 12l16-8-6 16-3-6-7-2z"
    }))),
    ArrowUp: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M12 19V5M6 11l6-6 6 6"
    })), {
      sw: 2.2
    }),
    Plus: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M12 5v14M5 12h14"
    })), {
      sw: 2.1
    }),
    Doc: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M14 3v5h5"
    }))),
    DocSearch: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h6"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M14 3v5h5"
    }), /*#__PURE__*/React.createElement("circle", {
      cx: "17",
      cy: "16",
      r: "3"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M21.5 20.5L19 18"
    }))),
    Lock: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("rect", {
      x: "5",
      y: "11",
      width: "14",
      height: "9",
      rx: "2"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M8 11V8a4 4 0 0 1 8 0v3"
    }))),
    Shield: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M12 3l7 3v6c0 4-3 6.5-7 9-4-2.5-7-5-7-9V6z"
    }))),
    ShieldCheck: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M12 3l7 3v6c0 4-3 6.5-7 9-4-2.5-7-5-7-9V6z"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M9 12l2 2 4-4"
    }))),
    Check: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M5 12.5l4.5 4.5L19 7"
    })), {
      sw: 2.3
    }),
    Copy: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("rect", {
      x: "9",
      y: "9",
      width: "11",
      height: "11",
      rx: "2"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M5 15V5a2 2 0 0 1 2-2h10"
    }))),
    Logout: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M9 21H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M16 17l5-5-5-5"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M21 12H9"
    }))),
    Chevron: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M6 9l6 6 6-6"
    })), {
      sw: 2
    }),
    Sparkle: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"
    }))),
    Mail: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("rect", {
      x: "3",
      y: "5",
      width: "18",
      height: "14",
      rx: "2"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M3 7l9 6 9-6"
    }))),
    Eye: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"
    }), /*#__PURE__*/React.createElement("circle", {
      cx: "12",
      cy: "12",
      r: "3"
    }))),
    Alert: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("circle", {
      cx: "12",
      cy: "12",
      r: "9"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M12 8v5M12 16h.01"
    }))),
    Info: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("circle", {
      cx: "12",
      cy: "12",
      r: "9"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M12 11v5M12 8h.01"
    }))),
    Filter: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M3 5h18l-7 8v5l-4 2v-7z"
    }))),
    Layers: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M12 3l9 5-9 5-9-5z"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M3 13l9 5 9-5"
    }))),
    Upload: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M12 15V4M7 9l5-5 5 5"
    })), {
      sw: 2
    }),
    Ask: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M21 11.5a8.4 8.4 0 0 1-8.5 8.5 8.6 8.6 0 0 1-3.9-.9L3 21l1.9-5.6A8.4 8.4 0 0 1 4 11.5 8.5 8.5 0 0 1 12.5 3 8.4 8.4 0 0 1 21 11.5z"
    }))),
    Users: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("circle", {
      cx: "9",
      cy: "8",
      r: "3.2"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M3 20a6 6 0 0 1 12 0"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M16 5.2a3.2 3.2 0 0 1 0 5.6M21 20a6 6 0 0 0-4-5.6"
    }))),
    Trash: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M4 7h16M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2M6 7l1 13a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-13"
    }))),
    Dots: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("circle", {
      cx: "5",
      cy: "12",
      r: "1.4",
      fill: "currentColor",
      stroke: "none"
    }), /*#__PURE__*/React.createElement("circle", {
      cx: "12",
      cy: "12",
      r: "1.4",
      fill: "currentColor",
      stroke: "none"
    }), /*#__PURE__*/React.createElement("circle", {
      cx: "19",
      cy: "12",
      r: "1.4",
      fill: "currentColor",
      stroke: "none"
    }))),
    Calendar: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("rect", {
      x: "4",
      y: "5",
      width: "16",
      height: "16",
      rx: "2"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M4 9h16M8 3v4M16 3v4"
    }))),
    Building: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("rect", {
      x: "5",
      y: "3",
      width: "14",
      height: "18",
      rx: "1.5"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M9 7h2M13 7h2M9 11h2M13 11h2M9 15h2M13 15h2"
    }))),
    Clock: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("circle", {
      cx: "12",
      cy: "12",
      r: "9"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M12 7v5l3 2"
    }))),
    X: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M6 6l12 12M18 6L6 18"
    })), {
      sw: 2.1
    }),
    ChevRight: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M9 6l6 6-6 6"
    })), {
      sw: 2
    }),
    Pages: S(/*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M8 3h8a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M9 8h6M9 12h6M9 16h3"
    })))
  };
  window.Icons = Icons;
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/finrag-app/Icons.jsx", error: String((e && e.message) || e) }); }

// ui_kits/finrag-app/LoginScreen.jsx
try { (() => {
/* FinRAG UI kit — Screen 1: Login (split brand panel + form). */
(function () {
  const DS = window.FinRAGDesignSystem_2f3924;
  const {
    Field,
    Input,
    Button,
    Banner
  } = DS;
  const I = window.Icons;
  function LoginScreen({
    onSuccess
  }) {
    const [email, setEmail] = React.useState('finance@acme.com');
    const [password, setPassword] = React.useState('');
    const [showPw, setShowPw] = React.useState(false);
    const [error, setError] = React.useState('');
    const [loading, setLoading] = React.useState(false);
    async function submit(e) {
      e.preventDefault();
      setError('');
      setLoading(true);
      try {
        const res = await window.FinRAGAPI.login(email.trim(), password);
        onSuccess(res);
      } catch (err) {
        setError(err.message === 'INVALID_CREDENTIALS' ? 'Invalid email or password. Please try again.' : 'Unable to sign in right now. Check your connection and retry.');
        setLoading(false);
      }
    }
    return /*#__PURE__*/React.createElement("div", {
      style: lg.page
    }, /*#__PURE__*/React.createElement("aside", {
      style: lg.brand
    }, /*#__PURE__*/React.createElement("img", {
      src: "../../assets/logo-wordmark-inverse.svg",
      alt: "FinRAG",
      height: "26"
    }), /*#__PURE__*/React.createElement("div", {
      style: lg.brandBody
    }, /*#__PURE__*/React.createElement("h1", {
      style: lg.brandHead
    }, "Answers your finance team can stand behind."), /*#__PURE__*/React.createElement("p", {
      style: lg.brandSub
    }, "Ask questions across your filings and reports. Every answer is grounded in cited sources \u2014 with chunk-level access controls on sensitive sections."), /*#__PURE__*/React.createElement("ul", {
      style: lg.points
    }, [['ShieldCheck', 'Cited, grounded answers — no unsourced claims'], ['Lock', 'Role-based access down to the document chunk'], ['Layers', 'Built for 10-Ks, annual reports & filings']].map(([icon, text]) => {
      const Ico = I[icon];
      return /*#__PURE__*/React.createElement("li", {
        key: text,
        style: lg.point
      }, /*#__PURE__*/React.createElement("span", {
        style: lg.pointIcon
      }, /*#__PURE__*/React.createElement(Ico, null)), text);
    }))), /*#__PURE__*/React.createElement("div", {
      style: lg.brandFoot
    }, "SOC 2 Type II \xB7 Data encrypted in transit & at rest")), /*#__PURE__*/React.createElement("main", {
      style: lg.formWrap
    }, /*#__PURE__*/React.createElement("form", {
      style: lg.form,
      onSubmit: submit,
      noValidate: true
    }, /*#__PURE__*/React.createElement("div", {
      style: lg.formHead
    }, /*#__PURE__*/React.createElement("h2", {
      style: lg.title
    }, "Sign in"), /*#__PURE__*/React.createElement("p", {
      style: lg.subtitle
    }, "Welcome back. Sign in to your workspace.")), error && /*#__PURE__*/React.createElement(Banner, {
      variant: "danger",
      title: "Sign-in failed"
    }, error), /*#__PURE__*/React.createElement(Field, {
      label: "Work email",
      htmlFor: "email"
    }, /*#__PURE__*/React.createElement(Input, {
      id: "email",
      type: "email",
      autoComplete: "username",
      icon: /*#__PURE__*/React.createElement(I.Mail, null),
      value: email,
      invalid: !!error,
      onChange: e => setEmail(e.target.value),
      placeholder: "you@company.com"
    })), /*#__PURE__*/React.createElement(Field, {
      label: "Password",
      htmlFor: "password"
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        position: 'relative'
      }
    }, /*#__PURE__*/React.createElement(Input, {
      id: "password",
      type: showPw ? 'text' : 'password',
      autoComplete: "current-password",
      value: password,
      invalid: !!error,
      onChange: e => setPassword(e.target.value),
      placeholder: "Enter your password"
    }), /*#__PURE__*/React.createElement("button", {
      type: "button",
      "aria-label": "Toggle password visibility",
      onClick: () => setShowPw(v => !v),
      style: lg.eye
    }, /*#__PURE__*/React.createElement(I.Eye, null)))), /*#__PURE__*/React.createElement("div", {
      style: lg.formRow
    }, /*#__PURE__*/React.createElement("label", {
      style: lg.remember
    }, /*#__PURE__*/React.createElement("input", {
      type: "checkbox",
      style: {
        accentColor: 'var(--accent)'
      },
      defaultChecked: true
    }), " Remember this device"), /*#__PURE__*/React.createElement("a", {
      href: "#",
      style: lg.link,
      onClick: e => e.preventDefault()
    }, "Forgot password?")), /*#__PURE__*/React.createElement(Button, {
      type: "submit",
      variant: "primary",
      size: "lg",
      block: true,
      loading: loading
    }, loading ? 'Signing in' : 'Sign in'), /*#__PURE__*/React.createElement("p", {
      style: lg.demoHint
    }, "Demo \xB7 password ", /*#__PURE__*/React.createElement("code", {
      style: lg.code
    }, "finance2024"), " \xB7 sign in as", /*#__PURE__*/React.createElement("code", {
      style: lg.code
    }, "owner@"), ", ", /*#__PURE__*/React.createElement("code", {
      style: lg.code
    }, "finance@"), ",", /*#__PURE__*/React.createElement("code", {
      style: lg.code
    }, "hr@"), " or ", /*#__PURE__*/React.createElement("code", {
      style: lg.code
    }, "employee@"), " to explore each role.")), /*#__PURE__*/React.createElement("p", {
      style: lg.legal
    }, "Protected workspace. Activity is logged for compliance.")));
  }
  const lg = {
    page: {
      minHeight: '100vh',
      display: 'grid',
      gridTemplateColumns: '1.05fr 1fr',
      background: 'var(--surface-card)'
    },
    brand: {
      background: 'var(--slate-950)',
      color: 'var(--slate-50)',
      padding: '40px 48px',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      backgroundImage: 'radial-gradient(120% 90% at 0% 0%, oklch(0.30 0.05 262) 0%, transparent 55%)'
    },
    brandBody: {
      maxWidth: 420
    },
    brandHead: {
      color: '#fff',
      fontSize: 'var(--text-3xl)',
      lineHeight: 1.18,
      letterSpacing: 'var(--tracking-tight)',
      marginBottom: 16,
      fontWeight: 600
    },
    brandSub: {
      color: 'var(--slate-400)',
      fontSize: 'var(--text-md)',
      lineHeight: 1.6
    },
    points: {
      listStyle: 'none',
      padding: 0,
      margin: '28px 0 0',
      display: 'flex',
      flexDirection: 'column',
      gap: 14
    },
    point: {
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      fontSize: 'var(--text-sm)',
      color: 'var(--slate-200)'
    },
    pointIcon: {
      width: 30,
      height: 30,
      flex: 'none',
      borderRadius: 'var(--radius-sm)',
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: 16,
      background: 'oklch(0.585 0.172 257 / 0.18)',
      color: 'var(--blue-300)',
      border: '1px solid oklch(0.585 0.172 257 / 0.28)'
    },
    brandFoot: {
      fontSize: 'var(--text-xs)',
      color: 'var(--slate-500)',
      fontFamily: 'var(--font-mono)'
    },
    formWrap: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px',
      position: 'relative'
    },
    form: {
      width: '100%',
      maxWidth: 360,
      display: 'flex',
      flexDirection: 'column',
      gap: 18
    },
    formHead: {
      marginBottom: 2
    },
    title: {
      fontSize: 'var(--text-2xl)',
      fontWeight: 600,
      letterSpacing: 'var(--tracking-snug)'
    },
    subtitle: {
      fontSize: 'var(--text-sm)',
      color: 'var(--text-secondary)',
      marginTop: 6
    },
    formRow: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginTop: -4
    },
    remember: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 7,
      fontSize: 'var(--text-sm)',
      color: 'var(--text-secondary)',
      cursor: 'pointer'
    },
    link: {
      fontSize: 'var(--text-sm)',
      color: 'var(--text-link)'
    },
    eye: {
      position: 'absolute',
      right: 8,
      top: '50%',
      transform: 'translateY(-50%)',
      background: 'none',
      border: 'none',
      cursor: 'pointer',
      color: 'var(--text-tertiary)',
      fontSize: 16,
      display: 'inline-flex',
      padding: 6,
      borderRadius: 'var(--radius-xs)'
    },
    demoHint: {
      fontSize: 'var(--text-xs)',
      color: 'var(--text-tertiary)',
      lineHeight: 1.6,
      textAlign: 'center',
      marginTop: 2
    },
    code: {
      fontFamily: 'var(--font-mono)',
      background: 'var(--surface-sunken)',
      padding: '1px 5px',
      borderRadius: 4,
      margin: '0 3px',
      color: 'var(--text-secondary)',
      fontSize: '0.92em'
    },
    legal: {
      position: 'absolute',
      bottom: 24,
      fontSize: 'var(--text-xs)',
      color: 'var(--text-tertiary)'
    }
  };
  window.LoginScreen = LoginScreen;
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/finrag-app/LoginScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/finrag-app/NavSidebar.jsx
try { (() => {
/* FinRAG UI kit — left navigation rail (app shell).
   Owner-only items are gated by `role`. */
(function () {
  const I = window.Icons;
  function NavItem({
    icon,
    label,
    active,
    onClick
  }) {
    const Ico = icon;
    return /*#__PURE__*/React.createElement("button", {
      type: "button",
      onClick: onClick,
      style: {
        ...nv.item,
        ...(active ? nv.itemActive : null)
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        ...nv.itemIcon,
        color: active ? 'var(--accent)' : 'var(--text-tertiary)'
      }
    }, /*#__PURE__*/React.createElement(Ico, null)), label);
  }
  function NavSidebar({
    view,
    onNavigate,
    role
  }) {
    const isOwner = role === 'owner';
    return /*#__PURE__*/React.createElement("nav", {
      style: nv.bar
    }, /*#__PURE__*/React.createElement("div", {
      style: nv.group
    }, /*#__PURE__*/React.createElement("span", {
      style: nv.groupLabel
    }, "Workspace"), /*#__PURE__*/React.createElement(NavItem, {
      icon: I.Ask,
      label: "Ask",
      active: view === 'ask',
      onClick: () => onNavigate('ask')
    }), /*#__PURE__*/React.createElement(NavItem, {
      icon: I.Doc,
      label: "Documents",
      active: view === 'docs',
      onClick: () => onNavigate('docs')
    })), isOwner && /*#__PURE__*/React.createElement("div", {
      style: nv.group
    }, /*#__PURE__*/React.createElement("span", {
      style: nv.groupLabel
    }, "Administration"), /*#__PURE__*/React.createElement(NavItem, {
      icon: I.Shield,
      label: "Access control",
      active: view === 'admin',
      onClick: () => onNavigate('admin')
    }), /*#__PURE__*/React.createElement(NavItem, {
      icon: I.Users,
      label: "Members",
      active: view === 'members',
      onClick: () => onNavigate('admin')
    })), /*#__PURE__*/React.createElement("div", {
      style: nv.spacer
    }), /*#__PURE__*/React.createElement("div", {
      style: nv.helpCard
    }, /*#__PURE__*/React.createElement("span", {
      style: nv.helpIcon
    }, /*#__PURE__*/React.createElement(I.ShieldCheck, null)), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
      style: nv.helpTitle
    }, "Grounded-only"), /*#__PURE__*/React.createElement("p", {
      style: nv.helpText
    }, "Every answer is backed by a cited source you\u2019re authorized to see."))));
  }
  const nv = {
    bar: {
      width: 'var(--sidebar-width)',
      flex: 'none',
      background: 'var(--surface-card)',
      borderRight: '1px solid var(--border-subtle)',
      padding: '16px 12px',
      display: 'flex',
      flexDirection: 'column',
      gap: 18,
      height: '100%',
      overflowY: 'auto'
    },
    group: {
      display: 'flex',
      flexDirection: 'column',
      gap: 2
    },
    groupLabel: {
      fontSize: 'var(--text-2xs)',
      fontWeight: 600,
      letterSpacing: 'var(--tracking-caps)',
      textTransform: 'uppercase',
      color: 'var(--text-tertiary)',
      padding: '4px 10px 6px'
    },
    item: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      width: '100%',
      textAlign: 'left',
      padding: '8px 10px',
      borderRadius: 'var(--radius-sm)',
      border: '1px solid transparent',
      background: 'none',
      cursor: 'pointer',
      font: 'inherit',
      fontSize: 'var(--text-sm)',
      fontWeight: 500,
      color: 'var(--text-secondary)',
      transition: 'background .12s, color .12s'
    },
    itemActive: {
      background: 'var(--accent-soft)',
      color: 'var(--accent-text)',
      borderColor: 'var(--accent-soft-bd)'
    },
    itemIcon: {
      fontSize: 17,
      display: 'inline-flex',
      flex: 'none'
    },
    spacer: {
      flex: 1
    },
    helpCard: {
      display: 'flex',
      gap: 9,
      padding: '12px',
      borderRadius: 'var(--radius-md)',
      background: 'var(--verified-soft)',
      border: '1px solid var(--verified-soft-bd)'
    },
    helpIcon: {
      fontSize: 16,
      color: 'var(--verified)',
      display: 'inline-flex',
      flex: 'none',
      marginTop: 1
    },
    helpTitle: {
      fontSize: 'var(--text-xs)',
      fontWeight: 600,
      color: 'var(--verified-text)',
      marginBottom: 2
    },
    helpText: {
      fontSize: 'var(--text-xs)',
      color: 'var(--verified-text)',
      opacity: 0.85,
      lineHeight: 1.45,
      margin: 0
    }
  };
  window.NavSidebar = NavSidebar;
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/finrag-app/NavSidebar.jsx", error: String((e && e.message) || e) }); }

// ui_kits/finrag-app/QueryScreen.jsx
try { (() => {
/* FinRAG UI kit — Screen 2 (HERO): cited-answer query interface.
   States: idle · generating · answer-with-citations · no-authorized-context. */
(function () {
  const DS = window.FinRAGDesignSystem_2f3924;
  const {
    Citation,
    SourceCard,
    ConfidenceMeter,
    Button,
    IconButton,
    Badge,
    EmptyState
  } = DS;
  const I = window.Icons;
  const FX = window.FINRAG_FIXTURES;

  /* ---- Ask bar -------------------------------------------------- */
  function AskBar({
    value,
    onChange,
    onSubmit,
    busy
  }) {
    return /*#__PURE__*/React.createElement("form", {
      style: qs.askForm,
      onSubmit: e => {
        e.preventDefault();
        onSubmit();
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: qs.askIcon
    }, /*#__PURE__*/React.createElement(I.DocSearch, null)), /*#__PURE__*/React.createElement("input", {
      style: qs.askInput,
      value: value,
      disabled: busy,
      onChange: e => onChange(e.target.value),
      placeholder: "Ask a question about your financial documents\u2026",
      "aria-label": "Ask a question"
    }), /*#__PURE__*/React.createElement(Button, {
      type: "submit",
      variant: "primary",
      loading: busy,
      disabled: !value.trim(),
      rightIcon: !busy && /*#__PURE__*/React.createElement(I.ArrowUp, null)
    }, busy ? 'Searching' : 'Ask'));
  }

  /* ---- Answer body with inline citations ------------------------ */
  function AnswerBody({
    result,
    activeRef,
    onCite
  }) {
    return /*#__PURE__*/React.createElement("p", {
      style: qs.answerText
    }, result.segments.map((seg, i) => {
      if (seg.sourceRef != null) {
        const active = activeRef === seg.sourceRef;
        return /*#__PURE__*/React.createElement(React.Fragment, {
          key: i
        }, /*#__PURE__*/React.createElement("span", {
          className: active ? 'fr-grounded-text fr-grounded-text--active' : 'fr-grounded-text'
        }, seg.text), /*#__PURE__*/React.createElement(Citation, {
          index: seg.sourceRef,
          active: active,
          onClick: () => onCite(seg.sourceRef)
        }));
      }
      return /*#__PURE__*/React.createElement(React.Fragment, {
        key: i
      }, seg.text);
    }));
  }

  /* ---- Main screen ---------------------------------------------- */
  function QueryScreen({
    session
  }) {
    const [question, setQuestion] = React.useState('');
    const [status, setStatus] = React.useState('idle'); // idle|loading|answer|nocontext|error
    const [result, setResult] = React.useState(null);
    const [asked, setAsked] = React.useState('');
    const [activeRef, setActiveRef] = React.useState(null);
    const sourceRefs = React.useRef({});
    const panelRef = React.useRef(null);
    async function ask(q) {
      const text = (q ?? question).trim();
      if (!text) return;
      setAsked(text);
      setQuestion(text);
      setStatus('loading');
      setResult(null);
      setActiveRef(null);
      try {
        const res = await window.FinRAGAPI.query(text, {
          token: session.token,
          role: session.role
        });
        if (res && res.noContext) {
          setStatus('nocontext');
          return;
        }
        setResult(res);
        setStatus('answer');
        setActiveRef(res.sources?.[0]?.ref ?? null);
      } catch (e) {
        setStatus('error');
      }
    }
    function focusSource(ref) {
      setActiveRef(ref);
      const el = sourceRefs.current[ref];
      const panel = panelRef.current;
      if (el && panel) panel.scrollTo({
        top: el.offsetTop - 12,
        behavior: 'smooth'
      });
    }
    const authorizedSources = result?.sources || [];
    return /*#__PURE__*/React.createElement("div", {
      style: qs.screen
    }, /*#__PURE__*/React.createElement("div", {
      style: qs.askWrap
    }, /*#__PURE__*/React.createElement("div", {
      style: qs.askInner
    }, /*#__PURE__*/React.createElement(AskBar, {
      value: question,
      onChange: setQuestion,
      onSubmit: () => ask(),
      busy: status === 'loading'
    }))), /*#__PURE__*/React.createElement("div", {
      style: qs.body
    }, status === 'idle' && /*#__PURE__*/React.createElement(IdleState, {
      onPick: q => ask(q)
    }), status === 'loading' && /*#__PURE__*/React.createElement(LoadingState, {
      question: asked
    }), status === 'error' && /*#__PURE__*/React.createElement(ErrorState, {
      onRetry: () => ask(asked)
    }), status === 'nocontext' && /*#__PURE__*/React.createElement(NoContextState, {
      question: asked
    }), status === 'answer' && result && /*#__PURE__*/React.createElement("div", {
      style: qs.answerGrid
    }, /*#__PURE__*/React.createElement("section", {
      style: qs.answerCol
    }, /*#__PURE__*/React.createElement("div", {
      style: qs.qEcho
    }, /*#__PURE__*/React.createElement("span", {
      style: qs.qLabel
    }, "Question"), /*#__PURE__*/React.createElement("span", {
      style: qs.qText
    }, asked)), /*#__PURE__*/React.createElement("div", {
      style: qs.answerHead
    }, /*#__PURE__*/React.createElement("span", {
      style: qs.answerEyebrow
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        display: 'inline-flex',
        fontSize: 14,
        color: 'var(--verified)'
      }
    }, /*#__PURE__*/React.createElement(I.ShieldCheck, null)), " Grounded answer"), /*#__PURE__*/React.createElement(ConfidenceMeter, {
      value: result.grounding,
      label: "Grounding"
    })), /*#__PURE__*/React.createElement(AnswerBody, {
      result: result,
      activeRef: activeRef,
      onCite: focusSource
    }), /*#__PURE__*/React.createElement("div", {
      style: qs.legend
    }, /*#__PURE__*/React.createElement("span", {
      style: qs.legendItem
    }, /*#__PURE__*/React.createElement("span", {
      className: "fr-grounded-text",
      style: {
        padding: '0 4px'
      }
    }, "highlighted text"), " is backed by its cited source \u2014 every claim is grounded")), /*#__PURE__*/React.createElement("div", {
      style: qs.actions
    }, /*#__PURE__*/React.createElement(Button, {
      variant: "secondary",
      size: "sm",
      leftIcon: /*#__PURE__*/React.createElement(I.Copy, null)
    }, "Copy with citations"), /*#__PURE__*/React.createElement(Button, {
      variant: "ghost",
      size: "sm",
      leftIcon: /*#__PURE__*/React.createElement(I.Plus, null)
    }, "Ask a follow-up"))), /*#__PURE__*/React.createElement("aside", {
      style: qs.sourcesCol,
      ref: panelRef
    }, /*#__PURE__*/React.createElement("div", {
      style: qs.sourcesHead
    }, /*#__PURE__*/React.createElement("span", {
      style: qs.sourcesTitle
    }, "Sources"), /*#__PURE__*/React.createElement(Badge, {
      variant: "neutral",
      mono: true
    }, authorizedSources.length)), /*#__PURE__*/React.createElement("div", {
      style: qs.sourcesList
    }, result.sources.map(s => /*#__PURE__*/React.createElement("div", {
      key: s.ref,
      ref: el => sourceRefs.current[s.ref] = el
    }, /*#__PURE__*/React.createElement(SourceCard, {
      refIndex: s.ref,
      docName: s.docName,
      page: s.page,
      score: s.score,
      excerpt: s.excerpt,
      access: s.access,
      active: activeRef === s.ref,
      onClick: () => focusSource(s.ref)
    })))), /*#__PURE__*/React.createElement("p", {
      style: qs.sourcesFoot
    }, "Sources reflect your access role. Sections outside your permissions are not used to answer.")))));
  }

  /* ---- State views ---------------------------------------------- */
  function IdleState({
    onPick
  }) {
    return /*#__PURE__*/React.createElement("div", {
      style: qs.centerWrap
    }, /*#__PURE__*/React.createElement("div", {
      style: qs.idleCard
    }, /*#__PURE__*/React.createElement("span", {
      style: qs.idleIcon
    }, /*#__PURE__*/React.createElement(I.Sparkle, null)), /*#__PURE__*/React.createElement("h2", {
      style: qs.idleTitle
    }, "Ask anything about your documents"), /*#__PURE__*/React.createElement("p", {
      style: qs.idleSub
    }, "Every answer is grounded in cited sources from your indexed filings \u2014 and respects your access role."), /*#__PURE__*/React.createElement("div", {
      style: qs.suggest
    }, FX.suggestedQuestions.map(q => /*#__PURE__*/React.createElement("button", {
      key: q,
      type: "button",
      style: qs.chip,
      onClick: () => onPick(q)
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        display: 'inline-flex',
        fontSize: 14,
        color: 'var(--text-tertiary)'
      }
    }, /*#__PURE__*/React.createElement(I.Search, null)), q)))));
  }
  function LoadingState({
    question
  }) {
    const steps = ['Retrieving authorized sources', 'Ranking relevant chunks', 'Grounding the answer'];
    const [step, setStep] = React.useState(0);
    React.useEffect(() => {
      const t = setInterval(() => setStep(s => Math.min(s + 1, steps.length - 1)), 450);
      return () => clearInterval(t);
    }, []);
    return /*#__PURE__*/React.createElement("div", {
      style: qs.answerGrid
    }, /*#__PURE__*/React.createElement("section", {
      style: qs.answerCol
    }, /*#__PURE__*/React.createElement("div", {
      style: qs.qEcho
    }, /*#__PURE__*/React.createElement("span", {
      style: qs.qLabel
    }, "Question"), /*#__PURE__*/React.createElement("span", {
      style: qs.qText
    }, question)), /*#__PURE__*/React.createElement("div", {
      style: qs.loadSteps
    }, steps.map((s, i) => /*#__PURE__*/React.createElement("div", {
      key: s,
      style: {
        ...qs.loadStep,
        opacity: i <= step ? 1 : 0.4
      }
    }, i < step ? /*#__PURE__*/React.createElement("span", {
      style: qs.loadDone
    }, /*#__PURE__*/React.createElement(I.Check, null)) : i === step ? /*#__PURE__*/React.createElement("span", {
      className: "fr-spinner fr-spinner--sm"
    }) : /*#__PURE__*/React.createElement("span", {
      style: qs.loadPending
    }), s))), /*#__PURE__*/React.createElement("div", {
      style: qs.skeletonWrap
    }, [100, 96, 88, 70].map((w, i) => /*#__PURE__*/React.createElement("div", {
      key: i,
      style: {
        ...qs.skel,
        width: w + '%'
      }
    })))), /*#__PURE__*/React.createElement("aside", {
      style: qs.sourcesCol
    }, /*#__PURE__*/React.createElement("div", {
      style: qs.sourcesHead
    }, /*#__PURE__*/React.createElement("span", {
      style: qs.sourcesTitle
    }, "Sources")), /*#__PURE__*/React.createElement("div", {
      style: qs.sourcesList
    }, [0, 1, 2].map(i => /*#__PURE__*/React.createElement("div", {
      key: i,
      style: qs.skelCard
    })))));
  }
  function NoContextState({
    question
  }) {
    return /*#__PURE__*/React.createElement("div", {
      style: qs.centerWrap
    }, /*#__PURE__*/React.createElement(EmptyState, {
      icon: /*#__PURE__*/React.createElement(I.DocSearch, null),
      title: "No authorized sources answer this question",
      description: "We couldn\u2019t find anything in the documents you\u2019re authorized to view that answers this. Try rephrasing, or check with a workspace owner if you expect access to more sources.",
      actions: /*#__PURE__*/React.createElement(Button, {
        variant: "secondary",
        size: "sm",
        leftIcon: /*#__PURE__*/React.createElement(I.Plus, null)
      }, "Ask a different question")
    }), /*#__PURE__*/React.createElement("p", {
      style: qs.noCtxQuote
    }, "\u201C", question, "\u201D"));
  }
  function ErrorState({
    onRetry
  }) {
    return /*#__PURE__*/React.createElement("div", {
      style: qs.centerWrap
    }, /*#__PURE__*/React.createElement(EmptyState, {
      icon: /*#__PURE__*/React.createElement(I.Alert, null),
      title: "Something went wrong",
      description: "We couldn\u2019t complete that request. Please try again.",
      actions: /*#__PURE__*/React.createElement(Button, {
        variant: "primary",
        size: "sm",
        onClick: onRetry
      }, "Retry")
    }));
  }

  /* ---- Styles --------------------------------------------------- */
  const qs = {
    screen: {
      height: '100%',
      minHeight: 0,
      display: 'flex',
      flexDirection: 'column',
      background: 'var(--surface-page)'
    },
    askWrap: {
      borderBottom: '1px solid var(--border-subtle)',
      background: 'var(--surface-card)',
      padding: '14px 24px'
    },
    askInner: {
      maxWidth: 'var(--container-max)',
      margin: '0 auto',
      width: '100%'
    },
    askForm: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      position: 'relative'
    },
    askIcon: {
      position: 'absolute',
      left: 13,
      fontSize: 18,
      color: 'var(--text-tertiary)',
      display: 'inline-flex',
      pointerEvents: 'none'
    },
    askInput: {
      flex: 1,
      height: 44,
      padding: '0 14px 0 40px',
      fontSize: 'var(--text-md)',
      fontFamily: 'var(--font-sans)',
      color: 'var(--text-primary)',
      background: 'var(--surface-card)',
      border: '1px solid var(--border-default)',
      borderRadius: 'var(--radius-md)',
      outline: 'none'
    },
    body: {
      flex: 1,
      overflow: 'hidden',
      display: 'flex'
    },
    answerGrid: {
      maxWidth: 'var(--container-max)',
      margin: '0 auto',
      width: '100%',
      display: 'grid',
      gridTemplateColumns: 'minmax(0,1fr) var(--source-panel-w)',
      gap: 0,
      height: '100%'
    },
    answerCol: {
      overflowY: 'auto',
      padding: '32px 40px',
      borderRight: '1px solid var(--border-subtle)'
    },
    qEcho: {
      display: 'flex',
      flexDirection: 'column',
      gap: 5,
      paddingBottom: 18,
      marginBottom: 22,
      borderBottom: '1px solid var(--border-subtle)'
    },
    qLabel: {
      fontSize: 'var(--text-2xs)',
      fontWeight: 600,
      letterSpacing: 'var(--tracking-caps)',
      textTransform: 'uppercase',
      color: 'var(--text-tertiary)'
    },
    qText: {
      fontSize: 'var(--text-xl)',
      fontWeight: 600,
      color: 'var(--text-primary)',
      letterSpacing: 'var(--tracking-snug)',
      lineHeight: 1.3
    },
    answerHead: {
      display: 'flex',
      alignItems: 'flex-end',
      justifyContent: 'space-between',
      gap: 24,
      marginBottom: 16
    },
    answerEyebrow: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 7,
      fontSize: 'var(--text-xs)',
      fontWeight: 600,
      letterSpacing: 'var(--tracking-wide)',
      textTransform: 'uppercase',
      color: 'var(--verified-text)'
    },
    answerText: {
      fontSize: 'var(--text-lg)',
      lineHeight: 1.75,
      color: 'var(--text-primary)',
      maxWidth: 'var(--content-max)'
    },
    legend: {
      display: 'flex',
      alignItems: 'center',
      gap: 14,
      marginTop: 24,
      padding: '10px 14px',
      background: 'var(--surface-sunken)',
      borderRadius: 'var(--radius-md)',
      fontSize: 'var(--text-xs)',
      color: 'var(--text-secondary)',
      flexWrap: 'wrap'
    },
    legendItem: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6
    },
    actions: {
      display: 'flex',
      gap: 8,
      marginTop: 22
    },
    sourcesCol: {
      overflowY: 'auto',
      padding: '24px 20px',
      background: 'var(--surface-card)',
      position: 'relative'
    },
    sourcesHead: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      marginBottom: 14,
      position: 'sticky',
      top: 0
    },
    sourcesTitle: {
      fontSize: 'var(--text-sm)',
      fontWeight: 600,
      color: 'var(--text-primary)',
      letterSpacing: 'var(--tracking-snug)'
    },
    sourcesList: {
      display: 'flex',
      flexDirection: 'column',
      gap: 10
    },
    sourcesFoot: {
      marginTop: 18,
      fontSize: 'var(--text-xs)',
      color: 'var(--text-tertiary)',
      lineHeight: 1.5,
      paddingTop: 14,
      borderTop: '1px solid var(--border-subtle)'
    },
    centerWrap: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      overflowY: 'auto'
    },
    idleCard: {
      maxWidth: 620,
      textAlign: 'center',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center'
    },
    idleIcon: {
      width: 52,
      height: 52,
      borderRadius: 'var(--radius-lg)',
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: 24,
      color: 'var(--accent)',
      background: 'var(--accent-soft)',
      border: '1px solid var(--accent-soft-bd)',
      marginBottom: 18
    },
    idleTitle: {
      fontSize: 'var(--text-2xl)',
      fontWeight: 600,
      letterSpacing: 'var(--tracking-snug)'
    },
    idleSub: {
      fontSize: 'var(--text-md)',
      color: 'var(--text-secondary)',
      marginTop: 10,
      lineHeight: 1.6,
      maxWidth: 480
    },
    suggest: {
      display: 'flex',
      flexDirection: 'column',
      gap: 8,
      marginTop: 26,
      width: '100%',
      maxWidth: 480
    },
    chip: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      textAlign: 'left',
      width: '100%',
      cursor: 'pointer',
      padding: '11px 14px',
      background: 'var(--surface-card)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-md)',
      fontSize: 'var(--text-sm)',
      color: 'var(--text-primary)',
      font: 'inherit',
      boxShadow: 'var(--shadow-xs)'
    },
    loadSteps: {
      display: 'flex',
      flexDirection: 'column',
      gap: 12,
      marginBottom: 26
    },
    loadStep: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      fontSize: 'var(--text-sm)',
      color: 'var(--text-secondary)',
      transition: 'opacity .2s'
    },
    loadDone: {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: 16,
      height: 16,
      borderRadius: '50%',
      background: 'var(--verified)',
      color: '#fff',
      fontSize: 11
    },
    loadPending: {
      width: 14,
      height: 14,
      borderRadius: '50%',
      border: '2px solid var(--border-default)'
    },
    skeletonWrap: {
      display: 'flex',
      flexDirection: 'column',
      gap: 12
    },
    skel: {
      height: 14,
      borderRadius: 5,
      background: 'linear-gradient(90deg, var(--slate-150) 25%, var(--slate-100) 37%, var(--slate-150) 63%)',
      backgroundSize: '400% 100%',
      animation: 'frShimmer 1.4s ease infinite'
    },
    skelCard: {
      height: 92,
      borderRadius: 'var(--radius-md)',
      background: 'linear-gradient(90deg, var(--slate-150) 25%, var(--slate-100) 37%, var(--slate-150) 63%)',
      backgroundSize: '400% 100%',
      animation: 'frShimmer 1.4s ease infinite'
    },
    noCtxQuote: {
      marginTop: 4,
      fontFamily: 'var(--font-serif)',
      fontStyle: 'italic',
      color: 'var(--text-tertiary)',
      fontSize: 'var(--text-sm)',
      maxWidth: 420,
      textAlign: 'center'
    }
  };
  window.QueryScreen = QueryScreen;
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/finrag-app/QueryScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/finrag-app/api.js
try { (() => {
/* ============================================================
   FinRAG — API client
   Thin wrapper over the configurable backend. Every call targets
   FINRAG_CONFIG.apiBaseUrl + endpoint; on network failure (or when
   no backend is running) it falls back to bundled fixtures so the
   prototype stays interactive. Swap-in real backend by setting
   window.FINRAG_API_BASE — no call-site changes required.
   ============================================================ */
(function () {
  const cfg = window.FINRAG_CONFIG;
  const fx = window.FINRAG_FIXTURES;
  function url(path) {
    return cfg.apiBaseUrl.replace(/\/$/, '') + path;
  }
  async function postJSON(path, body) {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), cfg.timeoutMs);
    try {
      const res = await fetch(url(path), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body),
        signal: ctrl.signal
      });
      clearTimeout(t);
      if (!res.ok) {
        const err = new Error('HTTP ' + res.status);
        err.status = res.status;
        throw err;
      }
      return await res.json();
    } catch (e) {
      clearTimeout(t);
      e.isNetwork = !e.status;
      throw e;
    }
  }

  // --- Auth -------------------------------------------------------
  async function login(email, password) {
    try {
      return await postJSON(cfg.endpoints.login, {
        email,
        password
      });
    } catch (e) {
      if (e.status === 401) throw new Error('INVALID_CREDENTIALS');
      if (e.isNetwork && cfg.allowMockFallback) return mockLogin(email, password);
      throw e;
    }
  }
  function roleFromEmail(email) {
    const local = (email.split('@')[0] || '').toLowerCase();
    if (/owner|admin/.test(local)) return 'owner';
    if (/finance|cfo/.test(local)) return 'finance';
    if (/^hr|people/.test(local)) return 'hr';
    if (/employee|staff/.test(local)) return 'employee';
    return 'finance'; // default demo role
  }
  function mockLogin(email, password) {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const ok = /\S+@\S+\.\S+/.test(email) && password === fx.demoPassword;
        if (!ok) return reject(new Error('INVALID_CREDENTIALS'));
        // Role derived from the local-part for the demo: owner / finance / hr / employee.
        const role = roleFromEmail(email);
        resolve({
          token: 'demo.' + btoa(email),
          role,
          email
        });
      }, 650);
    });
  }

  // --- Query ------------------------------------------------------
  async function query(question, {
    token,
    role
  } = {}) {
    try {
      return await postJSON(cfg.endpoints.query, {
        question
      }, token);
    } catch (e) {
      if (e.isNetwork && cfg.allowMockFallback) return mockQuery(question, role);
      throw e;
    }
  }
  function mockQuery(question, role) {
    return new Promise(resolve => {
      const q = (question || '').toLowerCase();
      const canSeeRestricted = role === 'owner' || role === 'finance';
      let payload;
      if (/salary|salaries|compensation|comp\b|executive pay|bonus/.test(q)) {
        // Restricted section: only owner + finance retrieve it. For hr /
        // employee the chunks never enter context — graceful no-context.
        payload = canSeeRestricted ? fx.answers.compensation : fx.noContext;
      } else if (/revenue|segment|sales|top line/.test(q)) {
        payload = fx.answers.revenue;
      } else {
        payload = fx.answers.margin;
      }
      // simulate retrieval + generation latency
      setTimeout(() => resolve(payload), 1400);
    });
  }
  window.FinRAGAPI = {
    login,
    query
  };
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/finrag-app/api.js", error: String((e && e.message) || e) }); }

// ui_kits/finrag-app/config.js
try { (() => {
/* ============================================================
   FinRAG — runtime config
   The API base URL is configurable (env / injected global), never
   hardcoded at call sites. A real FastAPI backend can be pointed
   to by setting window.FINRAG_API_BASE before this script loads,
   e.g. <script>window.FINRAG_API_BASE="https://api.acme.com"</script>
   ============================================================ */
window.FINRAG_CONFIG = {
  // Base URL of the FinRAG FastAPI backend.
  apiBaseUrl: typeof window !== 'undefined' && window.FINRAG_API_BASE || 'http://localhost:8000',
  // Endpoint paths (relative to apiBaseUrl).
  endpoints: {
    login: '/auth/login',
    query: '/query'
  },
  // When the backend is unreachable, fall back to bundled fixtures so
  // the prototype stays interactive. Set false to require a live API.
  allowMockFallback: true,
  // Request timeout (ms) before falling back / erroring.
  timeoutMs: 8000
};
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/finrag-app/config.js", error: String((e && e.message) || e) }); }

// ui_kits/finrag-app/mockData.js
try { (() => {
/* ============================================================
   FinRAG — fixtures (prototype fallback data)
   Mirrors the shape returned by the FastAPI backend so screens
   render identically whether data is live or mocked.
   ============================================================ */
window.FINRAG_FIXTURES = {
  // Demo credential used by the mock login path.
  demoPassword: 'finance2024',
  // Sample questions surfaced on the idle query screen.
  suggestedQuestions: ['What was operating margin in FY2024 and how did it change?', 'Summarize the key liquidity risks disclosed in the latest 10-K.', 'What were total revenues for fiscal 2024 by segment?', 'What are executive base salaries for FY2024?' // -> no authorized context for the finance role
  ],
  // Keyed canned responses. Any other question maps to `default`.
  answers: {
    margin: {
      question: 'What was operating margin in FY2024 and how did it change?',
      grounding: 0.94,
      segments: [{
        text: 'Operating margin reached '
      }, {
        text: '24.1% in fiscal 2024',
        sourceRef: 1
      }, {
        text: ', up from '
      }, {
        text: '21.8% in the prior fiscal year',
        sourceRef: 2
      }, {
        text: '. The improvement was driven primarily by '
      }, {
        text: 'operating leverage on higher revenue and disciplined operating expense growth',
        sourceRef: 1
      }, {
        text: '. Gross margin also expanded '
      }, {
        text: '60 basis points to 71.4%',
        sourceRef: 3
      }, {
        text: '.'
      }],
      sources: [{
        ref: 1,
        docName: 'FY2024_10-K.pdf',
        page: 42,
        score: 0.94,
        access: 'granted',
        excerpt: 'Operating margin was <mark>24.1%</mark> for fiscal 2024, compared with 21.8% in the prior fiscal year, reflecting <mark>operating leverage on higher revenue</mark> and disciplined operating expense growth.'
      }, {
        ref: 2,
        docName: 'FY2023_10-K.pdf',
        page: 39,
        score: 0.89,
        access: 'granted',
        excerpt: 'Operating margin of <mark>21.8%</mark> in fiscal 2023 reflected continued investment in research and development and go-to-market capacity.'
      }, {
        ref: 3,
        docName: 'FY2024_10-K.pdf',
        page: 41,
        score: 0.86,
        access: 'granted',
        excerpt: 'Gross margin expanded <mark>60 basis points to 71.4%</mark>, driven by infrastructure efficiency and favorable revenue mix.'
      }]
    },
    revenue: {
      question: 'What were total revenues for fiscal 2024 by segment?',
      grounding: 0.91,
      segments: [{
        text: 'Total revenue for fiscal 2024 was '
      }, {
        text: '$8.42 billion',
        sourceRef: 1
      }, {
        text: ', an increase of '
      }, {
        text: '14% year over year',
        sourceRef: 1
      }, {
        text: '. By segment, Platform contributed '
      }, {
        text: '$5.91 billion and Services $2.51 billion',
        sourceRef: 2
      }, {
        text: '.'
      }],
      sources: [{
        ref: 1,
        docName: 'FY2024_10-K.pdf',
        page: 56,
        score: 0.93,
        access: 'granted',
        excerpt: 'Total revenue was <mark>$8,421 million</mark> for fiscal 2024, an increase of <mark>14%</mark> compared with the prior year.'
      }, {
        ref: 2,
        docName: 'FY2024_10-K.pdf',
        page: 57,
        score: 0.9,
        access: 'granted',
        excerpt: 'Platform revenue was <mark>$5,908 million</mark> and Services revenue was <mark>$2,513 million</mark> for fiscal 2024.'
      }]
    },
    // Authorized ONLY for owner + finance. hr / employee get `noContext`
    // for the same question — the restricted chunks never enter their context.
    compensation: {
      question: 'What are executive base salaries for FY2024?',
      grounding: 0.96,
      segments: [{
        text: 'For fiscal 2024, the CEO base salary was '
      }, {
        text: '$1.20 million',
        sourceRef: 1
      }, {
        text: ', and the named executive officers received base salaries totaling '
      }, {
        text: '$4.85 million',
        sourceRef: 1
      }, {
        text: '. Annual cash incentives are tied to '
      }, {
        text: 'operating margin and revenue growth targets',
        sourceRef: 2
      }, {
        text: '.'
      }],
      sources: [{
        ref: 1,
        docName: 'FY2024_Proxy_Statement.pdf',
        page: 34,
        score: 0.95,
        access: 'restricted',
        excerpt: "The Chief Executive Officer's base salary was <mark>$1,200,000</mark> for fiscal 2024; aggregate base salary for named executive officers was <mark>$4,850,000</mark>."
      }, {
        ref: 2,
        docName: 'FY2024_Proxy_Statement.pdf',
        page: 36,
        score: 0.9,
        access: 'restricted',
        excerpt: 'Annual incentive awards are determined by performance against <mark>operating margin and revenue growth</mark> targets approved by the committee.'
      }]
    }
  },
  // Returned when a question only matches sources the role can't access.
  noContext: {
    noContext: true
  },
  // ---- Document library (dashboard) -----------------------------
  documents: [{
    id: 'DOC-10K-2024-0481',
    name: 'FY2024_10-K.pdf',
    kind: '10-K',
    fiscalYear: 'FY2024',
    status: 'indexed',
    pages: 184,
    chunks: 482,
    sizeMb: 4.8,
    uploaded: '2026-05-28',
    owner: 'Dana Whitfield'
  }, {
    id: 'DOC-10K-2023-0377',
    name: 'FY2023_10-K.pdf',
    kind: '10-K',
    fiscalYear: 'FY2023',
    status: 'indexed',
    pages: 176,
    chunks: 451,
    sizeMb: 4.5,
    uploaded: '2026-05-28',
    owner: 'Dana Whitfield'
  }, {
    id: 'DOC-AR-2024-0512',
    name: 'FY2024_Annual_Report.pdf',
    kind: 'Annual report',
    fiscalYear: 'FY2024',
    status: 'indexed',
    pages: 96,
    chunks: 268,
    sizeMb: 12.1,
    uploaded: '2026-06-02',
    owner: 'Marcus Cole'
  }, {
    id: 'DOC-10Q-2025Q1-0588',
    name: 'FY2025_Q1_10-Q.pdf',
    kind: '10-Q',
    fiscalYear: 'FY2025',
    status: 'processing',
    progress: 0.62,
    pages: 58,
    chunks: 112,
    sizeMb: 2.2,
    uploaded: '2026-06-13',
    owner: 'Priya Nair'
  }, {
    id: 'DOC-PROXY-2024-0490',
    name: 'FY2024_Proxy_Statement.pdf',
    kind: 'Proxy',
    fiscalYear: 'FY2024',
    status: 'indexed',
    pages: 72,
    chunks: 198,
    sizeMb: 3.4,
    uploaded: '2026-06-01',
    owner: 'Dana Whitfield'
  }, {
    id: 'DOC-MDA-2024-0466',
    name: 'FY2024_MD&A_Supplement.pdf',
    kind: 'Supplement',
    fiscalYear: 'FY2024',
    status: 'failed',
    pages: 14,
    chunks: 0,
    sizeMb: 0.9,
    uploaded: '2026-06-10',
    owner: 'Marcus Cole',
    error: '3 pages were unreadable (scanned images). Re-upload a text-based PDF.'
  }],
  documentStats: {
    total: 6,
    indexed: 4,
    chunks: 1511,
    processing: 1
  },
  // ---- Workspace members (owner admin) --------------------------
  members: [{
    id: 'u1',
    name: 'Dana Whitfield',
    email: 'dana@acme.com',
    role: 'owner',
    lastActive: '2026-06-14'
  }, {
    id: 'u2',
    name: 'Marcus Cole',
    email: 'marcus@acme.com',
    role: 'finance',
    lastActive: '2026-06-13'
  }, {
    id: 'u3',
    name: 'Priya Nair',
    email: 'priya@acme.com',
    role: 'hr',
    lastActive: '2026-06-14'
  }, {
    id: 'u4',
    name: 'Sam Okafor',
    email: 'sam@acme.com',
    role: 'employee',
    lastActive: '2026-06-11'
  }, {
    id: 'u5',
    name: 'Lena Brandt',
    email: 'lena@acme.com',
    role: 'employee',
    lastActive: '2026-06-09'
  }],
  // ---- Access policy (owner admin) ------------------------------
  // The four roles in the system, ordered most → least privileged.
  roles: ['owner', 'finance', 'hr', 'employee'],
  // Sensitivity tier -> roles permitted to retrieve. Mirrors the
  // backend exactly: public & internal are open to all four roles;
  // restricted is owner + finance ONLY (hr and employee cannot see it).
  // This is POLICY configuration — it states who is permitted, never
  // the withheld content itself.
  sensitivityAccess: {
    public: ['owner', 'finance', 'hr', 'employee'],
    internal: ['owner', 'finance', 'hr', 'employee'],
    restricted: ['owner', 'finance']
  },
  sensitivityTiers: ['public', 'internal', 'restricted'],
  sections: [{
    id: 's1',
    label: 'Financial statements',
    detail: 'Income statement, balance sheet, cash flows',
    sensitivity: 'public'
  }, {
    id: 's2',
    label: 'MD&A & risk factors',
    detail: 'Management discussion, liquidity & risk disclosures',
    sensitivity: 'public'
  }, {
    id: 's3',
    label: 'Segment detail',
    detail: 'Revenue & margin by operating segment',
    sensitivity: 'internal'
  }, {
    id: 's4',
    label: 'Notes & contingencies',
    detail: 'Legal contingencies, commitments, tax positions',
    sensitivity: 'internal'
  }, {
    id: 's5',
    label: 'Executive compensation',
    detail: 'Salary tables, bonus & equity awards',
    sensitivity: 'restricted'
  }, {
    id: 's6',
    label: 'Comp committee materials',
    detail: 'Board compensation committee deliberations',
    sensitivity: 'restricted'
  }]
};
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/finrag-app/mockData.js", error: String((e && e.message) || e) }); }

__ds_ns.AccessBadge = __ds_scope.AccessBadge;

__ds_ns.Citation = __ds_scope.Citation;

__ds_ns.ConfidenceMeter = __ds_scope.ConfidenceMeter;

__ds_ns.SourceCard = __ds_scope.SourceCard;

__ds_ns.Avatar = __ds_scope.Avatar;

__ds_ns.Badge = __ds_scope.Badge;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.IconButton = __ds_scope.IconButton;

__ds_ns.Spinner = __ds_scope.Spinner;

__ds_ns.Card = __ds_scope.Card;

__ds_ns.ProgressBar = __ds_scope.ProgressBar;

__ds_ns.StatTile = __ds_scope.StatTile;

__ds_ns.Tabs = __ds_scope.Tabs;

__ds_ns.Banner = __ds_scope.Banner;

__ds_ns.EmptyState = __ds_scope.EmptyState;

__ds_ns.Toast = __ds_scope.Toast;

__ds_ns.Tooltip = __ds_scope.Tooltip;

__ds_ns.Checkbox = __ds_scope.Checkbox;

__ds_ns.Field = __ds_scope.Field;

__ds_ns.Input = __ds_scope.Input;

__ds_ns.Select = __ds_scope.Select;

__ds_ns.Switch = __ds_scope.Switch;

__ds_ns.Textarea = __ds_scope.Textarea;

})();
