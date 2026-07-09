# coding=UTF-8
# WebUI 静态资源 — 由 build_frontend.py 自动生成
# 请勿手动编辑。模板文件在 templates/ 和 static/ 目录。

WEB_UI_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TRMD · 转存控制台</title>
<style>@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 300;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/cc762462ea67.woff2) format('woff2');
  unicode-range: U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 300;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d5bab8e28732.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 300;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d8e4fe0452aa.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 400;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/cc762462ea67.woff2) format('woff2');
  unicode-range: U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 400;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d5bab8e28732.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 400;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d8e4fe0452aa.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 500;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/cc762462ea67.woff2) format('woff2');
  unicode-range: U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 500;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d5bab8e28732.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 500;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d8e4fe0452aa.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 600;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/cc762462ea67.woff2) format('woff2');
  unicode-range: U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 600;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d5bab8e28732.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 600;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d8e4fe0452aa.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 700;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/cc762462ea67.woff2) format('woff2');
  unicode-range: U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 700;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d5bab8e28732.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 700;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d8e4fe0452aa.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url(/fonts/0b1fcab42c18.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url(/fonts/7d93459d8658.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 500;
  font-display: swap;
  src: url(/fonts/af5fda16a191.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 500;
  font-display: swap;
  src: url(/fonts/cd36de204aca.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url(/fonts/bb1f2d582e7f.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url(/fonts/f4e80d9dfd37.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 700;
  font-display: swap;
  src: url(/fonts/ccfd87f69ef0.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 700;
  font-display: swap;
  src: url(/fonts/9338e65fc077.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 800;
  font-display: swap;
  src: url(/fonts/a72eccfa6cfa.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 800;
  font-display: swap;
  src: url(/fonts/60bf0aba6526.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}</style>
<style>/*! tailwindcss v4.1.18 | MIT License | https://tailwindcss.com */
@layer properties{@supports (((-webkit-hyphens:none)) and (not (margin-trim:inline))) or ((-moz-orient:inline) and (not (color:rgb(from red r g b)))){*,:before,:after,::backdrop{--tw-rotate-x:initial;--tw-rotate-y:initial;--tw-rotate-z:initial;--tw-skew-x:initial;--tw-skew-y:initial;--tw-border-style:solid;--tw-leading:initial;--tw-font-weight:initial;--tw-tracking:initial;--tw-shadow:0 0 #0000;--tw-shadow-color:initial;--tw-shadow-alpha:100%;--tw-inset-shadow:0 0 #0000;--tw-inset-shadow-color:initial;--tw-inset-shadow-alpha:100%;--tw-ring-color:initial;--tw-ring-shadow:0 0 #0000;--tw-inset-ring-color:initial;--tw-inset-ring-shadow:0 0 #0000;--tw-ring-inset:initial;--tw-ring-offset-width:0px;--tw-ring-offset-color:#fff;--tw-ring-offset-shadow:0 0 #0000;--tw-outline-style:solid;--tw-blur:initial;--tw-brightness:initial;--tw-contrast:initial;--tw-grayscale:initial;--tw-hue-rotate:initial;--tw-invert:initial;--tw-opacity:initial;--tw-saturate:initial;--tw-sepia:initial;--tw-drop-shadow:initial;--tw-drop-shadow-color:initial;--tw-drop-shadow-alpha:100%;--tw-drop-shadow-size:initial;--tw-backdrop-blur:initial;--tw-backdrop-brightness:initial;--tw-backdrop-contrast:initial;--tw-backdrop-grayscale:initial;--tw-backdrop-hue-rotate:initial;--tw-backdrop-invert:initial;--tw-backdrop-opacity:initial;--tw-backdrop-saturate:initial;--tw-backdrop-sepia:initial;--tw-duration:initial}}}@layer theme{:root,:host{--font-sans:ui-sans-serif,system-ui,sans-serif,"Apple Color Emoji","Segoe UI Emoji","Segoe UI Symbol","Noto Color Emoji";--font-mono:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono","Courier New",monospace;--color-red-200:oklch(88.5% .062 18.334);--color-red-300:oklch(80.8% .114 19.571);--color-orange-50:oklch(98% .016 73.684);--color-slate-100:oklch(96.8% .007 247.896);--color-slate-300:oklch(86.9% .022 252.894);--color-slate-500:oklch(55.4% .046 257.417);--color-black:#000;--color-white:#fff;--spacing:.25rem;--text-xs:.75rem;--text-xs--line-height:calc(1/.75);--text-sm:.875rem;--text-sm--line-height:calc(1.25/.875);--text-base:1rem;--text-base--line-height:calc(1.5/1);--text-lg:1.125rem;--text-lg--line-height:calc(1.75/1.125);--text-xl:1.25rem;--text-xl--line-height:calc(1.75/1.25);--text-2xl:1.5rem;--text-2xl--line-height:calc(2/1.5);--font-weight-normal:400;--font-weight-medium:500;--font-weight-semibold:600;--font-weight-bold:700;--font-weight-extrabold:800;--leading-tight:1.25;--leading-relaxed:1.625;--radius-sm:8px;--radius-md:.375rem;--radius-lg:.5rem;--radius-xl:.75rem;--radius-2xl:1rem;--animate-spin:spin 1s linear infinite;--default-transition-duration:.15s;--default-transition-timing-function:cubic-bezier(.4,0,.2,1);--default-font-family:var(--font-sans);--default-mono-font-family:var(--font-mono);--color-primary:#2563eb;--color-primary-light:#3b82f6;--color-primary-soft:#eff6ff;--color-primary-ghost:#dbeafe;--color-primary-dark:#1d4ed8;--color-bg:#f0f4ff;--color-surface:#fff;--color-surface-alt:#f8fafc;--color-surface-hover:#f1f5f9;--color-surface-muted:#f0f3f5;--color-text:#1e293b;--color-text-secondary:#475569;--color-muted:#94a3b8;--color-line:#e2e8f0;--color-line-light:#f1f5f9;--color-success:#10b981;--color-success-bg:#ecfdf5;--color-warning:#f59e0b;--color-warning-bg:#fffbeb;--color-danger:#ef4444;--color-danger-bg:#fef2f2;--color-cta:#f97316;--font-heading:"Poppins","PingFang SC","Microsoft YaHei","Noto Sans SC",ui-sans-serif,system-ui,sans-serif;--font-body:"Open Sans","PingFang SC","Microsoft YaHei","Noto Sans SC",ui-sans-serif,system-ui,sans-serif;--font-mob:"Inter","PingFang SC","Microsoft YaHei","Noto Sans SC",ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;--tab-height:56px;--topbar-height:48px}}@layer base{*,:after,:before,::backdrop{box-sizing:border-box;border:0 solid;margin:0;padding:0}::file-selector-button{box-sizing:border-box;border:0 solid;margin:0;padding:0}html,:host{-webkit-text-size-adjust:100%;tab-size:4;line-height:1.5;font-family:var(--default-font-family,ui-sans-serif,system-ui,sans-serif,"Apple Color Emoji","Segoe UI Emoji","Segoe UI Symbol","Noto Color Emoji");font-feature-settings:var(--default-font-feature-settings,normal);font-variation-settings:var(--default-font-variation-settings,normal);-webkit-tap-highlight-color:transparent}hr{height:0;color:inherit;border-top-width:1px}abbr:where([title]){-webkit-text-decoration:underline dotted;text-decoration:underline dotted}h1,h2,h3,h4,h5,h6{font-size:inherit;font-weight:inherit}a{color:inherit;-webkit-text-decoration:inherit;-webkit-text-decoration:inherit;-webkit-text-decoration:inherit;text-decoration:inherit}b,strong{font-weight:bolder}code,kbd,samp,pre{font-family:var(--default-mono-font-family,ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono","Courier New",monospace);font-feature-settings:var(--default-mono-font-feature-settings,normal);font-variation-settings:var(--default-mono-font-variation-settings,normal);font-size:1em}small{font-size:80%}sub,sup{vertical-align:baseline;font-size:75%;line-height:0;position:relative}sub{bottom:-.25em}sup{top:-.5em}table{text-indent:0;border-color:inherit;border-collapse:collapse}:-moz-focusring{outline:auto}progress{vertical-align:baseline}summary{display:list-item}ol,ul,menu{list-style:none}img,svg,video,canvas,audio,iframe,embed,object{vertical-align:middle;display:block}img,video{max-width:100%;height:auto}button,input,select,optgroup,textarea{font:inherit;font-feature-settings:inherit;font-variation-settings:inherit;letter-spacing:inherit;color:inherit;opacity:1;background-color:#0000;border-radius:0}::file-selector-button{font:inherit;font-feature-settings:inherit;font-variation-settings:inherit;letter-spacing:inherit;color:inherit;opacity:1;background-color:#0000;border-radius:0}:where(select:is([multiple],[size])) optgroup{font-weight:bolder}:where(select:is([multiple],[size])) optgroup option{padding-inline-start:20px}::file-selector-button{margin-inline-end:4px}::placeholder{opacity:1}@supports (not ((-webkit-appearance:-apple-pay-button))) or (contain-intrinsic-size:1px){::placeholder{color:currentColor}@supports (color:color-mix(in lab, red, red)){::placeholder{color:color-mix(in oklab,currentcolor 50%,transparent)}}}textarea{resize:vertical}::-webkit-search-decoration{-webkit-appearance:none}::-webkit-date-and-time-value{min-height:1lh;text-align:inherit}::-webkit-datetime-edit{display:inline-flex}::-webkit-datetime-edit-fields-wrapper{padding:0}::-webkit-datetime-edit{padding-block:0}::-webkit-datetime-edit-year-field{padding-block:0}::-webkit-datetime-edit-month-field{padding-block:0}::-webkit-datetime-edit-day-field{padding-block:0}::-webkit-datetime-edit-hour-field{padding-block:0}::-webkit-datetime-edit-minute-field{padding-block:0}::-webkit-datetime-edit-second-field{padding-block:0}::-webkit-datetime-edit-millisecond-field{padding-block:0}::-webkit-datetime-edit-meridiem-field{padding-block:0}::-webkit-calendar-picker-indicator{line-height:1}:-moz-ui-invalid{box-shadow:none}button,input:where([type=button],[type=reset],[type=submit]){appearance:button}::file-selector-button{appearance:button}::-webkit-inner-spin-button{height:auto}::-webkit-outer-spin-button{height:auto}[hidden]:where(:not([hidden=until-found])){display:none!important}:root{--safe-bottom:env(safe-area-inset-bottom,0px)}html{font-family:var(--font-body);color:var(--color-text);background:var(--color-bg);font-size:15px;line-height:1.5}body{min-height:100vh;display:flex}button,input,select,textarea{font-family:inherit;font-size:inherit}button{cursor:pointer}button:disabled{cursor:not-allowed;opacity:.55}}@layer components{.sidebar{top:calc(var(--spacing)*0);z-index:50;border-right-style:var(--tw-border-style);border-right-width:1px;border-color:var(--color-line);background-color:var(--color-white);width:250px;height:100vh;padding-inline:calc(var(--spacing)*4);padding-block:calc(var(--spacing)*6);flex-direction:column;display:flex;position:sticky}.sidebar-brand{margin-bottom:calc(var(--spacing)*3);align-items:center;gap:calc(var(--spacing)*3);border-bottom-style:var(--tw-border-style);border-bottom-width:1px;border-color:var(--color-line);padding-bottom:calc(var(--spacing)*5);display:flex}.sidebar-brand-mark{height:calc(var(--spacing)*10);width:calc(var(--spacing)*10);font-size:var(--text-lg);line-height:var(--tw-leading,var(--text-lg--line-height));--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold);color:var(--color-white);background:linear-gradient(135deg,var(--color-primary),var(--color-primary-light));font-family:var(--font-heading);border-radius:10px;justify-content:center;align-items:center;display:flex;box-shadow:0 4px 10px #2563eb4d}.sidebar-nav-section{flex:1;overflow-y:auto}.sidebar-nav-label{padding-inline:calc(var(--spacing)*2.5);padding-top:calc(var(--spacing)*4);padding-bottom:calc(var(--spacing)*2);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);--tw-tracking:.08em;letter-spacing:.08em;color:var(--color-muted);text-transform:uppercase}.sidebar-nav-item{cursor:pointer;align-items:center;gap:calc(var(--spacing)*2.5);border-style:var(--tw-border-style);width:100%;padding-inline:calc(var(--spacing)*3);padding-block:calc(var(--spacing)*2.5);text-align:left;font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));--tw-font-weight:var(--font-weight-medium);font-weight:var(--font-weight-medium);color:var(--color-text-secondary);transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;background-color:#0000;border-width:0;border-radius:8px;font-family:inherit;transition-duration:.15s;display:flex}.sidebar-nav-item:hover{background-color:var(--color-primary-soft);color:var(--color-primary)}.sidebar-nav-item.active{background-color:var(--color-primary-soft);--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-primary)}.sidebar-nav-item svg{flex-shrink:0;width:18px;height:18px}.sidebar-nav-badge{background-color:var(--color-primary-ghost);padding-inline:calc(var(--spacing)*2);padding-block:calc(var(--spacing)*.5);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold);color:var(--color-primary);border-radius:3.40282e38px;margin-left:auto}.sidebar-footer{margin-top:calc(var(--spacing)*2);gap:calc(var(--spacing)*1.5);border-top-style:var(--tw-border-style);border-top-width:1px;border-color:var(--color-line);padding-top:calc(var(--spacing)*4);flex-direction:column;display:flex}.sidebar-footer-info{align-items:center;gap:calc(var(--spacing)*2);padding-inline:calc(var(--spacing)*2);padding-block:calc(var(--spacing)*1);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-text-secondary);display:flex}.sidebar-status-dot{height:calc(var(--spacing)*2);width:calc(var(--spacing)*2);background:var(--color-success);border-radius:3.40282e38px;flex-shrink:0;box-shadow:0 0 0 3px #10b98133}.sidebar-version{padding-inline:calc(var(--spacing)*2);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));color:var(--color-muted);opacity:.7}.main-content{min-width:calc(var(--spacing)*0);gap:calc(var(--spacing)*6);padding:calc(var(--spacing)*7);flex-direction:column;flex:1;display:flex}.topbar{justify-content:space-between;align-items:flex-start;gap:calc(var(--spacing)*4);display:flex}.topbar h1{font-size:var(--text-xl);line-height:var(--tw-leading,var(--text-xl--line-height));--tw-leading:var(--leading-tight);line-height:var(--leading-tight);--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold);color:var(--color-text);font-family:var(--font-heading)}.topbar p{margin-top:calc(var(--spacing)*1);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-muted)}.btn{cursor:pointer;align-items:center;gap:calc(var(--spacing)*1.5);border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);padding-inline:calc(var(--spacing)*4);padding-block:calc(var(--spacing)*2);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));--tw-font-weight:var(--font-weight-medium);font-weight:var(--font-weight-medium);white-space:nowrap;color:var(--color-text);transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;border-radius:6px;font-family:inherit;transition-duration:.15s;display:inline-flex}.btn:hover{border-color:var(--color-primary-light);background-color:var(--color-primary-soft)}.btn svg{height:calc(var(--spacing)*4);width:calc(var(--spacing)*4);flex-shrink:0}.btn-primary{border-color:var(--color-primary);background-color:var(--color-primary);--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-white)}.btn-primary:hover{border-color:var(--color-primary-dark);background-color:var(--color-primary-dark);color:var(--color-white)}.btn-danger{border-color:var(--color-red-200);color:var(--color-danger)}.btn-danger:hover{border-color:var(--color-danger);background-color:var(--color-danger-bg);color:var(--color-danger)}.btn-sm{padding-inline:calc(var(--spacing)*2.5);padding-block:calc(var(--spacing)*1);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height))}.btn-icon{width:34px;height:34px;padding:calc(var(--spacing)*0);justify-content:center}.stat-grid{gap:calc(var(--spacing)*4);grid-template-columns:repeat(4,minmax(0,1fr));display:grid}.stat-card{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);--tw-shadow:0 1px 3px 0 var(--tw-shadow-color,#0000001a),0 1px 2px -1px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow);transition-property:box-shadow;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.2s;border-radius:12px;justify-content:space-between;align-items:flex-start;padding:18px;transition-duration:.2s;display:flex}.stat-card:hover{border-color:var(--color-primary-ghost);--tw-shadow:0 4px 6px -1px var(--tw-shadow-color,#0000001a),0 2px 4px -2px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow)}.stat-card-icon{height:calc(var(--spacing)*10);width:calc(var(--spacing)*10);border-radius:8px;flex-shrink:0;justify-content:center;align-items:center;display:flex}.stat-card-icon.blue{background-color:var(--color-primary-soft);color:var(--color-primary)}.stat-card-icon.green{background-color:var(--color-success-bg);color:var(--color-success)}.stat-card-icon.orange{background-color:var(--color-orange-50);color:var(--color-cta)}.stat-card-icon.red{background-color:var(--color-danger-bg);color:var(--color-danger)}.stat-card-icon svg{height:calc(var(--spacing)*5);width:calc(var(--spacing)*5)}.stat-card-value{text-align:right;font-size:var(--text-xl);line-height:var(--tw-leading,var(--text-xl--line-height));--tw-leading:var(--leading-tight);line-height:var(--leading-tight);--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold);color:var(--color-text);font-family:var(--font-heading)}.stat-card-label{margin-top:calc(var(--spacing)*1);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-medium);font-weight:var(--font-weight-medium);color:var(--color-muted)}.panel{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);--tw-shadow:0 1px 3px 0 var(--tw-shadow-color,#0000001a),0 1px 2px -1px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow);border-radius:12px;flex-direction:column;display:flex;overflow:hidden}.panel-header{border-bottom-style:var(--tw-border-style);border-bottom-width:1px;border-color:var(--color-line);background-color:var(--color-surface-alt);padding-inline:18px;padding-block:calc(var(--spacing)*3.5);justify-content:space-between;align-items:center;display:flex}.panel-header h3{font-size:var(--text-base);line-height:var(--tw-leading,var(--text-base--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-text);font-family:var(--font-heading)}.panel-body{flex:1;padding:18px;overflow-y:auto}.panel-tabs{gap:calc(var(--spacing)*.5);display:flex}.panel-tab{cursor:pointer;border-style:var(--tw-border-style);padding-inline:calc(var(--spacing)*2.5);padding-block:calc(var(--spacing)*1);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-medium);font-weight:var(--font-weight-medium);color:var(--color-text-secondary);transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.1s;background-color:#0000;border-width:0;border-radius:.25rem;font-family:inherit;transition-duration:.1s}.panel-tab:hover{background-color:var(--color-primary-soft);color:var(--color-primary)}.panel-tab.active{background-color:var(--color-primary-soft);--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-primary)}.form-group{margin-bottom:calc(var(--spacing)*3.5)}.form-label{margin-bottom:calc(var(--spacing)*1.5);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);--tw-tracking:.04em;letter-spacing:.04em;color:var(--color-muted);text-transform:uppercase;display:block}.form-input,.form-select{height:calc(var(--spacing)*10);border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);width:100%;padding-inline:calc(var(--spacing)*3);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-text);transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;--tw-outline-style:none;border-radius:6px;outline-style:none;font-family:inherit;transition-duration:.15s}.form-input:focus,.form-select:focus{border-color:var(--color-primary);box-shadow:0 0 0 3px #2563eb1f}.watch-download-sources{resize:vertical;min-height:124px}.download-upload-align-spacer{margin-bottom:calc(var(--spacing)*3.5);border-style:var(--tw-border-style);--tw-border-style:dashed;border-style:dashed;border-width:1px;border-color:var(--color-line);background-color:var(--color-surface-alt);min-height:88px;padding-inline:calc(var(--spacing)*4);text-align:center;font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-muted);border-radius:8px;justify-content:center;align-items:center;display:flex}@media (min-width:64rem){.download-upload-align-spacer{min-height:184px}}.form-row{gap:calc(var(--spacing)*2.5);grid-template-columns:repeat(2,minmax(0,1fr));display:grid}.form-submit{margin-top:calc(var(--spacing)*1.5);height:calc(var(--spacing)*10);cursor:pointer;justify-content:center;align-items:center;gap:calc(var(--spacing)*1.5);border-style:var(--tw-border-style);background-color:var(--color-primary);width:100%;font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-white);transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;border-width:0;border-radius:6px;font-family:inherit;transition-duration:.15s;display:flex}.form-submit:hover{background-color:var(--color-primary-dark)}.data-table{border-collapse:collapse;width:100%;font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height))}.data-table thead th{top:calc(var(--spacing)*0);border-bottom-style:var(--tw-border-style);border-bottom-width:2px;border-color:var(--color-line);background-color:var(--color-surface-alt);padding-inline:calc(var(--spacing)*3);padding-block:calc(var(--spacing)*2.5);text-align:center;font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);--tw-tracking:.05em;letter-spacing:.05em;white-space:nowrap;color:var(--color-muted);text-transform:uppercase;position:sticky}.data-table tbody td{border-bottom-style:var(--tw-border-style);border-bottom-width:1px;border-color:var(--color-line-light);padding-inline:calc(var(--spacing)*3);padding-block:calc(var(--spacing)*2.5);text-align:center;vertical-align:middle;font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height))}.table-actions{justify-content:center}.data-table tbody tr{cursor:pointer;transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:75ms;transition-duration:75ms}.data-table tbody tr:hover{background-color:var(--color-surface-hover)}.data-table tbody tr.selected{background-color:var(--color-primary-soft)}.task-items-table{table-layout:fixed;min-width:840px}.task-items-table .task-item-col-file{width:34%}.task-items-table .task-item-col-size{width:112px}.task-items-table .task-item-col-progress,.task-items-table .task-item-col-source{width:220px}.task-items-table .task-item-col-status{width:118px}.task-items-table th,.task-items-table td{white-space:nowrap}.task-items-table .task-item-file{text-align:left;white-space:normal;overflow-wrap:anywhere;word-break:break-word;line-height:1.45}.task-items-table .task-item-size,.task-items-table .task-item-status{min-width:112px}.task-items-table .task-item-progress,.task-items-table .task-item-source{text-overflow:ellipsis;overflow:hidden}.badge{padding-inline:calc(var(--spacing)*2.5);padding-block:calc(var(--spacing)*.5);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);border-radius:3.40282e38px;align-items:center;display:inline-flex}.badge-running{background-color:var(--color-primary-soft);color:var(--color-primary)}.badge-success{background-color:var(--color-success-bg);color:var(--color-success)}.badge-failed{background-color:var(--color-danger-bg);color:var(--color-danger)}.badge-pending{background-color:var(--color-orange-50);color:var(--color-cta)}.badge-paused,.badge-skipped{background-color:var(--color-slate-100);color:var(--color-slate-500)}.badge-warning{background-color:var(--color-warning-bg);color:var(--color-warning)}.badge-muted{background-color:var(--color-slate-100);color:var(--color-slate-500)}.progress-bar{height:calc(var(--spacing)*1.5);background-color:var(--color-slate-100);border-radius:3.40282e38px;overflow:hidden}.progress-fill{height:100%;transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.3s;background:linear-gradient(90deg,var(--color-primary-light),var(--color-primary));border-radius:3.40282e38px;transition-duration:.3s}.status-dot{margin-right:calc(var(--spacing)*1.5);height:calc(var(--spacing)*1.5);width:calc(var(--spacing)*1.5);vertical-align:middle;border-radius:3.40282e38px;display:inline-block}.status-dot.running{background-color:var(--color-primary)}.status-dot.success{background-color:var(--color-success)}.status-dot.failed{background-color:var(--color-danger)}.status-dot.pending{background-color:var(--color-warning)}.status-dot.paused{background-color:var(--color-slate-300)}.activity-item{gap:calc(var(--spacing)*2);border-bottom-style:var(--tw-border-style);border-bottom-width:1px;border-color:var(--color-line-light);padding-block:calc(var(--spacing)*1.5);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-leading:1.5;line-height:1.5;display:flex}.activity-item:last-child{border-bottom-style:var(--tw-border-style);border-bottom-width:0}.activity-time{min-width:44px;font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));white-space:nowrap;color:var(--color-muted);font-family:ui-monospace,monospace}.activity-badge{font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);white-space:nowrap}.activity-badge.ok{color:var(--color-success)}.activity-badge.warn{color:var(--color-warning)}.activity-badge.err{color:var(--color-danger)}.view{display:none}.view.active{gap:18px;display:grid}.login-page{background-color:var(--color-bg);width:100%;min-height:100vh;padding-inline:calc(var(--spacing)*6);padding-block:calc(var(--spacing)*8);flex-direction:column;flex:1;justify-content:center;align-items:center;display:flex;overflow-x:hidden}@media not all and (min-width:40rem){.login-page{padding-inline:calc(var(--spacing)*4);padding-top:calc(var(--spacing)*14);padding-bottom:calc(var(--spacing)*8);justify-content:flex-start}}.login-page{min-height:100svh}.login-card{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);width:100%;max-width:420px;padding:calc(var(--spacing)*8);--tw-shadow:0 10px 15px -3px var(--tw-shadow-color,#0000001a),0 4px 6px -4px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow);border-radius:16px}@media not all and (min-width:40rem){.login-card{padding:calc(var(--spacing)*6);border-radius:14px}}.login-card{animation:.5s .1s both fadeIn}.login-brand{margin-bottom:calc(var(--spacing)*5);text-align:center;width:100%;max-width:420px}@media not all and (min-width:40rem){.login-brand{margin-bottom:calc(var(--spacing)*4)}}.login-brand{animation:.5s both fadeIn}.login-brand-mark{margin-bottom:calc(var(--spacing)*3);height:calc(var(--spacing)*12);width:calc(var(--spacing)*12);border-radius:var(--radius-xl);--tw-font-weight:var(--font-weight-bold);font-size:22px;font-weight:var(--font-weight-bold);color:var(--color-white);background:linear-gradient(135deg,var(--color-primary),var(--color-primary-light));font-family:var(--font-heading);justify-content:center;align-items:center;display:inline-flex}.login-brand h1{font-size:var(--text-xl);line-height:var(--tw-leading,var(--text-xl--line-height));--tw-font-weight:var(--font-weight-extrabold);font-weight:var(--font-weight-extrabold);color:var(--color-text);font-family:var(--font-heading)}.login-brand p{margin-top:calc(var(--spacing)*1);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-muted)}@media not all and (min-width:40rem){.login-brand p{padding-inline:calc(var(--spacing)*2);--tw-leading:calc(var(--spacing)*5);line-height:calc(var(--spacing)*5)}}.login-overlay{inset:calc(var(--spacing)*0);z-index:1000;background-color:var(--color-bg);width:100%;min-height:100svh;position:fixed}.login-error{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-red-300);background-color:var(--color-danger-bg);padding-inline:calc(var(--spacing)*3.5);padding-block:calc(var(--spacing)*2.5);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-danger);border-radius:8px;margin-bottom:18px;display:none}.login-error.visible{animation:.4s shake;display:block}@keyframes fadeIn{0%{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}@keyframes shake{0%,to{transform:translate(0)}20%,60%{transform:translate(-6px)}40%,80%{transform:translate(6px)}}.login-field{margin-bottom:calc(var(--spacing)*5)}.login-field label{margin-bottom:calc(var(--spacing)*2);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));--tw-font-weight:var(--font-weight-medium);font-weight:var(--font-weight-medium);color:var(--color-text);display:block}.login-field input{height:calc(var(--spacing)*12);border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);width:100%;padding-inline:calc(var(--spacing)*3.5);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-text);transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;--tw-outline-style:none;border-radius:8px;outline-style:none;font-family:inherit;transition-duration:.15s}.login-field input:focus{border-color:var(--color-primary);box-shadow:0 0 0 3px #2563eb1f}.login-options{margin-bottom:calc(var(--spacing)*6);justify-content:space-between;align-items:center;display:flex}.login-checkbox{cursor:pointer;align-items:center;gap:calc(var(--spacing)*2);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-muted);-webkit-user-select:none;user-select:none;display:flex}.login-submit{height:calc(var(--spacing)*12);cursor:pointer;justify-content:center;align-items:center;gap:calc(var(--spacing)*2);border-style:var(--tw-border-style);background-color:var(--color-primary);width:100%;font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-white);transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;border-width:0;border-radius:8px;font-family:inherit;transition-duration:.15s;display:flex}.login-submit:hover{background-color:var(--color-primary-dark)}.login-submit:disabled{cursor:not-allowed;opacity:.7}.login-submit:disabled:hover{background-color:var(--color-primary)}.spinner{width:18px;height:18px;animation:var(--animate-spin);border-style:var(--tw-border-style);border-width:2px;border-color:#ffffff4d;border-radius:3.40282e38px;flex-shrink:0}@supports (color:color-mix(in lab, red, red)){.spinner{border-color:color-mix(in oklab,var(--color-white)30%,transparent)}}.spinner{border-top-color:var(--color-white)}.watch-overlay{pointer-events:none;inset:calc(var(--spacing)*0);z-index:999;background-color:#00000059;justify-content:center;align-items:center;display:flex;position:fixed}@supports (color:color-mix(in lab, red, red)){.watch-overlay{background-color:color-mix(in oklab,var(--color-black)35%,transparent)}}.watch-overlay{opacity:0;transition-property:opacity;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.2s;transition-duration:.2s}.watch-overlay.open{pointer-events:auto;opacity:1}.watch-dialog{gap:calc(var(--spacing)*4);background-color:var(--color-surface);width:440px;max-width:calc(100vw - 32px);padding:calc(var(--spacing)*6);--tw-shadow:0 10px 15px -3px var(--tw-shadow-color,#0000001a),0 4px 6px -4px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow);border-radius:10px;display:grid}.watch-history-dialog{grid-template-rows:auto minmax(0,1fr) auto;width:900px;max-height:82vh}.watch-history-header{justify-content:space-between;align-items:center;gap:calc(var(--spacing)*3);display:flex}.watch-history-body{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);border-radius:8px;overflow:auto}.watch-history-pagination{justify-content:space-between;align-items:center;gap:calc(var(--spacing)*3);flex-wrap:wrap;display:flex}.watch-history-table{min-width:720px}.watch-row{cursor:pointer}.watch-row:hover{background:var(--color-surface-hover)}.watch-events-row{display:none}.watch-events-row.open{display:table-row}.watch-events-row td{background:var(--color-surface-alt);padding:0}.watch-events-panel{max-height:300px;padding:12px 16px;font-size:15px;overflow-y:auto}.watch-event-item{border-bottom:1px solid var(--color-line);align-items:flex-start;gap:8px;padding:4px 0;font-size:13px;display:flex}.watch-event-item:last-child{border-bottom:0}.watch-event-time{color:var(--color-muted);white-space:nowrap;min-width:90px}.watch-event-badge{flex-shrink:0}.watch-event-info{word-break:break-all;flex:1}.watch-events-load-more{cursor:pointer;margin:8px auto 0;font-size:13px;display:block}@media (max-width:1200px){.stat-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media (max-width:960px){.sidebar{display:none}.main-content{padding:calc(var(--spacing)*4)}}.mob-body{font-family:var(--font-mob);-webkit-tap-highlight-color:transparent;-webkit-user-select:none;user-select:none;width:100%;min-height:100svh;padding-top:var(--topbar-height);padding-bottom:calc(var(--tab-height) + var(--safe-bottom));background:var(--color-bg);color:var(--color-text);font-size:15px;line-height:1.5;display:block;overflow-x:hidden}.mob-body label{width:100%;min-width:0;color:var(--color-text-secondary);gap:6px;font-size:14px;font-weight:500;display:grid}.mob-body form{flex-direction:column;gap:10px;width:100%;min-width:0;display:flex}.mob-body input,.mob-body select,.mob-body textarea{border:1px solid var(--color-line);background:var(--color-surface);width:100%;min-width:0;color:var(--color-text);box-sizing:border-box;border-radius:8px;min-height:44px;padding:12px 14px;font-family:inherit;font-size:16px;transition:border-color .18s,box-shadow .18s}.mob-body input:focus,.mob-body select:focus,.mob-body textarea:focus{border-color:var(--color-primary);outline:none;box-shadow:0 0 0 3px #2563eb1f}.mob-body input[type=checkbox],.mob-body input[type=radio]{width:auto;min-width:auto;min-height:auto;accent-color:var(--color-primary);padding:0}.mob-body label:has(input[type=checkbox]),.mob-body label:has(input[type=radio]){flex-direction:row;align-items:center;gap:8px;display:flex}.mob-btn{background:var(--color-primary);color:#fff;cursor:pointer;border:0;border-radius:8px;justify-content:center;align-items:center;gap:6px;min-width:44px;min-height:44px;padding:0 16px;font-family:inherit;font-size:15px;font-weight:600;transition:opacity .15s,background .15s;display:inline-flex}.mob-btn:active{opacity:.78}.mob-btn-muted{background:var(--color-surface);color:var(--color-text);border:1px solid var(--color-line)}.mob-btn-muted:active{background:var(--color-surface-muted)}.mob-btn-danger{color:var(--color-danger);border:1px solid var(--color-danger);background:0 0}.mob-btn-danger:active{background:var(--color-danger-bg)}.mob-btn-sm{min-width:auto;min-height:36px;padding:0 12px;font-size:14px}.mob-btn svg{flex-shrink:0;width:18px;height:18px}.mob-topbar{height:var(--topbar-height);background:var(--color-surface);border-bottom:1px solid var(--color-line);z-index:100;align-items:center;gap:6px;padding:0 14px;display:flex;position:fixed;top:0;left:0;right:0}.mob-topbar__back{width:44px;height:44px;color:var(--color-primary);cursor:pointer;background:0 0;border:0;border-radius:8px;flex-shrink:0;justify-content:center;align-items:center;min-width:44px;min-height:44px;padding:0;font-family:inherit;font-size:20px;line-height:1;display:none}.mob-topbar__back:active{background:var(--color-primary-soft)}.mob-topbar__title{font-size:17px;font-weight:700;font-family:var(--font-heading);color:var(--color-text)}.mob-topbar.sub .mob-topbar__back{display:flex}.mob-tabbar{background:var(--color-surface);border-top:1px solid var(--color-line);z-index:100;height:calc(var(--tab-height) + var(--safe-bottom));padding-top:6px;padding-bottom:var(--safe-bottom);justify-content:space-around;align-items:flex-start;display:flex;position:fixed;bottom:0;left:0;right:0}.mob-tab{color:var(--color-muted);cursor:pointer;background:0 0;border:0;border-radius:0;flex-direction:column;align-items:center;gap:2px;min-width:44px;min-height:auto;padding:4px 0;font-family:inherit;font-size:11px;font-weight:500;transition:color .15s;display:flex}.mob-tab.active{color:var(--color-primary);font-weight:600}.mob-tab svg{flex-shrink:0;width:24px;height:24px}.mob-content{box-sizing:border-box;flex-direction:column;gap:10px;width:100%;min-width:0;max-width:100%;padding:12px;animation:.25s both mobRise;display:flex}@keyframes mobRise{0%{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}.mob-view{display:none}.mob-view.active{flex-direction:column;gap:10px;width:100%;min-width:0;display:flex}.mob-view.active>*{min-width:0}.mob-subpage{flex-direction:column;gap:10px;width:100%;min-width:0;display:none}.mob-subpage.active{display:flex}.mob-subpage.active>*{min-width:0}.mob-card{background:var(--color-surface);border:1px solid var(--color-line);border-left:3px solid var(--color-line);box-sizing:border-box;cursor:pointer;border-radius:10px;width:100%;max-width:100%;padding:14px;transition:all .15s;box-shadow:0 1px 3px #0000000a}.mob-card:active{transform:scale(.985)}.mob-card.status-pending{border-left-color:#94a3b8}.mob-card.status-running{border-left-color:var(--color-primary)}.mob-card.status-paused{border-left-color:var(--color-warning)}.mob-card.status-success,.mob-card.status-completed{border-left-color:var(--color-success)}.mob-card.status-failure{border-left-color:var(--color-danger)}.mob-card.status-cancelled{border-left-color:#94a3b8}.mob-card.status-skipped{border-left-color:#8b5cf6}.mob-card__head{justify-content:space-between;align-items:flex-start;margin-bottom:6px;display:flex}.mob-card__title{word-break:break-all;flex:1;min-width:0;font-size:15px;font-weight:650;line-height:1.35}.mob-card__badge{white-space:nowrap;border-radius:4px;flex-shrink:0;padding:2px 8px;font-size:12px;font-weight:600;display:inline-block}.mob-card__badge.pending{color:var(--color-text-secondary);background:#f1f5f9}.mob-card__badge.running{background:var(--color-success-bg);color:var(--color-success)}.mob-card__badge.paused{background:var(--color-warning-bg);color:var(--color-warning)}.mob-card__badge.completed{background:var(--color-primary-soft);color:var(--color-primary)}.mob-card__badge.failure{background:var(--color-danger-bg);color:var(--color-danger)}.mob-card__badge.cancelled{color:#94a3b8;background:#f1f5f9}.mob-card__row{justify-content:space-between;align-items:flex-start;gap:10px;padding:2px 0;font-size:13px;display:flex}.mob-card__row .label{color:var(--color-muted)}.mob-card__row span:last-child{text-align:right;overflow-wrap:anywhere;min-width:0}.mob-card__progress{background:var(--color-surface-muted);border-radius:3px;height:6px;margin:6px 0;overflow:hidden}.mob-card__progress-fill{background:var(--color-primary);border-radius:3px;height:100%;transition:width .3s}.mob-card__actions{flex-wrap:wrap;gap:6px;margin-top:8px;display:flex}.mob-watch-events{border-top:1px solid var(--color-line);margin-top:8px;padding-top:8px;font-size:12px}.mob-watch-events .watch-event-item{border-bottom:1px solid var(--color-line);align-items:flex-start;gap:6px;padding:3px 0;display:flex}.mob-watch-events .watch-event-item:last-child{border-bottom:0}.mob-collapse{border:1px solid var(--color-line);background:var(--color-surface);box-sizing:border-box;border-radius:10px;width:100%;min-width:0;max-width:100%;overflow:hidden}.mob-collapse__head{cursor:pointer;-webkit-user-select:none;user-select:none;color:var(--color-text);justify-content:space-between;align-items:center;min-width:0;padding:14px;font-size:15px;font-weight:600;display:flex}.mob-collapse__head:active{background:var(--color-surface-muted)}.mob-collapse__arrow{color:var(--color-muted);flex-shrink:0;font-size:12px;transition:transform .2s}.mob-collapse.open .mob-collapse__arrow{transform:rotate(180deg)}.mob-collapse__body{flex-direction:column;gap:10px;min-width:0;padding:0 14px 14px;display:none}.mob-collapse.open .mob-collapse__body{display:flex}.mob-collapse__body>*{width:100%;min-width:0}.mob-collapse__body>.mob-btn,.mob-collapse__body>.mob-empty{width:100%}.mob-menu-group{background:var(--color-surface);border:1px solid var(--color-line);box-sizing:border-box;border-radius:10px;flex-direction:column;width:100%;max-width:100%;display:flex;overflow:hidden}.mob-menu-group+.mob-menu-group{margin-top:10px}.mob-menu-label{color:var(--color-muted);text-transform:uppercase;letter-spacing:.06em;padding:10px 14px 4px;font-size:12px;font-weight:600}.mob-menu-item{color:var(--color-text);cursor:pointer;text-align:left;border:0;border-bottom:1px solid var(--color-line-light);background:0 0;border-radius:0;align-items:center;gap:10px;width:100%;min-height:44px;padding:14px;font-family:inherit;font-size:15px;font-weight:400;transition:background .15s;display:flex}.mob-menu-item:last-child{border-bottom:0}.mob-menu-item:active{background:var(--color-surface-hover)}.mob-menu-item svg{width:22px;height:22px;color:var(--color-primary);flex-shrink:0}.mob-menu-item__arrow{color:var(--color-muted);margin-left:auto;font-size:14px}.mob-menu-item__label{flex:1}.mob-menu-item--danger,.mob-menu-item--danger svg{color:var(--color-danger)}.mob-sheet-overlay{z-index:300;background:#00000059;align-items:flex-end;display:none;position:fixed;inset:0}.mob-sheet-overlay.open{display:flex}.mob-sheet{background:var(--color-surface);width:100%;padding:20px 16px max(24px,var(--safe-bottom));border-radius:16px 16px 0 0;flex-direction:column;gap:14px;max-height:85vh;animation:.25s mobSlideUp;display:flex;overflow-y:auto}@keyframes mobSlideUp{0%{transform:translateY(100%)}to{transform:translateY(0)}}.mob-sheet__title{font-size:15px;font-weight:700;font-family:var(--font-heading);margin:0}.mob-toast{left:50%;bottom:calc(var(--tab-height) + var(--safe-bottom) + 16px);background:var(--color-text);color:#fff;z-index:400;opacity:0;pointer-events:none;white-space:nowrap;border-radius:8px;padding:10px 20px;font-size:13px;transition:opacity .25s;position:fixed;transform:translate(-50%)}.mob-toast.show{opacity:1;pointer-events:auto}.mob-sheet__task-header{background:var(--color-surface-muted);border-radius:8px;padding:12px}.mob-sheet__task-header .task-title{word-break:break-all;margin-bottom:4px;font-size:15px;font-weight:650}.mob-sheet__task-header .task-meta{color:var(--color-muted);margin-bottom:6px;font-size:12px}.mob-sheet-tabs{gap:6px;padding-bottom:2px;display:flex;overflow-x:auto}.mob-sheet-tab{border:1px solid var(--color-line);background:var(--color-surface);color:var(--color-muted);cursor:pointer;white-space:nowrap;border-radius:6px;min-width:auto;min-height:36px;padding:8px 12px;font-family:inherit;font-size:12px;font-weight:600;transition:all .15s}.mob-sheet-tab.active{background:var(--color-primary);color:#fff;border-color:var(--color-primary)}.mob-sheet-tab .count{opacity:.8;margin-left:3px}.mob-item-row{border-bottom:1px solid var(--color-line);justify-content:space-between;align-items:center;gap:6px;padding:8px 0;font-size:13px;display:flex}.mob-item-row:last-child{border-bottom:0}.mob-item-row__name{text-overflow:ellipsis;white-space:nowrap;word-break:break-all;flex:1;min-width:0;overflow:hidden}.mob-item-row__progress{color:var(--color-muted);text-overflow:ellipsis;white-space:nowrap;margin-top:2px;font-size:12px;font-weight:500;display:block;overflow:hidden}.mob-event-row{border-bottom:1px solid var(--color-line);padding:6px 0;font-size:12px}.mob-event-row:last-child{border-bottom:0}.mob-event-row time{color:var(--color-muted);margin-right:6px}.mob-sheet-pagination{color:var(--color-muted);justify-content:space-between;align-items:center;padding-top:6px;font-size:12px;display:flex}.mob-empty{text-align:center;color:var(--color-muted);padding:32px 16px;font-size:13px;line-height:1.6}.mob-section-title{text-transform:uppercase;letter-spacing:.06em;color:var(--color-muted);padding:4px 0;font-size:12px;font-weight:600}.mob-media-scan-btn{width:100%;margin:8px 0}.mob-media-result{margin-top:12px;font-size:13px}.mob-subpage .mob-collapse__body label,.mob-subpage .mob-collapse__body [style*=display\:grid],.mob-body [style*=display\:grid],.mob-body [style*="display: grid"]{width:100%;min-width:0}.mob-body [style*="grid-template-columns:1fr 1fr"],.mob-body [style*="grid-template-columns: 1fr 1fr"]{grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important}#mob-tasks-list,#mob-watches-list,#mob-operations-list,#mob-statistics-list,#mob-records-list,#mob-media-result,#mob-profile-menu{width:100%;min-width:0;max-width:100%}.mob-check-group{border:1px solid var(--color-line);box-sizing:border-box;border-radius:8px;width:100%;min-width:0;margin:0;padding:10px 14px}.mob-check-group legend{color:var(--color-muted);padding:0 4px;font-size:13px}.mob-table-wrap{border:1px solid var(--color-line);-webkit-overflow-scrolling:touch;border-radius:8px;overflow-x:auto}.mob-table-wrap table{border-collapse:collapse;width:100%;font-size:13px}.mob-table-wrap th,.mob-table-wrap td{text-align:left;border-bottom:1px solid var(--color-line);white-space:nowrap;padding:8px 10px}.mob-table-wrap th{background:var(--color-surface-muted);font-weight:600;position:sticky;top:0}.mob-login-overlay{background:var(--color-bg);z-index:1000;padding:48px 16px;padding-bottom:max(32px,calc(24px + var(--safe-bottom)));flex-direction:column;justify-content:flex-start;align-items:center;gap:16px;display:none;position:fixed;inset:0;overflow-y:auto}.mob-login-overlay.active{display:flex}.mob-login-brand{text-align:center;width:100%;max-width:400px}.mob-login-brand-mark{background:linear-gradient(135deg,var(--color-primary),var(--color-primary-light));color:#fff;width:48px;height:48px;font-size:22px;font-weight:700;font-family:var(--font-heading);border-radius:12px;justify-content:center;align-items:center;margin-bottom:12px;display:inline-flex}.mob-login-brand h1{color:var(--color-text);font-size:22px;font-weight:800;font-family:var(--font-heading);letter-spacing:-.02em;margin:0}.mob-login-brand p{color:var(--color-muted);margin:4px 0 0;font-size:13px}.mob-login-card{background:var(--color-surface);border:1px solid var(--color-line);border-radius:14px;width:100%;max-width:400px;padding:20px;box-shadow:0 1px 3px #0000000a}.mob-login-card__step{color:var(--color-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px;font-size:12px}.mob-login-card__title{color:var(--color-text);font-size:20px;font-weight:700;font-family:var(--font-heading);margin:0 0 6px}.mob-login-card__subtitle{color:var(--color-muted);margin:0 0 20px;font-size:14px;line-height:1.5}.mob-login-field{margin-bottom:16px}.mob-login-field label{color:var(--color-text);margin-bottom:6px;font-size:13px;font-weight:500;display:block}.mob-login-field input{border:1px solid var(--color-line);background:var(--color-surface);width:100%;height:48px;color:var(--color-text);border-radius:8px;padding:0 14px;font-family:inherit;font-size:15px;transition:border-color .18s}.mob-login-field input:focus{border-color:var(--color-primary);outline:none;box-shadow:0 0 0 3px #2563eb1f}.mob-login-field__hint{color:var(--color-muted);margin-top:4px;font-size:12px}.mob-login-error{color:var(--color-danger);background:var(--color-danger-bg);border:1px solid #ef44444d;border-radius:8px;margin-bottom:16px;padding:10px 14px;font-size:13px;display:none}.mob-login-error.visible{display:block}.mob-login-actions{grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;display:grid}.mob-login-actions button{width:100%;min-width:0}.mob-login-submit{justify-content:center;align-items:center;gap:6px;display:inline-flex}.mob-login-submit svg{flex-shrink:0;width:18px;height:18px}.mob-login-success{text-align:center;padding:16px 0}.mob-login-success svg{width:48px;height:48px;color:var(--color-success);margin-bottom:12px}.mob-login-success__text{color:var(--color-success);margin:0;font-size:15px;font-weight:600}@media (min-width:640px){.mob-login-overlay{justify-content:center;padding-top:24px}.mob-login-card{padding:24px}}}@layer utilities{.collapse{visibility:collapse}.invisible{visibility:hidden}.visible{visibility:visible}.sr-only{clip-path:inset(50%);white-space:nowrap;border-width:0;width:1px;height:1px;margin:-1px;padding:0;position:absolute;overflow:hidden}.absolute{position:absolute}.fixed{position:fixed}.relative{position:relative}.static{position:static}.sticky{position:sticky}.bottom-0{bottom:calc(var(--spacing)*0)}.container{width:100%}@media (min-width:40rem){.container{max-width:40rem}}@media (min-width:48rem){.container{max-width:48rem}}@media (min-width:64rem){.container{max-width:64rem}}@media (min-width:80rem){.container{max-width:80rem}}@media (min-width:96rem){.container{max-width:96rem}}.m-0{margin:calc(var(--spacing)*0)}.mx-auto{margin-inline:auto}.mt-1{margin-top:calc(var(--spacing)*1)}.mt-2{margin-top:calc(var(--spacing)*2)}.mt-3{margin-top:calc(var(--spacing)*3)}.mt-4{margin-top:calc(var(--spacing)*4)}.mt-\[18px\]{margin-top:18px}.mb-1{margin-bottom:calc(var(--spacing)*1)}.mb-1\.5{margin-bottom:calc(var(--spacing)*1.5)}.mb-2{margin-bottom:calc(var(--spacing)*2)}.mb-3{margin-bottom:calc(var(--spacing)*3)}.mb-4{margin-bottom:calc(var(--spacing)*4)}.mb-5{margin-bottom:calc(var(--spacing)*5)}.mb-7{margin-bottom:calc(var(--spacing)*7)}.mb-\[14px\]{margin-bottom:14px}.ml-1{margin-left:calc(var(--spacing)*1)}.block{display:block}.contents{display:contents}.flex{display:flex}.grid{display:grid}.hidden{display:none}.inline{display:inline}.inline-flex{display:inline-flex}.table{display:table}.\!h-\[34px\]{height:34px!important}.h-4{height:calc(var(--spacing)*4)}.h-9{height:calc(var(--spacing)*9)}.max-h-\[300px\]{max-height:300px}.min-h-20{min-height:calc(var(--spacing)*20)}.min-h-screen{min-height:100vh}.\!w-\[34px\]{width:34px!important}.\!w-auto{width:auto!important}.w-4{width:calc(var(--spacing)*4)}.w-10{width:calc(var(--spacing)*10)}.w-20{width:calc(var(--spacing)*20)}.w-24{width:calc(var(--spacing)*24)}.w-40{width:calc(var(--spacing)*40)}.w-\[60px\]{width:60px}.w-\[80px\]{width:80px}.w-\[90px\]{width:90px}.w-\[160px\]{width:160px}.w-\[180px\]{width:180px}.w-full{width:100%}.max-w-\[160px\]{max-width:160px}.max-w-\[180px\]{max-width:180px}.max-w-\[200px\]{max-width:200px}.max-w-\[220px\]{max-width:220px}.max-w-\[240px\]{max-width:240px}.max-w-\[260px\]{max-width:260px}.max-w-\[900px\]{max-width:900px}.min-w-\[60px\]{min-width:60px}.min-w-\[600px\]{min-width:600px}.flex-1{flex:1}.flex-shrink{flex-shrink:1}.shrink-0{flex-shrink:0}.border-collapse{border-collapse:collapse}.transform{transform:var(--tw-rotate-x,)var(--tw-rotate-y,)var(--tw-rotate-z,)var(--tw-skew-x,)var(--tw-skew-y,)}.cursor-pointer{cursor:pointer}.resize{resize:both}.grid-cols-1{grid-template-columns:repeat(1,minmax(0,1fr))}.grid-cols-2{grid-template-columns:repeat(2,minmax(0,1fr))}.grid-cols-\[380px_1fr\]{grid-template-columns:380px 1fr}.flex-wrap{flex-wrap:wrap}.items-center{align-items:center}.justify-between{justify-content:space-between}.justify-center{justify-content:center}.justify-end{justify-content:flex-end}.gap-1{gap:calc(var(--spacing)*1)}.gap-2{gap:calc(var(--spacing)*2)}.gap-2\.5{gap:calc(var(--spacing)*2.5)}.gap-3{gap:calc(var(--spacing)*3)}.gap-4{gap:calc(var(--spacing)*4)}.gap-5{gap:calc(var(--spacing)*5)}.gap-x-2{column-gap:calc(var(--spacing)*2)}.gap-x-2\.5{column-gap:calc(var(--spacing)*2.5)}.gap-y-0{row-gap:calc(var(--spacing)*0)}.gap-y-1{row-gap:calc(var(--spacing)*1)}.overflow-auto{overflow:auto}.overflow-hidden{overflow:hidden}.overflow-x-auto{overflow-x:auto}.rounded{border-radius:.25rem}.rounded-lg{border-radius:var(--radius-lg)}.rounded-md{border-radius:var(--radius-md)}.border{border-style:var(--tw-border-style);border-width:1px}.border-t{border-top-style:var(--tw-border-style);border-top-width:1px}.border-line{border-color:var(--color-line)}.bg-bg{background-color:var(--color-bg)}.bg-danger-bg{background-color:var(--color-danger-bg)}.bg-surface-alt{background-color:var(--color-surface-alt)}.bg-white{background-color:var(--color-white)}.p-4{padding:calc(var(--spacing)*4)}.p-6{padding:calc(var(--spacing)*6)}.p-8{padding:calc(var(--spacing)*8)}.p-\[10px_14px\]{padding:10px 14px}.px-0{padding-inline:calc(var(--spacing)*0)}.px-6{padding-inline:calc(var(--spacing)*6)}.px-\[3px\]{padding-inline:3px}.px-\[18px\]{padding-inline:18px}.py-0{padding-block:calc(var(--spacing)*0)}.py-0\.5{padding-block:calc(var(--spacing)*.5)}.py-1{padding-block:calc(var(--spacing)*1)}.py-2{padding-block:calc(var(--spacing)*2)}.py-3{padding-block:calc(var(--spacing)*3)}.py-4{padding-block:calc(var(--spacing)*4)}.pt-3{padding-top:calc(var(--spacing)*3)}.pb-\[14px\]{padding-bottom:14px}.text-center{text-align:center}.text-right{text-align:right}.font-\[family-name\:var\(--font-body\)\]{font-family:var(--font-body)}.font-\[family-name\:var\(--font-heading\)\]{font-family:var(--font-heading)}.font-mono{font-family:var(--font-mono)}.text-base{font-size:var(--text-base);line-height:var(--tw-leading,var(--text-base--line-height))}.text-sm{font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height))}.text-xl{font-size:var(--text-xl);line-height:var(--tw-leading,var(--text-xl--line-height))}.text-xs{font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height))}.text-\[11px\]{font-size:11px}.text-\[14px\]{font-size:14px}.leading-\[1\.5\]{--tw-leading:1.5;line-height:1.5}.leading-tight{--tw-leading:var(--leading-tight);line-height:var(--leading-tight)}.font-\[650\]{--tw-font-weight:650;font-weight:650}.font-bold{--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold)}.font-medium{--tw-font-weight:var(--font-weight-medium);font-weight:var(--font-weight-medium)}.font-semibold{--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold)}.tracking-\[0\.06em\]{--tw-tracking:.06em;letter-spacing:.06em}.text-ellipsis{text-overflow:ellipsis}.whitespace-nowrap{white-space:nowrap}.text-danger{color:var(--color-danger)}.text-muted{color:var(--color-muted)}.text-primary{color:var(--color-primary)}.text-success{color:var(--color-success)}.text-text{color:var(--color-text)}.uppercase{text-transform:uppercase}.overline{text-decoration-line:overline}.underline{text-decoration-line:underline}.accent-primary{accent-color:var(--color-primary)}.opacity-70{opacity:.7}.shadow{--tw-shadow:0 1px 3px 0 var(--tw-shadow-color,#0000001a),0 1px 2px -1px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow)}.outline{outline-style:var(--tw-outline-style);outline-width:1px}.grayscale{--tw-grayscale:grayscale(100%);filter:var(--tw-blur,)var(--tw-brightness,)var(--tw-contrast,)var(--tw-grayscale,)var(--tw-hue-rotate,)var(--tw-invert,)var(--tw-saturate,)var(--tw-sepia,)var(--tw-drop-shadow,)}.invert{--tw-invert:invert(100%);filter:var(--tw-blur,)var(--tw-brightness,)var(--tw-contrast,)var(--tw-grayscale,)var(--tw-hue-rotate,)var(--tw-invert,)var(--tw-saturate,)var(--tw-sepia,)var(--tw-drop-shadow,)}.filter{filter:var(--tw-blur,)var(--tw-brightness,)var(--tw-contrast,)var(--tw-grayscale,)var(--tw-hue-rotate,)var(--tw-invert,)var(--tw-saturate,)var(--tw-sepia,)var(--tw-drop-shadow,)}.backdrop-filter{-webkit-backdrop-filter:var(--tw-backdrop-blur,)var(--tw-backdrop-brightness,)var(--tw-backdrop-contrast,)var(--tw-backdrop-grayscale,)var(--tw-backdrop-hue-rotate,)var(--tw-backdrop-invert,)var(--tw-backdrop-opacity,)var(--tw-backdrop-saturate,)var(--tw-backdrop-sepia,);backdrop-filter:var(--tw-backdrop-blur,)var(--tw-backdrop-brightness,)var(--tw-backdrop-contrast,)var(--tw-backdrop-grayscale,)var(--tw-backdrop-hue-rotate,)var(--tw-backdrop-invert,)var(--tw-backdrop-opacity,)var(--tw-backdrop-saturate,)var(--tw-backdrop-sepia,)}.transition{transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to,opacity,box-shadow,transform,translate,scale,rotate,filter,-webkit-backdrop-filter,backdrop-filter,display,content-visibility,overlay,pointer-events;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration))}.select-all{-webkit-user-select:all;user-select:all}@media (min-width:64rem){.lg\:grid-cols-2{grid-template-columns:repeat(2,minmax(0,1fr))}}.scrollbar-thin{scrollbar-width:thin;scrollbar-color:var(--color-line)transparent}}@property --tw-rotate-x{syntax:"*";inherits:false}@property --tw-rotate-y{syntax:"*";inherits:false}@property --tw-rotate-z{syntax:"*";inherits:false}@property --tw-skew-x{syntax:"*";inherits:false}@property --tw-skew-y{syntax:"*";inherits:false}@property --tw-border-style{syntax:"*";inherits:false;initial-value:solid}@property --tw-leading{syntax:"*";inherits:false}@property --tw-font-weight{syntax:"*";inherits:false}@property --tw-tracking{syntax:"*";inherits:false}@property --tw-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-shadow-color{syntax:"*";inherits:false}@property --tw-shadow-alpha{syntax:"<percentage>";inherits:false;initial-value:100%}@property --tw-inset-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-inset-shadow-color{syntax:"*";inherits:false}@property --tw-inset-shadow-alpha{syntax:"<percentage>";inherits:false;initial-value:100%}@property --tw-ring-color{syntax:"*";inherits:false}@property --tw-ring-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-inset-ring-color{syntax:"*";inherits:false}@property --tw-inset-ring-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-ring-inset{syntax:"*";inherits:false}@property --tw-ring-offset-width{syntax:"<length>";inherits:false;initial-value:0}@property --tw-ring-offset-color{syntax:"*";inherits:false;initial-value:#fff}@property --tw-ring-offset-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-outline-style{syntax:"*";inherits:false;initial-value:solid}@property --tw-blur{syntax:"*";inherits:false}@property --tw-brightness{syntax:"*";inherits:false}@property --tw-contrast{syntax:"*";inherits:false}@property --tw-grayscale{syntax:"*";inherits:false}@property --tw-hue-rotate{syntax:"*";inherits:false}@property --tw-invert{syntax:"*";inherits:false}@property --tw-opacity{syntax:"*";inherits:false}@property --tw-saturate{syntax:"*";inherits:false}@property --tw-sepia{syntax:"*";inherits:false}@property --tw-drop-shadow{syntax:"*";inherits:false}@property --tw-drop-shadow-color{syntax:"*";inherits:false}@property --tw-drop-shadow-alpha{syntax:"<percentage>";inherits:false;initial-value:100%}@property --tw-drop-shadow-size{syntax:"*";inherits:false}@property --tw-backdrop-blur{syntax:"*";inherits:false}@property --tw-backdrop-brightness{syntax:"*";inherits:false}@property --tw-backdrop-contrast{syntax:"*";inherits:false}@property --tw-backdrop-grayscale{syntax:"*";inherits:false}@property --tw-backdrop-hue-rotate{syntax:"*";inherits:false}@property --tw-backdrop-invert{syntax:"*";inherits:false}@property --tw-backdrop-opacity{syntax:"*";inherits:false}@property --tw-backdrop-saturate{syntax:"*";inherits:false}@property --tw-backdrop-sepia{syntax:"*";inherits:false}@property --tw-duration{syntax:"*";inherits:false}@keyframes spin{to{transform:rotate(360deg)}}</style>
</head>
<body>

<div class="sidebar">
  <div class="sidebar-brand">
    <div class="sidebar-brand-mark" aria-hidden="true">T</div>
    <div>
      <h2 class="font-[family-name:var(--font-heading)] text-base font-bold text-text leading-tight">TRMD</h2>
      <span class="text-xs text-muted font-medium" data-i18n="app.subtitle">转存控制台</span>
    </div>
  </div>

  <div class="sidebar-nav-section">
    <div class="sidebar-nav-label" data-i18n="nav.section.main">主要功能</div>
    <button class="sidebar-nav-item active" data-nav="transfers">
      <svg viewBox="0 0 24 24" fill="none"><path d="M7 7h10M7 12h10M7 17h6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      <span data-i18n="nav.transfers">转存任务</span>
      <span class="sidebar-nav-badge" id="badge-transfers">0</span>
    </button>
    <button class="sidebar-nav-item" data-nav="watches">
      <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/><path d="M12 9v3l2 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      <span data-i18n="nav.watches">实时监听</span>
      <span class="sidebar-nav-badge" id="badge-watches">0</span>
    </button>
    <button class="sidebar-nav-item" data-nav="downloads-uploads">
      <svg viewBox="0 0 24 24" fill="none"><path d="M8 17l4 4 4-4M12 21V3M4 10l4-4 4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      <span data-i18n="nav.downloadsUploads">下载与上传</span>
    </button>

    <div class="sidebar-nav-label" data-i18n="nav.section.monitor">监控与数据</div>
    <button class="sidebar-nav-item" data-nav="statistics">
      <svg viewBox="0 0 24 24" fill="none"><path d="M5 19V9M12 19V5M19 19v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M4 19h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      <span data-i18n="nav.statistics">统计面板</span>
    </button>
    <button class="sidebar-nav-item" data-nav="records">
      <svg viewBox="0 0 24 24" fill="none"><path d="M5 4h14v16H5z" stroke="currentColor" stroke-width="2"/><path d="M8 8h8M8 12h8M8 16h5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      <span data-i18n="nav.records">下载记录</span>
    </button>
    <button class="sidebar-nav-item" data-nav="media">
      <svg viewBox="0 0 24 24" fill="none"><path d="M3 6h18M5 6v13a2 2 0 002 2h10a2 2 0 002-2V6M8 6V4a1 1 0 011-1h6a1 1 0 011 1v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      <span data-i18n="nav.media">媒体管理</span>
    </button>

    <div class="sidebar-nav-label" data-i18n="nav.section.system">系统</div>
    <button class="sidebar-nav-item" data-nav="settings">
      <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="3.5" stroke="currentColor" stroke-width="2"/><path d="M19.4 15a1.8 1.8 0 0 0 .36 1.98" stroke="currentColor" stroke-width="1.5"/></svg>
      <span data-i18n="nav.settings">系统设置</span>
    </button>

    <div class="mt-[18px] px-[3px]">
      <div class="flex items-center justify-between text-xs text-muted py-0.5">
        <span data-i18n="side.failed">失败</span>
        <strong id="metric-failed" class="text-text">0</strong>
      </div>
    </div>
  </div>

  <div class="sidebar-footer">
    <button class="sidebar-nav-item mb-1 text-muted" id="btn-logout">
      <svg viewBox="0 0 24 24" fill="none" class="opacity-70"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      <span data-i18n="nav.logout">退出登录</span>
    </button>
    <div class="sidebar-footer-info">
      <span class="sidebar-status-dot"></span>
      <span data-i18n="side.status">系统运行中</span>
    </div>
    <span class="sidebar-version">TRMD v0.3.1 · by Asheblog</span>
  </div>
</div>

<main class="main-content">

  <!-- Login container (Telegram auth flow) -->
  <div id="login-container" class="login-page login-overlay hidden">
    <div class="login-brand">
      <div class="login-brand-mark" aria-hidden="true">T</div>
      <h1>TRMD</h1>
      <p class="text-sm text-muted mt-1">Telegram 账号登录</p>
    </div>
    <div class="login-card">
      <div class="login-error" id="login-error"></div>
      <div id="login-form-phone" class="login-step">
        <div class="text-xs text-muted uppercase tracking-[0.06em] mb-2">步骤 1 / 3</div>
        <h2 class="text-xl font-bold m-0 mb-1.5 text-text">输入电话号码</h2>
        <p class="text-sm text-muted m-0 mb-5">请输入您的 Telegram 账号绑定的手机号</p>
        <div class="login-field">
          <label for="login-phone">电话号码</label>
          <input id="login-phone" type="tel" placeholder="+8615000000000" autocomplete="tel">
          <div class="text-xs text-muted mt-1">需以「+地区号」开头，如中国 +86</div>
        </div>
        <div class="flex justify-end">
          <button type="button" id="login-btn-phone" class="login-submit !w-auto px-6">
            <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            发送验证码
          </button>
        </div>
      </div>
      <div id="login-form-code" class="login-step hidden">
        <div class="text-xs text-muted uppercase tracking-[0.06em] mb-2">步骤 2 / 3</div>
        <h2 class="text-xl font-bold m-0 mb-1.5 text-text">输入验证码</h2>
        <p class="text-sm text-muted m-0 mb-5" id="login-code-desc">验证码已发送到您的设备</p>
        <div class="login-field">
          <label for="login-code">验证码</label>
          <input id="login-code" type="text" inputmode="numeric" maxlength="10" placeholder="输入验证码" autocomplete="one-time-code">
        </div>
        <div class="flex gap-2.5 justify-end">
          <button type="button" class="btn" id="login-btn-back">返回</button>
          <button type="button" id="login-btn-code" class="login-submit !w-auto px-6">
            <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            验证
          </button>
        </div>
      </div>
      <div id="login-form-password" class="login-step hidden">
        <div class="text-xs text-muted uppercase tracking-[0.06em] mb-2">步骤 2.5 / 3</div>
        <h2 class="text-xl font-bold m-0 mb-1.5 text-text">两步验证密码</h2>
        <p class="text-sm text-muted m-0 mb-5" id="login-password-hint">该账号已设置两步验证</p>
        <div class="login-field">
          <label for="login-password">密码</label>
          <input id="login-password" type="password" placeholder="输入两步验证密码" autocomplete="current-password">
          <div class="text-sm text-muted mt-1" id="login-password-hint-text"></div>
        </div>
        <div class="flex gap-2.5 justify-end">
          <button type="button" class="btn" id="login-btn-back-pwd">取消</button>
          <button type="button" id="login-btn-password" class="login-submit !w-auto px-6">
            <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            验证
          </button>
        </div>
      </div>
      <div id="login-form-recovery" class="login-step hidden">
        <div class="text-xs text-muted uppercase tracking-[0.06em] mb-2">密码恢复</div>
        <h2 class="text-xl font-bold m-0 mb-1.5 text-text">输入恢复代码</h2>
        <p class="text-sm text-muted m-0 mb-5" id="login-recovery-desc">恢复代码已发送</p>
        <div class="login-field">
          <label for="login-recovery">恢复代码</label>
          <input id="login-recovery" type="text" placeholder="输入恢复代码">
        </div>
        <div class="flex gap-2.5 justify-end">
          <button type="button" class="btn" id="login-btn-back-recovery">返回</button>
          <button type="button" id="login-btn-recovery" class="login-submit !w-auto px-6">
            <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            提交
          </button>
        </div>
      </div>
      <div id="login-form-signup" class="login-step hidden">
        <div class="text-xs text-muted uppercase tracking-[0.06em] mb-2">注册信息</div>
        <h2 class="text-xl font-bold m-0 mb-1.5 text-text">完善个人信息</h2>
        <p class="text-sm text-muted m-0 mb-5">首次登录，请输入您的名字</p>
        <div class="login-field">
          <label for="login-first-name">名字</label>
          <input id="login-first-name" type="text" placeholder="名字">
        </div>
        <div class="login-field">
          <label for="login-last-name">姓氏</label>
          <input id="login-last-name" type="text" placeholder="姓氏（可选）">
        </div>
        <div class="flex justify-end">
          <button type="button" id="login-btn-signup" class="login-submit !w-auto px-6">
            <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            完成注册
          </button>
        </div>
      </div>
      <div id="login-form-done" class="login-step hidden">
        <div class="text-center py-4">
          <svg viewBox="0 0 24 24" fill="none" width="48" height="48" class="text-success mx-auto mb-3"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M8 12l3 3 5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <p class="text-base font-semibold text-success m-0" id="login-user-name">登录成功</p>
        </div>
      </div>
    </div>
  </div>

  <!-- Top Bar -->
  <div class="topbar">
    <div>
      <h1 data-i18n="hero.title">转存控制台</h1>
      <p data-i18n="hero.body">管理 Telegram 内容转存任务 — 实时监控、批量操作、智能过滤</p>
    </div>
    <div class="flex items-center gap-2">
      <select id="language-select" aria-label="语言" class="form-input !w-auto h-9">
        <option value="zh">中文</option>
        <option value="en">English</option>
      </select>
      <button class="btn" type="button" id="refresh">
        <svg viewBox="0 0 24 24" fill="none"><path d="M20 12a8 8 0 1 1-2.34-5.66M20 4v5h-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <span data-i18n="action.refresh">刷新</span>
      </button>
    </div>
  </div>

  <!-- ====== Transfers View ====== -->
<div class="view active" id="view-transfers">
  <!-- Stat Cards -->
  <div class="stat-grid">
    <div class="stat-card">
      <div class="stat-card-icon blue">
        <svg viewBox="0 0 24 24" fill="none"><path d="M7 7h10M7 12h10M7 17h6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      </div>
      <div>
        <div class="stat-card-value" id="stat-total">0</div>
        <div class="stat-card-label">总任务</div>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-card-icon green">
        <svg viewBox="0 0 24 24" fill="none"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </div>
      <div>
        <div class="stat-card-value" id="stat-success">0</div>
        <div class="stat-card-label">已完成</div>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-card-icon orange">
        <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      </div>
      <div>
        <div class="stat-card-value" id="stat-running">0</div>
        <div class="stat-card-label">运行中</div>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-card-icon red">
        <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M15 9l-6 6M9 9l6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      </div>
      <div>
        <div class="stat-card-value" id="stat-failed">0</div>
        <div class="stat-card-label">失败项</div>
      </div>
    </div>
  </div>

  <!-- Content Grid: Form + Table -->
  <div class="grid grid-cols-[380px_1fr] gap-4">
    <!-- Transfer Form -->
    <div class="panel">
      <div class="panel-header">
        <h3 data-i18n="new.title">新建转存</h3>
      </div>
      <div class="panel-body">
        <form id="transfer-form">
          <div class="form-group">
            <label class="form-label" data-i18n="new.source">来源链接</label>
            <input class="form-input" name="source_link" type="text" placeholder="https://t.me/channel/123" required>
          </div>
          <div class="form-group">
            <label class="form-label" data-i18n="new.target">目标</label>
            <input class="form-input" name="target_link" type="text" value="https://t.me/pikpak_bot" required>
          </div>
          <div class="form-group">
            <label class="form-label" data-i18n="new.targetProfile">目标配置</label>
            <select class="form-select" name="target_profile">
              <option value="pikpak" data-i18n="profile.pikpak">PikPak 文档转存</option>
              <option value="generic" data-i18n="profile.generic">通用 Telegram 目标</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label" data-i18n="new.startId">起始 ID</label>
              <input class="form-input" name="start_id" type="number" data-i18n-placeholder="new.optional" placeholder="可选">
            </div>
            <div class="form-group">
              <label class="form-label" data-i18n="new.endId">结束 ID</label>
              <input class="form-input" name="end_id" type="number" data-i18n-placeholder="new.optional" placeholder="可选">
            </div>
          </div>
          <label class="flex items-center gap-2 text-sm text-muted cursor-pointer mb-3">
            <input type="checkbox" name="include_comment" class="w-4 h-4">
            <span data-i18n="new.includeComment">包含评论区</span>
          </label>
          <p class="text-xs text-muted leading-[1.5] mb-2" data-i18n="new.hint">
            单条消息链接可留空。频道不填 ID 会自动探测可访问范围。
          </p>
          <div id="transfer-notice" class="text-xs mt-2 hidden"></div>
          <button type="submit" class="form-submit" id="transfer-submit">
            <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
            <span data-i18n="new.create">创建任务</span>
          </button>
        </form>
      </div>
    </div>

    <!-- Task List -->
    <div class="panel">
      <div class="panel-header">
        <h3 data-i18n="tasks.title">转存任务列表</h3>
        <span class="text-xs text-muted" id="last-sync" data-i18n="tasks.notSynced">尚未同步</span>
      </div>
      <div class="overflow-auto flex-1">
        <table class="data-table">
          <thead>
            <tr>
              <th class="w-[60px]" data-i18n="tasks.id">ID</th>
              <th class="w-20" data-i18n="tasks.status">状态</th>
              <th class="w-[180px]" data-i18n="tasks.source">来源</th>
              <th class="w-20" data-i18n="tasks.target">目标</th>
              <th class="w-40" data-i18n="tasks.progress">进度</th>
              <th class="w-[90px]" data-i18n="tasks.actions">操作</th>
            </tr>
          </thead>
          <tbody id="tasks-tbody"></tbody>
        </table>
        <div id="tasks-empty" class="p-8 text-center text-muted text-sm" data-i18n="tasks.empty">还没有转存任务。</div>
      </div>
    </div>
  </div>

  <!-- Task Detail Panel -->
  <div class="panel" id="task-detail">
    <div class="p-8 text-center text-muted text-sm" data-i18n="items.selectTask">选择一个任务查看详情</div>
  </div>
</div>

<!-- ====== Watches View ====== -->
<div class="view" id="view-watches">
  <div class="grid grid-cols-2 gap-4">
    <!-- Download Watch -->
    <div class="panel">
      <div class="panel-header">
        <div class="flex items-center gap-2.5">
          <div class="stat-card-icon green !w-[34px] !h-[34px]">
            <svg viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M12 16V4M7 9l5-5 5 5M5 20h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </div>
          <div>
            <h3 data-i18n="watches.downloadTitle">监听下载</h3>
            <span class="text-xs text-muted" data-i18n="watches.downloadMeta">新消息自动下载</span>
          </div>
        </div>
      </div>
      <div class="panel-body">
        <form id="watch-download-form">
          <div class="form-group">
            <label class="form-label" data-i18n="watches.sources">来源频道（每行一个）</label>
            <textarea class="form-input watch-download-sources" name="source_links" rows="3" placeholder="https://t.me/channel1&#10;https://t.me/channel2" required></textarea>
          </div>
          <button type="submit" class="form-submit">
            <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
            <span data-i18n="watches.createDownload">新增监听下载</span>
          </button>
        </form>
      </div>
    </div>

    <!-- Forward Watch -->
    <div class="panel">
      <div class="panel-header">
        <div class="flex items-center gap-2.5">
          <div class="stat-card-icon blue !w-[34px] !h-[34px]">
            <svg viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </div>
          <div>
            <h3 data-i18n="watches.forwardTitle">监听转发</h3>
            <span class="text-xs text-muted" data-i18n="watches.forwardMeta">新消息自动转发</span>
          </div>
        </div>
      </div>
      <div class="panel-body">
        <form id="watch-forward-form">
          <div class="form-group">
            <label class="form-label" data-i18n="watches.source">来源频道</label>
            <input class="form-input" name="source_link" type="text" placeholder="https://t.me/source" required>
          </div>
          <div class="form-group">
            <label class="form-label" data-i18n="watches.target">目标频道</label>
            <input class="form-input" name="target_link" type="text" placeholder="https://t.me/target" required>
          </div>
          <label class="flex items-center gap-2 text-sm text-muted cursor-pointer mb-3">
            <input type="checkbox" name="include_comment" class="w-4 h-4">
            <span data-i18n="watches.includeComment">包含评论区</span>
          </label>
          <button type="submit" class="form-submit">
            <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
            <span data-i18n="watches.createForward">新增监听转发</span>
          </button>
        </form>
      </div>
    </div>
  </div>

  <!-- Watch List -->
  <div class="panel">
    <div class="panel-header">
      <h3 data-i18n="watches.title">活跃监听</h3>
    </div>
    <div class="overflow-auto">
      <table class="data-table">
        <thead>
          <tr>
            <th data-i18n="watches.type">类型</th>
            <th data-i18n="watches.source">来源频道</th>
            <th data-i18n="watches.target">目标频道</th>
            <th>状态</th>
            <th class="w-20" data-i18n="watches.todayEvents">今日记录</th>
            <th class="w-24">操作</th>
          </tr>
        </thead>
        <tbody id="watches-tbody"></tbody>
      </table>
      <div id="watches-empty" class="p-8 text-center text-muted text-sm" data-i18n="watches.empty">还没有实时监听。</div>
    </div>
  </div>
</div>

<!-- Watch History Overlay -->
<div class="watch-overlay" id="watch-history-overlay">
  <div class="watch-dialog watch-history-dialog">
    <div class="watch-history-header">
      <h3 class="text-base font-semibold flex items-center gap-2">
        <svg viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <span data-i18n="watches.historyTitle">监听转发记录</span>
      </h3>
      <button type="button" class="btn btn-sm btn-icon" onclick="closeWatchHistoryModal()">✕</button>
    </div>
    <div class="watch-history-body" id="watch-history-body"></div>
    <div class="watch-history-pagination" id="watch-history-pagination"></div>
  </div>
</div>

<!-- Watch Edit Overlay -->
<div class="watch-overlay" id="watch-edit-overlay">
  <div class="watch-dialog">
    <h3 class="text-base font-semibold flex items-center gap-2">
      <svg viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      <span data-i18n="watches.edit">编辑监听</span>
    </h3>
    <form id="watch-edit-form">
      <input type="hidden" name="id" id="edit-watch-id">
      <div class="form-group">
        <label class="form-label" data-i18n="watches.source">来源频道</label>
        <input class="form-input" name="source_link" id="edit-watch-source" type="text" required>
      </div>
      <div class="form-group">
        <label class="form-label" data-i18n="watches.target">目标频道</label>
        <input class="form-input" name="target_link" id="edit-watch-target" type="text" required>
      </div>
      <label class="flex items-center gap-2 text-sm text-muted cursor-pointer mb-3">
        <input type="checkbox" name="include_comment" id="edit-watch-comment" class="w-4 h-4">
        <span data-i18n="watches.includeComment">包含评论区</span>
      </label>
      <div class="flex gap-2 justify-end">
        <button type="button" class="btn" onclick="closeEditWatchModal()" data-i18n="action.cancel">取消</button>
        <button type="submit" class="btn btn-primary" data-i18n="action.save">保存</button>
      </div>
    </form>
  </div>
</div>

<!-- ====== Downloads & Uploads View ====== -->
<div class="view" id="view-downloads-uploads">
  <!-- Two-panel form row: channel download (left) + local upload (right) -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
    <!-- Channel Download -->
    <div class="panel">
      <div class="panel-header">
        <div class="flex items-center gap-2.5">
          <div class="stat-card-icon green !w-[34px] !h-[34px]">
            <svg viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M5 5h14v10H8l-3 3V5Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>
          </div>
          <div>
            <h3 data-i18n="dl.title">频道下载</h3>
            <span class="text-xs text-muted" data-i18n="dl.meta">从 Telegram 频道拉取文件</span>
          </div>
        </div>
      </div>
      <div class="panel-body">
        <form id="channel-download-form">
          <div class="form-group">
            <label class="form-label" data-i18n="dl.link">频道链接</label>
            <input class="form-input" name="chat_link" type="text" placeholder="https://t.me/channel" required>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label" data-i18n="dl.startDate">起始时间</label>
              <input class="form-input" name="start_date" type="datetime-local">
            </div>
            <div class="form-group">
              <label class="form-label" data-i18n="dl.endDate">结束时间</label>
              <input class="form-input" name="end_date" type="datetime-local">
            </div>
          </div>
          <div class="form-group">
            <label class="form-label" data-i18n="dl.keywords">关键词</label>
            <input class="form-input" name="keywords" type="text" data-i18n-placeholder="dl.keywordsPlaceholder" placeholder="逗号分隔，可留空">
          </div>
          <fieldset class="border border-line rounded-md p-[10px_14px] mb-[14px]">
            <legend class="text-sm font-semibold text-muted" data-i18n="dl.types">下载类型</legend>
            <div class="grid grid-cols-2 gap-y-1 gap-x-2.5" id="dl-download-type-grid"></div>
          </fieldset>
          <label class="flex items-center gap-2 text-sm text-muted cursor-pointer mb-3">
            <input type="checkbox" name="include_comment" class="w-4 h-4">
            <span data-i18n="dl.includeComment">包含评论区</span>
          </label>
          <button type="submit" class="form-submit">
            <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M12 16V4M7 9l5-5 5 5M5 20h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span data-i18n="dl.create">创建下载任务</span>
          </button>
        </form>
      </div>
    </div>

    <!-- Local Upload -->
    <div class="panel">
      <div class="panel-header">
        <div class="flex items-center gap-2.5">
          <div class="stat-card-icon blue !w-[34px] !h-[34px]">
            <svg viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M12 16V4M7 9l5-5 5 5M5 20h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </div>
          <div>
            <h3 data-i18n="dl.uploadTitle">本地上传</h3>
            <span class="text-xs text-muted" data-i18n="dl.uploadMeta">推送到 Telegram 频道</span>
          </div>
        </div>
      </div>
      <div class="panel-body">
        <form id="upload-form">
          <div class="form-group">
            <label class="form-label" data-i18n="dl.uploadPath">本地路径</label>
            <input class="form-input" name="path" type="text" placeholder="/data/files/movie.mp4" required>
          </div>
          <div class="form-group">
            <label class="form-label" data-i18n="dl.uploadTarget">目标频道</label>
            <input class="form-input" name="target_link" type="text" placeholder="https://t.me/target" required>
          </div>
          <label class="flex items-center gap-2 text-sm text-muted cursor-pointer mb-3">
            <input type="checkbox" name="recursive" class="w-4 h-4">
            <span data-i18n="dl.recursive">递归上传文件夹</span>
          </label>
          <div class="download-upload-align-spacer" role="note">
            <span data-i18n="dl.uploadPlaceholder">占位区，待后续开发</span>
          </div>
          <button type="submit" class="form-submit">
            <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M12 16V4M7 9l5-5 5 5M5 20h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span data-i18n="dl.createUpload">创建上传任务</span>
          </button>
        </form>
      </div>
    </div>
  </div>

  <!-- Operation History -->
  <div class="panel">
    <div class="panel-header">
      <h3 data-i18n="dl.history">操作历史</h3>
      <button class="btn btn-sm" id="dl-history-refresh">
        <svg viewBox="0 0 24 24" fill="none" width="14" height="14"><path d="M20 12a8 8 0 1 1-2.34-5.66M20 4v5h-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <span data-i18n="action.refresh">刷新</span>
      </button>
    </div>
    <div class="overflow-auto">
      <table class="data-table">
        <thead>
          <tr>
            <th class="w-[80px]" data-i18n="dl.historyId">ID</th>
            <th class="w-24" data-i18n="dl.historyType">类型</th>
            <th data-i18n="dl.historyDetail">详情</th>
            <th class="w-24" data-i18n="dl.historyStatus">状态</th>
            <th class="w-40" data-i18n="dl.historyError">错误信息</th>
            <th class="w-[160px]" data-i18n="dl.historyTime">创建时间</th>
          </tr>
        </thead>
        <tbody id="dl-operations-tbody"></tbody>
      </table>
      <div id="dl-operations-empty" class="p-8 text-center text-muted text-sm" data-i18n="dl.historyEmpty">还没有下载或上传操作记录。</div>
    </div>
  </div>
</div>

<!-- ====== Statistics View ====== -->
<div class="view" id="view-statistics">
  <div class="panel">
    <div class="panel-header">
      <h3 data-i18n="statistics.title">统计与导出</h3>
    </div>
    <div class="overflow-auto">
      <table class="data-table">
        <thead>
          <tr>
            <th data-i18n="statistics.table">表格</th>
            <th data-i18n="statistics.available">可用</th>
            <th data-i18n="statistics.rows">行数</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody id="statistics-tbody"></tbody>
      </table>
    </div>
  </div>
</div>

<!-- ====== Records View ====== -->
<div class="view" id="view-records">
  <div class="panel">
    <div class="panel-header">
      <h3 data-i18n="records.title">下载记录</h3>
      <button class="btn btn-danger btn-sm" id="records-clear-btn" disabled data-i18n="records.clear">清空记录</button>
    </div>
    <div class="overflow-auto">
      <table class="data-table">
        <thead>
          <tr>
            <th data-i18n="records.chat">频道 ID</th>
            <th data-i18n="records.message">消息 ID</th>
            <th data-i18n="records.file">文件</th>
            <th data-i18n="records.size">大小</th>
            <th data-i18n="records.updated">更新时间</th>
          </tr>
        </thead>
        <tbody id="records-tbody"></tbody>
      </table>
      <div id="records-empty" class="p-8 text-center text-muted text-sm" data-i18n="records.empty">还没有下载成功记录。</div>
    </div>
    <div id="records-pagination"></div>
  </div>
</div>

<!-- ====== Media View ====== -->
<div class="view" id="view-media">
  <div class="panel">
    <div class="panel-header">
      <h3 data-i18n="media.title">媒体管理</h3>
      <div class="flex items-center gap-2" id="media-actions">
        <button class="btn btn-danger btn-sm" id="media-cleanup-btn" disabled data-i18n="media.cleanup">清理选中文件</button>
        <button class="btn btn-primary btn-sm" id="media-scan-btn">
          <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M20 12a8 8 0 1 1-2.34-5.66M20 4v5h-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span data-i18n="media.scan">扫描可清理文件</span>
        </button>
      </div>
    </div>
    <div class="panel-body">
      <div id="media-result" class="hidden">
        <div id="media-summary" class="flex gap-5 flex-wrap p-4 bg-surface-alt rounded-lg mb-4"></div>

        <div id="media-items-section" class="mb-4 hidden">
          <h4 class="text-base font-semibold mb-2" data-i18n="media.transferItems">转存任务文件</h4>
          <div class="overflow-x-auto rounded-lg border border-line">
            <table class="data-table min-w-[600px]">
              <thead><tr>
                <th class="w-10"><input type="checkbox" id="media-select-all-items"></th>
                <th data-i18n="media.file">文件</th>
                <th data-i18n="media.size" class="text-right">大小</th>
                <th data-i18n="media.status" class="text-center">状态</th>
                <th data-i18n="media.source">来源</th>
              </tr></thead>
              <tbody id="media-items-tbody"></tbody>
            </table>
          </div>
        </div>

        <div id="media-orphans-section" class="mb-4 hidden">
          <h4 class="text-base font-semibold mb-2" data-i18n="media.orphanFiles">遗留文件</h4>
          <div class="overflow-x-auto rounded-lg border border-line">
            <table class="data-table min-w-[600px]">
              <thead><tr>
                <th class="w-10"><input type="checkbox" id="media-select-all-orphans"></th>
                <th data-i18n="media.path">路径</th>
                <th data-i18n="media.size" class="text-right">大小</th>
                <th data-i18n="media.mtime">最后修改</th>
              </tr></thead>
              <tbody id="media-orphans-tbody"></tbody>
            </table>
          </div>
        </div>
      </div>

    </div>
  </div>
</div>

<!-- ====== Settings View ====== -->
<div class="view" id="view-settings">
  <div class="panel">
    <div class="panel-header">
      <h3 data-i18n="settings.title">系统设置</h3>
      <span class="text-xs text-muted" data-i18n="settings.safeNote">敏感字段只显示是否已配置</span>
    </div>
    <div class="panel-body max-w-[900px]" id="settings-body">

      <!-- Paths -->
      <div class="border border-line rounded-lg p-4 mb-[14px]">
        <h4 class="text-base font-semibold mb-3" data-i18n="settings.paths">路径与任务</h4>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label" data-i18n="settings.saveDirectory">保存目录</label>
            <input class="form-input" name="user.save_directory">
          </div>
          <div class="form-group">
            <label class="form-label" data-i18n="settings.tempDirectory">临时目录</label>
            <input class="form-input" name="user.temp_directory">
          </div>
        </div>
        <div class="form-group">
          <label class="form-label" data-i18n="settings.sessionDirectory">会话目录</label>
          <input class="form-input" name="user.session_directory">
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label" data-i18n="settings.maxDownload">最大下载任务</label>
            <input class="form-input" name="user.max_tasks.download" type="number" min="1">
          </div>
          <div class="form-group">
            <label class="form-label" data-i18n="settings.maxUpload">最大上传任务</label>
            <input class="form-input" name="user.max_tasks.upload" type="number" min="1">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label" data-i18n="settings.retryDownload">下载重试</label>
            <input class="form-input" name="user.max_retries.download" type="number" min="0">
          </div>
          <div class="form-group">
            <label class="form-label" data-i18n="settings.retryUpload">上传重试</label>
            <input class="form-input" name="user.max_retries.upload" type="number" min="0">
          </div>
        </div>
        <div class="form-group">
          <label class="form-label" data-i18n="settings.pikpakMaxFileSize">PikPak大小上限(字节)</label>
          <input class="form-input" name="global.target_profiles.pikpak.max_file_size" type="number" min="1">
        </div>
      </div>

      <!-- Behavior -->
      <div class="border border-line rounded-lg p-4 mb-[14px]">
        <h4 class="text-base font-semibold mb-3" data-i18n="settings.behavior">行为</h4>
        <div class="form-row">
          <label class="flex items-center gap-2 text-sm text-text cursor-pointer">
            <input type="checkbox" name="global.notice" class="w-4 h-4">
            <span data-i18n="settings.notice">机器人通知</span>
          </label>
          <label class="flex items-center gap-2 text-sm text-text cursor-pointer">
            <input type="checkbox" name="user.is_shutdown" class="w-4 h-4">
            <span data-i18n="settings.shutdown">退出后关机</span>
          </label>
          <label class="flex items-center gap-2 text-sm text-text cursor-pointer">
            <input type="checkbox" name="global.upload.download_upload" class="w-4 h-4">
            <span data-i18n="settings.downloadUpload">受限转发时下载后上传</span>
          </label>
          <label class="flex items-center gap-2 text-sm text-text cursor-pointer">
            <input type="checkbox" name="global.upload.delete" class="w-4 h-4">
            <span data-i18n="settings.uploadDelete">上传完成删除本地文件</span>
          </label>
        </div>
        <div class="form-group mt-3">
          <label class="form-label" data-i18n="settings.pendingLimit">下载后上传队列</label>
          <input class="form-input" name="global.upload.pending_limit" type="number" min="1" max="5">
        </div>
      </div>

      <!-- PikPak Archive -->
      <div class="border border-line rounded-lg p-4 mb-[14px]">
        <h4 class="text-base font-semibold mb-3" data-i18n="settings.pikpakArchive">PikPak 归档</h4>
        <label class="flex items-center gap-2 text-sm text-text cursor-pointer mb-3">
          <input type="checkbox" name="global.target_profiles.pikpak.archive.enable" class="w-4 h-4">
          <span data-i18n="settings.pikpakArchiveEnable">PikPak按来源频道归档</span>
        </label>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label" data-i18n="settings.pikpakArchiveRemote">PikPak rclone remote</label>
            <input class="form-input" name="global.target_profiles.pikpak.archive.remote">
          </div>
          <div class="form-group">
            <label class="form-label" data-i18n="settings.pikpakArchiveSource">PikPak入库目录</label>
            <input class="form-input" name="global.target_profiles.pikpak.archive.source_directory">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label" data-i18n="settings.pikpakArchiveRoot">PikPak归档根目录</label>
            <input class="form-input" name="global.target_profiles.pikpak.archive.root_directory">
          </div>
          <div class="form-group">
            <label class="form-label" data-i18n="settings.pikpakArchivePoll">入库轮询秒数</label>
            <input class="form-input" name="global.target_profiles.pikpak.archive.poll_seconds" type="number" min="0">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label" data-i18n="settings.pikpakArchiveInterval">轮询间隔秒数</label>
            <input class="form-input" name="global.target_profiles.pikpak.archive.poll_interval_seconds" type="number" min="0">
          </div>
          <div class="form-group">
            <label class="form-label" data-i18n="settings.pikpakArchiveWindow">匹配时间窗口秒数</label>
            <input class="form-input" name="global.target_profiles.pikpak.archive.match_window_seconds" type="number" min="0">
          </div>
        </div>
      </div>

      <!-- Account & Proxy -->
      <div class="border border-line rounded-lg p-4 mb-[14px]">
        <h4 class="text-base font-semibold mb-3" data-i18n="settings.sensitive">账号与代理</h4>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">API ID</label>
            <input class="form-input" name="user.api_id">
          </div>
          <div class="form-group">
            <label class="form-label">API Hash</label>
            <input class="form-input" name="user.api_hash" type="password" data-i18n-placeholder="settings.secretConfigured" placeholder="已配置">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Bot Token</label>
            <input class="form-input" name="user.bot_token" type="password" data-i18n-placeholder="settings.secretConfigured" placeholder="已配置">
          </div>
          <div class="form-group">
            <label class="form-label" data-i18n="settings.proxyPassword">代理密码</label>
            <input class="form-input" name="user.proxy.password" type="password" data-i18n-placeholder="settings.secretConfigured" placeholder="已配置">
          </div>
        </div>
      </div>

      <!-- Download Types -->
      <div class="border border-line rounded-lg p-4 mb-[14px]">
        <h4 class="text-base font-semibold mb-3" data-i18n="settings.downloadTypes">下载类型</h4>
        <span class="text-xs text-muted" data-i18n="settings.downloadTypesHint">（勾选 = 允许下载，未勾选的类型将被忽略）</span>
        <div class="grid grid-cols-2 gap-2 mt-1" id="download-type-grid"></div>
      </div>

      <!-- Forward Types -->
      <div class="border border-line rounded-lg p-4 mb-[14px]">
        <h4 class="text-base font-semibold mb-3" data-i18n="settings.forwardTypes">转发类型</h4>
        <span class="text-xs text-muted" data-i18n="settings.forwardTypesHint">（勾选 = 允许转发，未勾选的类型将被忽略）</span>
        <div class="grid grid-cols-2 gap-2 mt-1" id="forward-type-grid"></div>
      </div>

      <!-- Message Filter -->
      <div class="border border-line rounded-lg p-4 mb-[14px]">
        <h4 class="text-base font-semibold mb-3" data-i18n="settings.messageFilter">消息过滤</h4>
        <label class="flex items-center gap-2 text-sm text-text cursor-pointer mb-3">
          <input type="checkbox" name="global.message_filter.enabled" class="w-4 h-4">
          <span data-i18n="settings.enabled">启用消息过滤</span>
        </label>
        <div class="mb-3">
          <span class="form-label" data-i18n="settings.mediaTypes">媒体类型</span>
          <span class="text-xs text-muted ml-1" data-i18n="settings.mediaTypesHint">（勾选 = 允许处理，未勾选的类型将被过滤）</span>
          <div class="grid grid-cols-2 gap-2 mt-1" id="filter-media-grid"></div>
        </div>
        <div class="mb-3">
          <label class="flex items-center gap-2 text-sm text-text cursor-pointer mb-2">
            <input type="checkbox" name="global.message_filter.date_range.enabled" class="w-4 h-4">
            <span data-i18n="settings.dateRange">日期范围过滤</span>
          </label>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label" data-i18n="settings.startDate">起始日期</label>
              <input class="form-input" name="global.message_filter.date_range.start_date" type="datetime-local">
            </div>
            <div class="form-group">
              <label class="form-label" data-i18n="settings.endDate">结束日期</label>
              <input class="form-input" name="global.message_filter.date_range.end_date" type="datetime-local">
            </div>
          </div>
        </div>
        <div>
          <label class="flex items-center gap-2 text-sm text-text cursor-pointer mb-2">
            <input type="checkbox" name="global.message_filter.keywords.enabled" class="w-4 h-4">
            <span data-i18n="settings.keywords">关键词过滤</span>
          </label>
          <div class="form-group">
            <label class="form-label" data-i18n="settings.keywordList">关键词列表（逗号分隔）</label>
            <input class="form-input" name="global.message_filter.keywords.words" data-i18n-placeholder="settings.keywordPlaceholder" placeholder="广告,推广,赞助">
          </div>
        </div>
      </div>

      <!-- Export Tables -->
      <div class="border border-line rounded-lg p-4 mb-[14px]">
        <h4 class="text-base font-semibold mb-3" data-i18n="settings.exports">导出表格</h4>
        <div class="grid grid-cols-2 gap-2">
          <label class="flex items-center gap-2 text-sm text-text cursor-pointer">
            <input type="checkbox" name="global.export_table.link" class="w-4 h-4">
            <span data-i18n="settings.exportLink">链接统计表</span>
          </label>
          <label class="flex items-center gap-2 text-sm text-text cursor-pointer">
            <input type="checkbox" name="global.export_table.count" class="w-4 h-4">
            <span data-i18n="settings.exportCount">计数统计表</span>
          </label>
          <label class="flex items-center gap-2 text-sm text-text cursor-pointer">
            <input type="checkbox" name="global.export_table.upload" class="w-4 h-4">
            <span data-i18n="settings.exportUpload">上传统计表</span>
          </label>
        </div>
      </div>

      <div class="flex items-center justify-between gap-3 sticky bottom-0 bg-white py-3 border-t border-line mt-2">
        <div id="settings-notice" class="text-xs hidden"></div>
        <button class="btn btn-primary" id="settings-save">
          <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span data-i18n="settings.save">保存设置</span>
        </button>
      </div>
    </div>
  </div>
</div>


</main>

<script>/* TRMD WebUI - Shared JavaScript (i18n + utilities) */

const i18n = {
  zh: {
    'app.title': 'TRMD · 转存控制台',
    'app.subtitle': '转存控制台',
    'nav.section.main': '主要功能',
    'nav.section.monitor': '监控与数据',
    'nav.section.system': '系统',
    'nav.transfers': '转存任务',
    'nav.watches': '实时监听',
    'nav.downloadsUploads': '下载与上传',
    'nav.statistics': '统计面板',
    'nav.settings': '系统设置',
    'nav.records': '下载记录',
    'nav.media': '媒体管理',
    'nav.profile': '我的',
    'nav.logout': '退出登录',
    'side.failed': '失败项',
    'side.status': '系统运行中',
    'hero.title': '转存控制台',
    'hero.body': '管理 Telegram 内容转存任务 — 实时监控、批量操作、智能过滤',
    'action.refresh': '刷新',
    'new.title': '新建转存',
    'new.source': '来源链接',
    'new.target': '目标',
    'new.targetProfile': '目标配置',
    'profile.pikpak': 'PikPak 文档转存',
    'profile.generic': '通用 Telegram 目标',
    'new.startId': '起始 ID',
    'new.endId': '结束 ID',
    'new.optional': '可选',
    'new.includeComment': '包含评论区',
    'new.hint': '单条消息链接可留空。频道或群链接不填 ID 时会自动探测可访问范围，也可手动指定起止 ID。',
    'new.create': '创建任务',
    'watches.title': '活跃监听',
    'watches.downloadTitle': '监听下载',
    'watches.downloadMeta': '新消息自动下载',
    'watches.forwardTitle': '监听转发',
    'watches.forwardMeta': '新消息自动转发',
    'watches.type': '类型',
    'watches.source': '来源频道',
    'watches.target': '目标频道',
    'watches.sources': '来源频道（每行一个）',
    'watches.includeComment': '包含评论区',
    'watches.createDownload': '新增监听下载',
    'watches.createForward': '新增监听转发',
    'watches.empty': '还没有实时监听。',
    'watches.delete': '移除',
    'watches.edit': '编辑',
    'watches.download': '监听下载',
    'watches.forward': '监听转发',
    'watches.created': '实时监听已创建。',
    'watches.deleted': '实时监听已移除。',
    'watches.updated': '实时监听已更新。',
    'watches.events': '转发记录',
    'watches.todayEvents': '今日记录',
    'watches.allEvents': '完整记录',
    'watches.history': '记录',
    'watches.historyTitle': '监听转发记录',
    'watches.pageInfo': '第 {page} / {pages} 页 · 共 {total} 条',
    'watches.noEvents': '暂无转发记录',
    'watches.eventForwarded': '转发成功',
    'watches.eventSkipped': '已过滤',
    'watches.eventLoading': '加载中…',
    'watches.loadMore': '加载更多',
    'watches.targetRequired': '目标频道为必填项。',
    'watches.sourceRequired': '来源频道为必填项。',
    'action.cancel': '取消',
    'action.save': '保存',
    // merged downloads & uploads page
    'dl.title': '频道下载',
    'dl.meta': '从 Telegram 频道拉取文件',
    'dl.link': '频道链接',
    'dl.startDate': '起始时间',
    'dl.endDate': '结束时间',
    'dl.keywords': '关键词',
    'dl.keywordsPlaceholder': '逗号分隔，可留空',
    'dl.types': '下载类型',
    'dl.includeComment': '包含评论区',
    'dl.create': '创建下载任务',
    'dl.accepted': '频道下载任务已创建。',
    'dl.uploadTitle': '本地上传',
    'dl.uploadMeta': '推送到 Telegram 频道',
    'dl.uploadPath': '本地路径',
    'dl.uploadTarget': '目标频道',
    'dl.recursive': '递归上传文件夹',
    'dl.uploadPlaceholder': '占位区，待后续开发',
    'dl.createUpload': '创建上传任务',
    'dl.uploadAccepted': '上传任务已创建。',
    'dl.history': '操作历史',
    'dl.historyId': 'ID',
    'dl.historyType': '类型',
    'dl.historyDetail': '详情',
    'dl.historyStatus': '状态',
    'dl.historyError': '错误信息',
    'dl.historyTime': '创建时间',
    'dl.historyEmpty': '还没有下载或上传操作记录。',
    'dl.typeDownload': '频道下载',
    'dl.typeUpload': '本地上传',
    'statistics.title': '统计与导出',
    'statistics.table': '表格',
    'statistics.available': '可用',
    'statistics.rows': '行数',
    'statistics.yes': '是',
    'statistics.no': '否',
    'statistics.link': '链接统计表',
    'statistics.count': '计数统计表',
    'statistics.upload': '上传统计表',
    'statistics.exportLink': '导出链接统计表',
    'statistics.exportCount': '导出计数统计表',
    'statistics.exportUpload': '导出上传统计表',
    'statistics.exported': '统计表已导出。',
    'tasks.title': '转存任务列表',
    'tasks.notSynced': '尚未同步',
    'tasks.id': 'ID',
    'tasks.status': '状态',
    'tasks.source': '来源',
    'tasks.target': '目标',
    'tasks.progress': '进度',
    'tasks.actions': '操作',
    'tasks.pause': '暂停',
    'tasks.resume': '继续',
    'tasks.retryFailed': '重试失败',
    'tasks.delete': '删除',
    'tasks.empty': '还没有转存任务。',
    'items.title': '文件进度',
    'items.selectTask': '选择一个任务查看详情',
    'items.empty': '该任务还没有文件记录。',
    'items.tab.running': '进行中',
    'items.tab.success': '已完成',
    'items.tab.skipped': '跳过',
    'items.tab.failure': '失败',
    'items.retryFailed': '重试失败项',
    'items.page.previous': '上一页',
    'items.page.next': '下一页',
    'pagination.pageInfo': '第 {page} / {pages} 页 · 共 {total} 条',
    'events.title': '最近事件',
    'events.empty': '没有事件记录。',
    'events.loadMore': '加载更多',
    'settings.title': '系统设置',
    'settings.safeNote': '敏感字段只显示是否已配置',
    'settings.paths': '路径与任务',
    'settings.saveDirectory': '保存目录',
    'settings.tempDirectory': '临时目录',
    'settings.sessionDirectory': '会话目录',
    'settings.maxDownload': '最大下载任务',
    'settings.maxUpload': '最大上传任务',
    'settings.retryDownload': '下载重试',
    'settings.retryUpload': '上传重试',
    'settings.pikpakMaxFileSize': 'PikPak大小上限(字节)',
    'settings.pikpakArchive': 'PikPak 归档',
    'settings.pikpakArchiveEnable': 'PikPak按来源频道归档',
    'settings.pikpakArchiveRemote': 'PikPak rclone remote',
    'settings.pikpakArchiveSource': 'PikPak入库目录',
    'settings.pikpakArchiveRoot': 'PikPak归档根目录',
    'settings.pikpakArchivePoll': '入库轮询秒数',
    'settings.pikpakArchiveInterval': '轮询间隔秒数',
    'settings.pikpakArchiveWindow': '匹配时间窗口秒数',
    'settings.behavior': '行为',
    'settings.notice': '机器人通知',
    'settings.shutdown': '退出后关机',
    'settings.downloadUpload': '受限转发时下载后上传',
    'settings.uploadDelete': '上传完成删除本地文件',
    'settings.pendingLimit': '下载后上传队列',
    'settings.sensitive': '账号与代理',
    'settings.proxyPassword': '代理密码',
    'settings.secretConfigured': '已配置，如需更换请填写',
    'settings.downloadTypes': '下载类型',
    'settings.downloadTypesHint': '（勾选 = 允许下载，未勾选的类型将被忽略）',
    'settings.forwardTypes': '转发类型',
    'settings.forwardTypesHint': '（勾选 = 允许转发，未勾选的类型将被忽略）',
    'settings.messageFilter': '消息过滤',
    'settings.mediaTypes': '媒体类型',
    'settings.mediaTypesHint': '（勾选 = 允许处理，未勾选的类型将被过滤）',
    'settings.dateRange': '日期范围',
    'settings.keywords': '关键词',
    'settings.enabled': '启用',
    'settings.startDate': '起始日期',
    'settings.endDate': '结束日期',
    'settings.keywordList': '关键词列表（逗号分隔）',
    'settings.keywordPlaceholder': '输入关键词,用逗号分隔',
    'settings.exports': '导出表格',
    'settings.exportLink': '链接统计表',
    'settings.exportCount': '计数统计表',
    'settings.exportUpload': '上传统计表',
    'settings.save': '保存设置',
    'settings.saved': '设置已保存。',
    'records.title': '下载记录',
    'records.chat': '频道 ID',
    'records.message': '消息 ID',
    'records.file': '文件',
    'records.size': '大小',
    'records.updated': '更新时间',
    'records.empty': '还没有下载成功记录。',
    'records.clear': '清空记录',
    'records.confirmClear': '确定清空全部下载记录？此操作不可撤销。',
    'records.cleared': '下载记录已清空。',
    'form.createFailed': '创建失败。',
    'form.requestFailed': '请求失败。',
    'form.creatingTransfer': '正在分析来源消息范围…',
    'form.creatingTransferShort': '分析中…',
    'form.createSuccess': '任务已创建，正在排队处理。',
    'media.title': '媒体管理',
    'media.scan': '扫描可清理文件',
    'media.scanning': '正在扫描…',
    'media.totalFiles': '可清理文件',
    'media.totalSize': '总大小',
    'media.retentionDays': '保留天数',
    'media.transferItems': '转存任务文件',
    'media.orphanFiles': '遗留文件',
    'media.file': '文件',
    'media.size': '大小',
    'media.status': '状态',
    'media.source': '来源',
    'media.path': '路径',
    'media.mtime': '最后修改',
    'media.cleanup': '清理选中文件',
    'media.cleaning': '清理中…',
    'media.selected': '已选',
    'media.files': '个文件',
    'media.noSelection': '请先选择要清理的文件。',
    'media.confirmCleanup': '确定要删除选中的文件吗？此操作不可撤销。',
    'media.cleanupDone': '清理完成：已删除 {count} 个文件 ({size})。',
    'media.cleanupHistory': '清理历史',
    'media.empty': '没有可清理文件',
    'media.reason': '原因',
    'media.time': '时间',
    'media.filterByTask': '按任务筛选：',
    'media.allTasks': '全部任务',
    'status.pending': '排队中',
    'status.running': '运行中',
    'status.paused': '已暂停',
    'status.success': '已完成',
    'status.failure': '失败',
    'status.skipped': '跳过',
    'event.level.info': '信息',
    'event.level.warning': '警告',
    'event.level.error': '错误',
    'error.auth_required': '需要登录。',
    'error.invalid_task_id': '任务 ID 无效。',
    'error.task_not_found': '找不到任务。',
    'error.source_link_required': '请填写来源链接。',
    'error.target_link_required': '请填写目标链接。',
    'error.range_ids_required': '起始 ID 和结束 ID 必须同时填写。',
    'error.range_end_before_start': '结束 ID 必须大于或等于起始 ID。',
    'error.invalid_payload': '请求内容无效。',
  },
  en: {
    'app.subtitle': 'Transfer Console',
    'nav.section.main': 'Main',
    'nav.section.monitor': 'Monitor & Data',
    'nav.section.system': 'System',
    'nav.transfers': 'Transfer Tasks',
    'nav.watches': 'Live Watches',
    'nav.downloadsUploads': 'DL & Upload',
    'nav.statistics': 'Statistics',
    'nav.settings': 'Settings',
    'nav.records': 'Records',
    'nav.media': 'Media Mgmt',
    'nav.profile': 'Me',
    'nav.logout': 'Log Out',
    'side.failed': 'Failed items',
    'side.status': 'System running',
    'hero.title': 'Transfer Console',
    'hero.body': 'Manage Telegram content transfer tasks — live monitoring, batch operations, smart filtering',
    'action.refresh': 'Refresh',
    'new.title': 'New Transfer',
    'new.source': 'Source link',
    'new.target': 'Target',
    'new.targetProfile': 'Target profile',
    'profile.pikpak': 'PikPak Document Transfer',
    'profile.generic': 'Generic Telegram Target',
    'new.startId': 'Start ID',
    'new.endId': 'End ID',
    'new.optional': 'Optional',
    'new.includeComment': 'Include comments',
    'new.hint': 'Leave IDs empty for message links. Channel links auto-detect range if IDs omitted.',
    'new.create': 'Create task',
    'watches.title': 'Active Watches',
    'watches.downloadTitle': 'Download Watch',
    'watches.downloadMeta': 'Auto-download new messages',
    'watches.forwardTitle': 'Forward Watch',
    'watches.forwardMeta': 'Auto-forward new messages',
    'watches.type': 'Type',
    'watches.source': 'Source channel',
    'watches.target': 'Target channel',
    'watches.sources': 'Source channels (one per line)',
    'watches.includeComment': 'Include comments',
    'watches.createDownload': 'Add download watch',
    'watches.createForward': 'Add forward watch',
    'watches.empty': 'No live watches yet.',
    'watches.delete': 'Remove',
    'watches.edit': 'Edit',
    'watches.download': 'Download watch',
    'watches.forward': 'Forward watch',
    'watches.created': 'Live watch created.',
    'watches.deleted': 'Live watch removed.',
    'watches.updated': 'Live watch updated.',
    'watches.events': 'Forward log',
    'watches.todayEvents': 'Today',
    'watches.allEvents': 'Full log',
    'watches.history': 'Log',
    'watches.historyTitle': 'Forward watch log',
    'watches.pageInfo': 'Page {page} / {pages} · {total} total',
    'watches.noEvents': 'No forwarding events yet.',
    'watches.eventForwarded': 'Forwarded',
    'watches.eventSkipped': 'Filtered',
    'watches.eventLoading': 'Loading…',
    'watches.loadMore': 'Load more',
    'watches.targetRequired': 'Target link is required.',
    'watches.sourceRequired': 'Source link is required.',
    'action.cancel': 'Cancel',
    'action.save': 'Save',
    // merged downloads & uploads page
    'dl.title': 'Channel Download',
    'dl.meta': 'Pull files from Telegram channels',
    'dl.link': 'Channel link',
    'dl.startDate': 'Start time',
    'dl.endDate': 'End time',
    'dl.keywords': 'Keywords',
    'dl.keywordsPlaceholder': 'Comma-separated, optional',
    'dl.types': 'Download types',
    'dl.includeComment': 'Include comments',
    'dl.create': 'Create download',
    'dl.accepted': 'Channel download task created.',
    'dl.uploadTitle': 'Local Upload',
    'dl.uploadMeta': 'Push files to Telegram channel',
    'dl.uploadPath': 'Local path',
    'dl.uploadTarget': 'Target channel',
    'dl.recursive': 'Upload folder recursively',
    'dl.uploadPlaceholder': 'Placeholder, future work',
    'dl.createUpload': 'Create upload',
    'dl.uploadAccepted': 'Upload task created.',
    'dl.history': 'Operation History',
    'dl.historyId': 'ID',
    'dl.historyType': 'Type',
    'dl.historyDetail': 'Detail',
    'dl.historyStatus': 'Status',
    'dl.historyError': 'Error',
    'dl.historyTime': 'Created',
    'dl.historyEmpty': 'No download or upload operations yet.',
    'dl.typeDownload': 'Channel DL',
    'dl.typeUpload': 'Local Upload',
    'statistics.title': 'Statistics & Export',
    'statistics.table': 'Table',
    'statistics.available': 'Available',
    'statistics.rows': 'Rows',
    'statistics.yes': 'Yes',
    'statistics.no': 'No',
    'statistics.link': 'Link table',
    'statistics.count': 'Count table',
    'statistics.upload': 'Upload table',
    'statistics.exportLink': 'Export link table',
    'statistics.exportCount': 'Export count table',
    'statistics.exportUpload': 'Export upload table',
    'statistics.exported': 'Table exported.',
    'tasks.title': 'Transfer Tasks',
    'tasks.notSynced': 'Not synced',
    'tasks.id': 'ID',
    'tasks.status': 'Status',
    'tasks.source': 'Source',
    'tasks.target': 'Target',
    'tasks.progress': 'Progress',
    'tasks.actions': 'Actions',
    'tasks.pause': 'Pause',
    'tasks.resume': 'Resume',
    'tasks.retryFailed': 'Retry failed',
    'tasks.delete': 'Delete',
    'tasks.empty': 'No transfer tasks yet.',
    'items.title': 'File Progress',
    'items.selectTask': 'Select a task to view details',
    'items.empty': 'No file records for this task yet.',
    'items.tab.running': 'Running',
    'items.tab.success': 'Completed',
    'items.tab.skipped': 'Skipped',
    'items.tab.failure': 'Failed',
    'items.retryFailed': 'Retry failed',
    'items.page.previous': 'Prev',
    'items.page.next': 'Next',
    'pagination.pageInfo': 'Page {page} / {pages} · {total} total',
    'events.title': 'Recent Events',
    'events.empty': 'No events.',
    'events.loadMore': 'Load more',
    'settings.title': 'Settings',
    'settings.safeNote': 'Sensitive fields show configured status only',
    'settings.paths': 'Paths & Tasks',
    'settings.saveDirectory': 'Save directory',
    'settings.tempDirectory': 'Temp directory',
    'settings.sessionDirectory': 'Session directory',
    'settings.maxDownload': 'Max download tasks',
    'settings.maxUpload': 'Max upload tasks',
    'settings.retryDownload': 'Download retries',
    'settings.retryUpload': 'Upload retries',
    'settings.pikpakMaxFileSize': 'PikPak max file size (bytes)',
    'settings.pikpakArchive': 'PikPak Archive',
    'settings.pikpakArchiveEnable': 'Archive by source channel',
    'settings.pikpakArchiveRemote': 'rclone remote',
    'settings.pikpakArchiveSource': 'Ingest directory',
    'settings.pikpakArchiveRoot': 'Archive root',
    'settings.pikpakArchivePoll': 'Poll seconds',
    'settings.pikpakArchiveInterval': 'Poll interval',
    'settings.pikpakArchiveWindow': 'Match window seconds',
    'settings.behavior': 'Behavior',
    'settings.notice': 'Bot notifications',
    'settings.shutdown': 'Shutdown on exit',
    'settings.downloadUpload': 'Download-then-upload for restricted',
    'settings.uploadDelete': 'Delete local after upload',
    'settings.pendingLimit': 'Upload queue limit',
    'settings.sensitive': 'Account & Proxy',
    'settings.proxyPassword': 'Proxy password',
    'settings.secretConfigured': 'Configured, fill to replace',
    'settings.downloadTypes': 'Download Types',
    'settings.downloadTypesHint': '(Check = allow download, unchecked types will be ignored)',
    'settings.forwardTypes': 'Forward Types',
    'settings.forwardTypesHint': '(Check = allow forward, unchecked types will be ignored)',
    'settings.messageFilter': 'Message Filter',
    'settings.mediaTypes': 'Media types',
    'settings.mediaTypesHint': '(Check = allow, unchecked types will be filtered out)',
    'settings.dateRange': 'Date range',
    'settings.keywords': 'Keywords',
    'settings.enabled': 'Enabled',
    'settings.startDate': 'Start date',
    'settings.endDate': 'End date',
    'settings.keywordList': 'Keywords (comma separated)',
    'settings.keywordPlaceholder': 'Enter keywords, separated by commas',
    'settings.exports': 'Export Tables',
    'settings.exportLink': 'Link table',
    'settings.exportCount': 'Count table',
    'settings.exportUpload': 'Upload table',
    'settings.save': 'Save settings',
    'settings.saved': 'Settings saved.',
    'records.title': 'Download Records',
    'records.chat': 'Chat ID',
    'records.message': 'Message ID',
    'records.file': 'File',
    'records.size': 'Size',
    'records.updated': 'Updated',
    'records.empty': 'No download records yet.',
    'records.clear': 'Clear All',
    'records.confirmClear': 'Clear all download records? This cannot be undone.',
    'records.cleared': 'Download records cleared.',
    'form.createFailed': 'Creation failed.',
    'form.requestFailed': 'Request failed.',
    'form.creatingTransfer': 'Analyzing source message range…',
    'form.creatingTransferShort': 'Analyzing…',
    'form.createSuccess': 'Task created, queued for processing.',
    'media.title': 'Media Management',
    'media.scan': 'Scan cleanable files',
    'media.scanning': 'Scanning…',
    'media.totalFiles': 'Cleanable files',
    'media.totalSize': 'Total size',
    'media.retentionDays': 'Retention days',
    'media.transferItems': 'Transfer task files',
    'media.orphanFiles': 'Orphan files',
    'media.file': 'File',
    'media.size': 'Size',
    'media.status': 'Status',
    'media.source': 'Source',
    'media.path': 'Path',
    'media.mtime': 'Modified',
    'media.cleanup': 'Delete selected',
    'media.cleaning': 'Cleaning…',
    'media.selected': 'Selected',
    'media.files': 'files',
    'media.noSelection': 'Select files to delete first.',
    'media.confirmCleanup': 'Delete selected files? This cannot be undone.',
    'media.cleanupDone': 'Cleanup done: {count} files deleted ({size}).',
    'media.cleanupHistory': 'Cleanup history',
    'media.empty': 'No cleanable files',
    'media.reason': 'Reason',
    'media.time': 'Time',
    'media.filterByTask': 'Filter by task:',
    'media.allTasks': 'All tasks',
    'status.pending': 'Pending',
    'status.running': 'Running',
    'status.paused': 'Paused',
    'status.success': 'Completed',
    'status.failure': 'Failed',
    'status.skipped': 'Skipped',
    'event.level.info': 'Info',
    'event.level.warning': 'Warning',
    'event.level.error': 'Error',
    'error.auth_required': 'Authentication required.',
    'error.invalid_task_id': 'Invalid task ID.',
    'error.task_not_found': 'Task not found.',
    'error.source_link_required': 'Source link is required.',
    'error.target_link_required': 'Target link is required.',
    'error.range_ids_required': 'Start and end IDs required together.',
    'error.range_end_before_start': 'End ID must be >= Start ID.',
    'error.invalid_payload': 'Invalid payload.',
  }
};

const state = {
  lang: localStorage.getItem('trmd-lang') || 'zh',
  activeView: 'transfers',
  activeItemStatus: 'running',
  selectedTaskId: null,
  tasks: [],
  watches: [],
  settings: null,
  settingsSchema: {},
  settingsModel: {},
  items: [],
  events: [],
  records: [],
  statistics: null,
  lastSync: null,
  itemPages: {},
  itemData: {},
  eventData: {},
  taskPollTimer: null,
  watchEventCache: {},
  watchHistory: { watchId: null, page: 1, pageSize: 20, total: 0 },
  recordsPage: 1,
  recordsPageSize: 50,
  recordsTotal: 0,
};
window.state = state;

function $(sel) {
  return document.querySelector(sel);
}

function $$(sel) {
  return document.querySelectorAll(sel);
}

window.$ = $;
window.$$ = $$;

function t(key, replacements) {
  const dict = i18n[state.lang] || i18n.zh;
  let text = dict[key];
  if (text === undefined) {
    // fallback to zh
    text = (i18n.zh[key]) || key;
  }
  if (replacements) {
    for (const [k, v] of Object.entries(replacements)) {
      text = text.replace('{' + k + '}', v);
    }
  }
  return text;
}

function esc(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

const DEFAULT_PAGE_SIZE = 50;

function paginationMeta(total, pageSize, page) {
  const safePageSize = Math.max(1, Number(pageSize || DEFAULT_PAGE_SIZE));
  const safeTotal = Math.max(0, Number(total || 0));
  const totalPages = Math.max(1, Math.ceil(safeTotal / safePageSize) || 1);
  const safePage = Math.min(Math.max(1, Number(page || 1)), totalPages);
  return {
    page: safePage,
    pageSize: safePageSize,
    total: safeTotal,
    totalPages: totalPages
  };
}

function renderPaginationBar(options) {
  options = options || {};
  const meta = paginationMeta(options.total, options.pageSize, options.page);
  if (meta.totalPages <= 1 && !options.alwaysShow) return '';
  const prefix = options.prefix || 'pagination';
  const variant = options.variant || 'desktop';
  const pageInfoKey = options.pageInfoKey || 'pagination.pageInfo';
  const pageInfo = t(pageInfoKey)
    .replace('{page}', meta.page)
    .replace('{pages}', meta.totalPages)
    .replace('{total}', meta.total);
  if (variant === 'mobile') {
    return '<div class="mob-sheet-pagination">' +
      '<span class="mob-pagination-info">' + esc(pageInfo) + '</span>' +
      '<div class="mob-pagination-actions flex gap-2">' +
        '<button class="mob-btn mob-btn-sm mob-btn-muted" id="' + prefix + '-prev" ' + (meta.page <= 1 ? 'disabled' : '') + '>' + esc(t('items.page.previous')) + '</button>' +
        '<button class="mob-btn mob-btn-sm mob-btn-muted" id="' + prefix + '-next" ' + (meta.page >= meta.totalPages ? 'disabled' : '') + '>' + esc(t('items.page.next')) + '</button>' +
      '</div></div>';
  }
  return '<div class="pagination-bar flex items-center justify-between px-[18px] py-2 pb-[14px] gap-3 flex-wrap">' +
    '<span class="text-xs text-muted">' + esc(pageInfo) + '</span>' +
    '<div class="flex gap-2">' +
      '<button class="btn btn-sm" id="' + prefix + '-prev" ' + (meta.page <= 1 ? 'disabled' : '') + '>' + esc(t('items.page.previous')) + '</button>' +
      '<button class="btn btn-sm" id="' + prefix + '-next" ' + (meta.page >= meta.totalPages ? 'disabled' : '') + '>' + esc(t('items.page.next')) + '</button>' +
    '</div></div>';
}

function bindPaginationBar(prefix, page, totalPages, onPageChange) {
  const prevBtn = $('#' + prefix + '-prev');
  const nextBtn = $('#' + prefix + '-next');
  if (prevBtn) {
    prevBtn.addEventListener('click', function() {
      if (page > 1) onPageChange(page - 1);
    });
  }
  if (nextBtn) {
    nextBtn.addEventListener('click', function() {
      if (page < totalPages) onPageChange(page + 1);
    });
  }
}

function applyLanguage() {
  $$('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    if (key) el.textContent = t(key);
  });
  document.title = t('app.title') || 'TRMD · 转存控制台';
}

function applyLanguageAndRefresh() {
  applyLanguage();
  if (state.activeView === 'transfers' && typeof renderTasks === 'function') renderTasks();
  if (state.activeView === 'watches' && typeof renderWatches === 'function') renderWatches();
  if (state.activeView === 'settings' && typeof renderSettings === 'function') renderSettings();
  if (state.activeView === 'records' && typeof loadRecords === 'function') loadRecords();
  if (typeof renderMobTasks === 'function') renderMobTasks();
  if (typeof renderMobWatches === 'function') renderMobWatches();
}

function redirectToLoginPage() {
  if (window.__trmdRedirectingToLogin) return;
  window.__trmdRedirectingToLogin = true;
  window.location.assign('/');
}

async function fetchJson(url) {
  const resp = await fetch(url);
  if (resp.status === 401) { redirectToLoginPage(); throw { error_code: 'auth_required' }; }
  if (!resp.ok) {
    let data;
    try { data = await resp.json(); } catch(e) { data = {}; }
    throw data;
  }
  return resp.json();
}

async function postJson(url, payload, method) {
  const resp = await fetch(url, {
    method: method || 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (resp.status === 401) { redirectToLoginPage(); throw { error_code: 'auth_required' }; }
  const data = await resp.json();
  if (!resp.ok) throw data;
  return data;
}

async function patchJson(url, payload) {
  const resp = await fetch(url, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (resp.status === 401) { redirectToLoginPage(); throw { error_code: 'auth_required' }; }
  const data = await resp.json();
  if (!resp.ok) throw data;
  return data;
}

function translateApiError(data, fallbackKey) {
  if (data && data.error_code && data.error) {
    const key = 'error.' + data.error_code;
    const translated = t(key);
    if (translated !== key) return translated;
    return data.error;
  }
  return t(fallbackKey || 'form.requestFailed');
}

function fmtSize(bytes) {
  if (!bytes && bytes !== 0) return '-';
  bytes = Number(bytes);
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + ' MB';
  return (bytes / 1073741824).toFixed(2) + ' GB';
}

function formatBytes(bytes) {
  return fmtSize(bytes);
}

function fmtTime(iso) {
  if (!iso) return '-';
  try { return new Date(iso).toLocaleString(); } catch(e) { return iso; }
}

function fmtTimestamp(sec) {
  if (!sec) return '-';
  try { return new Date(sec * 1000).toLocaleString(); } catch(e) { return String(sec); }
}

function statusBadge(status) {
  const labels = { pending: 'status.pending', running: 'status.running', paused: 'status.paused', success: 'status.success', failure: 'status.failure', skipped: 'status.skipped' };
  const cls = status || 'pending';
  return '<span class="badge badge-' + cls + '"><span class="status-dot ' + cls + '"></span>' + t(labels[status] || 'status.pending') + '</span>';
}

function setLang(lang) {
  state.lang = lang || 'zh';
  localStorage.setItem('trmd-lang', state.lang);
  applyLanguageAndRefresh();
}

function optionValues(options) {
  return (options || []).map(function(option) {
    return typeof option === 'string' ? option : option.value;
  }).filter(Boolean);
}

function selectedKeys(value) {
  if (Array.isArray(value)) return value;
  if (value && typeof value === 'object') {
    return Object.entries(value).filter(function(entry) { return Boolean(entry[1]); }).map(function(entry) { return entry[0]; });
  }
  return [];
}

function taskProgressPercent(task) {
  return Number(task && task.progress_percent || 0);
}

function taskCompletedLabel(task) {
  if (!task) return '0/0';
  return String(Number(task.completed_items || 0)) + '/' + String(Number(task.total_items || 0));
}

function taskFailedCount(task) {
  return Number(task && task.failed_items || 0);
}

function formatSpeed(bytesPerSecond) {
  const value = Number(bytesPerSecond || 0);
  if (!value || value < 0) return '-';
  return fmtSize(value) + '/s';
}

function transferPhaseLabel(phase) {
  const labels = {
    downloading: '下载',
    downloaded: '下载完成',
    uploading: '上传',
    uploaded: '上传完成',
    sent: '已发送',
    forwarded: '已转发',
    failure: '失败',
    failed: '失败',
    skipped: '跳过',
    pending: '等待'
  };
  return labels[phase] || phase || '-';
}

function transferProgressLabel(current, total) {
  current = Number(current || 0);
  total = Number(total || 0);
  if (!total) return current ? fmtSize(current) : '-';
  const percent = Math.min(100, Math.round((current / total) * 100));
  return fmtSize(current) + '/' + fmtSize(total) + ' · ' + percent + '%';
}

function activeTransferSummary(task) {
  if (!task || !task.active_item_id) return '';
  const phase = transferPhaseLabel(task.active_phase);
  const name = task.active_file_name || ('#' + task.active_item_id);
  const progress = transferProgressLabel(task.active_progress_current, task.active_progress_total);
  const speed = formatSpeed(task.active_speed_bps);
  return phase + ' · ' + name + ' · ' + progress + (speed !== '-' ? ' · ' + speed : '');
}

function itemTransferSummary(item) {
  if (!item) return '-';
  const phase = transferPhaseLabel(item.phase || item.status);
  if (item.phase === 'uploading' || Number(item.upload_current || 0) > 0) {
    return phase + ' · ' + transferProgressLabel(item.upload_current, item.upload_total) +
      (Number(item.upload_speed_bps || 0) ? ' · ' + formatSpeed(item.upload_speed_bps) : '');
  }
  if (Number(item.download_total || 0) || Number(item.download_current || 0)) {
    return phase + ' · ' + transferProgressLabel(item.download_current, item.download_total) +
      (Number(item.download_speed_bps || 0) ? ' · ' + formatSpeed(item.download_speed_bps) : '');
  }
  return phase;
}

async function runTaskAction(event, taskId, action) {
  if (event && event.stopPropagation) event.stopPropagation();
  await postJson('/api/tasks/' + encodeURIComponent(taskId) + '/' + action, {});
  if (typeof loadMobileTasks === 'function') await loadMobileTasks();
  else if (typeof loadTasks === 'function') await loadTasks();
}

async function deleteTask(event, taskId) {
  if (event && event.stopPropagation) event.stopPropagation();
  if (!confirm('确定删除任务 #' + taskId + '？')) return;
  const resp = await fetch('/api/tasks/' + encodeURIComponent(taskId), { method: 'DELETE' });
  if (!resp.ok) {
    let data = {};
    try { data = await resp.json(); } catch(e) {}
    throw data;
  }
  state.tasks = (state.tasks || []).filter(function(task) { return Number(task.id) !== Number(taskId); });
  if (state.selectedTaskId === taskId) state.selectedTaskId = null;
  if (typeof renderMobTasks === 'function') renderMobTasks();
  if (typeof renderTasks === 'function') renderTasks();
}

async function deleteWatch(watchId) {
  if (!confirm(t('watches.delete'))) return;
  const resp = await fetch('/api/watches/' + encodeURIComponent(watchId), { method: 'DELETE' });
  if (!resp.ok) {
    let data = {};
    try { data = await resp.json(); } catch(e) {}
    throw data;
  }
  state.watches = (state.watches || []).filter(function(watch) { return watch.id !== watchId; });
  if (typeof loadMobileWatches === 'function') await loadMobileWatches();
  else if (typeof loadWatches === 'function') await loadWatches();
}
</script>
<script>/* TRMD WebUI - Desktop SPA Logic */

/* ====== View Switching ====== */
function switchView(view) {
  state.activeView = view;
  $$('.sidebar-nav-item').forEach(b => b.classList.remove('active'));
  const navBtn = document.querySelector('.sidebar-nav-item[data-nav="' + view + '"]');
  if (navBtn) navBtn.classList.add('active');

  $$('.view').forEach(v => v.classList.remove('active'));
  const viewEl = document.getElementById('view-' + view);
  if (viewEl) viewEl.classList.add('active');

  if (view === 'transfers') renderTasks();
  if (view === 'watches') loadWatches();
  if (view === 'downloads-uploads') { loadDownloadTypes(); loadOperations(); }
  if (view === 'settings') loadSettings();
  if (view === 'records') loadRecords();
  if (view === 'statistics') loadStatistics();
  if (view === 'media') loadMedia();
}

$$('[data-nav]').forEach(btn => btn.addEventListener('click', () => switchView(btn.dataset.nav)));

/* ====== Task List ====== */
async function loadTasks() {
  try {
    const data = await fetchJson('/api/tasks');
    state.tasks = data.tasks || [];
    renderTasks();
    updateStats();
  } catch(e) {
    if (e.error_code === 'auth_required') redirectToLoginPage();
  }
}

function updateStats() {
  const stats = { total: state.tasks.length, running: 0, success: 0, failed: 0, failedItems: 0 };
  state.tasks.forEach(t => {
    if (t.status === 'running') stats.running++;
    if (t.status === 'success') stats.success++;
    if (t.status === 'failure') stats.failed++;
    if (t.failed_items) stats.failedItems += (t.failed_items || 0);
  });
  $('#stat-total').textContent = stats.total;
  $('#stat-success').textContent = stats.success;
  $('#stat-running').textContent = stats.running;
  $('#stat-failed').textContent = stats.failedItems;
  $('#metric-failed').textContent = stats.failedItems;
  $('#badge-transfers').textContent = stats.running || '';
  $('#badge-transfers').style.display = stats.running ? '' : 'none';
}

function renderTasks() {
  if (state.activeView !== 'transfers') return;
  const tbody = $('#tasks-tbody');
  const empty = $('#tasks-empty');
  if (!state.tasks.length) {
    tbody.innerHTML = '';
    empty.style.display = '';
    return;
  }
  empty.style.display = 'none';
  tbody.innerHTML = state.tasks.map(task => {
    const isSelected = task.id === state.selectedTaskId;
    const progressPct = taskProgressPercent(task);
    const activeSummary = activeTransferSummary(task);
    return '<tr data-task-id="' + task.id + '" class="' + (isSelected ? 'selected' : '') + '">' +
      '<td class="font-semibold text-primary">#' + task.id + '</td>' +
      '<td>' + statusBadge(task.status) + '</td>' +
      '<td class="max-w-[160px] overflow-hidden text-ellipsis whitespace-nowrap text-xs" title="' + esc(task.source_link || '') + '">' + esc(task.source_link || '-') + '</td>' +
      '<td class="text-xs">' + esc(task.target_profile || task.target_link || '-') + '</td>' +
      '<td>' +
        (task.total_items > 0 ? (
          '<div class="flex items-center gap-2">' +
          '<span class="text-xs font-semibold">' + progressPct + '%</span>' +
          '<div class="flex-1 min-w-[60px]">' +
          '<div class="progress-bar"><div class="progress-fill" style="width:' + progressPct + '%"></div></div>' +
          '<span class="text-[11px] text-muted">' + taskCompletedLabel(task) + '</span>' +
          (activeSummary ? '<span class="block text-[11px] text-muted max-w-[260px] overflow-hidden text-ellipsis whitespace-nowrap" title="' + esc(activeSummary) + '">' + esc(activeSummary) + '</span>' : '') +
          '</div></div>'
        ) : '<span class="text-muted text-xs">-</span>') +
      '</td>' +
      '<td>' + taskActions(task) + '</td>' +
      '</tr>';
  }).join('');

  $$('#tasks-tbody tr').forEach(row => {
    row.addEventListener('click', () => {
      const id = parseInt(row.dataset.taskId);
      state.selectedTaskId = id;
      renderTasks();
      loadTaskDetail(id);
    });
  });
}

function taskActions(task) {
  let actions = '';
  if (task.can_pause) {
    actions += '<button class="btn btn-sm" data-task-action="pause" data-task-id="' + task.id + '" title="' + t('tasks.pause') + '">⏸</button>';
  }
  if (task.can_resume) {
    actions += '<button class="btn btn-sm btn-primary" data-task-action="resume" data-task-id="' + task.id + '" title="' + t('tasks.resume') + '">▶</button>';
  }
  if (task.can_retry) {
    actions += '<button class="btn btn-sm btn-danger" data-task-action="retry" data-task-id="' + task.id + '" title="' + t('tasks.retryFailed') + '">↻</button>';
  }
  if (task.can_delete) {
    actions += '<button class="btn btn-sm btn-danger" data-task-action="delete" data-task-id="' + task.id + '" title="' + t('tasks.delete') + '">✕</button>';
  }
  return '<div class="flex gap-1">' + actions + '</div>';
}

/* task action delegation */
document.addEventListener('click', async function(e) {
  const btn = e.target.closest('[data-task-action]');
  if (!btn) return;
  e.stopPropagation();
  const taskId = parseInt(btn.dataset.taskId);
  const action = btn.dataset.taskAction;

  if (action === 'delete') {
    if (!confirm('确定删除任务 #' + taskId + '？')) return;
    try {
      await fetch('/api/tasks/' + taskId, { method: 'DELETE' });
      state.tasks = state.tasks.filter(t => t.id !== taskId);
      if (state.selectedTaskId === taskId) state.selectedTaskId = null;
      renderTasks();
      $('#task-detail').innerHTML = '<div class="p-8 text-center text-muted text-sm">' + t('items.selectTask') + '</div>';
    } catch(e) { /* ignore */ }
    return;
  }

  const actionMap = { pause: 'pause', resume: 'resume', retry: 'retry-failed' };
  try {
    await postJson('/api/tasks/' + taskId + '/' + actionMap[action], {});
    await loadTasks();
  } catch(e) { /* ignore */ }
});

/* ====== Task Detail ====== */
function selectedTaskStillVisible(taskId) {
  return state.activeView === 'transfers' && Number(state.selectedTaskId) === Number(taskId);
}

async function loadTaskDetail(taskId) {
  const container = $('#task-detail');
  container.innerHTML = '<div class="p-8 text-center"><div class="spinner mx-auto"></div></div>';

  try {
    const data = await fetchJson('/api/tasks/' + taskId + '/summary');
    state.itemData[taskId] = data;
    state.eventData[taskId] = data.events || [];
    state.itemPages = { running: 1, success: 1, skipped: 1, failure: 1 };
    state.activeItemStatus = 'running';
    renderTaskDetail(taskId, data);
  } catch(e) {
    container.innerHTML = '<div class="p-8 text-center text-muted text-sm">加载失败</div>';
  }
}

function renderTaskDetail(taskId, data) {
  const task = state.tasks.find(t => t.id === taskId);
  const summary = data.summary || {};
  const detailEl = $('#task-detail');

  let html = '<div class="panel-header">' +
    '<h3>任务 #' + taskId + ' · ' + esc(task ? (task.source_link || '') : '') + ' → ' + esc(task ? (task.target_profile || task.target_link || '') : '') + '</h3>' +
    '<div class="panel-tabs">' +
      '<button class="panel-tab active" data-item-tab="running">' + t('items.tab.running') + ' (' + (summary.running || 0) + ')</button>' +
      '<button class="panel-tab" data-item-tab="success">' + t('items.tab.success') + ' (' + (summary.success || 0) + ')</button>' +
      '<button class="panel-tab" data-item-tab="skipped">' + t('items.tab.skipped') + ' (' + (summary.skipped || 0) + ')</button>' +
      '<button class="panel-tab" data-item-tab="failure">' + t('items.tab.failure') + ' (' + (summary.failed || 0) + ')</button>' +
    '</div>' +
    '</div>' +
    '<div id="task-items-body" class="overflow-auto max-h-[300px]"></div>' +
    '<div class="flex items-center justify-between px-[18px] py-2 pb-[14px] gap-3 flex-wrap" id="task-items-pagination"></div>';

  detailEl.innerHTML = html;
  loadTaskItems(taskId, 'running');

  /* tab switching */
  $$('#task-detail [data-item-tab]').forEach(btn => {
    btn.addEventListener('click', function() {
      $$('#task-detail [data-item-tab]').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      state.activeItemStatus = this.dataset.itemTab;
      loadTaskItems(taskId, this.dataset.itemTab);
    });
  });
}

async function loadTaskItems(taskId, status, options) {
  options = options || {};
  const silent = Boolean(options.silent);
  const page = state.itemPages[status] || 1;
  const body = $('#task-items-body');
  const pagEl = $('#task-items-pagination');
  if (!body || !pagEl) return;
  if (!silent) {
    body.innerHTML = '<div class="p-8 text-center"><div class="spinner mx-auto"></div></div>';
  }

  try {
    const data = await fetchJson('/api/tasks/' + taskId + '?items_limit=50&items_offset=' + ((page - 1) * 50) + '&item_status=' + encodeURIComponent(status));
    if (silent && !selectedTaskStillVisible(taskId)) return;
    const items = data.items || [];
    state.itemData[taskId] = data;

    if (!items.length) {
      body.innerHTML = '<div class="p-8 text-center text-muted text-sm">' + t('items.empty.' + status) + '</div>';
    } else {
      body.innerHTML = '<table class="data-table task-items-table"><colgroup>' +
        '<col class="task-item-col-file"><col class="task-item-col-size"><col class="task-item-col-progress"><col class="task-item-col-source"><col class="task-item-col-status">' +
        '</colgroup><thead><tr>' +
        '<th class="task-item-file">文件</th><th class="task-item-size">大小</th><th class="task-item-progress">进度/速度</th><th class="task-item-source">来源</th><th class="task-item-status">状态</th>' +
        '</tr></thead><tbody>' +
        items.map(item => '<tr>' +
          '<td class="task-item-file text-xs" title="' + esc(item.file_name || item.local_path || '-') + '">' + esc(item.file_name || item.local_path || '-') + '</td>' +
          '<td class="task-item-size text-xs">' + fmtSize(item.file_size) + '</td>' +
          '<td class="task-item-progress text-xs" title="' + esc(itemTransferSummary(item)) + '">' + esc(itemTransferSummary(item)) + '</td>' +
          '<td class="task-item-source text-xs" title="' + esc(item.source_link || '-') + '">' + esc(item.source_link || '-') + '</td>' +
          '<td class="task-item-status">' + statusBadge(item.status) + '</td>' +
          '</tr>').join('') +
        '</tbody></table>';
    }

    const statusToSummaryKey = { running: 'running', success: 'success', skipped: 'skipped', failure: 'failed' };
    const summaryKey = statusToSummaryKey[status] || status;
    const totalItems = state.itemData[taskId] ? (state.itemData[taskId].summary || {})[summaryKey] || 0 : 0;
    const totalPages = Math.max(1, Math.ceil(totalItems / 50));
    pagEl.innerHTML = renderPaginationBar({
      prefix: 'items',
      page: page,
      pageSize: 50,
      total: totalItems
    });
    bindPaginationBar('items', page, totalPages, function(newPage) {
      state.itemPages[state.activeItemStatus] = newPage;
      loadTaskItems(taskId, state.activeItemStatus);
    });
  } catch(e) {
    if (!silent) {
      body.innerHTML = '<div class="p-8 text-center text-muted text-sm">加载失败</div>';
    }
  }
}

async function refreshSelectedTaskDetail() {
  if (state.activeView !== 'transfers' || !state.selectedTaskId) return;
  const taskId = state.selectedTaskId;
  const detailEl = $('#task-detail');
  const body = $('#task-items-body');
  if (!detailEl || !body) return;
  try {
    const data = await fetchJson('/api/tasks/' + taskId + '/summary');
    if (!selectedTaskStillVisible(taskId)) return;
    state.itemData[taskId] = data;
    renderTaskDetailTabs(data.summary || {});
    await loadTaskItems(taskId, state.activeItemStatus || 'running', { silent: true });
  } catch(e) {}
}

function renderTaskDetailTabs(summary) {
  const tabs = {
    running: summary.running || 0,
    success: summary.success || 0,
    skipped: summary.skipped || 0,
    failure: summary.failed || 0,
  };
  Object.keys(tabs).forEach(status => {
    const btn = $('#task-detail [data-item-tab="' + status + '"]');
    if (!btn) return;
    btn.textContent = t('items.tab.' + status) + ' (' + tabs[status] + ')';
  });
}

/* ====== Transfer Form ====== */
$('#transfer-form').addEventListener('submit', async function(e) {
  e.preventDefault();
  const btn = $('#transfer-submit');
  const btnText = btn.querySelector('span');
  const originalText = btnText.textContent;
  const notice = $('#transfer-notice');

  btn.disabled = true;
  btnText.textContent = t('form.creatingTransferShort');
  notice.className = 'text-xs text-muted mt-2';
  notice.textContent = t('form.creatingTransfer');
  notice.style.display = '';

  const fd = new FormData(this);
  const payload = {
    source_link: fd.get('source_link') || '',
    target_link: fd.get('target_link') || '',
    target_profile: fd.get('target_profile') || 'pikpak',
    start_id: fd.get('start_id') ? Number(fd.get('start_id')) : null,
    end_id: fd.get('end_id') ? Number(fd.get('end_id')) : null,
    include_comment: Boolean(fd.get('include_comment')),
  };

  try {
    const data = await postJson('/api/tasks', payload);
    state.selectedTaskId = data.task_id;
    notice.className = 'text-xs text-success mt-2';
    notice.textContent = t('form.createSuccess');
    await loadTasks();
  } catch(err) {
    notice.className = 'text-xs text-danger mt-2';
    notice.textContent = translateApiError(err, 'form.createFailed');
  } finally {
    btn.disabled = false;
    btnText.textContent = originalText;
  }
});

/* ====== Polling ====== */
function hasActiveTasks() {
  return state.tasks.some(t => t.status === 'pending' || t.status === 'running');
}

async function refreshTransferData() {
  await loadTasks();
  await refreshSelectedTaskDetail();
}

function startPolling() {
  if (state.taskPollTimer) return;
  const fast = 3000, slow = 15000;
  let interval = fast, lastPoll = 0;

  async function poll() {
    if (document.hidden) { state.taskPollTimer = setTimeout(poll, interval); return; }
    const now = Date.now();
    if (now - lastPoll < interval - 500) { state.taskPollTimer = setTimeout(poll, interval); return; }
    lastPoll = now;
    try {
      await refreshTransferData();
    } catch(e) {}
    interval = hasActiveTasks() ? fast : slow;
    state.taskPollTimer = setTimeout(poll, interval);
  }
  poll();
}

document.addEventListener('visibilitychange', () => {
  if (!document.hidden && state.taskPollTimer) {
    clearTimeout(state.taskPollTimer);
    state.taskPollTimer = null;
    refreshTransferData().catch(() => {});
    startPolling();
  }
});

/* ====== Auth Flow ====== */
let authPollTimer = null, authStep = '';

function showLoginStep(step) {
  authStep = step;
  ['login-form-phone','login-form-code','login-form-password','login-form-recovery','login-form-signup','login-form-done'].forEach(id => {
    const el = document.getElementById(id); if (el) el.style.display = 'none';
  });
  const el = document.getElementById('login-form-' + step);
  if (el) el.style.display = '';
  const container = document.getElementById('login-container');
  if (container) container.style.display = 'flex';
  const errEl = document.getElementById('login-error');
  if (errEl) errEl.classList.remove('visible');
}

function hideLogin() {
  const container = document.getElementById('login-container');
  if (container) container.style.display = 'none';
  if (authPollTimer) { clearInterval(authPollTimer); authPollTimer = null; }
}

function showLoginError(msg) {
  const el = document.getElementById('login-error');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('visible');
}

async function checkAuthStatus() {
  try {
    const resp = await fetch('/api/auth/status');
    if (resp.status === 401) { redirectToLoginPage(); return; }
    const state = await resp.json();
    if (!state || !state.step) return;
    switch (state.step) {
      case 'pending':
        hideLogin();
        await refreshTransferData();
        startPolling();
        return;
      case 'done': case 'none':
        hideLogin();
        await refreshTransferData();
        startPolling();
        return;
      case 'phone': showLoginStep('phone'); if (state.error) showLoginError(state.error); break;
      case 'code':
        showLoginStep('code');
        if (state.code_type) {
          const desc = document.getElementById('login-code-desc');
          if (desc) desc.textContent = '验证码已通过「' + state.code_type + '」发送';
        }
        if (state.error) showLoginError(state.error);
        break;
      case 'password':
        showLoginStep('password');
        const hintEl = document.getElementById('login-password-hint-text');
        if (hintEl && state.hint) hintEl.textContent = state.hint;
        if (state.error) showLoginError(state.error);
        break;
      case 'recovery_code':
        showLoginStep('recovery');
        if (state.message) { const d = document.getElementById('login-recovery-desc'); if (d) d.textContent = state.message; }
        if (state.error) showLoginError(state.error);
        break;
      case 'signup': showLoginStep('signup'); if (state.error) showLoginError(state.error); break;
      case 'error': if (state.error) showLoginError(state.error); break;
    }
  } catch(e) {}
}

async function submitAuth(payload) {
  const btn = document.querySelector('.login-submit');
  if (btn) btn.disabled = true;
  showLoginError('');
  try {
    await fetch('/api/auth/submit', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
    await new Promise(r => setTimeout(r, 500));
    await checkAuthStatus();
  } catch(e) {
    showLoginError('提交失败，请重试');
  } finally {
    if (btn) btn.disabled = false;
  }
}

/* auth event bindings */
document.getElementById('login-btn-phone')?.addEventListener('click', () => {
  const phone = document.getElementById('login-phone').value.trim();
  if (!phone) { showLoginError('请输入电话号码'); return; }
  if (!phone.startsWith('+')) { showLoginError('电话号码需以 +地区号开头'); return; }
  submitAuth({ phone });
});

document.getElementById('login-btn-code')?.addEventListener('click', () => {
  const code = document.getElementById('login-code').value.trim();
  if (!code) { showLoginError('请输入验证码'); return; }
  submitAuth({ code });
});

document.getElementById('login-btn-back')?.addEventListener('click', () => {
  showLoginStep('phone');
  document.getElementById('login-code').value = '';
});

document.getElementById('login-btn-password')?.addEventListener('click', () => {
  submitAuth({ password: document.getElementById('login-password').value });
});

document.getElementById('login-btn-back-pwd')?.addEventListener('click', () => {
  showLoginStep('code');
  document.getElementById('login-password').value = '';
});

document.getElementById('login-btn-recovery')?.addEventListener('click', () => {
  const code = document.getElementById('login-recovery').value.trim();
  if (!code) { showLoginError('请输入恢复代码'); return; }
  submitAuth({ recovery_code: code });
});

document.getElementById('login-btn-back-recovery')?.addEventListener('click', () => {
  showLoginStep('password');
  document.getElementById('login-recovery').value = '';
});

document.getElementById('login-btn-signup')?.addEventListener('click', () => {
  const first = document.getElementById('login-first-name').value.trim();
  if (!first) { showLoginError('请输入名字'); return; }
  submitAuth({ first_name: first, last_name: document.getElementById('login-last-name').value.trim() });
});

document.getElementById('login-phone')?.addEventListener('keydown', e => {
  if (e.key === 'Enter') document.getElementById('login-btn-phone').click();
});

document.getElementById('login-code')?.addEventListener('keydown', e => {
  if (e.key === 'Enter') document.getElementById('login-btn-code').click();
});

/* ====== Language ====== */
$('#language-select').addEventListener('change', e => {
  state.lang = e.target.value;
  localStorage.setItem('trmd-lang', state.lang);
  applyLanguageAndRefresh();
});

/* ====== Refresh ====== */
$('#refresh').addEventListener('click', () => {
  loadTasks();
  if (state.activeView === 'records') loadRecords();
  if (state.activeView === 'settings') loadSettings();
  if (state.activeView === 'watches') loadWatches();
  if (state.activeView === 'statistics') loadStatistics();
  if (state.activeView === 'downloads-uploads') loadOperations();
});

/* ====== Logout ====== */
$('#btn-logout').addEventListener('click', async () => {
  await fetch('/api/auth/logout', { method: 'POST' });
  window.location.reload();
});

/* ====== Records ====== */
const RECORDS_PAGE_SIZE = 50;

async function loadRecords(page) {
  if (page !== undefined) state.recordsPage = page;
  const currentPage = state.recordsPage || 1;
  const tbody = $('#records-tbody');
  const empty = $('#records-empty');
  const pagEl = $('#records-pagination');
  const clearBtn = $('#records-clear-btn');
  try {
    const offset = (currentPage - 1) * RECORDS_PAGE_SIZE;
    const data = await fetchJson('/api/download-records?limit=' + RECORDS_PAGE_SIZE + '&offset=' + offset);
    const records = data.records || [];
    const total = Number(data.total || 0);
    state.records = records;
    state.recordsTotal = total;
    const totalPages = Math.max(1, Math.ceil(total / RECORDS_PAGE_SIZE) || 1);

    if (currentPage > totalPages && total > 0) {
      state.recordsPage = totalPages;
      return loadRecords(totalPages);
    }

    if (clearBtn) clearBtn.disabled = total === 0;

    if (!records.length) {
      tbody.innerHTML = '';
      empty.style.display = '';
      if (pagEl) pagEl.innerHTML = '';
      return;
    }
    empty.style.display = 'none';
    tbody.innerHTML = records.map(r => '<tr>' +
      '<td class="text-xs font-mono text-muted">' + esc(String(r.source_chat_id || '-')) + '</td>' +
      '<td class="text-xs font-mono text-muted">' + esc(String(r.source_message_id || '-')) + '</td>' +
      '<td class="text-xs max-w-[200px] overflow-hidden text-ellipsis whitespace-nowrap">' + esc(r.file_path || r.file_name || '-') + '</td>' +
      '<td class="text-xs">' + fmtSize(r.file_size) + '</td>' +
      '<td class="text-xs text-muted">' + fmtTime(r.updated_at) + '</td>' +
      '</tr>').join('');

    if (pagEl) {
      pagEl.innerHTML = renderPaginationBar({
        prefix: 'records',
        page: currentPage,
        pageSize: RECORDS_PAGE_SIZE,
        total: total
      });
      bindPaginationBar('records', currentPage, totalPages, function(newPage) {
        loadRecords(newPage);
      });
    }
  } catch(e) {}
}

$('#records-clear-btn')?.addEventListener('click', async function() {
  if (!confirm(t('records.confirmClear'))) return;
  try {
    const resp = await fetch('/api/download-records', { method: 'DELETE' });
    if (resp.status === 401) { redirectToLoginPage(); return; }
    if (!resp.ok) {
      let data = {};
      try { data = await resp.json(); } catch(e) {}
      throw data;
    }
    state.recordsPage = 1;
    await loadRecords();
  } catch(e) {
    alert(translateApiError(e, 'form.requestFailed'));
  }
});

/* ====== Watches ====== */
async function loadWatches() {
  try {
    const data = await fetchJson('/api/watches');
    state.watches = data.watches || [];
    renderWatches();
    updateWatchBadge();
  } catch(e) {}
}

function updateWatchBadge() {
  const count = (state.watches || []).filter(w => w.status !== 'paused').length;
  $('#badge-watches').textContent = count || '';
  $('#badge-watches').style.display = count ? '' : 'none';
}

function renderWatches() {
  if (state.activeView !== 'watches') return;
  const tbody = $('#watches-tbody');
  const empty = $('#watches-empty');
  const watches = state.watches || [];
  if (!watches.length) {
    tbody.innerHTML = '';
    empty.style.display = '';
    return;
  }
  empty.style.display = 'none';
  tbody.innerHTML = watches.map(w => {
    const typeLabel = w.type === 'download' ? t('watches.download') : t('watches.forward');
    const typeCls = w.type === 'download' ? 'badge-success' : 'badge-running';
    const statusCls = w.status === 'paused' ? 'badge-paused' : 'badge-success';
    const statusLabel = w.status === 'paused' ? t('status.paused') : '● ' + t('status.running');
    const eventCount = w.event_count || 0;
    const todayCount = w.today_count || 0;
    const sanitized = sanitizeWatchId(w.id);
    const rowAttrs = w.type === 'forward' ? ' class="watch-row" data-watch-id="' + esc(w.id) + '"' : '';
    const eventsRow = w.type === 'forward' ?
      '<tr class="watch-events-row" id="watch-events-' + sanitized + '">' +
      '<td colspan="6"><div class="watch-events-panel" id="watch-events-panel-' + sanitized + '"></div></td>' +
      '</tr>' : '';
    return '<tr' + rowAttrs + '>' +
      '<td><span class="badge ' + typeCls + '">' + typeLabel + '</span></td>' +
      '<td class="text-xs max-w-[180px] overflow-hidden text-ellipsis whitespace-nowrap font-mono text-muted">' + esc(w.source_link || '-') + '</td>' +
      '<td class="text-xs">' + esc(w.target_link || '本地') + '</td>' +
      '<td><span class="badge ' + statusCls + '">' + statusLabel + '</span></td>' +
      '<td class="text-xs font-semibold">' + todayCount + '</td>' +
      '<td><div class="table-actions flex gap-1">' +
        (w.type === 'forward' ? '<button class="btn btn-sm" data-edit-watch="' + esc(w.id) + '">✎</button>' : '') +
        (w.type === 'forward' ? '<button class="btn btn-sm" data-watch-history="' + esc(w.id) + '">' + esc(t('watches.history')) + (eventCount ? ' ' + eventCount : '') + '</button>' : '') +
        '<button class="btn btn-sm btn-danger" data-delete-watch="' + esc(w.id) + '">✕</button>' +
      '</div></td>' +
      '</tr>' + eventsRow;
  }).join('');
}

/* ====== Watch Events (expandable forwarding log) ====== */
function sanitizeWatchId(id) {
  return (id || '').replace(/:/g, '_');
}

document.addEventListener('click', function(e) {
  const row = e.target.closest('.watch-row');
  if (!row) return;
  if (e.target.closest('button, a')) return;
  toggleWatchEvents(row.dataset.watchId);
});

function toggleWatchEvents(watchId) {
  const sanitized = sanitizeWatchId(watchId);
  const row = document.getElementById('watch-events-' + sanitized);
  if (!row) return;
  const isOpen = row.classList.contains('open');
  if (isOpen) {
    row.classList.remove('open');
    return;
  }
  row.classList.add('open');
  loadWatchEvents(watchId, 0, true);
}

async function loadWatchEvents(watchId, offset, todayOnly) {
  const sanitized = sanitizeWatchId(watchId);
  const panel = document.getElementById('watch-events-panel-' + sanitized);
  if (!panel) return;
  if (offset === 0) panel.innerHTML = '<div class="watch-event-item">' + esc(t('watches.eventLoading')) + '</div>';
  try {
    const todayQuery = todayOnly ? '&today=1' : '';
    const res = await fetch('/api/watches/' + encodeURIComponent(watchId) + '/events?limit=50&offset=' + offset + todayQuery);
    const data = await res.json();
    if (!res.ok) { panel.innerHTML = '<div class="watch-event-item">' + esc(data.error || t('form.requestFailed')) + '</div>'; return; }
    const items = data.events || [];
    if (offset === 0) panel.innerHTML = '';
    if (!items.length && offset === 0) {
      panel.innerHTML = '<div class="watch-event-item">' + esc(t('watches.noEvents')) + '</div>';
      return;
    }
    items.forEach(evt => {
      const time = new Date(evt.created_at).toLocaleString();
      const statusLabel = evt.status === 'success' ? t('watches.eventForwarded') : t('watches.eventSkipped');
      const badgeCls = evt.status === 'success' ? 'badge-success' : 'badge-warning';
      const div = document.createElement('div');
      div.className = 'watch-event-item';
      div.innerHTML = '<span class="watch-event-time">' + esc(time) + '</span>'
        + '<span class="watch-event-badge"><span class="badge ' + badgeCls + '">' + esc(statusLabel) + '</span></span>'
        + '<span class="watch-event-info">' + esc(evt.message) + ' ' + esc(t('watches.source')) + ': #' + esc(String(evt.source_message_id || '')) + ' → ' + esc(t('watches.target')) + ': ' + esc(evt.target_link || evt.target_chat_id || '') + '</span>';
      panel.appendChild(div);
    });
    if (data.has_more) {
      const btn = document.createElement('button');
      btn.className = 'watch-events-load-more btn btn-sm';
      btn.textContent = t('watches.loadMore');
      btn.onclick = function() { loadWatchEvents(watchId, offset + items.length, todayOnly); };
      panel.appendChild(btn);
    }
  } catch (e) {
    panel.innerHTML = '<div class="watch-event-item">' + esc(t('form.requestFailed')) + '</div>';
  }
}

function renderWatchEventRows(items) {
  if (!items.length) {
    return '<div class="p-8 text-center text-muted text-sm">' + esc(t('watches.noEvents')) + '</div>';
  }
  return '<table class="data-table watch-history-table"><thead><tr>' +
    '<th>' + esc(t('events.title')) + '</th>' +
    '<th>' + esc(t('tasks.status')) + '</th>' +
    '<th>' + esc(t('watches.source')) + '</th>' +
    '<th>' + esc(t('watches.target')) + '</th>' +
    '<th>' + esc(t('records.updated')) + '</th>' +
    '</tr></thead><tbody>' +
    items.map(evt => {
      const statusLabel = evt.status === 'success' ? t('watches.eventForwarded') : t('watches.eventSkipped');
      const badgeCls = evt.status === 'success' ? 'badge-success' : 'badge-warning';
      return '<tr>' +
        '<td class="text-xs max-w-[240px] overflow-hidden text-ellipsis whitespace-nowrap" title="' + esc(evt.message || '') + '">' + esc(evt.message || '-') + '</td>' +
        '<td><span class="badge ' + badgeCls + '">' + esc(statusLabel) + '</span></td>' +
        '<td class="text-xs font-mono text-muted">#' + esc(String(evt.source_message_id || '-')) + '</td>' +
        '<td class="text-xs max-w-[180px] overflow-hidden text-ellipsis whitespace-nowrap" title="' + esc(evt.target_link || evt.target_chat_id || '') + '">' + esc(evt.target_link || evt.target_chat_id || '-') + '</td>' +
        '<td class="text-xs text-muted">' + fmtTime(evt.created_at) + '</td>' +
      '</tr>';
    }).join('') +
    '</tbody></table>';
}

async function openWatchHistoryModal(watchId, page) {
  state.watchHistory = { watchId: watchId, page: page || 1, pageSize: 20, total: 0 };
  const overlay = $('#watch-history-overlay');
  const body = $('#watch-history-body');
  if (!overlay || !body) return;
  overlay.classList.add('open');
  await loadWatchHistoryPage();
}

async function loadWatchHistoryPage() {
  const body = $('#watch-history-body');
  const pagination = $('#watch-history-pagination');
  if (!body || !pagination || !state.watchHistory.watchId) return;
  const page = state.watchHistory.page || 1;
  const pageSize = state.watchHistory.pageSize || 20;
  const offset = (page - 1) * pageSize;
  body.innerHTML = '<div class="p-8 text-center"><div class="spinner mx-auto"></div></div>';
  pagination.innerHTML = '';
  try {
    const data = await fetchJson('/api/watches/' + encodeURIComponent(state.watchHistory.watchId) + '/events?limit=' + pageSize + '&offset=' + offset);
    const items = data.events || [];
    const total = Number(data.total || 0);
    const totalPages = Math.max(1, Math.ceil(total / pageSize));
    state.watchHistory.total = total;
    body.innerHTML = renderWatchEventRows(items);
    pagination.innerHTML = renderPaginationBar({
      prefix: 'watch-history',
      page: page,
      pageSize: pageSize,
      total: total,
      pageInfoKey: 'watches.pageInfo'
    });
    bindPaginationBar('watch-history', page, totalPages, function(newPage) {
      state.watchHistory.page = newPage;
      loadWatchHistoryPage();
    });
  } catch(e) {
    body.innerHTML = '<div class="p-8 text-center text-muted text-sm">' + esc(t('form.requestFailed')) + '</div>';
  }
}

function closeWatchHistoryModal() {
  $('#watch-history-overlay')?.classList.remove('open');
}

/* watch form */
$('#watch-download-form')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const fd = new FormData(this);
  const links = fd.get('source_links').split('\n').map(l => l.trim()).filter(Boolean);
  try {
    await postJson('/api/watches', { type: 'download', source_links: links });
    await loadWatches();
    this.reset();
  } catch(err) {
    alert(translateApiError(err, 'form.createFailed'));
  }
});

$('#watch-forward-form')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const fd = new FormData(this);
  try {
    await postJson('/api/watches', {
      type: 'forward',
      source_link: fd.get('source_link'),
      target_link: fd.get('target_link'),
      include_comment: Boolean(fd.get('include_comment')),
    });
    await loadWatches();
    this.reset();
  } catch(err) {
    alert(translateApiError(err, 'form.createFailed'));
  }
});

document.addEventListener('click', async function(e) {
  const delBtn = e.target.closest('[data-delete-watch]');
  if (delBtn) {
    if (!confirm('确定移除这个监听？')) return;
    try {
      await fetch('/api/watches/' + encodeURIComponent(delBtn.dataset.deleteWatch), { method: 'DELETE' });
      await loadWatches();
    } catch(err) {}
  }
  const editBtn = e.target.closest('[data-edit-watch]');
  if (editBtn) {
    openEditWatchModal(editBtn.dataset.editWatch);
  }
  const historyBtn = e.target.closest('[data-watch-history]');
  if (historyBtn) {
    openWatchHistoryModal(historyBtn.dataset.watchHistory, 1);
  }
});

function openEditWatchModal(watchId) {
  const watch = (state.watches || []).find(w => w.id === watchId);
  if (!watch) return;
  $('#edit-watch-id').value = watch.id;
  $('#edit-watch-source').value = watch.source_link || '';
  $('#edit-watch-target').value = watch.target_link || '';
  $('#edit-watch-comment').checked = watch.include_comment || false;
  $('#watch-edit-overlay').classList.add('open');
}

function closeEditWatchModal() {
  $('#watch-edit-overlay').classList.remove('open');
}

$('#watch-edit-overlay')?.addEventListener('click', function(e) {
  if (e.target === this) closeEditWatchModal();
});

$('#watch-history-overlay')?.addEventListener('click', function(e) {
  if (e.target === this) closeWatchHistoryModal();
});

$('#watch-edit-form')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const fd = new FormData(this);
  const watchId = fd.get('id');
  try {
    await fetch('/api/watches/' + encodeURIComponent(watchId), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_link: fd.get('source_link'),
        target_link: fd.get('target_link'),
        include_comment: Boolean(fd.get('include_comment')),
      }),
    });
    closeEditWatchModal();
    await loadWatches();
  } catch(err) {
    alert(translateApiError(err, 'form.requestFailed'));
  }
});

/* ====== Downloads & Uploads ====== */

/* download type checkboxes — populate from the unified settings schema */
async function loadDownloadTypes() {
  const grid = $('#dl-download-type-grid');
  if (!grid) return;
  if (!state.settings || !state.settingsSchema) {
    try {
      const data = await fetchJson('/api/settings');
      state.settings = data.settings || {};
      state.settingsSchema = data.schema || {};
      state.settingsModel = data.settings_model || {};
    } catch(e) {}
  }
  const types = optionValues((state.settingsModel.options || {}).download_type || (state.settingsSchema || {}).download_type || []);
  const selected = (state.settings && state.settings.user && state.settings.user.download_type) || types;
  grid.innerHTML = types.map(t =>
    '<label class="flex items-center gap-2 text-sm text-text cursor-pointer">' +
      '<input type="checkbox" name="download_type" value="' + t + '" class="w-4 h-4"' + (selected.includes(t) ? ' checked' : '') + '>' +
      '<span>' + t + '</span>' +
    '</label>'
  ).join('');
}

/* Channel Download form */
$('#channel-download-form')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const fd = new FormData(this);
  const payload = {
    chat_link: fd.get('chat_link'),
    download_type: fd.getAll('download_type'),
    keywords: fd.get('keywords') ? fd.get('keywords').split(',').map(k => k.trim()).filter(Boolean) : [],
    include_comment: Boolean(fd.get('include_comment')),
  };
  const startDate = fd.get('start_date');
  const endDate = fd.get('end_date');
  if (startDate || endDate) {
    payload.date_range = {
      start_date: startDate ? new Date(startDate).getTime() / 1000 : null,
      end_date: endDate ? new Date(endDate).getTime() / 1000 : null,
    };
  }
  try {
    await postJson('/api/channel-downloads', payload);
    alert(t('dl.accepted'));
    this.reset();
    loadDownloadTypes();
    loadOperations();
  } catch(err) {
    alert(translateApiError(err, 'form.createFailed'));
  }
});

/* Upload form */
$('#upload-form')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const fd = new FormData(this);
  try {
    await postJson('/api/uploads', {
      path: fd.get('path'),
      target_link: fd.get('target_link'),
      recursive: Boolean(fd.get('recursive')),
    });
    alert(t('dl.uploadAccepted'));
    this.reset();
    loadOperations();
  } catch(err) {
    alert(translateApiError(err, 'form.createFailed'));
  }
});

/* Operations history */
async function loadOperations() {
  if (state.activeView !== 'downloads-uploads') return;
  const tbody = $('#dl-operations-tbody');
  const empty = $('#dl-operations-empty');
  try {
    const data = await fetchJson('/api/operations');
    const ops = data.operations || [];
    if (!ops.length) {
      tbody.innerHTML = '';
      empty.style.display = '';
      return;
    }
    empty.style.display = 'none';
    tbody.innerHTML = ops.map(op => {
      const typeLabel = op.type === 'channel_download' ? t('dl.typeDownload') : t('dl.typeUpload');
      const payload = op.payload || {};
      const detail = op.type === 'channel_download'
        ? (payload.chat_link || '-')
        : (payload.path || '-');
      return '<tr>' +
        '<td class="font-mono text-xs text-muted">' + esc(String(op.id || '-')) + '</td>' +
        '<td><span class="badge ' + (op.type === 'channel_download' ? 'badge-running' : 'badge-success') + '">' + esc(typeLabel) + '</span></td>' +
        '<td class="text-xs max-w-[220px] overflow-hidden text-ellipsis whitespace-nowrap">' + esc(detail) + '</td>' +
        '<td>' + statusBadge(op.status) + '</td>' +
        '<td class="text-xs text-danger max-w-[180px] overflow-hidden text-ellipsis whitespace-nowrap" title="' + esc(op.error_message || '') + '">' + esc(op.error_message || '-') + '</td>' +
        '<td class="text-xs text-muted">' + fmtTime(op.created_at) + '</td>' +
        '</tr>';
    }).join('');
  } catch(e) {}
}

$('#dl-history-refresh')?.addEventListener('click', () => loadOperations());

/* poll operations when active */
setInterval(() => {
  if (state.activeView === 'downloads-uploads') loadOperations();
}, 10000);

/* ====== Statistics ====== */
async function loadStatistics() {
  try {
    const data = await fetchJson('/api/statistics');
    const tables = data.tables || {};
    const tbody = $('#statistics-tbody');
    const rows = [
      { key: 'link', label: t('statistics.link') },
      { key: 'count', label: t('statistics.count') },
      { key: 'upload', label: t('statistics.upload') },
    ];
    tbody.innerHTML = rows.map(r => {
      const tbl = tables[r.key] || {};
      return '<tr>' +
        '<td class="font-semibold">' + r.label + '</td>' +
        '<td>' + (tbl.available ? '<span class="badge badge-success">' + t('statistics.yes') + '</span>' : '<span class="badge badge-paused">' + t('statistics.no') + '</span>') + '</td>' +
        '<td>' + (tbl.rows || 0) + '</td>' +
        '<td>' + (tbl.available ? '<button class="btn btn-sm btn-primary" data-export="' + r.key + '">' + t('statistics.export' + r.key.charAt(0).toUpperCase() + r.key.slice(1)) + '</button>' : '-') + '</td>' +
        '</tr>';
    }).join('');
  } catch(e) {}
}

document.addEventListener('click', async function(e) {
  const exportBtn = e.target.closest('[data-export]');
  if (exportBtn) {
    try {
      await postJson('/api/tables/export', { table_type: exportBtn.dataset.export });
      alert(t('statistics.exported'));
    } catch(err) {
      alert(translateApiError(err, 'form.requestFailed'));
    }
  }
});

/* ====== Settings ====== */
async function loadSettings() {
  try {
    const data = await fetchJson('/api/settings');
    state.settings = data.settings || {};
    state.settingsSchema = data.schema || {};
    state.settingsModel = data.settings_model || {};
    renderSettings();
  } catch(e) {}
}

function renderSettings() {
  if (state.activeView !== 'settings') return;
  const s = state.settings || {};
  const su = s.user || {};
  const sg = s.global || {};

  /* fill paths */
  setFieldVal('user.save_directory', su.save_directory);
  setFieldVal('user.temp_directory', su.temp_directory);
  setFieldVal('user.session_directory', su.session_directory);
  setFieldVal('user.max_tasks.download', su.max_tasks?.download);
  setFieldVal('user.max_tasks.upload', su.max_tasks?.upload);
  setFieldVal('user.max_retries.download', su.max_retries?.download);
  setFieldVal('user.max_retries.upload', su.max_retries?.upload);
  setFieldVal('global.target_profiles.pikpak.max_file_size', sg.target_profiles?.pikpak?.max_file_size);

  /* behavior */
  setCheckboxVal('global.notice', sg.notice);
  setCheckboxVal('user.is_shutdown', su.is_shutdown);
  setCheckboxVal('global.upload.download_upload', sg.upload?.download_upload);
  setCheckboxVal('global.upload.delete', sg.upload?.delete);
  setFieldVal('global.upload.pending_limit', sg.upload?.pending_limit);

  /* archive */
  setCheckboxVal('global.target_profiles.pikpak.archive.enable', sg.target_profiles?.pikpak?.archive?.enable);
  setFieldVal('global.target_profiles.pikpak.archive.remote', sg.target_profiles?.pikpak?.archive?.remote);
  setFieldVal('global.target_profiles.pikpak.archive.source_directory', sg.target_profiles?.pikpak?.archive?.source_directory);
  setFieldVal('global.target_profiles.pikpak.archive.root_directory', sg.target_profiles?.pikpak?.archive?.root_directory);
  setFieldVal('global.target_profiles.pikpak.archive.poll_seconds', sg.target_profiles?.pikpak?.archive?.poll_seconds);
  setFieldVal('global.target_profiles.pikpak.archive.poll_interval_seconds', sg.target_profiles?.pikpak?.archive?.poll_interval_seconds);
  setFieldVal('global.target_profiles.pikpak.archive.match_window_seconds', sg.target_profiles?.pikpak?.archive?.match_window_seconds);

  /* sensitive */
  setSensitiveVal('user.api_id', su.api_id);
  setSensitiveVal('user.api_hash', su.api_hash);
  setSensitiveVal('user.bot_token', su.bot_token);
  setSensitiveVal('user.proxy.password', su.proxy?.password);

  /* download types */
  renderCheckboxGrid('download-type-grid', 'user.download_type', su.download_type || [], (state.settingsModel.options || {}).download_type || state.settingsSchema.download_type);
  /* forward types */
  renderCheckboxGrid('forward-type-grid', 'global.forward_type', sg.forward_type || [], (state.settingsModel.options || {}).forward_type || state.settingsSchema.forward_type);
  /* message filter */
  renderMessageFilter(sg.message_filter || {});
  /* exports */
  setCheckboxVal('global.export_table.link', sg.export_table?.link);
  setCheckboxVal('global.export_table.count', sg.export_table?.count);
  setCheckboxVal('global.export_table.upload', sg.export_table?.upload);
}

function setFieldVal(name, val) {
  const el = document.querySelector('[name="' + name + '"]');
  if (el) el.value = val ?? '';
}

function setCheckboxVal(name, val) {
  const el = document.querySelector('[name="' + name + '"]');
  if (el) el.checked = Boolean(val);
}

function setSensitiveVal(name, val) {
  const el = document.querySelector('[name="' + name + '"]');
  if (!el) return;
  if (val && typeof val === 'object' && val.configured) {
    el.placeholder = t('settings.secretConfigured');
    el.value = '';
  } else {
    el.value = val || '';
  }
}

function renderCheckboxGrid(containerId, inputName, selected, options) {
  const types = normalizeOptionList(options || ['video','photo','audio','voice','animation','document','video_note']);
  const container = document.getElementById(containerId);
  if (!container) return;
  var sel;
  if (Array.isArray(selected)) {
    sel = selected;
  } else if (selected && typeof selected === 'object') {
    // 兼容 dict 格式 {video: true, photo: false, ...}
    sel = Object.entries(selected).filter(function(e) { return e[1]; }).map(function(e) { return e[0]; });
  } else {
    sel = [];
  }
  container.innerHTML = types.map(function(t) {
    const value = typeof t === 'string' ? t : t.value;
    const label = typeof t === 'string' ? t : (t.label || t.value);
    return '<label class="flex items-center gap-2 text-sm text-text cursor-pointer">' +
      '<input type="checkbox" name="' + inputName + '" value="' + esc(value) + '" class="w-4 h-4"' + (sel.indexOf(value) >= 0 ? ' checked' : '') + '>' +
      '<span>' + esc(label) + '</span>' +
    '</label>';
  }).join('');
}

function normalizeOptionList(options) {
  if (Array.isArray(options)) {
    return options.map(function(option) {
      if (option && typeof option === 'object') {
        return {value: String(option.value), label: String(option.label || option.value)};
      }
      return {value: String(option), label: String(option)};
    });
  }
  return Object.keys(options || {}).map(function(key) {
    return {value: String(key), label: String(options[key] || key)};
  });
}

function renderMessageFilter(mf) {
  setCheckboxVal('global.message_filter.enabled', mf.enabled);
  /* media types */
  renderCheckboxGrid('filter-media-grid', 'global.message_filter.media_types', mf.media_types || [], (state.settingsModel.options || {}).message_filter_media_types || (state.settingsSchema.message_filter || {}).media_types);
  /* date range */
  setCheckboxVal('global.message_filter.date_range.enabled', mf.date_range?.enabled);
  setFieldVal('global.message_filter.date_range.start_date', mf.date_range?.start_date);
  setFieldVal('global.message_filter.date_range.end_date', mf.date_range?.end_date);
  /* keywords */
  setCheckboxVal('global.message_filter.keywords.enabled', mf.keywords?.enabled);
  setFieldVal('global.message_filter.keywords.words', (mf.keywords?.words || []).join(','));
}

$('#settings-save').addEventListener('click', async function() {
  const notice = $('#settings-notice');
  const payload = buildSettingsPayload();

  try {
    await patchJson('/api/settings', payload);
    notice.className = 'text-xs text-success mt-2';
    notice.textContent = t('settings.saved');
    notice.style.display = '';
    setTimeout(() => { notice.style.display = 'none'; }, 3000);
  } catch(err) {
    notice.className = 'text-xs text-danger mt-2';
    notice.textContent = translateApiError(err, 'form.requestFailed');
    notice.style.display = '';
  }
});

function buildSettingsPayload() {
  /* rebuild full settings structure from form */
  const payload = { user: {}, global: {} };

  /* user settings */
  $$('[name^="user."]').forEach(el => {
    if (!el.name) return;
    if (el.name === 'user.download_type') return;
    const parts = el.name.split('.');
    if (parts[0] !== 'user') return;
    if (el.type === 'checkbox') {
      setNested(payload, parts, el.checked);
    } else if (el.value !== '') {
      setNested(payload, parts, el.value);
    }
  });

  /* global settings */
  $$('[name^="global."]').forEach(el => {
    if (!el.name) return;
    if (el.name === 'global.forward_type' || el.name === 'global.message_filter.media_types') return;
    const parts = el.name.split('.');
    if (parts[0] !== 'global') return;
    if (el.type === 'checkbox') {
      setNested(payload, parts, el.checked);
    } else if (el.value !== '') {
      setNested(payload, parts, el.value);
    }
  });

  /* download types */
  const downloadTypes = Array.from($$('input[name="user.download_type"]:checked')).map(cb => cb.value);
  setNested(payload, ['user', 'download_type'], downloadTypes);

  /* forward types */
  const forwardTypes = Array.from($$('input[name="global.forward_type"]:checked')).map(cb => cb.value);
  const forwardTypeOptions = normalizeOptionList((state.settingsModel.options || {}).forward_type || state.settingsSchema.forward_type || []);
  const allForwardTypes = forwardTypeOptions.length ? forwardTypeOptions.map(function(option) { return option.value; }) : forwardTypes;
  const forwardTypesDict = {};
  allForwardTypes.forEach(function(t) { forwardTypesDict[t] = forwardTypes.indexOf(t) >= 0; });
  setNested(payload, ['global', 'forward_type'], forwardTypesDict);

  /* filter media types — 构建 {video: true, photo: false, ...} dict 格式与后端一致 */
  const mediaTypeOptions = normalizeOptionList((state.settingsModel.options || {}).message_filter_media_types || (state.settingsSchema.message_filter || {}).media_types || []);
  const allMediaTypes = mediaTypeOptions.length ? mediaTypeOptions.map(function(option) { return option.value; }) : ['video','photo','audio','document','voice','text','animation','video_note'];
  const checkedMedia = Array.from($$('input[name="global.message_filter.media_types"]:checked')).map(function(cb) { return cb.value; });
  const mediaTypesDict = {};
  allMediaTypes.forEach(function(t) { mediaTypesDict[t] = checkedMedia.indexOf(t) >= 0; });
  setNested(payload, ['global', 'message_filter', 'media_types'], mediaTypesDict);

  /* filter keywords */
  const kwInput = document.querySelector('[name="global.message_filter.keywords.words"]');
  if (kwInput && kwInput.value) {
    setNested(payload, ['global', 'message_filter', 'keywords', 'words'], kwInput.value.split(',').map(k => k.trim()).filter(Boolean));
  }

  return payload;
}

function setNested(obj, parts, value) {
  let current = obj;
  for (let i = 0; i < parts.length - 1; i++) {
    if (!current[parts[i]]) current[parts[i]] = {};
    current = current[parts[i]];
  }
  current[parts[parts.length - 1]] = value;
}

/* ====== Media Management ====== */
let mediaScanResult = null;
let mediaItemsPage = 0;
let mediaOrphansPage = 0;
const MEDIA_PAGE_SIZE = 50;

function showMediaElement(el, visible) {
  if (!el) return;
  el.classList.toggle('hidden', !visible);
  el.style.display = visible ? '' : 'none';
}

function setMediaScanButtonLoading(isLoading) {
  const btn = $('#media-scan-btn');
  if (!btn) return;
  const label = btn.querySelector('[data-i18n]');
  btn.disabled = Boolean(isLoading);
  btn.setAttribute('aria-busy', isLoading ? 'true' : 'false');
  if (label) label.textContent = isLoading ? t('media.scanning') : t('media.scan');
}

function updateMediaCleanupButton() {
  const btn = $('#media-cleanup-btn');
  if (!btn) return;
  btn.disabled = $$('.media-cb:checked').length === 0;
}

function mediaScanUrl() {
  var itemsOffset = mediaItemsPage * MEDIA_PAGE_SIZE;
  var orphansOffset = mediaOrphansPage * MEDIA_PAGE_SIZE;
  return '/api/media/scan?items_limit=' + MEDIA_PAGE_SIZE + '&items_offset=' + itemsOffset +
    '&orphans_limit=' + MEDIA_PAGE_SIZE + '&orphans_offset=' + orphansOffset;
}

async function loadMedia() {
  const container = $('#media-result');
  try {
    setMediaScanButtonLoading(true);
    updateMediaCleanupButton();
    if (container) {
      container.classList.remove('hidden');
      container.style.display = '';
      container.innerHTML = '<div class="p-8 text-center"><div class="spinner mx-auto"></div><div class="text-xs text-muted mt-2">' + t('media.scanning') + '</div></div>';
      updateMediaCleanupButton();
    }
    const data = await fetchJson(mediaScanUrl());
    mediaScanResult = data;
    renderMediaResult(data);
  } catch(e) {
    renderMediaError(e);
  } finally {
    setMediaScanButtonLoading(false);
  }
}

function renderMediaPagination(prefix, page, totalPages, totalCount) {
  if (totalPages <= 1) return '';
  return renderPaginationBar({
    prefix: prefix,
    page: page + 1,
    pageSize: MEDIA_PAGE_SIZE,
    total: totalCount
  });
}

function bindMediaPagination(prefix, currentPage, totalPages, onChange) {
  bindPaginationBar(prefix, currentPage + 1, totalPages, function(newPage) {
    onChange(newPage - 1);
  });
}

function renderMediaResult(data) {
  const container = $('#media-result');
  if (!container) return;
  if (!data) {
    container.classList.add('hidden');
    container.style.display = 'none';
    return;
  }

  container.classList.remove('hidden');
  container.style.display = '';
  container.innerHTML =
    '<div id="media-summary" class="flex gap-5 flex-wrap p-4 bg-surface-alt rounded-lg mb-4"></div>' +
    '<div id="media-items-section" class="mb-4 hidden">' +
      '<h4 class="text-base font-semibold mb-2">' + t('media.transferItems') + '</h4>' +
      '<div class="overflow-x-auto rounded-lg border border-line">' +
        '<table class="data-table min-w-[600px]"><thead><tr>' +
          '<th class="w-10"><input type="checkbox" id="media-select-all-items"></th>' +
          '<th>' + t('media.file') + '</th>' +
          '<th class="text-right">' + t('media.size') + '</th>' +
          '<th class="text-center">' + t('media.status') + '</th>' +
          '<th>' + t('media.source') + '</th>' +
        '</tr></thead><tbody id="media-items-tbody"></tbody></table>' +
      '</div>' +
      '<div id="media-items-pagination"></div>' +
    '</div>' +
    '<div id="media-orphans-section" class="mb-4 hidden">' +
      '<h4 class="text-base font-semibold mb-2">' + t('media.orphanFiles') + '</h4>' +
      '<div class="overflow-x-auto rounded-lg border border-line">' +
        '<table class="data-table min-w-[600px]"><thead><tr>' +
          '<th class="w-10"><input type="checkbox" id="media-select-all-orphans"></th>' +
          '<th>' + t('media.path') + '</th>' +
          '<th class="text-right">' + t('media.size') + '</th>' +
          '<th>' + t('media.mtime') + '</th>' +
        '</tr></thead><tbody id="media-orphans-tbody"></tbody></table>' +
      '</div>' +
      '<div id="media-orphans-pagination"></div>' +
    '</div>';

  const ti = data.transfer_items || {};
  const orph = data.orphan_files || {};

  /* summary */
  $('#media-summary').innerHTML =
    '<div><strong class="text-xl font-bold text-primary">' + (data.total_count || 0) + '</strong><span class="text-xs text-muted ml-1">' + t('media.totalFiles') + '</span></div>' +
    '<div><strong class="text-xl font-bold text-primary">' + fmtSize(data.total_size || 0) + '</strong><span class="text-xs text-muted ml-1">' + t('media.totalSize') + '</span></div>' +
    '<div><strong class="text-xl font-bold text-primary">' + (data.retention_days || 7) + '</strong><span class="text-xs text-muted ml-1">' + t('media.retentionDays') + '</span></div>';

  /* transfer items */
  const items = ti.items || [];
  const itemsSection = $('#media-items-section');
  const totalItemsPages = Math.max(1, Math.ceil((ti.total_count || 0) / MEDIA_PAGE_SIZE));
  if (ti.total_count > 0) {
    showMediaElement(itemsSection, true);
    if (items.length) {
      $('#media-items-tbody').innerHTML = items.map(item => '<tr>' +
        '<td><input type="checkbox" class="media-cb" data-type="item" data-id="' + item.item_id + '"></td>' +
        '<td class="text-xs max-w-[240px] overflow-hidden text-ellipsis whitespace-nowrap" title="' + esc((item.paths || []).join('\\n') || item.local_path || '') + '">' + esc(item.file_name || item.local_path || '-') + '</td>' +
        '<td class="text-xs text-right">' + fmtSize(item.file_size) + '</td>' +
        '<td class="text-center">' + statusBadge(item.status || '') + '</td>' +
        '<td class="text-xs max-w-[160px] overflow-hidden text-ellipsis whitespace-nowrap" title="' + esc(item.source_link || '-') + '">' + esc(item.source_link || '-') + '</td>' +
        '</tr>').join('');
    } else {
      $('#media-items-tbody').innerHTML = '<tr><td colspan="5" class="text-center text-muted text-xs py-4">暂无数据</td></tr>';
    }
    $('#media-items-pagination').innerHTML = renderMediaPagination('media-items', mediaItemsPage, totalItemsPages, ti.total_count || 0);
    bindMediaPagination('media-items', mediaItemsPage, totalItemsPages, function(newPage) {
      mediaItemsPage = newPage;
      loadMedia();
    });
  } else {
    showMediaElement(itemsSection, false);
  }

  /* orphans */
  const files = orph.files || [];
  const orphansSection = $('#media-orphans-section');
  const totalOrphansPages = Math.max(1, Math.ceil((orph.total_count || 0) / MEDIA_PAGE_SIZE));
  if (orph.total_count > 0) {
    showMediaElement(orphansSection, true);
    if (files.length) {
      $('#media-orphans-tbody').innerHTML = files.map(f => '<tr>' +
        '<td><input type="checkbox" class="media-cb" data-type="orphan" data-path="' + esc(f.path) + '"></td>' +
        '<td class="text-xs max-w-[240px] overflow-hidden text-ellipsis whitespace-nowrap" title="' + esc(f.path) + '">' + esc(f.path) + '</td>' +
        '<td class="text-xs text-right">' + fmtSize(f.size) + '</td>' +
        '<td class="text-xs text-muted">' + fmtTimestamp(f.mtime) + '</td>' +
        '</tr>').join('');
    } else {
      $('#media-orphans-tbody').innerHTML = '<tr><td colspan="4" class="text-center text-muted text-xs py-4">暂无数据</td></tr>';
    }
    $('#media-orphans-pagination').innerHTML = renderMediaPagination('media-orphans', mediaOrphansPage, totalOrphansPages, orph.total_count || 0);
    bindMediaPagination('media-orphans', mediaOrphansPage, totalOrphansPages, function(newPage) {
      mediaOrphansPage = newPage;
      loadMedia();
    });
  } else {
    showMediaElement(orphansSection, false);
  }

  if (!ti.total_count && !orph.total_count) {
    container.insertAdjacentHTML('beforeend', '<div class="p-6 text-center text-muted text-sm">' + t('media.empty') + '</div>');
  }

  /* select-all */
  const selectAllItems = $('#media-select-all-items');
  if (selectAllItems) selectAllItems.onclick = function() {
    $$('#media-items-tbody .media-cb').forEach(cb => cb.checked = this.checked);
    updateMediaCleanupButton();
  };
  const selectAllOrphans = $('#media-select-all-orphans');
  if (selectAllOrphans) selectAllOrphans.onclick = function() {
    $$('#media-orphans-tbody .media-cb').forEach(cb => cb.checked = this.checked);
    updateMediaCleanupButton();
  };
  updateMediaCleanupButton();
}


function renderMediaError(error) {
  const container = $('#media-result');
  if (!container) return;
  container.classList.remove('hidden');
  container.style.display = '';
  container.innerHTML =
    '<div class="p-6 rounded-lg border border-line bg-danger-bg text-danger text-sm">' +
      esc(translateApiError(error, 'form.requestFailed')) +
    '</div>';
  updateMediaCleanupButton();
}

async function doMediaCleanup() {
  const checked = $$('.media-cb:checked');
  if (!checked.length) { alert(t('media.noSelection')); return; }
  if (!confirm(t('media.confirmCleanup'))) return;

  const payload = { item_ids: [], file_paths: [] };
  checked.forEach(cb => {
    if (cb.dataset.type === 'item') payload.item_ids.push(Number(cb.dataset.id));
    else payload.file_paths.push(cb.dataset.path);
  });

  try {
    const result = await postJson('/api/media/cleanup', payload);
    alert(t('media.cleanupDone').replace('{count}', result.total_deleted_count || 0).replace('{size}', fmtSize(result.total_deleted_size || 0)));
    mediaItemsPage = 0;
    mediaOrphansPage = 0;
    loadMedia();
  } catch(e) {
    alert(translateApiError(e, 'form.requestFailed'));
  }
}

$('#media-scan-btn')?.addEventListener('click', function() {
  mediaItemsPage = 0;
  mediaOrphansPage = 0;
  loadMedia();
});
$('#media-cleanup-btn')?.addEventListener('click', doMediaCleanup);
document.addEventListener('change', function(e) {
  if (e.target && e.target.classList && e.target.classList.contains('media-cb')) {
    updateMediaCleanupButton();
  }
});

/* ====== Init ====== */
(function init() {
  applyLanguage();
  checkAuthStatus();
  authPollTimer = setInterval(() => {
    if (authStep === 'done' || authStep === 'none') {
      clearInterval(authPollTimer);
      authPollTimer = null;
      return;
    }
    checkAuthStatus();
  }, 2000);
})();
</script>
</body>
</html>
"""

WEB_UI_MOBILE_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title data-i18n="app.title">TRMD 转存控制台</title>
<style>@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 300;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/cc762462ea67.woff2) format('woff2');
  unicode-range: U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 300;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d5bab8e28732.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 300;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d8e4fe0452aa.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 400;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/cc762462ea67.woff2) format('woff2');
  unicode-range: U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 400;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d5bab8e28732.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 400;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d8e4fe0452aa.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 500;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/cc762462ea67.woff2) format('woff2');
  unicode-range: U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 500;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d5bab8e28732.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 500;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d8e4fe0452aa.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 600;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/cc762462ea67.woff2) format('woff2');
  unicode-range: U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 600;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d5bab8e28732.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 600;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d8e4fe0452aa.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 700;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/cc762462ea67.woff2) format('woff2');
  unicode-range: U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 700;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d5bab8e28732.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 700;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d8e4fe0452aa.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url(/fonts/0b1fcab42c18.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url(/fonts/7d93459d8658.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 500;
  font-display: swap;
  src: url(/fonts/af5fda16a191.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 500;
  font-display: swap;
  src: url(/fonts/cd36de204aca.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url(/fonts/bb1f2d582e7f.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url(/fonts/f4e80d9dfd37.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 700;
  font-display: swap;
  src: url(/fonts/ccfd87f69ef0.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 700;
  font-display: swap;
  src: url(/fonts/9338e65fc077.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 800;
  font-display: swap;
  src: url(/fonts/a72eccfa6cfa.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 800;
  font-display: swap;
  src: url(/fonts/60bf0aba6526.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}</style>
<style>/*! tailwindcss v4.1.18 | MIT License | https://tailwindcss.com */
@layer properties{@supports (((-webkit-hyphens:none)) and (not (margin-trim:inline))) or ((-moz-orient:inline) and (not (color:rgb(from red r g b)))){*,:before,:after,::backdrop{--tw-rotate-x:initial;--tw-rotate-y:initial;--tw-rotate-z:initial;--tw-skew-x:initial;--tw-skew-y:initial;--tw-border-style:solid;--tw-leading:initial;--tw-font-weight:initial;--tw-tracking:initial;--tw-shadow:0 0 #0000;--tw-shadow-color:initial;--tw-shadow-alpha:100%;--tw-inset-shadow:0 0 #0000;--tw-inset-shadow-color:initial;--tw-inset-shadow-alpha:100%;--tw-ring-color:initial;--tw-ring-shadow:0 0 #0000;--tw-inset-ring-color:initial;--tw-inset-ring-shadow:0 0 #0000;--tw-ring-inset:initial;--tw-ring-offset-width:0px;--tw-ring-offset-color:#fff;--tw-ring-offset-shadow:0 0 #0000;--tw-outline-style:solid;--tw-blur:initial;--tw-brightness:initial;--tw-contrast:initial;--tw-grayscale:initial;--tw-hue-rotate:initial;--tw-invert:initial;--tw-opacity:initial;--tw-saturate:initial;--tw-sepia:initial;--tw-drop-shadow:initial;--tw-drop-shadow-color:initial;--tw-drop-shadow-alpha:100%;--tw-drop-shadow-size:initial;--tw-backdrop-blur:initial;--tw-backdrop-brightness:initial;--tw-backdrop-contrast:initial;--tw-backdrop-grayscale:initial;--tw-backdrop-hue-rotate:initial;--tw-backdrop-invert:initial;--tw-backdrop-opacity:initial;--tw-backdrop-saturate:initial;--tw-backdrop-sepia:initial;--tw-duration:initial}}}@layer theme{:root,:host{--font-sans:ui-sans-serif,system-ui,sans-serif,"Apple Color Emoji","Segoe UI Emoji","Segoe UI Symbol","Noto Color Emoji";--font-mono:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono","Courier New",monospace;--color-red-200:oklch(88.5% .062 18.334);--color-red-300:oklch(80.8% .114 19.571);--color-orange-50:oklch(98% .016 73.684);--color-slate-100:oklch(96.8% .007 247.896);--color-slate-300:oklch(86.9% .022 252.894);--color-slate-500:oklch(55.4% .046 257.417);--color-black:#000;--color-white:#fff;--spacing:.25rem;--text-xs:.75rem;--text-xs--line-height:calc(1/.75);--text-sm:.875rem;--text-sm--line-height:calc(1.25/.875);--text-base:1rem;--text-base--line-height:calc(1.5/1);--text-lg:1.125rem;--text-lg--line-height:calc(1.75/1.125);--text-xl:1.25rem;--text-xl--line-height:calc(1.75/1.25);--text-2xl:1.5rem;--text-2xl--line-height:calc(2/1.5);--font-weight-normal:400;--font-weight-medium:500;--font-weight-semibold:600;--font-weight-bold:700;--font-weight-extrabold:800;--leading-tight:1.25;--leading-relaxed:1.625;--radius-sm:8px;--radius-md:.375rem;--radius-lg:.5rem;--radius-xl:.75rem;--radius-2xl:1rem;--animate-spin:spin 1s linear infinite;--default-transition-duration:.15s;--default-transition-timing-function:cubic-bezier(.4,0,.2,1);--default-font-family:var(--font-sans);--default-mono-font-family:var(--font-mono);--color-primary:#2563eb;--color-primary-light:#3b82f6;--color-primary-soft:#eff6ff;--color-primary-ghost:#dbeafe;--color-primary-dark:#1d4ed8;--color-bg:#f0f4ff;--color-surface:#fff;--color-surface-alt:#f8fafc;--color-surface-hover:#f1f5f9;--color-surface-muted:#f0f3f5;--color-text:#1e293b;--color-text-secondary:#475569;--color-muted:#94a3b8;--color-line:#e2e8f0;--color-line-light:#f1f5f9;--color-success:#10b981;--color-success-bg:#ecfdf5;--color-warning:#f59e0b;--color-warning-bg:#fffbeb;--color-danger:#ef4444;--color-danger-bg:#fef2f2;--color-cta:#f97316;--font-heading:"Poppins","PingFang SC","Microsoft YaHei","Noto Sans SC",ui-sans-serif,system-ui,sans-serif;--font-body:"Open Sans","PingFang SC","Microsoft YaHei","Noto Sans SC",ui-sans-serif,system-ui,sans-serif;--font-mob:"Inter","PingFang SC","Microsoft YaHei","Noto Sans SC",ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;--tab-height:56px;--topbar-height:48px}}@layer base{*,:after,:before,::backdrop{box-sizing:border-box;border:0 solid;margin:0;padding:0}::file-selector-button{box-sizing:border-box;border:0 solid;margin:0;padding:0}html,:host{-webkit-text-size-adjust:100%;tab-size:4;line-height:1.5;font-family:var(--default-font-family,ui-sans-serif,system-ui,sans-serif,"Apple Color Emoji","Segoe UI Emoji","Segoe UI Symbol","Noto Color Emoji");font-feature-settings:var(--default-font-feature-settings,normal);font-variation-settings:var(--default-font-variation-settings,normal);-webkit-tap-highlight-color:transparent}hr{height:0;color:inherit;border-top-width:1px}abbr:where([title]){-webkit-text-decoration:underline dotted;text-decoration:underline dotted}h1,h2,h3,h4,h5,h6{font-size:inherit;font-weight:inherit}a{color:inherit;-webkit-text-decoration:inherit;-webkit-text-decoration:inherit;-webkit-text-decoration:inherit;text-decoration:inherit}b,strong{font-weight:bolder}code,kbd,samp,pre{font-family:var(--default-mono-font-family,ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono","Courier New",monospace);font-feature-settings:var(--default-mono-font-feature-settings,normal);font-variation-settings:var(--default-mono-font-variation-settings,normal);font-size:1em}small{font-size:80%}sub,sup{vertical-align:baseline;font-size:75%;line-height:0;position:relative}sub{bottom:-.25em}sup{top:-.5em}table{text-indent:0;border-color:inherit;border-collapse:collapse}:-moz-focusring{outline:auto}progress{vertical-align:baseline}summary{display:list-item}ol,ul,menu{list-style:none}img,svg,video,canvas,audio,iframe,embed,object{vertical-align:middle;display:block}img,video{max-width:100%;height:auto}button,input,select,optgroup,textarea{font:inherit;font-feature-settings:inherit;font-variation-settings:inherit;letter-spacing:inherit;color:inherit;opacity:1;background-color:#0000;border-radius:0}::file-selector-button{font:inherit;font-feature-settings:inherit;font-variation-settings:inherit;letter-spacing:inherit;color:inherit;opacity:1;background-color:#0000;border-radius:0}:where(select:is([multiple],[size])) optgroup{font-weight:bolder}:where(select:is([multiple],[size])) optgroup option{padding-inline-start:20px}::file-selector-button{margin-inline-end:4px}::placeholder{opacity:1}@supports (not ((-webkit-appearance:-apple-pay-button))) or (contain-intrinsic-size:1px){::placeholder{color:currentColor}@supports (color:color-mix(in lab, red, red)){::placeholder{color:color-mix(in oklab,currentcolor 50%,transparent)}}}textarea{resize:vertical}::-webkit-search-decoration{-webkit-appearance:none}::-webkit-date-and-time-value{min-height:1lh;text-align:inherit}::-webkit-datetime-edit{display:inline-flex}::-webkit-datetime-edit-fields-wrapper{padding:0}::-webkit-datetime-edit{padding-block:0}::-webkit-datetime-edit-year-field{padding-block:0}::-webkit-datetime-edit-month-field{padding-block:0}::-webkit-datetime-edit-day-field{padding-block:0}::-webkit-datetime-edit-hour-field{padding-block:0}::-webkit-datetime-edit-minute-field{padding-block:0}::-webkit-datetime-edit-second-field{padding-block:0}::-webkit-datetime-edit-millisecond-field{padding-block:0}::-webkit-datetime-edit-meridiem-field{padding-block:0}::-webkit-calendar-picker-indicator{line-height:1}:-moz-ui-invalid{box-shadow:none}button,input:where([type=button],[type=reset],[type=submit]){appearance:button}::file-selector-button{appearance:button}::-webkit-inner-spin-button{height:auto}::-webkit-outer-spin-button{height:auto}[hidden]:where(:not([hidden=until-found])){display:none!important}:root{--safe-bottom:env(safe-area-inset-bottom,0px)}html{font-family:var(--font-body);color:var(--color-text);background:var(--color-bg);font-size:15px;line-height:1.5}body{min-height:100vh;display:flex}button,input,select,textarea{font-family:inherit;font-size:inherit}button{cursor:pointer}button:disabled{cursor:not-allowed;opacity:.55}}@layer components{.sidebar{top:calc(var(--spacing)*0);z-index:50;border-right-style:var(--tw-border-style);border-right-width:1px;border-color:var(--color-line);background-color:var(--color-white);width:250px;height:100vh;padding-inline:calc(var(--spacing)*4);padding-block:calc(var(--spacing)*6);flex-direction:column;display:flex;position:sticky}.sidebar-brand{margin-bottom:calc(var(--spacing)*3);align-items:center;gap:calc(var(--spacing)*3);border-bottom-style:var(--tw-border-style);border-bottom-width:1px;border-color:var(--color-line);padding-bottom:calc(var(--spacing)*5);display:flex}.sidebar-brand-mark{height:calc(var(--spacing)*10);width:calc(var(--spacing)*10);font-size:var(--text-lg);line-height:var(--tw-leading,var(--text-lg--line-height));--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold);color:var(--color-white);background:linear-gradient(135deg,var(--color-primary),var(--color-primary-light));font-family:var(--font-heading);border-radius:10px;justify-content:center;align-items:center;display:flex;box-shadow:0 4px 10px #2563eb4d}.sidebar-nav-section{flex:1;overflow-y:auto}.sidebar-nav-label{padding-inline:calc(var(--spacing)*2.5);padding-top:calc(var(--spacing)*4);padding-bottom:calc(var(--spacing)*2);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);--tw-tracking:.08em;letter-spacing:.08em;color:var(--color-muted);text-transform:uppercase}.sidebar-nav-item{cursor:pointer;align-items:center;gap:calc(var(--spacing)*2.5);border-style:var(--tw-border-style);width:100%;padding-inline:calc(var(--spacing)*3);padding-block:calc(var(--spacing)*2.5);text-align:left;font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));--tw-font-weight:var(--font-weight-medium);font-weight:var(--font-weight-medium);color:var(--color-text-secondary);transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;background-color:#0000;border-width:0;border-radius:8px;font-family:inherit;transition-duration:.15s;display:flex}.sidebar-nav-item:hover{background-color:var(--color-primary-soft);color:var(--color-primary)}.sidebar-nav-item.active{background-color:var(--color-primary-soft);--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-primary)}.sidebar-nav-item svg{flex-shrink:0;width:18px;height:18px}.sidebar-nav-badge{background-color:var(--color-primary-ghost);padding-inline:calc(var(--spacing)*2);padding-block:calc(var(--spacing)*.5);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold);color:var(--color-primary);border-radius:3.40282e38px;margin-left:auto}.sidebar-footer{margin-top:calc(var(--spacing)*2);gap:calc(var(--spacing)*1.5);border-top-style:var(--tw-border-style);border-top-width:1px;border-color:var(--color-line);padding-top:calc(var(--spacing)*4);flex-direction:column;display:flex}.sidebar-footer-info{align-items:center;gap:calc(var(--spacing)*2);padding-inline:calc(var(--spacing)*2);padding-block:calc(var(--spacing)*1);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-text-secondary);display:flex}.sidebar-status-dot{height:calc(var(--spacing)*2);width:calc(var(--spacing)*2);background:var(--color-success);border-radius:3.40282e38px;flex-shrink:0;box-shadow:0 0 0 3px #10b98133}.sidebar-version{padding-inline:calc(var(--spacing)*2);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));color:var(--color-muted);opacity:.7}.main-content{min-width:calc(var(--spacing)*0);gap:calc(var(--spacing)*6);padding:calc(var(--spacing)*7);flex-direction:column;flex:1;display:flex}.topbar{justify-content:space-between;align-items:flex-start;gap:calc(var(--spacing)*4);display:flex}.topbar h1{font-size:var(--text-xl);line-height:var(--tw-leading,var(--text-xl--line-height));--tw-leading:var(--leading-tight);line-height:var(--leading-tight);--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold);color:var(--color-text);font-family:var(--font-heading)}.topbar p{margin-top:calc(var(--spacing)*1);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-muted)}.btn{cursor:pointer;align-items:center;gap:calc(var(--spacing)*1.5);border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);padding-inline:calc(var(--spacing)*4);padding-block:calc(var(--spacing)*2);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));--tw-font-weight:var(--font-weight-medium);font-weight:var(--font-weight-medium);white-space:nowrap;color:var(--color-text);transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;border-radius:6px;font-family:inherit;transition-duration:.15s;display:inline-flex}.btn:hover{border-color:var(--color-primary-light);background-color:var(--color-primary-soft)}.btn svg{height:calc(var(--spacing)*4);width:calc(var(--spacing)*4);flex-shrink:0}.btn-primary{border-color:var(--color-primary);background-color:var(--color-primary);--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-white)}.btn-primary:hover{border-color:var(--color-primary-dark);background-color:var(--color-primary-dark);color:var(--color-white)}.btn-danger{border-color:var(--color-red-200);color:var(--color-danger)}.btn-danger:hover{border-color:var(--color-danger);background-color:var(--color-danger-bg);color:var(--color-danger)}.btn-sm{padding-inline:calc(var(--spacing)*2.5);padding-block:calc(var(--spacing)*1);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height))}.btn-icon{width:34px;height:34px;padding:calc(var(--spacing)*0);justify-content:center}.stat-grid{gap:calc(var(--spacing)*4);grid-template-columns:repeat(4,minmax(0,1fr));display:grid}.stat-card{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);--tw-shadow:0 1px 3px 0 var(--tw-shadow-color,#0000001a),0 1px 2px -1px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow);transition-property:box-shadow;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.2s;border-radius:12px;justify-content:space-between;align-items:flex-start;padding:18px;transition-duration:.2s;display:flex}.stat-card:hover{border-color:var(--color-primary-ghost);--tw-shadow:0 4px 6px -1px var(--tw-shadow-color,#0000001a),0 2px 4px -2px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow)}.stat-card-icon{height:calc(var(--spacing)*10);width:calc(var(--spacing)*10);border-radius:8px;flex-shrink:0;justify-content:center;align-items:center;display:flex}.stat-card-icon.blue{background-color:var(--color-primary-soft);color:var(--color-primary)}.stat-card-icon.green{background-color:var(--color-success-bg);color:var(--color-success)}.stat-card-icon.orange{background-color:var(--color-orange-50);color:var(--color-cta)}.stat-card-icon.red{background-color:var(--color-danger-bg);color:var(--color-danger)}.stat-card-icon svg{height:calc(var(--spacing)*5);width:calc(var(--spacing)*5)}.stat-card-value{text-align:right;font-size:var(--text-xl);line-height:var(--tw-leading,var(--text-xl--line-height));--tw-leading:var(--leading-tight);line-height:var(--leading-tight);--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold);color:var(--color-text);font-family:var(--font-heading)}.stat-card-label{margin-top:calc(var(--spacing)*1);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-medium);font-weight:var(--font-weight-medium);color:var(--color-muted)}.panel{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);--tw-shadow:0 1px 3px 0 var(--tw-shadow-color,#0000001a),0 1px 2px -1px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow);border-radius:12px;flex-direction:column;display:flex;overflow:hidden}.panel-header{border-bottom-style:var(--tw-border-style);border-bottom-width:1px;border-color:var(--color-line);background-color:var(--color-surface-alt);padding-inline:18px;padding-block:calc(var(--spacing)*3.5);justify-content:space-between;align-items:center;display:flex}.panel-header h3{font-size:var(--text-base);line-height:var(--tw-leading,var(--text-base--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-text);font-family:var(--font-heading)}.panel-body{flex:1;padding:18px;overflow-y:auto}.panel-tabs{gap:calc(var(--spacing)*.5);display:flex}.panel-tab{cursor:pointer;border-style:var(--tw-border-style);padding-inline:calc(var(--spacing)*2.5);padding-block:calc(var(--spacing)*1);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-medium);font-weight:var(--font-weight-medium);color:var(--color-text-secondary);transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.1s;background-color:#0000;border-width:0;border-radius:.25rem;font-family:inherit;transition-duration:.1s}.panel-tab:hover{background-color:var(--color-primary-soft);color:var(--color-primary)}.panel-tab.active{background-color:var(--color-primary-soft);--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-primary)}.form-group{margin-bottom:calc(var(--spacing)*3.5)}.form-label{margin-bottom:calc(var(--spacing)*1.5);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);--tw-tracking:.04em;letter-spacing:.04em;color:var(--color-muted);text-transform:uppercase;display:block}.form-input,.form-select{height:calc(var(--spacing)*10);border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);width:100%;padding-inline:calc(var(--spacing)*3);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-text);transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;--tw-outline-style:none;border-radius:6px;outline-style:none;font-family:inherit;transition-duration:.15s}.form-input:focus,.form-select:focus{border-color:var(--color-primary);box-shadow:0 0 0 3px #2563eb1f}.watch-download-sources{resize:vertical;min-height:124px}.download-upload-align-spacer{margin-bottom:calc(var(--spacing)*3.5);border-style:var(--tw-border-style);--tw-border-style:dashed;border-style:dashed;border-width:1px;border-color:var(--color-line);background-color:var(--color-surface-alt);min-height:88px;padding-inline:calc(var(--spacing)*4);text-align:center;font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-muted);border-radius:8px;justify-content:center;align-items:center;display:flex}@media (min-width:64rem){.download-upload-align-spacer{min-height:184px}}.form-row{gap:calc(var(--spacing)*2.5);grid-template-columns:repeat(2,minmax(0,1fr));display:grid}.form-submit{margin-top:calc(var(--spacing)*1.5);height:calc(var(--spacing)*10);cursor:pointer;justify-content:center;align-items:center;gap:calc(var(--spacing)*1.5);border-style:var(--tw-border-style);background-color:var(--color-primary);width:100%;font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-white);transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;border-width:0;border-radius:6px;font-family:inherit;transition-duration:.15s;display:flex}.form-submit:hover{background-color:var(--color-primary-dark)}.data-table{border-collapse:collapse;width:100%;font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height))}.data-table thead th{top:calc(var(--spacing)*0);border-bottom-style:var(--tw-border-style);border-bottom-width:2px;border-color:var(--color-line);background-color:var(--color-surface-alt);padding-inline:calc(var(--spacing)*3);padding-block:calc(var(--spacing)*2.5);text-align:center;font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);--tw-tracking:.05em;letter-spacing:.05em;white-space:nowrap;color:var(--color-muted);text-transform:uppercase;position:sticky}.data-table tbody td{border-bottom-style:var(--tw-border-style);border-bottom-width:1px;border-color:var(--color-line-light);padding-inline:calc(var(--spacing)*3);padding-block:calc(var(--spacing)*2.5);text-align:center;vertical-align:middle;font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height))}.table-actions{justify-content:center}.data-table tbody tr{cursor:pointer;transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:75ms;transition-duration:75ms}.data-table tbody tr:hover{background-color:var(--color-surface-hover)}.data-table tbody tr.selected{background-color:var(--color-primary-soft)}.task-items-table{table-layout:fixed;min-width:840px}.task-items-table .task-item-col-file{width:34%}.task-items-table .task-item-col-size{width:112px}.task-items-table .task-item-col-progress,.task-items-table .task-item-col-source{width:220px}.task-items-table .task-item-col-status{width:118px}.task-items-table th,.task-items-table td{white-space:nowrap}.task-items-table .task-item-file{text-align:left;white-space:normal;overflow-wrap:anywhere;word-break:break-word;line-height:1.45}.task-items-table .task-item-size,.task-items-table .task-item-status{min-width:112px}.task-items-table .task-item-progress,.task-items-table .task-item-source{text-overflow:ellipsis;overflow:hidden}.badge{padding-inline:calc(var(--spacing)*2.5);padding-block:calc(var(--spacing)*.5);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);border-radius:3.40282e38px;align-items:center;display:inline-flex}.badge-running{background-color:var(--color-primary-soft);color:var(--color-primary)}.badge-success{background-color:var(--color-success-bg);color:var(--color-success)}.badge-failed{background-color:var(--color-danger-bg);color:var(--color-danger)}.badge-pending{background-color:var(--color-orange-50);color:var(--color-cta)}.badge-paused,.badge-skipped{background-color:var(--color-slate-100);color:var(--color-slate-500)}.badge-warning{background-color:var(--color-warning-bg);color:var(--color-warning)}.badge-muted{background-color:var(--color-slate-100);color:var(--color-slate-500)}.progress-bar{height:calc(var(--spacing)*1.5);background-color:var(--color-slate-100);border-radius:3.40282e38px;overflow:hidden}.progress-fill{height:100%;transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.3s;background:linear-gradient(90deg,var(--color-primary-light),var(--color-primary));border-radius:3.40282e38px;transition-duration:.3s}.status-dot{margin-right:calc(var(--spacing)*1.5);height:calc(var(--spacing)*1.5);width:calc(var(--spacing)*1.5);vertical-align:middle;border-radius:3.40282e38px;display:inline-block}.status-dot.running{background-color:var(--color-primary)}.status-dot.success{background-color:var(--color-success)}.status-dot.failed{background-color:var(--color-danger)}.status-dot.pending{background-color:var(--color-warning)}.status-dot.paused{background-color:var(--color-slate-300)}.activity-item{gap:calc(var(--spacing)*2);border-bottom-style:var(--tw-border-style);border-bottom-width:1px;border-color:var(--color-line-light);padding-block:calc(var(--spacing)*1.5);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-leading:1.5;line-height:1.5;display:flex}.activity-item:last-child{border-bottom-style:var(--tw-border-style);border-bottom-width:0}.activity-time{min-width:44px;font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));white-space:nowrap;color:var(--color-muted);font-family:ui-monospace,monospace}.activity-badge{font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);white-space:nowrap}.activity-badge.ok{color:var(--color-success)}.activity-badge.warn{color:var(--color-warning)}.activity-badge.err{color:var(--color-danger)}.view{display:none}.view.active{gap:18px;display:grid}.login-page{background-color:var(--color-bg);width:100%;min-height:100vh;padding-inline:calc(var(--spacing)*6);padding-block:calc(var(--spacing)*8);flex-direction:column;flex:1;justify-content:center;align-items:center;display:flex;overflow-x:hidden}@media not all and (min-width:40rem){.login-page{padding-inline:calc(var(--spacing)*4);padding-top:calc(var(--spacing)*14);padding-bottom:calc(var(--spacing)*8);justify-content:flex-start}}.login-page{min-height:100svh}.login-card{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);width:100%;max-width:420px;padding:calc(var(--spacing)*8);--tw-shadow:0 10px 15px -3px var(--tw-shadow-color,#0000001a),0 4px 6px -4px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow);border-radius:16px}@media not all and (min-width:40rem){.login-card{padding:calc(var(--spacing)*6);border-radius:14px}}.login-card{animation:.5s .1s both fadeIn}.login-brand{margin-bottom:calc(var(--spacing)*5);text-align:center;width:100%;max-width:420px}@media not all and (min-width:40rem){.login-brand{margin-bottom:calc(var(--spacing)*4)}}.login-brand{animation:.5s both fadeIn}.login-brand-mark{margin-bottom:calc(var(--spacing)*3);height:calc(var(--spacing)*12);width:calc(var(--spacing)*12);border-radius:var(--radius-xl);--tw-font-weight:var(--font-weight-bold);font-size:22px;font-weight:var(--font-weight-bold);color:var(--color-white);background:linear-gradient(135deg,var(--color-primary),var(--color-primary-light));font-family:var(--font-heading);justify-content:center;align-items:center;display:inline-flex}.login-brand h1{font-size:var(--text-xl);line-height:var(--tw-leading,var(--text-xl--line-height));--tw-font-weight:var(--font-weight-extrabold);font-weight:var(--font-weight-extrabold);color:var(--color-text);font-family:var(--font-heading)}.login-brand p{margin-top:calc(var(--spacing)*1);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-muted)}@media not all and (min-width:40rem){.login-brand p{padding-inline:calc(var(--spacing)*2);--tw-leading:calc(var(--spacing)*5);line-height:calc(var(--spacing)*5)}}.login-overlay{inset:calc(var(--spacing)*0);z-index:1000;background-color:var(--color-bg);width:100%;min-height:100svh;position:fixed}.login-error{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-red-300);background-color:var(--color-danger-bg);padding-inline:calc(var(--spacing)*3.5);padding-block:calc(var(--spacing)*2.5);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-danger);border-radius:8px;margin-bottom:18px;display:none}.login-error.visible{animation:.4s shake;display:block}@keyframes fadeIn{0%{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}@keyframes shake{0%,to{transform:translate(0)}20%,60%{transform:translate(-6px)}40%,80%{transform:translate(6px)}}.login-field{margin-bottom:calc(var(--spacing)*5)}.login-field label{margin-bottom:calc(var(--spacing)*2);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));--tw-font-weight:var(--font-weight-medium);font-weight:var(--font-weight-medium);color:var(--color-text);display:block}.login-field input{height:calc(var(--spacing)*12);border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);width:100%;padding-inline:calc(var(--spacing)*3.5);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-text);transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;--tw-outline-style:none;border-radius:8px;outline-style:none;font-family:inherit;transition-duration:.15s}.login-field input:focus{border-color:var(--color-primary);box-shadow:0 0 0 3px #2563eb1f}.login-options{margin-bottom:calc(var(--spacing)*6);justify-content:space-between;align-items:center;display:flex}.login-checkbox{cursor:pointer;align-items:center;gap:calc(var(--spacing)*2);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-muted);-webkit-user-select:none;user-select:none;display:flex}.login-submit{height:calc(var(--spacing)*12);cursor:pointer;justify-content:center;align-items:center;gap:calc(var(--spacing)*2);border-style:var(--tw-border-style);background-color:var(--color-primary);width:100%;font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-white);transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;border-width:0;border-radius:8px;font-family:inherit;transition-duration:.15s;display:flex}.login-submit:hover{background-color:var(--color-primary-dark)}.login-submit:disabled{cursor:not-allowed;opacity:.7}.login-submit:disabled:hover{background-color:var(--color-primary)}.spinner{width:18px;height:18px;animation:var(--animate-spin);border-style:var(--tw-border-style);border-width:2px;border-color:#ffffff4d;border-radius:3.40282e38px;flex-shrink:0}@supports (color:color-mix(in lab, red, red)){.spinner{border-color:color-mix(in oklab,var(--color-white)30%,transparent)}}.spinner{border-top-color:var(--color-white)}.watch-overlay{pointer-events:none;inset:calc(var(--spacing)*0);z-index:999;background-color:#00000059;justify-content:center;align-items:center;display:flex;position:fixed}@supports (color:color-mix(in lab, red, red)){.watch-overlay{background-color:color-mix(in oklab,var(--color-black)35%,transparent)}}.watch-overlay{opacity:0;transition-property:opacity;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.2s;transition-duration:.2s}.watch-overlay.open{pointer-events:auto;opacity:1}.watch-dialog{gap:calc(var(--spacing)*4);background-color:var(--color-surface);width:440px;max-width:calc(100vw - 32px);padding:calc(var(--spacing)*6);--tw-shadow:0 10px 15px -3px var(--tw-shadow-color,#0000001a),0 4px 6px -4px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow);border-radius:10px;display:grid}.watch-history-dialog{grid-template-rows:auto minmax(0,1fr) auto;width:900px;max-height:82vh}.watch-history-header{justify-content:space-between;align-items:center;gap:calc(var(--spacing)*3);display:flex}.watch-history-body{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);border-radius:8px;overflow:auto}.watch-history-pagination{justify-content:space-between;align-items:center;gap:calc(var(--spacing)*3);flex-wrap:wrap;display:flex}.watch-history-table{min-width:720px}.watch-row{cursor:pointer}.watch-row:hover{background:var(--color-surface-hover)}.watch-events-row{display:none}.watch-events-row.open{display:table-row}.watch-events-row td{background:var(--color-surface-alt);padding:0}.watch-events-panel{max-height:300px;padding:12px 16px;font-size:15px;overflow-y:auto}.watch-event-item{border-bottom:1px solid var(--color-line);align-items:flex-start;gap:8px;padding:4px 0;font-size:13px;display:flex}.watch-event-item:last-child{border-bottom:0}.watch-event-time{color:var(--color-muted);white-space:nowrap;min-width:90px}.watch-event-badge{flex-shrink:0}.watch-event-info{word-break:break-all;flex:1}.watch-events-load-more{cursor:pointer;margin:8px auto 0;font-size:13px;display:block}@media (max-width:1200px){.stat-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media (max-width:960px){.sidebar{display:none}.main-content{padding:calc(var(--spacing)*4)}}.mob-body{font-family:var(--font-mob);-webkit-tap-highlight-color:transparent;-webkit-user-select:none;user-select:none;width:100%;min-height:100svh;padding-top:var(--topbar-height);padding-bottom:calc(var(--tab-height) + var(--safe-bottom));background:var(--color-bg);color:var(--color-text);font-size:15px;line-height:1.5;display:block;overflow-x:hidden}.mob-body label{width:100%;min-width:0;color:var(--color-text-secondary);gap:6px;font-size:14px;font-weight:500;display:grid}.mob-body form{flex-direction:column;gap:10px;width:100%;min-width:0;display:flex}.mob-body input,.mob-body select,.mob-body textarea{border:1px solid var(--color-line);background:var(--color-surface);width:100%;min-width:0;color:var(--color-text);box-sizing:border-box;border-radius:8px;min-height:44px;padding:12px 14px;font-family:inherit;font-size:16px;transition:border-color .18s,box-shadow .18s}.mob-body input:focus,.mob-body select:focus,.mob-body textarea:focus{border-color:var(--color-primary);outline:none;box-shadow:0 0 0 3px #2563eb1f}.mob-body input[type=checkbox],.mob-body input[type=radio]{width:auto;min-width:auto;min-height:auto;accent-color:var(--color-primary);padding:0}.mob-body label:has(input[type=checkbox]),.mob-body label:has(input[type=radio]){flex-direction:row;align-items:center;gap:8px;display:flex}.mob-btn{background:var(--color-primary);color:#fff;cursor:pointer;border:0;border-radius:8px;justify-content:center;align-items:center;gap:6px;min-width:44px;min-height:44px;padding:0 16px;font-family:inherit;font-size:15px;font-weight:600;transition:opacity .15s,background .15s;display:inline-flex}.mob-btn:active{opacity:.78}.mob-btn-muted{background:var(--color-surface);color:var(--color-text);border:1px solid var(--color-line)}.mob-btn-muted:active{background:var(--color-surface-muted)}.mob-btn-danger{color:var(--color-danger);border:1px solid var(--color-danger);background:0 0}.mob-btn-danger:active{background:var(--color-danger-bg)}.mob-btn-sm{min-width:auto;min-height:36px;padding:0 12px;font-size:14px}.mob-btn svg{flex-shrink:0;width:18px;height:18px}.mob-topbar{height:var(--topbar-height);background:var(--color-surface);border-bottom:1px solid var(--color-line);z-index:100;align-items:center;gap:6px;padding:0 14px;display:flex;position:fixed;top:0;left:0;right:0}.mob-topbar__back{width:44px;height:44px;color:var(--color-primary);cursor:pointer;background:0 0;border:0;border-radius:8px;flex-shrink:0;justify-content:center;align-items:center;min-width:44px;min-height:44px;padding:0;font-family:inherit;font-size:20px;line-height:1;display:none}.mob-topbar__back:active{background:var(--color-primary-soft)}.mob-topbar__title{font-size:17px;font-weight:700;font-family:var(--font-heading);color:var(--color-text)}.mob-topbar.sub .mob-topbar__back{display:flex}.mob-tabbar{background:var(--color-surface);border-top:1px solid var(--color-line);z-index:100;height:calc(var(--tab-height) + var(--safe-bottom));padding-top:6px;padding-bottom:var(--safe-bottom);justify-content:space-around;align-items:flex-start;display:flex;position:fixed;bottom:0;left:0;right:0}.mob-tab{color:var(--color-muted);cursor:pointer;background:0 0;border:0;border-radius:0;flex-direction:column;align-items:center;gap:2px;min-width:44px;min-height:auto;padding:4px 0;font-family:inherit;font-size:11px;font-weight:500;transition:color .15s;display:flex}.mob-tab.active{color:var(--color-primary);font-weight:600}.mob-tab svg{flex-shrink:0;width:24px;height:24px}.mob-content{box-sizing:border-box;flex-direction:column;gap:10px;width:100%;min-width:0;max-width:100%;padding:12px;animation:.25s both mobRise;display:flex}@keyframes mobRise{0%{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}.mob-view{display:none}.mob-view.active{flex-direction:column;gap:10px;width:100%;min-width:0;display:flex}.mob-view.active>*{min-width:0}.mob-subpage{flex-direction:column;gap:10px;width:100%;min-width:0;display:none}.mob-subpage.active{display:flex}.mob-subpage.active>*{min-width:0}.mob-card{background:var(--color-surface);border:1px solid var(--color-line);border-left:3px solid var(--color-line);box-sizing:border-box;cursor:pointer;border-radius:10px;width:100%;max-width:100%;padding:14px;transition:all .15s;box-shadow:0 1px 3px #0000000a}.mob-card:active{transform:scale(.985)}.mob-card.status-pending{border-left-color:#94a3b8}.mob-card.status-running{border-left-color:var(--color-primary)}.mob-card.status-paused{border-left-color:var(--color-warning)}.mob-card.status-success,.mob-card.status-completed{border-left-color:var(--color-success)}.mob-card.status-failure{border-left-color:var(--color-danger)}.mob-card.status-cancelled{border-left-color:#94a3b8}.mob-card.status-skipped{border-left-color:#8b5cf6}.mob-card__head{justify-content:space-between;align-items:flex-start;margin-bottom:6px;display:flex}.mob-card__title{word-break:break-all;flex:1;min-width:0;font-size:15px;font-weight:650;line-height:1.35}.mob-card__badge{white-space:nowrap;border-radius:4px;flex-shrink:0;padding:2px 8px;font-size:12px;font-weight:600;display:inline-block}.mob-card__badge.pending{color:var(--color-text-secondary);background:#f1f5f9}.mob-card__badge.running{background:var(--color-success-bg);color:var(--color-success)}.mob-card__badge.paused{background:var(--color-warning-bg);color:var(--color-warning)}.mob-card__badge.completed{background:var(--color-primary-soft);color:var(--color-primary)}.mob-card__badge.failure{background:var(--color-danger-bg);color:var(--color-danger)}.mob-card__badge.cancelled{color:#94a3b8;background:#f1f5f9}.mob-card__row{justify-content:space-between;align-items:flex-start;gap:10px;padding:2px 0;font-size:13px;display:flex}.mob-card__row .label{color:var(--color-muted)}.mob-card__row span:last-child{text-align:right;overflow-wrap:anywhere;min-width:0}.mob-card__progress{background:var(--color-surface-muted);border-radius:3px;height:6px;margin:6px 0;overflow:hidden}.mob-card__progress-fill{background:var(--color-primary);border-radius:3px;height:100%;transition:width .3s}.mob-card__actions{flex-wrap:wrap;gap:6px;margin-top:8px;display:flex}.mob-watch-events{border-top:1px solid var(--color-line);margin-top:8px;padding-top:8px;font-size:12px}.mob-watch-events .watch-event-item{border-bottom:1px solid var(--color-line);align-items:flex-start;gap:6px;padding:3px 0;display:flex}.mob-watch-events .watch-event-item:last-child{border-bottom:0}.mob-collapse{border:1px solid var(--color-line);background:var(--color-surface);box-sizing:border-box;border-radius:10px;width:100%;min-width:0;max-width:100%;overflow:hidden}.mob-collapse__head{cursor:pointer;-webkit-user-select:none;user-select:none;color:var(--color-text);justify-content:space-between;align-items:center;min-width:0;padding:14px;font-size:15px;font-weight:600;display:flex}.mob-collapse__head:active{background:var(--color-surface-muted)}.mob-collapse__arrow{color:var(--color-muted);flex-shrink:0;font-size:12px;transition:transform .2s}.mob-collapse.open .mob-collapse__arrow{transform:rotate(180deg)}.mob-collapse__body{flex-direction:column;gap:10px;min-width:0;padding:0 14px 14px;display:none}.mob-collapse.open .mob-collapse__body{display:flex}.mob-collapse__body>*{width:100%;min-width:0}.mob-collapse__body>.mob-btn,.mob-collapse__body>.mob-empty{width:100%}.mob-menu-group{background:var(--color-surface);border:1px solid var(--color-line);box-sizing:border-box;border-radius:10px;flex-direction:column;width:100%;max-width:100%;display:flex;overflow:hidden}.mob-menu-group+.mob-menu-group{margin-top:10px}.mob-menu-label{color:var(--color-muted);text-transform:uppercase;letter-spacing:.06em;padding:10px 14px 4px;font-size:12px;font-weight:600}.mob-menu-item{color:var(--color-text);cursor:pointer;text-align:left;border:0;border-bottom:1px solid var(--color-line-light);background:0 0;border-radius:0;align-items:center;gap:10px;width:100%;min-height:44px;padding:14px;font-family:inherit;font-size:15px;font-weight:400;transition:background .15s;display:flex}.mob-menu-item:last-child{border-bottom:0}.mob-menu-item:active{background:var(--color-surface-hover)}.mob-menu-item svg{width:22px;height:22px;color:var(--color-primary);flex-shrink:0}.mob-menu-item__arrow{color:var(--color-muted);margin-left:auto;font-size:14px}.mob-menu-item__label{flex:1}.mob-menu-item--danger,.mob-menu-item--danger svg{color:var(--color-danger)}.mob-sheet-overlay{z-index:300;background:#00000059;align-items:flex-end;display:none;position:fixed;inset:0}.mob-sheet-overlay.open{display:flex}.mob-sheet{background:var(--color-surface);width:100%;padding:20px 16px max(24px,var(--safe-bottom));border-radius:16px 16px 0 0;flex-direction:column;gap:14px;max-height:85vh;animation:.25s mobSlideUp;display:flex;overflow-y:auto}@keyframes mobSlideUp{0%{transform:translateY(100%)}to{transform:translateY(0)}}.mob-sheet__title{font-size:15px;font-weight:700;font-family:var(--font-heading);margin:0}.mob-toast{left:50%;bottom:calc(var(--tab-height) + var(--safe-bottom) + 16px);background:var(--color-text);color:#fff;z-index:400;opacity:0;pointer-events:none;white-space:nowrap;border-radius:8px;padding:10px 20px;font-size:13px;transition:opacity .25s;position:fixed;transform:translate(-50%)}.mob-toast.show{opacity:1;pointer-events:auto}.mob-sheet__task-header{background:var(--color-surface-muted);border-radius:8px;padding:12px}.mob-sheet__task-header .task-title{word-break:break-all;margin-bottom:4px;font-size:15px;font-weight:650}.mob-sheet__task-header .task-meta{color:var(--color-muted);margin-bottom:6px;font-size:12px}.mob-sheet-tabs{gap:6px;padding-bottom:2px;display:flex;overflow-x:auto}.mob-sheet-tab{border:1px solid var(--color-line);background:var(--color-surface);color:var(--color-muted);cursor:pointer;white-space:nowrap;border-radius:6px;min-width:auto;min-height:36px;padding:8px 12px;font-family:inherit;font-size:12px;font-weight:600;transition:all .15s}.mob-sheet-tab.active{background:var(--color-primary);color:#fff;border-color:var(--color-primary)}.mob-sheet-tab .count{opacity:.8;margin-left:3px}.mob-item-row{border-bottom:1px solid var(--color-line);justify-content:space-between;align-items:center;gap:6px;padding:8px 0;font-size:13px;display:flex}.mob-item-row:last-child{border-bottom:0}.mob-item-row__name{text-overflow:ellipsis;white-space:nowrap;word-break:break-all;flex:1;min-width:0;overflow:hidden}.mob-item-row__progress{color:var(--color-muted);text-overflow:ellipsis;white-space:nowrap;margin-top:2px;font-size:12px;font-weight:500;display:block;overflow:hidden}.mob-event-row{border-bottom:1px solid var(--color-line);padding:6px 0;font-size:12px}.mob-event-row:last-child{border-bottom:0}.mob-event-row time{color:var(--color-muted);margin-right:6px}.mob-sheet-pagination{color:var(--color-muted);justify-content:space-between;align-items:center;padding-top:6px;font-size:12px;display:flex}.mob-empty{text-align:center;color:var(--color-muted);padding:32px 16px;font-size:13px;line-height:1.6}.mob-section-title{text-transform:uppercase;letter-spacing:.06em;color:var(--color-muted);padding:4px 0;font-size:12px;font-weight:600}.mob-media-scan-btn{width:100%;margin:8px 0}.mob-media-result{margin-top:12px;font-size:13px}.mob-subpage .mob-collapse__body label,.mob-subpage .mob-collapse__body [style*=display\:grid],.mob-body [style*=display\:grid],.mob-body [style*="display: grid"]{width:100%;min-width:0}.mob-body [style*="grid-template-columns:1fr 1fr"],.mob-body [style*="grid-template-columns: 1fr 1fr"]{grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important}#mob-tasks-list,#mob-watches-list,#mob-operations-list,#mob-statistics-list,#mob-records-list,#mob-media-result,#mob-profile-menu{width:100%;min-width:0;max-width:100%}.mob-check-group{border:1px solid var(--color-line);box-sizing:border-box;border-radius:8px;width:100%;min-width:0;margin:0;padding:10px 14px}.mob-check-group legend{color:var(--color-muted);padding:0 4px;font-size:13px}.mob-table-wrap{border:1px solid var(--color-line);-webkit-overflow-scrolling:touch;border-radius:8px;overflow-x:auto}.mob-table-wrap table{border-collapse:collapse;width:100%;font-size:13px}.mob-table-wrap th,.mob-table-wrap td{text-align:left;border-bottom:1px solid var(--color-line);white-space:nowrap;padding:8px 10px}.mob-table-wrap th{background:var(--color-surface-muted);font-weight:600;position:sticky;top:0}.mob-login-overlay{background:var(--color-bg);z-index:1000;padding:48px 16px;padding-bottom:max(32px,calc(24px + var(--safe-bottom)));flex-direction:column;justify-content:flex-start;align-items:center;gap:16px;display:none;position:fixed;inset:0;overflow-y:auto}.mob-login-overlay.active{display:flex}.mob-login-brand{text-align:center;width:100%;max-width:400px}.mob-login-brand-mark{background:linear-gradient(135deg,var(--color-primary),var(--color-primary-light));color:#fff;width:48px;height:48px;font-size:22px;font-weight:700;font-family:var(--font-heading);border-radius:12px;justify-content:center;align-items:center;margin-bottom:12px;display:inline-flex}.mob-login-brand h1{color:var(--color-text);font-size:22px;font-weight:800;font-family:var(--font-heading);letter-spacing:-.02em;margin:0}.mob-login-brand p{color:var(--color-muted);margin:4px 0 0;font-size:13px}.mob-login-card{background:var(--color-surface);border:1px solid var(--color-line);border-radius:14px;width:100%;max-width:400px;padding:20px;box-shadow:0 1px 3px #0000000a}.mob-login-card__step{color:var(--color-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px;font-size:12px}.mob-login-card__title{color:var(--color-text);font-size:20px;font-weight:700;font-family:var(--font-heading);margin:0 0 6px}.mob-login-card__subtitle{color:var(--color-muted);margin:0 0 20px;font-size:14px;line-height:1.5}.mob-login-field{margin-bottom:16px}.mob-login-field label{color:var(--color-text);margin-bottom:6px;font-size:13px;font-weight:500;display:block}.mob-login-field input{border:1px solid var(--color-line);background:var(--color-surface);width:100%;height:48px;color:var(--color-text);border-radius:8px;padding:0 14px;font-family:inherit;font-size:15px;transition:border-color .18s}.mob-login-field input:focus{border-color:var(--color-primary);outline:none;box-shadow:0 0 0 3px #2563eb1f}.mob-login-field__hint{color:var(--color-muted);margin-top:4px;font-size:12px}.mob-login-error{color:var(--color-danger);background:var(--color-danger-bg);border:1px solid #ef44444d;border-radius:8px;margin-bottom:16px;padding:10px 14px;font-size:13px;display:none}.mob-login-error.visible{display:block}.mob-login-actions{grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;display:grid}.mob-login-actions button{width:100%;min-width:0}.mob-login-submit{justify-content:center;align-items:center;gap:6px;display:inline-flex}.mob-login-submit svg{flex-shrink:0;width:18px;height:18px}.mob-login-success{text-align:center;padding:16px 0}.mob-login-success svg{width:48px;height:48px;color:var(--color-success);margin-bottom:12px}.mob-login-success__text{color:var(--color-success);margin:0;font-size:15px;font-weight:600}@media (min-width:640px){.mob-login-overlay{justify-content:center;padding-top:24px}.mob-login-card{padding:24px}}}@layer utilities{.collapse{visibility:collapse}.invisible{visibility:hidden}.visible{visibility:visible}.sr-only{clip-path:inset(50%);white-space:nowrap;border-width:0;width:1px;height:1px;margin:-1px;padding:0;position:absolute;overflow:hidden}.absolute{position:absolute}.fixed{position:fixed}.relative{position:relative}.static{position:static}.sticky{position:sticky}.bottom-0{bottom:calc(var(--spacing)*0)}.container{width:100%}@media (min-width:40rem){.container{max-width:40rem}}@media (min-width:48rem){.container{max-width:48rem}}@media (min-width:64rem){.container{max-width:64rem}}@media (min-width:80rem){.container{max-width:80rem}}@media (min-width:96rem){.container{max-width:96rem}}.m-0{margin:calc(var(--spacing)*0)}.mx-auto{margin-inline:auto}.mt-1{margin-top:calc(var(--spacing)*1)}.mt-2{margin-top:calc(var(--spacing)*2)}.mt-3{margin-top:calc(var(--spacing)*3)}.mt-4{margin-top:calc(var(--spacing)*4)}.mt-\[18px\]{margin-top:18px}.mb-1{margin-bottom:calc(var(--spacing)*1)}.mb-1\.5{margin-bottom:calc(var(--spacing)*1.5)}.mb-2{margin-bottom:calc(var(--spacing)*2)}.mb-3{margin-bottom:calc(var(--spacing)*3)}.mb-4{margin-bottom:calc(var(--spacing)*4)}.mb-5{margin-bottom:calc(var(--spacing)*5)}.mb-7{margin-bottom:calc(var(--spacing)*7)}.mb-\[14px\]{margin-bottom:14px}.ml-1{margin-left:calc(var(--spacing)*1)}.block{display:block}.contents{display:contents}.flex{display:flex}.grid{display:grid}.hidden{display:none}.inline{display:inline}.inline-flex{display:inline-flex}.table{display:table}.\!h-\[34px\]{height:34px!important}.h-4{height:calc(var(--spacing)*4)}.h-9{height:calc(var(--spacing)*9)}.max-h-\[300px\]{max-height:300px}.min-h-20{min-height:calc(var(--spacing)*20)}.min-h-screen{min-height:100vh}.\!w-\[34px\]{width:34px!important}.\!w-auto{width:auto!important}.w-4{width:calc(var(--spacing)*4)}.w-10{width:calc(var(--spacing)*10)}.w-20{width:calc(var(--spacing)*20)}.w-24{width:calc(var(--spacing)*24)}.w-40{width:calc(var(--spacing)*40)}.w-\[60px\]{width:60px}.w-\[80px\]{width:80px}.w-\[90px\]{width:90px}.w-\[160px\]{width:160px}.w-\[180px\]{width:180px}.w-full{width:100%}.max-w-\[160px\]{max-width:160px}.max-w-\[180px\]{max-width:180px}.max-w-\[200px\]{max-width:200px}.max-w-\[220px\]{max-width:220px}.max-w-\[240px\]{max-width:240px}.max-w-\[260px\]{max-width:260px}.max-w-\[900px\]{max-width:900px}.min-w-\[60px\]{min-width:60px}.min-w-\[600px\]{min-width:600px}.flex-1{flex:1}.flex-shrink{flex-shrink:1}.shrink-0{flex-shrink:0}.border-collapse{border-collapse:collapse}.transform{transform:var(--tw-rotate-x,)var(--tw-rotate-y,)var(--tw-rotate-z,)var(--tw-skew-x,)var(--tw-skew-y,)}.cursor-pointer{cursor:pointer}.resize{resize:both}.grid-cols-1{grid-template-columns:repeat(1,minmax(0,1fr))}.grid-cols-2{grid-template-columns:repeat(2,minmax(0,1fr))}.grid-cols-\[380px_1fr\]{grid-template-columns:380px 1fr}.flex-wrap{flex-wrap:wrap}.items-center{align-items:center}.justify-between{justify-content:space-between}.justify-center{justify-content:center}.justify-end{justify-content:flex-end}.gap-1{gap:calc(var(--spacing)*1)}.gap-2{gap:calc(var(--spacing)*2)}.gap-2\.5{gap:calc(var(--spacing)*2.5)}.gap-3{gap:calc(var(--spacing)*3)}.gap-4{gap:calc(var(--spacing)*4)}.gap-5{gap:calc(var(--spacing)*5)}.gap-x-2{column-gap:calc(var(--spacing)*2)}.gap-x-2\.5{column-gap:calc(var(--spacing)*2.5)}.gap-y-0{row-gap:calc(var(--spacing)*0)}.gap-y-1{row-gap:calc(var(--spacing)*1)}.overflow-auto{overflow:auto}.overflow-hidden{overflow:hidden}.overflow-x-auto{overflow-x:auto}.rounded{border-radius:.25rem}.rounded-lg{border-radius:var(--radius-lg)}.rounded-md{border-radius:var(--radius-md)}.border{border-style:var(--tw-border-style);border-width:1px}.border-t{border-top-style:var(--tw-border-style);border-top-width:1px}.border-line{border-color:var(--color-line)}.bg-bg{background-color:var(--color-bg)}.bg-danger-bg{background-color:var(--color-danger-bg)}.bg-surface-alt{background-color:var(--color-surface-alt)}.bg-white{background-color:var(--color-white)}.p-4{padding:calc(var(--spacing)*4)}.p-6{padding:calc(var(--spacing)*6)}.p-8{padding:calc(var(--spacing)*8)}.p-\[10px_14px\]{padding:10px 14px}.px-0{padding-inline:calc(var(--spacing)*0)}.px-6{padding-inline:calc(var(--spacing)*6)}.px-\[3px\]{padding-inline:3px}.px-\[18px\]{padding-inline:18px}.py-0{padding-block:calc(var(--spacing)*0)}.py-0\.5{padding-block:calc(var(--spacing)*.5)}.py-1{padding-block:calc(var(--spacing)*1)}.py-2{padding-block:calc(var(--spacing)*2)}.py-3{padding-block:calc(var(--spacing)*3)}.py-4{padding-block:calc(var(--spacing)*4)}.pt-3{padding-top:calc(var(--spacing)*3)}.pb-\[14px\]{padding-bottom:14px}.text-center{text-align:center}.text-right{text-align:right}.font-\[family-name\:var\(--font-body\)\]{font-family:var(--font-body)}.font-\[family-name\:var\(--font-heading\)\]{font-family:var(--font-heading)}.font-mono{font-family:var(--font-mono)}.text-base{font-size:var(--text-base);line-height:var(--tw-leading,var(--text-base--line-height))}.text-sm{font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height))}.text-xl{font-size:var(--text-xl);line-height:var(--tw-leading,var(--text-xl--line-height))}.text-xs{font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height))}.text-\[11px\]{font-size:11px}.text-\[14px\]{font-size:14px}.leading-\[1\.5\]{--tw-leading:1.5;line-height:1.5}.leading-tight{--tw-leading:var(--leading-tight);line-height:var(--leading-tight)}.font-\[650\]{--tw-font-weight:650;font-weight:650}.font-bold{--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold)}.font-medium{--tw-font-weight:var(--font-weight-medium);font-weight:var(--font-weight-medium)}.font-semibold{--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold)}.tracking-\[0\.06em\]{--tw-tracking:.06em;letter-spacing:.06em}.text-ellipsis{text-overflow:ellipsis}.whitespace-nowrap{white-space:nowrap}.text-danger{color:var(--color-danger)}.text-muted{color:var(--color-muted)}.text-primary{color:var(--color-primary)}.text-success{color:var(--color-success)}.text-text{color:var(--color-text)}.uppercase{text-transform:uppercase}.overline{text-decoration-line:overline}.underline{text-decoration-line:underline}.accent-primary{accent-color:var(--color-primary)}.opacity-70{opacity:.7}.shadow{--tw-shadow:0 1px 3px 0 var(--tw-shadow-color,#0000001a),0 1px 2px -1px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow)}.outline{outline-style:var(--tw-outline-style);outline-width:1px}.grayscale{--tw-grayscale:grayscale(100%);filter:var(--tw-blur,)var(--tw-brightness,)var(--tw-contrast,)var(--tw-grayscale,)var(--tw-hue-rotate,)var(--tw-invert,)var(--tw-saturate,)var(--tw-sepia,)var(--tw-drop-shadow,)}.invert{--tw-invert:invert(100%);filter:var(--tw-blur,)var(--tw-brightness,)var(--tw-contrast,)var(--tw-grayscale,)var(--tw-hue-rotate,)var(--tw-invert,)var(--tw-saturate,)var(--tw-sepia,)var(--tw-drop-shadow,)}.filter{filter:var(--tw-blur,)var(--tw-brightness,)var(--tw-contrast,)var(--tw-grayscale,)var(--tw-hue-rotate,)var(--tw-invert,)var(--tw-saturate,)var(--tw-sepia,)var(--tw-drop-shadow,)}.backdrop-filter{-webkit-backdrop-filter:var(--tw-backdrop-blur,)var(--tw-backdrop-brightness,)var(--tw-backdrop-contrast,)var(--tw-backdrop-grayscale,)var(--tw-backdrop-hue-rotate,)var(--tw-backdrop-invert,)var(--tw-backdrop-opacity,)var(--tw-backdrop-saturate,)var(--tw-backdrop-sepia,);backdrop-filter:var(--tw-backdrop-blur,)var(--tw-backdrop-brightness,)var(--tw-backdrop-contrast,)var(--tw-backdrop-grayscale,)var(--tw-backdrop-hue-rotate,)var(--tw-backdrop-invert,)var(--tw-backdrop-opacity,)var(--tw-backdrop-saturate,)var(--tw-backdrop-sepia,)}.transition{transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to,opacity,box-shadow,transform,translate,scale,rotate,filter,-webkit-backdrop-filter,backdrop-filter,display,content-visibility,overlay,pointer-events;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration))}.select-all{-webkit-user-select:all;user-select:all}@media (min-width:64rem){.lg\:grid-cols-2{grid-template-columns:repeat(2,minmax(0,1fr))}}.scrollbar-thin{scrollbar-width:thin;scrollbar-color:var(--color-line)transparent}}@property --tw-rotate-x{syntax:"*";inherits:false}@property --tw-rotate-y{syntax:"*";inherits:false}@property --tw-rotate-z{syntax:"*";inherits:false}@property --tw-skew-x{syntax:"*";inherits:false}@property --tw-skew-y{syntax:"*";inherits:false}@property --tw-border-style{syntax:"*";inherits:false;initial-value:solid}@property --tw-leading{syntax:"*";inherits:false}@property --tw-font-weight{syntax:"*";inherits:false}@property --tw-tracking{syntax:"*";inherits:false}@property --tw-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-shadow-color{syntax:"*";inherits:false}@property --tw-shadow-alpha{syntax:"<percentage>";inherits:false;initial-value:100%}@property --tw-inset-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-inset-shadow-color{syntax:"*";inherits:false}@property --tw-inset-shadow-alpha{syntax:"<percentage>";inherits:false;initial-value:100%}@property --tw-ring-color{syntax:"*";inherits:false}@property --tw-ring-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-inset-ring-color{syntax:"*";inherits:false}@property --tw-inset-ring-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-ring-inset{syntax:"*";inherits:false}@property --tw-ring-offset-width{syntax:"<length>";inherits:false;initial-value:0}@property --tw-ring-offset-color{syntax:"*";inherits:false;initial-value:#fff}@property --tw-ring-offset-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-outline-style{syntax:"*";inherits:false;initial-value:solid}@property --tw-blur{syntax:"*";inherits:false}@property --tw-brightness{syntax:"*";inherits:false}@property --tw-contrast{syntax:"*";inherits:false}@property --tw-grayscale{syntax:"*";inherits:false}@property --tw-hue-rotate{syntax:"*";inherits:false}@property --tw-invert{syntax:"*";inherits:false}@property --tw-opacity{syntax:"*";inherits:false}@property --tw-saturate{syntax:"*";inherits:false}@property --tw-sepia{syntax:"*";inherits:false}@property --tw-drop-shadow{syntax:"*";inherits:false}@property --tw-drop-shadow-color{syntax:"*";inherits:false}@property --tw-drop-shadow-alpha{syntax:"<percentage>";inherits:false;initial-value:100%}@property --tw-drop-shadow-size{syntax:"*";inherits:false}@property --tw-backdrop-blur{syntax:"*";inherits:false}@property --tw-backdrop-brightness{syntax:"*";inherits:false}@property --tw-backdrop-contrast{syntax:"*";inherits:false}@property --tw-backdrop-grayscale{syntax:"*";inherits:false}@property --tw-backdrop-hue-rotate{syntax:"*";inherits:false}@property --tw-backdrop-invert{syntax:"*";inherits:false}@property --tw-backdrop-opacity{syntax:"*";inherits:false}@property --tw-backdrop-saturate{syntax:"*";inherits:false}@property --tw-backdrop-sepia{syntax:"*";inherits:false}@property --tw-duration{syntax:"*";inherits:false}@keyframes spin{to{transform:rotate(360deg)}}</style>
</head>
<body class="mob-body bg-bg text-text">
<!-- ================================================================
     Mobile Body v2 — 4-tab navigation, clean single-page layout
     ================================================================ -->

<!-- Top Bar -->
<div class="mob-topbar" id="mob-topbar">
  <button class="mob-topbar__back" id="mob-topbar-back" aria-label="返回">
    <svg viewBox="0 0 24 24" fill="none" width="20" height="20"><path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
  </button>
  <span class="mob-topbar__title" id="mob-topbar-title">TRMD</span>
</div>

<!-- Login Overlay -->
<div class="mob-login-overlay" id="login-container">
  <div class="mob-login-brand">
    <div class="mob-login-brand-mark" aria-hidden="true">T</div>
    <h1>TRMD</h1>
    <p>Telegram 账号登录</p>
  </div>
  <div class="mob-login-card">
    <div class="mob-login-error" id="login-error"></div>

    <!-- Step 1: Phone -->
    <div id="login-form-phone" class="login-step">
      <div class="mob-login-card__step">步骤 1 / 3</div>
      <h2 class="mob-login-card__title">输入电话号码</h2>
      <p class="mob-login-card__subtitle">请输入您的 Telegram 账号绑定的手机号</p>
      <div class="mob-login-field">
        <label for="login-phone">电话号码</label>
        <input id="login-phone" type="tel" placeholder="+8615000000000" autocomplete="tel">
        <div class="mob-login-field__hint">需以「+地区号」开头，如中国 +86</div>
      </div>
      <div class="mob-login-actions">
        <button type="button" id="login-btn-phone" class="mob-btn mob-login-submit">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          发送验证码
        </button>
      </div>
    </div>

    <!-- Step 2: Code -->
    <div id="login-form-code" class="login-step hidden">
      <div class="mob-login-card__step">步骤 2 / 3</div>
      <h2 class="mob-login-card__title">输入验证码</h2>
      <p class="mob-login-card__subtitle" id="login-code-desc">验证码已发送到您的设备</p>
      <div class="mob-login-field">
        <label for="login-code">验证码</label>
        <input id="login-code" type="text" inputmode="numeric" maxlength="10" placeholder="输入验证码" autocomplete="one-time-code">
      </div>
      <div class="mob-login-actions">
        <button type="button" class="mob-btn mob-btn-muted" id="login-btn-back">返回</button>
        <button type="button" id="login-btn-code" class="mob-btn mob-login-submit">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          验证
        </button>
      </div>
    </div>

    <!-- Step 2.5: 2FA Password -->
    <div id="login-form-password" class="login-step hidden">
      <div class="mob-login-card__step">步骤 2.5 / 3</div>
      <h2 class="mob-login-card__title">两步验证密码</h2>
      <p class="mob-login-card__subtitle" id="login-password-hint">该账号已设置两步验证</p>
      <div class="mob-login-field">
        <label for="login-password">密码</label>
        <input id="login-password" type="password" placeholder="输入两步验证密码" autocomplete="current-password">
        <div class="mob-login-field__hint" id="login-password-hint-text"></div>
      </div>
      <div class="mob-login-actions">
        <button type="button" class="mob-btn mob-btn-muted" id="login-btn-back-pwd">取消</button>
        <button type="button" id="login-btn-password" class="mob-btn mob-login-submit">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          验证
        </button>
      </div>
    </div>

    <!-- Recovery -->
    <div id="login-form-recovery" class="login-step hidden">
      <div class="mob-login-card__step">密码恢复</div>
      <h2 class="mob-login-card__title">输入恢复代码</h2>
      <p class="mob-login-card__subtitle" id="login-recovery-desc">恢复代码已发送</p>
      <div class="mob-login-field">
        <label for="login-recovery">恢复代码</label>
        <input id="login-recovery" type="text" placeholder="输入恢复代码">
      </div>
      <div class="mob-login-actions">
        <button type="button" class="mob-btn mob-btn-muted" id="login-btn-back-recovery">返回</button>
        <button type="button" id="login-btn-recovery" class="mob-btn mob-login-submit">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          提交
        </button>
      </div>
    </div>

    <!-- Signup -->
    <div id="login-form-signup" class="login-step hidden">
      <div class="mob-login-card__step">注册信息</div>
      <h2 class="mob-login-card__title">完善个人信息</h2>
      <p class="mob-login-card__subtitle">首次登录，请输入您的名字</p>
      <div class="mob-login-field">
        <label for="login-first-name">名字</label>
        <input id="login-first-name" type="text" placeholder="名字">
      </div>
      <div class="mob-login-field">
        <label for="login-last-name">姓氏</label>
        <input id="login-last-name" type="text" placeholder="姓氏（可选）">
      </div>
      <div class="mob-login-actions">
        <button type="button" id="login-btn-signup" class="mob-btn mob-login-submit">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          完成注册
        </button>
      </div>
    </div>

    <!-- Done -->
    <div id="login-form-done" class="login-step hidden">
      <div class="mob-login-success">
        <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M8 12l3 3 5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <p class="mob-login-success__text" id="login-user-name">登录成功</p>
      </div>
    </div>
  </div>
</div>

<!-- Content Area -->
<div class="mob-content" id="mob-content">

  <!-- ===== Tab 1: 转存任务 ===== -->
  <div class="mob-view active" id="mob-view-transfers">
    <div class="mob-collapse" id="collapse-transfer-form">
      <div class="mob-collapse__head" data-i18n="new.title">新建转存 <span class="mob-collapse__arrow">&#9660;</span></div>
      <div class="mob-collapse__body">
        <form id="mob-transfer-form">
          <label><span data-i18n="new.source">来源链接</span>
            <input type="text" name="source_link" placeholder="https://t.me/..." required>
          </label>
          <label><span data-i18n="new.target">目标</span>
            <input type="text" name="target_link" value="https://t.me/pikpak_bot" required>
          </label>
          <label><span data-i18n="new.targetProfile">目标配置</span>
            <select name="target_profile">
              <option value="pikpak" data-i18n="profile.pikpak">PikPak 文档转存</option>
              <option value="generic" data-i18n="profile.generic">通用 Telegram 目标</option>
            </select>
          </label>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
            <label><span data-i18n="new.startId">起始 ID</span>
              <input type="number" name="start_id" placeholder="可选">
            </label>
            <label><span data-i18n="new.endId">结束 ID</span>
              <input type="number" name="end_id" placeholder="可选">
            </label>
          </div>
          <label style="display:flex;flex-direction:row;align-items:center;gap:8px;">
            <input type="checkbox" name="include_comment">
            <span data-i18n="new.includeComment">包含评论区</span>
          </label>
          <button type="submit" class="mob-btn" style="width:100%;" data-i18n="new.create">创建任务</button>
          <p class="mob-empty hidden" id="mob-form-notice"></p>
        </form>
      </div>
    </div>
    <div id="mob-tasks-list"></div>
  </div>

  <!-- ===== Tab 2: 实时监听 ===== -->
  <div class="mob-view" id="mob-view-watches">
    <div class="mob-collapse" id="collapse-watch-form">
      <div class="mob-collapse__head" data-i18n="watches.title">实时监听 <span class="mob-collapse__arrow">&#9660;</span></div>
      <div class="mob-collapse__body">
        <form id="mob-watch-form">
          <label><span data-i18n="watches.type">类型</span>
            <select name="type" id="mob-watch-type">
              <option value="download" data-i18n="watches.download">监听下载</option>
              <option value="forward" data-i18n="watches.forward">监听转发</option>
            </select>
          </label>
          <div id="mob-watch-source-group">
            <label id="mob-watch-source-label"><span data-i18n="watches.sources">来源频道</span>
              <textarea name="source_links" rows="3" placeholder="每行一个 https://t.me/... 链接" required></textarea>
              <input type="text" name="source_link" placeholder="https://t.me/source" class="hidden">
            </label>
          </div>
          <div id="mob-watch-target-group" class="hidden">
            <label><span data-i18n="watches.target">目标频道</span>
              <input type="text" name="target_link" placeholder="https://t.me/...">
            </label>
          </div>
          <div id="mob-watch-comment-group" class="hidden">
            <label style="display:flex;flex-direction:row;align-items:center;gap:8px;">
              <input type="checkbox" name="include_comment">
              <span data-i18n="watches.includeComment">包含评论区</span>
            </label>
          </div>
          <button type="submit" class="mob-btn" style="width:100%;" data-i18n="watches.createDownload">新增监听</button>
          <p class="mob-empty hidden" id="mob-watch-notice"></p>
        </form>
      </div>
    </div>
    <div id="mob-watches-list"></div>
  </div>

  <!-- ===== Tab 3: 下载与上传 ===== -->
  <div class="mob-view" id="mob-view-downloads-uploads">

    <!-- 频道下载 -->
    <div class="mob-collapse" id="collapse-channel-form">
      <div class="mob-collapse__head" data-i18n="dl.title">频道下载 <span class="mob-collapse__arrow">&#9660;</span></div>
      <div class="mob-collapse__body">
        <form id="mob-channel-form">
          <label><span data-i18n="dl.link">频道链接</span>
            <input type="text" name="chat_link" placeholder="https://t.me/..." required>
          </label>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
            <label><span data-i18n="dl.startDate">起始时间</span>
              <input type="datetime-local" name="start_date">
            </label>
            <label><span data-i18n="dl.endDate">结束时间</span>
              <input type="datetime-local" name="end_date">
            </label>
          </div>
          <label><span data-i18n="dl.keywords">关键词</span>
            <input type="text" name="keywords" data-i18n-placeholder="dl.keywordsPlaceholder" placeholder="逗号分隔，可留空">
          </label>
          <fieldset class="mob-check-group">
            <legend data-i18n="dl.types">下载类型</legend>
            <div id="mob-channel-download-types" style="display:grid;grid-template-columns:1fr 1fr;gap:2px 10px;"></div>
          </fieldset>
          <label style="display:flex;flex-direction:row;align-items:center;gap:8px;">
            <input type="checkbox" name="include_comment">
            <span data-i18n="dl.includeComment">包含评论区</span>
          </label>
          <button type="submit" class="mob-btn" style="width:100%;" data-i18n="dl.create">创建下载任务</button>
          <p class="mob-empty hidden" id="mob-channel-notice"></p>
        </form>
      </div>
    </div>

    <!-- 本地上传 -->
    <div class="mob-collapse" id="collapse-upload-form">
      <div class="mob-collapse__head" data-i18n="dl.uploadTitle">本地上传 <span class="mob-collapse__arrow">&#9660;</span></div>
      <div class="mob-collapse__body">
        <form id="mob-upload-form">
          <label><span data-i18n="dl.uploadPath">本地路径</span>
            <input type="text" name="path" placeholder="/path/to/file" required>
          </label>
          <label><span data-i18n="dl.uploadTarget">目标频道</span>
            <input type="text" name="target_link" placeholder="https://t.me/..." required>
          </label>
          <label style="display:flex;flex-direction:row;align-items:center;gap:8px;">
            <input type="checkbox" name="recursive">
            <span data-i18n="dl.recursive">递归上传文件夹</span>
          </label>
          <button type="submit" class="mob-btn" style="width:100%;" data-i18n="dl.createUpload">创建上传任务</button>
          <p class="mob-empty hidden" id="mob-upload-notice"></p>
        </form>
      </div>
    </div>

    <!-- 操作历史 -->
    <div class="mob-section-title" data-i18n="dl.history">操作历史</div>
    <div id="mob-operations-list"></div>
  </div>

  <!-- ===== Tab 4: 我的 ===== -->
  <div class="mob-view" id="mob-view-profile">
    <!-- Profile Menu -->
    <div id="mob-profile-menu">
      <div class="mob-menu-group">
        <div class="mob-menu-label" data-i18n="nav.section.monitor">数据</div>
        <button class="mob-menu-item" data-profile-nav="statistics">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 19V9M12 19V5M19 19v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M4 19h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          <span class="mob-menu-item__label" data-i18n="nav.statistics">统计面板</span>
          <span class="mob-menu-item__arrow">›</span>
        </button>
        <button class="mob-menu-item" data-profile-nav="records">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 4h14v16H5z" stroke="currentColor" stroke-width="2"/><path d="M8 8h8M8 12h8M8 16h5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          <span class="mob-menu-item__label" data-i18n="nav.records">下载记录</span>
          <span class="mob-menu-item__arrow">›</span>
        </button>
        <button class="mob-menu-item" data-profile-nav="media">
          <svg viewBox="0 0 24 24" fill="none"><path d="M3 6h18M5 6v13a2 2 0 002 2h10a2 2 0 002-2V6M8 6V4a1 1 0 011-1h6a1 1 0 011 1v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span class="mob-menu-item__label" data-i18n="nav.media">媒体管理</span>
          <span class="mob-menu-item__arrow">›</span>
        </button>
      </div>
      <div class="mob-menu-group">
        <div class="mob-menu-label" data-i18n="nav.section.system">系统</div>
        <button class="mob-menu-item" data-profile-nav="settings">
          <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="3.5" stroke="currentColor" stroke-width="2"/><path d="M19.4 15a1.8 1.8 0 0 0 .36 1.98" stroke="currentColor" stroke-width="1.5"/></svg>
          <span class="mob-menu-item__label" data-i18n="nav.settings">系统设置</span>
          <span class="mob-menu-item__arrow">›</span>
        </button>
        <button class="mob-menu-item" id="mob-btn-language">
          <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z" stroke="currentColor" stroke-width="2"/></svg>
          <span class="mob-menu-item__label">语言 <span id="mob-lang-label">中文</span></span>
          <span class="mob-menu-item__arrow">›</span>
        </button>
      </div>
      <div class="mob-menu-group">
        <button class="mob-menu-item mob-menu-item--danger" id="mob-btn-logout">
          <svg viewBox="0 0 24 24" fill="none"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span class="mob-menu-item__label" data-i18n="nav.logout">退出登录</span>
        </button>
      </div>
    </div>

    <!-- Sub-pages (hidden by default, shown when navigating from profile menu) -->
    <div class="mob-subpage" id="mob-subpage-statistics">
      <div id="mob-statistics-list"></div>
    </div>
    <div class="mob-subpage" id="mob-subpage-records">
      <div class="flex items-center justify-end gap-2 mb-3">
        <button class="mob-btn mob-btn-sm mob-btn-danger" id="mob-records-clear-btn" disabled data-i18n="records.clear">清空记录</button>
      </div>
      <div id="mob-records-list"></div>
      <div id="mob-records-pagination"></div>
    </div>
    <div class="mob-subpage" id="mob-subpage-media">
      <button id="mob-media-scan-btn" class="mob-btn mob-btn-sm" style="width:100%;" data-i18n="media.scan">扫描可清理文件</button>
      <div id="mob-media-result"></div>
    </div>
    <div class="mob-subpage" id="mob-subpage-settings">
      <div class="mob-collapse open" id="collapse-settings-paths">
        <div class="mob-collapse__head" data-i18n="settings.paths">路径与任务 <span class="mob-collapse__arrow">&#9660;</span></div>
        <div class="mob-collapse__body" id="mob-settings-path-fields"></div>
      </div>
      <div class="mob-collapse" id="collapse-settings-behavior">
        <div class="mob-collapse__head" data-i18n="settings.behavior">行为 <span class="mob-collapse__arrow">&#9660;</span></div>
        <div class="mob-collapse__body" id="mob-settings-behavior-fields"></div>
      </div>
      <div class="mob-collapse" id="collapse-settings-archive">
        <div class="mob-collapse__head" data-i18n="settings.pikpakArchive">PikPak 归档 <span class="mob-collapse__arrow">&#9660;</span></div>
        <div class="mob-collapse__body" id="mob-settings-archive-fields"></div>
      </div>
      <div class="mob-collapse" id="collapse-settings-sensitive">
        <div class="mob-collapse__head" data-i18n="settings.sensitive">账号与代理 <span class="mob-collapse__arrow">&#9660;</span></div>
        <div class="mob-collapse__body" id="mob-settings-sensitive-fields"></div>
      </div>
      <div class="mob-collapse" id="collapse-settings-download-types">
        <div class="mob-collapse__head" data-i18n="settings.downloadTypes">下载类型 <span class="mob-collapse__arrow">&#9660;</span></div>
        <div class="mob-collapse__body" id="mob-settings-download-types-fields"></div>
      </div>
      <div class="mob-collapse" id="collapse-settings-forward-types">
        <div class="mob-collapse__head" data-i18n="settings.forwardTypes">转发类型 <span class="mob-collapse__arrow">&#9660;</span></div>
        <div class="mob-collapse__body" id="mob-settings-forward-types-fields"></div>
      </div>
      <div class="mob-collapse" id="collapse-settings-message-filter">
        <div class="mob-collapse__head" data-i18n="settings.messageFilter">消息过滤 <span class="mob-collapse__arrow">&#9660;</span></div>
        <div class="mob-collapse__body" id="mob-settings-message-filter-fields"></div>
      </div>
      <div class="mob-collapse" id="collapse-settings-exports">
        <div class="mob-collapse__head" data-i18n="settings.exports">导出表格 <span class="mob-collapse__arrow">&#9660;</span></div>
        <div class="mob-collapse__body" id="mob-settings-exports-fields"></div>
      </div>
      <button id="mob-save-settings" class="mob-btn" style="width:100%;margin-top:4px;" data-i18n="settings.save">保存设置</button>
      <p class="mob-empty hidden" id="mob-settings-notice"></p>
    </div>
  </div>
</div>

<!-- Bottom Tab Bar -->
<div class="mob-tabbar" id="mob-tabbar">
  <button class="mob-tab active" data-mob-tab="transfers">
    <svg viewBox="0 0 24 24" fill="none"><path d="M7 7h10M7 12h10M7 17h6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
    <span data-i18n="nav.transfers">转存</span>
  </button>
  <button class="mob-tab" data-mob-tab="watches">
    <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/><path d="M4 12s3-6 8-6 8 6 8 6-3 6-8 6-8-6-8-6Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M12 9v3l2 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
    <span data-i18n="nav.watches">监听</span>
  </button>
  <button class="mob-tab" data-mob-tab="downloads-uploads">
    <svg viewBox="0 0 24 24" fill="none"><path d="M8 17l4 4 4-4M12 21V3M4 10l4-4 4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
    <span data-i18n="nav.downloadsUploads">下载上传</span>
  </button>
  <button class="mob-tab" data-mob-tab="profile">
    <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="2"/><path d="M4 20a8 8 0 0116 0" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
    <span data-i18n="nav.profile">我的</span>
  </button>
</div>

<!-- Bottom Sheet Overlay (通用 detail) -->
<div class="mob-sheet-overlay" id="mob-sheet-overlay">
  <div class="mob-sheet" id="mob-sheet"></div>
</div>

<!-- Toast -->
<div class="mob-toast" id="mob-toast"></div>
<script>/* TRMD WebUI - Shared JavaScript (i18n + utilities) */

const i18n = {
  zh: {
    'app.title': 'TRMD · 转存控制台',
    'app.subtitle': '转存控制台',
    'nav.section.main': '主要功能',
    'nav.section.monitor': '监控与数据',
    'nav.section.system': '系统',
    'nav.transfers': '转存任务',
    'nav.watches': '实时监听',
    'nav.downloadsUploads': '下载与上传',
    'nav.statistics': '统计面板',
    'nav.settings': '系统设置',
    'nav.records': '下载记录',
    'nav.media': '媒体管理',
    'nav.profile': '我的',
    'nav.logout': '退出登录',
    'side.failed': '失败项',
    'side.status': '系统运行中',
    'hero.title': '转存控制台',
    'hero.body': '管理 Telegram 内容转存任务 — 实时监控、批量操作、智能过滤',
    'action.refresh': '刷新',
    'new.title': '新建转存',
    'new.source': '来源链接',
    'new.target': '目标',
    'new.targetProfile': '目标配置',
    'profile.pikpak': 'PikPak 文档转存',
    'profile.generic': '通用 Telegram 目标',
    'new.startId': '起始 ID',
    'new.endId': '结束 ID',
    'new.optional': '可选',
    'new.includeComment': '包含评论区',
    'new.hint': '单条消息链接可留空。频道或群链接不填 ID 时会自动探测可访问范围，也可手动指定起止 ID。',
    'new.create': '创建任务',
    'watches.title': '活跃监听',
    'watches.downloadTitle': '监听下载',
    'watches.downloadMeta': '新消息自动下载',
    'watches.forwardTitle': '监听转发',
    'watches.forwardMeta': '新消息自动转发',
    'watches.type': '类型',
    'watches.source': '来源频道',
    'watches.target': '目标频道',
    'watches.sources': '来源频道（每行一个）',
    'watches.includeComment': '包含评论区',
    'watches.createDownload': '新增监听下载',
    'watches.createForward': '新增监听转发',
    'watches.empty': '还没有实时监听。',
    'watches.delete': '移除',
    'watches.edit': '编辑',
    'watches.download': '监听下载',
    'watches.forward': '监听转发',
    'watches.created': '实时监听已创建。',
    'watches.deleted': '实时监听已移除。',
    'watches.updated': '实时监听已更新。',
    'watches.events': '转发记录',
    'watches.todayEvents': '今日记录',
    'watches.allEvents': '完整记录',
    'watches.history': '记录',
    'watches.historyTitle': '监听转发记录',
    'watches.pageInfo': '第 {page} / {pages} 页 · 共 {total} 条',
    'watches.noEvents': '暂无转发记录',
    'watches.eventForwarded': '转发成功',
    'watches.eventSkipped': '已过滤',
    'watches.eventLoading': '加载中…',
    'watches.loadMore': '加载更多',
    'watches.targetRequired': '目标频道为必填项。',
    'watches.sourceRequired': '来源频道为必填项。',
    'action.cancel': '取消',
    'action.save': '保存',
    // merged downloads & uploads page
    'dl.title': '频道下载',
    'dl.meta': '从 Telegram 频道拉取文件',
    'dl.link': '频道链接',
    'dl.startDate': '起始时间',
    'dl.endDate': '结束时间',
    'dl.keywords': '关键词',
    'dl.keywordsPlaceholder': '逗号分隔，可留空',
    'dl.types': '下载类型',
    'dl.includeComment': '包含评论区',
    'dl.create': '创建下载任务',
    'dl.accepted': '频道下载任务已创建。',
    'dl.uploadTitle': '本地上传',
    'dl.uploadMeta': '推送到 Telegram 频道',
    'dl.uploadPath': '本地路径',
    'dl.uploadTarget': '目标频道',
    'dl.recursive': '递归上传文件夹',
    'dl.uploadPlaceholder': '占位区，待后续开发',
    'dl.createUpload': '创建上传任务',
    'dl.uploadAccepted': '上传任务已创建。',
    'dl.history': '操作历史',
    'dl.historyId': 'ID',
    'dl.historyType': '类型',
    'dl.historyDetail': '详情',
    'dl.historyStatus': '状态',
    'dl.historyError': '错误信息',
    'dl.historyTime': '创建时间',
    'dl.historyEmpty': '还没有下载或上传操作记录。',
    'dl.typeDownload': '频道下载',
    'dl.typeUpload': '本地上传',
    'statistics.title': '统计与导出',
    'statistics.table': '表格',
    'statistics.available': '可用',
    'statistics.rows': '行数',
    'statistics.yes': '是',
    'statistics.no': '否',
    'statistics.link': '链接统计表',
    'statistics.count': '计数统计表',
    'statistics.upload': '上传统计表',
    'statistics.exportLink': '导出链接统计表',
    'statistics.exportCount': '导出计数统计表',
    'statistics.exportUpload': '导出上传统计表',
    'statistics.exported': '统计表已导出。',
    'tasks.title': '转存任务列表',
    'tasks.notSynced': '尚未同步',
    'tasks.id': 'ID',
    'tasks.status': '状态',
    'tasks.source': '来源',
    'tasks.target': '目标',
    'tasks.progress': '进度',
    'tasks.actions': '操作',
    'tasks.pause': '暂停',
    'tasks.resume': '继续',
    'tasks.retryFailed': '重试失败',
    'tasks.delete': '删除',
    'tasks.empty': '还没有转存任务。',
    'items.title': '文件进度',
    'items.selectTask': '选择一个任务查看详情',
    'items.empty': '该任务还没有文件记录。',
    'items.tab.running': '进行中',
    'items.tab.success': '已完成',
    'items.tab.skipped': '跳过',
    'items.tab.failure': '失败',
    'items.retryFailed': '重试失败项',
    'items.page.previous': '上一页',
    'items.page.next': '下一页',
    'pagination.pageInfo': '第 {page} / {pages} 页 · 共 {total} 条',
    'events.title': '最近事件',
    'events.empty': '没有事件记录。',
    'events.loadMore': '加载更多',
    'settings.title': '系统设置',
    'settings.safeNote': '敏感字段只显示是否已配置',
    'settings.paths': '路径与任务',
    'settings.saveDirectory': '保存目录',
    'settings.tempDirectory': '临时目录',
    'settings.sessionDirectory': '会话目录',
    'settings.maxDownload': '最大下载任务',
    'settings.maxUpload': '最大上传任务',
    'settings.retryDownload': '下载重试',
    'settings.retryUpload': '上传重试',
    'settings.pikpakMaxFileSize': 'PikPak大小上限(字节)',
    'settings.pikpakArchive': 'PikPak 归档',
    'settings.pikpakArchiveEnable': 'PikPak按来源频道归档',
    'settings.pikpakArchiveRemote': 'PikPak rclone remote',
    'settings.pikpakArchiveSource': 'PikPak入库目录',
    'settings.pikpakArchiveRoot': 'PikPak归档根目录',
    'settings.pikpakArchivePoll': '入库轮询秒数',
    'settings.pikpakArchiveInterval': '轮询间隔秒数',
    'settings.pikpakArchiveWindow': '匹配时间窗口秒数',
    'settings.behavior': '行为',
    'settings.notice': '机器人通知',
    'settings.shutdown': '退出后关机',
    'settings.downloadUpload': '受限转发时下载后上传',
    'settings.uploadDelete': '上传完成删除本地文件',
    'settings.pendingLimit': '下载后上传队列',
    'settings.sensitive': '账号与代理',
    'settings.proxyPassword': '代理密码',
    'settings.secretConfigured': '已配置，如需更换请填写',
    'settings.downloadTypes': '下载类型',
    'settings.downloadTypesHint': '（勾选 = 允许下载，未勾选的类型将被忽略）',
    'settings.forwardTypes': '转发类型',
    'settings.forwardTypesHint': '（勾选 = 允许转发，未勾选的类型将被忽略）',
    'settings.messageFilter': '消息过滤',
    'settings.mediaTypes': '媒体类型',
    'settings.mediaTypesHint': '（勾选 = 允许处理，未勾选的类型将被过滤）',
    'settings.dateRange': '日期范围',
    'settings.keywords': '关键词',
    'settings.enabled': '启用',
    'settings.startDate': '起始日期',
    'settings.endDate': '结束日期',
    'settings.keywordList': '关键词列表（逗号分隔）',
    'settings.keywordPlaceholder': '输入关键词,用逗号分隔',
    'settings.exports': '导出表格',
    'settings.exportLink': '链接统计表',
    'settings.exportCount': '计数统计表',
    'settings.exportUpload': '上传统计表',
    'settings.save': '保存设置',
    'settings.saved': '设置已保存。',
    'records.title': '下载记录',
    'records.chat': '频道 ID',
    'records.message': '消息 ID',
    'records.file': '文件',
    'records.size': '大小',
    'records.updated': '更新时间',
    'records.empty': '还没有下载成功记录。',
    'records.clear': '清空记录',
    'records.confirmClear': '确定清空全部下载记录？此操作不可撤销。',
    'records.cleared': '下载记录已清空。',
    'form.createFailed': '创建失败。',
    'form.requestFailed': '请求失败。',
    'form.creatingTransfer': '正在分析来源消息范围…',
    'form.creatingTransferShort': '分析中…',
    'form.createSuccess': '任务已创建，正在排队处理。',
    'media.title': '媒体管理',
    'media.scan': '扫描可清理文件',
    'media.scanning': '正在扫描…',
    'media.totalFiles': '可清理文件',
    'media.totalSize': '总大小',
    'media.retentionDays': '保留天数',
    'media.transferItems': '转存任务文件',
    'media.orphanFiles': '遗留文件',
    'media.file': '文件',
    'media.size': '大小',
    'media.status': '状态',
    'media.source': '来源',
    'media.path': '路径',
    'media.mtime': '最后修改',
    'media.cleanup': '清理选中文件',
    'media.cleaning': '清理中…',
    'media.selected': '已选',
    'media.files': '个文件',
    'media.noSelection': '请先选择要清理的文件。',
    'media.confirmCleanup': '确定要删除选中的文件吗？此操作不可撤销。',
    'media.cleanupDone': '清理完成：已删除 {count} 个文件 ({size})。',
    'media.cleanupHistory': '清理历史',
    'media.empty': '没有可清理文件',
    'media.reason': '原因',
    'media.time': '时间',
    'media.filterByTask': '按任务筛选：',
    'media.allTasks': '全部任务',
    'status.pending': '排队中',
    'status.running': '运行中',
    'status.paused': '已暂停',
    'status.success': '已完成',
    'status.failure': '失败',
    'status.skipped': '跳过',
    'event.level.info': '信息',
    'event.level.warning': '警告',
    'event.level.error': '错误',
    'error.auth_required': '需要登录。',
    'error.invalid_task_id': '任务 ID 无效。',
    'error.task_not_found': '找不到任务。',
    'error.source_link_required': '请填写来源链接。',
    'error.target_link_required': '请填写目标链接。',
    'error.range_ids_required': '起始 ID 和结束 ID 必须同时填写。',
    'error.range_end_before_start': '结束 ID 必须大于或等于起始 ID。',
    'error.invalid_payload': '请求内容无效。',
  },
  en: {
    'app.subtitle': 'Transfer Console',
    'nav.section.main': 'Main',
    'nav.section.monitor': 'Monitor & Data',
    'nav.section.system': 'System',
    'nav.transfers': 'Transfer Tasks',
    'nav.watches': 'Live Watches',
    'nav.downloadsUploads': 'DL & Upload',
    'nav.statistics': 'Statistics',
    'nav.settings': 'Settings',
    'nav.records': 'Records',
    'nav.media': 'Media Mgmt',
    'nav.profile': 'Me',
    'nav.logout': 'Log Out',
    'side.failed': 'Failed items',
    'side.status': 'System running',
    'hero.title': 'Transfer Console',
    'hero.body': 'Manage Telegram content transfer tasks — live monitoring, batch operations, smart filtering',
    'action.refresh': 'Refresh',
    'new.title': 'New Transfer',
    'new.source': 'Source link',
    'new.target': 'Target',
    'new.targetProfile': 'Target profile',
    'profile.pikpak': 'PikPak Document Transfer',
    'profile.generic': 'Generic Telegram Target',
    'new.startId': 'Start ID',
    'new.endId': 'End ID',
    'new.optional': 'Optional',
    'new.includeComment': 'Include comments',
    'new.hint': 'Leave IDs empty for message links. Channel links auto-detect range if IDs omitted.',
    'new.create': 'Create task',
    'watches.title': 'Active Watches',
    'watches.downloadTitle': 'Download Watch',
    'watches.downloadMeta': 'Auto-download new messages',
    'watches.forwardTitle': 'Forward Watch',
    'watches.forwardMeta': 'Auto-forward new messages',
    'watches.type': 'Type',
    'watches.source': 'Source channel',
    'watches.target': 'Target channel',
    'watches.sources': 'Source channels (one per line)',
    'watches.includeComment': 'Include comments',
    'watches.createDownload': 'Add download watch',
    'watches.createForward': 'Add forward watch',
    'watches.empty': 'No live watches yet.',
    'watches.delete': 'Remove',
    'watches.edit': 'Edit',
    'watches.download': 'Download watch',
    'watches.forward': 'Forward watch',
    'watches.created': 'Live watch created.',
    'watches.deleted': 'Live watch removed.',
    'watches.updated': 'Live watch updated.',
    'watches.events': 'Forward log',
    'watches.todayEvents': 'Today',
    'watches.allEvents': 'Full log',
    'watches.history': 'Log',
    'watches.historyTitle': 'Forward watch log',
    'watches.pageInfo': 'Page {page} / {pages} · {total} total',
    'watches.noEvents': 'No forwarding events yet.',
    'watches.eventForwarded': 'Forwarded',
    'watches.eventSkipped': 'Filtered',
    'watches.eventLoading': 'Loading…',
    'watches.loadMore': 'Load more',
    'watches.targetRequired': 'Target link is required.',
    'watches.sourceRequired': 'Source link is required.',
    'action.cancel': 'Cancel',
    'action.save': 'Save',
    // merged downloads & uploads page
    'dl.title': 'Channel Download',
    'dl.meta': 'Pull files from Telegram channels',
    'dl.link': 'Channel link',
    'dl.startDate': 'Start time',
    'dl.endDate': 'End time',
    'dl.keywords': 'Keywords',
    'dl.keywordsPlaceholder': 'Comma-separated, optional',
    'dl.types': 'Download types',
    'dl.includeComment': 'Include comments',
    'dl.create': 'Create download',
    'dl.accepted': 'Channel download task created.',
    'dl.uploadTitle': 'Local Upload',
    'dl.uploadMeta': 'Push files to Telegram channel',
    'dl.uploadPath': 'Local path',
    'dl.uploadTarget': 'Target channel',
    'dl.recursive': 'Upload folder recursively',
    'dl.uploadPlaceholder': 'Placeholder, future work',
    'dl.createUpload': 'Create upload',
    'dl.uploadAccepted': 'Upload task created.',
    'dl.history': 'Operation History',
    'dl.historyId': 'ID',
    'dl.historyType': 'Type',
    'dl.historyDetail': 'Detail',
    'dl.historyStatus': 'Status',
    'dl.historyError': 'Error',
    'dl.historyTime': 'Created',
    'dl.historyEmpty': 'No download or upload operations yet.',
    'dl.typeDownload': 'Channel DL',
    'dl.typeUpload': 'Local Upload',
    'statistics.title': 'Statistics & Export',
    'statistics.table': 'Table',
    'statistics.available': 'Available',
    'statistics.rows': 'Rows',
    'statistics.yes': 'Yes',
    'statistics.no': 'No',
    'statistics.link': 'Link table',
    'statistics.count': 'Count table',
    'statistics.upload': 'Upload table',
    'statistics.exportLink': 'Export link table',
    'statistics.exportCount': 'Export count table',
    'statistics.exportUpload': 'Export upload table',
    'statistics.exported': 'Table exported.',
    'tasks.title': 'Transfer Tasks',
    'tasks.notSynced': 'Not synced',
    'tasks.id': 'ID',
    'tasks.status': 'Status',
    'tasks.source': 'Source',
    'tasks.target': 'Target',
    'tasks.progress': 'Progress',
    'tasks.actions': 'Actions',
    'tasks.pause': 'Pause',
    'tasks.resume': 'Resume',
    'tasks.retryFailed': 'Retry failed',
    'tasks.delete': 'Delete',
    'tasks.empty': 'No transfer tasks yet.',
    'items.title': 'File Progress',
    'items.selectTask': 'Select a task to view details',
    'items.empty': 'No file records for this task yet.',
    'items.tab.running': 'Running',
    'items.tab.success': 'Completed',
    'items.tab.skipped': 'Skipped',
    'items.tab.failure': 'Failed',
    'items.retryFailed': 'Retry failed',
    'items.page.previous': 'Prev',
    'items.page.next': 'Next',
    'pagination.pageInfo': 'Page {page} / {pages} · {total} total',
    'events.title': 'Recent Events',
    'events.empty': 'No events.',
    'events.loadMore': 'Load more',
    'settings.title': 'Settings',
    'settings.safeNote': 'Sensitive fields show configured status only',
    'settings.paths': 'Paths & Tasks',
    'settings.saveDirectory': 'Save directory',
    'settings.tempDirectory': 'Temp directory',
    'settings.sessionDirectory': 'Session directory',
    'settings.maxDownload': 'Max download tasks',
    'settings.maxUpload': 'Max upload tasks',
    'settings.retryDownload': 'Download retries',
    'settings.retryUpload': 'Upload retries',
    'settings.pikpakMaxFileSize': 'PikPak max file size (bytes)',
    'settings.pikpakArchive': 'PikPak Archive',
    'settings.pikpakArchiveEnable': 'Archive by source channel',
    'settings.pikpakArchiveRemote': 'rclone remote',
    'settings.pikpakArchiveSource': 'Ingest directory',
    'settings.pikpakArchiveRoot': 'Archive root',
    'settings.pikpakArchivePoll': 'Poll seconds',
    'settings.pikpakArchiveInterval': 'Poll interval',
    'settings.pikpakArchiveWindow': 'Match window seconds',
    'settings.behavior': 'Behavior',
    'settings.notice': 'Bot notifications',
    'settings.shutdown': 'Shutdown on exit',
    'settings.downloadUpload': 'Download-then-upload for restricted',
    'settings.uploadDelete': 'Delete local after upload',
    'settings.pendingLimit': 'Upload queue limit',
    'settings.sensitive': 'Account & Proxy',
    'settings.proxyPassword': 'Proxy password',
    'settings.secretConfigured': 'Configured, fill to replace',
    'settings.downloadTypes': 'Download Types',
    'settings.downloadTypesHint': '(Check = allow download, unchecked types will be ignored)',
    'settings.forwardTypes': 'Forward Types',
    'settings.forwardTypesHint': '(Check = allow forward, unchecked types will be ignored)',
    'settings.messageFilter': 'Message Filter',
    'settings.mediaTypes': 'Media types',
    'settings.mediaTypesHint': '(Check = allow, unchecked types will be filtered out)',
    'settings.dateRange': 'Date range',
    'settings.keywords': 'Keywords',
    'settings.enabled': 'Enabled',
    'settings.startDate': 'Start date',
    'settings.endDate': 'End date',
    'settings.keywordList': 'Keywords (comma separated)',
    'settings.keywordPlaceholder': 'Enter keywords, separated by commas',
    'settings.exports': 'Export Tables',
    'settings.exportLink': 'Link table',
    'settings.exportCount': 'Count table',
    'settings.exportUpload': 'Upload table',
    'settings.save': 'Save settings',
    'settings.saved': 'Settings saved.',
    'records.title': 'Download Records',
    'records.chat': 'Chat ID',
    'records.message': 'Message ID',
    'records.file': 'File',
    'records.size': 'Size',
    'records.updated': 'Updated',
    'records.empty': 'No download records yet.',
    'records.clear': 'Clear All',
    'records.confirmClear': 'Clear all download records? This cannot be undone.',
    'records.cleared': 'Download records cleared.',
    'form.createFailed': 'Creation failed.',
    'form.requestFailed': 'Request failed.',
    'form.creatingTransfer': 'Analyzing source message range…',
    'form.creatingTransferShort': 'Analyzing…',
    'form.createSuccess': 'Task created, queued for processing.',
    'media.title': 'Media Management',
    'media.scan': 'Scan cleanable files',
    'media.scanning': 'Scanning…',
    'media.totalFiles': 'Cleanable files',
    'media.totalSize': 'Total size',
    'media.retentionDays': 'Retention days',
    'media.transferItems': 'Transfer task files',
    'media.orphanFiles': 'Orphan files',
    'media.file': 'File',
    'media.size': 'Size',
    'media.status': 'Status',
    'media.source': 'Source',
    'media.path': 'Path',
    'media.mtime': 'Modified',
    'media.cleanup': 'Delete selected',
    'media.cleaning': 'Cleaning…',
    'media.selected': 'Selected',
    'media.files': 'files',
    'media.noSelection': 'Select files to delete first.',
    'media.confirmCleanup': 'Delete selected files? This cannot be undone.',
    'media.cleanupDone': 'Cleanup done: {count} files deleted ({size}).',
    'media.cleanupHistory': 'Cleanup history',
    'media.empty': 'No cleanable files',
    'media.reason': 'Reason',
    'media.time': 'Time',
    'media.filterByTask': 'Filter by task:',
    'media.allTasks': 'All tasks',
    'status.pending': 'Pending',
    'status.running': 'Running',
    'status.paused': 'Paused',
    'status.success': 'Completed',
    'status.failure': 'Failed',
    'status.skipped': 'Skipped',
    'event.level.info': 'Info',
    'event.level.warning': 'Warning',
    'event.level.error': 'Error',
    'error.auth_required': 'Authentication required.',
    'error.invalid_task_id': 'Invalid task ID.',
    'error.task_not_found': 'Task not found.',
    'error.source_link_required': 'Source link is required.',
    'error.target_link_required': 'Target link is required.',
    'error.range_ids_required': 'Start and end IDs required together.',
    'error.range_end_before_start': 'End ID must be >= Start ID.',
    'error.invalid_payload': 'Invalid payload.',
  }
};

const state = {
  lang: localStorage.getItem('trmd-lang') || 'zh',
  activeView: 'transfers',
  activeItemStatus: 'running',
  selectedTaskId: null,
  tasks: [],
  watches: [],
  settings: null,
  settingsSchema: {},
  settingsModel: {},
  items: [],
  events: [],
  records: [],
  statistics: null,
  lastSync: null,
  itemPages: {},
  itemData: {},
  eventData: {},
  taskPollTimer: null,
  watchEventCache: {},
  watchHistory: { watchId: null, page: 1, pageSize: 20, total: 0 },
  recordsPage: 1,
  recordsPageSize: 50,
  recordsTotal: 0,
};
window.state = state;

function $(sel) {
  return document.querySelector(sel);
}

function $$(sel) {
  return document.querySelectorAll(sel);
}

window.$ = $;
window.$$ = $$;

function t(key, replacements) {
  const dict = i18n[state.lang] || i18n.zh;
  let text = dict[key];
  if (text === undefined) {
    // fallback to zh
    text = (i18n.zh[key]) || key;
  }
  if (replacements) {
    for (const [k, v] of Object.entries(replacements)) {
      text = text.replace('{' + k + '}', v);
    }
  }
  return text;
}

function esc(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

const DEFAULT_PAGE_SIZE = 50;

function paginationMeta(total, pageSize, page) {
  const safePageSize = Math.max(1, Number(pageSize || DEFAULT_PAGE_SIZE));
  const safeTotal = Math.max(0, Number(total || 0));
  const totalPages = Math.max(1, Math.ceil(safeTotal / safePageSize) || 1);
  const safePage = Math.min(Math.max(1, Number(page || 1)), totalPages);
  return {
    page: safePage,
    pageSize: safePageSize,
    total: safeTotal,
    totalPages: totalPages
  };
}

function renderPaginationBar(options) {
  options = options || {};
  const meta = paginationMeta(options.total, options.pageSize, options.page);
  if (meta.totalPages <= 1 && !options.alwaysShow) return '';
  const prefix = options.prefix || 'pagination';
  const variant = options.variant || 'desktop';
  const pageInfoKey = options.pageInfoKey || 'pagination.pageInfo';
  const pageInfo = t(pageInfoKey)
    .replace('{page}', meta.page)
    .replace('{pages}', meta.totalPages)
    .replace('{total}', meta.total);
  if (variant === 'mobile') {
    return '<div class="mob-sheet-pagination">' +
      '<span class="mob-pagination-info">' + esc(pageInfo) + '</span>' +
      '<div class="mob-pagination-actions flex gap-2">' +
        '<button class="mob-btn mob-btn-sm mob-btn-muted" id="' + prefix + '-prev" ' + (meta.page <= 1 ? 'disabled' : '') + '>' + esc(t('items.page.previous')) + '</button>' +
        '<button class="mob-btn mob-btn-sm mob-btn-muted" id="' + prefix + '-next" ' + (meta.page >= meta.totalPages ? 'disabled' : '') + '>' + esc(t('items.page.next')) + '</button>' +
      '</div></div>';
  }
  return '<div class="pagination-bar flex items-center justify-between px-[18px] py-2 pb-[14px] gap-3 flex-wrap">' +
    '<span class="text-xs text-muted">' + esc(pageInfo) + '</span>' +
    '<div class="flex gap-2">' +
      '<button class="btn btn-sm" id="' + prefix + '-prev" ' + (meta.page <= 1 ? 'disabled' : '') + '>' + esc(t('items.page.previous')) + '</button>' +
      '<button class="btn btn-sm" id="' + prefix + '-next" ' + (meta.page >= meta.totalPages ? 'disabled' : '') + '>' + esc(t('items.page.next')) + '</button>' +
    '</div></div>';
}

function bindPaginationBar(prefix, page, totalPages, onPageChange) {
  const prevBtn = $('#' + prefix + '-prev');
  const nextBtn = $('#' + prefix + '-next');
  if (prevBtn) {
    prevBtn.addEventListener('click', function() {
      if (page > 1) onPageChange(page - 1);
    });
  }
  if (nextBtn) {
    nextBtn.addEventListener('click', function() {
      if (page < totalPages) onPageChange(page + 1);
    });
  }
}

function applyLanguage() {
  $$('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    if (key) el.textContent = t(key);
  });
  document.title = t('app.title') || 'TRMD · 转存控制台';
}

function applyLanguageAndRefresh() {
  applyLanguage();
  if (state.activeView === 'transfers' && typeof renderTasks === 'function') renderTasks();
  if (state.activeView === 'watches' && typeof renderWatches === 'function') renderWatches();
  if (state.activeView === 'settings' && typeof renderSettings === 'function') renderSettings();
  if (state.activeView === 'records' && typeof loadRecords === 'function') loadRecords();
  if (typeof renderMobTasks === 'function') renderMobTasks();
  if (typeof renderMobWatches === 'function') renderMobWatches();
}

function redirectToLoginPage() {
  if (window.__trmdRedirectingToLogin) return;
  window.__trmdRedirectingToLogin = true;
  window.location.assign('/');
}

async function fetchJson(url) {
  const resp = await fetch(url);
  if (resp.status === 401) { redirectToLoginPage(); throw { error_code: 'auth_required' }; }
  if (!resp.ok) {
    let data;
    try { data = await resp.json(); } catch(e) { data = {}; }
    throw data;
  }
  return resp.json();
}

async function postJson(url, payload, method) {
  const resp = await fetch(url, {
    method: method || 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (resp.status === 401) { redirectToLoginPage(); throw { error_code: 'auth_required' }; }
  const data = await resp.json();
  if (!resp.ok) throw data;
  return data;
}

async function patchJson(url, payload) {
  const resp = await fetch(url, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (resp.status === 401) { redirectToLoginPage(); throw { error_code: 'auth_required' }; }
  const data = await resp.json();
  if (!resp.ok) throw data;
  return data;
}

function translateApiError(data, fallbackKey) {
  if (data && data.error_code && data.error) {
    const key = 'error.' + data.error_code;
    const translated = t(key);
    if (translated !== key) return translated;
    return data.error;
  }
  return t(fallbackKey || 'form.requestFailed');
}

function fmtSize(bytes) {
  if (!bytes && bytes !== 0) return '-';
  bytes = Number(bytes);
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + ' MB';
  return (bytes / 1073741824).toFixed(2) + ' GB';
}

function formatBytes(bytes) {
  return fmtSize(bytes);
}

function fmtTime(iso) {
  if (!iso) return '-';
  try { return new Date(iso).toLocaleString(); } catch(e) { return iso; }
}

function fmtTimestamp(sec) {
  if (!sec) return '-';
  try { return new Date(sec * 1000).toLocaleString(); } catch(e) { return String(sec); }
}

function statusBadge(status) {
  const labels = { pending: 'status.pending', running: 'status.running', paused: 'status.paused', success: 'status.success', failure: 'status.failure', skipped: 'status.skipped' };
  const cls = status || 'pending';
  return '<span class="badge badge-' + cls + '"><span class="status-dot ' + cls + '"></span>' + t(labels[status] || 'status.pending') + '</span>';
}

function setLang(lang) {
  state.lang = lang || 'zh';
  localStorage.setItem('trmd-lang', state.lang);
  applyLanguageAndRefresh();
}

function optionValues(options) {
  return (options || []).map(function(option) {
    return typeof option === 'string' ? option : option.value;
  }).filter(Boolean);
}

function selectedKeys(value) {
  if (Array.isArray(value)) return value;
  if (value && typeof value === 'object') {
    return Object.entries(value).filter(function(entry) { return Boolean(entry[1]); }).map(function(entry) { return entry[0]; });
  }
  return [];
}

function taskProgressPercent(task) {
  return Number(task && task.progress_percent || 0);
}

function taskCompletedLabel(task) {
  if (!task) return '0/0';
  return String(Number(task.completed_items || 0)) + '/' + String(Number(task.total_items || 0));
}

function taskFailedCount(task) {
  return Number(task && task.failed_items || 0);
}

function formatSpeed(bytesPerSecond) {
  const value = Number(bytesPerSecond || 0);
  if (!value || value < 0) return '-';
  return fmtSize(value) + '/s';
}

function transferPhaseLabel(phase) {
  const labels = {
    downloading: '下载',
    downloaded: '下载完成',
    uploading: '上传',
    uploaded: '上传完成',
    sent: '已发送',
    forwarded: '已转发',
    failure: '失败',
    failed: '失败',
    skipped: '跳过',
    pending: '等待'
  };
  return labels[phase] || phase || '-';
}

function transferProgressLabel(current, total) {
  current = Number(current || 0);
  total = Number(total || 0);
  if (!total) return current ? fmtSize(current) : '-';
  const percent = Math.min(100, Math.round((current / total) * 100));
  return fmtSize(current) + '/' + fmtSize(total) + ' · ' + percent + '%';
}

function activeTransferSummary(task) {
  if (!task || !task.active_item_id) return '';
  const phase = transferPhaseLabel(task.active_phase);
  const name = task.active_file_name || ('#' + task.active_item_id);
  const progress = transferProgressLabel(task.active_progress_current, task.active_progress_total);
  const speed = formatSpeed(task.active_speed_bps);
  return phase + ' · ' + name + ' · ' + progress + (speed !== '-' ? ' · ' + speed : '');
}

function itemTransferSummary(item) {
  if (!item) return '-';
  const phase = transferPhaseLabel(item.phase || item.status);
  if (item.phase === 'uploading' || Number(item.upload_current || 0) > 0) {
    return phase + ' · ' + transferProgressLabel(item.upload_current, item.upload_total) +
      (Number(item.upload_speed_bps || 0) ? ' · ' + formatSpeed(item.upload_speed_bps) : '');
  }
  if (Number(item.download_total || 0) || Number(item.download_current || 0)) {
    return phase + ' · ' + transferProgressLabel(item.download_current, item.download_total) +
      (Number(item.download_speed_bps || 0) ? ' · ' + formatSpeed(item.download_speed_bps) : '');
  }
  return phase;
}

async function runTaskAction(event, taskId, action) {
  if (event && event.stopPropagation) event.stopPropagation();
  await postJson('/api/tasks/' + encodeURIComponent(taskId) + '/' + action, {});
  if (typeof loadMobileTasks === 'function') await loadMobileTasks();
  else if (typeof loadTasks === 'function') await loadTasks();
}

async function deleteTask(event, taskId) {
  if (event && event.stopPropagation) event.stopPropagation();
  if (!confirm('确定删除任务 #' + taskId + '？')) return;
  const resp = await fetch('/api/tasks/' + encodeURIComponent(taskId), { method: 'DELETE' });
  if (!resp.ok) {
    let data = {};
    try { data = await resp.json(); } catch(e) {}
    throw data;
  }
  state.tasks = (state.tasks || []).filter(function(task) { return Number(task.id) !== Number(taskId); });
  if (state.selectedTaskId === taskId) state.selectedTaskId = null;
  if (typeof renderMobTasks === 'function') renderMobTasks();
  if (typeof renderTasks === 'function') renderTasks();
}

async function deleteWatch(watchId) {
  if (!confirm(t('watches.delete'))) return;
  const resp = await fetch('/api/watches/' + encodeURIComponent(watchId), { method: 'DELETE' });
  if (!resp.ok) {
    let data = {};
    try { data = await resp.json(); } catch(e) {}
    throw data;
  }
  state.watches = (state.watches || []).filter(function(watch) { return watch.id !== watchId; });
  if (typeof loadMobileWatches === 'function') await loadMobileWatches();
  else if (typeof loadWatches === 'function') await loadWatches();
}
</script>
<script>// ================================================================
// mobile_script.js v2 — 4-tab clean navigation, no FAB/Drawer
// ($ already defined in shared.js)
// ================================================================

// ---------------------------------------------------------------------------
// Login helpers (delegates to shared.js utilities)
// ---------------------------------------------------------------------------
function showLoginStep(step) {
  var steps = ['phone', 'code', 'password', 'recovery', 'signup', 'done'];
  steps.forEach(function(id) { var el = document.getElementById('login-form-' + id); if (el) el.style.display = 'none'; });
  var el = document.getElementById('login-form-' + step);
  if (el) el.style.display = '';
  var container = document.getElementById('login-container');
  if (container && !container.classList.contains('active')) container.classList.add('active');
  var loginError = document.getElementById('login-error');
  if (loginError) loginError.classList.remove('visible');
}

function hideLogin() {
  var container = document.getElementById('login-container');
  if (container) container.classList.remove('active');
}

function showLoginError(msg) {
  var el = document.getElementById('login-error');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('visible');
}

async function checkAuthStatus() {
  try {
    var resp = await fetch('/api/auth/status');
    if (resp.status === 401) { redirectToLoginPage(); return; }
    var state = await resp.json();
    if (!state || !state.step) return;
    switch (state.step) {
      case 'pending':
        var container = document.getElementById('login-container');
        if (container) container.classList.remove('active');
        await loadCurrentView();
        startPolling();
        return;
      case 'done': case 'none':
        hideLogin();
        startPolling();
        return;
      case 'phone':
        showLoginStep('phone');
        if (state.error) showLoginError(state.error);
        break;
      case 'code':
        showLoginStep('code');
        if (state.code_type) {
          var desc = document.getElementById('login-code-desc');
          if (desc) desc.textContent = '验证码已通过「' + state.code_type + '」发送';
        }
        if (state.error) showLoginError(state.error);
        break;
      case 'password':
        showLoginStep('password');
        var hintEl = document.getElementById('login-password-hint-text');
        if (hintEl && state.hint) hintEl.textContent = state.hint;
        if (state.error) showLoginError(state.error);
        break;
      case 'recovery_code':
        showLoginStep('recovery');
        var rDesc = document.getElementById('login-recovery-desc');
        if (rDesc && state.message) rDesc.textContent = state.message;
        if (state.error) showLoginError(state.error);
        break;
      case 'signup':
        showLoginStep('signup');
        if (state.error) showLoginError(state.error);
        break;
      case 'error':
        if (state.error) showLoginError(state.error);
        break;
      default:
        break;
    }
  } catch (e) { /* ignore */ }
}

async function submitAuth(payload) {
  var btns = document.querySelectorAll('.mob-login-submit');
  btns.forEach(function(b) { b.disabled = true; });
  showLoginError('');
  try {
    await fetch('/api/auth/submit', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    await new Promise(function(r) { setTimeout(r, 500); });
    await checkAuthStatus();
  } catch (e) {
    showLoginError('提交失败，请重试');
  } finally {
    btns.forEach(function(b) { b.disabled = false; });
  }
}

// ---------------------------------------------------------------------------
// Login button bindings
// ---------------------------------------------------------------------------
(function() {
  var phoneBtn = document.getElementById('login-btn-phone');
  if (phoneBtn) phoneBtn.addEventListener('click', function() {
    var phone = document.getElementById('login-phone').value.trim();
    if (!phone) { showLoginError('请输入电话号码'); return; }
    submitAuth({ phone: phone });
  });

  var codeBtn = document.getElementById('login-btn-code');
  if (codeBtn) codeBtn.addEventListener('click', function() {
    var code = document.getElementById('login-code').value.trim();
    if (!code) { showLoginError('请输入验证码'); return; }
    submitAuth({ code: code });
  });

  var backBtn = document.getElementById('login-btn-back');
  if (backBtn) backBtn.addEventListener('click', function() {
    document.getElementById('login-code').value = '';
    showLoginStep('phone');
  });

  var pwdBtn = document.getElementById('login-btn-password');
  if (pwdBtn) pwdBtn.addEventListener('click', function() {
    var pwd = document.getElementById('login-password').value;
    if (!pwd) { showLoginError('请输入两步验证密码'); return; }
    submitAuth({ password: pwd });
  });

  var pwdBackBtn = document.getElementById('login-btn-back-pwd');
  if (pwdBackBtn) pwdBackBtn.addEventListener('click', function() {
    document.getElementById('login-password').value = '';
    showLoginStep('phone');
  });

  var recBtn = document.getElementById('login-btn-recovery');
  if (recBtn) recBtn.addEventListener('click', function() {
    var code = document.getElementById('login-recovery').value.trim();
    if (!code) { showLoginError('请输入恢复代码'); return; }
    submitAuth({ recovery_code: code });
  });

  var recBackBtn = document.getElementById('login-btn-back-recovery');
  if (recBackBtn) recBackBtn.addEventListener('click', function() {
    document.getElementById('login-recovery').value = '';
    showLoginStep('phone');
  });

  var signupBtn = document.getElementById('login-btn-signup');
  if (signupBtn) signupBtn.addEventListener('click', function() {
    var first = document.getElementById('login-first-name').value.trim();
    if (!first) { showLoginError('请输入名字'); return; }
    submitAuth({ first_name: first, last_name: document.getElementById('login-last-name').value.trim() });
  });
})();

// ---------------------------------------------------------------------------
// Polling
// ---------------------------------------------------------------------------
var pollTimer = null;
var initialLoadDone = false;
var mobileSettingsLoadPromise = null;

function hasActiveTasks() {
  return (window.state && Array.isArray(window.state.tasks) && window.state.tasks.some(function(t) {
    return t.status === 'pending' || t.status === 'running';
  }));
}

function startPolling() {
  stopPolling();
  initialLoadDone = true;

  async function poll() {
    if (document.hidden) {
      pollTimer = setTimeout(poll, hasActiveTasks() ? 3000 : 10000);
      return;
    }
    await loadCurrentView();
    pollTimer = setTimeout(poll, hasActiveTasks() ? 3000 : 10000);
  }

  poll();
}

document.addEventListener('visibilitychange', function() {
  if (document.hidden) return;
  loadCurrentView();
  startPolling();
});

function stopPolling() {
  if (pollTimer) { clearTimeout(pollTimer); pollTimer = null; }
}

async function loadCurrentView() {
  var active = document.querySelector('.mob-view.active');
  if (!active) return;
  var id = active.id;
  if (id === 'mob-view-transfers') {
    await loadMobileTasks();
    await refreshOpenTaskSheet();
  }
  else if (id === 'mob-view-watches') { await loadMobileWatches(); }
  else if (id === 'mob-view-downloads-uploads') { await loadMobileDownloadsUploads(); }
  // profile sub-pages load on demand
  var subActive = document.querySelector('.mob-subpage.active');
  if (subActive) {
    if (subActive.id === 'mob-subpage-statistics') { await loadMobileStatistics(); }
    else if (subActive.id === 'mob-subpage-records') { await loadMobileRecords(); }
  }
}

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------
var currentMainTab = 'transfers';
var currentProfileSub = null;
var profileTitles = {
  statistics: '统计面板',
  records: '下载记录',
  media: '媒体管理',
  settings: '系统设置'
};

function mobSwitchView(view) {
  // Hide all main views
  var views = document.querySelectorAll('.mob-view');
  views.forEach(function(v) { v.classList.remove('active'); });

  // Show target view
  var target = document.getElementById('mob-view-' + view);
  if (target) target.classList.add('active');

  // Update tab bar
  var tabs = document.querySelectorAll('#mob-tabbar .mob-tab');
  tabs.forEach(function(t) { t.classList.remove('active'); });
  var tab = document.querySelector('#mob-tabbar [data-mob-tab="' + view + '"]');
  if (tab) tab.classList.add('active');

  // Reset top bar (exit sub-page mode)
  exitSubPage();

  currentMainTab = view;

  // Load content
  if (view === 'transfers') { loadMobileTasks(); }
  else if (view === 'watches') { loadMobileWatches(); }
  else if (view === 'downloads-uploads') { loadMobileDownloadsUploads(); }
  else if (view === 'profile') { /* menu is static, sub-pages load on demand */ }
}

function mobNavigateTo(subpage) {
  // Hide profile menu
  var menu = document.getElementById('mob-profile-menu');
  if (menu) menu.style.display = 'none';

  // Hide all subpages
  var subs = document.querySelectorAll('.mob-subpage');
  subs.forEach(function(s) { s.classList.remove('active'); });

  // Show target subpage
  var target = document.getElementById('mob-subpage-' + subpage);
  if (target) target.classList.add('active');

  // Update top bar
  enterSubPage(profileTitles[subpage] || subpage);

  currentProfileSub = subpage;

  // Load content
  if (subpage === 'statistics') { loadMobileStatistics(); }
  else if (subpage === 'records') { loadMobileRecords(); }
  else if (subpage === 'media') { loadMediaMobile(); }
  else if (subpage === 'settings') { loadMobileSettings(); }
}

function mobNavigateBack() {
  exitSubPage();

  // Hide all subpages
  var subs = document.querySelectorAll('.mob-subpage');
  subs.forEach(function(s) { s.classList.remove('active'); });

  // Show profile menu
  var menu = document.getElementById('mob-profile-menu');
  if (menu) menu.style.display = '';

  currentProfileSub = null;
}

function enterSubPage(title) {
  var topbar = document.getElementById('mob-topbar');
  var titleEl = document.getElementById('mob-topbar-title');
  if (topbar) topbar.classList.add('sub');
  if (titleEl) titleEl.textContent = title;
}

function exitSubPage() {
  var topbar = document.getElementById('mob-topbar');
  var titleEl = document.getElementById('mob-topbar-title');
  if (topbar) topbar.classList.remove('sub');
  if (titleEl) titleEl.textContent = 'TRMD';
}

// ---------------------------------------------------------------------------
// Toast
// ---------------------------------------------------------------------------
function showToast(message, duration) {
  var el = document.getElementById('mob-toast');
  if (!el) return;
  el.textContent = message;
  el.classList.add('show');
  clearTimeout(el._timeout);
  el._timeout = setTimeout(function() { el.classList.remove('show'); }, duration || 2000);
}

// ---------------------------------------------------------------------------
// Badge helper
// ---------------------------------------------------------------------------
function mobBadge(status) {
  var map = {
    pending: '<span class="mob-card__badge pending">等待中</span>',
    running: '<span class="mob-card__badge running">运行中</span>',
    paused: '<span class="mob-card__badge paused">已暂停</span>',
    completed: '<span class="mob-card__badge completed">已完成</span>',
    success: '<span class="mob-card__badge completed">已完成</span>',
    failure: '<span class="mob-card__badge failure">失败</span>',
    cancelled: '<span class="mob-card__badge cancelled">已取消</span>',
    skipped: '<span class="mob-card__badge cancelled">已跳过</span>'
  };
  return map[status] || '<span class="mob-card__badge pending">' + esc(status) + '</span>';
}

// ---------------------------------------------------------------------------
// Collapse toggle
// ---------------------------------------------------------------------------
function toggleCollapse(head) {
  var parent = head.closest('.mob-collapse');
  if (!parent) return;
  parent.classList.toggle('open');
}

function mobEmptyHtml(message, i18nKey) {
  var attr = i18nKey ? ' data-i18n="' + escAttr(i18nKey) + '"' : '';
  return '<div class="mob-empty"' + attr + '>' + esc(message) + '</div>';
}

async function loadMobileTasks() {
  var container = document.getElementById('mob-tasks-list');
  if (!container) return;
  if (!window.state) window.state = {};
  if (!Array.isArray(window.state.tasks)) {
    container.innerHTML = mobEmptyHtml('加载中...');
  }
  try {
    var data = await fetchJson('/api/tasks');
    window.state.tasks = Array.isArray(data.tasks) ? data.tasks : [];
    window.state.lastSync = new Date().toLocaleTimeString();
    renderMobTasks();
  } catch (e) {
    window.state.tasks = [];
    container.innerHTML = mobEmptyHtml('加载失败');
  }
}

async function loadMobileWatches() {
  var container = document.getElementById('mob-watches-list');
  if (!container) return;
  if (!window.state) window.state = {};
  if (!Array.isArray(window.state.watches)) {
    container.innerHTML = mobEmptyHtml('加载中...');
  }
  try {
    var data = await fetchJson('/api/watches');
    window.state.watches = Array.isArray(data.watches) ? data.watches : [];
    renderMobWatches();
  } catch (e) {
    window.state.watches = [];
    container.innerHTML = mobEmptyHtml('加载失败');
  }
}

async function ensureMobileSettingsData() {
  if (!window.state) window.state = {};
  if (window.state.settings) return true;
  if (!mobileSettingsLoadPromise) {
    mobileSettingsLoadPromise = fetchJson('/api/settings').then(function(data) {
      window.state.settings = data.settings || {};
      window.state.schema = data.schema || {};
      window.state.settingsSchema = data.schema || {};
      window.state.settingsModel = data.settings_model || {};
      return true;
    }).catch(function(e) {
      mobileSettingsLoadPromise = null;
      throw e;
    });
  }
  return mobileSettingsLoadPromise;
}

async function loadMobileSettings() {
  try {
    await ensureMobileSettingsData();
    settingsRendered = false;
    ensureSettingsForm();
  } catch (e) {
    var notice = document.getElementById('mob-settings-notice');
    if (notice) {
      notice.classList.remove('hidden');
      notice.textContent = '加载失败';
      notice.style.color = 'var(--color-danger)';
    }
  }
}

async function loadMobileDownloadsUploads() {
  try {
    await ensureMobileSettingsData();
  } catch (e) {
    // Keep operations history usable even when settings cannot be loaded.
  }
  mobInitDownloadTypes();
  loadMobileOperations();
}

// ---------------------------------------------------------------------------
// Task rendering
// ---------------------------------------------------------------------------
function renderMobTasks() {
  var container = document.getElementById('mob-tasks-list');
  if (!container) return;
  if (!window.state || !Array.isArray(window.state.tasks)) {
    container.innerHTML = mobEmptyHtml('还没有转存任务。', 'tasks.empty');
    return;
  }
  if (window.state.tasks.length === 0) {
    container.innerHTML = mobEmptyHtml('还没有转存任务。', 'tasks.empty');
    return;
  }

  var html = '';
  window.state.tasks.forEach(function(t) {
    var progressPct = taskProgressPercent(t);
    var activeSummary = activeTransferSummary(t);
    html += '<div class="mob-card status-' + esc(t.status) + '" data-task-id="' + t.id + '">' +
      '<div class="mob-card__head">' +
        '<span class="mob-card__title">' + esc(t.title || t.source_link || '#' + t.id) + '</span>' +
        mobBadge(t.status) +
      '</div>' +
      '<div class="mob-card__row"><span class="label">来源</span><span>' + esc(t.source_link || '-') + '</span></div>' +
      '<div class="mob-card__row"><span class="label">进度</span><span>' + taskCompletedLabel(t) + (taskFailedCount(t) ? ' · 失败 ' + taskFailedCount(t) : '') + '</span></div>' +
      (activeSummary ? '<div class="mob-card__row"><span class="label">当前</span><span>' + esc(activeSummary) + '</span></div>' : '') +
      '<div class="mob-card__progress"><div class="mob-card__progress-fill" style="width:' + progressPct + '%"></div></div>' +
      '<div class="mob-card__actions">' +
        (t.can_pause ? '<button class="mob-btn mob-btn-sm mob-btn-muted" data-pause="' + t.id + '">暂停</button>' : '') +
        (t.can_resume ? '<button class="mob-btn mob-btn-sm mob-btn-muted" data-resume="' + t.id + '">继续</button>' : '') +
        (t.can_retry ? '<button class="mob-btn mob-btn-sm mob-btn-muted" data-retry="' + t.id + '">重试</button>' : '') +
        (t.can_delete ? '<button class="mob-btn mob-btn-sm mob-btn-danger" data-delete="' + t.id + '">删除</button>' : '') +
      '</div>' +
    '</div>';
  });
  container.innerHTML = html || mobEmptyHtml('还没有转存任务。', 'tasks.empty');
  bindTaskCardEvents(container);
}

function bindTaskCardEvents(container) {
  container.querySelectorAll('[data-pause]').forEach(function(btn) {
    btn.addEventListener('click', function(e) { e.stopPropagation(); runTaskAction(e, Number(btn.dataset.pause), 'pause'); });
  });
  container.querySelectorAll('[data-resume]').forEach(function(btn) {
    btn.addEventListener('click', function(e) { e.stopPropagation(); runTaskAction(e, Number(btn.dataset.resume), 'resume'); });
  });
  container.querySelectorAll('[data-retry]').forEach(function(btn) {
    btn.addEventListener('click', function(e) { e.stopPropagation(); runTaskAction(e, Number(btn.dataset.retry), 'retry-failed'); });
  });
  container.querySelectorAll('[data-delete]').forEach(function(btn) {
    btn.addEventListener('click', function(e) { e.stopPropagation(); deleteTask(e, Number(btn.dataset.delete)); });
  });
  container.querySelectorAll('.mob-card').forEach(function(card) {
    card.addEventListener('click', function(e) {
      if (e.target.closest('button')) return;
      openTaskDetail(Number(card.dataset.taskId));
    });
  });
}

// ---------------------------------------------------------------------------
// Watch rendering
// ---------------------------------------------------------------------------
function renderMobWatches() {
  var container = document.getElementById('mob-watches-list');
  if (!container) return;
  if (!window.state || !Array.isArray(window.state.watches)) {
    container.innerHTML = mobEmptyHtml('还没有实时监听。', 'watches.empty');
    return;
  }
  if (window.state.watches.length === 0) {
    container.innerHTML = mobEmptyHtml('还没有实时监听。', 'watches.empty');
    return;
  }

  var typeLabels = { download: '下载监听', forward: '转发监听' };
  var html = '';
  window.state.watches.forEach(function(w) {
    var statusClass = w.status === 'paused' ? 'paused' : 'running';
    var statusLabel = w.status === 'paused' ? '已暂停' : '运行中';
    var sanitized = esc(w.id).replace(/[^a-zA-Z0-9_-]/g, '_');
    var eventCount = Number(w.event_count || 0);
    html += '<div class="mob-card status-' + statusClass + '">' +
      '<div class="mob-card__head">' +
        '<span class="mob-card__title">' + esc(typeLabels[w.type] || w.type || '监听') + '</span>' +
        '<span class="mob-card__badge ' + statusClass + '">' + statusLabel + '</span>' +
      '</div>' +
      '<div class="mob-card__row"><span class="label">来源</span><span>' + esc(Array.isArray(w.source_links) ? w.source_links.join(', ') : (w.source_link || '-')) + '</span></div>' +
      (w.target_link ? '<div class="mob-card__row"><span class="label">目标</span><span>' + esc(w.target_link) + '</span></div>' : '') +
      '<div class="mob-card__row"><span class="label">今日</span><span>' + (w.today_count || 0) + '</span></div>' +
      '<div class="mob-card__actions">' +
        '<button class="mob-btn mob-btn-sm mob-btn-muted" data-delete-watch="' + esc(w.id) + '">删除</button>' +
        (w.type === 'forward' ? '<button class="mob-btn mob-btn-sm mob-btn-muted" data-events-watch="' + esc(w.id) + '" data-sanitized="' + sanitized + '">今日</button>' : '') +
        (w.type === 'forward' ? '<button class="mob-btn mob-btn-sm mob-btn-muted" data-watch-history="' + esc(w.id) + '">记录' + (eventCount ? ' ' + eventCount : '') + '</button>' : '') +
      '</div>' +
      '<div class="mob-watch-events hidden" id="mob-watch-events-' + sanitized + '"></div>' +
    '</div>';
  });
  container.innerHTML = html || mobEmptyHtml('还没有实时监听。', 'watches.empty');

  container.querySelectorAll('[data-delete-watch]').forEach(function(btn) {
    btn.addEventListener('click', function() { deleteWatch(btn.dataset.deleteWatch); });
  });
  container.querySelectorAll('[data-events-watch]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var panel = document.getElementById('mob-watch-events-' + btn.dataset.sanitized);
      if (!panel) return;
      var isHidden = panel.classList.contains('hidden');
      panel.classList.toggle('hidden');
      if (isHidden) loadMobileWatchEvents(btn.dataset.eventsWatch, btn.dataset.sanitized);
    });
  });
  container.querySelectorAll('[data-watch-history]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      openMobileWatchHistory(btn.dataset.watchHistory, 1);
    });
  });
}

async function loadMobileWatchEvents(watchId, sanitized) {
  var panel = document.getElementById('mob-watch-events-' + sanitized);
  if (!panel) return;
  panel.innerHTML = '<div style="padding:8px;color:var(--color-muted);">加载中...</div>';
  try {
    var data = await fetchJson('/api/watches/' + encodeURIComponent(watchId) + '/events?limit=20&today=1');
    if (!data || !data.events || data.events.length === 0) {
      panel.innerHTML = '<div style="padding:8px;color:var(--color-muted);">暂无事件</div>';
      return;
    }
    var html = '';
    data.events.forEach(function(ev) {
      var statusLabel = ev.status === 'success' ? '转发成功' : '已过滤';
      html += '<div class="watch-event-item">' +
        '<span class="watch-event-time">' + esc(fmtTime(ev.created_at)) + '</span>' +
        '<span class="watch-event-badge badge ' + (ev.status === 'success' ? 'badge-success' : 'badge-warning') + '">' + esc(statusLabel) + '</span>' +
        '<span class="watch-event-info">' + esc(ev.message || '') + '</span>' +
      '</div>';
    });
    panel.innerHTML = html;
  } catch (e) {
    panel.innerHTML = '<div style="padding:8px;color:var(--color-danger);">加载失败</div>';
  }
}

async function openMobileWatchHistory(watchId, page) {
  sheetState.sheetType = 'watch-history';
  state.watchHistory = { watchId: watchId, page: page || 1, pageSize: 20, total: 0 };
  var overlay = document.getElementById('mob-sheet-overlay');
  var sheet = document.getElementById('mob-sheet');
  if (!overlay || !sheet) return;
  sheet.innerHTML = '<div style="padding:20px;text-align:center;color:var(--color-muted);">加载中...</div>';
  overlay.classList.add('open');
  await loadMobileWatchHistoryPage();
}

async function loadMobileWatchHistoryPage() {
  var sheet = document.getElementById('mob-sheet');
  if (!sheet || !state.watchHistory.watchId) return;
  var page = state.watchHistory.page || 1;
  var pageSize = state.watchHistory.pageSize || 20;
  var offset = (page - 1) * pageSize;
  try {
    var data = await fetchJson('/api/watches/' + encodeURIComponent(state.watchHistory.watchId) + '/events?limit=' + pageSize + '&offset=' + offset);
    var items = data.events || [];
    var total = Number(data.total || 0);
    var totalPages = Math.max(1, Math.ceil(total / pageSize));
    var html = '<div class="mob-sheet__title">' + esc(t('watches.historyTitle')) + '</div>';
    if (!items.length) {
      html += '<div class="mob-empty">' + esc(t('watches.noEvents')) + '</div>';
    } else {
      items.forEach(function(ev) {
        var statusLabel = ev.status === 'success' ? t('watches.eventForwarded') : t('watches.eventSkipped');
        html += '<div class="mob-event-row">' +
          '<time>' + esc(fmtTime(ev.created_at)) + '</time>' +
          '<span class="mob-card__badge ' + (ev.status === 'success' ? 'completed' : 'pending') + '">' + esc(statusLabel) + '</span>' +
          '<div style="margin-top:4px;word-break:break-all;">' + esc(ev.message || '-') + '</div>' +
        '</div>';
      });
    }
    html += '<div class="mob-sheet-pagination">' +
      '<span>' + esc(t('watches.pageInfo').replace('{page}', page).replace('{pages}', totalPages).replace('{total}', total)) + '</span>' +
      '<div style="display:flex;gap:8px;">' +
        '<button class="mob-btn mob-btn-sm mob-btn-muted" id="mob-watch-history-prev" ' + (page <= 1 ? 'disabled' : '') + '>' + esc(t('items.page.previous')) + '</button>' +
        '<button class="mob-btn mob-btn-sm mob-btn-muted" id="mob-watch-history-next" ' + (page >= totalPages ? 'disabled' : '') + '>' + esc(t('items.page.next')) + '</button>' +
      '</div>' +
    '</div>' +
    '<button class="mob-btn mob-btn-muted mob-btn-sm" style="align-self:flex-end;margin-top:4px;" id="mob-watch-history-close">关闭</button>';
    sheet.innerHTML = html;
    document.getElementById('mob-watch-history-close')?.addEventListener('click', closeSheet);
    document.getElementById('mob-watch-history-prev')?.addEventListener('click', function() {
      state.watchHistory.page = Math.max(1, page - 1);
      loadMobileWatchHistoryPage();
    });
    document.getElementById('mob-watch-history-next')?.addEventListener('click', function() {
      state.watchHistory.page = page + 1;
      loadMobileWatchHistoryPage();
    });
  } catch (e) {
    sheet.innerHTML = '<div style="padding:20px;text-align:center;color:var(--color-danger);">加载失败</div>';
  }
}

// ---------------------------------------------------------------------------
// Task detail sheet
// ---------------------------------------------------------------------------
var sheetState = { sheetType: '', taskId: null, items: [], events: [], currentTab: 'all', currentPage: 0, pageSize: 30, loading: false, hasMore: false };

async function openTaskDetail(taskId) {
  sheetState = { sheetType: 'task-detail', taskId: taskId, items: [], events: [], currentTab: 'all', currentPage: 0, pageSize: 30, loading: false, hasMore: false };
  var overlay = document.getElementById('mob-sheet-overlay');
  var sheet = document.getElementById('mob-sheet');
  if (!overlay || !sheet) return;
  sheet.innerHTML = '<div style="padding:20px;text-align:center;color:var(--color-muted);">加载中...</div>';
  overlay.classList.add('open');

  try {
    var data = await fetchJson('/api/tasks/' + taskId);
    sheetState.items = data.items || [];
    sheetState.events = data.events || [];
    renderSheetContent(data);
  } catch (e) {
    sheet.innerHTML = '<div style="padding:20px;text-align:center;color:var(--color-danger);">加载失败</div>';
  }
}

async function refreshOpenTaskSheet() {
  var overlay = document.getElementById('mob-sheet-overlay');
  if (!overlay || !overlay.classList.contains('open') || sheetState.sheetType !== 'task-detail' || !sheetState.taskId) return;
  var sheet = document.getElementById('mob-sheet');
  if (!sheet) return;
  try {
    var data = await fetchJson('/api/tasks/' + sheetState.taskId);
    sheetState.items = data.items || [];
    sheetState.events = data.events || [];
    updateSheetContent(data);
  } catch (e) {}
}

function renderSheetContent(data) {
  var sheet = document.getElementById('mob-sheet');
  if (!sheet) return;

  var task = data.task || {};
  var summary = data.summary || {};
  var totalItems = summary.total || sheetState.items.length || 0;
  var successCount = summary.success || 0;
  var failedCount = summary.failed || 0;
  var skippedCount = summary.skipped || 0;

  var tabsHtml = '';
  var tabs = [
    { key: 'all', label: '全部', count: totalItems },
    { key: 'success', label: '成功', count: successCount },
    { key: 'failure', label: '失败', count: failedCount },
    { key: 'skipped', label: '跳过', count: skippedCount }
  ];
  tabs.forEach(function(tab) {
    tabsHtml += '<button class="mob-sheet-tab' + (sheetState.currentTab === tab.key ? ' active' : '') + '" data-sheet-tab="' + tab.key + '">' +
      tab.label + '<span class="count">' + tab.count + '</span></button>';
  });

  sheet.innerHTML =
    '<div class="mob-sheet__title">任务详情 #' + task.id + '</div>' +
    '<div class="mob-sheet__task-header" id="mob-sheet-task-header">' +
      '<div class="task-title">' + esc(task.title || task.source_link || '任务 #' + task.id) + '</div>' +
      '<div class="task-meta">状态: ' + esc(task.status || '-') + ' · 进度: ' + esc(taskCompletedLabel(task)) + '</div>' +
      (activeTransferSummary(task) ? '<div class="task-meta">' + esc(activeTransferSummary(task)) + '</div>' : '') +
    '</div>' +
    '<div class="mob-sheet-tabs" id="mob-sheet-item-tabs">' + tabsHtml + '</div>' +
    '<div id="mob-sheet-item-list"></div>' +
    '<button class="mob-btn mob-btn-muted mob-btn-sm" style="align-self:flex-end;margin-top:4px;" id="mob-sheet-close">关闭</button>';

  bindSheetTabClicks();
  renderSheetItemPage();
  document.getElementById('mob-sheet-close').addEventListener('click', closeSheet);
}

function updateSheetContent(data) {
  var task = data.task || {};
  var summary = data.summary || {};
  var header = document.getElementById('mob-sheet-task-header');
  if (header) {
    header.innerHTML =
      '<div class="task-title">' + esc(task.title || task.source_link || '任务 #' + task.id) + '</div>' +
      '<div class="task-meta">状态: ' + esc(task.status || '-') + ' · 进度: ' + esc(taskCompletedLabel(task)) + '</div>' +
      (activeTransferSummary(task) ? '<div class="task-meta">' + esc(activeTransferSummary(task)) + '</div>' : '');
  }
  var counts = {
    all: summary.total || sheetState.items.length || 0,
    success: summary.success || 0,
    failure: summary.failed || 0,
    skipped: summary.skipped || 0
  };
  document.querySelectorAll('#mob-sheet-item-tabs .mob-sheet-tab').forEach(function(tab) {
    var key = tab.dataset.sheetTab;
    var count = counts[key] || 0;
    var label = key === 'all' ? '全部' : key === 'success' ? '成功' : key === 'failure' ? '失败' : '跳过';
    tab.innerHTML = label + '<span class="count">' + count + '</span>';
  });
  renderSheetItemPage();
}

function closeSheet() {
  var overlay = document.getElementById('mob-sheet-overlay');
  if (overlay) overlay.classList.remove('open');
  sheetState.sheetType = '';
}

function bindSheetTabClicks() {
  var tabs = document.querySelectorAll('#mob-sheet-item-tabs .mob-sheet-tab');
  tabs.forEach(function(tab) {
    tab.addEventListener('click', function() {
      tabs.forEach(function(t) { t.classList.remove('active'); });
      tab.classList.add('active');
      sheetState.currentTab = tab.dataset.sheetTab;
      sheetState.currentPage = 0;
      renderSheetItemPage();
    });
  });
}

function renderSheetItemPage() {
  var container = document.getElementById('mob-sheet-item-list');
  if (!container) return;

  var filtered = sheetState.items;
  if (sheetState.currentTab !== 'all') {
    filtered = sheetState.items.filter(function(item) { return item.status === sheetState.currentTab; });
  }

  var start = sheetState.currentPage * sheetState.pageSize;
  var page = filtered.slice(start, start + sheetState.pageSize);
  sheetState.hasMore = start + sheetState.pageSize < filtered.length;

  if (page.length === 0) {
    container.innerHTML = '<div class="mob-empty">暂无数据</div>';
    return;
  }

  var html = '';
  page.forEach(function(item) {
    var summary = itemTransferSummary(item);
    html += '<div class="mob-item-row">' +
      '<span class="mob-item-row__name">' + esc(item.file_name || item.message_id || '#' + item.id) +
        '<small class="mob-item-row__progress">' + esc(summary) + '</small>' +
      '</span>' +
      '<span class="mob-card__badge ' + (item.status === 'success' ? 'completed' : item.status === 'failure' ? 'failure' : 'pending') + '">' + esc(item.status || '-') + '</span>' +
    '</div>';
  });

  if (sheetState.hasMore) {
    html += '<div style="text-align:center;padding:8px;">' +
      '<button class="mob-btn mob-btn-sm mob-btn-muted" id="mob-sheet-load-more">加载更多</button>' +
    '</div>';
  }

  container.innerHTML = html;

  var loadMoreBtn = document.getElementById('mob-sheet-load-more');
  if (loadMoreBtn) loadMoreBtn.addEventListener('click', function() {
    sheetState.currentPage++;
    renderSheetItemPage();
  });
}

// ---------------------------------------------------------------------------
// Task actions — defined in shared.js; this file only refreshes
// mobile-specific rendering (renderMobTasks/renderMobWatches/showToast)
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------
var settingsRendered = false;
function ensureSettingsForm() {
  if (!settingsRendered) { renderMobSettingsForm(); settingsRendered = true; }
}

function renderMobSettingsForm() {
  if (!window.state || !window.state.settings) return;
  var settings = window.state.settings;
  var model = window.state.settingsModel || {options: {}, selections: {}};
  var glob = settings.global || {};
  var user = settings.user || {};

  // Paths
  var pathFields = document.getElementById('mob-settings-path-fields');
  if (pathFields) pathFields.innerHTML =
    '<label><span>保存目录</span><input name="user.save_directory" value="' + escAttr(user.save_directory || '') + '"></label>' +
    '<label><span>临时目录</span><input name="user.temp_directory" value="' + escAttr(user.temp_directory || '') + '"></label>' +
    '<label><span>会话目录</span><input name="user.session_directory" value="' + escAttr(user.session_directory || '') + '"></label>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">' +
      '<label><span>最大下载</span><input name="user.max_tasks.download" type="number" min="1" value="' + (getSettingLeafKey(user, 'max_tasks.download') || '') + '"></label>' +
      '<label><span>最大上传</span><input name="user.max_tasks.upload" type="number" min="1" value="' + (getSettingLeafKey(user, 'max_tasks.upload') || '') + '"></label>' +
    '</div>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">' +
      '<label><span>下载重试</span><input name="user.max_retries.download" type="number" min="0" value="' + (getSettingLeafKey(user, 'max_retries.download') || '') + '"></label>' +
      '<label><span>上传重试</span><input name="user.max_retries.upload" type="number" min="0" value="' + (getSettingLeafKey(user, 'max_retries.upload') || '') + '"></label>' +
    '</div>' +
    '<label><span>PikPak大小上限(字节)</span><input name="global.target_profiles.pikpak.max_file_size" type="number" min="1" value="' + (getSettingLeafKey(glob, 'target_profiles.pikpak.max_file_size') || '') + '"></label>';

  // Behavior
  var behFields = document.getElementById('mob-settings-behavior-fields');
  if (behFields) behFields.innerHTML =
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">' +
      '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.notice" ' + (glob.notice ? ' checked' : '') + '><span>机器人通知</span></label>' +
      '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="user.is_shutdown"' + (user.is_shutdown ? ' checked' : '') + '><span>退出后关机</span></label>' +
      '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.upload.download_upload"' + (getSettingLeafKey(glob, 'upload.download_upload') ? ' checked' : '') + '><span>受限转发时下载后上传</span></label>' +
      '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.upload.delete"' + (getSettingLeafKey(glob, 'upload.delete') ? ' checked' : '') + '><span>上传完成删除本地文件</span></label>' +
    '</div>' +
    '<label style="margin-top:10px;"><span>下载后上传队列</span><input name="global.upload.pending_limit" type="number" min="1" max="5" value="' + (getSettingLeafKey(glob, 'upload.pending_limit') || '') + '"></label>';

  // Archive
  var archiveFields = document.getElementById('mob-settings-archive-fields');
  if (archiveFields) {
    var arch = getSettingLeafKey(glob, 'target_profiles.pikpak.archive') || {};
    archiveFields.innerHTML =
      '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.target_profiles.pikpak.archive.enable"' + (arch.enable ? ' checked' : '') + '><span>PikPak按来源频道归档</span></label>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">' +
        '<label><span>PikPak rclone remote</span><input name="global.target_profiles.pikpak.archive.remote" value="' + escAttr(arch.remote || '') + '"></label>' +
        '<label><span>入库目录</span><input name="global.target_profiles.pikpak.archive.source_directory" value="' + escAttr(arch.source_directory || '') + '"></label>' +
      '</div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">' +
        '<label><span>归档根目录</span><input name="global.target_profiles.pikpak.archive.root_directory" value="' + escAttr(arch.root_directory || '') + '"></label>' +
        '<label><span>入库轮询秒数</span><input name="global.target_profiles.pikpak.archive.poll_seconds" type="number" min="0" value="' + (arch.poll_seconds || '') + '"></label>' +
      '</div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">' +
        '<label><span>轮询间隔秒数</span><input name="global.target_profiles.pikpak.archive.poll_interval_seconds" type="number" min="0" value="' + (arch.poll_interval_seconds || '') + '"></label>' +
        '<label><span>匹配时间窗口秒数</span><input name="global.target_profiles.pikpak.archive.match_window_seconds" type="number" min="0" value="' + (arch.match_window_seconds || '') + '"></label>' +
      '</div>';
  }

  // Sensitive
  var sensFields = document.getElementById('mob-settings-sensitive-fields');
  if (sensFields) sensFields.innerHTML =
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">' +
      '<label><span>API ID</span><input name="user.api_id" value="' + escAttr(user.api_id || '') + '"></label>' +
      '<label><span>API Hash</span><input name="user.api_hash" type="password" placeholder="已配置"></label>' +
    '</div>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">' +
      '<label><span>Bot Token</span><input name="user.bot_token" type="password" placeholder="已配置"></label>' +
      '<label><span>代理密码</span><input name="user.proxy.password" type="password" placeholder="已配置"></label>' +
    '</div>';

  // Download types
  var dlFields = document.getElementById('mob-settings-download-types-fields');
  if (dlFields) dlFields.innerHTML = renderCheckCards('user.download_type', model.options.download_type || [], selectedDownloadTypes(user), true);

  // Forward types
  var fwFields = document.getElementById('mob-settings-forward-types-fields');
  if (fwFields) fwFields.innerHTML = renderCheckCards('global.forward_type', model.options.forward_type || [], selectedForward(glob), false);

  // Message filter
  var mf = glob.message_filter || {};
  var mfFields = document.getElementById('mob-settings-message-filter-fields');
  if (mfFields) mfFields.innerHTML =
    '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.message_filter.enabled"' + (mf.enabled ? ' checked' : '') + '><span>启用消息过滤</span></label>' +
      '<div style="margin-top:10px;"><span style="font-size:13px;font-weight:500;color:var(--color-text-secondary);">媒体类型</span><span style="font-size:11px;color:var(--color-muted);margin-left:4px;">（勾选 = 允许处理，未勾选的类型将被过滤）</span>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 10px;margin-top:4px;">' + renderCheckCards('global.message_filter.media_types', model.options.message_filter_media_types || [], selectedMediaTypes(glob), false) + '</div>' +
    '</div>' +
    '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;margin-top:10px;"><input type="checkbox" name="global.message_filter.date_range.enabled"' + (getSettingLeafKey(mf, 'date_range.enabled') ? ' checked' : '') + '><span>日期范围过滤</span></label>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">' +
      '<label><span>起始日期</span><input name="global.message_filter.date_range.start_date" type="datetime-local" value="' + escAttr(getSettingLeafKey(mf, 'date_range.start_date') || '') + '"></label>' +
      '<label><span>结束日期</span><input name="global.message_filter.date_range.end_date" type="datetime-local" value="' + escAttr(getSettingLeafKey(mf, 'date_range.end_date') || '') + '"></label>' +
    '</div>' +
    '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;margin-top:10px;"><input type="checkbox" name="global.message_filter.keywords.enabled"' + (getSettingLeafKey(mf, 'keywords.enabled') ? ' checked' : '') + '><span>关键词过滤</span></label>' +
    '<label><span>关键词列表（逗号分隔）</span><input name="global.message_filter.keywords.words" value="' + escAttr(getSettingLeafKey(mf, 'keywords.words') || '') + '" placeholder="广告,推广,赞助"></label>';

  // Exports
  var expFields = document.getElementById('mob-settings-exports-fields');
  if (expFields) {
    var et = glob.export_table || {};
    expFields.innerHTML =
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 10px;">' +
        '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.export_table.link"' + (et.link ? ' checked' : '') + '><span>链接统计表</span></label>' +
        '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.export_table.count"' + (et.count ? ' checked' : '') + '><span>计数统计表</span></label>' +
        '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.export_table.upload"' + (et.upload ? ' checked' : '') + '><span>上传统计表</span></label>' +
      '</div>';
  }
}

function getSettingLeafKey(obj, key) {
  if (!obj) return '';
  var parts = key.split('.');
  var cur = obj;
  for (var i = 0; i < parts.length; i++) { if (cur == null) return ''; cur = cur[parts[i]]; }
  return cur;
}

function selectedForward(glob) {
  var types = getSettingLeafKey(glob, 'forward_type');
  if (!types || typeof types !== 'object') return [];
  return Object.keys(types).filter(function(k) { return types[k]; });
}

function selectedMediaTypes(glob) {
  var types = getSettingLeafKey(glob, 'message_filter.media_types');
  if (!types || typeof types !== 'object') return [];
  return Object.keys(types).filter(function(k) { return types[k]; });
}

function selectedDownloadTypes(user) {
  return Array.isArray(user && user.download_type) ? user.download_type : [];
}

function escAttr(value) { return String(value || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

function renderCheckCards(baseName, types, selected, repeatName) {
  var html = '';
  var selSet = {};
  (selected || []).forEach(function(k) { selSet[k] = true; });
  var options = Array.isArray(types) ? types : Object.keys(types || {}).map(function(key) { return {value: key, label: types[key] || key}; });
  options.forEach(function(option) {
    var key = typeof option === 'string' ? option : option.value;
    var label = typeof option === 'string' ? option : (option.label || option.value);
    html += '<label style="display:flex;align-items:center;gap:6px;font-size:13px;padding:4px 0;">' +
      '<input type="checkbox" name="' + (repeatName ? baseName : baseName + '.' + key) + '" value="' + escAttr(key) + '"' + (selSet[key] ? ' checked' : '') + '>' +
      '<span>' + esc(label || key) + '</span></label>';
  });
  return html || '<span style="font-size:13px;color:var(--color-muted);">无可用选项</span>';
}

// ---------------------------------------------------------------------------
// Operations history
// ---------------------------------------------------------------------------
function mobInitDownloadTypes() {
  var grid = document.getElementById('mob-channel-download-types');
  if (!grid) return;
  var model = (window.state && window.state.settingsModel) || {options: {}};
  var types = model.options.download_type || [];
  var selected = (window.state && window.state.settings && window.state.settings.user && selectedDownloadTypes(window.state.settings.user)) || [];
  var selSet = {};
  selected.forEach(function(k) { selSet[k] = true; });
  var html = '';
  types.forEach(function(option) {
    var key = typeof option === 'string' ? option : option.value;
    var label = typeof option === 'string' ? option : (option.label || option.value);
    html += '<label style="display:flex;align-items:center;gap:6px;font-size:13px;padding:3px 0;">' +
      '<input type="checkbox" name="download_types" value="' + escAttr(key) + '"' + (selSet[key] ? ' checked' : '') + '>' +
      '<span>' + esc(label || key) + '</span></label>';
  });
  grid.innerHTML = html || '<span style="font-size:13px;color:var(--color-muted);">无可用类型</span>';
}

async function loadMobileOperations() {
  var container = document.getElementById('mob-operations-list');
  if (!container) return;
  try {
    var data = await fetchJson('/api/operations?limit=30');
    if (!data || !data.operations || data.operations.length === 0) {
      container.innerHTML = '<div class="mob-empty">暂无操作记录</div>';
      return;
    }
    var html = '';
    data.operations.forEach(function(op) {
      var payload = op.payload || {};
      var isChannelDownload = op.type === 'channel_download';
      var typeLabel = isChannelDownload ? '频道下载' : op.type === 'upload' ? '本地上传' : esc(op.type || '');
      var detail = isChannelDownload ? (payload.chat_link || '-') : (payload.path || op.detail || op.file || '#' + op.id);
      var statusClass = op.status === 'success' ? 'completed' : op.status === 'failure' ? 'failure' : 'pending';
      html += '<div class="mob-card status-' + esc(op.status || 'pending') + '">' +
        '<div class="mob-card__head">' +
          '<span class="mob-card__title">' + esc(detail) + '</span>' +
          '<span class="mob-card__badge ' + statusClass + '">' + typeLabel + '</span>' +
        '</div>' +
        '<div class="mob-card__row"><span class="label">状态</span><span>' + esc(op.status || '-') + '</span></div>' +
        (op.error_message || op.error ? '<div class="mob-card__row"><span class="label">错误</span><span>' + esc(op.error_message || op.error) + '</span></div>' : '') +
        '<div class="mob-card__row"><span class="label">时间</span><span>' + esc(op.created_at || '') + '</span></div>' +
      '</div>';
    });
    container.innerHTML = html;
  } catch (e) {
    container.innerHTML = '<div class="mob-empty">加载失败</div>';
  }
}

// ---------------------------------------------------------------------------
// Records
// ---------------------------------------------------------------------------
const MOBILE_RECORDS_PAGE_SIZE = 50;

async function loadMobileRecords(page) {
  if (page !== undefined) state.recordsPage = page;
  var currentPage = state.recordsPage || 1;
  var container = document.getElementById('mob-records-list');
  var pagEl = document.getElementById('mob-records-pagination');
  var clearBtn = document.getElementById('mob-records-clear-btn');
  if (!container) return;
  try {
    var offset = (currentPage - 1) * MOBILE_RECORDS_PAGE_SIZE;
    var data = await fetchJson('/api/download-records?limit=' + MOBILE_RECORDS_PAGE_SIZE + '&offset=' + offset);
    var records = data && Array.isArray(data.records) ? data.records : [];
    var total = Number(data && data.total || 0);
    var totalPages = Math.max(1, Math.ceil(total / MOBILE_RECORDS_PAGE_SIZE) || 1);
    state.recordsTotal = total;

    if (currentPage > totalPages && total > 0) {
      state.recordsPage = totalPages;
      return loadMobileRecords(totalPages);
    }

    if (clearBtn) clearBtn.disabled = total === 0;

    if (!records.length) {
      container.innerHTML = '<div class="mob-empty" data-i18n="records.empty">还没有下载成功记录。</div>';
      if (pagEl) pagEl.innerHTML = '';
      return;
    }
    var html = '';
    records.forEach(function(r) {
      html += '<div class="mob-card">' +
        '<div class="mob-card__row"><span class="label">频道</span><span>' + esc(r.source_chat_id || r.chat_id || r.chat_title || '-') + '</span></div>' +
        '<div class="mob-card__row"><span class="label">消息</span><span>' + esc(r.source_message_id || r.message_id || '-') + '</span></div>' +
        '<div class="mob-card__row"><span class="label">文件</span><span>' + esc(r.file_name || r.file_path || '-') + '</span></div>' +
        '<div class="mob-card__row"><span class="label">大小</span><span>' + (r.file_size ? formatBytes(r.file_size) : '-') + '</span></div>' +
        '<div class="mob-card__row"><span class="label">时间</span><span>' + esc(r.updated_at || '') + '</span></div>' +
      '</div>';
    });
    container.innerHTML = html;
    if (pagEl) {
      pagEl.innerHTML = renderPaginationBar({
        prefix: 'mob-records',
        page: currentPage,
        pageSize: MOBILE_RECORDS_PAGE_SIZE,
        total: total,
        variant: 'mobile'
      });
      bindPaginationBar('mob-records', currentPage, totalPages, function(newPage) {
        loadMobileRecords(newPage);
      });
    }
  } catch (e) {
    container.innerHTML = '<div class="mob-empty">加载失败</div>';
    if (pagEl) pagEl.innerHTML = '';
  }
}

document.getElementById('mob-records-clear-btn')?.addEventListener('click', async function() {
  if (!confirm(t('records.confirmClear'))) return;
  try {
    var resp = await fetch('/api/download-records', { method: 'DELETE' });
    if (resp.status === 401) { redirectToLoginPage(); return; }
    if (!resp.ok) {
      var data = {};
      try { data = await resp.json(); } catch (e) {}
      throw data;
    }
    state.recordsPage = 1;
    await loadMobileRecords();
  } catch (e) {
    alert(translateApiError(e, 'form.requestFailed'));
  }
});

// ---------------------------------------------------------------------------
// Statistics
// ---------------------------------------------------------------------------
async function loadMobileStatistics() {
  var container = document.getElementById('mob-statistics-list');
  if (!container) return;
  try {
    var data = await fetchJson('/api/statistics');
    var tables = data && data.tables ? data.tables : null;
    if (!tables) {
      container.innerHTML = '<div class="mob-empty">暂无统计数据</div>';
      return;
    }
    var rows = [
      { key: 'link', label: '链接统计表' },
      { key: 'count', label: '计数统计表' },
      { key: 'upload', label: '上传统计表' }
    ];
    var html = '';
    rows.forEach(function(row) {
      var t = tables[row.key] || {};
      html += '<div class="mob-card">' +
        '<div class="mob-card__head"><span class="mob-card__title">' + esc(row.label) + '</span></div>' +
        '<div class="mob-card__row"><span class="label">行数</span><span>' + (t.row_count || t.rows || 0) + '</span></div>' +
        '<div class="mob-card__row"><span class="label">可用</span><span>' + (t.available ? '是' : '否') + '</span></div>' +
      '</div>';
    });
    container.innerHTML = html || '<div class="mob-empty">暂无统计数据</div>';
  } catch (e) {
    container.innerHTML = '<div class="mob-empty">加载失败</div>';
  }
}

// ---------------------------------------------------------------------------
// Media management
// ---------------------------------------------------------------------------
async function loadMediaMobile() {
  var container = document.getElementById('mob-media-result');
  if (!container) return;
  container.innerHTML = '<div class="mob-empty">扫描中...</div>';
  try {
    var data = await fetchJson('/api/media/scan');
    if (!data) { container.innerHTML = '<div class="mob-empty">扫描失败</div>'; return; }
    var transferItems = ((data.transfer_items || {}).items || []);
    var orphanFiles = ((data.orphan_files || {}).files || []);

    var html = '<div style="font-size:13px;">' +
      '<div style="display:flex;gap:16px;flex-wrap:wrap;padding:12px;background:var(--color-surface-muted);border-radius:8px;margin-bottom:12px;">' +
        '<div><strong>总文件</strong><br>' + (data.total_count || 0) + '</div>' +
        '<div><strong>总大小</strong><br>' + formatBytes(data.total_size || 0) + '</div>' +
        '<div><strong>遗留文件</strong><br>' + orphanFiles.length + ' 个</div>' +
      '</div></div>';

    if (transferItems.length > 0) {
      html += '<div style="margin-top:12px;"><strong style="font-size:14px;">转存任务文件</strong></div>';
      transferItems.forEach(function(item) {
        html += '<div style="display:flex;justify-content:space-between;padding:6px 0;font-size:13px;border-bottom:1px solid var(--color-line);">' +
          '<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + esc(item.file_name || item.local_path || '') + '</span>' +
          '<span style="flex-shrink:0;margin-left:8px;">' + formatBytes(item.file_size || 0) + '</span>' +
        '</div>';
      });
    }

    if (orphanFiles.length > 0) {
      html += '<div style="margin-top:12px;"><strong style="font-size:14px;">遗留文件</strong></div>';
      orphanFiles.forEach(function(f) {
        html += '<div style="display:flex;justify-content:space-between;padding:6px 0;font-size:13px;border-bottom:1px solid var(--color-line);">' +
          '<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + esc(f.path || '') + '</span>' +
          '<span style="flex-shrink:0;margin-left:8px;">' + formatBytes(f.size || 0) + '</span>' +
        '</div>';
      });
    }

    if (!transferItems.length && !orphanFiles.length) {
      html += '<div class="mob-empty">没有可清理文件</div>';
    } else {
      html += '<div class="mob-empty">请在桌面端选择并执行清理</div>';
    }

    container.innerHTML = html;
  } catch (e) {
    container.innerHTML = '<div class="mob-empty">加载失败: ' + esc(e.message || '') + '</div>';
  }
}

// ---------------------------------------------------------------------------
// Event bindings (init)
// ---------------------------------------------------------------------------
(function() {
  // Tab bar clicks
  var tabbar = document.getElementById('mob-tabbar');
  if (tabbar) {
    tabbar.querySelectorAll('.mob-tab').forEach(function(tab) {
      tab.addEventListener('click', function() {
        mobSwitchView(tab.dataset.mobTab);
      });
    });
  }

  // Top bar back button
  var backBtn = document.getElementById('mob-topbar-back');
  if (backBtn) {
    backBtn.addEventListener('click', function() {
      mobNavigateBack();
    });
  }

  // Profile menu items
  var menu = document.getElementById('mob-profile-menu');
  if (menu) {
    menu.querySelectorAll('[data-profile-nav]').forEach(function(item) {
      item.addEventListener('click', function() {
        mobNavigateTo(item.dataset.profileNav);
      });
    });
  }

  // Language button (toggle zh/en)
  var langBtn = document.getElementById('mob-btn-language');
  if (langBtn) {
    langBtn.addEventListener('click', function() {
      var current = (window.state && window.state.lang) || 'zh';
      var next = current === 'zh' ? 'en' : 'zh';
      if (window.state) window.state.lang = next;
      localStorage.setItem('trmd-lang', next);
      var label = document.getElementById('mob-lang-label');
      if (label) label.textContent = next === 'zh' ? '中文' : 'English';
      if (typeof setLang === 'function') setLang(next);
      showToast(next === 'zh' ? '已切换为中文' : 'Switched to English');
      loadCurrentView();
    });
  }

  // Logout button
  var logoutBtn = document.getElementById('mob-btn-logout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async function() {
      if (!confirm('确认退出登录？')) return;
      try {
        await fetch('/api/auth/logout', { method: 'POST' });
        stopPolling();
        if (window.state) { window.state.tasks = []; window.state.watches = []; }
        document.querySelectorAll('.mob-view,.mob-subpage').forEach(function(v) { v.classList.remove('active'); });
        var transfers = document.getElementById('mob-view-transfers');
        if (transfers) transfers.classList.add('active');
        mobSwitchView('transfers');
        checkAuthStatus();
      } catch (e) { showToast('退出失败'); }
    });
  }

  // Collapse toggles (delegated only — avoid double-fire with inline handlers)
  document.addEventListener('click', function(e) {
    var head = e.target.closest('.mob-collapse__head');
    if (head && !e.target.closest('button, input, select, textarea, label')) {
      toggleCollapse(head);
    }
  });

  // Sheet overlay close
  var sheetOverlay = document.getElementById('mob-sheet-overlay');
  if (sheetOverlay) {
    sheetOverlay.addEventListener('click', function(e) {
      if (e.target === sheetOverlay) closeSheet();
    });
  }

  // Watch type toggle
  var watchTypeSelect = document.getElementById('mob-watch-type');
  if (watchTypeSelect) {
    watchTypeSelect.addEventListener('change', function() {
      var val = watchTypeSelect.value;
      var targetGroup = document.getElementById('mob-watch-target-group');
      var commentGroup = document.getElementById('mob-watch-comment-group');
      var sourceLabel = document.getElementById('mob-watch-source-label');
      var sourceTextarea = document.querySelector('#mob-watch-source-group textarea[name="source_links"]');
      var sourceInput = document.querySelector('#mob-watch-source-group input[name="source_link"]');

      if (val === 'download') {
        if (targetGroup) targetGroup.classList.add('hidden');
        if (commentGroup) commentGroup.classList.add('hidden');
        if (sourceLabel) sourceLabel.querySelector('span').textContent = '来源频道';
        if (sourceTextarea) { sourceTextarea.classList.remove('hidden'); sourceTextarea.required = true; }
        if (sourceInput) { sourceInput.classList.add('hidden'); sourceInput.required = false; }
      } else {
        if (targetGroup) targetGroup.classList.remove('hidden');
        if (commentGroup) commentGroup.classList.remove('hidden');
        if (sourceLabel) sourceLabel.querySelector('span').textContent = '来源频道';
        if (sourceTextarea) { sourceTextarea.classList.add('hidden'); sourceTextarea.required = false; }
        if (sourceInput) { sourceInput.classList.remove('hidden'); sourceInput.required = true; }
      }
    });
  }

  // Transfer form
  var transferForm = document.getElementById('mob-transfer-form');
  if (transferForm) {
    transferForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      var formData = new FormData(transferForm);
      var payload = {};
      formData.forEach(function(v, k) { payload[k] = v; });
      if (payload.start_id) payload.start_id = Number(payload.start_id);
      if (payload.end_id) payload.end_id = Number(payload.end_id);
      payload.include_comment = transferForm.querySelector('[name="include_comment"]').checked;
      var notice = document.getElementById('mob-form-notice');
      try {
        await postJson('/api/tasks', payload);
        if (notice) { notice.classList.remove('hidden'); notice.textContent = '创建成功'; notice.style.color = 'var(--color-success)'; }
        transferForm.reset();
        setTimeout(function() { if (notice) notice.classList.add('hidden'); loadMobileTasks(); }, 1000);
      } catch (e) {
        if (notice) { notice.classList.remove('hidden'); notice.textContent = '创建失败: ' + (e.message || ''); notice.style.color = 'var(--color-danger)'; }
      }
    });
  }

  // Watch form
  var watchForm = document.getElementById('mob-watch-form');
  if (watchForm) {
    watchForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      var formData = new FormData(watchForm);
      var payload = { type: formData.get('type') };
      if (payload.type === 'download') {
        payload.source_links = (formData.get('source_links') || '').split('\n').map(function(s) { return s.trim(); }).filter(Boolean);
        payload.include_comment = watchForm.querySelector('[name="include_comment"]') ? watchForm.querySelector('[name="include_comment"]').checked : false;
      } else {
        payload.source_link = formData.get('source_link');
        payload.target_link = formData.get('target_link');
        payload.include_comment = watchForm.querySelector('[name="include_comment"]') ? watchForm.querySelector('[name="include_comment"]').checked : false;
      }
      var notice = document.getElementById('mob-watch-notice');
      try {
        await postJson('/api/watches', payload);
        if (notice) { notice.classList.remove('hidden'); notice.textContent = '创建成功'; notice.style.color = 'var(--color-success)'; }
        watchForm.reset();
        setTimeout(function() { if (notice) notice.classList.add('hidden'); loadMobileWatches(); }, 1000);
      } catch (e) {
        if (notice) { notice.classList.remove('hidden'); notice.textContent = '创建失败: ' + (e.message || ''); notice.style.color = 'var(--color-danger)'; }
      }
    });
  }

  // Channel download form
  var channelForm = document.getElementById('mob-channel-form');
  if (channelForm) {
    channelForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      var formData = new FormData(channelForm);
      var payload = { chat_link: formData.get('chat_link') };
      if (formData.get('start_date')) payload.start_date = formData.get('start_date');
      if (formData.get('end_date')) payload.end_date = formData.get('end_date');
      if (formData.get('keywords')) payload.keywords = formData.get('keywords');
      payload.include_comment = channelForm.querySelector('[name="include_comment"]').checked;
      var checkboxes = channelForm.querySelectorAll('[name="download_types"]:checked');
      if (checkboxes.length > 0) payload.download_type = Array.from(checkboxes).map(function(cb) { return cb.value; });

      var notice = document.getElementById('mob-channel-notice');
      try {
        await postJson('/api/channel-downloads', payload);
        if (notice) { notice.classList.remove('hidden'); notice.textContent = '创建成功'; notice.style.color = 'var(--color-success)'; }
        channelForm.reset();
        setTimeout(function() { if (notice) notice.classList.add('hidden'); loadMobileOperations(); }, 1000);
      } catch (e) {
        if (notice) { notice.classList.remove('hidden'); notice.textContent = '创建失败: ' + (e.message || ''); notice.style.color = 'var(--color-danger)'; }
      }
    });
  }

  // Upload form
  var uploadForm = document.getElementById('mob-upload-form');
  if (uploadForm) {
    uploadForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      var formData = new FormData(uploadForm);
      var payload = { path: formData.get('path'), target_link: formData.get('target_link'), recursive: uploadForm.querySelector('[name="recursive"]').checked };
      var notice = document.getElementById('mob-upload-notice');
      try {
        await postJson('/api/uploads', payload);
        if (notice) { notice.classList.remove('hidden'); notice.textContent = '创建成功'; notice.style.color = 'var(--color-success)'; }
        uploadForm.reset();
        setTimeout(function() { if (notice) notice.classList.add('hidden'); loadMobileOperations(); }, 1000);
      } catch (e) {
        if (notice) { notice.classList.remove('hidden'); notice.textContent = '创建失败: ' + (e.message || ''); notice.style.color = 'var(--color-danger)'; }
      }
    });
  }

  // Settings save
  var saveBtn = document.getElementById('mob-save-settings');
  if (saveBtn) {
    saveBtn.addEventListener('click', async function() {
      var notice = document.getElementById('mob-settings-notice');
      var settingsContainer = document.getElementById('mob-subpage-settings');
      if (!settingsContainer) return;

      // Collect form data from all inputs in settings subpage
      var inputs = settingsContainer.querySelectorAll('input[name], select[name]');
      var payload = {};
      var downloadTypes = Array.from(settingsContainer.querySelectorAll('input[name="user.download_type"]:checked')).map(function(input) { return input.value; });
      payload.user = payload.user || {};
      payload.user.download_type = downloadTypes;
      inputs.forEach(function(input) {
        if (input.name === 'user.download_type') return;
        var keys = input.name.split('.');
        var cur = payload;
        for (var i = 0; i < keys.length - 1; i++) {
          if (!cur[keys[i]]) cur[keys[i]] = {};
          cur = cur[keys[i]];
        }
        var lastKey = keys[keys.length - 1];
        if (input.type === 'checkbox') {
          cur[lastKey] = input.checked;
        } else if (input.type === 'number') {
          cur[lastKey] = input.value !== '' ? Number(input.value) : undefined;
        } else {
          cur[lastKey] = input.value || undefined;
        }
      });

      // Clean undefined values
      function clean(obj) {
        Object.keys(obj).forEach(function(k) {
          if (obj[k] === undefined) delete obj[k];
          else if (typeof obj[k] === 'object' && obj[k] !== null) clean(obj[k]);
        });
      }
      clean(payload);

      try {
        await postJson('/api/settings', payload, 'PATCH');
        if (notice) { notice.classList.remove('hidden'); notice.textContent = '保存成功'; notice.style.color = 'var(--color-success)'; }
        setTimeout(function() { if (notice) notice.classList.add('hidden'); }, 2000);
      } catch (e) {
        if (notice) { notice.classList.remove('hidden'); notice.textContent = '保存失败: ' + (e.message || ''); notice.style.color = 'var(--color-danger)'; }
      }
    });
  }

  // Media scan button
  var mediaBtn = document.getElementById('mob-media-scan-btn');
  if (mediaBtn) mediaBtn.addEventListener('click', loadMediaMobile);

  // Kickoff
  checkAuthStatus();
})();
</script>
</body>
</html>"""

LOGIN_PAGE_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TRMD · 登录</title>
<style>@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 300;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/cc762462ea67.woff2) format('woff2');
  unicode-range: U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 300;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d5bab8e28732.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 300;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d8e4fe0452aa.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 400;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/cc762462ea67.woff2) format('woff2');
  unicode-range: U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 400;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d5bab8e28732.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 400;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d8e4fe0452aa.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 500;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/cc762462ea67.woff2) format('woff2');
  unicode-range: U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 500;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d5bab8e28732.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 500;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d8e4fe0452aa.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 600;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/cc762462ea67.woff2) format('woff2');
  unicode-range: U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 600;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d5bab8e28732.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 600;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d8e4fe0452aa.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 700;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/cc762462ea67.woff2) format('woff2');
  unicode-range: U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 700;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d5bab8e28732.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 700;
  font-stretch: 100%;
  font-display: swap;
  src: url(/fonts/d8e4fe0452aa.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url(/fonts/0b1fcab42c18.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url(/fonts/7d93459d8658.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 500;
  font-display: swap;
  src: url(/fonts/af5fda16a191.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 500;
  font-display: swap;
  src: url(/fonts/cd36de204aca.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url(/fonts/bb1f2d582e7f.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url(/fonts/f4e80d9dfd37.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 700;
  font-display: swap;
  src: url(/fonts/ccfd87f69ef0.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 700;
  font-display: swap;
  src: url(/fonts/9338e65fc077.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 800;
  font-display: swap;
  src: url(/fonts/a72eccfa6cfa.woff2) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Poppins';
  font-style: normal;
  font-weight: 800;
  font-display: swap;
  src: url(/fonts/60bf0aba6526.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}</style>
<style>/*! tailwindcss v4.1.18 | MIT License | https://tailwindcss.com */
@layer properties{@supports (((-webkit-hyphens:none)) and (not (margin-trim:inline))) or ((-moz-orient:inline) and (not (color:rgb(from red r g b)))){*,:before,:after,::backdrop{--tw-rotate-x:initial;--tw-rotate-y:initial;--tw-rotate-z:initial;--tw-skew-x:initial;--tw-skew-y:initial;--tw-border-style:solid;--tw-leading:initial;--tw-font-weight:initial;--tw-tracking:initial;--tw-shadow:0 0 #0000;--tw-shadow-color:initial;--tw-shadow-alpha:100%;--tw-inset-shadow:0 0 #0000;--tw-inset-shadow-color:initial;--tw-inset-shadow-alpha:100%;--tw-ring-color:initial;--tw-ring-shadow:0 0 #0000;--tw-inset-ring-color:initial;--tw-inset-ring-shadow:0 0 #0000;--tw-ring-inset:initial;--tw-ring-offset-width:0px;--tw-ring-offset-color:#fff;--tw-ring-offset-shadow:0 0 #0000;--tw-outline-style:solid;--tw-blur:initial;--tw-brightness:initial;--tw-contrast:initial;--tw-grayscale:initial;--tw-hue-rotate:initial;--tw-invert:initial;--tw-opacity:initial;--tw-saturate:initial;--tw-sepia:initial;--tw-drop-shadow:initial;--tw-drop-shadow-color:initial;--tw-drop-shadow-alpha:100%;--tw-drop-shadow-size:initial;--tw-backdrop-blur:initial;--tw-backdrop-brightness:initial;--tw-backdrop-contrast:initial;--tw-backdrop-grayscale:initial;--tw-backdrop-hue-rotate:initial;--tw-backdrop-invert:initial;--tw-backdrop-opacity:initial;--tw-backdrop-saturate:initial;--tw-backdrop-sepia:initial;--tw-duration:initial}}}@layer theme{:root,:host{--font-sans:ui-sans-serif,system-ui,sans-serif,"Apple Color Emoji","Segoe UI Emoji","Segoe UI Symbol","Noto Color Emoji";--font-mono:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono","Courier New",monospace;--color-red-200:oklch(88.5% .062 18.334);--color-red-300:oklch(80.8% .114 19.571);--color-orange-50:oklch(98% .016 73.684);--color-slate-100:oklch(96.8% .007 247.896);--color-slate-300:oklch(86.9% .022 252.894);--color-slate-500:oklch(55.4% .046 257.417);--color-black:#000;--color-white:#fff;--spacing:.25rem;--text-xs:.75rem;--text-xs--line-height:calc(1/.75);--text-sm:.875rem;--text-sm--line-height:calc(1.25/.875);--text-base:1rem;--text-base--line-height:calc(1.5/1);--text-lg:1.125rem;--text-lg--line-height:calc(1.75/1.125);--text-xl:1.25rem;--text-xl--line-height:calc(1.75/1.25);--text-2xl:1.5rem;--text-2xl--line-height:calc(2/1.5);--font-weight-normal:400;--font-weight-medium:500;--font-weight-semibold:600;--font-weight-bold:700;--font-weight-extrabold:800;--leading-tight:1.25;--leading-relaxed:1.625;--radius-sm:8px;--radius-md:.375rem;--radius-lg:.5rem;--radius-xl:.75rem;--radius-2xl:1rem;--animate-spin:spin 1s linear infinite;--default-transition-duration:.15s;--default-transition-timing-function:cubic-bezier(.4,0,.2,1);--default-font-family:var(--font-sans);--default-mono-font-family:var(--font-mono);--color-primary:#2563eb;--color-primary-light:#3b82f6;--color-primary-soft:#eff6ff;--color-primary-ghost:#dbeafe;--color-primary-dark:#1d4ed8;--color-bg:#f0f4ff;--color-surface:#fff;--color-surface-alt:#f8fafc;--color-surface-hover:#f1f5f9;--color-surface-muted:#f0f3f5;--color-text:#1e293b;--color-text-secondary:#475569;--color-muted:#94a3b8;--color-line:#e2e8f0;--color-line-light:#f1f5f9;--color-success:#10b981;--color-success-bg:#ecfdf5;--color-warning:#f59e0b;--color-warning-bg:#fffbeb;--color-danger:#ef4444;--color-danger-bg:#fef2f2;--color-cta:#f97316;--font-heading:"Poppins","PingFang SC","Microsoft YaHei","Noto Sans SC",ui-sans-serif,system-ui,sans-serif;--font-body:"Open Sans","PingFang SC","Microsoft YaHei","Noto Sans SC",ui-sans-serif,system-ui,sans-serif;--font-mob:"Inter","PingFang SC","Microsoft YaHei","Noto Sans SC",ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;--tab-height:56px;--topbar-height:48px}}@layer base{*,:after,:before,::backdrop{box-sizing:border-box;border:0 solid;margin:0;padding:0}::file-selector-button{box-sizing:border-box;border:0 solid;margin:0;padding:0}html,:host{-webkit-text-size-adjust:100%;tab-size:4;line-height:1.5;font-family:var(--default-font-family,ui-sans-serif,system-ui,sans-serif,"Apple Color Emoji","Segoe UI Emoji","Segoe UI Symbol","Noto Color Emoji");font-feature-settings:var(--default-font-feature-settings,normal);font-variation-settings:var(--default-font-variation-settings,normal);-webkit-tap-highlight-color:transparent}hr{height:0;color:inherit;border-top-width:1px}abbr:where([title]){-webkit-text-decoration:underline dotted;text-decoration:underline dotted}h1,h2,h3,h4,h5,h6{font-size:inherit;font-weight:inherit}a{color:inherit;-webkit-text-decoration:inherit;-webkit-text-decoration:inherit;-webkit-text-decoration:inherit;text-decoration:inherit}b,strong{font-weight:bolder}code,kbd,samp,pre{font-family:var(--default-mono-font-family,ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono","Courier New",monospace);font-feature-settings:var(--default-mono-font-feature-settings,normal);font-variation-settings:var(--default-mono-font-variation-settings,normal);font-size:1em}small{font-size:80%}sub,sup{vertical-align:baseline;font-size:75%;line-height:0;position:relative}sub{bottom:-.25em}sup{top:-.5em}table{text-indent:0;border-color:inherit;border-collapse:collapse}:-moz-focusring{outline:auto}progress{vertical-align:baseline}summary{display:list-item}ol,ul,menu{list-style:none}img,svg,video,canvas,audio,iframe,embed,object{vertical-align:middle;display:block}img,video{max-width:100%;height:auto}button,input,select,optgroup,textarea{font:inherit;font-feature-settings:inherit;font-variation-settings:inherit;letter-spacing:inherit;color:inherit;opacity:1;background-color:#0000;border-radius:0}::file-selector-button{font:inherit;font-feature-settings:inherit;font-variation-settings:inherit;letter-spacing:inherit;color:inherit;opacity:1;background-color:#0000;border-radius:0}:where(select:is([multiple],[size])) optgroup{font-weight:bolder}:where(select:is([multiple],[size])) optgroup option{padding-inline-start:20px}::file-selector-button{margin-inline-end:4px}::placeholder{opacity:1}@supports (not ((-webkit-appearance:-apple-pay-button))) or (contain-intrinsic-size:1px){::placeholder{color:currentColor}@supports (color:color-mix(in lab, red, red)){::placeholder{color:color-mix(in oklab,currentcolor 50%,transparent)}}}textarea{resize:vertical}::-webkit-search-decoration{-webkit-appearance:none}::-webkit-date-and-time-value{min-height:1lh;text-align:inherit}::-webkit-datetime-edit{display:inline-flex}::-webkit-datetime-edit-fields-wrapper{padding:0}::-webkit-datetime-edit{padding-block:0}::-webkit-datetime-edit-year-field{padding-block:0}::-webkit-datetime-edit-month-field{padding-block:0}::-webkit-datetime-edit-day-field{padding-block:0}::-webkit-datetime-edit-hour-field{padding-block:0}::-webkit-datetime-edit-minute-field{padding-block:0}::-webkit-datetime-edit-second-field{padding-block:0}::-webkit-datetime-edit-millisecond-field{padding-block:0}::-webkit-datetime-edit-meridiem-field{padding-block:0}::-webkit-calendar-picker-indicator{line-height:1}:-moz-ui-invalid{box-shadow:none}button,input:where([type=button],[type=reset],[type=submit]){appearance:button}::file-selector-button{appearance:button}::-webkit-inner-spin-button{height:auto}::-webkit-outer-spin-button{height:auto}[hidden]:where(:not([hidden=until-found])){display:none!important}:root{--safe-bottom:env(safe-area-inset-bottom,0px)}html{font-family:var(--font-body);color:var(--color-text);background:var(--color-bg);font-size:15px;line-height:1.5}body{min-height:100vh;display:flex}button,input,select,textarea{font-family:inherit;font-size:inherit}button{cursor:pointer}button:disabled{cursor:not-allowed;opacity:.55}}@layer components{.sidebar{top:calc(var(--spacing)*0);z-index:50;border-right-style:var(--tw-border-style);border-right-width:1px;border-color:var(--color-line);background-color:var(--color-white);width:250px;height:100vh;padding-inline:calc(var(--spacing)*4);padding-block:calc(var(--spacing)*6);flex-direction:column;display:flex;position:sticky}.sidebar-brand{margin-bottom:calc(var(--spacing)*3);align-items:center;gap:calc(var(--spacing)*3);border-bottom-style:var(--tw-border-style);border-bottom-width:1px;border-color:var(--color-line);padding-bottom:calc(var(--spacing)*5);display:flex}.sidebar-brand-mark{height:calc(var(--spacing)*10);width:calc(var(--spacing)*10);font-size:var(--text-lg);line-height:var(--tw-leading,var(--text-lg--line-height));--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold);color:var(--color-white);background:linear-gradient(135deg,var(--color-primary),var(--color-primary-light));font-family:var(--font-heading);border-radius:10px;justify-content:center;align-items:center;display:flex;box-shadow:0 4px 10px #2563eb4d}.sidebar-nav-section{flex:1;overflow-y:auto}.sidebar-nav-label{padding-inline:calc(var(--spacing)*2.5);padding-top:calc(var(--spacing)*4);padding-bottom:calc(var(--spacing)*2);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);--tw-tracking:.08em;letter-spacing:.08em;color:var(--color-muted);text-transform:uppercase}.sidebar-nav-item{cursor:pointer;align-items:center;gap:calc(var(--spacing)*2.5);border-style:var(--tw-border-style);width:100%;padding-inline:calc(var(--spacing)*3);padding-block:calc(var(--spacing)*2.5);text-align:left;font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));--tw-font-weight:var(--font-weight-medium);font-weight:var(--font-weight-medium);color:var(--color-text-secondary);transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;background-color:#0000;border-width:0;border-radius:8px;font-family:inherit;transition-duration:.15s;display:flex}.sidebar-nav-item:hover{background-color:var(--color-primary-soft);color:var(--color-primary)}.sidebar-nav-item.active{background-color:var(--color-primary-soft);--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-primary)}.sidebar-nav-item svg{flex-shrink:0;width:18px;height:18px}.sidebar-nav-badge{background-color:var(--color-primary-ghost);padding-inline:calc(var(--spacing)*2);padding-block:calc(var(--spacing)*.5);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold);color:var(--color-primary);border-radius:3.40282e38px;margin-left:auto}.sidebar-footer{margin-top:calc(var(--spacing)*2);gap:calc(var(--spacing)*1.5);border-top-style:var(--tw-border-style);border-top-width:1px;border-color:var(--color-line);padding-top:calc(var(--spacing)*4);flex-direction:column;display:flex}.sidebar-footer-info{align-items:center;gap:calc(var(--spacing)*2);padding-inline:calc(var(--spacing)*2);padding-block:calc(var(--spacing)*1);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-text-secondary);display:flex}.sidebar-status-dot{height:calc(var(--spacing)*2);width:calc(var(--spacing)*2);background:var(--color-success);border-radius:3.40282e38px;flex-shrink:0;box-shadow:0 0 0 3px #10b98133}.sidebar-version{padding-inline:calc(var(--spacing)*2);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));color:var(--color-muted);opacity:.7}.main-content{min-width:calc(var(--spacing)*0);gap:calc(var(--spacing)*6);padding:calc(var(--spacing)*7);flex-direction:column;flex:1;display:flex}.topbar{justify-content:space-between;align-items:flex-start;gap:calc(var(--spacing)*4);display:flex}.topbar h1{font-size:var(--text-xl);line-height:var(--tw-leading,var(--text-xl--line-height));--tw-leading:var(--leading-tight);line-height:var(--leading-tight);--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold);color:var(--color-text);font-family:var(--font-heading)}.topbar p{margin-top:calc(var(--spacing)*1);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-muted)}.btn{cursor:pointer;align-items:center;gap:calc(var(--spacing)*1.5);border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);padding-inline:calc(var(--spacing)*4);padding-block:calc(var(--spacing)*2);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));--tw-font-weight:var(--font-weight-medium);font-weight:var(--font-weight-medium);white-space:nowrap;color:var(--color-text);transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;border-radius:6px;font-family:inherit;transition-duration:.15s;display:inline-flex}.btn:hover{border-color:var(--color-primary-light);background-color:var(--color-primary-soft)}.btn svg{height:calc(var(--spacing)*4);width:calc(var(--spacing)*4);flex-shrink:0}.btn-primary{border-color:var(--color-primary);background-color:var(--color-primary);--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-white)}.btn-primary:hover{border-color:var(--color-primary-dark);background-color:var(--color-primary-dark);color:var(--color-white)}.btn-danger{border-color:var(--color-red-200);color:var(--color-danger)}.btn-danger:hover{border-color:var(--color-danger);background-color:var(--color-danger-bg);color:var(--color-danger)}.btn-sm{padding-inline:calc(var(--spacing)*2.5);padding-block:calc(var(--spacing)*1);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height))}.btn-icon{width:34px;height:34px;padding:calc(var(--spacing)*0);justify-content:center}.stat-grid{gap:calc(var(--spacing)*4);grid-template-columns:repeat(4,minmax(0,1fr));display:grid}.stat-card{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);--tw-shadow:0 1px 3px 0 var(--tw-shadow-color,#0000001a),0 1px 2px -1px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow);transition-property:box-shadow;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.2s;border-radius:12px;justify-content:space-between;align-items:flex-start;padding:18px;transition-duration:.2s;display:flex}.stat-card:hover{border-color:var(--color-primary-ghost);--tw-shadow:0 4px 6px -1px var(--tw-shadow-color,#0000001a),0 2px 4px -2px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow)}.stat-card-icon{height:calc(var(--spacing)*10);width:calc(var(--spacing)*10);border-radius:8px;flex-shrink:0;justify-content:center;align-items:center;display:flex}.stat-card-icon.blue{background-color:var(--color-primary-soft);color:var(--color-primary)}.stat-card-icon.green{background-color:var(--color-success-bg);color:var(--color-success)}.stat-card-icon.orange{background-color:var(--color-orange-50);color:var(--color-cta)}.stat-card-icon.red{background-color:var(--color-danger-bg);color:var(--color-danger)}.stat-card-icon svg{height:calc(var(--spacing)*5);width:calc(var(--spacing)*5)}.stat-card-value{text-align:right;font-size:var(--text-xl);line-height:var(--tw-leading,var(--text-xl--line-height));--tw-leading:var(--leading-tight);line-height:var(--leading-tight);--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold);color:var(--color-text);font-family:var(--font-heading)}.stat-card-label{margin-top:calc(var(--spacing)*1);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-medium);font-weight:var(--font-weight-medium);color:var(--color-muted)}.panel{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);--tw-shadow:0 1px 3px 0 var(--tw-shadow-color,#0000001a),0 1px 2px -1px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow);border-radius:12px;flex-direction:column;display:flex;overflow:hidden}.panel-header{border-bottom-style:var(--tw-border-style);border-bottom-width:1px;border-color:var(--color-line);background-color:var(--color-surface-alt);padding-inline:18px;padding-block:calc(var(--spacing)*3.5);justify-content:space-between;align-items:center;display:flex}.panel-header h3{font-size:var(--text-base);line-height:var(--tw-leading,var(--text-base--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-text);font-family:var(--font-heading)}.panel-body{flex:1;padding:18px;overflow-y:auto}.panel-tabs{gap:calc(var(--spacing)*.5);display:flex}.panel-tab{cursor:pointer;border-style:var(--tw-border-style);padding-inline:calc(var(--spacing)*2.5);padding-block:calc(var(--spacing)*1);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-medium);font-weight:var(--font-weight-medium);color:var(--color-text-secondary);transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.1s;background-color:#0000;border-width:0;border-radius:.25rem;font-family:inherit;transition-duration:.1s}.panel-tab:hover{background-color:var(--color-primary-soft);color:var(--color-primary)}.panel-tab.active{background-color:var(--color-primary-soft);--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-primary)}.form-group{margin-bottom:calc(var(--spacing)*3.5)}.form-label{margin-bottom:calc(var(--spacing)*1.5);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);--tw-tracking:.04em;letter-spacing:.04em;color:var(--color-muted);text-transform:uppercase;display:block}.form-input,.form-select{height:calc(var(--spacing)*10);border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);width:100%;padding-inline:calc(var(--spacing)*3);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-text);transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;--tw-outline-style:none;border-radius:6px;outline-style:none;font-family:inherit;transition-duration:.15s}.form-input:focus,.form-select:focus{border-color:var(--color-primary);box-shadow:0 0 0 3px #2563eb1f}.watch-download-sources{resize:vertical;min-height:124px}.download-upload-align-spacer{margin-bottom:calc(var(--spacing)*3.5);border-style:var(--tw-border-style);--tw-border-style:dashed;border-style:dashed;border-width:1px;border-color:var(--color-line);background-color:var(--color-surface-alt);min-height:88px;padding-inline:calc(var(--spacing)*4);text-align:center;font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-muted);border-radius:8px;justify-content:center;align-items:center;display:flex}@media (min-width:64rem){.download-upload-align-spacer{min-height:184px}}.form-row{gap:calc(var(--spacing)*2.5);grid-template-columns:repeat(2,minmax(0,1fr));display:grid}.form-submit{margin-top:calc(var(--spacing)*1.5);height:calc(var(--spacing)*10);cursor:pointer;justify-content:center;align-items:center;gap:calc(var(--spacing)*1.5);border-style:var(--tw-border-style);background-color:var(--color-primary);width:100%;font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-white);transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;border-width:0;border-radius:6px;font-family:inherit;transition-duration:.15s;display:flex}.form-submit:hover{background-color:var(--color-primary-dark)}.data-table{border-collapse:collapse;width:100%;font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height))}.data-table thead th{top:calc(var(--spacing)*0);border-bottom-style:var(--tw-border-style);border-bottom-width:2px;border-color:var(--color-line);background-color:var(--color-surface-alt);padding-inline:calc(var(--spacing)*3);padding-block:calc(var(--spacing)*2.5);text-align:center;font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);--tw-tracking:.05em;letter-spacing:.05em;white-space:nowrap;color:var(--color-muted);text-transform:uppercase;position:sticky}.data-table tbody td{border-bottom-style:var(--tw-border-style);border-bottom-width:1px;border-color:var(--color-line-light);padding-inline:calc(var(--spacing)*3);padding-block:calc(var(--spacing)*2.5);text-align:center;vertical-align:middle;font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height))}.table-actions{justify-content:center}.data-table tbody tr{cursor:pointer;transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:75ms;transition-duration:75ms}.data-table tbody tr:hover{background-color:var(--color-surface-hover)}.data-table tbody tr.selected{background-color:var(--color-primary-soft)}.task-items-table{table-layout:fixed;min-width:840px}.task-items-table .task-item-col-file{width:34%}.task-items-table .task-item-col-size{width:112px}.task-items-table .task-item-col-progress,.task-items-table .task-item-col-source{width:220px}.task-items-table .task-item-col-status{width:118px}.task-items-table th,.task-items-table td{white-space:nowrap}.task-items-table .task-item-file{text-align:left;white-space:normal;overflow-wrap:anywhere;word-break:break-word;line-height:1.45}.task-items-table .task-item-size,.task-items-table .task-item-status{min-width:112px}.task-items-table .task-item-progress,.task-items-table .task-item-source{text-overflow:ellipsis;overflow:hidden}.badge{padding-inline:calc(var(--spacing)*2.5);padding-block:calc(var(--spacing)*.5);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);border-radius:3.40282e38px;align-items:center;display:inline-flex}.badge-running{background-color:var(--color-primary-soft);color:var(--color-primary)}.badge-success{background-color:var(--color-success-bg);color:var(--color-success)}.badge-failed{background-color:var(--color-danger-bg);color:var(--color-danger)}.badge-pending{background-color:var(--color-orange-50);color:var(--color-cta)}.badge-paused,.badge-skipped{background-color:var(--color-slate-100);color:var(--color-slate-500)}.badge-warning{background-color:var(--color-warning-bg);color:var(--color-warning)}.badge-muted{background-color:var(--color-slate-100);color:var(--color-slate-500)}.progress-bar{height:calc(var(--spacing)*1.5);background-color:var(--color-slate-100);border-radius:3.40282e38px;overflow:hidden}.progress-fill{height:100%;transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.3s;background:linear-gradient(90deg,var(--color-primary-light),var(--color-primary));border-radius:3.40282e38px;transition-duration:.3s}.status-dot{margin-right:calc(var(--spacing)*1.5);height:calc(var(--spacing)*1.5);width:calc(var(--spacing)*1.5);vertical-align:middle;border-radius:3.40282e38px;display:inline-block}.status-dot.running{background-color:var(--color-primary)}.status-dot.success{background-color:var(--color-success)}.status-dot.failed{background-color:var(--color-danger)}.status-dot.pending{background-color:var(--color-warning)}.status-dot.paused{background-color:var(--color-slate-300)}.activity-item{gap:calc(var(--spacing)*2);border-bottom-style:var(--tw-border-style);border-bottom-width:1px;border-color:var(--color-line-light);padding-block:calc(var(--spacing)*1.5);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-leading:1.5;line-height:1.5;display:flex}.activity-item:last-child{border-bottom-style:var(--tw-border-style);border-bottom-width:0}.activity-time{min-width:44px;font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));white-space:nowrap;color:var(--color-muted);font-family:ui-monospace,monospace}.activity-badge{font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);white-space:nowrap}.activity-badge.ok{color:var(--color-success)}.activity-badge.warn{color:var(--color-warning)}.activity-badge.err{color:var(--color-danger)}.view{display:none}.view.active{gap:18px;display:grid}.login-page{background-color:var(--color-bg);width:100%;min-height:100vh;padding-inline:calc(var(--spacing)*6);padding-block:calc(var(--spacing)*8);flex-direction:column;flex:1;justify-content:center;align-items:center;display:flex;overflow-x:hidden}@media not all and (min-width:40rem){.login-page{padding-inline:calc(var(--spacing)*4);padding-top:calc(var(--spacing)*14);padding-bottom:calc(var(--spacing)*8);justify-content:flex-start}}.login-page{min-height:100svh}.login-card{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);width:100%;max-width:420px;padding:calc(var(--spacing)*8);--tw-shadow:0 10px 15px -3px var(--tw-shadow-color,#0000001a),0 4px 6px -4px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow);border-radius:16px}@media not all and (min-width:40rem){.login-card{padding:calc(var(--spacing)*6);border-radius:14px}}.login-card{animation:.5s .1s both fadeIn}.login-brand{margin-bottom:calc(var(--spacing)*5);text-align:center;width:100%;max-width:420px}@media not all and (min-width:40rem){.login-brand{margin-bottom:calc(var(--spacing)*4)}}.login-brand{animation:.5s both fadeIn}.login-brand-mark{margin-bottom:calc(var(--spacing)*3);height:calc(var(--spacing)*12);width:calc(var(--spacing)*12);border-radius:var(--radius-xl);--tw-font-weight:var(--font-weight-bold);font-size:22px;font-weight:var(--font-weight-bold);color:var(--color-white);background:linear-gradient(135deg,var(--color-primary),var(--color-primary-light));font-family:var(--font-heading);justify-content:center;align-items:center;display:inline-flex}.login-brand h1{font-size:var(--text-xl);line-height:var(--tw-leading,var(--text-xl--line-height));--tw-font-weight:var(--font-weight-extrabold);font-weight:var(--font-weight-extrabold);color:var(--color-text);font-family:var(--font-heading)}.login-brand p{margin-top:calc(var(--spacing)*1);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-muted)}@media not all and (min-width:40rem){.login-brand p{padding-inline:calc(var(--spacing)*2);--tw-leading:calc(var(--spacing)*5);line-height:calc(var(--spacing)*5)}}.login-overlay{inset:calc(var(--spacing)*0);z-index:1000;background-color:var(--color-bg);width:100%;min-height:100svh;position:fixed}.login-error{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-red-300);background-color:var(--color-danger-bg);padding-inline:calc(var(--spacing)*3.5);padding-block:calc(var(--spacing)*2.5);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-danger);border-radius:8px;margin-bottom:18px;display:none}.login-error.visible{animation:.4s shake;display:block}@keyframes fadeIn{0%{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}@keyframes shake{0%,to{transform:translate(0)}20%,60%{transform:translate(-6px)}40%,80%{transform:translate(6px)}}.login-field{margin-bottom:calc(var(--spacing)*5)}.login-field label{margin-bottom:calc(var(--spacing)*2);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));--tw-font-weight:var(--font-weight-medium);font-weight:var(--font-weight-medium);color:var(--color-text);display:block}.login-field input{height:calc(var(--spacing)*12);border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);width:100%;padding-inline:calc(var(--spacing)*3.5);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-text);transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;--tw-outline-style:none;border-radius:8px;outline-style:none;font-family:inherit;transition-duration:.15s}.login-field input:focus{border-color:var(--color-primary);box-shadow:0 0 0 3px #2563eb1f}.login-options{margin-bottom:calc(var(--spacing)*6);justify-content:space-between;align-items:center;display:flex}.login-checkbox{cursor:pointer;align-items:center;gap:calc(var(--spacing)*2);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-muted);-webkit-user-select:none;user-select:none;display:flex}.login-submit{height:calc(var(--spacing)*12);cursor:pointer;justify-content:center;align-items:center;gap:calc(var(--spacing)*2);border-style:var(--tw-border-style);background-color:var(--color-primary);width:100%;font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-white);transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;border-width:0;border-radius:8px;font-family:inherit;transition-duration:.15s;display:flex}.login-submit:hover{background-color:var(--color-primary-dark)}.login-submit:disabled{cursor:not-allowed;opacity:.7}.login-submit:disabled:hover{background-color:var(--color-primary)}.spinner{width:18px;height:18px;animation:var(--animate-spin);border-style:var(--tw-border-style);border-width:2px;border-color:#ffffff4d;border-radius:3.40282e38px;flex-shrink:0}@supports (color:color-mix(in lab, red, red)){.spinner{border-color:color-mix(in oklab,var(--color-white)30%,transparent)}}.spinner{border-top-color:var(--color-white)}.watch-overlay{pointer-events:none;inset:calc(var(--spacing)*0);z-index:999;background-color:#00000059;justify-content:center;align-items:center;display:flex;position:fixed}@supports (color:color-mix(in lab, red, red)){.watch-overlay{background-color:color-mix(in oklab,var(--color-black)35%,transparent)}}.watch-overlay{opacity:0;transition-property:opacity;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.2s;transition-duration:.2s}.watch-overlay.open{pointer-events:auto;opacity:1}.watch-dialog{gap:calc(var(--spacing)*4);background-color:var(--color-surface);width:440px;max-width:calc(100vw - 32px);padding:calc(var(--spacing)*6);--tw-shadow:0 10px 15px -3px var(--tw-shadow-color,#0000001a),0 4px 6px -4px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow);border-radius:10px;display:grid}.watch-history-dialog{grid-template-rows:auto minmax(0,1fr) auto;width:900px;max-height:82vh}.watch-history-header{justify-content:space-between;align-items:center;gap:calc(var(--spacing)*3);display:flex}.watch-history-body{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);border-radius:8px;overflow:auto}.watch-history-pagination{justify-content:space-between;align-items:center;gap:calc(var(--spacing)*3);flex-wrap:wrap;display:flex}.watch-history-table{min-width:720px}.watch-row{cursor:pointer}.watch-row:hover{background:var(--color-surface-hover)}.watch-events-row{display:none}.watch-events-row.open{display:table-row}.watch-events-row td{background:var(--color-surface-alt);padding:0}.watch-events-panel{max-height:300px;padding:12px 16px;font-size:15px;overflow-y:auto}.watch-event-item{border-bottom:1px solid var(--color-line);align-items:flex-start;gap:8px;padding:4px 0;font-size:13px;display:flex}.watch-event-item:last-child{border-bottom:0}.watch-event-time{color:var(--color-muted);white-space:nowrap;min-width:90px}.watch-event-badge{flex-shrink:0}.watch-event-info{word-break:break-all;flex:1}.watch-events-load-more{cursor:pointer;margin:8px auto 0;font-size:13px;display:block}@media (max-width:1200px){.stat-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media (max-width:960px){.sidebar{display:none}.main-content{padding:calc(var(--spacing)*4)}}.mob-body{font-family:var(--font-mob);-webkit-tap-highlight-color:transparent;-webkit-user-select:none;user-select:none;width:100%;min-height:100svh;padding-top:var(--topbar-height);padding-bottom:calc(var(--tab-height) + var(--safe-bottom));background:var(--color-bg);color:var(--color-text);font-size:15px;line-height:1.5;display:block;overflow-x:hidden}.mob-body label{width:100%;min-width:0;color:var(--color-text-secondary);gap:6px;font-size:14px;font-weight:500;display:grid}.mob-body form{flex-direction:column;gap:10px;width:100%;min-width:0;display:flex}.mob-body input,.mob-body select,.mob-body textarea{border:1px solid var(--color-line);background:var(--color-surface);width:100%;min-width:0;color:var(--color-text);box-sizing:border-box;border-radius:8px;min-height:44px;padding:12px 14px;font-family:inherit;font-size:16px;transition:border-color .18s,box-shadow .18s}.mob-body input:focus,.mob-body select:focus,.mob-body textarea:focus{border-color:var(--color-primary);outline:none;box-shadow:0 0 0 3px #2563eb1f}.mob-body input[type=checkbox],.mob-body input[type=radio]{width:auto;min-width:auto;min-height:auto;accent-color:var(--color-primary);padding:0}.mob-body label:has(input[type=checkbox]),.mob-body label:has(input[type=radio]){flex-direction:row;align-items:center;gap:8px;display:flex}.mob-btn{background:var(--color-primary);color:#fff;cursor:pointer;border:0;border-radius:8px;justify-content:center;align-items:center;gap:6px;min-width:44px;min-height:44px;padding:0 16px;font-family:inherit;font-size:15px;font-weight:600;transition:opacity .15s,background .15s;display:inline-flex}.mob-btn:active{opacity:.78}.mob-btn-muted{background:var(--color-surface);color:var(--color-text);border:1px solid var(--color-line)}.mob-btn-muted:active{background:var(--color-surface-muted)}.mob-btn-danger{color:var(--color-danger);border:1px solid var(--color-danger);background:0 0}.mob-btn-danger:active{background:var(--color-danger-bg)}.mob-btn-sm{min-width:auto;min-height:36px;padding:0 12px;font-size:14px}.mob-btn svg{flex-shrink:0;width:18px;height:18px}.mob-topbar{height:var(--topbar-height);background:var(--color-surface);border-bottom:1px solid var(--color-line);z-index:100;align-items:center;gap:6px;padding:0 14px;display:flex;position:fixed;top:0;left:0;right:0}.mob-topbar__back{width:44px;height:44px;color:var(--color-primary);cursor:pointer;background:0 0;border:0;border-radius:8px;flex-shrink:0;justify-content:center;align-items:center;min-width:44px;min-height:44px;padding:0;font-family:inherit;font-size:20px;line-height:1;display:none}.mob-topbar__back:active{background:var(--color-primary-soft)}.mob-topbar__title{font-size:17px;font-weight:700;font-family:var(--font-heading);color:var(--color-text)}.mob-topbar.sub .mob-topbar__back{display:flex}.mob-tabbar{background:var(--color-surface);border-top:1px solid var(--color-line);z-index:100;height:calc(var(--tab-height) + var(--safe-bottom));padding-top:6px;padding-bottom:var(--safe-bottom);justify-content:space-around;align-items:flex-start;display:flex;position:fixed;bottom:0;left:0;right:0}.mob-tab{color:var(--color-muted);cursor:pointer;background:0 0;border:0;border-radius:0;flex-direction:column;align-items:center;gap:2px;min-width:44px;min-height:auto;padding:4px 0;font-family:inherit;font-size:11px;font-weight:500;transition:color .15s;display:flex}.mob-tab.active{color:var(--color-primary);font-weight:600}.mob-tab svg{flex-shrink:0;width:24px;height:24px}.mob-content{box-sizing:border-box;flex-direction:column;gap:10px;width:100%;min-width:0;max-width:100%;padding:12px;animation:.25s both mobRise;display:flex}@keyframes mobRise{0%{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}.mob-view{display:none}.mob-view.active{flex-direction:column;gap:10px;width:100%;min-width:0;display:flex}.mob-view.active>*{min-width:0}.mob-subpage{flex-direction:column;gap:10px;width:100%;min-width:0;display:none}.mob-subpage.active{display:flex}.mob-subpage.active>*{min-width:0}.mob-card{background:var(--color-surface);border:1px solid var(--color-line);border-left:3px solid var(--color-line);box-sizing:border-box;cursor:pointer;border-radius:10px;width:100%;max-width:100%;padding:14px;transition:all .15s;box-shadow:0 1px 3px #0000000a}.mob-card:active{transform:scale(.985)}.mob-card.status-pending{border-left-color:#94a3b8}.mob-card.status-running{border-left-color:var(--color-primary)}.mob-card.status-paused{border-left-color:var(--color-warning)}.mob-card.status-success,.mob-card.status-completed{border-left-color:var(--color-success)}.mob-card.status-failure{border-left-color:var(--color-danger)}.mob-card.status-cancelled{border-left-color:#94a3b8}.mob-card.status-skipped{border-left-color:#8b5cf6}.mob-card__head{justify-content:space-between;align-items:flex-start;margin-bottom:6px;display:flex}.mob-card__title{word-break:break-all;flex:1;min-width:0;font-size:15px;font-weight:650;line-height:1.35}.mob-card__badge{white-space:nowrap;border-radius:4px;flex-shrink:0;padding:2px 8px;font-size:12px;font-weight:600;display:inline-block}.mob-card__badge.pending{color:var(--color-text-secondary);background:#f1f5f9}.mob-card__badge.running{background:var(--color-success-bg);color:var(--color-success)}.mob-card__badge.paused{background:var(--color-warning-bg);color:var(--color-warning)}.mob-card__badge.completed{background:var(--color-primary-soft);color:var(--color-primary)}.mob-card__badge.failure{background:var(--color-danger-bg);color:var(--color-danger)}.mob-card__badge.cancelled{color:#94a3b8;background:#f1f5f9}.mob-card__row{justify-content:space-between;align-items:flex-start;gap:10px;padding:2px 0;font-size:13px;display:flex}.mob-card__row .label{color:var(--color-muted)}.mob-card__row span:last-child{text-align:right;overflow-wrap:anywhere;min-width:0}.mob-card__progress{background:var(--color-surface-muted);border-radius:3px;height:6px;margin:6px 0;overflow:hidden}.mob-card__progress-fill{background:var(--color-primary);border-radius:3px;height:100%;transition:width .3s}.mob-card__actions{flex-wrap:wrap;gap:6px;margin-top:8px;display:flex}.mob-watch-events{border-top:1px solid var(--color-line);margin-top:8px;padding-top:8px;font-size:12px}.mob-watch-events .watch-event-item{border-bottom:1px solid var(--color-line);align-items:flex-start;gap:6px;padding:3px 0;display:flex}.mob-watch-events .watch-event-item:last-child{border-bottom:0}.mob-collapse{border:1px solid var(--color-line);background:var(--color-surface);box-sizing:border-box;border-radius:10px;width:100%;min-width:0;max-width:100%;overflow:hidden}.mob-collapse__head{cursor:pointer;-webkit-user-select:none;user-select:none;color:var(--color-text);justify-content:space-between;align-items:center;min-width:0;padding:14px;font-size:15px;font-weight:600;display:flex}.mob-collapse__head:active{background:var(--color-surface-muted)}.mob-collapse__arrow{color:var(--color-muted);flex-shrink:0;font-size:12px;transition:transform .2s}.mob-collapse.open .mob-collapse__arrow{transform:rotate(180deg)}.mob-collapse__body{flex-direction:column;gap:10px;min-width:0;padding:0 14px 14px;display:none}.mob-collapse.open .mob-collapse__body{display:flex}.mob-collapse__body>*{width:100%;min-width:0}.mob-collapse__body>.mob-btn,.mob-collapse__body>.mob-empty{width:100%}.mob-menu-group{background:var(--color-surface);border:1px solid var(--color-line);box-sizing:border-box;border-radius:10px;flex-direction:column;width:100%;max-width:100%;display:flex;overflow:hidden}.mob-menu-group+.mob-menu-group{margin-top:10px}.mob-menu-label{color:var(--color-muted);text-transform:uppercase;letter-spacing:.06em;padding:10px 14px 4px;font-size:12px;font-weight:600}.mob-menu-item{color:var(--color-text);cursor:pointer;text-align:left;border:0;border-bottom:1px solid var(--color-line-light);background:0 0;border-radius:0;align-items:center;gap:10px;width:100%;min-height:44px;padding:14px;font-family:inherit;font-size:15px;font-weight:400;transition:background .15s;display:flex}.mob-menu-item:last-child{border-bottom:0}.mob-menu-item:active{background:var(--color-surface-hover)}.mob-menu-item svg{width:22px;height:22px;color:var(--color-primary);flex-shrink:0}.mob-menu-item__arrow{color:var(--color-muted);margin-left:auto;font-size:14px}.mob-menu-item__label{flex:1}.mob-menu-item--danger,.mob-menu-item--danger svg{color:var(--color-danger)}.mob-sheet-overlay{z-index:300;background:#00000059;align-items:flex-end;display:none;position:fixed;inset:0}.mob-sheet-overlay.open{display:flex}.mob-sheet{background:var(--color-surface);width:100%;padding:20px 16px max(24px,var(--safe-bottom));border-radius:16px 16px 0 0;flex-direction:column;gap:14px;max-height:85vh;animation:.25s mobSlideUp;display:flex;overflow-y:auto}@keyframes mobSlideUp{0%{transform:translateY(100%)}to{transform:translateY(0)}}.mob-sheet__title{font-size:15px;font-weight:700;font-family:var(--font-heading);margin:0}.mob-toast{left:50%;bottom:calc(var(--tab-height) + var(--safe-bottom) + 16px);background:var(--color-text);color:#fff;z-index:400;opacity:0;pointer-events:none;white-space:nowrap;border-radius:8px;padding:10px 20px;font-size:13px;transition:opacity .25s;position:fixed;transform:translate(-50%)}.mob-toast.show{opacity:1;pointer-events:auto}.mob-sheet__task-header{background:var(--color-surface-muted);border-radius:8px;padding:12px}.mob-sheet__task-header .task-title{word-break:break-all;margin-bottom:4px;font-size:15px;font-weight:650}.mob-sheet__task-header .task-meta{color:var(--color-muted);margin-bottom:6px;font-size:12px}.mob-sheet-tabs{gap:6px;padding-bottom:2px;display:flex;overflow-x:auto}.mob-sheet-tab{border:1px solid var(--color-line);background:var(--color-surface);color:var(--color-muted);cursor:pointer;white-space:nowrap;border-radius:6px;min-width:auto;min-height:36px;padding:8px 12px;font-family:inherit;font-size:12px;font-weight:600;transition:all .15s}.mob-sheet-tab.active{background:var(--color-primary);color:#fff;border-color:var(--color-primary)}.mob-sheet-tab .count{opacity:.8;margin-left:3px}.mob-item-row{border-bottom:1px solid var(--color-line);justify-content:space-between;align-items:center;gap:6px;padding:8px 0;font-size:13px;display:flex}.mob-item-row:last-child{border-bottom:0}.mob-item-row__name{text-overflow:ellipsis;white-space:nowrap;word-break:break-all;flex:1;min-width:0;overflow:hidden}.mob-item-row__progress{color:var(--color-muted);text-overflow:ellipsis;white-space:nowrap;margin-top:2px;font-size:12px;font-weight:500;display:block;overflow:hidden}.mob-event-row{border-bottom:1px solid var(--color-line);padding:6px 0;font-size:12px}.mob-event-row:last-child{border-bottom:0}.mob-event-row time{color:var(--color-muted);margin-right:6px}.mob-sheet-pagination{color:var(--color-muted);justify-content:space-between;align-items:center;padding-top:6px;font-size:12px;display:flex}.mob-empty{text-align:center;color:var(--color-muted);padding:32px 16px;font-size:13px;line-height:1.6}.mob-section-title{text-transform:uppercase;letter-spacing:.06em;color:var(--color-muted);padding:4px 0;font-size:12px;font-weight:600}.mob-media-scan-btn{width:100%;margin:8px 0}.mob-media-result{margin-top:12px;font-size:13px}.mob-subpage .mob-collapse__body label,.mob-subpage .mob-collapse__body [style*=display\:grid],.mob-body [style*=display\:grid],.mob-body [style*="display: grid"]{width:100%;min-width:0}.mob-body [style*="grid-template-columns:1fr 1fr"],.mob-body [style*="grid-template-columns: 1fr 1fr"]{grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important}#mob-tasks-list,#mob-watches-list,#mob-operations-list,#mob-statistics-list,#mob-records-list,#mob-media-result,#mob-profile-menu{width:100%;min-width:0;max-width:100%}.mob-check-group{border:1px solid var(--color-line);box-sizing:border-box;border-radius:8px;width:100%;min-width:0;margin:0;padding:10px 14px}.mob-check-group legend{color:var(--color-muted);padding:0 4px;font-size:13px}.mob-table-wrap{border:1px solid var(--color-line);-webkit-overflow-scrolling:touch;border-radius:8px;overflow-x:auto}.mob-table-wrap table{border-collapse:collapse;width:100%;font-size:13px}.mob-table-wrap th,.mob-table-wrap td{text-align:left;border-bottom:1px solid var(--color-line);white-space:nowrap;padding:8px 10px}.mob-table-wrap th{background:var(--color-surface-muted);font-weight:600;position:sticky;top:0}.mob-login-overlay{background:var(--color-bg);z-index:1000;padding:48px 16px;padding-bottom:max(32px,calc(24px + var(--safe-bottom)));flex-direction:column;justify-content:flex-start;align-items:center;gap:16px;display:none;position:fixed;inset:0;overflow-y:auto}.mob-login-overlay.active{display:flex}.mob-login-brand{text-align:center;width:100%;max-width:400px}.mob-login-brand-mark{background:linear-gradient(135deg,var(--color-primary),var(--color-primary-light));color:#fff;width:48px;height:48px;font-size:22px;font-weight:700;font-family:var(--font-heading);border-radius:12px;justify-content:center;align-items:center;margin-bottom:12px;display:inline-flex}.mob-login-brand h1{color:var(--color-text);font-size:22px;font-weight:800;font-family:var(--font-heading);letter-spacing:-.02em;margin:0}.mob-login-brand p{color:var(--color-muted);margin:4px 0 0;font-size:13px}.mob-login-card{background:var(--color-surface);border:1px solid var(--color-line);border-radius:14px;width:100%;max-width:400px;padding:20px;box-shadow:0 1px 3px #0000000a}.mob-login-card__step{color:var(--color-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px;font-size:12px}.mob-login-card__title{color:var(--color-text);font-size:20px;font-weight:700;font-family:var(--font-heading);margin:0 0 6px}.mob-login-card__subtitle{color:var(--color-muted);margin:0 0 20px;font-size:14px;line-height:1.5}.mob-login-field{margin-bottom:16px}.mob-login-field label{color:var(--color-text);margin-bottom:6px;font-size:13px;font-weight:500;display:block}.mob-login-field input{border:1px solid var(--color-line);background:var(--color-surface);width:100%;height:48px;color:var(--color-text);border-radius:8px;padding:0 14px;font-family:inherit;font-size:15px;transition:border-color .18s}.mob-login-field input:focus{border-color:var(--color-primary);outline:none;box-shadow:0 0 0 3px #2563eb1f}.mob-login-field__hint{color:var(--color-muted);margin-top:4px;font-size:12px}.mob-login-error{color:var(--color-danger);background:var(--color-danger-bg);border:1px solid #ef44444d;border-radius:8px;margin-bottom:16px;padding:10px 14px;font-size:13px;display:none}.mob-login-error.visible{display:block}.mob-login-actions{grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;display:grid}.mob-login-actions button{width:100%;min-width:0}.mob-login-submit{justify-content:center;align-items:center;gap:6px;display:inline-flex}.mob-login-submit svg{flex-shrink:0;width:18px;height:18px}.mob-login-success{text-align:center;padding:16px 0}.mob-login-success svg{width:48px;height:48px;color:var(--color-success);margin-bottom:12px}.mob-login-success__text{color:var(--color-success);margin:0;font-size:15px;font-weight:600}@media (min-width:640px){.mob-login-overlay{justify-content:center;padding-top:24px}.mob-login-card{padding:24px}}}@layer utilities{.collapse{visibility:collapse}.invisible{visibility:hidden}.visible{visibility:visible}.sr-only{clip-path:inset(50%);white-space:nowrap;border-width:0;width:1px;height:1px;margin:-1px;padding:0;position:absolute;overflow:hidden}.absolute{position:absolute}.fixed{position:fixed}.relative{position:relative}.static{position:static}.sticky{position:sticky}.bottom-0{bottom:calc(var(--spacing)*0)}.container{width:100%}@media (min-width:40rem){.container{max-width:40rem}}@media (min-width:48rem){.container{max-width:48rem}}@media (min-width:64rem){.container{max-width:64rem}}@media (min-width:80rem){.container{max-width:80rem}}@media (min-width:96rem){.container{max-width:96rem}}.m-0{margin:calc(var(--spacing)*0)}.mx-auto{margin-inline:auto}.mt-1{margin-top:calc(var(--spacing)*1)}.mt-2{margin-top:calc(var(--spacing)*2)}.mt-3{margin-top:calc(var(--spacing)*3)}.mt-4{margin-top:calc(var(--spacing)*4)}.mt-\[18px\]{margin-top:18px}.mb-1{margin-bottom:calc(var(--spacing)*1)}.mb-1\.5{margin-bottom:calc(var(--spacing)*1.5)}.mb-2{margin-bottom:calc(var(--spacing)*2)}.mb-3{margin-bottom:calc(var(--spacing)*3)}.mb-4{margin-bottom:calc(var(--spacing)*4)}.mb-5{margin-bottom:calc(var(--spacing)*5)}.mb-7{margin-bottom:calc(var(--spacing)*7)}.mb-\[14px\]{margin-bottom:14px}.ml-1{margin-left:calc(var(--spacing)*1)}.block{display:block}.contents{display:contents}.flex{display:flex}.grid{display:grid}.hidden{display:none}.inline{display:inline}.inline-flex{display:inline-flex}.table{display:table}.\!h-\[34px\]{height:34px!important}.h-4{height:calc(var(--spacing)*4)}.h-9{height:calc(var(--spacing)*9)}.max-h-\[300px\]{max-height:300px}.min-h-20{min-height:calc(var(--spacing)*20)}.min-h-screen{min-height:100vh}.\!w-\[34px\]{width:34px!important}.\!w-auto{width:auto!important}.w-4{width:calc(var(--spacing)*4)}.w-10{width:calc(var(--spacing)*10)}.w-20{width:calc(var(--spacing)*20)}.w-24{width:calc(var(--spacing)*24)}.w-40{width:calc(var(--spacing)*40)}.w-\[60px\]{width:60px}.w-\[80px\]{width:80px}.w-\[90px\]{width:90px}.w-\[160px\]{width:160px}.w-\[180px\]{width:180px}.w-full{width:100%}.max-w-\[160px\]{max-width:160px}.max-w-\[180px\]{max-width:180px}.max-w-\[200px\]{max-width:200px}.max-w-\[220px\]{max-width:220px}.max-w-\[240px\]{max-width:240px}.max-w-\[260px\]{max-width:260px}.max-w-\[900px\]{max-width:900px}.min-w-\[60px\]{min-width:60px}.min-w-\[600px\]{min-width:600px}.flex-1{flex:1}.flex-shrink{flex-shrink:1}.shrink-0{flex-shrink:0}.border-collapse{border-collapse:collapse}.transform{transform:var(--tw-rotate-x,)var(--tw-rotate-y,)var(--tw-rotate-z,)var(--tw-skew-x,)var(--tw-skew-y,)}.cursor-pointer{cursor:pointer}.resize{resize:both}.grid-cols-1{grid-template-columns:repeat(1,minmax(0,1fr))}.grid-cols-2{grid-template-columns:repeat(2,minmax(0,1fr))}.grid-cols-\[380px_1fr\]{grid-template-columns:380px 1fr}.flex-wrap{flex-wrap:wrap}.items-center{align-items:center}.justify-between{justify-content:space-between}.justify-center{justify-content:center}.justify-end{justify-content:flex-end}.gap-1{gap:calc(var(--spacing)*1)}.gap-2{gap:calc(var(--spacing)*2)}.gap-2\.5{gap:calc(var(--spacing)*2.5)}.gap-3{gap:calc(var(--spacing)*3)}.gap-4{gap:calc(var(--spacing)*4)}.gap-5{gap:calc(var(--spacing)*5)}.gap-x-2{column-gap:calc(var(--spacing)*2)}.gap-x-2\.5{column-gap:calc(var(--spacing)*2.5)}.gap-y-0{row-gap:calc(var(--spacing)*0)}.gap-y-1{row-gap:calc(var(--spacing)*1)}.overflow-auto{overflow:auto}.overflow-hidden{overflow:hidden}.overflow-x-auto{overflow-x:auto}.rounded{border-radius:.25rem}.rounded-lg{border-radius:var(--radius-lg)}.rounded-md{border-radius:var(--radius-md)}.border{border-style:var(--tw-border-style);border-width:1px}.border-t{border-top-style:var(--tw-border-style);border-top-width:1px}.border-line{border-color:var(--color-line)}.bg-bg{background-color:var(--color-bg)}.bg-danger-bg{background-color:var(--color-danger-bg)}.bg-surface-alt{background-color:var(--color-surface-alt)}.bg-white{background-color:var(--color-white)}.p-4{padding:calc(var(--spacing)*4)}.p-6{padding:calc(var(--spacing)*6)}.p-8{padding:calc(var(--spacing)*8)}.p-\[10px_14px\]{padding:10px 14px}.px-0{padding-inline:calc(var(--spacing)*0)}.px-6{padding-inline:calc(var(--spacing)*6)}.px-\[3px\]{padding-inline:3px}.px-\[18px\]{padding-inline:18px}.py-0{padding-block:calc(var(--spacing)*0)}.py-0\.5{padding-block:calc(var(--spacing)*.5)}.py-1{padding-block:calc(var(--spacing)*1)}.py-2{padding-block:calc(var(--spacing)*2)}.py-3{padding-block:calc(var(--spacing)*3)}.py-4{padding-block:calc(var(--spacing)*4)}.pt-3{padding-top:calc(var(--spacing)*3)}.pb-\[14px\]{padding-bottom:14px}.text-center{text-align:center}.text-right{text-align:right}.font-\[family-name\:var\(--font-body\)\]{font-family:var(--font-body)}.font-\[family-name\:var\(--font-heading\)\]{font-family:var(--font-heading)}.font-mono{font-family:var(--font-mono)}.text-base{font-size:var(--text-base);line-height:var(--tw-leading,var(--text-base--line-height))}.text-sm{font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height))}.text-xl{font-size:var(--text-xl);line-height:var(--tw-leading,var(--text-xl--line-height))}.text-xs{font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height))}.text-\[11px\]{font-size:11px}.text-\[14px\]{font-size:14px}.leading-\[1\.5\]{--tw-leading:1.5;line-height:1.5}.leading-tight{--tw-leading:var(--leading-tight);line-height:var(--leading-tight)}.font-\[650\]{--tw-font-weight:650;font-weight:650}.font-bold{--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold)}.font-medium{--tw-font-weight:var(--font-weight-medium);font-weight:var(--font-weight-medium)}.font-semibold{--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold)}.tracking-\[0\.06em\]{--tw-tracking:.06em;letter-spacing:.06em}.text-ellipsis{text-overflow:ellipsis}.whitespace-nowrap{white-space:nowrap}.text-danger{color:var(--color-danger)}.text-muted{color:var(--color-muted)}.text-primary{color:var(--color-primary)}.text-success{color:var(--color-success)}.text-text{color:var(--color-text)}.uppercase{text-transform:uppercase}.overline{text-decoration-line:overline}.underline{text-decoration-line:underline}.accent-primary{accent-color:var(--color-primary)}.opacity-70{opacity:.7}.shadow{--tw-shadow:0 1px 3px 0 var(--tw-shadow-color,#0000001a),0 1px 2px -1px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow)}.outline{outline-style:var(--tw-outline-style);outline-width:1px}.grayscale{--tw-grayscale:grayscale(100%);filter:var(--tw-blur,)var(--tw-brightness,)var(--tw-contrast,)var(--tw-grayscale,)var(--tw-hue-rotate,)var(--tw-invert,)var(--tw-saturate,)var(--tw-sepia,)var(--tw-drop-shadow,)}.invert{--tw-invert:invert(100%);filter:var(--tw-blur,)var(--tw-brightness,)var(--tw-contrast,)var(--tw-grayscale,)var(--tw-hue-rotate,)var(--tw-invert,)var(--tw-saturate,)var(--tw-sepia,)var(--tw-drop-shadow,)}.filter{filter:var(--tw-blur,)var(--tw-brightness,)var(--tw-contrast,)var(--tw-grayscale,)var(--tw-hue-rotate,)var(--tw-invert,)var(--tw-saturate,)var(--tw-sepia,)var(--tw-drop-shadow,)}.backdrop-filter{-webkit-backdrop-filter:var(--tw-backdrop-blur,)var(--tw-backdrop-brightness,)var(--tw-backdrop-contrast,)var(--tw-backdrop-grayscale,)var(--tw-backdrop-hue-rotate,)var(--tw-backdrop-invert,)var(--tw-backdrop-opacity,)var(--tw-backdrop-saturate,)var(--tw-backdrop-sepia,);backdrop-filter:var(--tw-backdrop-blur,)var(--tw-backdrop-brightness,)var(--tw-backdrop-contrast,)var(--tw-backdrop-grayscale,)var(--tw-backdrop-hue-rotate,)var(--tw-backdrop-invert,)var(--tw-backdrop-opacity,)var(--tw-backdrop-saturate,)var(--tw-backdrop-sepia,)}.transition{transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to,opacity,box-shadow,transform,translate,scale,rotate,filter,-webkit-backdrop-filter,backdrop-filter,display,content-visibility,overlay,pointer-events;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration))}.select-all{-webkit-user-select:all;user-select:all}@media (min-width:64rem){.lg\:grid-cols-2{grid-template-columns:repeat(2,minmax(0,1fr))}}.scrollbar-thin{scrollbar-width:thin;scrollbar-color:var(--color-line)transparent}}@property --tw-rotate-x{syntax:"*";inherits:false}@property --tw-rotate-y{syntax:"*";inherits:false}@property --tw-rotate-z{syntax:"*";inherits:false}@property --tw-skew-x{syntax:"*";inherits:false}@property --tw-skew-y{syntax:"*";inherits:false}@property --tw-border-style{syntax:"*";inherits:false;initial-value:solid}@property --tw-leading{syntax:"*";inherits:false}@property --tw-font-weight{syntax:"*";inherits:false}@property --tw-tracking{syntax:"*";inherits:false}@property --tw-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-shadow-color{syntax:"*";inherits:false}@property --tw-shadow-alpha{syntax:"<percentage>";inherits:false;initial-value:100%}@property --tw-inset-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-inset-shadow-color{syntax:"*";inherits:false}@property --tw-inset-shadow-alpha{syntax:"<percentage>";inherits:false;initial-value:100%}@property --tw-ring-color{syntax:"*";inherits:false}@property --tw-ring-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-inset-ring-color{syntax:"*";inherits:false}@property --tw-inset-ring-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-ring-inset{syntax:"*";inherits:false}@property --tw-ring-offset-width{syntax:"<length>";inherits:false;initial-value:0}@property --tw-ring-offset-color{syntax:"*";inherits:false;initial-value:#fff}@property --tw-ring-offset-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-outline-style{syntax:"*";inherits:false;initial-value:solid}@property --tw-blur{syntax:"*";inherits:false}@property --tw-brightness{syntax:"*";inherits:false}@property --tw-contrast{syntax:"*";inherits:false}@property --tw-grayscale{syntax:"*";inherits:false}@property --tw-hue-rotate{syntax:"*";inherits:false}@property --tw-invert{syntax:"*";inherits:false}@property --tw-opacity{syntax:"*";inherits:false}@property --tw-saturate{syntax:"*";inherits:false}@property --tw-sepia{syntax:"*";inherits:false}@property --tw-drop-shadow{syntax:"*";inherits:false}@property --tw-drop-shadow-color{syntax:"*";inherits:false}@property --tw-drop-shadow-alpha{syntax:"<percentage>";inherits:false;initial-value:100%}@property --tw-drop-shadow-size{syntax:"*";inherits:false}@property --tw-backdrop-blur{syntax:"*";inherits:false}@property --tw-backdrop-brightness{syntax:"*";inherits:false}@property --tw-backdrop-contrast{syntax:"*";inherits:false}@property --tw-backdrop-grayscale{syntax:"*";inherits:false}@property --tw-backdrop-hue-rotate{syntax:"*";inherits:false}@property --tw-backdrop-invert{syntax:"*";inherits:false}@property --tw-backdrop-opacity{syntax:"*";inherits:false}@property --tw-backdrop-saturate{syntax:"*";inherits:false}@property --tw-backdrop-sepia{syntax:"*";inherits:false}@property --tw-duration{syntax:"*";inherits:false}@keyframes spin{to{transform:rotate(360deg)}}</style>
</head>
<body class="bg-bg text-text font-[family-name:var(--font-body)] text-[14px]">
<div class="login-page">
  <div class="login-brand">
    <div class="login-brand-mark" aria-hidden="true">T</div>
    <h1>TRMD</h1>
    <p>Telegram Restricted Media Downloader</p>
  </div>
  <div class="login-card">
    <h2 class="font-[family-name:var(--font-heading)] text-xl font-[650] mb-7 text-text">登录控制台</h2>
    <div class="login-error" id="login-error" role="alert"></div>
    <form id="login-form" method="post" autocomplete="on" novalidate>
      <div class="login-field">
        <label for="username">用户名</label>
        <input id="username" type="text" name="username" autocomplete="username" placeholder="请输入用户名" required autofocus>
      </div>
      <div class="login-field">
        <label for="password">密码</label>
        <input id="password" type="password" name="password" autocomplete="current-password" placeholder="请输入密码" required>
      </div>
      <div class="login-options">
        <label class="login-checkbox">
          <input type="checkbox" id="remember-me" name="remember_me" class="w-4 h-4 accent-primary">
          <span>保持登录 30 天</span>
        </label>
      </div>
      <button type="submit" id="login-submit" class="login-submit">
        <span id="login-btn-text">登 录</span>
      </button>
    </form>
  </div>
</div>
<script>
(function() {
  var form = document.getElementById('login-form');
  var errorEl = document.getElementById('login-error');
  var submitBtn = document.getElementById('login-submit');
  var btnText = document.getElementById('login-btn-text');

  function showError(msg) {
    errorEl.textContent = msg;
    errorEl.classList.add('visible');
  }

  function hideError() {
    errorEl.textContent = '';
    errorEl.classList.remove('visible');
  }

  function setLoading(loading) {
    submitBtn.disabled = loading;
    btnText.innerHTML = loading ? '<span class="spinner"></span>登录中...' : '登 录';
  }

  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    hideError();
    var username = document.getElementById('username').value.trim();
    var password = document.getElementById('password').value;
    if (!username) { showError('请输入用户名'); document.getElementById('username').focus(); return; }
    if (!password) { showError('请输入密码'); document.getElementById('password').focus(); return; }
    setLoading(true);
    try {
      var resp = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: username,
          password: password,
          remember_me: document.getElementById('remember-me').checked
        })
      });
      var data = await resp.json();
      if (resp.ok && data.success) {
        window.location.href = '/';
      } else {
        showError(data.error || '登录失败，请检查用户名和密码。');
        setLoading(false);
        document.getElementById('password').value = '';
        document.getElementById('password').focus();
      }
    } catch (err) {
      showError('网络错误，请检查连接后重试。');
      setLoading(false);
    }
  });
})();
</script>
</body>
</html>
"""

FONTS = {
    "0b1fcab42c18.woff2": "d09GMgABAAAAABYMAAwAAAAAM2QAABW4AAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGx4cLgZgAIIoCslkvQ0LgmwAATYCJAOFVAQgBYNcB4pBG8sqRUaGjQMQwdYWUZQHRgz+rxe4MZxWB7KjzmqN3SQJN0ZMglJcPSERRqOarAyvDj7vbhBCqP8R0is2wo0X49b6gOm1kEOO0dBIYvL0/fDd2b0pVQWQTTlsJpbxpY8HyRcKhUPSHaoqVapxyLwf+G32PjpQl1YzQVQwCCuAT3xCEEQUPkq0ggHC1urceTeXLdNFX6RufZGlu2uXIUYymNd/lMAp4kmIBxAYmNmE0zMKu8X/fXOfM9lcYSb7vqoDdOI/vwE+Almijc0WVOsASNYe6p+UIXdF+DbSWeH1IKGiOtW3rQ66sVDSOFr6OLr8/f433fxlWecvoBsA9Bo0iqrORvL/T2fZSp6ZJbL3GLpA0XhdVCr6NM3s90iG0RglL5L3gLwB1soHskPaA6wC+HoCZ0NIrycsaiiByvRtrkwdf/qpeXBZ44KQRRzHoi5y5n/7tx/HMK8/IiEta8urfBlUjRhgPEMBcABp0iCCk1wDERAOwJoRpqX58oVtnnTXHmRD3FYynxuQdfdbYY02mQXQ4bYEzuQWaYsdDJltOFDahZfk9IZICZfAtZPwlL8xsG11jf8I8BxQ6pwBrlZcXACz9oIwQLgxHInruY57kV/2MZAdCAlJRcFUBqOCs1tpY7bkcVNHN+f6Tt/rT5ef6t7MuE8mk4/1z/TPD2JnZgo9FECikAy5SlWQ02jjmigfNWlpf/dGxj0y8beLmc96sXox8nIomRmpyYnxs9aev+j2d9HHz/5/+/+b/+8+p/125rdXf938iwH8+//LcUDgoGIP2HuNXox+pMq0S8/uYe8KOMoMtnaAfmtHAHEKwpggcYIaSliSdhYEbG6GzRyAWjgDsNikdoYOZextrAKDdSQh+euFqrqBAAci8+eplvwzNFYXWpYWyVYWZpYkHe0d8vomYT32+S4CD8lG1TRsfFlCpJK2G76vVFbldUV8ZCbSfCorr438UEuird3swg8BGC9zmRDaLQgWCbHl5yXhiDLSAMbj1ppJeThthuYGa3iUueGtVfYVTRrnbi0Y8+vzZ9ww8L0hoUJPfe1oQorIoh42BnrZKBZCtLCa/Z2snqA/HyrF4cNGId1LrE9/U/ULC1XT7dh05EXlBSaAgTpXLoFmg8z5jBCNvpMOSkQHW0ADjqKcU/Ki4IGQihtCaxa0MWzRyz+auhpjlA9TDz8y6dvanAMDgQSnR8KGS9Z1UAKwm2pdIre/pM9HA9yicSnBY3f8GRnTQkfwtUjkEgiVrNcKh8ORW4kk+LgZn7WXv9oCAUihcWR1/K2ETzcBZFMPYW5pzhHBljaxlNiRUJaojNOc3tmWwCIRcRj7Ehyc8GU4Bw8D1J5FLgZe4p/yQrzOKELoOcFBXSz57fqaxNSx6IzmOK+FdVmy0aEllnnHFLJTsUopBDS3MWCRKH4AVBKu6rclqBMeKAOVbBBILYsSNycGEIBxSXWyesYdW/w3BUMJAWyIAkqGMd2wZSvF2dsz8smfnMBiwWYGekpmKjKxuSFX6G/JoXZ01HSjhEERFNoGQcii2ILPS/HfJD4ezEuVgPAaqOcxRAZwi82DMGuhDrdabd2Htpf97e1blxQbZxxFwSPuwh9Kfao9Q1y0hpTRSSJk0Hf0FfSD0CwQCflu6lxbiEHVAd/LQgZ++44/M2o99UhwAsbMsZTU0LWPtX4uZth21a9LbBvxmfMWNKExfssGC4YSNJ+dVWnGq/NwD9tk9KInayw2OSvQS3posA0plHNDi4apfDxrhAfDwxYNSvJgsaXPmojjt90gyDrO6OJVPNQfeqZOJ9muzgeZ2boooMvtDYAjFPqCLR+UFdMYvS3dy/FLd956dKSmU+vkRhbzrlbSSdXpCOa3+Pj5/MA0dzsRJmkhzS881uK0v0O/+NISss3YPwP5hy562RLIfibaRFHMWwBZesUuHc8DDehL6J2KRGMLb8kH+VjtPC5024x9ZVppKBq07MFah1qcZrSV/UelO8qPVF3nSM0lthyKks3JZ7OI5n1klfLsU1uJo4r9dmuhVnZtM7JmbtEYnnXAkBwuY7hOdjMdlFdPSNy7Qkc9pQsTykPXb9b5q2S9YrNB7sTZJw8qXyC9c58wd4LKaQI6FvhkMTBKHzwtdQT52PbAOHPozF7KR2BF3Dac4+3SiJdSrtD1WPkbdEe31kGF/nkpgw8qehpOHjctTh0u2My5yZxQ/idu/zdHPLnGOt+dZpzvJg88Bm7G/q1g5bFAfHrxeRcoXa9l6sn4xG/BpT59cHBIholq6sRC+VDcDEcVdU6aWlNSwBHrcyrb/DhR3VbDLSstGcnJEPiizouT6ewCJmag1+q8hvCG1pojpZwRGnyWGj3AH4oQVNf7FhqVTwd7V2nA6rSbrA6vdb3PM2+BTciXxOglKBkdgL/2MMv2mB6+7H7wskk1tcIYDqdAfx0fG8HNvuNems37sQeVS/wob7mmkbfcj0rkHv7HXpr1uMdnHtHjow7YOX5E07K/o6Nl3xG177uJ74a86zcMrNqweWgldSUc7fz7iezJtTTZojOLZGCY/tDLl0h6+fzlajV/WS9f4hhcEuVMkC4SkZrwDdvVBnNIbxh1OAxjIb2564SXZoWj4xP4BByV3JIqJ3Dowb10Bn4G9+bRccghmshY2IKz8FGnk/Lbs2CKXpS/olHDX+5HpVJPfULTKNPVfzEJnDuc1pmOT/ym9JSU4FWY2quOfpbSbx+SSrCaWgyVDcEU0cOs0UaYuSK+gCflcnJf4CWvFESrKZVyXkVFs6tIYFluJjXYxJLqmgpxZQntub82CmIaqVVyPqdE5y7D4P649EIX3nVRCofHJ1r1OlWDXtc6gY83C4PBCqk0WCEINo9D1ZaJ98Ydo8yjTBu8PmHeqTiqcITku+RQPP77CyScNPmC/aTppAl2KzTKS5hqoUJ5BoMrmwRf9iiB7kRXBoUSzF0zYjNQDY7n2mvFkoAYHWj8pJqFa5gcTmMRC6+tYxkaJRoo57W8H+rFQoV9lTlOa/msoaJaYWy3WI0dimpl2aQlvnHQZlUsFqJ9WuDOyX81vMGmx6oUpY8t8YpBi0WxVCjsb2pC+5YKGhSLUG5Q1ioqkCpoTKGpmVivh0B+u0lPiimr6w3ylJ6N9jnN+t9aq/myttYm/3PuOrEkaCXXmL9bH/xg62H36OQUPgVnC5Yt9qH6UrVKK8Y0Om0RTsUVxw0F5TAdsVwo6m/SYP0rBArFCgHW19Qk7e8TKpjKpoJinM/n4I35LLY6n4XzUSauymfBxfstHG5b0u4jdJyK6+CTCCu9Qr6wrVzAKS8+T6He4C/4RE4u5ZbQWUI8twrvwsOUOH2yhLU7KzVL8N9zkox6pIAl1udWAZtCxVW7DYXlXHtxpVvO05eocoWk8UYKgO2jnqC0Db7YvC5tJymtKz54+oPW1R8u+xColLiDtLYO0o/p9pNnj5+FTdK5soAsckOEtEcKJd7/ExKmE+Kn2az/49f9FP6ZwtTPOAG63xSYBHDlwpc9gi+XA6Pn6iPRo9spWGDvbO0e6/DEc1jvxq2/b4HjFfjO9XzHatY0F3/3lG/9llWr1m8eWvnPJc2lf1cC7/qc8jfEJQplTj63sfQnS7yiz2JEu2vebFe6P++oFSboJRGsXCSUo67ycLvcLvIOy3sFdUGslVsob8hlYS6cqHDL/49W8doonhDsm6qrW2kc8Whj1u77nA195eT6+S/EJd5LXRLoLt+gcpO8ekU2R8TkiM2cptwt0JR0R/u5PONunfhGJauAklKut/KTLMOUwXnA7TzBH9Tbu7IraRxGii41kaU1/Lul1M611VDTyh/XCP4C7e0u7VYZVDWZMiviR105VbWg4MmZRbK0LsfMt6ugnDktLfzo8xSxNP5rj3UIjXBiFYsVNbXdm+VP+bkKqt9OZ5bHMNV6SBzM77HTi0oTmVpcTavPzNqNfpwCs7CP4hMEid9Z83JOSgpNJFNghJIsuumvSt8Ug1OfHBylUHEq1C7KqKnFJ3A0k++vMjStO0b32+hFlj8ceLj86+s38Cn8pc9v9CELStA9uSRSkdr+2yMosWfYruPdYgIRFVD9Dt9jOP3dfFPEqMxhM5J1aYmsJsMtG1WU32OfLXKnJrK1A/JxvAvTt/mI4wnoOxnIJ/Ep/GTFJRpfm/cjHo4JRYpiVZpQlV6HZ3hoInrC+XB9oyi1F1c9q2CiFDmeO3lT6pz7Rpxr0UL7z6S+l43Gtp2juXQIyPOuS67PeHfXCyOQ2HW0bsLDY6EBkh/v0RsKNfqKKxUHhBxmEVpW6q8yL5xMSpxcyO5pJfmdoNzUrgF8rTFqlbPYwi9/HQ0RdjyM30wPAYWVAj9T34Kui9JvpRe6IL2c6HFxBtAMFyqWiYfx4Y2yjWjuAjpar55vqgLPp+4TFXDoyabYGJYWP/TrbVguEzawfgbQPD7ucQ1oY9rr8BNUcRmt83oGe8bxDXp/SNicv2eC1+qHcSoCMm8M/r20U9c46nKrD/B/HltNW+Wqrc50ciFBVONxVvEUPlkC3012Hl8crA04i2ttYYLP+RU2V5kACDc6UIWfKOktiyFKZDxxElEam36OUxYjIkrEikidS2Unyo4hbWXqDDmn9NteH1NLFWfZ23THxMYXJiv2wm8joKZsojnyGL0qh12jB4e+/CPETlMZx4w09lcP5MX98OWFvceHNdiweo0ag+wja1TDKmxYs0YDBWNSDEVlWGV0KW1HUeEOWmkMsLZSWENpeT5haue7hQXfFRV9V1D4LlMynZg4nZx8NTHxajIkbhbmxp5ifKefGx2gFquahrM+TLuf93jt2SVQ31LD362q3l0t3t0A+nG78Xcu3P7hEiniTz2lfQQD6Zp07XbgswM/nv76gtQUfy1E42un+2Ebo9WN5U62ffg8g/883XYqjz95Yy/dKdjQ/9xp+DLL9L3k+6X4Uq1Ea9JiWsVvwaU9+uagb+lT4iEZJqipEwvkQwBDIAJkHNBgE2xW5UQ579oCFuUovOgdhZcQaXEOEgE7UZIyB04tGUOEsJlhrHzx13qI/UOu53tDtokIRN5EFwHyUiLSJ6qRk6VGH89IJDKSZOfO7OVjXrMWVH7VCYmMW/MBaK+IKo3+LkxpXI9Cdbg4pTqz0WzvofWNrNlYOPQNDAramlAA7atydP1QM/qL+eacimhOVw4N9FR19rrjEp6rKyXSuoHOx+eGarF4Q46geV6a9+X0jTtA25BmvlH/qaprFCkPJ8J72Hkx3xF6Uc6QmrkNDEFbURU6EwtyeeiWEJlqXz+SpTnkaXBaFXqEor0hfj2mA9VOy2RpRuwHZLnFdXIPPJvCmA0hu0ax8qBvlQe9ozzsYwhCBhS7eCSSdvOF8I6YwXFpa7YoyzXydOPN9oyIBx9WZYpU8yYQ3BroHUEhvv8mjMcHY8muCp2K3IcVncT0dP416s/HYm1hZUJK29GX4DcLlIofbw/gbOWV2cHauX+2x637EhxQSzu3k++QAfbYRJ8II9XBK3F5Ywwd3dzv7G7b2e27aQ+uCHANdGC0MdbdNs9bOumLTMu1D/r+HEYzZ+dhV+18ToZKXVUPumv6RaLzRCdg5s06Mo+B9JFpYiGfk35+FdFf8szzG76AsYVS5fqrO2N1cva8u9730Vc7e95a//kiw/pmEaaJhnwYS72ufRN6hXb+no/1yvYA95TvPOD+oJ+e+/2znZ6m+ZBIH7lNVvMH+Xpe2drocF5leuSKRTF7WNFIvpl4wkMDvSOLIg/yIrL0LbWsLmzdK2feZaIlb5E+Mo1fr12WWE33/6bENTNfZ405AJMz18SCluwAFj45b/Y9uyoEmZ6QPJCRmTfBltp+Tvr51bK66Hap3Mq8J3K+dqkTojuQnnmrPj5ESdUDHRWd/sg3OERJhdD5/Ti8qx543ykIgC2EmP8ru2WcX/2JCAv7C/D99fELAPy6VPrh4///v0mk8LzALhAAEICPBCT2/zdV/O48CCBwMPdjbjEye/kAtpqq77I4HbNwwoHRN/QsAvUTpVW4k8zzkC9GYiyy6YHIqmh6WT1INp9KLFYsShUGgegewqhxLHv0Q2XS7UcHIwHZEQVF2vTYFDeHwGkO8o48P6UrS8ygaHdFz2rLll+JDJfE8AblbGXQb3EjWAvhG4AylYSDEYTOooegZSBbGnFnvR2TOTKP36eJWpWb9bDIWnVBkg2yXDDSk04mB9lXRMLDsUG4GI8dsagpAjIgfohRJSJjPYFo7Qj6NBRPKZC6oGcQ/3Yh6C/0CnoM/dJ6DX2zlSeZmASR/3/av/MOl8fwQsdHZ/gBOWVFy4MSt4SNYt00H9HpUotWW5N5vQCg5E02q/ypLandUfvwDkAAfLTdHAgiAgIEyEAEcBcYIADYA4cwQMIjAbz0pbYcgXnwtkwg48vDoNry5eGQoW35LIgCTYSYJqWReZtx8FDvaPVufpWKqNzcysetmxv9CjvcPPht6uLjVERJRK5Bl27d3Dr5FVCzcwrwMPMpVoiJqdgeiPxlkNAQUapCnoPRWvwgFuUbuyIcVfmSdrizUcpdbMxxB5kmUdxeGfSIjyLtFm7N7OAJSO4KAGzFcyPrcnJvOwIsm1yrLl5FqYhDGw/oZCsRWUI2NYfyEODgGNcr2P7H+QhCQMIgDAlHZgEVTY5cdPmKsLCVKFWmXKVqNVACIhgpJRW1Jlot9AxaQ4QNvrfeJn87EBISgUQiUchsZA489iRzkXkwg0DmIwtEQ5AYseLES5AoSbIUqd1zP2nSZchEtlAWCqpsNDk98E1y5aFjyFegUBEmVr+bDBtHsRKlypSrUKlKtRq16nDx8KEEhETETbkSjISUjFw9BaUGKmqNNJpoNWuho4d3Ngat2hj7w58xdSRmFlY2dg5Orr71W9z94Ec/+c4vadfBw6tTl249fPy9ZlV6BQQPiotcTkDPs3w/3Xb77A8q8k7tlkiBt5vJ5DFJvNd/eWCQzPLkRN7NZw/aieaBmqJfn6KUOhhlo9BHV68dvlZB3LofJAru5nPotmOq0mHE3EsSXoDYsRDZXVHCM5bbaa56WWw3iEJGdleUmPyc8IZ6WGy2nIZDlHy7PTY70T2YJIkb7FbNAuWwwKZWxm4Gk1PK05QR5VdroNdO9AxqUvApjJqYT+SpDJcnwz1HBlGR7d9pFpfIcKmJEeo0SUqHoouZWQjx7URzlc9Ap9PsC3g95kDv3C7VIKrr+fvMklIKl5kYIZ9BbMxp4SdCXcS1pexuDlFzst670geJFksQdhiDTBk+65oyiqlCCy3MOIJncirytU60n8/kRjX/8TvDblvoXXFvkUBfUy4yRSgjQTObVU4qCA/zRUm6ho+eG60g5ovBdj9tV3oY9dIhtu/zSyNmQveGnRP4MVQZOQhFJxnEyJHJ54G6a7fzO6RYHAAAAA==",
    "60bf0aba6526.woff2": "d09GMgABAAAAAB6QAAwAAAAAPdgAAB4/AAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGx4cLgZgAIFUCuQEzhQLgzYAATYCJAOGaAQgBYNaB4QLG1owsyLYOAAQoVeNomIzsOC/TOCGiFD3gF68krzalo1aRVjRKrd3ymGtUpQS3T/q5H63i62YBwNDYBEzZsswm2f4ahPwOCI2QpJZHnzGaH8b6tklilklaeKRTDKV0EyiJxKh30FoZsl2ANvsjOmMwgoQWsJGUlFAQrAARRsTCwuxerpI56Lc5jb3oc71b26igm7f6/r0M9yo4u/Bano/xWMegxPhe0rVWWSdA1Th1+n/zen/b+5OD4kviTYD1iWCQNsZO70GJ/JO7T+59f69sBs5B96m6FOl8qJPa8MMkhciTsRJ8g1aaL+KdFkh6l/t/3SW7RzrLuEKSekOiioIZeqk6FLNfI+lGY0Uj+2lWSAdgeQllEJah7EokbRBOexUDhC3eakIyusCVHNfbjqq4/edqbtvMklb25wcoWoH7BOHep14HSDX5RHqWwphyWpek+VqB6hJSIeQyu9E7/fbf2esF71YXKIcQgX0c+thCmCUAAEstmyTKWEta0A3UHHKLKzA7/Ov1BDBQyENfAWZ7nxI1RXKGpA3Uw3sJgvimIilQs1I3w5ouBdp55HEFDCCmb/Wfv+PQsmQ2mycDm4BckWagemsgQQKmMKKRbOeNaNYTPdkOgJjdXkX31DkbC7lw3w83QPlhwpCoVF4FAslQD2dBtAItKfhwLQeyuEZ6Vu7o3xQATtm/qC6/uO9egtv+9vzb95a/by68vy8M06b9qF9tgt5du5LT01g4dvMdx5WPAO+g7HrwaQfgBoHEL8AhoLIN27Fz2DJAsBIDHPJsfzZZsWyezppitixhdlSuiDNYdOOJsZYsB0xIQKGEJMmWYITU77DdExZsvYj62h/o8whEEZ5DseK7dQ5MTtxaTQdKzIcPxBrQmoyO+S4K9MalkCLTUjC0l4MwjAmmjjK6u6OU03VMFbHxx6QJf/Ux0Dp1hnagfCd9GxIT6UMzF2nyqOxGloBCQOrm7pKZX7s6gM6hyUNi0sjeveEIUHbL741Mc4tCxwx7nRh2ISUOGv1FbxjXb4iiyJitUK6oyQr3vQsw+Mj8JK09s3vqnjtSLCYWYK6hmvMSQo2v/HwnsVP7UFX+8vjEBRBFDu70TeJNUWM9HQF6ypty1CVyE0GNmzm2WcoMHBrKNegkRIUdfxZFJn4JjLPR5a3ZBlrRRGUMpY4PLgiw01vCa6s6+twXFtT7gWcVWgrQSWSRsZdW1Ccg4q26YAacjnTLeYGK2ZAuBKetShYraQ+OGSjwn255+7rnM8Fo73owqZ9XAdVnlqgGzew/hViRzWo6pwg0u7X0DV45bi+uMaKyAi9jeCMdbNHlmYXBIp4UcL1MbLxlrBDQ0D/LS7KpBGZ1PRWMNewh363mx1rA2lM3egoA+Ak9HHoc0tCAJ/b53m/n7ZBrAsEyjeyaFOSrg1ON9OjQKDZumkZyHPwMGmm3jNngDSuNvjh93mR0aYlYA+MduMw8kHF0qdYhTzQ8GQwhNasffMg9CsvuwBpICDA6px0nhY/ahNceYDdB314PGcdTVTKlO6RHXNGBu57FJSBfYhaqQCPTtFTW1vzt6TNCXqeVzUg3z6X5naoOFgy2rSvFji9QZioIs5KuAM9XQ+DgtNIrfndzIagH2rc/8iyxZrgeL8cwpPKFkVeDGD1LLFwvteJPGGdlj8ugcdcKBCK1S4lBJPdPPQ3P5vh000gGsrLaFIl7WUP/noPPfp5T1eVXtxwXnPRD9M1SzNu2OgkZHnTuXyMxaVJNsCmkUUbfZ7nTPUT3TOVz3/nODK0sMoaWbpYuMO+HoKs6i76LRhfbpjCY0wFpzrZ5GcvxjLPB/wUec9Q4CfONOBezwFboHYvj3WJLQU99KG5V5VrV1bRpxdJvf1yFVYzyW7K82n8QoYyQmuQpYwc46SMBZoWH/j6UKZ0c6ADuQkwgxLMXnuEh9cGypnQ0CEPJ9/hnV+IxbCxaQ/q2c8rzF2seJ9qkvl+m0hNbkbwjY7XGUFnryYUQmFnsTPE7xK//ve2YGvULB9eApsrbOQP7NoMDz6UB66uWV4sV9XG7801jrh2j1ugijSfgIbqbwkWUS+kkoK95IuePRwy6hUD00unKwLNh26fobUXthZSLPq/wCDvSaJaaV6FSp0kRcdRhqqGmSGbe9AeZlIuwT1yBvwNZFcXSyYtUUd6MYDHJdBi7TlJxFiT+zjeofU1DZ6/3QVSqWnpI/J1M9Kufn1GOJwDOxRgHnaY0D1amCWDWPMffQOlKBfcCZGVL/IcExXCMqzMdnZnlnCYyavV1ntP0ScmrFOn+mUUwpkGy7CyVNsIKv8xnFRom15/4o1TojfWWjMbT76pXFUXvg+jaEI6LGaCi95OFkxsmXWSvDE0Vt/DLpmyHymDUKImJrn2Rr+7KbhfHPt9a7nZ82xFyZUfbr12V7joLdou44LLPoBRZu66j4IFlLLGF0k4hLfBm+hhGj5/rkb2I4U2X7goB5mj8u1Hz4F8/rxTZ5Pg/25ahTwbYBsEaes/oI+06bPUTH0xyt+ksZV8Pmq6TsD9CxWg1O2sgULZb1vpQZ9O+UWO3dxwihYZQYLvc55koBKjx0/Jgk41FMG6D8bZphBcsJBASzhpRpe93GZJmwzTUGRxxL+7Pr/pwmNDdYnxcRm84ecGUY4Tek0lBTzUrQ2FURfBvOUnZL61D9BHeTA0rw3HaUY55SXfhMzZ3XkY+uYyW17FemJZuQXFGkb7QKA7Ogqt4bKF/vjZYQ3cysZuFR5IZnEqfXEFXkVziJa1RuQjRSJdMi0tyh0GsqEpvlhkz4JJ67JZbAIF2azCkF8P9Ssxfa5ab69puFtgovKDTVrB38F9yrGQe+Qv0+7dp/aLM+ad4meUSkmhZHKCFwET5wGhqduffoJKneRm7qZ7wtp4rTdOPpe/0tlz6f9twSP5ymCUHPOMNyqVI5VC+ymcMdd17mQ9+YuLaJidWafsv99N/h/w3DBhdOmLG5znZMkxwWNO1owDS6DHM/s2Cm0ZXcEuL7W7J4W0dx3micQ8Itl+ZdFDf59nz/C2eGTzha5rKPjlgjH2/6J5It6HT832R0OqfkZHcGG5URfJ9xfXRphoMg94g53NWu3DTzzR0Ly6gWPkySdxit8nU3qTzNEMGfMuCydhykmmxeYlShbrah3NJplsH9EkJVHwFZ23qtHR2Tc1RsHtUDVPWzyTp3l4bwUON3mwBlbgM3KbJdD3/4R3fD1T/y9PSozs1tVBbBzzAPdSyymv6sRcAX3lGwrl26jIbynkbyPBsR/t8GrA6ZXO8VX/EAevJn3q9af3Bay/ALQXna/bdvp8ybP59Bn//vNAe9GF1ubTyr3Ta2wvlO3k5OuZaZapcek1dhvqrTQ3Irp7FF4FeGmmLC4htzFCZJUWl6az7au10dziBnUPidzzQ/hKYZ3zXd098kDlrBcmuh58GwuykuUyQaUsyJbLC7OV5vG2hdlQYrCcwyF51AQF1XjINIU1KD+vyl/7rlL1sTncEHddUKDOHdIG83kDirboBA2Pl6BNQG3NCo6KVmkjxJLSqIgMy3Peu909Tnhg3I4d7t0TubCMUb0/MX5++7oNA2N7vVBsKhKVwdmuGsIHk7qQohwjorSsDrVvjy6wqAwxBxYPERozuWefxUo5M/qwV05+cOVnVpADB65wdXqCHhffmJfh197j256jFhj0hAYMV6dRBHT0+3cA7t2RE7Mnjs4cnZidOAL2E5WYjkgMFNl6w+9/5qLr2dYrMg7wmI3mXbs2mT+c0nG7d28wT/Vl4fLZbOiyc7H5HM7fplxwQ1+MevQZBnq/aa9R6KNRiwGBPzsHLNUifSNd1N7cqtFuOFcu+nfs7QhE1ve3GOTVUTHZTEF86kHrFkp3HLOgJlrWua3FsmPOOwcfaBWEt4rBjKFTpSTkU7/Ak4FzENF8NOLcvSn5+/KWpRbntvVfbgAWlVKLifcmigvjqVU8w+C6ZkULI64U4ufwbsGYOCJBjfW3x8xdegptIe+Qs9hMyItNwtA0+uY6KUfXwE7e32KcMXVf2NJo6LHJP19wbRlH2EvADuNx63Hwr/gn8fVfwgNPvgb+FS2doW6MUqkkDon0aJpsFys6iyuRaDuiZTJgSAmXvzZZ3x2gBwWK0GhhYKAQXf7ZCh77hED4DIt/jIfVPbFUlDKfIwqmFjY310u5uga2fG/LxVNm/fwWuS6WVca+ULjcgiEOYbHDeMx6PLzpmnsw9/DPPc5vD7T0Ge4Mx+EU9xSQIv+Y438MX4e23/trtTktFUUW1uLJNUtigSiI6P+5b4Ax4KMAekktK73lf79OtD8eO5utOVal5mxrVinoYuKbXUpStDRdJRczu8tkvJC62d37iN/TnEhYCrVGJuFVtTIVtWcry87VNA0NtpWmoJHtxeSupunsgona/dv/XG0PSoJZIYE3/bCO5ACjH/zR8C+u4XMwvnwXKmasTXolfQUxOeJ8bnZ7aV3efHp1W0FmLC89fzW2WMqNkxZfXheL0mDrexoAeT3j6Fi2duDMJt+WW4QEEkWQWpiWLqWAwiThloVtOaD1Ye9ruAKuGE+os8bKy7LHTmTrvOe9E901eRmZmvwMQaUA/sM0vhh90f3u4OL84kHwNB7w6/hy9EsP0zz8c5+TRKmyIC0nOz+znJxr3qy7Wq7WDMVmVh7NVh+t0MrkI9mVg5PdHjqYMs6b/H/yN3VL7H6yg/9o+fNgb7zV3NNZ37JlsGsB0jl0wS148DgqOiaEPQx9aalyqYT/Rh/tGltagf7rfPQODgwcGxwa9o33w6nrH14Hs8l6/YZT8dZbtpoAb3M8t/CYViv9x3OKS47lFDBUkJhbLD2XoUlXZhQmyVSFSgV6yaBklKU1xJrsxye+6jiVgc2uEC4nyeSK5L3J4Nck169BF/PskyncYdx5JWBwiybxfUzg4EYrT2vTfLSqicUu44mTq5O8DiHa12uITVj0OoIGlmwONn9p1TewaUH+IT7I7TwPgZcyJDadL+AXNofL2nc0WJffcUkJ9PrIx2Pl9hcJXhmU2NTYuNhiAzMNpMYDszgT7tIB+Mt4D1NOp+sYe017NWnDmwQZGesEsqGivfDG+Kvx/98+Pjr2/6H/IX7H/IfGXwqni6Z/ed94O+2F7sW9qidpT+CX4SX90rPX2pXMrwfm6+efvSj6OQ8uGv96fs78PJPtLn0cOB3CjVmMBm9GH1JlQIDV8KED+ANjymK4YnR53Torl8CBh8qx4pvmkBKeHTX9ipz/BWnaHAcfk64OXwWrR4P/aHaCd21sb7WQz1JQy5JN4abkMiWVya8WxvZljkRPkikHYuiHKOTJGEDYKygr6nozM6vIxQ2YCkq597XJ4pMdH5Kdkh5z6ckiT9HBu1bU2yNUVG3Xe2i/9IrCfchmT+Kibb70KN/eVKXoEYp61apRzWx0JcUA5tfmXaAomWKLb6R+iglPunFdml0fKbwHievUoh79RCoV3XxRV8ZyGPZvLPZuKZRtVm8xb+GOc9dUdzU0+xgn6pxRj5FqiItRWvhFkFPYXV1Jmr79rfba+exVfEmd2GKRicSJjn2jw8NaG13XoxOZqGFeIRSvMKrptclqVE1jQVnJN+Tz5Kq+iSyMDDeFQ+lcvGb/nbuiiRBfhXeVCdbsm68eiN2679H3j32fe8F/ry4dJ0HMr/SW7lqRiUp1I5PdFBnWtyBTvshwk3QkPYQeWxh96omGwQbb6HptgC4xdTSTxoRvbAaESb3qTFmvlkqlxGCZTOsbLEl8r5rJrCISc5gsNgkQdu9v0HeHKJ1qyDZxTcn9tYK+BomgKI9JM6FzxTmCBhG/VzHC+o5AWGEy7xMJ3zMhYDUvhn4jhncj9g/TQlMxPLQxRAjUMVdZB5E+Z1w9byVdTglk8VkR0anaUKmus8ouc0YqQ/r0unrcDvk0FclJ5IYz5FqKCPpOTKju3flIOC4cNg+XjZfNevN9oSks3Jw6mEljFtX11CYuUsPwIWSvMCoILmqbbxjDfjcuuAEx6eFbwh7LFamKR5vDFmMb0xtvqvRcPewq2ZSy6d4l9ILTY4JSXxNXA80IGAnz4nPuDKLf+Dxs4tZz4ZejP40v73/665PHruyHpOOuR9A+dqJk2wS/3LrSQukYFnU5wN1WuDbLnxklybLMyiTTf8OF1c7D/zIKOyYtrCvN9bNNSLYTeQtyLWFl2DxnhgQrgbeovfP32Cv3gAp80Edcx4DMrdWr0IqISUc3/2cJOxBtDXrlvEHwZirisVRsAxvut2TKt5FR31Io30QpXCa8Ht8B+e5m1dk16q6qXJvk2OQ6u+7hhnqJNTnEhuyqdLzGzhoy/MhfhYe9IUPWyF5337w/KWpkZX+KG48jjC2ujZI09/WsKT9nLeahfUke+y9M9+9FByZ+B5YsDkYs4fGmoiOfxceLJUoyL45dhtkEgs8iaI/5/F/ukbL4q4lFaIwiIECBwcQHQOh5dd/+nrO9y/3m/uu953sO9mUP2z1vJ7WTnoDNCN18zGzyMx83gws2jR6jqAyVVrTUrMlapOJd0QiPqdM/7E2sC6PJhN9TeVakmJQsVtdLlL0pxTMw8I/9JM/ZAoBe9Ska81mHJxj0Y8yZqcnoe4GG7z8Zy1aPV1Soj43larWHczXBvRg/nK3NZPdJhOtycoRDfVK1WrYJh7OzESNRx8pL6YwSPh9YP8fxafo8R/nxb/GBzjSac6DnrvTjjsn63DTwKs0tFMs6SDsKdxDxGSRJXqFyFFkQ4J+GDEr3D1AgobM5dWpe90z6VIb7kQzTs57m3os7gfdpcQyjOI4XcVQ8XgnTeHGopFdim1ItEiszwmtOlSEWqdTiotNxtqFpSpzYRiK7pcfsRBo8/FycnV384L3fBw4PgHeZobBI01SoVOqLC3nFFLoixgdX7uvXTCCs8/dNJMBAvujIzNuZI90Wp46UzpZOhLD05Yf1oppuESfYDeGJ2MEtkinlsngK5pwgEDx7VNIcqYoVyk10slqfiQzPipIVqnjyPSRP+1nnwGBUjE9wkLenl+MmsLr4j2bwnzrYFBZuShtSUhlrZ+xMXBOFigihIKgUODBG5VAPOfmnVXHCNSxWeHEVJ20nrCBTmRyuiskeL98U7OkZnNyvJ4B7cv2Nwh0/gZcgIi2fGhcHrD1RUZHp+TRWSR4tIj3KEYXw80MEB7v7+mGCYRCvmDqbMpWy1vCn3m8Cxo29xrk+4+V6ng/sCgLPGeEsy7bc/eQmfkbPrxfAyYV1C3NDC72NcZSn0Omnzdht4hc/a21ZmNt/sdJ1OM4I55qs5+7Dm7jpAcGAEPp418tTM/P/ZfQBwXu4xgc7H/T/deBy9cPIqju5xvj9l3CU7WSYmLrnXS2vim1DVS7YcAyvne4s+8EC8Z5C7R3xRGC8E87pg2CMMVx9hB48U5bkl20Z21LGh9M5AwN9/V2dsq2rt7ujx+zmOjoHB2Gv8hC1XXQDu7nmXB5RV6zbRmsT3al4S6Ffjddu5pu3iZHXqEI+nfn6rSr8ZvUnByUYVqmBk6HpNc0vdhZ1D3eU/SRrweJayMn7k4GanlQzxFbLWsITlJEhshdo3BYbpz+YPDBexqHHpJdSE8o7il3yTomDfD2K3BD//OKQIjYl8PO5rBQ3/8+xVAvy20UA74ZN5EhqLoHPveGubqtVc9SU5mRjcrOSUsQfcY1QwFCQm+VGeaSiVaQTcDpVSyTbfRTiUJv18ckYen1/36FkzOZLN3VdndIZs9WXqMy1bVSfeYf5yQJJEDuVVSbfMSBNS18vSu3LyBD3dAmSQ9EETqG/sOAVbXpfqnciaeiHbDZrA564j8X+mAi/PUqPC/+XNPN25vMTC53B94E1WsOq3jdTJKbFaJJVfJmhsidrpDSRZitNOLwz14+Yw5z1JJWOsv1I1Uzw9pQgIwQNEn6fQsHvbRAJwiWEJaXpZ/HYffL4CoH4gMl8RCTeZ4JLWLg5HP6afrHzRc+7+xfptHykpuhQbtbxigr57BzKKaIXIEOjFw+8GxSqIllSRpFSmaFJkqk0SuDOO4gbQy9j715X2igVphVjWMqbB2Py5yA1TINhKnr4oi7VMsn23yHct+p3E9UsZi6RmMtkcUjw/onDKf2HZYdk/WC7Ryygx0SNydJi6DGsVM99Hh7ve3q+35W7zxMCV9u85R1rWx1xNcVOSpmM7cU5QCvBbi6Chg/Go8aBXv/hOHEcfj5hbvDtg3Lj0uT2Q9o00NkTXvNdkyf6rpyisHGvMXenxCSSiEIhSTRumYRNkmgiSSCPj847jxnQFtoWrrQvwI1pPsnrtm/L2U0D3TP9QXWifIaHiw2zQIzUnertGijjmrf/bS8+iYKf4uwoOGXj4mRzKn9nrBEPAQsR9cofNsKKMtq1Pr/b6rz0fJ5kYbE1f5Z9Wnwavvlg3DwOkHAfwExwAzAc3ABiBxDADYIt1oEluHgDJLj2naUj3L5A1xX2zPezkUlpwCVf4DWHsNL5YNkvRES+jdKAS6qCSmlEQT43acCl/jmobHkSbiCNU8QnPwCkAZc8x2umg0pLxEC+R9KASy4FlQ5POC3d0YL3wvcFAGlIlkwX0rWr71hpNFh2YyI2b/++NY00JEs29IdheLbVC+fEn22qxgCWqlL5YZSmOrhmL6fvl1l+SEOyZKIwzLVzbVBp80SNiPqs10gDLpkMKo1QLhpcNZX6Tfr0MIvbLMlyVipbg0KcuDEMvt0G3vr1z8ZefgrqD7Czs/g2PoR9f8/OUoX9BhaSkuV/hfk0PGO3tSA/1nOSL/F2Hsv2GgPEn3rOl8wY/8FUdKDc//ZX+cp9Th9RjC/5trZDvX/67ZUHzqUemDHRamce8KU6UmuQr7WPra7k4BCm+RbYkdJsqZUOTKl2QwMxv+TaKd1bhP59fboc3ZlcEm8rqZSGSQzZnCHq/Zeh5EzoO7agTv9/586SA6gp2ETQcj6MhL4VFvu3F7fLdZEFMCRsWk7fvRa4cH6vtbL6BjBwdzkA3k+jX1+dWt1jt32IBhjOEiDAbxHKkf0u7e9VWAh+2+Rd/M5+8/IfMh7QxKKQ280lR+FumN/RYP0mZHeJ4m6vhpWScoSxYEuAHRV27/fvbUdYP0RMyIoQOyOyrbKyHTMH8G6zyPKRRoOdDjtHwDeKki2E5MfzS5WUv1mbYxj9CdUzjLAYhWP0B1RfYywKIzFEdzH2PcZNYLSKce5QdWCcB1SjGFXDlMuta6L7nvWQKP694phXWGepiOyhusSMaQeSfCLgrIEfkezzJJ9OYlRAYiCtuyZOU2LKjI7ERfazhkAxPjL4lHQ62Ik/u7noZ/DfcQjPMxPVenbVxDL1LHNr/7//+G2FLDwRtyKuo3xCcKOZB9kYdMk4Jj+g2K0iU/htmH3ZAnqPeCdDbUUkjBPArJ1lH8/x5CQjbgRug5zDGezzvqT8mu8EwiZmHw7gsS/F+CMuXshVSnUFKwpf/A+rcesTViGZgjVhk0Xxn9n/rnzeS5bhCIW2NChaeIQk0ADQ0Dk0/MNb7cOl2iJa2HQ5aMipW//Vyycc4VAohKuebRsEAggdkE/aciQNQUF9tuCzbIwp2YcruzjNMmfE3XFxy0ah8SdCp0CR+IlSsbDZQkmFwq4YFXcWUWT/db4QNyIwpyPyMrAA3tnGUS0bFiwFsQGOA8USGKGMFYshdgBuuzm1rQW0U9tacnZ0Wys8RVFr2m3XsKfmNvY0OncmS8BpeqGv04gllMxLijWoMLierUfTyKsDrzV5uc+fIpFMKsfLlnUq6HZIJdRCv7ppJKhVrUQUmjBhokgoJUrBhmLfORRxjxbx6S3CkK5UuSbVNBoECT6laHVGlLu5DCVC2E+FojSKlxoE77wh8EqPKGZU8Zq00LoPdMWJiDWUq/hQTYpmXnyB15gwqDK18OuUaNCKEJUuiaVvB9vPRRj+DkRaWIHVX6D8L2ctO/YcOHLizIUrNwjuPHjy4s2HLz/+AgQKgoQSDA0DCwePgIgkBBkFFU2oMOEiRIoSjS4GAxMLGwdXrDg88RLwCQglEhGTkEoiI5csRao06RSUVDJkUsuSLUeuPPkKFNKENYwbMOiKXb6xzhYbHfSeY7EGNnio34hf/WZz2MCwRU/94pD3/eF3fzpq0nXLphQptk2JT5S65mNf+NRnPvetMrd86YZp5X623V233aH1vR+sV6lClRrVdA6rVa9Og0ZN9AyafadFm1btOnW46IhuXXr0WvGjS+45ZSZs4b4nHjjtjPMuMDnrHLMhH7hqzmyshU1+Cjvr5KMymSX/kG3TmYqw5fFh5FTBGgnR7SsT+Nb/NxdG2yNWhkcD",
    "7d93459d8658.woff2": "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",
    "9338e65fc077.woff2": "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",
    "a72eccfa6cfa.woff2": "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",
    "af5fda16a191.woff2": "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",
    "bb1f2d582e7f.woff2": "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",
    "cc762462ea67.woff2": "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",
    "ccfd87f69ef0.woff2": "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",
    "cd36de204aca.woff2": "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",
    "d5bab8e28732.woff2": "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",
    "d8e4fe0452aa.woff2": "d09GMgABAAAAALzAABcAAAABQkQAALxFAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGoVPG55CHIZoP0hWQVKIeAZgP1NUQVSBJCceAIIoKxMIgXwJnxQvVhEQCoG1GIGbKwuEMgAwgs0UATYCJAOIYAQgBYd+B4kfDIUfW5gxcSNacVv1x4BuMQL4Ss8t1RmfoIBz4iu3gy7y7Dc4GccswHkI1Dlfzi/7///PTCoyZlI06TY2mKB4/R/LjtLk4qCmm1aht9EKly2RtI9E03x41nqIDSFRkqV4wHJUFVScDvw0NWF7hRcGrVR2kZWQTRbmMcmCUIoqvLdH2KHWlJDUR0+c3DcyTzUIbyguosQun2RUKdDiQZM3CToTIx15n3QJmW3FCiFNk/Nw1lLQPHpL8iV6wj95KAey1N6CbJkvLuUj/kBeF756vm8/zli3fXdr6ZfECip58brwWrjhYt1h17Iv2RJEorpyPkv8e6s//0c9w9cdfif0y6VhFfvuloGxi6G0GGNd3p+nub3/726MMWDMgTARRlrYGGBQNRmlkiPSETVH1MiwsMFIRDARqwkrwMRoRCzoLQB4qOwe/k/39Mw+MwJDWJXLCuVvhjAj4e4O/27W/0FKbXamHe+suM/ufWb6JUZzzWRM2ikt4gkESEiIC8ESoAQ/Xmc5X2Cv3kgyhbhKHa6vCoFo7QU2hUDSNFa2s7PdIZK9RZOiugHYZrFwOuecFbMBA5MQA5GWEklBJRVMFBUFCxurURetGDmdOne7GYvqv0VfbRf1/PPPye4nntBOHiRRBbxOQEGShSlmFNDevbrXu7PIEGTluVJ5JNCLA8ROAdgFcnHsMjoFWpaO4+f5/9+vct/3C7sGiNQIl7WqQyDszMQlNhbfSU3Ah110PCpAFJq4h+e32fufMEDUZdx0rq82d72vrq/aiy4eHxCDMhuJVqEVHGn0VIxZebMXhcPjpv1LAiEKCQkREpIQAsELXqpQXbvO9URs939pdl9FT77v/s53PtNOvEp/ni79P5cD7SyzEYq0fWRSvOcvcmc2/QQeoIKpkjRaj++FXlq+PknbbKf0ClCnpQNqGgC1/84BOJQE0pvBNqMSpDDtuulr98ye93LonOjX7GfmI9Y6RQNJiJHEgHezb+hKu2Zdk5pDHYshGop6EAsEghRatse5fdqfuT05s+6eWeade0uJkxTwI+av2UGGOTRuxh+RNHsrCHeq/Ubt0KY1kkY8gtUum2LHDpDzQNBVekrpuryi+eLjN/n9lreSKInaiE20EqJJ+gZ32xNMDsdYd+AbLjJB1K81Uie0CaL/BHTzq+LECEkgiKrd0m5bfWj5r2oq2T1VzmSAKZ/46TxnblVXXe8OzqfSyKvIsPU5wM+2PKbKYxqqcIDHi2fUDgAYcDjo7ngblKT/MzVtZxHIpWRaglIEHaGQi0a5ci46Pxedq5n/ZzE7s7vEYEGcgAVwB4IXQOLCAkeKQQkgFADeySGnSs/VglSAYq5UOr0+xNJF7aJ1U7gu7dq1/69Uy2t9kh/T1CbQ8qE2Fx0/ZxxaGofrSI7p7MPFh1OjAZJAk1w1QMnbBKWZJiStm1QqgqRfARpOoLRJcg5ySPkDkNZFUHouitpnSNpAOeVjvMV4uPh2WPuafkbVr//U/FBrrSynJOfAQ4Qi0AD6j7RBmi9PuWTXbJJDuhQitNnBgwfgBnQhQ6NLxY8d4ff3c6X92f9ygNmUti5XYiHxC1dSMpsDopQ4x9mdk4C2hMIBuuwe5Ti3WzjAOgDSCEJWyHpJwpaF8xWuiIPjQ4CBNQxA8kzWqqoSgb4Ni8pon4yd4fVdv/am+u3at5RRbCeY8TAqoRvKMFSl+Ehu+a/9k5YxLQPbWtRyFRcQltyPYUyzYuDWTq42UyNulClb2v5QM6YJF+H+TEOSVnsAFbC2mb2Qfs+vHxSTusbSWCnNzdjP++z35fEao6iEEEE0gEidueWAENgaU+jRpDAmQ8sgtgKuqRgxqUyZqTyVqfW2pLZpTZ1zU349jyL06of99uct9deQRPHZA2gDYEJovvrrn/8GDEJ8/kMQwPsiAGwB4A+Ag4GYPB6CFwHSUenyItJQ/sPowiXXbr+XPMUakdrh81t36V/ydy51LYyXi8rcw+yYgY3xSNmXPZV81U/NN8Pv6nvB8r7/btf+IED5D4WK/rBQ6V98q/T+yt+Cd0sneqcYQPx9f7jQYdJVn9g1XsKFSOlFP+9LoeTrP/326Cn53Qj63bj8u1TFPWeTB+HxD/Hqh9TSx5DIf/tJewzjPyegXvxLeRHLeYHLeenk9NLd/aU/9WVwycsI3Et06iu7gFfulq8QRFjZr5CMV5H0Nx6QN2GkN0gqBL2qfPOmE+hvw3HvQvkHEJH7Lkb5PjjqPQr9Hsf7YBv7Acr6AJd8tMNWnt9vZCYPYitPLv/jLerZ11cdHhPPHzfOnwpC084/vvjwKWbPbX3k+igifP1Roe9RmblwQrywEYYsXXgoNnDlwmsrHjuhi+vcxZc2/BmRrZPTl+6SLj1lXj5uXTkmX7kFpL1XT6nXTogDpK5HieC46NSI82MTU8eFqZtDU0+Xp15c/C/app8e/ff08H+yw2fD6xrO8y8FJJJGCCv/F/QF/dyFidfg+gEAAnABQHXwH4UAQIP/iS38emHhVwuucfSpq+RlKnGVhVOj5dOd5ZY5RAszrzbXDpTW/P3n+V7/P7+7vpsj2uahPOMD/ft+HUJ83gCwOPXdy4WyBIidYbFVqCOO4nsB75zSpJgkLygMj5YXKkKS5KUycZzZTAq3AeT21CjxFXMNNC7LyTuACgDcEMDxbWQm+KcVAw0LqgUSbPznkHRMNN4cLTeLDhXEIqvt63lgAFh2JyCgHmEKY+3qM/0ZnaPloVtwVlStt5VJj/x+rMMiiCYBxPNDNKCyT8TO2CJYo6P874/9w+U1liggMmEC49ciJGL1k3l30KDQCOTOBpRvvygt5fEQHVq3J74Sr8unAUMX+J8DQAXHAy0cMRHmKTOViCYVxAgDwAF6xdDFMD6mIxfr9HPpb+0kiaSvEYRcs3Z7RAIxYNQbhwT7dt5V0YMZoEQUh4LRQr0kkygAMY9gW5SYV4l2Ii1Ls+5oajouxtKToCT8e62lMFShnhGzgcJvOoDl1ktm41ib6xOi0Ks+AMnKxBUBMPMguYnJFxTzfgMJ1L9qHf+1q+C12zAd/7/5d57i73kJv8fvcJk1PNOXPtbLelgPa4/WaiEaiLAE7+EdlKFZz+Qlj+WmnJRRGZQm/KdLrIYVWZ9an1jvWm9Y7gKqIjy3tH9p79Lf1D+oP1C/oM6p7xn5eOSVkYsjj2HTWD+mK3FwevGtxf8t/kn5jfId5TPKh4a/HH5l+PTwcc+kp+ihPO5d6B1MvJh4OvE7/gv+Df4J/o7j7x9/4Th2/AF0FC2j4G70nl44uPDiQryfX7AfsS+xGnvHsfhjF4895p52F90tapLsqzdrh8xxD5fQhLqFqip77XklLtFa7ycIwqqF7GtpzVuzraaueWgCHXACxiFthPSTz2vI8AqPvq9tjYLW2ppaXdvYytZwnkCKBATBbSHLNmcNbjNu2lPHBOyAvjpluA8f8WKhG3kuj42WPDBqJ9iB9SjZNTWjUth74AXnF1t231yYJqkvphwmV+lRmJ10NIT64mPqQ7+YDBGBSccetpZInyxdK2iudV5JAF2OzFiLDyALzlFhrZ3sLWeOcse6RNSj5h2O68WTZ41aXq6twSlTjovQ9Jr5ZN0p7o9KGjxcYvBK0lgzehUzGeZE52fcWoliT615x7UxWWdlqvf6La9Lx9dLDF5xsm1Grxi0V1K8k+LqqEcCYAyKY/Irj+ETAGgHmwoclKmhi9B4JU1pjpGAwQVrWq8iRkE+7ZzBKyHMWHmUHpjRq7YR0bKeOdWXGQbvkr0lqG7SLoDkikfMRklXcQ5CzdX9UcnU3Ph19bUWPmPw6k181IlePelDg+wyGIxcxdMISW6N1a0pEJc8smyqrgeZf2bvZNXtfdabqvpSYxuq+7zABzQdQH0LOJ53YGes/Z7pVk28yaU3OXVep/Y5hz6jba4UxM5wg1qfXxPRX7ngmYmT1TgghDdVjR1Sk+qxXvYjw4IzWuMvTQfErjsE4ZHCiUF706ry57HVuKcEscu4pLziqtGkUuPqUScZu0RKUwYWsqcBAixNfr8b0a6mxr+pC5hDUy2kd/MTgC7l27OgM0Yk+LYz84QAjBSFOhHjiSj61IIY91IDp2SGbxrvP4LqxnWZzwklYCjGxoG5mVEhpij79AZD3HHQpJnb7RNEwmIE1/GtqJnOQsFQPEPjnG17XCCFXNnezZswXfy6mdzpH8W8HXgkFjKnAaYIWI9LouQzPIL1YIpQRyuIA47RmRUFMtO3C15C77V2hAnRCQxXc90nHLbAcfMLIufcX6auMGO266SwtfIy9b57YuiDxo7nyonLaeQkAk53ZATR6yavE0N2DpWspDvVwPluPlG3GntdiAFUXbBLJtRp5wuRdYBexUS3KDbznDUotS7AdFsAXcGJrsGXNGdWDjHrtH4xCFMo/j49rnBGu2VebpmV6pUAMUIp18UIzbf9LlHw7bgvtVRQDGDhosB5+guFuper3Pyk9HzqK7UYINfZga56K9k6VWa9tOnMQ5wxFht7Vc9JlvrMk1LD8TCw9B0D+Y5479aEcHyr9qKm3iYsnyEkZmFwP25aJ0jpBkG3l//b/jOdKdYpgFa3i3FBN7UwdEUnzF9iH+Y/WRS2RRIVtuXM2ce0y+X6VR932+sIb3LvdPEu/X8+rI9yQEdyY0gw+biuy7YQ/RIX6S+R1buhTMMA7x0h4DYe5wlGM5YX7Oc9IlM/C3gHCxR3s9r6ilb0yIYsgIDm730eQq5cE94ibOQ9FjIxKjf37n1wUweAAM5sUxIA8D6eiCAfwJfyknMjHirgjJMW9NcAMfGb/XX3t2daaWW5Svne9XXQcBl3GPG6hnXfA9WPwwNrvL44llnnaDa80Vpmy75nf5+EOEHyBcK2Vk4tjOhY1jBQn4x3MnQsPDM6abmK5z/w4dHP/x3tq8KXIdxCIoXck88m8O805igh/IplAd4/TLW4we1amPxPIyqgMmkkoFoRXTEmFC5hzSJCG3mIFY1RF+byj6WhHSQMeD9PblPBF2aLoI/8HmgXqpdSjOnQxOZT+2ACPy8RX2/ipB8xLfCLEj4EOeT/IG1hwfzGIBATwHZ3hX4jWb5YaE/FjDEQCnY1S1wyqxWGA2d2aCu2KK0MZaQB9JHuuLXb7aPZ93J8dkYj8PAE2m/utGN/E37kGiwtwCfPdunrywVoJaMTGRW4xwpECoxxLwDZ5uwPU0k1fPuzQUODpy+FcZjUGTXIkPVD+h18pz5PUyi7wtEAPub1NW9WqIcmS82+zUkbmrW6bFZsPWZLIWGJ5KBifQf0W8rxj9giUD53YQQS+InlocQzRcLlKuBrVfl1zhLZCrFRoXseShOlAnMls9atkpd4/LIAedZxUa5Mp1JSLrzZ14fcBHl+nfuum6p0EOGL0FKSeJbCuFj6b/unSoJ5ut7XBKMQhTDb7hxMOth0f6m/65564aV+OJ+33BAmQZWUgvTHUEhSFYJzP7TSfZVbtooXoMpLGx7DFolaLpMdvPT7wz3iI127DR4L5VqMokaiarfmeoDmmleeuI0jI0lYERNqqqx5yC1PDgxXXQmzkMUPU5sTCf/Pce5YzV4GO9GCxVgjsRW958Nbodp47Q46vnheYH63NqIXXXLlolganXVt95cS3A9zk+H++fmPY+adJzS3v+qcuQv8j8y7qVH9veBAqD/nZpg+r9ydl2FzoL2u+/76o8rbd+BasN/lqI/vgSpy74UzMV3D6aCaPYt5n1Lo+efhXgRhigJdX4KhCFRujZlfI3Xk21DvCT7gFsM/cDR4P9MdNr8BpWH8B7WO/Rm4t+37b8vbPyn76Jt2fvRzVz4nceBzf/n5eR9bPy+y6QtBKr8gsu5LMTYUatPHs+3Lgcq+HOrFlxMUfM3T/q8Fy/3GTPnf9CX9tkDbD+OU/OwN5P3SUM0vTdT+KcCmvyZYertfwxt71ccqTtsXc37xMy91nHaN5J0MIUnuPVbps6GvHy2/9MbuN+Mb34565NuvVb79evoHu9g33un98ETt7Uc7335y4xOH609El3DR9hwKHXo6YuTpj6hfRNpH45ZO7IqdeOLB32L53yHQ6UOrfnf8kT+crE0+svGPofbZN7qHhJ/+iv/u19JM9Wb4cdTSP8ewf18vTk1Onnp04J/nu/8KuiT9ztkXsi1QDLSKKEexE1w5sfDv8UXv00e7Gw8oQA4U0t4/P/5D/8oQ6N0cX0CWVpyT+YHave4C2KYCcNl5Xq7XpEnBjVg09YoCcDhZ4ICuALkelatDgD7jcoBeBADkMb0FAA8JQegIABx0ACbwDeeKoxACSLkgSowA0H8jc0bapjGCuLG12JHMswzMX3sBjIYA+71yrgWQQkaPQzj+3xCGX9C9Tw1AHQNJw4iiL3VL+I1WAzoEo35wI8HDrDs3hwzAv7a84O/TVvIVBCCVcqEiPEVIBPxuaXiPNXQ29OwhK74r+lb0nRhEKNHIhAGP4qPkKG8EDc0wjZhRNDqMgXs/CY+bfjPQmsvMSu+UAb4x+ax3AoQQ9a2cIRnqBy4YtX+5oKT2+PzZ+dPz+7fpFsiq2dqsrRs5Aca/+4u3Pd09XT2tPad7TvUc72nq2dtT17OpZ9bPX3jT8RajT75CmvfAVN5gAPj8s0C9xHK5kTU4lHoLjd1VyhEHyFMjX0znTUvYSqsDedYGhzSozakD8uSRtT1RvWqH355tm1hltolWZbt0+1SGuQLIPdrep1BqOM4yXZbqNDjpyS6LNbaqd5YPO9ZTOaAxSC1dXiBQcn1T7krPNt1eRzTLV2FLmEskVaw63Xa/LEXKbTo+fpM+qbKV2BCO0kjp922jbQ6Oay29M4CzvJB17eAhx21dmZWZwGYxcQak34/62Xu97m6n3WqKjbpQq/KVcqlYyOeyGS6dSibisWgkHAoG/D6vp/b3cHCwv7e7s93rdtqt5tULxTF/X74dBgk/mR7b38jeGYQnfXz/h7cWIoF8ZhhzBHcgtteX8qmx1hu2Lw0wU+72x4mmP7S9U2YdPsTzd+oNuHdQCZW6DvY2PDS4K3fTbukSKEll9LrUvYj3ianR3wNjADGSCTCu+VYCz7QWnEl4eHSefFnAmPOMTceWZepblxREncPw5DwRjcp1C5RQXQnJcij1jGvEukqg12e+7VwAMtguG9RwIH57tMNvT54SQRge7Yt2FrjOxkz1hfWGadDaSd7XpV1VSB+itxqJoCvF+HYiuSk0VUldCc3Rb6flKyEl4bFPOxJtEB13MQLcIBzE9Ew2lA/1Y6ruTe3q4pnDThAupDXCa1yRIxMhQW5lLzHLkgYlWNwxYrCEcjPM5C5DxSqPOgJCKO75m59AKI/18Bh3a27dnaAyakl4Kr+yyH8IYCB8j7AMMZLF+/U/mG23FUzdidd/MjI4T2bMnEDQ3Yq9sPBJD8wQf9uZSr5FUIYtW1ZUj98eYKtRJhp1LNN0LoEMQrARvOFD4kmiDbiB4M0HY/1H+6d9oFiRJDw17FNtrV57sqGy8klPk4NKzVC6lqeNFRucyhtIWYmL23QdPNMZczPk5xnMfGQnLI0PidmbjexcoqKpvQqhYqahfo7wTEJm8pOZxj0iiagI4uljhPHjwtNOZdqYILIKrGf4My65pM03mvKICG5f5mbmI3R6hTiCxY/NeAZd1vrNfH+DygSj7qlZ3ztIbs/tP5eIYJo076alJRvH8WbFU2vY6uWvjbufemy7pLpwLTIUzdJjW5KRZg9HmiTXH4AZAkzx6VcVfnhYiUZbvOqB3PVDbSiNo7Etb3RhzOz6061GPpJsYNkyWVCRvpfNePazvNaQDDw6Ac3c9HXLeSZnDT2Zz92+8DuOizrI5aQIn3bkt/OSvliaeHnxYdxm3M0K18YFgmda3q2Vx46SyBjTX0CLs3DynGp+zgQwcwOhb6nVu1hcMLjkXfl2Edkmqa7k2/yFNY0WaUm+B1kaDZMSascCo7uWZGSsB7MPZ1XZKGO+GORzccW1h+a0E6fFgsxUQsjGKfiPDAkyoa1xBg9oFiULTK7anwvbUpVQOepUn4LFs2ggp6WqNGXrwTldOOOBvCYzXUDdekBLnsd5gWPeNN8bCNxC2M6O6Q3XHMcp9PpQtgZoxmpcZQx01DQlW48yAWwEqjVqgs2vcanGG4SV4MDNhlabdUd0/ghWiqxCjw8x2tOigprEZx2NBxRQHaD9HeCVTN9gU/y4i8Vll1ZWzRkHc1ddxROUvTUBJgXj5Y7MCLevR2VquJmBiZdwslIO4xJQzuabHUbt+kqZhvQs0HSZx5qqTj3PnBGWEMq/xWyW1Hho9eiIj3hEfKL0FQf0iVWm5FSy3cEeRszxieddHz1sbCIeFca4Fw4CZqbP3BXC6EHogYv8GTJ1KbU8OvzAgFLoW6leEBvbdfQGJguPx1Z0gELxEQtVZ/y9l5wgU5IoLObTGeJUF4yr1aUU0/AG76Gw5pnPGmnpHDlNzrmTBu5K1ugQja12YXwQaejn0jnPdrUFMWh5JEw5Teflfmao27UMoJDNvJczfTL7swT1YIO4P0f1TBfI86C7yDfwVwJU8c074ncmQllgvSEKFSejPOXPXJg46fZ9ARxuuYsDJZS/AbGqO2bpqGlZbllakBcauXf56dgtlAqo7urjrGSiUsU5RUBFrEkEEbAFcOy1Bp+BXPVElBN+KB+gJfo07NqTu8idShds5y50KrsWMtBnX3OzFqSVU9pZjuxGKnwGgbkFaZFAZIv9KO3DeL9KnfE7fyiT8EKe5c1xVBZtzm+5ZndDEuG0YMB9pS7NSUZMTgHI4JVpq8xqiIoJmfRcNT9lmFUTWFrkHdfQ4cjii7a5OLfwS3LcEjj5HHcGRzohXTOUpZblBQQdrQKeuc3KeXu8kL7Wo9lpaWOc0G7NQ9sPsHUEwLPA8gvCgp6U8NjV0OpPQZUVbrn24JzMLAHnyr7hgrUUloIEYRK7gF9SPvdX3AA3n/7bm0/ADFVi/BPAK9i9CWXzVGCRs82SlpxJntt8kxrKJ2BS+X9BzsCAW/upDN1gIFTv4lUX5KpPgpXPfwu2V9b0JoIleeyvh32gNwiTajRwZc03EBV/8TWMvcn9Xj8yfrBBJVxQfjxTtaxlrBQjJARmBNl4ywPX65Ku2ip0fKr12TZUrYsNnDq7WlQ28Iq2VrHD55TWICwGO5iZy3McILx5gvKhQbOyyZh9jMtjXKyuPuWve8sUNd0IjGs4x28tG+gxv8rvLNbG0PqF1IwA/IGRs15zvao4kSocyhZLSKAReQACko+pfYhLdg6PnRDq3/H8PyHBH5DywUh4yElo/Ab57PMfqbjhz0DefOS3xTucx1F/gEc0sG8ULLSGbX/+Sz4vWsKRjNr1yknBY0KDmjCaWBr/+0oewPHUFg/cgOh9Co4A0DtURfaAWYUAoF2lIWo9CwpFLA+/wXIYxFfDWg2HFHkaWgcgsBMGCEADz5oEJ0R5CwA0Hhi9GQA/BBB6GcD1Ggh1NxcMjQPPyghwp60h5GDFyUOk3IjDSaTPfRK+sVAODpKEBN8zTwNsBaWB/I3WJNAFtJNIujzENbjWCOPuMaTWY6fsre8f8b0eklUi55ukqbATtbBaiMNFBDQQMCvuiQboMY611vQt7bHXEPlUhYS4xpOxRJj0jT+2NSWRxxSd4/bs6XCd9FWK/J+IyJNG1Ff0fRy+te7KO3IHwpLU1JUU3JiyfTVdeiDrDBqNYevHuJ3CZObXTCukhlq8G0qa8xiHx3mKj7R1N3izIB2PxzwifpKIulW38VqraLsOMyGtHsK2HWMgrTF6i2mFD95eUcYUaeV9cl+9T+aUkWh2fhPnfEqmRSJaED157ykjotb4SW/Q251eIuGWBqJd3EZsqMS4ffH+NzWaZ3c+AOpIOc6c9wgJ1jUawVihXEMih+wItROVcyJHeYofo35SA1OqT6kPbB1m7rViovQ+EQ0ClQTpzGP2Ugr0p6YhxSOV7AOwfdk99Xmv/EeiGDJa7PY6apt94pqfugaCh8DhfbqXM/sxtKoXdFpzSi7iVObHs/xhxgfI+CYxSO/3nfAqsJjQmN1KivuvV0jRtD8x7FWjoDYVTlbFIVuDbitH5+mXzcIaKWhd8z+WQjYBwRXphJGQd5ULG28PnUgAdLvWsS5eo2Flfdtn76x0eEGdK0WsLxIFxTSwn0wunxrljRkqyLdLx7SErOXzrzsGdWSbnGomgtEEDbqrhHNs62Slz8ZeVDSoJRqLzYiGYLxAbnTC1wlmlUY6PsJA8JFj0YQuxd3eBkV2GxspRSxR3C5kyX5WAImBemA+F7f8iDkkBECIWDXeVprUMfrs0dhbHwfeZfdEDoguPZQeDN13i2NoTBSdqRKKEyGSWVnzSeLUR9dNcYQIQV0+TlFjlkCWOdhZJB0YjdZ2oU7/UOchSepP0hRVcl6Ct/9z4wmgomvb2TYuvupGEE5a1dXm0taqlSmROAtPEDFHth1ySldhGDnlvnTJAjnavHvUrwXqhN9aleebkI3nMMQL/9gilcDVCuQaBQd7w6AVOaOpBVHcVsdjh3VbYBYNCBslk3lbnkRdK1Lb5srudufpQjz+9q7SqKHr/OfrNgUqpVhHC21ykAXIZ/JXigXo5KZbrTeHeV4iiJBKAvjzaeMQQ1h5JQzIJAzxsx7Q9i95rjutKWTyQBMt+xUhH3CgTQdqTg0klbNBqLeU2o7u67RVhWzJ3TX/+2GeD/4YmZcYKSeHaDM3UL9eDu317/pztPSr0skoJusQ1Xy2HJAt4/KlwloNtFvcbHPjH7sUGzBTI+CLK6VB6dI2NeHEkQSp/+2wlZPY47SkHdFJEUuyj7aTcNoWv0zZzsMFAS7qzOe8t0OZ3nXo2b9OFK2DDJ6fjAeX54YHac5TWNWB02W3e9S7TQUoqY/TTfBGCpzPSzKyllcb6pwgwMG8VH04HFREpn+O3L6KTpkD410WhQGE7RzyUGHMbU3cWwA5s5pV0Ke32TEs378UOuTtW4il9k3jKvM+X5jFx5bgPEagTUyMgE/Uu2K9agWm0YouEBmCVes1kHXUOmF2XpRrYz+PFg9Rm+JZfs2nXBePvcfL6zzTRMvTIA6EKZ5tkf/Mtl2z2O+TOsp6cURJ1px0WbhbHjqSCNVyxJ/1rgrrCA7pIkdM2f0YQRU7HvXMs3En08EHnA85aRWGNDfmCj3D0zsChM7UEuCQQwEFtM9L1WLaysUoEyoMmRyyjeljaUjqaiYbOqFNR9ijbJtc3uJ6nGMZ+xFkWAmMkfzoJvB5DbDHb7F1cgOwOmbM2XqoibkZiDEOWS0AswSXFnx9WFoopOAXfhuz0qmmlDVHFiia5px3vKbyKYDmzA6XFrSqzkMVnlGS6BbM/bwrM+oJE5AxwTxdHPjQOieQWAQd7SelvoYcEAQV/ShhZPx2wx2yzVGopQRldSOziAqK/1fwu0v9Qeg/uLcnne+dU3S7B/zg7DB2F3yD8LJp5VDGYkBXIiSRyl40ZeEcNE+WT68gYw10qya2AGpj6hTv4xsY4FT52Z2QugrKqoxbaMHg9v7AY/flfNsvY98gg/ld6hoNgFlq0A1HzRFc5CEfpXx2nE6WtLZagju+aLFize3G6/7MrDc3vbutGNCL6o+845nvMDKMKjSd3WRfgo6p+v3aMlYkvJiDtF5Z+L1clSgN9T5HXBUnnDkRPKl6jpAwQKy0II/MBH7ogRPtxPKzW6AOuK/Wmb1dWMXFLTSnnkBgPya/NQbyC7Mdq4Pic9BUIXvXev4BysHMJlte3Vkp8YJpuSzaE2uOpmT5TFCfC2cndrZjPjYeq/NiOfeXslWbDSbQnKMyz1/ZrGCMWzZsQMfXpIFD3d3tqQ9xKh3rcSjnn3a6ovWcH2lhjx+najr3Pa5uRwhqSqljyoXe8w2inw0mFJuTMITHAJa4Q5LDp54NOY4oLwgHwY8dStUPmSoqvhdB6KdOXJH7FkXw+INoK1jjhefNvc+QAamzsyVladOmxlRQjEJtwJI48JDXJ2y1bb4UrLj0LLnoByIKVm0/aiw6fWPh9BW9N2bWlS9ed1ETQXjaxkZNE9eC1roq0Yzb4y5ucG2f9QhAmX2G839rhN4pqG2f3tin70pd4xQJOXrMSrCtRW7KqmEuLpCO40UvmGvk1h4qHg09B2VI+82areMWOgyr9QCsG5yTZ4HUOS2MjAdFG+/b3ENMQF1YZl9LrhJPT8jDyL53wc/RlrUPtFg95/NgLB3UObWUoamE5JUsrDUZd2WlAdUL+fILiwcArKtY0F3xE4xn6VSIuAFp/0ibWVYukFmSUlhFCr8BtSMdcld2qfdedsgeLLPKZWY9FK/uq5qB2u3F5XHvTR4dZwN65ukYwVj0sME1oQoEg/NaQK3l59lLb3UkZHs7jgnP57Spe7ajo+DrmrRtR8ttnScg54fTvgsWTwJYpsmpsdMdjdXvmsRporKtfqADfot/p5p2cK3VbafkU1zzEFSr7ArUiPoLzAprElQTfKBUEPXxflHp+XpABBExQqrZ/acFoUzfOBIWB4VDF4tEJC4iwdf/RlbMgXAoEr7LCUuCPqAPcAXwou/qBK0K/25wWg0SfKufknlBdq7vN0Vqj3cUx+t+0WPRpPcO8qQMLOv4/61bkf35GyGDhI+CQQlRJCIBDYXh0Q62C4ugHVnWDm/gVtEqBl+H4bhWwbkzjUo9jDWjZ8xsqdJxHAddEHuheUAwVH8zbtXl17hhWE5YpInm5cINN3ywOw8TPO6HZG44XgecFPOaU9OlXTOsYpOpsonsjTN+VA9YC95lHyhhy4IefIyfUpPRc3du1eZRXtm2kq2MiOC4LHiyY+n1RupmRQZKgUUHMuThfk7fLmfu/vLokeGXPYLBX1w7ur/0a1i00bEx2gSLy5oYG2WOwbtSoQuLPS8xG27Y00Y9nFI48MvDvq4vA1pqhBp3Gp24WEe9wd+ufr2Xym1Nqx2dr6EYmlXEUcfUUY86+VMaB+j+8tjsXz1vzIWq266m5B+tyY4f6CxOQ/7AyYaVUeXJ7Ubaht5t8ek8flQuo3hfW33TqSRcrMNmyNCsmEdnVdHiKwj51fyETBmEmreMOSs3honVeylKD3R9333920EsvNpDXLVPodW7YKLNt0JHMKh613TNPklltRcm/OARbHS1j7TyQHpZvScGbe63aAdqayl0ni4F/0o4JDiWNpw2IvjZVgt2na4vBLe5+p122Nu0d7R59Pt3w3izpfLsOWty+DDG6EmusEvwnfWc3BpHsd7u+6kv0JBBwkeFwYhRJCIRDQvDo82DDIveJotD3vaL23C/ejqHcFSvLclrjtw5msn88kHMvH1sevjuXAYz7ManKzE7WhoKClr06B1XL8ZYNjep1c1NKEur64ctogFcTLJ+FOYb9Yn5raEt9j6nWhvalLl9E/FGeUVPbUnWoTguVqDqaqLthSQ1nhZlT5UUpZwbXs9TxqBMPzqi78hSaZ2NySnWZlP20/M9VZrTX/NWis4AkwL2JgfehcovHN3fIkktOh5e29PRqx0mJlbyVb0lVYwqDxWyiFOQEPM6qefF88sepDXOY85hzuk2SN3zqbuPdc+QGwQIHSZCZr6hgtr1Sg8fWKXhsbxkpbm/5sGvReOFp31xvvvJkOuwVJWRJOzK65nbv4butf2bE46cuj9IAR7na6181Pn1wL/5DwaO/E94ICjDzLmTLt4WeuLOIZHdlsltLyXMppCU6lMZmWfbB1SPr2k6c+ZZ9YcoP/14o+nI1GxX90ivvJfN0mFx4MYEdSnRwxukd3cbvF4NIobbAvWXq04n5O0uSKLX16QywKKA/hx+t7xcM3dX0rXngTB/ulzB62vP4QDJviUKUlOKKn/3GaYFMCl/X9fBweEuDYWW18oX+6BSQNVCfLHt6TqNIT+bTs7UUeM9aB7FdHwWNbtP5YLjxOmBfwseDhx5JTwAyTX376KnWYZ+d/egyM5k0uK5lNkcKqw6mZF5tm2g8Ml1bbtynlV/mPzjZ75+aGqmu32kL72PxdThxr/7wlKShwzFnCQfDyUTiDE2x1ilfL5nHYc0Yowe5Eo7hu+s99TWOOknDGcEXo+PQchscF2/osLjErvsSV/oywJmKd7GFJbcON4YdWiXllikPxX6Mw0i1X1ZY8XZHbfxMMCZboXUNBwyHpOc7JuCzdTnlaXtCiN5R+pZASsIzdrtUyOi6NpcJRWFRRK5zgK012wQCRsFDzNx3wfC4Fi0Y07hI0nAMX5XLS9JlJtjTsFBjJ70nL2j1yYbsq+ta/RJI27Wtj2bHbYpx6hIfHJmyKxyZdd2y/bZGcvcP12Q2I5c6XJz6rtU9hIh8KrlAx8G1/3MO7bA+bKmwb/4jKm9eJ86e5KE9UrXZ5WLi5RTph3bNl9gWwRlVMoi9/iL5q9T565P+pw9uctHf7I/ffwKy4Xlym8ZdGDaE7RTV1wt9Iv7bWyPnOVhGsr5yVbmEm9vAqdT1Vix/IN47+/mR/BOKz26Ut107so/BT6hpw8N1nLIxYfRTR4wA6J0ld2wN+5p6/FCy1e9k6mTniynvgS3mZ2lzwOO97HeGIU2c+c3x/xQdRXC9sN3Ej2MwVY8m/e/z1/kGn9tB6SW5efYw9PouZ/OMv7f0rfe1uBgf6vfgoFJS3B//UNJn8St3rlw/PD0O4kMIkdYz3//31fwL6DPvYpYOMR898Mci33iS9mjQJEfppfpvR6WOf9fL3v78lKx5Z8GV1q7w4FVnjNrFSB7J0DbReZxFUDV4HwhN1qNFubVUNr2ie4/KeaQCBEEmSUCmDRNDA3sbk6eNwos3ly0vLWnNbpJ9Q8jMNrqKOz4nfPEUpemdes0D1rStAVLswiTYqSFvHc/ZvrPziurAZPlq39dHRodxW6qNSlKmnnYW+zk/ASZiztXzHimFa42ChnvMj0dNnTBlG1SvbkPk3DQMWX96RjPbvTcnznD4//kGM+z7cde9LICv/vhod/yIJO8+vpE1o5HvWPjD3ozdpxw/YT+e7y/O9vCCqhYdN385JoIZWysfEI+OBc71npyu85wD7SdiBY15Pcsd7T7rDom81m92BnEz/yVO7L90PbObXYGIRaPfRCoF9qLOLsbJXTnrq5zCllo6hDaq3vuh72bH+3uMMyVu2Gs9bXVi28l+zi9O7xb8PURqvt9uCZvIIqRx6Bh5YPsumChZztDkhZaxyvWGG8JmovPQdhAeDfDcxYiFleH49OI8RhFB6M4oDp4PlPUv7N5AkDiXenH9l+yZQ0vzu2p+Hn0M7U7XEC/TcvnT5y5eKZhXMqeVh+zovMWPe8uTlhtc/ZppymeWc6yffucU72yqfb4VduigpNT8U1o4/PgogPXln4p2H3MiubAu2x95P6EE3HxqOW84Xs7gRVne8Ia0g6un++QdMVK3Tpj7dPzzDHFJtGSsVJqm+NS/J/KfJ/r4FpLXVfdwps/z1i+V5LySMdOH3dBPah/suSurkKOh7jXNZ5wJP4ufRC+/49Bz9xZwn5/52z8WQB55CzHB2Dy1cdym2HRG7Q47G2/aAFdPo1sOpf7WX6OJrBc1Xulbrf3Gorfc95bLmbBmsubzawbvHSkfEa2iVMBipvAEeCZgXY2wL7kM9/PrL0v9Thk9jiNWesnke8mCtpzhzbNbDU9aYr/WGmBKnFPGNELqqOAVhBxMcYtV0wPFivFBUninuVDh33sE+30+C06/9ZAypii/trXnfKy6t9O2FprlAYSt3v1lAC2cF7jta1C1InOrdebHy3uGnx+407/XZDCtu9lqe7PS576f97/YWAPepqFtdjWekQW9suo37fqyd91pebyW4FNfTkNblZw2xu/uEquv3vu5dcEieg/MdGmOeaSEUDmNDjtMX0hTqgNRjfPdp8/636z5fnSroEPly/1PwaBuMK28+VZzwwZ3/Dq8sWxzAMgHrCHDTzspdr/obrmzwWtZuOD1q5G/b4pyz0EgMy8T8t29lefsz5nPLfOXAuntLAm97DyYzPtdQG1LlybQElyWR3T2vXFxwfvD3Zn1HarHY+gEuAoXDLBn+edbVRpZMZlfr3bkABRknPR6Z5vLn7o6ep68O/mUCzEU0Gxgq/NnzJ0Lfqu2dQ0zYUL0uNw0Ti1A/cUNTcoKgmfZBBuS7tTq9Wqy0vLtIVllWX55dog+0S7m36bmI1tzpkMvR+tfpYjmGm7NLTSXNFYU9YlRM/XxhgBZI6rPZdMNpK5u/yHIpDD/hA9MqLeKuAjjGa53Pj+L78BDk3+54Fr8tiOOhrgd1lEPQSnH2ztSXZ+fiaFiillueJUTt3p47cfqC/UbqkvbR8GkDmeiSPfa2DEgrdauLB08ua1oXP6wvqCA51L84rhc0nQYnlUfG5dUtRsDcFIbnDavdUsbUm5L0k3KgSJtyLE3wn9IHLh6fOnbhO7YrH36hk01l9G+7b65zD0fq6kjeBG4u267hN0Td4ivb6bfLvxWOk/75n7+l/oK/4xNebriWvdWerCniziWn0d8VR3RtHE/pdWEKDw6q/OyneqfztgC78uSBT/2cLYLDexPgIgz2u2P2T2cwq7PjSmtbCFHzu9oc6zFbXSlqZNb8zFnale738Finj54Z7vJsXAtiDamKLh4q+uwWXVv3cYzXXD6cEUM6e99QDyvDeSotZEzMyGWp87nY/mdxs+XLxoeAYKsBN6xW1ZsNtlxJq64Yrg/NSwFh59hNxifdFUWyKvjHZGYgOzMjvW4xrVIz4vduE8lxGyjqqUhCAoQYvJAmf6DjLYBSmtL/qW0ibBVE9kPX7nLl+muoyGg0VgdZHp4HSQgcksdLFS+/O2j9VcSbcO47ejuN01LXtZezHYz/L/rGqx+gyxwg1fTyY3Oe7a6pQT3wCm185wBDMt10bXm8sbqsq6UmLnarGuB102k3/1U/8WPOxIt+lR5JAD7qfaShc7sj1uduO67oIDw4b8hWQa/syGYs98cLnsO5tX5Ml9wr+1H7RLJ5oJvEQ/w55x+GLZ/HrpjzszHKVEszD7tJ3af+vfHrP5SnadDy1zOOU57DF8ssyhM/QU9BT81MmdACB57ufyOJ90V1G56U3YYTfuq7J5tzvvQXK5oZOZHhJn3q/nvvVGJwdjk3TRu1xUHnmgXgGs9lM5yJYudv4eXw6Y04vbc6BxyMRcX1YLE5BrjOTFwXPS2uaI2ibKhsxEOI8QlJmly7W1UPkzdFkwAoKb6UsFuLmfs28FBFKtZrj+FsqGjHg4lxCSla1T2ljkcZm6zFAigpfhRwU0dQFHdeI2ZSgZmZjny2ph5fkieaTw7LT2oyQ3/26Sh8wpJLIS72OwK0NQ0EUufBDZXeIcFK3D2/b+WhpBRRU7u90eVW185XF5+6cEEiEKugpFBKP7DKNtg0wuD9M3tnmAQ1rk9e4R6gEJ9VRnB+V4T3KeoNHrYXe2xiNhw/nqKxXWCxWy98eW0r4sVJdZT9kFvL6omgkmekXrr/QFc0p1VR0eB6sOPuP65mFwPKdBAPerIjxcm/LifNX5sAr51JIQtHgr1k9j1dSWktSs36iN4TBqsE2LPiWpoXVHgAaLAZdg6puTBC36n4vBGFwp+IfmhmRBY4uVn6YqNp5cUUGmM3QUSoWQU3Q6anx8BZXMleNeldyYccFvMivvnI5WY+44vANVjprOtNll06ajgaz9TGxt/aU1uNXC7LS/QqHDudPAvDxe2bX21YJ9YKobtIrg2gaW6nLwaP+Ykkg5MANoSGSquZli/S0ykKlktr7ZfbNg1Oe/LqcaXOWI2aNJQQd8X4RS+maCBzgsTUcOIjKhmpDly0ZxxaTwKE47pQL0XCJxsVUUQmPAvvHQMIwvOLQq9MaAwCItTDAo1BKBsTtio7p0Mc/m8BGVjePHKg7vs8q/ekltffjw8SmuAV26/McNlvTK8aJ6XI1HG1LtLHMJqWqd3X2wcqIZWugMLzPJUNJX9O8kM9Npn9obxO8n5j/I29o+SCanxYNB9GFy7t8QVwf9+dq6XO16ikNidkFEPEYMgSbhCcSUzjDlJhUSQuQi0cj0nfcDxJE1nrczZZvKkaTeKMQNRKYwlePBgHAGNXh3qbtUQ+D0t7sIBovwblI3aRFB0A/E4R12NDQimyzRrjqTI3tq62Wp+X/0Jg1dS2uRP1JxxCxSPB8vzDUjFKe5LocUE2ijDybdzqKKMnNNS5F2xjPbhCJGWycjVdLFYLWJhFa5K15YkCpTCoRypUThHlookCqtMhpPNzr/4Jqif3ldfWFcbOant6wEvsKTFYKLJ+Fi0oPJOMHR1ujE2t7qfEJ4QbaaTh47stvGPvx2Z7culSvIurXFzSe+laMd752j1TpfLcV7NPuglemJNLqGoNRmazOlLDyWG4vB5AWk4gVPWhGu7hovOxSByRFwE1Aqp2+07Lh8nQ0BTiY3Og9stRfRK/xYiSUInZnvJhIkKCcYAWRT4xl9VVNNRbsQNVeD9SLe3BwPthx9QL4F+cR38WYg3ZJU/uDY97mPz4r0ATbjbjKDsttDsykrsuBOS4DAkdlhbDPBz1UIlTPTP4Ro5e6wltsYDnQP3ImLXFfSsSLz4zaQO6qhyaXe1um5MePYXJ+sjRm/C/BNWkpFerqworQkpTRdIdJaRfXYCAbUBDeZm0SNFwx0ufAGio4iivBHdS6m4a8Xu8K/LZ6htKw/raS1c6lZ+dXpak9qH74VXl1YfXUQve164IZcYxQlkoXfaA3k24DI9iDX/wMUy048Lm5RXqVwgvLiEkhYtGI8rOBQWzRvILIgK1kLlrfwSrxePB9JrXO5Wor3bPFGK9N5dLqW/h82N6AQz3/ahhB3dFemcvhZt0wFPsktHO1EH2w9ijhmAG2ONjpdiM4ey5yAJ7ip01t9SjKYacgrZaEkr0GnEFoxT0lBlcMIYDAmCrEcgUE7mC8ds8hkAP/cuPW0dTbg2+LlfvZDSB/EjU0Lu7m0pIZcEzYnz89+8Rnu8DT64+/zF3nGr5XNewx7Bru73puKP1v0+/X7g/x9z9b9Pw/zTGYRdaZfJJXJpIlYmiYRSlKlN37eOVWSBlwrNapZgVKgik41LXdPclqS+9yKRiVnGUoNkrUUMrJ6hbLUROULDcgH4bQA22Pa7sCU9KahmK4TtbBbMLr/D9O8Zl9eohMcSWLlpAcsxZ3Ghspn5COz2NRPBmifbnjydcv++jsIldKg6l1su3zaAzv0NS5SwY3nYiMxfh7XGShKaFxIlixCw8kXdY+SCmSd3pIBghCU5RhelJ7KRQDjuVRSEBsh4/sLIrBIAQfPjkUyIgRdLHV8VQAtPWXEONKsHrpIqalZwWXX28/+Pt0eXxLqT5UrngKE+bOb2ofX98p3gZjAHhZwr5dCuj+8JNs3PpCclzMQlSPfS0xqz83N63/GNm5eNo37sC5fydobSvSG6Sjgc3B5zVASWA5PnlIkxu7dsmpaX6wUK5NSklvjEjqV53eWdo+aH7QGpC7oU7FggrpoXDVuePcayu4PTXGKyxqxoOMdw3X4lHbTy7oDPS+0umeDu4of39N000pdxIg/aneXNF0VMM13kTLe1E9JIsy+Zqt7OaRDxZmkxkYEhROHrp9Dg/MSEivCvATbqvSPNp1uetkV/CAGezs48DY25gHk+5sOgzBXih1pI/hY2X/v2fsSGoD1/BIlVVqHouKu1Fpa+n5kNPsWczUqsrQumoy/CPesYjs1zd+uokrcoib2vzScT3DW99yuDpC6RsagwYjZfHXiCr7fqf5th82CuiAR/T+mtQkBiZMujgACZCPNHptkqulPQmZdaPLVX91+ZHen79beyZ4zG64Cb7Q/m89okOPWvCzCeJfh0q2X7PqFDxF9CDdh/7Yl2Vb4DwHf9bD/97+eBPDyJ0PNSVbZHtTTthPZlk97xiMUVpWaTtn2ID4wufV0WeZTQ8b/NrVPrw7l7AWxk5pP7T4vZc/d0hhNdPGtsrbup/qK/05Xaf9+y9zddLU8Ug2i5Wd3R6w0G/sf3GzDrbal5qtaZbiTLR341TbZ8IbqAaPFweA0ZG8RM8gj0bMtKT8tJ91Bwy5QJCbmyTmFDnxpjkC11zHAIGvgN1hsUxxOM1QsbL4++qC8IF1eVpAqqbEqGVWFUgkCh0EiCbEw6MC79sdgLE2AT1K8REgs3TskmAOkBZOAXqHU56kWRfe0SAJZgWUy0Ccs6pkb63GfsM9sSiheBZBObFQ/s2BNRhqxRs+4Mlu631GvaXOS1xa0+LpAfdiTXPbOvcZV76ArtoTYL9oVM8x5TW0l/VLljhjGGb3Iv506/WJBHz6MTXQMsH9KUdCQVGdH8z/qNVNa+fRdK0pEpqXknXuNi95Bp3Ac/8hHZkpDYmKsCTIrkYvMloZdKKxVZvbDi+MECxXhajtmbjFOtLixlemXYenjc1tZ+JzlDbjafRMrP/vF8G+LPHknbgt9fSl9OpAVTGzsGAhjMmrC0hTEQRvFH5kmm8wc7LebXKtYcSjJHBtJUifsA/1t6BsEyo6803V83Dk8UjFotsnV0d1ysGLYabTzjw8JkO5XN+fPwi7Dpm+W7XfcJKNMb8HSL8DMbDZy+VG7rJuZbpm3syD6kdsMwvWqvtphvoMsLbe3b/l/hlnATjB4LbvC5l3feWDzfHt1x8TeIXyr68Pq/GYQUqLiJbOUAkU4bcfbBc8RD3MYV/pnx08CsYPPDiuHxBsFB5V5dF4axoPtJVVxC0aaGmVNUaRcWqQ/jxJ7D+tLSGIoh4o4r75ioJ4YfxSPnpjEpcWgkplsF4CeocdERHDj/rB0jCdFRTBiHGPf2EWdHo86PRZ1ZAw9+3dIYR8ONh3PAcvwzScHjkSWuKggj1hH8V6VQcjYhyFRcBIeTkPh8pnRLjZkJhoVwUaT6WxUBIqJcnS6+yhexCVbmeXdajFJt0jMhYXRfaJ3ym3lCI1vaU2yvYMPYd+ed88fGz4c2bf/7bNHhs/DWiFvaGKcNyRM5g5NjnGGLN3e3PQgmhbfn0EyB6uqeZE9JinY5fxoXqmho05MbWqmiEQ9XN5UXQb4hLRrjOMwFy2AhBJ8EQEyXgyamSqVMvkpzvaJd4W97MTxhgzwSXHvCLfWJ85U8aAAuy0sX5ccYdjMJ5ayMJza/m693jjSkktPEwlZHKkgShAQRvCN8Zdwka48I9losaZXspRtDTAgI/oCIH16qcEMf/9fQxotPybXrEY6zn8UJ9w6NmO8c3sEWFfI2Fh3MPwpwMjwBr0yf/iILaGtAFKLfQKRh2mzD8dxxmik7YMkN4wazjo4tK4qD4afnnpZr3G2ycWv0hvj4uuFFMtHdF/STBLYSL8vl9y+cs60QXqfT9593P+Yc/DdMwpATaRYZvzetNoZpZv37cr+w7BW/PJxqb3V2NGP3Js8GKT6LJFKrLwKzVD/geB0IZLLdw+KP+WUBeSPdeQcA/Jw47KxG/AR6FAlMD6Z671zViLbPfff7gDuB3OBFF/t2nVmRfXphNy3SKDqoDDAAMWaf6C3Pr0dSylOoNDyWviS10HuH1fMoBKL2rD59yjuGhohm5bdq6ooNuRn0ymZFVRHHMwnDwaGXqXEWwM6z3HnoNjWZCrIiAYLH7dyfvITv2FocrarY7gH8OkmJrMi/kLXFgKmAQvgCdQAPjuNGQLU2adtNjEt4tOSuJK+5Uu6w/llIqYBJO3hJY/GSXpqgGpqcKqrqTyqpn74MWIRPZqkbZbDaYmQ9K2lF4vmB5wbd8RSzkvbxLW0JL2X34oc46M88jR4p7XYRzWZADRWi90KGB9ur5Z2lKkDW37AK8BpSYiX37LtKwM6Lpt/SfQHQdwejIF9jnshbDl639nA5cKgOoQsmPzT/q7OsnljSHJglt06BTwCexwDd9QaUXngw0ykJbEvfUvH8g5144PlFlXlXdWaeMSfzcq7eorMQ7ar/CXYYElIRevQ+8RsAaQtvVZxZgVYCu9VbR2/Z8r/kMMPgx1Qa0yhlhAKXumexgPuzcWXwi44lRX4FfO4cST/qYJoiqjk/up6iAUEoTpo87/bByWrWQc7/uc+eHvG86JVs8Dj38DYuzEDxbgWX+Mb/I5vsQd/iG+jsn9iBopxLb7GN/gd32LP8I/vhAZsTTNieXDO86/v7i8hpsJPvPjfLzxy8IhXaZ0JatM+CpoLfmfUugo1jNXIRysbA7JmTnX2Tm2A+Kd3K2B13mr5WkUPtcSpGB/L0aWlcsWeoHl4/1DCUAdPfFnLp34BWxFWT9GYlbPA3QJYHXAcAMibhPA7a51DD21hgjfdX3uPsLZE0sxp68uflLomeDejBI+ybfmnAD2m6WqAt89YLgJ8VsaiAryNqXmBPLS/hh3EzVSClwVTuZfG4k04wWNM47lQmIM9Q06D/7GWGNviqweH1TyEovzkKfw8unYZ73t9w21Xw8rzmCuKbJ2Txzo6gPrc0MU0uWVimqZ9iXw84v/O1b1SDb1VNczlyq/o/071al4j0XNXvQyTHjx/6qzg9kemLV2va9n4AP2yJeAuPAQA/NOR/xC5dtH5KKI3AgDriGQ8tXYu+uE9lKa/SWThsSk4VR7Xxc8QmdjXKn2FyNWx6CXwD6g28Ey7KBsh/R4eqiOGfjpWDyLRS+HPQ258XqujLsJT6EXwZwWl6R9Tt8FjU0Op8rhn8WvULbCvVfke1Rn7tfa+H6Xyoz1gTOvgK+cVHnclot/OrxeNZJcg0aqXWS++Yr5i67ULu1Eahhh7aIz3MbqxFZUz8A3NM5gRivwzTLeMQcYeje1Wx+N6b6yfHcW6gha8/RoYnPvl2LeKY4bz2M1dcZw6daGiYJXbIIcNlQR27p3q+n/us95+IkE5eeZGeg/PkVWzq++BwAKiw4zEDMfsVXhij7I/TggYIxm8SjjvnivP0mp0XgTGyStzASBZr9aGylkrFZxHxurPkhcEu8xQ5TzmLA6E9UOxtjWCV2bgmx1saDdB1l6Gi3A7ijvvnCKsQBSmALOj8boi64qv14IEKjsUr5Qkhs08t49PhUJLzXEeDYoZK9teDdZKxnjRWHkjeEDikGZRS5pG0QiAvl2VPjaZplnmN1NpNptyU73eOnV25YuBeeMjVnIuxonYa+PjpH+McA3Z9BkKKCak2JRuDCURJtChtk+6UodK5ptdbDB5YdR1er4Sl0ygUFAtz8RUApQeoaxwJclQcAEqQR+S+91uNttYlVrRU54SbE37259jQru4EyPsTz+FpKRL1UcPGlmHqB0oC5/GziGIwrmQvGphIBKKz2utaduiABuM1lbAWcKpzugVYZaqzVZnld/TSCPeMClrmeTItGPQKYw3exGhgH837QGULoi6lhb3omSEkF4Ny1ZaNeMV6tPLrILSFGMQ4lFwE2EoVEeVl83oiAxxrpw89QxNdJUx6yiLwtxzsq1Hi8zW5hM2N/GkQa7hPlnrI8EWfh760LZ0oF6tFAdURy/EXRtNKTbFJsnPddGoMcDHyhl0+3Wq4nEjVcJGgpTvsVoIpBdIkm6tPxjJoOJkHkWCsz8GfWWORyndb+E0T5aSbohceoPMUejaCFwLCRDINcciARsaUbbtGwZAgfBO1XxMKwZnyrxZMUI2+aDJZW3IqxmJwJqgx2wF4TCDnT3CxVNMwflh+V+bX0DRp5O1bX3gfUVXR9DGK2s9WT6yG0DtXS3taOTJtMRx1Lm94F9gcGSK94zgge6a5maG6p3+cFVd2y5JgF/DaaUU2My9qc9YCawKKcnYqHpmiFXh+EIz2PjhYH/7raE++2yzAUscf2zf1VdIDRnhotX/OWT537RATbOrKNvWGDGM9ih0QlXerTqDuu0WK/B0O/icb0vnE0SU3igXQuOqU9IQ4JgxO82hMofTGDGuB/OF3LYTY7D3evmiapSzk3GUoAKKZ2UnVMvIfkBpDAvE6G30P3aQ9EsXtTaxToeDlviF+i5NgQbAGeKerWpbztYVZR8W65CKONxJmsaLa2Mst5GMV7Pa49GrJC8Mh76HXlHE06DaD+lNKY7BrBBYiu5nL5xHm9MKiD3gG1qLaE1/UEW833ip6kN0LVlD1JNVYExmKK1KpooTaOeoNmsHYUJeJYC9SyOuruOenof1xnTWQueL9QRADChogAGKVCg5u9blAShwfUxzehblS268aKXyCAab6moGe4+5XQug6aArh/Nd/vs51MtUU5jqEQTg0REWVHP0/WiottnECINdNUiAEAHeRl7vh8N1mCTrdR5Nr2c8yj2iV6HU66sRQ0Bp7YrgG0rOMi3ec/BYdDKihy5AptYhP13XNDbrsZLKOlWOzSOIU1AJ1LAnSuc9Hd68E6N5OkKD2Q2MOt6R+l6yO/NwWDFT1Lvu1xmsXy3rhEBPEtXxiAdASvtuAKJ4L0GM8aJePNG4kzEqCAdaceZZafGWmBGjK4Yg4n40opCJAgbho738XgeX3dgbN6RRj5zBmZ4umgxzUkfXEB0xBKudYwyAMEKtoES3nN0evLnmP/iGPhM1kpTebLIscN6uASOl8LNfiBkykLdrGtujmCZZ9zo1BP6zBYLTZcpa0Uiqcle5U5tN8a6Ac9apH2G9I438LfxHg+dnYz9XiMFagngibl3QoFB4J4kZKkGz17Xuh8Mk8ad5HmFJFKqBokVMjCXkmIYdx92BCKMmO9TtdsXMbzwrhuRIvnae62CM2713dXV5Se5evSqPkniBiNu7IEDIwv2iT9xLu+ScMX16iLIAs9lGq9RCNqsPwdMsndDwOZ/cTRyr1d0aMT6C961hs3BBrHeSitfImHR7LcQYIVE8qm+x8Np982q17xEUTDvWNztQhZn1HZGoaayuM3IMP7a3gQJfMrs6V7d2G0U+eTf5PPF+pfr4AWHLz6zVlgnjuTROAZhOISoQhMCXizkce1gMw8Mh5o9Rd/cbyxtzOJhW2i5ytF3s+bjevNjcKp/YV6v7DYKC6azbeUpq8mqVpoCBWBd74fUhXj4T6oeuLsVSctZ5yhl0bz750cTn1err9xHjz7QV/B4Yuyh6vLzki805eaNOT7S0f19dHwI+S6x6/voOaB77JUbMiXl5Nx325MknSi746B7oUxxXvWAiV6o5IM6JZ3KS5VHs1fZqZAwDeHZ9hQHtpB+zHpO37LiBOPk88f6B6uFjd7oH0cEArY8Pzx/U/DPzZbNcRtF4HAZQq7frwnRaPzwYBr1Q+c3p26Byuzy5peA/7x85OP0EakMZxuNMqzlmWVHt7a3s6WqFsAeqD24BFaKn03SKjKqdEz6+7qwErzdzCoQg4JYDCLle1H6xeKWq4UMAQ622T3sj56hjuLfCLl7xeXiLUZSLSsQIzg8fLL1HWRKJM37MLg+sK4B0Ue+IZcJ1GNg2srnMs5ka1pTTGbwvLYlVr/gmtXMxH0HWd3SmvPCH4q7JUMUL67l/YP8ZXEozokZODDFaeUTyKLUnzhL1Vq2Bq+uYCF4JlQAumbQ7AcdM7VMSBDiq4qUCX30/D95/cDp5t1OyDe2UYD1zvL+wJsIVQ7UXs4pjKZGYdIwAYaJwPgXwc7Crwv8cIab7ODwo761FxsRb0t6se239OHGzLtJUUqqlN769MgB1NpIx9SbcD6+6hm6XQH2Re+HdeUCe+qzdn8QxPT6KMJ1MGClgZuivrAS1764Yeg9ObVlN8FZUL5gcPwD5lG6HT9qjOnSQh+j6+TxJoPG2/cFTdAihJ9VgE35DsOaqNcsnWsc/ZqSdtdJfN5i2+eCFrVYgCCic/Err+KgUH/4whM/IRim4keuIQGDfM4rCBjZD6Q8ZjGWbiYddVCBj4gpSuaDoD1EvBpUN6h5G3t3r03vKkl7EuEcBDbqEINYm7utauwA0Q08Rvmq6NnKDuPlvvsj3xutL+KVHHkdecEREAq/meuPRUnoTDX3R/W12NLFmGHjePrwS/kTdu/wr/Q0n3asR8mmnfjlVbF535tUzWnv7WeehoO+qc9+cu3mEyfQyn2IOrc2t333hxcOrL/6Ku+7SL/nXXv4Qf+SYHTh03BY2j35E+L3wwPHJE0GxJD58jZG+J4/IPwxuDH5C+Y5qDq699b9bI6H67RnHW3eq+0WPfI+/PXd6bfQq9nriDfb+5lPzWfX5CdgE7gUFgNrDf5C7YDH4F98f+W32A/vb+xcHMAIeQfwgNAg30CsQGbgv8FEQLuhOsENwd/C94M8h5JCWkI+hEaE3wtqgWpgPLBrGgeXA6mB7YPNwU7g7HAlnwNPhOrgBPgU/C3+KYCIyEdWIAcQ04iziSbh9+O3wj8iNSGdkKJKCXIgwRpyKuBfxJXJLpHtkeBR/bfFR8qjyqJ6osai1qIdRP0fj0Wejn0R/RZEob1QkiolajlHEVMT0xozHrMU8QjeiD6KX0DdiSzDxmGHMGnYDdgt2FfsQ+4t1AC4dp8M9wxPxQvxh/Cn8/whOBCqhnDBAlBLPEn8gwUjDpBtxtWimJ26EvOkPcyfFhPI1yjLlNuUz1YKaosZRe6lG6jL1CvU59ReXQBqGxqVl0ipoXbQh2nHaFdoL2le+hr4aHx7/goFnXEioT5hldrPiWCksFauONcCaYK2wbrPesv722MG2MHk3DihuAfQBJBADMIhhMgDqQOotVkU51nc7/zTN21qye2Vj1Z4NXgjyYSxJeeu6inSxgcKHQ3fTd1r/5MmhqJRZhrYgwUfA0RWegE2m9C5Xam0/5JB3ZiTV0UMY/uYr9vFg74NoWnU6BU7c5sVVkuU795RJjYbMDzt5ARo5FAbE6zoD7ctH2nlQlmRCcHTIfydyZDSzMqjLmt9jjFJFNdDcKQtFBn5VFFghXnnRYAAHcAjsDdSX1XFUl7ebJ0bWRYRYFTdzCoeunFDPzoRib7OcjJyEiAPHlSNcEyrEQ7/rNyvn3ZEJIaub4zfS0QtRyqzo/0s/1X6cH0dVZ9hdic927i3eEsbU2e/sPua47n22fFxJIiQb6Ouy/xZvDbVCUP/Fbyy094odW7XF3m9mfynw7YrXnKU0jUR+LfS19M97VvK3/uTqae2Frt887/f38SRCEkBLv+k3l/NNSAiqfvTYxYvoUwDuw3vw/rRZQ78pTyM058UsY171KSy/l2/D8HtSLsJ6RcwTD/iCPSwZ2NvO+LgZiGg8bM8feOMzucXF2wYlUTOtSKQZHo/EzHXRkO9XksBRlSoK8v4Zx4dmKPaGGccH2RUJWRmEIKlvniSN0OOfuwlY2feqPqcvP3zbp5qEg4xe0uftL/NVjxxq0vSXpv5C7Ew4tbDrASTekXWzX53cRwhRnGJzTAiw6C+bVMrHa3nda3QwePaWGWKtI5P62bf+zjY0LFSGBxeenm0bGNbrmrjNS8aOzpPxSLpnY1JTySYpj/jjuee9s0qfJ9x6enZtIPJHrb8ESCg9/nJnR/xPvpR5028qm524pJswHtf9zAe/IBA8dyIXVeyJFvDBhUV00fXj8re+X1N2Omu1VQMAdPZuPfbSJy699EOXlsqowMwDEkXauL0tPQiPOCTwSmcCPeSr5klOljpdvSAbSTN0q4AvECVgyndGAQnYUTw4+xXBpbHwqKfEdRg5GD8QEN22A86ECWAUxcFQxMOo+Lf08v4IIi5+QcW6QBDW6ojplMv1H52byiBSSdlyZ6XUIT2ZbNJI14GHSi9XO4HsjsjRpCMJv/j0wXXTr+JhMEZkUzz+9dOH16MbEClj61rOkO1fyPlD5e1yzXeqOp14E470qHR6Hf4vBF2EnqjDpC7FT2yziARo9ombwAXwyHR1d8wtz0PlgBiqCBZUXxnu2rRlyf8a6/hmFyWUUSqsap8qsYBzd3rWAPtDzA7vwffi97LxK6QJuqW8UE/g1eCbJN7Z3qSjFKIaOslpCYXjCYuz9UbOp4IN+4rIMiaVAc8MLIBDgSGYG5SzO0oEz8u2mUTLLOobQgljB4tuayrxyhvCItrbLehEOE8VZE9WctzA0AtOj1nOD+Nksn8nv2V+4Zu2rfr1Q0rPTDIXREhrWym2dhE1Mnv2hqYvvH3lO58Ou2hMLtKn6vuvgiPQJ4zNZCXKvxdzKDvHJlAP34K6mxFmifEaXIR4lDq++NYznZg9UGaPCubLX3Y3nUNp4Yp8ZOELOLpg1T6DDOgkZxy+dWW3TpPBliRZxZ6PHtEO2gZ0rFdSOi9WujsNfV0abQRRbdRnyCAec2YK24mbKWSjpWmG86zzj24Z1AkSMNaROUm3O29ConCcHo87bvJNfPqeu7lejCkYU1KGFgzr7H/hF03R/C0UyuF2m6OUT+2uauuOLZtF9ltZAh5wxNE75F4B/0kCSbjH4P2PokgXraDljEmpxiGOMSyafhRzBnteS/X+pAsVQCJjeCl0lG4qHkWpMBPpCI9zPvRC5BJefClBazwawhoexH+Tl2nDygxAQctHGNXJhx6aKwTxp5EkocTJu5wvnpLKccEOYAY+KSVOtRMJ2x8QiCyGrHJxIIlJrDJcK1KpoAkqx3bKkMpjP/YBAe0haChWEZpJy3WNeJjZTr3womAoFJT+K7h10VmIEb9KCoARlRZJY+w5qfVwYF5FJkslKh4RXXQqVYfR3VV4aWQpJXN3L4RCgEaeIdYCPKfGE4m46l+AiRGM/aXwHjQsheDugvbdbgtMwHK8opoPXPTnMwW/OCAdhnVmyqQKNevIfvW1lOLtw8FqNE4d8v+z2X3kWx3dJ/KHQ7uZc4tUZZ38xdHYHz97Wd6ygvHQSdv07/9x+jJGpb6duyrfvW234AQZhRH5RAAXZPfAk+UGWj0R8pMbdPVkHzh79Z/B3OQb3t6H3Jv3zZ560P3Z20yv+NrwoV+9jW7/WFbb15kDFAxiZH+o///b4qgiM+wiBL436QSpNRPrYSUlWzcFOzuszfqHOb0bIBp6ArQwtWA0Z4eFna1MDHDyeUIUePBZ9GW1STg3Z477EBe72wLAkEC6+f0xclK73cmoDS0fhc55PgZv8fp9t01FV7wVcgkaaqjptG23Em6vf1Kc1rPBXnVLp4+w0WB2mT+pxSB8BBxTs0L5anS0Pkrcu1a0bHVtwHU5bsI9uZgb9jzuzYV/ReDlExSSe5euz52E0qR1jHVgCPvwBsZccG3XByPnbYtOEc+qapUeQC4yz2DZILTcqgJ/hOBM6dgVMucai9lo7JzFyhDcjXpGy7yK1EeHQqpIwuWFiEXtg14JCb6H946Bd54W4i7tA5Gv8wMis8h8EiEBoTlV2dmrixD3WIv6UQavHIDCurs7SyYzp/K0qtOcWe7ugyMcnjs4n9/Hii38IMF8sjZGIo+jg52QjBkI+UpIplYKWNvdOIAESujBaWZzGZRvSy120MmWnMUHHW3MJr4DpzKYLImKbpw/yLwN/FEzaCdjNNJGG7uC7bY+/gf2y3bsyBUrfrn63oF3HopZLuNV5OlRQKAm8xGmocUFRLVqkB3Bftn9HObwXpvnt7vDH7X0rSULFklHHoEFXziqS6hjHy4z9JED1LmZqFG8N3Kv8RPVIBlVAk2TMkh++peRnJm0+8Okc8nBskytxrC4r0nIBoudg/ScOwdty5y92sKLV+Rn16N2dF8/O9uY66xTV6VkugVhj+IejS+vRGaYq9wMkAB9tOdrAzXHTb3891Jp0N/7hu+SsZABXwciHi3/9v/e4bbOlTHGo+bFhqyGr9ypXuQ0T0h5Lf/B09GRm4q839yubZIHqsGSLjdPQ0tFieawE7fjE2YO5rQm8aLIa8WaPkdSB461z2bwmzwD4xzRl2RYAMWFukir6IZm4I8IylAj4uCaNLGqkPvgSpQ0YKImTo0bgR4p8W0J4PKBWj9jOmkqi7ERlzU5N1xpGloIqU/gN/rqg86/heK3Bu7VutmRsTNeC+Bph7ANhQKMddNg/iCWVr7pME9drUzLf+VHVPLl1oU0B0GWKJDuwya8OMBspPP5Qh99tgyyWRqGw9c+GxtLzE4/oZ93Lmu406gK+3Nc9tb03eKR+f5IeAA7oa7pJznAqEUN1UeU3Ck58RiCtll4fbJG0eLc+Znzro+e2VhvLPioGJH6sAUXW1DGXlwRS0F32f22i255i5fttsesSCSqqr6HgN9D+mYTH9LjMOSbjq8O6Ehtg9xqrJzCwSbSWbnv/OzG4C8rdv/MMZFIbKrkH77Rq4FkQKX3TwXX2XlEcqCiHy8hjKGbARdWReMuAyTZr4gJYaa2EVLXb3zu5ce3IoZd0aobp1j+ePfE7iTdA7wX/vlCozQBE43Jwz3hP1uVrbbw/sgG4QojOIxblyNrQlBjOx/RTVNLvUC6nUGjGqFFRwvzswOccYE/QtuYUMJ1zDByf7WM6vTE4bbV0tmm65KO03a/Hj7XkiV4EWuiFceBEjWp/t0UBlP3c2Po/epUcEMqtuHwqXE7LLNun7Ww8JY/ZZRvwbdosZrMriRx/fojqbiTu8m8XuY2pTDSW5Eko3LX4uoccH4bRspjMk493PJirQ8CZQpaFHZCZklsREWijuRy17f7zUgTLWW24uY7+bWSmyODMRV91s/pCIEPt+Et+AEOcDHEGrBt5sKklbGwarZYLuezsNDrtYREWHTMgIVHCirV3d5FeaRlAH+kitvyiQCMkubKfIlW2ddahBEEf7EogH03pwnPV+ypE5NRvKaTTSrQg0/g0lZiQSli21Y81dY9araaNG1X44ghI6ApW1HN4P7Pobx+ZSDKuZS8o6ajGvMOZcC3jPaRNFq3nM1m4tE+hsQS2Feb9dmbilt0Oe5few+z5XXFgfOoo46bx2vVxU6n3bCwao8Gn4BQyrZHwixrJO26qpJw5ls0/mfrMuTJbkCmA2CqvOv8IXEJhCAdxoioGMnxRymMDy8yjhepOBh0pEa+mtBYl49HKL0TSrO1wNE3BWbVs3F9w0zwJqkNHLKoNGMPVnxOqylDew0x72hCNJNf5fWR91jLBvE2buxXexmol9liqb6TJJAq+Gu1GCY4PSHrcpbwJD6J38h6/NMma6J2KpRujev2iDEkYNeyKuMj0GMdvbCXZBKmROGFjvlKHULas0Is+UhE0PJ8CqGqCqOMyFTpeBqSoWVdZVIyE+DWsW8H5GacC6phU6POzqsECVExhEDqaN65DEb5iCRV7UwZYSKggiY8wQq7RZz1eXhzeKlFfIvR9C0y6aXhoSNbIfrrs/RlEd8F0WQG+COplLafBoSxPx1CMHTSxqJNWhCFkg64TMYHpXSmKoQ/+5nHiJvl7qLa0nPfxHfzse7RIt5sycXoiWWNWuunSeWS2tJC1BUQ0/1obsLTrbHSfqyVjJd3JNYvCN6Z4mygpPv2UdaqZ29ubL2o5hgbWqWMigXj3U9Zohou6Tua63V4ukXt3GLQX6KQhS1711+4ivwoO0/WMpuVivD7ZQeXOtalPcutztexny/kPLw1N2HMmTSKmitgsLbModIjstliOSViBPNmJGe+O8z8vTkUO2KKXU9YvqhBT9TwfoMaQFpFUKR/RjYhYJlhakRWc1O2nykFsL4HXR0G2NdLlqfKYvLTgkARBIXWKtsaqNbRqDfwDsN7KbAHozCAbdtRq67j1fmJ2Da5PuyUxBRFZfKVXD6vuop4DZxQsjWIOz9E6ZfXOZxjjQHmyTjLf1uIRwzqFPK8JglEo0GUmzcKEqHc8lpPudHuKkydQLw2eH0DBS150hB9+4gwroylF9JesBNqfd0Vwom4MW7vQRFRG6ZH/dsI/vMnU80le5QIpZfGMOUpN2T7JYv332NmvTrHf3smhJKCABWsYOXtZHV6K9X6iM3JMdN2y3Ex0/mNMo6sZm+lch8hJqdBeCQ4/eneN2pAW9XvrVTxI8Tk3bAa2aKvFc2ZWQRKWMBOB8mTzlRxYom2TSvHXDH4jF+MNwY5sFeD+YHJVDOQ65r0Cu2WDf8/U0JMxYSWW1X6soYeB8egvyDCnoMJghzPnRmMsWcoTcIzoU+b+s+lSHxov7rpp6H7wNmUL+/u6vJ4k+qLt7t4Bjz6UWzDosATiT+Oj6S/7RW9pd9BzEPk3EXvCOb+8w66Vzoafx4cx10brw7Pt+vwNhuEIHrzU3c33oKfrZaMAg6ZEW6eRLt9faiEEgrvzC3HTwAXeZ6Qk7fsLiIj/3/20Pvx0vP+dIZcL/ruo98F+aspF5IoADp/wDgVjoi15kehfNE+58EPPMAfbUPg2h2Sq11HV2H9s48qZu/u2yk0bMEt2IwzxCaEMGL1cXNdE7gH9JbBUBC8DrfwFlljrhlizkk0RjlwOuHHG5yuSpTgq1aVf3mDuED7ZZ2jkHIXaeyL3b9Y70g63xMsBW4pXUsGT4wn4LcvSUOKlTwvtsmBatSxXHBybEeb8E7cZVyANTNLQWTN80X+5dn8cc8vX5p6VI7T29cWWO0xLngkquV6Vny3PLwsw8oPAexWC3D5wtSx0DIwfoZJj4GuznIMOGrRQ3GGcHIE1GUGfLuEYJbNc0FmGjpQcLoY+j8SwmSdM5uBAyLEqT7YuZMAfVPc8D98H3+APxvA6OgGwtw4iHA9uCN13IsxXB8ruq60kvd1WaMhooHmWIm0JIsnGCVZ/VBknWaIj8GSI25Nq0GVx6UclQA4nVPxAHMTZd3Tc6FqCG7qrKVXFain8oaEtsZQ3EejYT/U2S6qdN5rEqpct23hkBx+nbMSH6cmRUl2IOtX5hivjtPD8KxtdDCJ4Cc9ULeVy6WyEue18nXaoM3pDR2D/KbB0Ft7ekqqREaIQYnQGrJkzjQDaDRiOWVO5BQTQN6VhEjFUf9Np9lAeYSd53xeMxlg1mQ7SfGuxn8ytEL7uta1RFmdl3wWNQ2dCIuJg4k+0q4M4hiDuYiTeu+kpQmkOoguy7S7cAThEGIyaNftNru6PUtfKqVer3tIcWWKt04w2KVbIpZxDV+mGJTXXU9hQ9Yql5w5m81n4bhWHHUB8bb2y7xXRx0ol7UV1R+NZUu+tM1nQ/S1FRJYVa7mz19e14kEB+sMWETHxb0+berSSMxSeT6gBCk1VqnTlp+pnMedEwwBaSxg42F4YvN/24BwTyp2VFB0RZFlUegOsIWOLCj39P0tT57l0W1099udjv/g+EXEBgKlHXiXkG1OPfOcmdH29BTiibvxa2pIRQUzYPjdX5LaYfjbWH2jD+eja8caKChaDUrWZzN4du77cKuUSqYCVgMBfcfYQ4+RCgpqhYUrpYts5HUuveVyLCKz5HU+z7AMl+BdyzY5aveMkO22KuG+erWeeM4NJ/JU8zd5sz/ijK0ooDcMauyjRBi40FIQiNi/hJw6VsXT/sdigWtommM3NlL9UDa7u5vSbfqKMfXCf187eDE/c/eu/OiBHzg6RwOgDB1CIGQXuxRT1bmfPwvpmb+S5tX/M0vdbJHFIhTw1HM7QtR8BQUp44032Ywymri07w0YrPxHo2b8OGt4qA+GU5b/nSJtKSkHNkANThAXZy2s3wwjT9mqz7b32Sv7PnX2SD/7DnPA+vqK+1czZzTUAUt6AMdwoxZG1y+nr5fhZtwpntfeWDoVsUtGUZLbyy0FroZmVsuoOGlv5IUvRN0+RTAsMxPT966X9m85pJc6UKHAjrsf2H77ouYsuDuJpXudHcemMLQhP97XAaFQaePG0pqxad9YuR66QYBeLNSnMEo7bX36v9xMTMfR/rMfZqDWEm1Tsn/xKUohFKKafCWb3M7qtooV+5Jmgii4PSd7FErWk/HGxxmokINDWwm4T5E4lsrEaLS8JTFgG9+4AGMfLbZroauLYvAEum+ca92iinNUOq3EVPBGkhjtVkrxiQ2VFv8dXII2WZZCoAZy8Kr12a+b7pns6slPZIBd8DNBsp0fpiG+3X7d0Y1jqmTu6z5hJWN9kjace8JmTzTqMLH8HDa9m4RwiNVwvJtAqnbvWamNM3qJKmffrCvwoQ+kFw/e7oIHvxne7kcRNTu5+9+AvHjILukW5JFb5vzrSyDd1CYDtN+A2YpmCtgzb5yh6MDsi/QIP937e/88/M34dilJMDu8HbgXw0dO/kYfkC2LXgBId2A/tIJLdH9m38Dj36X348rczrbuxYa0zj69ZDPeoqY/J3Va2Wo3n5/07FJpH7jpkY/jK26fOzsx5yG7pdAeowyJ4XJfpuCrd27TnPKP1pUh2qO4H5fOnAsdmAHB0XdT4JA1Q9DZNnVsv557wWVw2yOLqqjikwPUcROfPbv/8W+mhcj79ifX8jYu/NVmaOMvNsWT0y64s8yOmuXzsHZ4fEaKA0jTEfmlg+1vpfSY4g/lGtgOiW/wFMUn+/6Pe6iPhuW9kp8wO2gjH8aRaU8yVfZTEMmvq3X1dlT+j6L6HPm5rfv6/x/shjAV8uXM/98fv24dB3fAQxCYVzJtdANTK4g8jENZwIsBEF+PGPpecZP57Q5DTg9AWkRv7+HLfPLyo8C+dZhw74Mk5rHAcouWYZpatzUI+FrcT+kudIaiJpl3BwibHYE8YmDAs4453WAplKEpMqrfBSaRTUSAoYfyuBNF3qBJE82Q+2bpNHqkM10YpbAKFk6wsPgW6vFCcQW4hVxvadFpX765kiSKnGfSp17R0wtiaI0UmwFhpx5zpHfQ+SccrGah3qkD9kBkKevgrrpPYfVtC8WVRd/+qNfb+U7JSWL5bwLODr50PMju+xBhaWxWSoKV+k45G+WQysRUz7pPp8EZ30L0X4uBoeaMz8i5OcPKSTVKoW0+cJ0589kwPSUHN/jty6sVZhD63874H8LnVTxwrw/uPpwhDtWhinVcpct34TpSKbU/gf7iNbX2sz8suVeWaaeBPnTC4vauHSTSKVZIQwMe855JHYLVC8ZureujZDyVDfto8Q7kbjGy/vrG7RE9a9zUb8CbqZ2pTDgNPswFhSQHu6qJHA34t1pWaLsWAnx5v1SZfD3rfgPTbdTyulk64smfNjAh+A7U9ERJG4vO4bZNmEl4BIphb211Zu8ND53VrPvm7Fo8SGAXDq0LGPIvdNSJ9vv+PrfX6Xf1B2ALJFmRqtFkecAuX/ZeL85kYZLmNz5Jc6n0TtWrJ+pQ5biPu+vgr3hIUVFcAik4cssu8LybUmLZ8u4/r3Xj85AuTQami9Mk24y6jA93nEFrx1QEnmlbOnVRpsbiZZc2PO+Kfl7m+40tOJrzcFvbMCfpTrena9rCJM0l7rrFw3lEjdeKqzsrXj/1tgrFBPtsaoeWiRnGUHC6OiMHSoJdj5YlStTVUqlMSmcxmUhM5THRtlQDKYO+iN9kz+hzzPrWqncTU6aDSOiDtR2TywBB66pyGHulhnLfB3sesaiHoPCOjt6uOIu0c5NWZ5bLN7b74NMusuZ+4dU4qYcNNVzPWtZre9bXQVRmVBhAJNRxdEEXYkaPn8RpC8GPr8p5sqd6RocCFkZ6MyAt9La7UYOpHheWO0M6zQ7TwmKwPzBAnYGQPYSa0BZWjjNmWEhWnL5BHUPDYGVZjizfO6T02U5LFu5BtFv7Psa1kaKByYYNJ2Rs+IgpDQ/0sEU4nchVGy3k6fas+3dvs1nEGVluFmbAU13aj77G3tkKa4yYLY7ba2Zq954k7KuUb1iOa/Hef0j28HA7dzn79rgklagThlJ94KG66poUGr8K6onm/i9WIoX0q/Pv6TjBjSWNJiRMrQr0H8dNFITSqvbUncaI1++GccJgd598829+NV8bDN/gyFJwsI1dmzqtbHa9tRCHq6EY8vPgUTvZKnkLPk31UH9wAruo/Vi3zv0v2p2gM94xNln9kd3feAvhVv95ZFgYAm900KhQRgnOvYeR5Otff7wZ5vjVDJw03b2xyDINXPnhTTr773LFDz+W9uozH0wyBP587EgOS2uRmbeSyF/+cizndnp92mI5MfrJx5Ec3Ii3omPPL/eqIZkHCueagO7hclOT5UU/QU1VJUHRIzNqjLdTumEax+s9iCO4g0UcQFL94ukCfRAltBRFDJBYOpwaKJLLGlsOVAy5WxNRtwbBMF8WZAZSDdylRwX9F4zx4pegnOLOWcHT5gkIpRYLyKpfy2xu4i5EGYUmADfEaizmY9IqNiDE2HYXluAKMydjcPa6xd0SR/PsuvGBtHQfsMLDjfuilsYzju0TSNoesF61WZ9ajVz4xvbaxDj71G9aO4quueP+eNfaRm8zYZW2GVDECbs3qpCPPUQF8DjEi/rGJzC2+gbR1ZxRwUPwN7mPteCLWr3BbC/yYx/1Tr9DMuEiiG7WHpWvFqvDhLZWpjFQSA37pweKTB7+J136f4IZiObybY7dsP0dbwR7o2a9UgO5XuozuRbXBicO7IoDM60EdUxQcaviB8lxKRuYDET6cQzXfIU67oVUuGCuNKBUqRDRFe9S9puzyJUqOOnySCLQxLR2n8S7Vd2tBSrHqg7erZ+GjRw2xN08XhLb3juR8CisodYTmI9Y5SbyadMccza1IsOtG+gYx1wr09twCPzp1/5C/xZZmnwHeDPMwNKNIl2NroSfwATfLpFUHwAmYWG7Xu5qL9Uq8VPg28yBd5aAkyQba6vuB585y+s6ehFgFax/uFYucbGQ2/IpgPGGed6geV10zHQ6TOsxTMB6vBM/91c1pfy5+/+3cFoQeJZX3MFTtwgv+D2CCWlJU9oLf32ygVTKlWopnxuYPtjDCEythQzaQe1omgRT2iq4akOp1p7dUeVzE2FQWVWhpta+JRYmM8FvSyQtnjxQ7WgvlYqZRLpYB+fQK6N/Js9mC+Ui7zuXmv5neSpmJ2w7nU1MgTfjX2waHpkqm8iVysa9wWEvG/orC2eSiNFk9Ofz/gMlsN5IWEzmMgGWXy/P+r9IdPwPHRg4EuAY6C1N7JBglCpaQBpoBiujawKUgIUjTQmJCnvAgcWo3hbK5XNVoXAf1F0N4+IuEpWiSjSLt2FXFv4gKuKjOVC/yKhRnWJMbAUmKw+9WvbhwbXzhewb2RPgvKLWxgTVWunqH0KYxLQLrUcvdbdk7p+7g7//A6gCwaG98IuO+7xbn1Fbk1cTELYRzu6AoITjDdQydIzBJUTipnhUH1/FzWEQ2diLjkUn7sEycO1AtkCjenNIw9JNWH7z4LNt/AcChkZCGSCGyU+3GUPgD+wBthH85m5k/adYsCTc6W1cA0xmHcfKhkE5KPpnsehxJQttWrC8esXTE654nMgpMDDIvUHRYfIAI3/aiHAmHj9H+IuClOp8DJTdgHjkCLf/sQbYaHTK6bVgvA3y1SEmeWzse1JGgWUdfl5KgQTuknNi/gcSyWtQgsSqrhdcN4mevRcQl5YWjwR+eX+/9u/rw7M3/S/2Jh/89XY52bz6rvwC8po3ZP8RfAHFqvBmDcSXgPhq543ghIXa++SE63+wC2Do2vf6xC+mh+Y2r93+7s0rwGMAg22YOo52L2Rfo/6fECYqJJjmzGmc9nbwoPGv2xc49MO9bCq+IfU0tiLs2j23Upfa0XwQfCPEh3eSf9XfkKb1Ur4AQ88INkpAjRpq80bjC+A9a68HC7n7fjn9IeN8NyeMov1HRmhPOTGGSSCUMx8GQycgmYgIEcQDAtOOQKZySgqKkadDbRG+JWUg+m5fUmYlyPVq01YQjUYSA3yEdGx/vdp/y6jtyRPGZKa1LX09rMVNeFstOTVYzAyJO8fAEZFO5/UkZEXuuHKQVsuX0C/hEWkB02BPCCEn6GQbVBW63h+auiCrfTNul7bEguCHUjpMDqLqY8UZHeu517bL02PGuFTufEnJiN4qokUiyqmgdOz4Mk3V2l5jvHZMBh8FDygen/TkVazwUrgtnrADB3ZIHHuHF/XTtsfCtfWun70MQa/fpVpH7mrfWds0TMuxLUel4g7Bps5C9MS8+v/UEzSaSHN2eeuD/1eBzmQQNtqwiJBOuslY0Iczvb19xBmTe5/8nJ2b7f28fHKoQMFe4uJTZfd7NQyW4lJ8OI45ypfLpbe7BI3cRuDRYipbIuKuVoKmIWl2fzjyVKZB7ewq7+5SE12EOYz2MScWm7BmZhQ4rA9gJqqzYsbZsIt2et181Epuo2ODid1uPfl46fieO/ebqfPmQb38FXAY1qiT9LBphiRcfCZHPh5MtM2Q5uaGSIrrvYvLlL4javw8E1k0qv6j5UsexwVTT9Z1g8zFExeGknDo8p1Yv5krXPKCqUlu/ltqsbgHYKlRjdLduVwq1r1EniI+/rNLbcYYjy9IR83I55kwsxZ4dQ92PkknqGM/rslktMO85hGxtJ46inKZuXaKRlmLzVrEsQLc9LxttJ0mRqDS+vJSlihwwkYlJpudod3SXecmDfhuNsh0Lx6ji76zt4rsJq1WrXStlpTAonibF5ADV4Qi2c+OVpJ6zwgvzkbiUd7QwucYRnRz5l4mw6XREoHkkfN6ffMeBgou0kU9TzPokqKYUWu0ehBSC8FINH4Jn5Xq7Hf8MvH0kcrjDMTRBoPmSkrcBEtwCe5IY0GxFz/OiUZYEUWl01t9B4OKrvMzK0EsIGSBEaWfpdTxpraN51ihwFizzihjULD3g6ENAofaL1+hYGj//0cNP4eW0zdqLCYN+0TXG3pNpdl12xl7GmlsLKm3sTgMPaqiVQJusqrrRn7FwL065Bp8cfu6Rz8otWXypuJtg5FfPT6azRtVRamClESWwTXmC1xWYpb4keMl5a4df2YACRyES+wAi0dRKalRXexEKlXdSYCzIv7FTIMYcg8bfM+F/TNWamTes345MS8JRhjEwZENDRC+MzGaWFLbHYZK8bykOmqftmtMuvle6k5TxuBEaEO8qXo55mIZW64YSt+iq3FuB5sT2GpzVEk4Y5Ldu0xaF63jdq2hlkLcrOEaWOqiWuvJITMBuqA9UVRl8vDgbWt4qFByhOgrj1rjhiH+yx21LPSAG0LnjNR0SCR2Bxf21pW+XLVacy4Y85IPOR6sU6Cr4x2/elk/CR6MYhTN2r57vE8MgAP3mCKtmNxXHraFF4Xot39626yG31VWbKhiFUfNYOXt6bgr7bywQSLRcJXnOBFJY54D+iBG0SY/sOyVu1nEZ1D8vHJBPmte94f9D/R6j5cGpHwNNu5q35FlaL16c8+kjs//4p08GSS7rhbUWbNh+vFvZVWb64AgONuV6xYr246MHfK5w9xyaNtL6mY2EmeQ2u3gyjumIEheHiQf+i5POjY/8dFI+bbUoEbh/EKo/hpF+Rm+jl/Hv6YK610J/ZamrZvSyWEKS3qJ65omim41wBDO0jQKITW01ajDih6moY+yqDX1Rl5RN52e5OWU0UnbG6At8FQ2gV6uUiw8pFJnhrbGjKmfGAlgimY60aJZgzK5o+lO4PFPSStk/iBYmU6WDUlavuKwBn4KdWfQKd5ZSkGTOlIQeZl1Iow/0Z7r6dngoiGTOCZD7aRS7Wzv7lWGt73XpuIgOTnTZ1LzdPFyWfbKpU2ucpCBzVOY4lDr0GMwqqiGUwiwKz/L80drqAUWE83UPMNIFsvomLEEMHjNhoI19jtg5bCcG5xJ4APIKo7f40rCETczVyWS9Vi2XbvfwdFjuJYfqwh6sMIHVKvA06fRi6H4yn0rhqf1aXD/Smq02sJt41qDShdmVOneQoMth2SzaHLI49OL/W2jlHMKMDCMUyjtKX04SeOQMgqSHjEOhw+rX9JaJqLnJzlhMNQ9tOPvaFdb4P473BPUavMe2FbEXi6YzdOYsejijL2WGGVwqGEnrotVp0Y2n94yehjsNVDcpHqpRWRqC25PBJP6tB2r11va2EO41JGCB1LKCr5vcBcjtnr77UI6EM4ifrQyn3yf7zF+6JugY9IXa8bteIbskzifp3CvRn3B4K6/+7mWq1J57mdipVUgA8SSjeLxyaybf2gLjfxlXIYuH/g5tRirULhmu1XryNtujGpiEx3ZYBu1xpP26thguFvseWn0/Zfm34/IHUlOjJTKiZfMTfQHaAi44ZmDletrQYs4iH+dhigM5OQeob8D6R95fOKR1ppyuX/ynQ81jUJ8coS3HigA0GDZXRhe9P2cWFHZdK357oGeud3PgwOR0DRa5aLYXTza8Ix0uM9Fc+jFblxZZ1an+njKAGMRd1zMd5KBy/mrJGMT3CbCv1c4cjXtB//n+jBOby3raAPBa7bd79DKa/F2vcL8pX1y2fiXb6stRzLA16lvuS1fDJfmRoVSQQLEgQIyTqyM8BZEsei/jKmajOZt5t6qiGdLx2t/euXWRXXKPeKOo2Tj7XcBJi34WTJyy/Jfv5x4ezS6gp0C/lhXId8GGrLGHNZj3tVsoZAuX7X6T996Pbhv4r7ghh+HHjzxGnq+ylJcfmNQRMjgODsoy+aOKPRKIqU/aZd1TDqemBe1i8olL5cQsCs7l6iHRgU3ay7df/cLrMmhBipqWhXdHkE2Qy+U3QdS4HdvN7cuH8BqXbPp6CSeJfr9CS4/EY3fwupDbONP2TXU7wQN8Li/Hi+9DV/fAmDCdhg3fECIYC1uw/E0UScVt5iW9XrrkrhxJuN4nY/6PerJ3KiuaS+mty1aFZDK46usOWks87o6qzdVlmqvWaFSaFp/aYw4SpMuukmSGtRRjEiBnsRHL7U8Ort6X/z5HFTbhgucNuAz6VK5Wi3kCgIJJnrLwE8hE0WW9Gi3zWpXm5uSgbdrq1e22l5KhmgIphkJia5YbW0x8RROQwVLHI+70pQoPkDBDPHkuV9kn6zdwIOiVf/D4mzNky1NLomOl1DR3qmoY7JDMIqqXBPtqdsnn2OCIxDdsz2JQ7OEHQoY8nu9VEooaT9Etp9ejg6Q48jT4pV2UXTMLr+GwQXa6eYxPYoHbheXm3yQ/QNBlaBeuclzEHoGRDxHlUYpj/iy8DhfUfjotrYkWUOIdqTt+KlMDIFTPp0blqbfRxUzzyCjoE3pBB38vGMvFjd1yzpx/D+bySRiBYBhHMZ1nNnXJ1i9Rq4NL/HaIhlWBZlKVXhnzt/ALqG9WQqMhJB4OPOrVP1I2pZLKmfa2IUJ1UuglOJZx7yovRgP+okUpVgGjJWS7Q+JMYX/YvqH7NLhrveLiICIwbGMZ4m54QoilJ8cW1Iktvtk8Jcf8TNQ+CsTAZPcEqE1ibV9J5JbkqAk6faSeNH4+W/G0o/tUb5690MEXB1cCC5QdG7IzIJiRutCROUqD4yw08e717mLFz7m7EDBYR2uw/fVk+N6W9fEkMheKqsVdM4m0Efz2VQOHyw3Mo8armsjW+9Q44pJoQMCgv0Ra7JYDHNuTQvYL1MVNdiSkmaM8UkUpg2V5+ZTJ/mSq4y2+qOVIWn1ugm2HV4Wu5169mrt5i5JVilPly/u0yQ4DN0VkdQV7I8kjixLoRTmOMG2TUX8+c9dXce7bV2ZTra71NpP2iIfU9pTlRPGOUGuEjudGAtp5tyfy1uj6wd2KjXpZ+YhtTHhBCJsmkwmh29urhu/ecJ60falqyzvEsGmon4/RXwnTky/CRmK2flqNZ+IdsaeVXzsmDBMI2Xx/eLDy/wJAstxGW6pxrYYDcgGlhJoC2WfUwMcsQc3fFMSkVA23ua7wGAiNKeUKZdDLZRNUjMoz1ZwfrD2fEWI+PFqUirOcxUoBez/5dpqXZW+vsnZYHesF7dqamxPdpvwPidld2i0eTsrDkMu02Dhl7aM+3Gm6q5bliC0/pJzTKDqni5KfjVzU/mD8SWnJAsVtR2yjS5dV+VlZ+d/edcQ94hFxFdfcBFyxxEOYYb5qz81G6ZKIchYrblKJRptnYZIdXy+nOr7L73TnvUhYvpVr4CIyC3v5WxBcQprlnYstsZlf7yxtLtlA75QB1qMLm3LVSNlBqgoIaQ10LyHC+6woQzf3BTZhnksX6vW63gnZjJZ+fzXU7shrVdtkJZlBO91h1RCfMyS7BvA9BUOKX2tL7cu378yZCVEKhR38HeItUjMb2XRhjVZqbu0mz9UyI6OcmoGCGzC7XhHWUi62G7EJcJYsfYIq4lXhLTBuaBGuTKBkM1LOBE8BhMamA3aFNY/UtjzJgIrj61QkKORcGc5SppLMwl3sWUyouEG0TB8UXsl6jWtgB0e4w/8EGJHEYTvd3eVLyipgXuspI5RwInbNNbNGtTtIAkxT8R9w5n9l3x+2RU6nVGi2kuscxHFe/50psZ9Ihos1NqrxYQztiWS8a6k+Iveid3qi1xIVoXW6rO7H4iXl5a3k1L5cT0cEA5i3D0O5hAfwcvBczLCBBqQ9yBXkgxoPrx2nDnX37EEj4+KtlLob9SLNvfGzQG3x2Xaph1UcQiXs8H61hIMlymiqc31R0Lvb9e0ItsrOtAZUsem20z6nE7WI6PMueYQvD/rgoBAaATfPt2opdpnVJL1Ocfpzw0Z9isJ5yH+IJUGTFFI0cVa8zLpq5IF89d/HVtCeVl477VzoDjYpYSSWlPTS9bSlBaBe3UpEBsxYELBPDxxaG3HXE4cpU3HWjx2wqaP1Sb8thXjqej7+edeBJQiFcrYgUO8XF8/Vw9ckegIwIhE3KJwRRoZNXhJrt0OmU7a3ARNSMaYGsNswzi/Tr+pMDLGPOtHLhQ4KVFo40Vb6lXOGMT/S2ySXUqVgZhhZ5eFxeG8RtJtGnVmFQzcQjbHMZwShq2Ji2+hDjTmdMXtd2uMwc//FJHR3wNET4Z1NxrdpUMWOb5QhFOS9hHCmMD87n0I/PFHrkXgnQo8+MPvgSp0yiD70m86Lf6+9PM+1hED6rgzcdluNBF3FWgWPKyO4X3FaAi5rhs5LqfMGWhngT6TdIom6dVqetteGMfGdYnx8Oh9egONqqNdqhtcb01Lhh/YjA5+967T8w2VerPVaKFoi6CuUqk7JhSe4Wg7nn3sTH57TzGfyWUyOxZL50ezQUYOtX7Pqc1atm1luleG/u+n9FPfUXvLnW4pK5Q/mK//Vu8plYoXCvPuBjRDk/nBfjPtdjps6lTYriOnmOkdoC9C46FAbB7Xjpk+gqF4LcjvtBq5XM9Q0w3IZNldWIF/uzQM4tL6xWcMg31kAsrQzvKuj+EbYEgaJzh3djw8iQTJQ8pl/uFjWjWZtajG3DGjzXu1IDzjka4ZdAwzRsTRTIue9o5804WhXeiWjoeNgT7J3u2ejdKpZ2WB8F1FcqxC5tLf1elO1wbIfJ2fjdvVUqVMv2YfsXKW43tkSfNnR0bRrFc9saynwmw0mTKjqxYvH0GLHm7l+70h02FIc3uea3E4qNe0TUS7DFRvGYn95bKN/M6+BPaELGPs336Q1EEWejiu6LX48mmLYtzqv6EO2D6A72+hjLKwflQghB2uy9G6638+PxLAdTT9Fm+8WExfULVotA5uO51hm5DjzAJ9uAJ3GPraHx6qo2hj9wjrjf7vvp0nc5NSd83pndYliuJdIMvO6/6vtqwuGC5dsd4Y/B/lzuyV9lG4vLcGv+SAfwa584xq0EhT2wod3FUB71rS1nBK3V4qFgvFUqVazCBQlxyShhCqbu/1v6ecXf23pkt+REA9AHftW0Msn8Th7g5MqlYmYZJYKCaVEWQnhtyFeQ2Em0NCXhdNbo/fTigz7DUUolFUbPRpqHlCWherLi9uWPXF0XDHajKpVKfvaal1uAmLrqBlKvhZUz2NvP7oK+rxE+nDz+X5ol5p//byHu/rp/0R6/6IxAo8J36QPYv8GcpgJa4cuXEVsJsvKz0b5Sbid6un9Wo1dbGSDQ+K5tI/DJ29CjpDD1uYrZcgcIMsH58wRrCFRjxybiEbUZr6qIaIMDO6AcNQlHi012WTpSmKZuHVTfaEmB5ysaEjSRqvGBZEYGf2CC8eYCxRq1SezKWjWlynPbXv/8rSxQnWVBjIKJHskN8/KD5y/1pMmtq152rTu1utb32kxSKbVFk8xpd8TPD0d18ut6Xgt0xNzlkj8l/7eaXyhbNJU17AzwQC7/ukuF0A//8tjLV9rLi50x6AIevzggHG4YOh51GkB9DDb3uz6HQAb/n871H5ObqEFbgCt6/CiNQN6dYgPC0qXa2yLprlPEfJRkRe1twkTR/pvr3NKCXMJXXRQajfzBTyACLa1YVrqaJsyDwmF3vp+kafE4+a0uBlWUxjdny2sN2+KU2dPXVC03lXW2Uo09/KAG8fMx8O+RFPa96R2MZVsRggtNGkaqXz+eebam26zfXmigsLh6obaUiWpacdqvRcvuAtmIPYwkNeildiLYJVfPG7TYDdfPFb1N7f28EV3ZWDPO6cEz3U+i02e6PAEejc7hGH462/r7J5Fq4XFjWhA9tHOvYDAFFoFQlXTUVhnLhEVLmTEAthrAwMEJHcJ6j9yphx3pCiZsqK4A5Loj/kyIlfddc9X9Mq0fmevGDCIKcaqVefwloqtHmfHZfpRDw1n0lbCe1LC9qukA6pGaXcBG6tJKbSSTuRiKqBgB+EoHzT3wRbfaXZcqouGYpklF738f/bvpoaPChWLsncxrbXPXuJ0bu2S40Vs0cjVEue2z+l0q9cV129sudlr74Z/frz7KLgMyaEAg3n9GkSdcBxrqSj08ON1hC0xxBTuKUx/Undmc1pmw737eIEdM6fPxA/7f4+0m2sRufIvMAYLsadfHSxixMnDgFRePsfl9Xr6KBBMD6uquvTNCxmDHIfLGhF45viKRBXltskCiLsQkUWC3PkLn0lDr2y9ES3HikFEtkiHsLZ08YSWZ0zqJUzTZkRxWMy08aMO0IxEH2TwlP2sa+XS0yjYPe50LudKP4/5jTCQmEJ4LqizGlzAQ7H8HP8nEE7uQRAj+JiTx8V+oPjeDw2Ojy8JHBCpZGCcYOvcHxrV4KhZ/U9UgiOYvLkwn04nL6DgeA3VSZj5D2dIhm45mVuC2OgzFEDx3IPMxTSyKILfa096SpNTwxPYY6zQlRMy6okkQ16oRU11ynmZV1F7exlSVpjDlO1fC6XpNxXQtfHa8zcZvty7tq2p9q8zJnY2E6VZSdGqFQnY15bTxurgYecxzk8xgj9+McZtnn953r+FT3g+i9c9APzzc2yx/gzmN/511ES15WpyIBnjLPHLMiw5j6VpKQ73svu0vYR07ilYWHnT5SnOvcUEIIIpZzslHJhyEUsf++b4DY8YG81xWSFkkolO+OkUK2qlOLvXSx+eCEe87iLaeBuvBOftJdvT4AmtlVrLFxeioDLb0E7J9iJSBwiRKGSMw3M/LlEeFnfzOMSoWSzVQL+qIjUUjDq6loFq6SuJfMoSiuDDi04xnCobE939tG6ckVCDbBvQ8kx5qufy1iE+OWWRgs8omorDBZR9k+tj1B8X6xpZtuO6a92a8SFUzvS2G2TYaVn9aD2UCAxtWUGTbAGXu0JVh6CNhLJTbkTBhcU47MjOgEy5oNoJXDiRbGjbQo6lM2yjvp6LkY2x+ktKdlGy9xzaMO//p+L92gs3Xuyo80+uhe4can84diTPU6dd7/Xv2EPq9F4ZKNZPB/aT0Ra+4Lvv/e1guuA0Ic6lvx1YqTQvTkePm27wAD7Mwop5PBRxCR488nYhJOW0+2zCAXMjdTSsFCAgji81x10/pXKdL68Ozz/uy6g7vPDSIJ+bZm5G0Runzy/sBmqsvSqmnK1Vs80vWfI2dNT/4bfnv8uNA+R9oKW8aEtUjNzBhhM8h88ct/8Qxl9c/N/+9Kb8NqJoTdBS47s+BdwHzryeOcEOM4dhYoPhqqdt+niiHtqZLzlbZmYK/rP23eBq+/zXPwpUf7qn9tD+Ax+Br+q94YxajbGtUGmqE4neCrlTYnunSB5W6odWmNnDMecGxpBzhT7QYsBxzPvULpJxSXT9Iz7UbO7C0he7ZREKKNaC5S2257HeW5G53V3SDwCzsvzJIQuayob2Rw4uA7C92gBH87aOWf0FowI1ecaUQIMWr9y1caKmAI3WuH72T7HeEO9kKoKRw2SfcbdTot+0H5r3Ih894vuh8zdYVT71e5ycGHv7pcKAr7/575xsRv8O6dCU3PcwWkPoaLmO7936h2jl7iEtjU7YBmqmce7EgnrynJBC9IsrKy17kEXcpKejlKxf5ZpInUNOnqY4QjOkfO62QH6ME/NrtqFpNaFiMZKPohnfdYggyUqDHjTb/QhkuQY529/2Mwz/yaEp6aZK72pLi17z8HK/RjPqVjs8NZwpW+UQvFnvqNxaNWmOiv7BChssM0Qw7AXIMy9JeJi/+9MBzzdhJXskRIs9plZanRq4TiyozdPe1XnOrVNApLJucwkcwWOA7N8ykKQgDVIkjlGpDPT2bcjHoJo83yYt/rDjPtb/KBzZLxzI5oyzl4BF5kYowWlQUbJ240fjDrz6x/2jCsjdr06jX8vUL1wU5eCgrD1w6ENDLJQLBRXKBXcVeLthriUd/gINvHDy+NvpETiYyoDF8OSpLLzqJR1MeoSyoDKI6s5ug3AYrquESDK0p0RZFGYaxLeNjlyxq/3YrxyvaW1Km3BLWAKw4YRWpmyKNmdYxrSK3PORtGLHuOk7IwRcNklBTZAYZh1LqUyxCabYFjwEH+NEJacctKmxkipLDNRGOatIJE/siTGx2sj0EqqThW/p+6RJQXBVFzBETxqJkQDqtuQD7mQGhAlUZX2RebUkORjMNOkijczegkQPS7k9IZIsAa30P1dFnI7f56c1SvsmycVqb1UhffNdxGhp9OgsXFDic/UogdMK/aud52no3Ah2o7PAQHKjEfapookX/yOSPaDvfHdE/zQTXJrdzFMwtzKbmhTlR0C7ct2t1mwBtfgmjRxU8PygW6AME2qipKyNlIQ0LroDJ+Q2JNg3gMcCIzEtmUVZMWaSr0CUxMyamm6hiDgllLWJYhU95zN5/SZfXcEP2bgTiYDhkbsYXSZhlN/lKaDE7tJMtL8nAWXwyZtf5Oi+idoOd7oSyKj7lilCJvZ1V0w8iPNDCkLhdehgzfYed+0n867aVhIH8Gn2VVRijDnF6XTwYV3k7jJ83YB8fFohzLZrB2QkINpM2QLUbfnekVYafncCB5+v0r6psxXIJYDuGEO8++Gj/PS+MeVqhHv8dRHUvn2BmAkhAX1M+go87fhIGLcD1LwGk0febvisLDgerkjp+KBueZZar2UKxxdh4O13uglSbOBsJWe/SkodNcuWQLBu6To2OYDi0eAt1/XrX134FK7BwzSw8yUR9KmpVOocF3Vk5rVxtLTHr74/wffue0Z37u6E1m4ESsAIKAAXSsCdqglNQ8m8AncrfVs4PEOa65eyrfx+xl6iWvju+LIQ2CPvgLXFoakh0WVOAhW8922zU4onUQgckVe3nqPDc+WN7V6xlFCGG90QV6o/BtMRcDHMFwX9takLI0Uc6lJ28aWO8NGeL9gL84pV8Gp9bvzRNdAq3QyX3v7dOefyH7vm60dPb0Hb82l4VmBNWGoVWBoCrJTQ9PjU4stqWyx9wLuzQ1ceR8tngGKKKKr3j+RJ1vQfOA684n3t7gZOrETu7PxK6qda+LTYKapVC82UJSIkCvnaR2tygHGq1PfJZqdC8hXh763EoERvaw7HN8WyB2IOgajP6KCpNjDJBdOJMvW3+hNN3kwVhmyPZXF8jeC9cZB9bxMM9vVnaHYbZcgpBcHakKpnvDfl2VXMNbFmuByhH71qyVGL+a+sOtY4UpJGs1eKHyX6RmJVz3I5KCjOhLzgtRJOKXyOIzhO1T3gom9ROVYF1TlvZNK8/Bghr+Q5zn4YMsJ7yvVq53oXhDScKY+MLuc4e7yC8s3sBeBgtiDPYaKEGIqBbM5HrQkP5xWpMI4VJoCR8CpwC2HLL1PyEIUlbApDduRwnDabhHQluuPkcJprQJnxOVE4uLokEi0RIeeYYYAy68H1mnMKHQ8yJEzLuk1CyP6SARU03yWU//wjaBrpQnLTYbal5ql4anVmSyJ2+R03OwfxhfBRFNb2Frhy1HywjmfPgsrae6EbyowD2zE9bi+niL1uvv10umyA0PcTNO4cOjhoirrUdxA2F1wZYweSZtwKgdF2HMRRCgmMO+hGDrICbIrQk5cfpU51G/4UCyGqQ18TGU5zk5wlqoEBYH3Vq+3oIt+WW6FW237WrBc9PtDu63vR1FAk2xMgp6NUsxnmVVScc0z4oh0L9f2/Pm9UbiewtFvTaiq15vhOKNFbYbDWroHPQJ9qHPUPOY72bamZfp1l/lSifTaj2kuJTNCmzLL5KNVPnKdOegRd8jZ9pm8G0VFi3+9PDCKdh90cJAkOhSRJNEHU22utvOA4Di9lhhWFq02slGfMkktKRY+oMjs18H1DnSiHCQiwgRBu+3tpk0HjrLIk3GLJKrFrgO1pyLHwBWKkd1w6fUde2nfpZduvGTXm5rm+vE8eUq+ZD+TK+Qz6a4uuKeMHKSh13l4xYTi1CcJhM9LsZiVrA0e6AFTU1inBsX7dbD7E+7Yajk00n2hWqdL0dmgMGXuFeYMmXnwminFSZhOx2jUtmLFex5RFpYE876DhMs06ohlACMU3pWx4e89kBlk9nAPE2bTyypGVKjSyLhikokQ7718xPz1898qkgGlXexpVSYneDAVh/S+iu+80N4Hz1+0M7A/yOGDThE+8Awku6vkgv0riIwaTfz56C4SHgXbejd4CELnFCYIBRZiKXDBwlVfrPz0pzBwLWItZ5i+j9/1t+4VuUOoWY9U1pput70X056lL/pMMRfgQQ96kqZa9urmsAmOVYYXEf02jW4gWMR2Uxpk9NiCTVQSgO1uy8NknmA4pihGbIYEmmc5/V4CUeSRDrcNpcAPTnXKO7Z6nj/Po01dkXd1aYGzpc1J/wTJ9Gv1GrOMSuSFJ/3cnG068LvkCbDPvnyCZY1ownUUdolu3puLZQRgOP/xxoXM6bs3nzLxqRPXC/INSpVcYE00cunkITisP0KtFM44FZDhVBhBlBd0y4yZeX439PrsQENIz6mdTAHU4wPOW/o961e5BVn5iuZ3xhgd4+MdH4gy5vqN7rPPgdvin2eRUa7ghZixYPcpO66K4LRQw+pIzQDBMXHQJX7aBWOlyLL2oO3mcNgcgKlsUQq0suRBRGUmcK/LhIeNXfLW3RzUMKsEkyKSs7y85+J57eqic52NgymNOUrTuj2UWBMnCO/b2wMgeLJq+l1rcFF/wK7eV9NdOnie9qHD/TXsh9K8kljr8EIj6634eCrSNb9TMDVsCeY1s8phny/9tLPe+IZAU9db7916Bm3MG56cAuX/ck5DS2BPuzdXpeAsgU+VNx+7599BOJvnG44eZ6grmYh1FhkdPQ9KlUo5cDI6tCt3WdtZj6sdbxyBvC9Ck2+/C6W6hTHciPdq9qZXisfNdtI1jWtXGnb/f/+79j+3urfuwvAhzgz9+QmuIjDsDbPOVxxsaEEBXoI3Bixw3SdVJb/caX7x1d9cyNnxtu1IUbIxKp8J6afDYZ4P6R2zKsZzmMbFswu+cCQSLVSAHQ+zwQxligIdQjsbow46mpvkp53pdOpK7VlLwNP/Erhj/cF6mSxNrBb51egKm+sAW2k8j6XXHNgWprNCq3rppKVf+yUtHbOjzd0MNz7MZrYnbvy7EMwFvemmrR5dCryVwebHnxSvSnhyq1sDPo4fXGmLvpSKq3f2lpBCJrgJ3PNWKHqwPdicL5EEr2EobkvuaIh8cT8FJ8IMpsyqGKV2lWrA4juRt3sLn2zbcgl36oC5FZpY76dQGBqC8pF8v/Ae0YCpQJU6lyTiK2dVqxn8PkMGSgNHoz7ItJEZXJKbUlhO0SkVony2twL2mTsoPQD21uKzrXq1eifRDSr/Cd+ZDGI1PHGQi4pkb91uIBoNQZPgTfPlQ2dAl0CzyP+ajIWa0Sa0cueHMxN3MHehRVTSLCFM7YNOXOaWW9wqE12r/3JUSeFczLVJVcvJpY1Coa2FD+An8Du23qijlVyukVDFNFXp2SNSjce1ohjpJKFSsKMZrxJiVBFKHCKHeRnT9pOaNsT0wXCWqZEBFZwMfnRpUjp5qlfWEyg8gVnPTRA5/NAY5n1EgL3zBgcwFj/f091dq1VzHdL10IvKnZ1GeJY7Pd211rtW7l20vgjFrpZGLa36+XRvb2oQyUFwwrQ+j5+PumQ7ekBdYvDt6kfyTLNSqbrmr4gjcy615pwfxjaWgH7SPPO7FrjCBYl9FANeMcZu2FHWarn2NePXi166OplUKvPchZXBUHShY10w3sFHIGESV+n34rTruSAVZx7j1jTYEKaLLvgOgEgvZOHp2OLk1iUfafAtt5mzHnH7HMpLElK8dDeMqdum1JTUFVfJSbAFb8D3xpm5IpZl2CLO9WUrMZq1LmM5iKSZQUkhB9iAUdMNioUHgdrYoYwhyqql4eFu0XTH7va19CZANdRMH2GGwp3DSmUYi2To8He1F5KxKg26mIS987LtTNdYv0wvyrAkYZrVJfmrDDkvXmkcn25kwrWxf/6yWGuwtquzfMeNptnaLUaLzVKCCr7w/Uxt7+4ZZR3hzM+tQU8blFSyKMQdc7qoUgdW9uCsGM2SMMrd7L0pXCgyozWBl5I3ITSbrV5l3/bmmHm9tI6AsAdssxbUWisx1FWEcMNi75BgD5Y2unJwlSZWKrmMrkVUctn5beN05nsYnNpSpBxM/wPM2/r7Tb5uQ+gA2X+VzQDwlyV7vQ2WHxUb+CYpjl3cRzqJj+NNpEV8Gu8hraE1pIX2hXbPGp6mTDoJJYYWAkbDWA1h/veD7h0w+Exsad5TrIXyoJFJR0xLEwpESevtSzpAXXktGiTALXwsDuUcKpi5PbiRqkPBLuNdAl+ptf8SfAnEUTmNUxiFP9tJVVPArzT738vWSKAIVxayAy+hHeLGir0uVywfXErHmwxcDWthTYCPuQqi/HfAjDCLdgQxaGzsKghZqlvc4tIumxoN2jxyFKRN24Qw/+zg4DMrIWkzJsxhFfeSVbvo90RpRIcbfZmIG7w6KqaRHsMuvkz6Ml7AG6eWqR66CuujgIYJ4y2JYtvPKPEjd3DL2kskTEZVsUWcB75AolwCRny2rp+YAq/C8j8CO0ygiInOMKzfjBcJSY6PDbuFe+je6m9nEpYPZZiK4Tbsgp9et6fxmRL49MNn/keAiQlYMREPnRi9GS98n/jfelkuwc9+NS6lGHp/peVn4yRt065dPgfCoUdEqotjn2xoePUCWkpA/PAPSbEqvdh8TtR/QO1C3KjglsuGJ5BBVOESzaLTjU6X2SorKrg0qq553RBzwv1YRVaIoa/iZbKTuIO7jqcpjVZBu2YBMTBNTQah+YTlOZYE/ogMTwFHZlHsONh1k4Yo9yeqyIPggXvZ/bNbEEkfBg/fLYbng/+Puh36X5XXXf4T9eITWvUlJ0EIkvxP8NLfv557DYr28rtN6mb6PvojIQUKkXSR7hT61H0Uosxqet9ZgefiChH7160MyGbPf/5zY+fRiIdKxGnOgHs5CNYbUHvGpIRrzBtAfqT+216mjQSda07fmjoKMUSHUpQ92tWw3SWRkxEZT08ksqmLmbHrDTDG8et0G+/3ne7FNDn8gbv74KKsWl+/FL+APhLfOKU6QHd8t4ceC7D2T/f7cTfLYu/y7/3ZUYgh22BG0ra10eoYHhyFaI620ubt1d6OQcSN8SJ/E9QpbfwLr76gHq/GvHca3FHe9mHC0YfW3rvq0SNjPSASfPrEZODSMo7gD9dlYlr3EmJwHrL7HLJUbTDllzicgp/QLnLFtXDRbLX0aHB1VF33uiGOhEewgUyMI3yPXi7g3YMzvcULzM+A5QVYDD06ULL6xNthRTZ3+kgUofuwNVl4jEyPk8MMtegkWvxmwGsZqct9TsahQ6fgXU7oMz2b3wHzyzY8Pi5BqAi+JhNR8BU4m3snVPwFsasIEQ3RDkErCQYKGXCa+0VOo8y3zqTi6/NGdO+t9I6UMaEvCce4JgUDdqjGnmsiYPBXHi2dMFzR4lddOM1IJIluia8zcKZ40zr+35lJXPyDttOfc/hdgLScZfIx9JZKWYVUudpWU1NfKsHlvRSsMh5Dq4P2ChlcdwHZTaN4QO9ym9pbUqCeYUU2oBoiFq8k3R218znqD8vo94giEg1iD/kDDI65VeAYbz5oFHlUypSRRE+r/ToIqqc+dx4i2ItmHTGgXSOo2RWce6TZ4PlChc/SqzVPd99WOzcciPI99DjzYd0bBBIiNb1tdAk7Now3CWUQGQjQEMf1Kb7OzP7zPo/bVixJntVBpt2oIzBcLe1eKylAXfK6JHqny95EBjMofvbq+FPQNHQmdG5lu2Qvy56RnZdFQ5uQpWHQgn6VcvGhkCKNEHPXiFymrt9yaDe7ab9Po4AJhPFYTGzZ/smRWkXh8Zkheaxf/U2jqHTToh0I11uSBcJHA/xeMLHCqwiRnVvdJ7GjDYUbukq1SqkQ56edrUIcPeogaXoT7z85uIn0/w1SnBxx9hto1J+GjyTIbsAkjQVdFkjoJesFRbhH9gBeAZNMEz4Ah0wbPoPW1JOoT9Bfov/Stl4Eri2pajHrPN9fEUzTckcrsjUAJiQRThs0k1tyJVIGB2TcXBAXvHXoFPDLNIyagGY7uBU8X3g0Y/rg0uj5UWXX8XXrxJyVMaj6dGgasiCr3v/pcIln+Wz0v7NNk3X0rxQqiYR7nh+VEw78NK/SKxQgBsb5B8W4Tp8RhKp/q6ezzZZ8OmLwR5EWipmm19py1QLiWiUr2T1qOty+YjoPtLWBBff6ws9FGs1LbLAE7h2RP0ryHBy4Vws5sGC4rr8FLYVTmXjCLp2zhXPnDgeVpaV1ajHURwJz7fKlhmaTlnu/G0IianoISIJwW9czSC1xlAYkTFRO3a9jHfSGzuKRDfM2jONEtm992GOlRnY3Als9myvc748PgKEF7C4ap1hOz839GgWcjnE0KtZyoC7D139UFL/L/SokaCF/78CItrmBGCsOmCiKONWRE66oYHfSrn4lAc5UOLF/RDlY2z59yBO6Fjd1pqzsrlnNc0cZDjQLVhGmWGucZwbAXwVdkqXgBLsdnpj1SvgZdOExSTcYwimSCyCDkRnTHXG2DzToz8HXUciBci74JSjCH7I/oApPyJ7BN+BOrU/dQ99DjytVqGk1qFOpmKmUMj1GnZOUIdZGMgJxTVc02uNHahpHndJaKTiE442FzJoSgvtCdb2tk58UIFKhj/D6kzJpW0ZtKFHlwVShjSxJhhGPq2i0aCIkTCblqXLcqRRFUaA2jbIGtWPkQgEizLR1W6XWzm1bzZPhBPowbvULxR0dFiTXAsfM2mrtPmyCFEZUNfYo0uCkYCr+pKR2JaRGWzhdKnvvOle73FPLZfb28P18bDiAfIFIxtU9aP+mX6QFqX+/X884hnPNFmZUu11vkct9Jzsrd3Rl28qb8hCm3mIgVitZI/GXTr3+fSJtEv77JnhuTJU5pcA/O5hzk1+k/QGREO18W2ytLvJ4r/z0oxrQ834u86UC+3Sk5z4KvGj/1xuuztV+UsAZbAge3WYKGxmMDcG8/hsQsd8x+gkXLkMKy+IH1wW9/xyq8EeSP8IKLJN0oQUdx5jqobvoHlmIzGNp1ZE2YFKNS00fVEBESvWktiFJdDgmVeADS4rHQ1grRbmnhuKO0vQO98HVEYYhGGOlSOB/EZ96MLFvI7rRgFVmAXido2krPKWuzLUsGtrZHV4Q92b7Gma20Vfq3sMyEILKTe/Sj/1cVNPr2zEPtrZFKysDe2jG2dQpsl3H1A56O/2k1bY+Uu03xih6aSgwXUtCDFTeP7OFJ1OpcuNuDevNUrdpnOuv//N5O9cPDgVNAszfWAh71hY9JDlNZ72QBiZocVXgyHpopHOW2QOpyhVh7LNave2i9raQP1ysjt2Fe2mbztkei51YskBZxvWRB0ZuvziusDf/Pb3iB60OIiBksPrGluiXrg6BUdjWI1p5amlD9pPa37qz8XXbIsvqUZEg7uoTPd/ZLjdbYu/aSroyRV5uuGnhSH1FC1I7kz3mc6BarOdhjx5P3FoXCKiHMZZtnkWl4nEY+eBcK8Awgk4gsK9+1gc7shwWtGir18aY8ToxzXU8QYC/uG8pI+fkkVMVvFcfLe3WV8gS78BvOE5vLNCSoAzfSHqADZ0kN6EXWNOyysO5mLUDWRXBjSj5FibC0JQ5CDfhh9vSAwMMTcC7Y8Nn8qQwbZPLZXZcuKRTt+toe/7YlDO0oa3rSxHS/Q5Hh6cRgUID42leMZB0uqYHLZWtPFXw4q39cIpb0JEnw+CKZmqdbifFRWF6kGZ9t1XLhi3ke/8+fmyk1+12bdenyhfBYYhjU3EwYVlaD+LBiPqGVmOWFX4IWvrMg2o1vOq99K4l75xDNS7tVZ1PrICUvICno7mffdhZQ8FASyJHYsUGSa/wdQ3rb6dhel8bEq+fLMIurCRgwePETcXBOY63xEFvMCJzLbVaKLQ9BH0qyP9LYGvhDRW20Skm391kZ1b1MNKVm44OV60JS7SKaPLkeln052P3E7JoMS9gsfFmLXURxEiuINkcgg14Ez7OJW8Gmcuyn0gbZA7Bu85IZOB2Q4CbMtyY1dNb7V7GMWkM4+yDhD1gKvJcXDup3a7/O5/cShVtnMC8YFfmbQlDvX2EHQq7r5bzDiC16bGBm7hvfVi012fT8qmpPhywpJmDuDYQNDu4uB7e/j7La28d06NNQhfBR0EY+8q3vvXAWf/K/V3hoCoFO1uAGH/jG+V2Fex9eXye0HzBFzPxXUMu6lMG8QoaprXs/1+0zS5JbaIw6B2D8003lFOa45qu8hagrOoj7gvOLJbw7GkZir8/YH6Sv64XhGclN0XLuuDqKTLDCeBiG+dl41ga3IZduAu/kHVH2UGqnU4Jsz6OcFmOl2d8389ccwMGixJxokRQUpzXUhBYHihGqr/FxL2L8q+5TGtAgN5I4KBduWss39I/NxFReMKYMPvz2TpxfHtGJXQE28aPpTg2lUzqGkYl6XSzatcKnUxWBScXG6Q2gg8GSWSMsDMW7ICLC3GPEbzDi0VIUhla2JvpTwDqGaP2n/HaFC6H3qocmuwrdw+LH/t+x+Y+xI28JMsOlT1L8k9/OryaWF2kzbPov5z9kbegTRgHChBpMt7n05kEFOPGcxbZfG9vfWz+jrwl6BllRmEHv5zh3UU9YuaepOEhuujgVUvzVz/v/z6znza0TwCvv/6VeRLERNlot8Xoewqv6wwsvvezjZuBxCiolu0dbiCQPd5DTX3sY51Heh4PftF+/MP0jbM/5olEmsLL7vwWpBBxCdszSntcXrHG1o4gGEXgm8RxyYEob9LKVCrliWiEso8oY7PhLnVcvNwcO+fJPXwylfIHnkEQ5VDnCBEBRGDG4+ixxUSIIh4gfnPaghVYMFv+0c5Uq90mISg4g/+ACrNSStLl2AHGKqpAYWFrH8IjSPI46GzYnk7P4/nmfxgYei8nm+zVlxBCC2PX8ARYentKcKWnEevIPAfBhzY9gaaC+vjGUEIS9VqJFxz46mpk8iVpZkUTK8BS+K4QUAkwlrCMZQNMDXkZNnnLbggpKXnJEw9WspnlJZdMa3z3aWMiWRGLW8oUQgZov2gPxNqRUcVHpKtE8pFl0a9lsz4XSppqHJGd0hCHpVbCt+AP3hYhraS6N0aqUrJHDqQ6liZKsFEtmR6hF4ZtlevM7Fv0iu7ljYfp+X4PQ6xhbbDxKzJpK8PWeFYSvLUGRqmC4vRWusdk0ElmqRkuMqZxpLSskTGWk7SYrl8ZwBwet2B4SAAkBOoJ9EnkQ7xBfr5gEBIKA/Dvsr93gEPCkkeicGXUe7jtSdBcSfWXv/80gImFk6eTCxgetdPGMu0GOoUcCwvwJbLYADnZn669DKZ5gSxiyxdqfOa2+WbFf8X9aN5oxI5CFORM16HkG/NH/yiGIbT9U0uDNz0bNko5q3OwrqK0+1N6y2wFLZAyz43WEATPSSlim/kwxWWz+CA+8rMSfdf2HjYmpOr0JEd7z5WvSEnHiBLc2KjsnApT1i4r8NyBhirGetNOR66ConE8x3H+f9YPp8p6RKa1nYOQj1P/UeQa6f+dkvK6F8YeQTCC5hTp9nxh8i7sgJyUhHhQ0hidgWg2vvEThanNF8wAbnS/LeEalzIhePk4j/TzyAnwFOu8bR7jYH8x+yvJicl9VLteKZcy2xYrhTplHSgIHSUo9uChePq+35wtN68GTRq338jdvPMpLpvPwS8AgkCdK3RkTK8jufRSy9zT5wA0DW2FzoTOAh9+epmUkJ6iUFM6GRNyna4BVsebpa2oB32j8vK+uC9xLRSxAxc9gJT2lYz84uKuDi/y2UwebjTieI7nOfDV8oZM4HnrRZOUn9t1WK+48l6c229Ox2MxjkunU0np/12nugJkEEUEbxsUQ/7dZL0su81j0MW530XQhdAF4KvyZcuQbvNUKD3lZKQTJUNTOd8RUm6FZvMn+Zr+fun+rKlN8mNwXxutObCcxHSTA/VQEcBCC1Om78nuJA2X92SaxfsQcqjbqdE+NaYhJQnsiO5my4rjnDnTaIF1D4+wSuEHk+9e3k+0e5ZINCFw5JXzfS5JELm+vnaJld1BgUFs0+BF5uKNH4K9sEabsb0tic+DV5/ifIXiLqGPxAi1PRgfuqsBDJuOLroXmML1HDiFAU6wPcuOgEYfcnuAg+7rS4K5QETFrpPMD6bPzqbXEyLjegjXZ6GSNhA0q3k+HXAbVTT64MPT3zOBoIY+0BBAy6iwbIOjJJ7EAM/Ia34wLY2bHtzLoiA3re9QorwCZLGy5a+4sWPz3kcvCCmNSk6Z9Dv5rqEk2wLZ06QoNV+HPKpEtMLpmaaQx49MZ3/U4PytZ6wWQ5hHedjggK/WwbFRLG1+0jGxVt9hgRg6I0KU8KQL4hXmzXkDFZZ7wv/gwXmwQHKr//InQGTQlb/90huSLUH/XcoVPID34Wf7t29gp6xVvMRTcSrI42g130Fw3O2GfJjT9k0iU8pqOdU0LUFIJhNWTn7YYhFdBq0oTIheHNBtS7LBecs6LlGBU3WUnycLTC6/n8VsHOH5+QPr49RlBWHS6iauc0GJZ72tRSIQ6w8U62dp7xRq4Hqc/O6yTyHLiLTUyQeQBjrMu2IZxLpR/JobE5xw4Ev4zR+n6lJs75eFw4K7D6ysKMfkQ2M8TC7znyhmA1OWK6NNFC2v9j8usHAwxM+0ktEr/VPbBgUt/ydjVX1FIkOGI4eSpD60cii4/qrNihoIaOvXp4T5wEVWbppiSEv0DY/miQgxd1CqzDjiPWZOfeHU3ZGXUa4XO0Gu8fjrPRuPM9AgRkJUgzR2z/YuBIuZSCXoYE2w7jtXKVT3JsFOU+vt/Yqh9VMZNe23WmvkDRcNBl16fSC3Lj4AggBpGKBzRfwZ7I/Hm3RmRqVXIfJe3u2umX9bY/psjqMbf0qx+JxSTkWOmCXnoP2bsAp3NYiOMRUwqb1aLHFgS7v/0oPJX3OesImGtms4hqA6PMkmUISmk4CmeFW1cqRUCiqpapq1f/0LSg7HQCMB9LTquI7Hxjm50Uk83zwc2rzvtXXzR65E+z7GkpDFJGbNwAxFrTEeRX+LdN+anrY2qO4HM0EmrabdrNCn7Ak5adDPMswvJD+YVo38xY0me70LQH2ld3852H5hdLejH8Pc+KZy+TfaEvbodr7wm2aexYjn4otV3k03hXZ3gtgcmNTOS0qrrBt/QD/240BkhDpueIlls6gl86leKz2AvgG7RDmqVpXAqdB3jOiX+hRZjGJHcXaQ5mQ/86XgKkvNjW7LDBppQttVl1tQpKAgMJQRJ9jDfFuli3SgntqOP/9yvetFOirDStor36plhGnJXQ3Dfeeea4xVsZzPzV3F6eeiCdOU/ew1Qns4vDzIjSrgtgyr3/3u3uEQMsgQVEn7usOE3FbBGzeKgro02zdyOaHG+pt+1CpGSHMN7GZiQZrlXboMsFfvP/9p9l4mtZMY4i6/JErwxeh997tfQbT67ePdubuT5dG8pYRJ4rg7iB23NMsYUU2DRoS0R9JVIri8xCTTU5kEhlNq2Yy7kFBq46MNhUpYHh1CFuujAywmSXDsIcjldd1Lw8p2Q8boTnk01x+pt6iGlcLwQ5FSgsJ5dUSqc5lfqnRoUcVCRm2D3NSQBeYAqOdcxpC0ZvMDUotlIG7oVJoucA/6U7QFKP0ZHRUynHZqNW6qGRGdSEY16MT5yytIoc03VGKNvT5UvK2lUicMe4st6Vv1tdRpHeUVTWlU8Bebzwa35VxF0co0cOdJJ9Ql5FnFD+bk4bih3IkoCSU7xj1MczON8hlNk5GwbAM+nT6Dexoiv82E0M8hSj0gfPdLCKlfNfm7KuVRUPFBBCXgyZqCHOawhwnMO96CecBvKO2uB0iNc9XIIWsQwcrRpudk+hBvTmNcFmcmhhsGtmVqhfwZnr0BNzJZE5pNepGNZJbY7nAhrpJN1CxaDVU5u0wXdmxB7oA5V/GHB9lDwESWK5ZUi3uucNTEsD5k+P9km95GfZ09xpHwNWMrjSikqE+16FDGMnak8o1JoOQBmkjFJ37pDgo80saSZRvDCElsM1EX7P1Kj+h1lhC80IaQEW6Ct0dik20ol8PXEemPjQp1CzBdbj4AASZMgN55yjnbQr8XSwc4/NIAzQ5N2BPbRgpIyzp4rQlEf04hg6RtDb74V975aNyXvptFevSC//oc/7WcHQXb38g5bMNteI9LdsZb7bVQaVoS0cZwRpA4iaC5vdBSw0WaeNlWvOVlh5AMLGUDlmgiYi3o+Po3gRbBlPU74aMjdB6u8EoqWTF+L1oTnew5cNtKfHnY7QmnOC65Y9CrINWMJdM6dfpsOb0koRxLCjiwOIeZTaf4n+cskg7fpBhPCVaYNo/lqBjhvT4pYGJp0N3Pke1NKMBzJ5ZKJSs5A6AcpUTEQeOib384IvEalXEW26AVS/F+wZCkzcXMGHyX7Ai+yFYXVdQf78iE1N7i8CysNI4STMKmjaJUe3+/ucOZ9fVHOCXHF2exhs24MbczXemlohleo0fNwVJjTrAOcUuXyjhKgee4UnpNPajhHktYSEjNXRCczT0IHWYZCTcqcF6tXVE5mPd5WdeJhRtxTjedzGimWtOtnJSoAutzcvBpXWJoljf7WYgspAc4ZZ4PTkvzw+IUlx0Mza1+8h7tGgNX5pBWQ2soGHXz4z912IuxsIonGsmVvYbv7hgJxHHz6tfzGs6YXlIuwpm9vd0m2zNpGh7JUigj2loKNT1NWRtOjcZr2Trj66boR5TdK1I5sj0vy1LAVF3P2rnTbR7o4KcSp7OdswX4nJdpSWL9eLUAtlGau1cSZWrVKBLmEC6YN7NvghvESMvR07U6b+65n3xmk+aBNkS/rJRFbTwVIZ+TVnOecOirxu6k9aMEJkw23s2XwTLYHQ3/jwyWlt5eqms1AHhrHRYZR9fIXTuWLG3tp3sD0ft6Qj7xXB7iDeDu61COYzer+5PXWjR3fGTdpBuupCvptmMNFPA5ICsJViVc5Qjw+NDgxzsF8pDn47LmXMBXegVsV2kBgfHcZVBRxUhKUvNxk35KbfpDR2lGymQXrvmteyflGO/cX5FufjLun4GM48etvT7uGmxtafGzRkwTC6djoabNUnxM/rW/ihNrNaFtYZOwviOk43eXj7mHZiKsI75438koMIAjuDUOX1XqjoRPWibLkfTToly2wlIWg6WkhSW0DG5GCE54F7vjVjjXeeyLlXOkjGOyZhvOPbdYyJgCjVNJ0/QFI1NsgB2y/etHD32XN7V3y113EWAnOAq122gMYWiBsGCJ63lsPXDhz3DYDWsRHgqwmfLwSHGRg0R3eHx7bGzPaYnPIuvU3ds+CNWpDk4Lt0lMhAOa4y9Q6Wvmz09HzZZ166apiuHk9odw/7ufjX6hW/iEkZc2nrOVmHX8qQ83ClE4+MribQJnecJY0wxnqv30V19oyMJDQWC8aYtNGbaeUz1jNRmKtzn2Nxx1QCOQaUsVjUcbsnDXeRZuragW/i4Ys/+33/QSYCR0+3JEjHdujcYjoZkmPxrIl/KHVWu50DVsw79n00asAYkkcUkH8Hm1qvHM6ppTgS9kk+851rHc8uUGu9q3k2tCE+M6UrYl/OxAnufF2dTc8PpxbTfaWpFiuVxAhEcZR5MMQ5DtkcrDj2c8NfyWze9hWtPbsDtY11EEtCSI8qzyCtZ9lbgeZwo2odXPVGVEItEMb0sEixiTzbL+o2z4awbxcbShwt//XzhoT6zUhRHzPWcC0tNsjdmv0iP3M3zLbMS5a02W9UrPsO64wDJebd0dnmh95zQV3PG57Sb738rKT3+koURYk4P649Fc+0mqZNkjOAQ1TYtRhag0kZ9NZneth2+2un4lkz947JTrY6ejjBXlt9n8BW/sxHqT+ESXLNcvjBqUyi3Wq6PWWepqOwbugzXdNiI0WMpgNIZI9aBOvVg5MJu//sOVvz/ZmoZQuePXf1hUUlJcVGbSv4sKpdRaMF4OovXfO1sNx0EORmuSsKLx4lO7EfSrNdtyrlSeZSwTxzlFpZjKDs51yuA27x/FLwaWzuDN66UC29vA/D78Z754UbwKD11M/nojN0yNyMQE9wleVjTVbrOuBGPiataPJI2KGacTIbvlbIIWjTafzpZ5kwtLE50pg7zuC3mdaGZ3hTiTjv8whlEt4pkfvjO8o5DVABJW4XDm3uGllOzXEcPSiuPs8and/4/NF+9ypHXpJ9nXLr/W049MEu3yO9jjPtmSipLx5Bn/5v7HCj/FWRvenXs/E6AUw2H89EqDiAUl05OZbOqGl7Z7jQJMP1a5NVbmTsxgXmhJavrBJ+DitVeAZfepoRxfstP+tUCw784IcvPtaPpj0VQGg8ZgcdMKCgpVch6dTiEpExPk7Wa16S/3S6s4+6NbTPbbjz/Zo6U7owHYXLE2n45Vs9ee/O7EjfL2193lq0lZErGktFQp5sQBmqCBDobM6CED73KxVpUxMCKi4peDSMQuOszFrvru36qDko+Pj1th88PzuuaSUY3mQEC/J9cetRtVJa7xnvcnOeYCRg8IBXzjQlxYgiMTkMtJH/tAEuVLMzyYTdSfplf1dHYXxyerOukz80D80fZBNDz1txngYQJ347ez3tUoZRkpRCtp2UtUmapmReR2iVQNopm+rDyiti4QcOxDwvaSNTUu+XkdWcZNAK6NF8a5JVWfzY3xVpipt7kE2j/GDbE2WrRq1+3epXCb1G2jDa9EBUqMsLUiyihkbJBaf3q83NOnSBLNy1ddP6am0TW5si5NHFPIYt2P5MBq+eZfhO0+ABz0nlBps5WIm0uw9YJpXLNNSyG+OKouaQuHSfk2mjOOLnZhRnJnJToPSripY1QHyU6cs2kbF3RL6KH87+PrVvhPTkVW0uAoKG8Y5aigJzJVSKTuCF0VolL3Cw4pS0CEHlWozVfeKcu4SaEhS57ZLN4UbZOO1FvE26YFqK/xyhcOfD0WPlrUcHNscGXE23JNZlzCSiUxeg1XZpnSCz3bTmUtH8wqg4ShasqamVvfoepxwqLuYqoeOB8iPVknnM2DmDxaR0Dz1mPZhEQQy9IIwm7tpf1cJYC19zqEMgpIz6w4xVmsaHKBVkg9sVS2RlarFbQw6zrdTktGHyqFUu2NOyM9KMd98OJzt71ERkAjVM73VepPmx9Lt3nKtcf6H/GSc7SntzfluDVqX5fmuqXMsnITLZwvKy0RXSI6Zlgi1qag1bUiOn47pRLuTZKZy99+7+s/W3DmBrwd+qhacUneREaocBtj5/1Hq09VGaxGHA3WGMWJ0auzzYJlP/f9HTdlMroL1zpfRbn08j6oJwxX8aLnUOPwe5B7VwACACDgn2du+tCDf3zuiatLpAqN8Tff2/OBP3Tnj6V3NVtrLcupaaqBV9FgpxD4Dx4qesmO0H9jCE1EW9RdV53Am+zct1Xb5ijuM5jWBjljp4j+RHxcfV9Kfx4k6+LyiuLTbo9MNs/cIBfnqs1f1JkYZ41ww98wMQoMsREQiwQpo2cFlayeYRPTnUxIuioAtZu2zoCsfg/5ShKp92w8JJ/zuZTzxssfsLtZM/U0j1ODdshMVj1QpH98hVpTUdj9qbN1Eyg8P7ZO1aNVGiCf5Zp1DqTLRM7nM3NructdX8yjkgjrk+b2VBJZIdn5PN4X5U23vmpOCnaxIa8p0yOlOUWBrVAPpLJZSonNTta1ByLzBV779e9tcqDtTrPmmFIYcLvCrQGYVXj0NgCbfFh5t3Jn2BppStf9nEpbeu2NheOQsHzMtg2CQA4M7WsUyGXEWltuM684Rt3o/APNfZn0XM/HLdqt58/PcbBpg7Ci97IeRkyGOb0mtiDn/XYN2l+lvwxYAkGA/DJQeaoa8GFav8ecNt01aoNCgjL0EADK1ahRaM55XzbHZ+QtsjGflHyIRrU8zcNf6o7EEmwKyAkoKEMPA6BcoOA8epY5UfMUIWuqldDseOQoeEQMSYjZyswCcw2YDz+TylW58R+sssMkyfWOs2oYjgwztfGcWzPj2RlJ0FgRNNn5f8h0aNMtj6Eul4thXjItsDPRGRp04BW6AcY7sX1vGi5t0EPoVMubpgg4B+F8XAfGtgTjd1ayRV72XSW/LY7v55fjnxddsWenxYewz6oaJDeJ+SUiqBKra5s5dXR21UguNrU6Jf3+EYkIBddWBgTQFq8RxQYJY5ltG8CfXT8fAQHQDGOdL0V9uBvTBMJOLkwlmQgL4xmSfpxC4cY2NLxIHxWmYb8QADPMIWDEnBBl/GScAwpYoYEG9FChAGxjVMDYM6owXSMWE1JqDPljm2UWLiZ92jEmZSG1mWTIyfHJAC4uJ15ZQoVJY5w/2lNsOGlKsd204wkVUWZVY6XCJR6se65foNPWIIhNCfMdd3pxz91lF+56//NsOBezRKXn4xeqlFX+i+U0krXUplG75dK3yrTKHHOcBXY0zlRtW1pblyLIqwq7pxbVZalCDstZS/EL6lnT2zx96Y2O4Cd5ab9HYdFyzim8cvf4eu51y5pKBqyy+f4po/Ua/SKUafz7ng6hy6V75IK78j3uN4Prm5h0+Mu8QstJ1RWSmDHIBrhy09nz6otKVt5ZFiVFpUoHFlYlH1slnExOILu1JXw8rz5fmDGk+VBSV/7F521RfrG0BBz9l/+XkyBKMoAIE8q4kBVV0w3Tsh3X84MwipM0y4uyqpu264dxmpd127tyC5asWLNhy449B46cOHPBt4IrATfuPHjystIqq3nz4cuPvwBCgYIEBwl7FSh0Ua2vilQpt9Nh+4KCsqBBvg2hgOhQGYpQ4ro3wYA6Df77Z8AeR7W7rUmIUDXCdArXpsN9d9x1zzcRHnvgoWaR+q3zzBNPRfnhp1Iia0SLFSPOLvESJUiSbC0xiRTfpUqXJkOWTK12y5FNKlevPudCCTHhmOO6vPDKa91OOKnFGTecctpNxX5UueDVZssqldICCQAhGEExnCBTqDQ6o1QvM1nhbA6XxxcIRWKJVCZXKFVqjVanNxhNZovVZnc4XW6P1+d3KcXA7DNW6xA9OSxeyS8vN3LKHzgxqFk4hly8VewrIFlMltfVjk5s8Y2jpYN7fPi53ONjsKWODvIp/MQ++XK1RMlysppon84VkrVY37l6nV5PTTGgjg19/UdzV/nimTscw619Kb6c/DVejpOVthqyt5Y5Vgqx/MItPX9ZsYrv30h4HTyRSMWGPrdxvpRGQU2RK6lWO7VztTEwXLiBAfLX6bvD3hH+CneYa9xtOSeHnh8W6sSY9HNdPN+UnFY/38YR+McNDqg/bk6rnK84w+GD0s3H52yBilKNVGCq4QoUVOBiFwBWcMAKnmQXAE8XBtoGgAcAggNrBGoEAoBrDqw5EAjU+Od+ZfJ8ub6QojprOoHmJquL7ZJG+5vVK18lVK5mrZJRrUr4ckalGNXLRV0qvZvFklkoZORzWT2Xi8jmBD2T0+lcHjqd7wul8qyebPOaiTYdz6qOZf1mNBuKZNf1zRnRoXTbDKZDgXRW96c0wpd6BW9K4knSdCe0K6GmM5GxE3/IEZdsNe12hi0msUa1JfqcYY4SuskyjRFtMMXUm1pn9mUw4VegwxmU/lWkrgm9bWqNkMa4RVdr1KoQM5Tq/fq2umZLXaZv1J/9uEOvFtfQSi6lJ+J17HRAkTfbNzN6LFrXJ7xpY4R1I69HZF03ZX/4vn6Lfk+vM0qVhM3aNVUPiQuDLRR9s7DbuUnaFKqbgjom/oEHrvcIC21X/GvYFWaNP8AEaDlJLkcZBVig4mifHTL3nOSVodxJKVcSY+CJgSAgAv9VJRwsfOh7u0NMIAtyIz05lypAgYqhPh2Sex6OZHdM9gH8UkxDLH+QpZW0d/jjS+/At4VxPTQdK/gOEcaCZ4f870R88YL+40e4XR1tX6YE7/JgC214JxE98YvJvBCujjlzJh+oyL45siz8YQC6B1LQsssuagA23MBZ/5WYi7r7Tkk=",
    "f4e80d9dfd37.woff2": "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"
}
