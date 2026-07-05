# coding=UTF-8
# WebUI 静态资源 — 由 build_frontend.py 自动生成
# 请勿手动编辑。模板文件在 templates/ 和 static/ 目录。

from html import escape


def _html_attr(name: str, value: str = None) -> str:
    if value is None:
        return ''
    return f' {name}="{escape(str(value), quote=True)}"'


def panel_head(
        *,
        title_i18n: str,
        title_text: str,
        meta_i18n: str = None,
        meta_text: str = None,
        meta_id: str = None,
        indent: int = 10
) -> str:
    pad = ' ' * indent
    child_pad = ' ' * (indent + 2)
    title = escape(title_text, quote=False)
    head = [
        f'{pad}<div class="panel-head" data-component="panel-head">',
        f'{child_pad}<h3 class="panel-head__title"{_html_attr("data-i18n", title_i18n)}>{title}</h3>'
    ]
    if meta_text is not None or meta_i18n is not None or meta_id is not None:
        meta = escape(meta_text or '', quote=False)
        head.append(
            f'{child_pad}<div class="panel-head__meta"'
            f'{_html_attr("id", meta_id)}'
            f'{_html_attr("data-i18n", meta_i18n)}>{meta}</div>'
        )
    head.append(f'{pad}</div>')
    return '\n'.join(head)


WEB_UI_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TRMD · 转存控制台</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>/*! tailwindcss v4.1.18 | MIT License | https://tailwindcss.com */
@layer properties{@supports (((-webkit-hyphens:none)) and (not (margin-trim:inline))) or ((-moz-orient:inline) and (not (color:rgb(from red r g b)))){*,:before,:after,::backdrop{--tw-rotate-x:initial;--tw-rotate-y:initial;--tw-rotate-z:initial;--tw-skew-x:initial;--tw-skew-y:initial;--tw-border-style:solid;--tw-font-weight:initial;--tw-shadow:0 0 #0000;--tw-shadow-color:initial;--tw-shadow-alpha:100%;--tw-inset-shadow:0 0 #0000;--tw-inset-shadow-color:initial;--tw-inset-shadow-alpha:100%;--tw-ring-color:initial;--tw-ring-shadow:0 0 #0000;--tw-inset-ring-color:initial;--tw-inset-ring-shadow:0 0 #0000;--tw-ring-inset:initial;--tw-ring-offset-width:0px;--tw-ring-offset-color:#fff;--tw-ring-offset-shadow:0 0 #0000;--tw-outline-style:solid;--tw-blur:initial;--tw-brightness:initial;--tw-contrast:initial;--tw-grayscale:initial;--tw-hue-rotate:initial;--tw-invert:initial;--tw-opacity:initial;--tw-saturate:initial;--tw-sepia:initial;--tw-drop-shadow:initial;--tw-drop-shadow-color:initial;--tw-drop-shadow-alpha:100%;--tw-drop-shadow-size:initial;--tw-backdrop-blur:initial;--tw-backdrop-brightness:initial;--tw-backdrop-contrast:initial;--tw-backdrop-grayscale:initial;--tw-backdrop-hue-rotate:initial;--tw-backdrop-invert:initial;--tw-backdrop-opacity:initial;--tw-backdrop-saturate:initial;--tw-backdrop-sepia:initial;--tw-tracking:initial;--tw-duration:initial;--tw-leading:initial}}}@layer theme{:root,:host{--font-sans:ui-sans-serif,system-ui,sans-serif,"Apple Color Emoji","Segoe UI Emoji","Segoe UI Symbol","Noto Color Emoji";--font-mono:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono","Courier New",monospace;--color-red-200:oklch(88.5% .062 18.334);--color-red-300:oklch(80.8% .114 19.571);--color-orange-50:oklch(98% .016 73.684);--color-slate-100:oklch(96.8% .007 247.896);--color-slate-300:oklch(86.9% .022 252.894);--color-slate-500:oklch(55.4% .046 257.417);--color-black:#000;--color-white:#fff;--spacing:.25rem;--text-xs:.75rem;--text-xs--line-height:calc(1/.75);--text-sm:.875rem;--text-sm--line-height:calc(1.25/.875);--text-lg:1.125rem;--text-lg--line-height:calc(1.75/1.125);--text-xl:1.25rem;--text-xl--line-height:calc(1.75/1.25);--text-2xl:1.5rem;--text-2xl--line-height:calc(2/1.5);--font-weight-medium:500;--font-weight-semibold:600;--font-weight-bold:700;--font-weight-extrabold:800;--leading-tight:1.25;--radius-lg:.5rem;--radius-xl:.75rem;--animate-spin:spin 1s linear infinite;--default-transition-duration:.15s;--default-transition-timing-function:cubic-bezier(.4,0,.2,1);--default-font-family:var(--font-sans);--default-mono-font-family:var(--font-mono);--color-primary:#2563eb;--color-primary-light:#3b82f6;--color-primary-soft:#eff6ff;--color-primary-ghost:#dbeafe;--color-primary-dark:#1d4ed8;--color-bg:#f0f4ff;--color-surface:#fff;--color-surface-alt:#f8fafc;--color-surface-hover:#f1f5f9;--color-text:#1e293b;--color-text-secondary:#475569;--color-muted:#94a3b8;--color-line:#e2e8f0;--color-line-light:#f1f5f9;--color-success:#10b981;--color-success-bg:#ecfdf5;--color-warning:#f59e0b;--color-danger:#ef4444;--color-danger-bg:#fef2f2;--color-cta:#f97316;--font-heading:"Poppins",ui-sans-serif,system-ui,sans-serif;--font-body:"Open Sans",ui-sans-serif,system-ui,sans-serif}}@layer base{*,:after,:before,::backdrop{box-sizing:border-box;border:0 solid;margin:0;padding:0}::file-selector-button{box-sizing:border-box;border:0 solid;margin:0;padding:0}html,:host{-webkit-text-size-adjust:100%;tab-size:4;line-height:1.5;font-family:var(--default-font-family,ui-sans-serif,system-ui,sans-serif,"Apple Color Emoji","Segoe UI Emoji","Segoe UI Symbol","Noto Color Emoji");font-feature-settings:var(--default-font-feature-settings,normal);font-variation-settings:var(--default-font-variation-settings,normal);-webkit-tap-highlight-color:transparent}hr{height:0;color:inherit;border-top-width:1px}abbr:where([title]){-webkit-text-decoration:underline dotted;text-decoration:underline dotted}h1,h2,h3,h4,h5,h6{font-size:inherit;font-weight:inherit}a{color:inherit;-webkit-text-decoration:inherit;-webkit-text-decoration:inherit;-webkit-text-decoration:inherit;text-decoration:inherit}b,strong{font-weight:bolder}code,kbd,samp,pre{font-family:var(--default-mono-font-family,ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono","Courier New",monospace);font-feature-settings:var(--default-mono-font-feature-settings,normal);font-variation-settings:var(--default-mono-font-variation-settings,normal);font-size:1em}small{font-size:80%}sub,sup{vertical-align:baseline;font-size:75%;line-height:0;position:relative}sub{bottom:-.25em}sup{top:-.5em}table{text-indent:0;border-color:inherit;border-collapse:collapse}:-moz-focusring{outline:auto}progress{vertical-align:baseline}summary{display:list-item}ol,ul,menu{list-style:none}img,svg,video,canvas,audio,iframe,embed,object{vertical-align:middle;display:block}img,video{max-width:100%;height:auto}button,input,select,optgroup,textarea{font:inherit;font-feature-settings:inherit;font-variation-settings:inherit;letter-spacing:inherit;color:inherit;opacity:1;background-color:#0000;border-radius:0}::file-selector-button{font:inherit;font-feature-settings:inherit;font-variation-settings:inherit;letter-spacing:inherit;color:inherit;opacity:1;background-color:#0000;border-radius:0}:where(select:is([multiple],[size])) optgroup{font-weight:bolder}:where(select:is([multiple],[size])) optgroup option{padding-inline-start:20px}::file-selector-button{margin-inline-end:4px}::placeholder{opacity:1}@supports (not ((-webkit-appearance:-apple-pay-button))) or (contain-intrinsic-size:1px){::placeholder{color:currentColor}@supports (color:color-mix(in lab, red, red)){::placeholder{color:color-mix(in oklab,currentcolor 50%,transparent)}}}textarea{resize:vertical}::-webkit-search-decoration{-webkit-appearance:none}::-webkit-date-and-time-value{min-height:1lh;text-align:inherit}::-webkit-datetime-edit{display:inline-flex}::-webkit-datetime-edit-fields-wrapper{padding:0}::-webkit-datetime-edit{padding-block:0}::-webkit-datetime-edit-year-field{padding-block:0}::-webkit-datetime-edit-month-field{padding-block:0}::-webkit-datetime-edit-day-field{padding-block:0}::-webkit-datetime-edit-hour-field{padding-block:0}::-webkit-datetime-edit-minute-field{padding-block:0}::-webkit-datetime-edit-second-field{padding-block:0}::-webkit-datetime-edit-millisecond-field{padding-block:0}::-webkit-datetime-edit-meridiem-field{padding-block:0}::-webkit-calendar-picker-indicator{line-height:1}:-moz-ui-invalid{box-shadow:none}button,input:where([type=button],[type=reset],[type=submit]){appearance:button}::file-selector-button{appearance:button}::-webkit-inner-spin-button{height:auto}::-webkit-outer-spin-button{height:auto}[hidden]:where(:not([hidden=until-found])){display:none!important}html{font-family:var(--font-body);color:var(--color-text);background:var(--color-bg);font-size:14px}body{min-height:100vh;display:flex}button,input,select,textarea{font-family:inherit;font-size:inherit}button{cursor:pointer}button:disabled{cursor:not-allowed;opacity:.55}}@layer components{.sidebar{top:calc(var(--spacing)*0);z-index:50;border-right-style:var(--tw-border-style);border-right-width:1px;border-color:var(--color-line);background-color:var(--color-white);width:250px;height:100vh;padding-inline:calc(var(--spacing)*4);padding-block:calc(var(--spacing)*6);flex-direction:column;display:flex;position:sticky}.sidebar-brand{margin-bottom:calc(var(--spacing)*3);align-items:center;gap:calc(var(--spacing)*3);border-bottom-style:var(--tw-border-style);border-bottom-width:1px;border-color:var(--color-line);padding-bottom:calc(var(--spacing)*5);display:flex}.sidebar-brand-mark{height:calc(var(--spacing)*10);width:calc(var(--spacing)*10);font-size:var(--text-lg);line-height:var(--tw-leading,var(--text-lg--line-height));--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold);color:var(--color-white);background:linear-gradient(135deg,var(--color-primary),var(--color-primary-light));font-family:var(--font-heading);border-radius:10px;justify-content:center;align-items:center;display:flex;box-shadow:0 4px 10px #2563eb4d}.sidebar-nav-section{flex:1;overflow-y:auto}.sidebar-nav-label{padding-inline:calc(var(--spacing)*2.5);padding-top:calc(var(--spacing)*4);padding-bottom:calc(var(--spacing)*2);--tw-font-weight:var(--font-weight-semibold);font-size:11px;font-weight:var(--font-weight-semibold);--tw-tracking:.08em;letter-spacing:.08em;color:var(--color-muted);text-transform:uppercase}.sidebar-nav-item{cursor:pointer;align-items:center;gap:calc(var(--spacing)*2.5);border-style:var(--tw-border-style);width:100%;padding-inline:calc(var(--spacing)*3);padding-block:calc(var(--spacing)*2.5);text-align:left;--tw-font-weight:var(--font-weight-medium);font-size:13px;font-weight:var(--font-weight-medium);color:var(--color-text-secondary);transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;background-color:#0000;border-width:0;border-radius:8px;font-family:inherit;transition-duration:.15s;display:flex}.sidebar-nav-item:hover{background-color:var(--color-primary-soft);color:var(--color-primary)}.sidebar-nav-item.active{background-color:var(--color-primary-soft);--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-primary)}.sidebar-nav-item svg{flex-shrink:0;width:18px;height:18px}.sidebar-nav-badge{background-color:var(--color-primary-ghost);padding-inline:calc(var(--spacing)*2);padding-block:calc(var(--spacing)*.5);--tw-font-weight:var(--font-weight-bold);font-size:11px;font-weight:var(--font-weight-bold);color:var(--color-primary);border-radius:3.40282e38px;margin-left:auto}.sidebar-footer{margin-top:calc(var(--spacing)*2);gap:calc(var(--spacing)*1.5);border-top-style:var(--tw-border-style);border-top-width:1px;border-color:var(--color-line);padding-top:calc(var(--spacing)*4);flex-direction:column;display:flex}.sidebar-footer-info{align-items:center;gap:calc(var(--spacing)*2);padding-inline:calc(var(--spacing)*2);padding-block:calc(var(--spacing)*1);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));color:var(--color-text-secondary);display:flex}.sidebar-status-dot{height:calc(var(--spacing)*2);width:calc(var(--spacing)*2);background:var(--color-success);border-radius:3.40282e38px;flex-shrink:0;box-shadow:0 0 0 3px #10b98133}.sidebar-version{padding-inline:calc(var(--spacing)*2);color:var(--color-muted);opacity:.7;font-size:11px}.main-content{min-width:calc(var(--spacing)*0);gap:calc(var(--spacing)*6);padding:calc(var(--spacing)*7);flex-direction:column;flex:1;display:flex}.topbar{justify-content:space-between;align-items:flex-start;gap:calc(var(--spacing)*4);display:flex}.topbar h1{font-size:var(--text-2xl);line-height:var(--tw-leading,var(--text-2xl--line-height));--tw-leading:var(--leading-tight);line-height:var(--leading-tight);--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold);color:var(--color-text);font-family:var(--font-heading)}.topbar p{margin-top:calc(var(--spacing)*1);color:var(--color-muted);font-size:13px}.btn{cursor:pointer;align-items:center;gap:calc(var(--spacing)*1.5);border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);padding-inline:calc(var(--spacing)*4);padding-block:calc(var(--spacing)*2);--tw-font-weight:var(--font-weight-medium);font-size:13px;font-weight:var(--font-weight-medium);white-space:nowrap;color:var(--color-text);transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;border-radius:6px;font-family:inherit;transition-duration:.15s;display:inline-flex}.btn:hover{border-color:var(--color-primary-light);background-color:var(--color-primary-soft)}.btn svg{height:calc(var(--spacing)*4);width:calc(var(--spacing)*4);flex-shrink:0}.btn-primary{border-color:var(--color-primary);background-color:var(--color-primary);--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-white)}.btn-primary:hover{border-color:var(--color-primary-dark);background-color:var(--color-primary-dark);color:var(--color-white)}.btn-danger{border-color:var(--color-red-200);color:var(--color-danger)}.btn-danger:hover{border-color:var(--color-danger);background-color:var(--color-danger-bg);color:var(--color-danger)}.btn-sm{padding-inline:calc(var(--spacing)*2.5);padding-block:calc(var(--spacing)*1);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height))}.btn-icon{width:34px;height:34px;padding:calc(var(--spacing)*0);justify-content:center}.stat-grid{gap:calc(var(--spacing)*4);grid-template-columns:repeat(4,minmax(0,1fr));display:grid}.stat-card{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);--tw-shadow:0 1px 3px 0 var(--tw-shadow-color,#0000001a),0 1px 2px -1px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow);transition-property:box-shadow;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.2s;border-radius:12px;justify-content:space-between;align-items:flex-start;padding:18px;transition-duration:.2s;display:flex}.stat-card:hover{border-color:var(--color-primary-ghost);--tw-shadow:0 4px 6px -1px var(--tw-shadow-color,#0000001a),0 2px 4px -2px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow)}.stat-card-icon{height:calc(var(--spacing)*10);width:calc(var(--spacing)*10);border-radius:8px;flex-shrink:0;justify-content:center;align-items:center;display:flex}.stat-card-icon.blue{background-color:var(--color-primary-soft);color:var(--color-primary)}.stat-card-icon.green{background-color:var(--color-success-bg);color:var(--color-success)}.stat-card-icon.orange{background-color:var(--color-orange-50);color:var(--color-cta)}.stat-card-icon.red{background-color:var(--color-danger-bg);color:var(--color-danger)}.stat-card-icon svg{height:calc(var(--spacing)*5);width:calc(var(--spacing)*5)}.stat-card-value{text-align:right;--tw-leading:var(--leading-tight);font-size:28px;line-height:var(--leading-tight);--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold);color:var(--color-text);font-family:var(--font-heading)}.stat-card-label{margin-top:calc(var(--spacing)*1);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-medium);font-weight:var(--font-weight-medium);color:var(--color-muted)}.panel{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);--tw-shadow:0 1px 3px 0 var(--tw-shadow-color,#0000001a),0 1px 2px -1px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow);border-radius:12px;flex-direction:column;display:flex;overflow:hidden}.panel-header{border-bottom-style:var(--tw-border-style);border-bottom-width:1px;border-color:var(--color-line);background-color:var(--color-surface-alt);padding-inline:18px;padding-block:calc(var(--spacing)*3.5);justify-content:space-between;align-items:center;display:flex}.panel-header h3{font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-text);font-family:var(--font-heading)}.panel-body{flex:1;padding:18px;overflow-y:auto}.panel-tabs{gap:calc(var(--spacing)*.5);display:flex}.panel-tab{cursor:pointer;border-style:var(--tw-border-style);padding-inline:calc(var(--spacing)*2.5);padding-block:calc(var(--spacing)*1);--tw-font-weight:var(--font-weight-medium);font-size:11px;font-weight:var(--font-weight-medium);color:var(--color-text-secondary);transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.1s;background-color:#0000;border-width:0;border-radius:.25rem;font-family:inherit;transition-duration:.1s}.panel-tab:hover{background-color:var(--color-primary-soft);color:var(--color-primary)}.panel-tab.active{background-color:var(--color-primary-soft);--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-primary)}.form-group{margin-bottom:calc(var(--spacing)*3.5)}.form-label{margin-bottom:calc(var(--spacing)*1.5);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);--tw-tracking:.04em;letter-spacing:.04em;color:var(--color-muted);text-transform:uppercase;display:block}.form-input,.form-select{height:calc(var(--spacing)*10);border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);width:100%;padding-inline:calc(var(--spacing)*3);color:var(--color-text);transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;--tw-outline-style:none;border-radius:6px;outline-style:none;font-family:inherit;font-size:13px;transition-duration:.15s}.form-input:focus,.form-select:focus{border-color:var(--color-primary);box-shadow:0 0 0 3px #2563eb1f}.form-row{gap:calc(var(--spacing)*2.5);grid-template-columns:repeat(2,minmax(0,1fr));display:grid}.form-submit{margin-top:calc(var(--spacing)*1.5);height:calc(var(--spacing)*10);cursor:pointer;justify-content:center;align-items:center;gap:calc(var(--spacing)*1.5);border-style:var(--tw-border-style);background-color:var(--color-primary);--tw-font-weight:var(--font-weight-semibold);width:100%;font-size:13px;font-weight:var(--font-weight-semibold);color:var(--color-white);transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;border-width:0;border-radius:6px;font-family:inherit;transition-duration:.15s;display:flex}.form-submit:hover{background-color:var(--color-primary-dark)}.data-table{border-collapse:collapse;width:100%;font-size:13px}.data-table thead th{top:calc(var(--spacing)*0);border-bottom-style:var(--tw-border-style);border-bottom-width:2px;border-color:var(--color-line);background-color:var(--color-surface-alt);padding-inline:calc(var(--spacing)*3);padding-block:calc(var(--spacing)*2.5);text-align:left;--tw-font-weight:var(--font-weight-semibold);font-size:11px;font-weight:var(--font-weight-semibold);--tw-tracking:.05em;letter-spacing:.05em;white-space:nowrap;color:var(--color-muted);text-transform:uppercase;position:sticky}.data-table tbody td{border-bottom-style:var(--tw-border-style);border-bottom-width:1px;border-color:var(--color-line-light);padding-inline:calc(var(--spacing)*3);padding-block:calc(var(--spacing)*2.5);vertical-align:middle;font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height))}.data-table tbody tr{cursor:pointer;transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:75ms;transition-duration:75ms}.data-table tbody tr:hover{background-color:var(--color-surface-hover)}.data-table tbody tr.selected{background-color:var(--color-primary-soft)}.badge{padding-inline:calc(var(--spacing)*2.5);padding-block:calc(var(--spacing)*.5);--tw-font-weight:var(--font-weight-semibold);font-size:11px;font-weight:var(--font-weight-semibold);border-radius:3.40282e38px;align-items:center;display:inline-flex}.badge-running{background-color:var(--color-primary-soft);color:var(--color-primary)}.badge-success{background-color:var(--color-success-bg);color:var(--color-success)}.badge-failed{background-color:var(--color-danger-bg);color:var(--color-danger)}.badge-pending{background-color:var(--color-orange-50);color:var(--color-cta)}.badge-paused,.badge-skipped{background-color:var(--color-slate-100);color:var(--color-slate-500)}.progress-bar{height:calc(var(--spacing)*1.5);background-color:var(--color-slate-100);border-radius:3.40282e38px;overflow:hidden}.progress-fill{height:100%;transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.3s;background:linear-gradient(90deg,var(--color-primary-light),var(--color-primary));border-radius:3.40282e38px;transition-duration:.3s}.status-dot{margin-right:calc(var(--spacing)*1.5);height:calc(var(--spacing)*1.5);width:calc(var(--spacing)*1.5);vertical-align:middle;border-radius:3.40282e38px;display:inline-block}.status-dot.running{background-color:var(--color-primary)}.status-dot.success{background-color:var(--color-success)}.status-dot.failed{background-color:var(--color-danger)}.status-dot.pending{background-color:var(--color-warning)}.status-dot.paused{background-color:var(--color-slate-300)}.activity-item{gap:calc(var(--spacing)*2);border-bottom-style:var(--tw-border-style);border-bottom-width:1px;border-color:var(--color-line-light);padding-block:calc(var(--spacing)*1.5);--tw-leading:1.4;font-size:11px;line-height:1.4;display:flex}.activity-item:last-child{border-bottom-style:var(--tw-border-style);border-bottom-width:0}.activity-time{white-space:nowrap;min-width:44px;color:var(--color-muted);font-family:ui-monospace,monospace;font-size:10px}.activity-badge{--tw-font-weight:var(--font-weight-semibold);font-size:10px;font-weight:var(--font-weight-semibold);white-space:nowrap}.activity-badge.ok{color:var(--color-success)}.activity-badge.warn{color:var(--color-warning)}.activity-badge.err{color:var(--color-danger)}.view{display:none}.view.active{gap:18px;display:grid}.login-page{background-color:var(--color-bg);min-height:100vh;padding:calc(var(--spacing)*6);justify-content:center;align-items:center;display:flex}.login-card{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);width:100%;max-width:448px;padding:calc(var(--spacing)*10);--tw-shadow:0 10px 15px -3px var(--tw-shadow-color,#0000001a),0 4px 6px -4px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow);border-radius:16px}.login-brand{margin-bottom:calc(var(--spacing)*8);text-align:center}.login-brand-mark{margin-bottom:calc(var(--spacing)*4);--tw-font-weight:var(--font-weight-bold);width:52px;height:52px;font-size:24px;font-weight:var(--font-weight-bold);color:var(--color-white);background:linear-gradient(135deg,var(--color-primary),var(--color-primary-light));font-family:var(--font-heading);border-radius:14px;justify-content:center;align-items:center;display:inline-flex}.login-brand h1{--tw-font-weight:var(--font-weight-extrabold);font-size:28px;font-weight:var(--font-weight-extrabold);color:var(--color-text);font-family:var(--font-heading)}.login-brand p{margin-top:calc(var(--spacing)*1.5);color:var(--color-muted);font-size:13px}.login-error{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-red-300);background-color:var(--color-danger-bg);padding-inline:calc(var(--spacing)*3.5);padding-block:calc(var(--spacing)*2.5);color:var(--color-danger);border-radius:8px;margin-bottom:18px;font-size:13px;display:none}.login-error.visible{display:block}.login-field{margin-bottom:calc(var(--spacing)*5)}.login-field label{margin-bottom:calc(var(--spacing)*2);--tw-font-weight:var(--font-weight-medium);font-size:13px;font-weight:var(--font-weight-medium);color:var(--color-text);display:block}.login-field input{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);width:100%;height:46px;padding-inline:calc(var(--spacing)*3.5);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-text);transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;--tw-outline-style:none;border-radius:8px;outline-style:none;font-family:inherit;transition-duration:.15s}.login-field input:focus{border-color:var(--color-primary);box-shadow:0 0 0 3px #2563eb1f}.login-options{margin-bottom:calc(var(--spacing)*7);justify-content:space-between;align-items:center;display:flex}.login-checkbox{cursor:pointer;align-items:center;gap:calc(var(--spacing)*2);color:var(--color-muted);-webkit-user-select:none;user-select:none;font-size:13px;display:flex}.login-submit{cursor:pointer;justify-content:center;align-items:center;gap:calc(var(--spacing)*2);border-style:var(--tw-border-style);background-color:var(--color-primary);--tw-font-weight:var(--font-weight-semibold);width:100%;height:46px;font-size:15px;font-weight:var(--font-weight-semibold);color:var(--color-white);transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;border-width:0;border-radius:8px;font-family:inherit;transition-duration:.15s;display:flex}.login-submit:hover{background-color:var(--color-primary-dark)}.login-submit:disabled{cursor:not-allowed;opacity:.7}.login-submit:disabled:hover{background-color:var(--color-primary)}.spinner{width:18px;height:18px;animation:var(--animate-spin);border-style:var(--tw-border-style);border-width:2px;border-color:#ffffff4d;border-radius:3.40282e38px;flex-shrink:0}@supports (color:color-mix(in lab, red, red)){.spinner{border-color:color-mix(in oklab,var(--color-white)30%,transparent)}}.spinner{border-top-color:var(--color-white)}.watch-overlay{pointer-events:none;inset:calc(var(--spacing)*0);z-index:999;background-color:#00000059;justify-content:center;align-items:center;display:flex;position:fixed}@supports (color:color-mix(in lab, red, red)){.watch-overlay{background-color:color-mix(in oklab,var(--color-black)35%,transparent)}}.watch-overlay{opacity:0;transition-property:opacity;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.2s;transition-duration:.2s}.watch-overlay.open{pointer-events:auto;opacity:1}.watch-dialog{gap:calc(var(--spacing)*4);background-color:var(--color-surface);width:440px;max-width:calc(100vw - 32px);padding:calc(var(--spacing)*6);--tw-shadow:0 10px 15px -3px var(--tw-shadow-color,#0000001a),0 4px 6px -4px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow);border-radius:10px;display:grid}@media (max-width:1200px){.stat-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media (max-width:960px){.sidebar{display:none}.main-content{padding:calc(var(--spacing)*4)}}}@layer utilities{.collapse{visibility:collapse}.invisible{visibility:hidden}.visible{visibility:visible}.sr-only{clip-path:inset(50%);white-space:nowrap;border-width:0;width:1px;height:1px;margin:-1px;padding:0;position:absolute;overflow:hidden}.absolute{position:absolute}.fixed{position:fixed}.relative{position:relative}.static{position:static}.sticky{position:sticky}.bottom-0{bottom:calc(var(--spacing)*0)}.container{width:100%}@media (min-width:40rem){.container{max-width:40rem}}@media (min-width:48rem){.container{max-width:48rem}}@media (min-width:64rem){.container{max-width:64rem}}@media (min-width:80rem){.container{max-width:80rem}}@media (min-width:96rem){.container{max-width:96rem}}.mt-1{margin-top:calc(var(--spacing)*1)}.mt-2{margin-top:calc(var(--spacing)*2)}.mt-3{margin-top:calc(var(--spacing)*3)}.mt-4{margin-top:calc(var(--spacing)*4)}.mb-2{margin-bottom:calc(var(--spacing)*2)}.mb-3{margin-bottom:calc(var(--spacing)*3)}.mb-4{margin-bottom:calc(var(--spacing)*4)}.ml-1{margin-left:calc(var(--spacing)*1)}.block{display:block}.contents{display:contents}.flex{display:flex}.grid{display:grid}.hidden{display:none}.inline-flex{display:inline-flex}.table{display:table}.h-4{height:calc(var(--spacing)*4)}.w-4{width:calc(var(--spacing)*4)}.max-w-\[160px\]{max-width:160px}.max-w-\[180px\]{max-width:180px}.max-w-\[200px\]{max-width:200px}.max-w-\[240px\]{max-width:240px}.flex-shrink{flex-shrink:1}.border-collapse{border-collapse:collapse}.transform{transform:var(--tw-rotate-x,)var(--tw-rotate-y,)var(--tw-rotate-z,)var(--tw-skew-x,)var(--tw-skew-y,)}.cursor-pointer{cursor:pointer}.resize{resize:both}.grid-cols-2{grid-template-columns:repeat(2,minmax(0,1fr))}.flex-wrap{flex-wrap:wrap}.items-center{align-items:center}.justify-between{justify-content:space-between}.gap-1{gap:calc(var(--spacing)*1)}.gap-2{gap:calc(var(--spacing)*2)}.gap-3{gap:calc(var(--spacing)*3)}.gap-5{gap:calc(var(--spacing)*5)}.overflow-hidden{overflow:hidden}.overflow-x-auto{overflow-x:auto}.rounded{border-radius:.25rem}.rounded-lg{border-radius:var(--radius-lg)}.border{border-style:var(--tw-border-style);border-width:1px}.border-t{border-top-style:var(--tw-border-style);border-top-width:1px}.border-line{border-color:var(--color-line)}.bg-surface-alt{background-color:var(--color-surface-alt)}.bg-white{background-color:var(--color-white)}.p-4{padding:calc(var(--spacing)*4)}.p-8{padding:calc(var(--spacing)*8)}.py-3{padding-block:calc(var(--spacing)*3)}.pt-3{padding-top:calc(var(--spacing)*3)}.text-center{text-align:center}.text-right{text-align:right}.font-mono{font-family:var(--font-mono)}.text-sm{font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height))}.text-xl{font-size:var(--text-xl);line-height:var(--tw-leading,var(--text-xl--line-height))}.text-xs{font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height))}.text-\[10px\]{font-size:10px}.text-\[11px\]{font-size:11px}.text-\[12px\]{font-size:12px}.text-\[13px\]{font-size:13px}.font-bold{--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold)}.font-semibold{--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold)}.text-ellipsis{text-overflow:ellipsis}.whitespace-nowrap{white-space:nowrap}.text-danger{color:var(--color-danger)}.text-muted{color:var(--color-muted)}.text-primary{color:var(--color-primary)}.text-success{color:var(--color-success)}.text-text{color:var(--color-text)}.overline{text-decoration-line:overline}.underline{text-decoration-line:underline}.shadow{--tw-shadow:0 1px 3px 0 var(--tw-shadow-color,#0000001a),0 1px 2px -1px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow)}.outline{outline-style:var(--tw-outline-style);outline-width:1px}.grayscale{--tw-grayscale:grayscale(100%);filter:var(--tw-blur,)var(--tw-brightness,)var(--tw-contrast,)var(--tw-grayscale,)var(--tw-hue-rotate,)var(--tw-invert,)var(--tw-saturate,)var(--tw-sepia,)var(--tw-drop-shadow,)}.invert{--tw-invert:invert(100%);filter:var(--tw-blur,)var(--tw-brightness,)var(--tw-contrast,)var(--tw-grayscale,)var(--tw-hue-rotate,)var(--tw-invert,)var(--tw-saturate,)var(--tw-sepia,)var(--tw-drop-shadow,)}.filter{filter:var(--tw-blur,)var(--tw-brightness,)var(--tw-contrast,)var(--tw-grayscale,)var(--tw-hue-rotate,)var(--tw-invert,)var(--tw-saturate,)var(--tw-sepia,)var(--tw-drop-shadow,)}.backdrop-filter{-webkit-backdrop-filter:var(--tw-backdrop-blur,)var(--tw-backdrop-brightness,)var(--tw-backdrop-contrast,)var(--tw-backdrop-grayscale,)var(--tw-backdrop-hue-rotate,)var(--tw-backdrop-invert,)var(--tw-backdrop-opacity,)var(--tw-backdrop-saturate,)var(--tw-backdrop-sepia,);backdrop-filter:var(--tw-backdrop-blur,)var(--tw-backdrop-brightness,)var(--tw-backdrop-contrast,)var(--tw-backdrop-grayscale,)var(--tw-backdrop-hue-rotate,)var(--tw-backdrop-invert,)var(--tw-backdrop-opacity,)var(--tw-backdrop-saturate,)var(--tw-backdrop-sepia,)}.transition{transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to,opacity,box-shadow,transform,translate,scale,rotate,filter,-webkit-backdrop-filter,backdrop-filter,display,content-visibility,overlay,pointer-events;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration))}.select-all{-webkit-user-select:all;user-select:all}.scrollbar-thin{scrollbar-width:thin;scrollbar-color:var(--color-line)transparent}}@property --tw-rotate-x{syntax:"*";inherits:false}@property --tw-rotate-y{syntax:"*";inherits:false}@property --tw-rotate-z{syntax:"*";inherits:false}@property --tw-skew-x{syntax:"*";inherits:false}@property --tw-skew-y{syntax:"*";inherits:false}@property --tw-border-style{syntax:"*";inherits:false;initial-value:solid}@property --tw-font-weight{syntax:"*";inherits:false}@property --tw-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-shadow-color{syntax:"*";inherits:false}@property --tw-shadow-alpha{syntax:"<percentage>";inherits:false;initial-value:100%}@property --tw-inset-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-inset-shadow-color{syntax:"*";inherits:false}@property --tw-inset-shadow-alpha{syntax:"<percentage>";inherits:false;initial-value:100%}@property --tw-ring-color{syntax:"*";inherits:false}@property --tw-ring-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-inset-ring-color{syntax:"*";inherits:false}@property --tw-inset-ring-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-ring-inset{syntax:"*";inherits:false}@property --tw-ring-offset-width{syntax:"<length>";inherits:false;initial-value:0}@property --tw-ring-offset-color{syntax:"*";inherits:false;initial-value:#fff}@property --tw-ring-offset-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-outline-style{syntax:"*";inherits:false;initial-value:solid}@property --tw-blur{syntax:"*";inherits:false}@property --tw-brightness{syntax:"*";inherits:false}@property --tw-contrast{syntax:"*";inherits:false}@property --tw-grayscale{syntax:"*";inherits:false}@property --tw-hue-rotate{syntax:"*";inherits:false}@property --tw-invert{syntax:"*";inherits:false}@property --tw-opacity{syntax:"*";inherits:false}@property --tw-saturate{syntax:"*";inherits:false}@property --tw-sepia{syntax:"*";inherits:false}@property --tw-drop-shadow{syntax:"*";inherits:false}@property --tw-drop-shadow-color{syntax:"*";inherits:false}@property --tw-drop-shadow-alpha{syntax:"<percentage>";inherits:false;initial-value:100%}@property --tw-drop-shadow-size{syntax:"*";inherits:false}@property --tw-backdrop-blur{syntax:"*";inherits:false}@property --tw-backdrop-brightness{syntax:"*";inherits:false}@property --tw-backdrop-contrast{syntax:"*";inherits:false}@property --tw-backdrop-grayscale{syntax:"*";inherits:false}@property --tw-backdrop-hue-rotate{syntax:"*";inherits:false}@property --tw-backdrop-invert{syntax:"*";inherits:false}@property --tw-backdrop-opacity{syntax:"*";inherits:false}@property --tw-backdrop-saturate{syntax:"*";inherits:false}@property --tw-backdrop-sepia{syntax:"*";inherits:false}@property --tw-tracking{syntax:"*";inherits:false}@property --tw-duration{syntax:"*";inherits:false}@property --tw-leading{syntax:"*";inherits:false}@keyframes spin{to{transform:rotate(360deg)}}</style>
</head>
<body>

<div class="sidebar">
  <div class="sidebar-brand">
    <div class="sidebar-brand-mark" aria-hidden="true">T</div>
    <div>
      <h2 style="font-family:var(--font-heading);font-size:16px;font-weight:700;color:var(--color-text);line-height:1.2;">TRMD</h2>
      <span style="font-size:11px;color:var(--color-muted);font-weight:500;" data-i18n="app.subtitle">转存控制台</span>
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
    <button class="sidebar-nav-item" data-nav="channel-downloads">
      <svg viewBox="0 0 24 24" fill="none"><path d="M5 5h14v10H8l-3 3V5Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>
      <span data-i18n="nav.channelDownloads">频道下载</span>
    </button>
    <button class="sidebar-nav-item" data-nav="uploads">
      <svg viewBox="0 0 24 24" fill="none"><path d="M12 16V4M7 9l5-5 5 5M5 20h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      <span data-i18n="nav.uploads">本地上传</span>
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

    <div style="margin-top:18px;padding:0 3px;">
      <div style="display:flex;align-items:center;justify-content:space-between;font-size:12px;color:var(--color-muted);padding:2px 0;">
        <span data-i18n="side.failed">失败</span>
        <strong id="metric-failed" style="color:var(--color-text);">0</strong>
      </div>
    </div>
  </div>

  <div class="sidebar-footer">
    <button class="sidebar-nav-item" id="btn-logout" style="margin-bottom:4px;color:var(--color-muted);">
      <svg viewBox="0 0 24 24" fill="none" style="opacity:0.7;"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      <span data-i18n="nav.logout">退出登录</span>
    </button>
    <div class="sidebar-footer-info">
      <span class="sidebar-status-dot"></span>
      <span data-i18n="side.status">系统运行中</span>
    </div>
    <span class="sidebar-version">TRMD v0.3.0 · by Asheblog</span>
  </div>
</div>

<main class="main-content">

  <!-- Login container (Telegram auth flow) -->
  <div id="login-container" style="display:none;position:fixed;inset:0;background:var(--color-bg);z-index:1000;align-items:center;justify-content:center;flex-direction:column;gap:20px;">
    <div class="login-brand">
      <h1>TRMD</h1>
      <p>Telegram 账号登录</p>
    </div>
    <div class="login-card">
      <div class="login-error" id="login-error"></div>
      <div id="login-form-phone" class="login-step">
        <div style="font-size:12px;color:var(--color-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px;">步骤 1 / 3</div>
        <h2 style="font-size:var(--font-text-xl,20px);font-weight:700;margin:0 0 6px;color:var(--color-text);">输入电话号码</h2>
        <p style="font-size:13px;color:var(--color-muted);margin:0 0 20px;">请输入您的 Telegram 账号绑定的手机号</p>
        <div class="login-field">
          <label for="login-phone">电话号码</label>
          <input id="login-phone" type="tel" placeholder="+8615000000000" autocomplete="tel">
          <div style="font-size:12px;color:var(--color-muted);margin-top:4px;">需以「+地区号」开头，如中国 +86</div>
        </div>
        <div style="display:flex;justify-content:flex-end;">
          <button type="button" id="login-btn-phone" class="login-submit" style="width:auto;padding:0 24px;">
            <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            发送验证码
          </button>
        </div>
      </div>
      <div id="login-form-code" class="login-step" style="display:none">
        <div style="font-size:12px;color:var(--color-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px;">步骤 2 / 3</div>
        <h2 style="font-size:var(--font-text-xl,20px);font-weight:700;margin:0 0 6px;color:var(--color-text);">输入验证码</h2>
        <p style="font-size:13px;color:var(--color-muted);margin:0 0 20px;" id="login-code-desc">验证码已发送到您的设备</p>
        <div class="login-field">
          <label for="login-code">验证码</label>
          <input id="login-code" type="text" inputmode="numeric" maxlength="10" placeholder="输入验证码" autocomplete="one-time-code">
        </div>
        <div style="display:flex;gap:10px;justify-content:flex-end;">
          <button type="button" class="btn" id="login-btn-back">返回</button>
          <button type="button" id="login-btn-code" class="login-submit" style="width:auto;padding:0 24px;">
            <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            验证
          </button>
        </div>
      </div>
      <div id="login-form-password" class="login-step" style="display:none">
        <div style="font-size:12px;color:var(--color-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px;">步骤 2.5 / 3</div>
        <h2 style="font-size:var(--font-text-xl,20px);font-weight:700;margin:0 0 6px;color:var(--color-text);">两步验证密码</h2>
        <p style="font-size:13px;color:var(--color-muted);margin:0 0 20px;" id="login-password-hint">该账号已设置两步验证</p>
        <div class="login-field">
          <label for="login-password">密码</label>
          <input id="login-password" type="password" placeholder="输入两步验证密码" autocomplete="current-password">
          <div style="font-size:12px;color:var(--color-muted);margin-top:4px;" id="login-password-hint-text"></div>
        </div>
        <div style="display:flex;gap:10px;justify-content:flex-end;">
          <button type="button" class="btn" id="login-btn-back-pwd">取消</button>
          <button type="button" id="login-btn-password" class="login-submit" style="width:auto;padding:0 24px;">
            <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            验证
          </button>
        </div>
      </div>
      <div id="login-form-recovery" class="login-step" style="display:none">
        <div style="font-size:12px;color:var(--color-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px;">密码恢复</div>
        <h2 style="font-size:var(--font-text-xl,20px);font-weight:700;margin:0 0 6px;color:var(--color-text);">输入恢复代码</h2>
        <p style="font-size:13px;color:var(--color-muted);margin:0 0 20px;" id="login-recovery-desc">恢复代码已发送</p>
        <div class="login-field">
          <label for="login-recovery">恢复代码</label>
          <input id="login-recovery" type="text" placeholder="输入恢复代码">
        </div>
        <div style="display:flex;gap:10px;justify-content:flex-end;">
          <button type="button" class="btn" id="login-btn-back-recovery">返回</button>
          <button type="button" id="login-btn-recovery" class="login-submit" style="width:auto;padding:0 24px;">
            <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            提交
          </button>
        </div>
      </div>
      <div id="login-form-signup" class="login-step" style="display:none">
        <div style="font-size:12px;color:var(--color-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px;">注册信息</div>
        <h2 style="font-size:var(--font-text-xl,20px);font-weight:700;margin:0 0 6px;color:var(--color-text);">完善个人信息</h2>
        <p style="font-size:13px;color:var(--color-muted);margin:0 0 20px;">首次登录，请输入您的名字</p>
        <div class="login-field">
          <label for="login-first-name">名字</label>
          <input id="login-first-name" type="text" placeholder="名字">
        </div>
        <div class="login-field">
          <label for="login-last-name">姓氏</label>
          <input id="login-last-name" type="text" placeholder="姓氏（可选）">
        </div>
        <div style="display:flex;justify-content:flex-end;">
          <button type="button" id="login-btn-signup" class="login-submit" style="width:auto;padding:0 24px;">
            <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            完成注册
          </button>
        </div>
      </div>
      <div id="login-form-done" class="login-step" style="display:none">
        <div style="text-align:center;padding:16px 0;">
          <svg viewBox="0 0 24 24" fill="none" width="48" height="48" style="color:var(--color-success);margin:0 auto 12px;"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M8 12l3 3 5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <p style="font-size:16px;font-weight:600;color:var(--color-success);margin:0;" id="login-user-name">登录成功</p>
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
      <select id="language-select" aria-label="语言" class="form-input" style="width:auto;height:36px;">
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
  <div style="display:grid;grid-template-columns:380px 1fr;gap:16px;">
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
          <label style="display:flex;align-items:center;gap:8px;font-size:13px;color:var(--color-muted);cursor:pointer;margin-bottom:12px;">
            <input type="checkbox" name="include_comment" style="width:16px;height:16px;">
            <span data-i18n="new.includeComment">包含评论区</span>
          </label>
          <p style="font-size:11px;color:var(--color-muted);line-height:1.5;margin-bottom:8px;" data-i18n="new.hint">
            单条消息链接可留空。频道不填 ID 会自动探测可访问范围。
          </p>
          <div id="transfer-notice" class="text-[12px] mt-2" style="display:none;"></div>
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
        <span style="font-size:12px;color:var(--color-muted);" id="last-sync" data-i18n="tasks.notSynced">尚未同步</span>
      </div>
      <div style="overflow:auto;flex:1;">
        <table class="data-table">
          <thead>
            <tr>
              <th style="width:60px;" data-i18n="tasks.id">ID</th>
              <th style="width:80px;" data-i18n="tasks.status">状态</th>
              <th style="width:180px;" data-i18n="tasks.source">来源</th>
              <th style="width:80px;" data-i18n="tasks.target">目标</th>
              <th style="width:160px;" data-i18n="tasks.progress">进度</th>
              <th style="width:90px;" data-i18n="tasks.actions">操作</th>
            </tr>
          </thead>
          <tbody id="tasks-tbody"></tbody>
        </table>
        <div id="tasks-empty" class="p-8 text-center text-muted text-[13px]" data-i18n="tasks.empty">还没有转存任务。</div>
      </div>
    </div>
  </div>

  <!-- Task Detail Panel -->
  <div class="panel" id="task-detail">
    <div class="p-8 text-center text-muted text-[13px]" data-i18n="items.selectTask">选择一个任务查看详情</div>
  </div>
</div>

<!-- ====== Watches View ====== -->
<div class="view" id="view-watches">
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
    <!-- Download Watch -->
    <div class="panel">
      <div class="panel-header">
        <div style="display:flex;align-items:center;gap:10px;">
          <div class="stat-card-icon green" style="width:34px;height:34px;">
            <svg viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M12 16V4M7 9l5-5 5 5M5 20h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </div>
          <div>
            <h3 data-i18n="watches.downloadTitle">监听下载</h3>
            <span class="text-[11px] text-muted" data-i18n="watches.downloadMeta">新消息自动下载</span>
          </div>
        </div>
      </div>
      <div class="panel-body">
        <form id="watch-download-form">
          <div class="form-group">
            <label class="form-label" data-i18n="watches.sources">来源频道（每行一个）</label>
            <textarea class="form-input" name="source_links" rows="3" placeholder="https://t.me/channel1&#10;https://t.me/channel2" required style="min-height:80px;"></textarea>
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
        <div style="display:flex;align-items:center;gap:10px;">
          <div class="stat-card-icon blue" style="width:34px;height:34px;">
            <svg viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </div>
          <div>
            <h3 data-i18n="watches.forwardTitle">监听转发</h3>
            <span class="text-[11px] text-muted" data-i18n="watches.forwardMeta">新消息自动转发</span>
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
          <label style="display:flex;align-items:center;gap:8px;font-size:13px;color:var(--color-muted);cursor:pointer;margin-bottom:12px;">
            <input type="checkbox" name="include_comment" style="width:16px;height:16px;">
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
    <div style="overflow:auto;">
      <table class="data-table">
        <thead>
          <tr>
            <th data-i18n="watches.type">类型</th>
            <th data-i18n="watches.source">来源频道</th>
            <th data-i18n="watches.target">目标频道</th>
            <th>状态</th>
            <th style="width:80px;">今日</th>
            <th style="width:80px;">操作</th>
          </tr>
        </thead>
        <tbody id="watches-tbody"></tbody>
      </table>
      <div id="watches-empty" class="p-8 text-center text-muted text-[13px]" data-i18n="watches.empty">还没有实时监听。</div>
    </div>
  </div>
</div>

<!-- Watch Edit Overlay -->
<div class="watch-overlay" id="watch-edit-overlay">
  <div class="watch-dialog">
    <h3 style="font-size:16px;font-weight:600;display:flex;align-items:center;gap:8px;">
      <svg viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      <span data-i18n="watches.edit">编辑监听</span>
    </h3>
    <form id="watch-edit-form">
      <input type="hidden" name="id" id="edit-watch-id">
      <div class="form-group">
        <label class="form-label" data-i18n="watches.target">目标频道</label>
        <input class="form-input" name="target_link" id="edit-watch-target" type="text" required>
      </div>
      <label style="display:flex;align-items:center;gap:8px;font-size:13px;color:var(--color-muted);cursor:pointer;margin-bottom:12px;">
        <input type="checkbox" name="include_comment" id="edit-watch-comment" style="width:16px;height:16px;">
        <span data-i18n="watches.includeComment">包含评论区</span>
      </label>
      <div style="display:flex;gap:8px;justify-content:flex-end;">
        <button type="button" class="btn" onclick="closeEditWatchModal()" data-i18n="action.cancel">取消</button>
        <button type="submit" class="btn btn-primary" data-i18n="action.save">保存</button>
      </div>
    </form>
  </div>
</div>

<!-- ====== Channel Downloads View ====== -->
<div class="view" id="view-channel-downloads">
  <div class="panel" style="max-width:640px;">
    <div class="panel-header">
      <h3 data-i18n="channel.title">频道下载</h3>
    </div>
    <div class="panel-body">
      <form id="channel-download-form">
        <div class="form-group">
          <label class="form-label" data-i18n="channel.link">频道链接</label>
          <input class="form-input" name="chat_link" type="text" placeholder="https://t.me/channel" required>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label" data-i18n="channel.startDate">起始时间</label>
            <input class="form-input" name="start_date" type="datetime-local">
          </div>
          <div class="form-group">
            <label class="form-label" data-i18n="channel.endDate">结束时间</label>
            <input class="form-input" name="end_date" type="datetime-local">
          </div>
        </div>
        <div class="form-group">
          <label class="form-label" data-i18n="channel.keywords">关键词</label>
          <input class="form-input" name="keywords" type="text" data-i18n-placeholder="channel.keywordsPlaceholder" placeholder="逗号分隔，可留空">
        </div>
        <fieldset style="border:1px solid var(--color-line);border-radius:6px;padding:10px 14px;margin-bottom:14px;">
          <legend style="font-size:12px;font-weight:600;color:var(--color-muted);" data-i18n="channel.types">下载类型</legend>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 10px;">
            <label class="flex items-center gap-2 text-[13px] text-text cursor-pointer"><input type="checkbox" name="download_type" value="video" checked style="width:16px;height:16px;">video</label>
            <label class="flex items-center gap-2 text-[13px] text-text cursor-pointer"><input type="checkbox" name="download_type" value="photo" checked style="width:16px;height:16px;">photo</label>
            <label class="flex items-center gap-2 text-[13px] text-text cursor-pointer"><input type="checkbox" name="download_type" value="audio" checked style="width:16px;height:16px;">audio</label>
            <label class="flex items-center gap-2 text-[13px] text-text cursor-pointer"><input type="checkbox" name="download_type" value="voice" checked style="width:16px;height:16px;">voice</label>
            <label class="flex items-center gap-2 text-[13px] text-text cursor-pointer"><input type="checkbox" name="download_type" value="animation" checked style="width:16px;height:16px;">animation</label>
            <label class="flex items-center gap-2 text-[13px] text-text cursor-pointer"><input type="checkbox" name="download_type" value="document" checked style="width:16px;height:16px;">document</label>
            <label class="flex items-center gap-2 text-[13px] text-text cursor-pointer"><input type="checkbox" name="download_type" value="video_note" checked style="width:16px;height:16px;">video_note</label>
          </div>
        </fieldset>
        <label style="display:flex;align-items:center;gap:8px;font-size:13px;color:var(--color-muted);cursor:pointer;margin-bottom:12px;">
          <input type="checkbox" name="include_comment" style="width:16px;height:16px;">
          <span data-i18n="channel.includeComment">包含评论区</span>
        </label>
        <button type="submit" class="form-submit">
          <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M12 16V4M7 9l5-5 5 5M5 20h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span data-i18n="channel.create">创建频道下载</span>
        </button>
      </form>
    </div>
  </div>
</div>

<!-- ====== Uploads View ====== -->
<div class="view" id="view-uploads">
  <div class="panel" style="max-width:640px;">
    <div class="panel-header">
      <h3 data-i18n="uploads.title">本地上传</h3>
    </div>
    <div class="panel-body">
      <form id="upload-form">
        <div class="form-group">
          <label class="form-label" data-i18n="uploads.path">本地路径</label>
          <input class="form-input" name="path" type="text" placeholder="/data/files/movie.mp4" required>
        </div>
        <div class="form-group">
          <label class="form-label" data-i18n="uploads.target">目标频道</label>
          <input class="form-input" name="target_link" type="text" placeholder="https://t.me/target" required>
        </div>
        <label style="display:flex;align-items:center;gap:8px;font-size:13px;color:var(--color-muted);cursor:pointer;margin-bottom:12px;">
          <input type="checkbox" name="recursive" style="width:16px;height:16px;">
          <span data-i18n="uploads.recursive">递归上传文件夹</span>
        </label>
        <button type="submit" class="form-submit">
          <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M12 16V4M7 9l5-5 5 5M5 20h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span data-i18n="uploads.create">创建上传</span>
        </button>
      </form>
    </div>
  </div>
</div>

<!-- ====== Statistics View ====== -->
<div class="view" id="view-statistics">
  <div class="panel">
    <div class="panel-header">
      <h3 data-i18n="statistics.title">统计与导出</h3>
    </div>
    <div style="overflow:auto;">
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
    </div>
    <div style="overflow:auto;">
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
      <div id="records-empty" class="p-8 text-center text-muted text-[13px]" data-i18n="records.empty">还没有下载成功记录。</div>
    </div>
  </div>
</div>

<!-- ====== Media View ====== -->
<div class="view" id="view-media">
  <div class="panel">
    <div class="panel-header">
      <h3 data-i18n="media.title">媒体管理</h3>
      <button class="btn btn-primary btn-sm" id="media-scan-btn">
        <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M20 12a8 8 0 1 1-2.34-5.66M20 4v5h-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <span data-i18n="media.scan">扫描可清理文件</span>
      </button>
    </div>
    <div class="panel-body">
      <div id="media-result" style="display:none;">
        <div id="media-summary" class="flex gap-5 flex-wrap p-4 bg-surface-alt rounded-lg mb-4"></div>

        <div id="media-items-section" class="mb-4" style="display:none;">
          <h4 class="text-sm font-semibold mb-2" data-i18n="media.transferItems">转存任务文件</h4>
          <div class="overflow-x-auto rounded-lg border border-line">
            <table class="data-table" style="min-width:600px;">
              <thead><tr>
                <th style="width:40px;"><input type="checkbox" id="media-select-all-items"></th>
                <th data-i18n="media.file">文件</th>
                <th data-i18n="media.size" class="text-right">大小</th>
                <th data-i18n="media.status" class="text-center">状态</th>
                <th data-i18n="media.source">来源</th>
              </tr></thead>
              <tbody id="media-items-tbody"></tbody>
            </table>
          </div>
        </div>

        <div id="media-orphans-section" class="mb-4" style="display:none;">
          <h4 class="text-sm font-semibold mb-2" data-i18n="media.orphanFiles">遗留文件</h4>
          <div class="overflow-x-auto rounded-lg border border-line">
            <table class="data-table" style="min-width:600px;">
              <thead><tr>
                <th style="width:40px;"><input type="checkbox" id="media-select-all-orphans"></th>
                <th data-i18n="media.path">路径</th>
                <th data-i18n="media.size" class="text-right">大小</th>
                <th data-i18n="media.mtime">最后修改</th>
              </tr></thead>
              <tbody id="media-orphans-tbody"></tbody>
            </table>
          </div>
        </div>

        <div class="flex items-center gap-3 pt-3 border-t border-line">
          <button class="btn btn-danger btn-sm" id="media-cleanup-btn" data-i18n="media.cleanup">清理选中文件</button>
        </div>
      </div>

      <div id="media-logs-section" style="display:none;">
        <h4 class="text-sm font-semibold mb-2 mt-4" data-i18n="media.cleanupHistory">清理历史</h4>
        <div class="overflow-x-auto rounded-lg border border-line">
          <table class="data-table">
            <thead><tr>
              <th data-i18n="media.file">文件</th>
              <th data-i18n="media.size" class="text-right">大小</th>
              <th data-i18n="media.reason">原因</th>
              <th data-i18n="media.time">时间</th>
            </tr></thead>
            <tbody id="media-logs-tbody"></tbody>
          </table>
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
      <span class="text-[12px] text-muted" data-i18n="settings.safeNote">敏感字段只显示是否已配置</span>
    </div>
    <div class="panel-body" id="settings-body" style="max-width:900px;">

      <!-- Paths -->
      <div style="border:1px solid var(--color-line);border-radius:8px;padding:16px;margin-bottom:14px;">
        <h4 class="text-sm font-semibold mb-3" data-i18n="settings.paths">路径与任务</h4>
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
      <div style="border:1px solid var(--color-line);border-radius:8px;padding:16px;margin-bottom:14px;">
        <h4 class="text-sm font-semibold mb-3" data-i18n="settings.behavior">行为</h4>
        <div class="form-row">
          <label class="flex items-center gap-2 text-[13px] text-text cursor-pointer">
            <input type="checkbox" name="global.notice" style="width:16px;height:16px;">
            <span data-i18n="settings.notice">机器人通知</span>
          </label>
          <label class="flex items-center gap-2 text-[13px] text-text cursor-pointer">
            <input type="checkbox" name="user.is_shutdown" style="width:16px;height:16px;">
            <span data-i18n="settings.shutdown">退出后关机</span>
          </label>
          <label class="flex items-center gap-2 text-[13px] text-text cursor-pointer">
            <input type="checkbox" name="global.upload.download_upload" style="width:16px;height:16px;">
            <span data-i18n="settings.downloadUpload">受限转发时下载后上传</span>
          </label>
          <label class="flex items-center gap-2 text-[13px] text-text cursor-pointer">
            <input type="checkbox" name="global.upload.delete" style="width:16px;height:16px;">
            <span data-i18n="settings.uploadDelete">上传完成删除本地文件</span>
          </label>
        </div>
        <div class="form-group mt-3">
          <label class="form-label" data-i18n="settings.pendingLimit">下载后上传队列</label>
          <input class="form-input" name="global.upload.pending_limit" type="number" min="1" max="5">
        </div>
      </div>

      <!-- PikPak Archive -->
      <div style="border:1px solid var(--color-line);border-radius:8px;padding:16px;margin-bottom:14px;">
        <h4 class="text-sm font-semibold mb-3" data-i18n="settings.pikpakArchive">PikPak 归档</h4>
        <label class="flex items-center gap-2 text-[13px] text-text cursor-pointer mb-3">
          <input type="checkbox" name="global.target_profiles.pikpak.archive.enable" style="width:16px;height:16px;">
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
      <div style="border:1px solid var(--color-line);border-radius:8px;padding:16px;margin-bottom:14px;">
        <h4 class="text-sm font-semibold mb-3" data-i18n="settings.sensitive">账号与代理</h4>
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
      <div style="border:1px solid var(--color-line);border-radius:8px;padding:16px;margin-bottom:14px;">
        <h4 class="text-sm font-semibold mb-3" data-i18n="settings.downloadTypes">下载类型</h4>
        <div class="grid grid-cols-2 gap-2" id="download-type-grid"></div>
      </div>

      <!-- Forward Types -->
      <div style="border:1px solid var(--color-line);border-radius:8px;padding:16px;margin-bottom:14px;">
        <h4 class="text-sm font-semibold mb-3" data-i18n="settings.forwardTypes">转发类型</h4>
        <div class="grid grid-cols-2 gap-2" id="forward-type-grid"></div>
      </div>

      <!-- Message Filter -->
      <div style="border:1px solid var(--color-line);border-radius:8px;padding:16px;margin-bottom:14px;">
        <h4 class="text-sm font-semibold mb-3" data-i18n="settings.messageFilter">消息过滤</h4>
        <label class="flex items-center gap-2 text-[13px] text-text cursor-pointer mb-3">
          <input type="checkbox" name="global.message_filter.enabled" style="width:16px;height:16px;">
          <span data-i18n="settings.enabled">启用消息过滤</span>
        </label>
        <div class="mb-3">
          <span class="form-label" data-i18n="settings.mediaTypes">媒体类型</span>
          <div class="grid grid-cols-2 gap-2 mt-1" id="filter-media-grid"></div>
        </div>
        <div class="mb-3">
          <label class="flex items-center gap-2 text-[13px] text-text cursor-pointer mb-2">
            <input type="checkbox" name="global.message_filter.date_range.enabled" style="width:16px;height:16px;">
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
          <label class="flex items-center gap-2 text-[13px] text-text cursor-pointer mb-2">
            <input type="checkbox" name="global.message_filter.keywords.enabled" style="width:16px;height:16px;">
            <span data-i18n="settings.keywords">关键词过滤</span>
          </label>
          <div class="form-group">
            <label class="form-label" data-i18n="settings.keywordList">关键词列表（逗号分隔）</label>
            <input class="form-input" name="global.message_filter.keywords.words" data-i18n-placeholder="settings.keywordPlaceholder" placeholder="广告,推广,赞助">
          </div>
        </div>
      </div>

      <!-- Export Tables -->
      <div style="border:1px solid var(--color-line);border-radius:8px;padding:16px;margin-bottom:14px;">
        <h4 class="text-sm font-semibold mb-3" data-i18n="settings.exports">导出表格</h4>
        <div class="grid grid-cols-2 gap-2">
          <label class="flex items-center gap-2 text-[13px] text-text cursor-pointer">
            <input type="checkbox" name="global.export_table.link" style="width:16px;height:16px;">
            <span data-i18n="settings.exportLink">链接统计表</span>
          </label>
          <label class="flex items-center gap-2 text-[13px] text-text cursor-pointer">
            <input type="checkbox" name="global.export_table.count" style="width:16px;height:16px;">
            <span data-i18n="settings.exportCount">计数统计表</span>
          </label>
          <label class="flex items-center gap-2 text-[13px] text-text cursor-pointer">
            <input type="checkbox" name="global.export_table.upload" style="width:16px;height:16px;">
            <span data-i18n="settings.exportUpload">上传统计表</span>
          </label>
        </div>
      </div>

      <div class="flex items-center justify-between gap-3 sticky bottom-0 bg-white py-3 border-t border-line mt-2">
        <div id="settings-notice" class="text-[12px]" style="display:none;"></div>
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
    'nav.channelDownloads': '频道下载',
    'nav.uploads': '本地上传',
    'nav.statistics': '统计面板',
    'nav.settings': '系统设置',
    'nav.records': '下载记录',
    'nav.media': '媒体管理',
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
    'watches.noEvents': '暂无转发记录',
    'watches.eventForwarded': '转发成功',
    'watches.eventSkipped': '已过滤',
    'watches.eventLoading': '加载中…',
    'watches.loadMore': '加载更多',
    'watches.targetRequired': '目标频道为必填项。',
    'watches.sourceRequired': '来源频道为必填项。',
    'action.cancel': '取消',
    'action.save': '保存',
    'channel.title': '频道下载',
    'channel.link': '频道链接',
    'channel.startDate': '起始时间',
    'channel.endDate': '结束时间',
    'channel.types': '下载类型',
    'channel.keywords': '关键词',
    'channel.keywordsPlaceholder': '逗号分隔，可留空',
    'channel.includeComment': '包含评论区',
    'channel.create': '创建频道下载',
    'channel.accepted': '频道下载任务已创建。',
    'uploads.title': '本地上传',
    'uploads.path': '本地路径',
    'uploads.target': '目标频道',
    'uploads.recursive': '递归上传文件夹',
    'uploads.create': '创建上传',
    'uploads.accepted': '上传任务已创建。',
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
    'settings.forwardTypes': '转发类型',
    'settings.messageFilter': '消息过滤',
    'settings.mediaTypes': '媒体类型',
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
    'nav.channelDownloads': 'Channel DL',
    'nav.uploads': 'Uploads',
    'nav.statistics': 'Statistics',
    'nav.settings': 'Settings',
    'nav.records': 'Records',
    'nav.media': 'Media Mgmt',
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
    'watches.noEvents': 'No forwarding events yet.',
    'watches.eventForwarded': 'Forwarded',
    'watches.eventSkipped': 'Filtered',
    'watches.eventLoading': 'Loading…',
    'watches.loadMore': 'Load more',
    'watches.targetRequired': 'Target link is required.',
    'watches.sourceRequired': 'Source link is required.',
    'action.cancel': 'Cancel',
    'action.save': 'Save',
    'channel.title': 'Channel Download',
    'channel.link': 'Channel link',
    'channel.startDate': 'Start time',
    'channel.endDate': 'End time',
    'channel.types': 'Download types',
    'channel.keywords': 'Keywords',
    'channel.keywordsPlaceholder': 'Comma-separated, optional',
    'channel.includeComment': 'Include comments',
    'channel.create': 'Create download',
    'channel.accepted': 'Channel download task created.',
    'uploads.title': 'Local Upload',
    'uploads.path': 'Local path',
    'uploads.target': 'Target channel',
    'uploads.recursive': 'Upload folder recursively',
    'uploads.create': 'Create upload',
    'uploads.accepted': 'Upload task created.',
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
    'settings.forwardTypes': 'Forward Types',
    'settings.messageFilter': 'Message Filter',
    'settings.mediaTypes': 'Media types',
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
  itemPages: {},
  itemData: {},
  eventData: {},
  taskPollTimer: null,
  watchEventCache: {},
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

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

function applyLanguage() {
  $$('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    if (key) el.textContent = t(key);
  });
  document.title = t('app.title') || 'TRMD · 转存控制台';
}

function applyLanguageAndRefresh() {
  applyLanguage();
  if (state.activeView === 'transfers') renderTasks();
  if (state.activeView === 'watches') renderWatches();
  if (state.activeView === 'settings') renderSettings();
}

async function fetchJson(url) {
  const resp = await fetch(url);
  if (resp.status === 401) { throw { error_code: 'auth_required' }; }
  if (!resp.ok) {
    let data;
    try { data = await resp.json(); } catch(e) { data = {}; }
    throw data;
  }
  return resp.json();
}

async function postJson(url, payload) {
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (resp.status === 401) { throw { error_code: 'auth_required' }; }
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
  if (resp.status === 401) { throw { error_code: 'auth_required' }; }
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
    if (e.error_code === 'auth_required') checkAuthStatus();
  }
}

function updateStats() {
  const stats = { total: state.tasks.length, running: 0, success: 0, failed: 0, failedItems: 0 };
  state.tasks.forEach(t => {
    if (t.status === 'running') stats.running++;
    if (t.status === 'success') stats.success++;
    if (t.status === 'failure') stats.failed++;
    if (t.failed_count) stats.failedItems += (t.failed_count || 0);
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
    const progressPct = task.total_items > 0 ? Math.round((task.completed_items / task.total_items) * 100) : 0;
    return '<tr data-task-id="' + task.id + '" class="' + (isSelected ? 'selected' : '') + '">' +
      '<td style="font-weight:600;color:var(--color-primary);">#' + task.id + '</td>' +
      '<td>' + statusBadge(task.status) + '</td>' +
      '<td class="max-w-[160px] overflow-hidden text-ellipsis whitespace-nowrap text-[12px]" title="' + esc(task.source_link || '') + '">' + esc(task.source_link || '-') + '</td>' +
      '<td class="text-[12px]">' + esc(task.target_profile || task.target_link || '-') + '</td>' +
      '<td>' +
        (task.total_items > 0 ? (
          '<div class="flex items-center gap-2">' +
          '<span class="text-[12px] font-semibold">' + progressPct + '%</span>' +
          '<div style="flex:1;min-width:60px;">' +
          '<div class="progress-bar"><div class="progress-fill" style="width:' + progressPct + '%"></div></div>' +
          '<span class="text-[10px] text-muted">' + task.completed_items + '/' + task.total_items + '</span>' +
          '</div></div>'
        ) : '<span class="text-muted text-[11px]">-</span>') +
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
  if (task.status === 'running') {
    actions += '<button class="btn btn-sm" data-task-action="pause" data-task-id="' + task.id + '" title="' + t('tasks.pause') + '">⏸</button>';
  }
  if (task.status === 'paused') {
    actions += '<button class="btn btn-sm btn-primary" data-task-action="resume" data-task-id="' + task.id + '" title="' + t('tasks.resume') + '">▶</button>';
  }
  if (task.status === 'failure' && task.failed_count > 0) {
    actions += '<button class="btn btn-sm btn-danger" data-task-action="retry" data-task-id="' + task.id + '" title="' + t('tasks.retryFailed') + '">↻</button>';
  }
  if (task.status === 'success' || task.status === 'failure' || task.status === 'paused') {
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
      $('#task-detail').innerHTML = '<div class="p-8 text-center text-muted text-[13px]">' + t('items.selectTask') + '</div>';
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
async function loadTaskDetail(taskId) {
  const container = $('#task-detail');
  container.innerHTML = '<div class="p-8 text-center"><div class="spinner" style="margin:0 auto;"></div></div>';

  try {
    const data = await fetchJson('/api/tasks/' + taskId + '/summary');
    state.itemData[taskId] = data;
    state.eventData[taskId] = data.events || [];
    state.itemPages = { running: 1, success: 1, skipped: 1, failure: 1 };
    state.activeItemStatus = 'running';
    renderTaskDetail(taskId, data);
  } catch(e) {
    container.innerHTML = '<div class="p-8 text-center text-muted text-[13px]">加载失败</div>';
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
      '<button class="panel-tab" data-item-tab="failure">' + t('items.tab.failure') + ' (' + (summary.failure || 0) + ')</button>' +
    '</div>' +
    '</div>' +
    '<div id="task-items-body" style="overflow:auto;max-height:300px;"></div>' +
    '<div style="display:flex;align-items:center;justify-content:space-between;padding:8px 18px 14px;gap:12px;flex-wrap:wrap;" id="task-items-pagination"></div>';

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

async function loadTaskItems(taskId, status) {
  const page = state.itemPages[status] || 1;
  const body = $('#task-items-body');
  const pagEl = $('#task-items-pagination');
  body.innerHTML = '<div class="p-8 text-center"><div class="spinner" style="margin:0 auto;"></div></div>';

  try {
    const data = await fetchJson('/api/tasks/' + taskId + '?items_limit=50&items_offset=' + ((page - 1) * 50));
    const items = (data.items || []).filter(i => i.status === status);
    state.itemData[taskId] = data;

    if (!items.length) {
      body.innerHTML = '<div class="p-8 text-center text-muted text-[13px]">' + t('items.empty.' + status) + '</div>';
    } else {
      body.innerHTML = '<table class="data-table"><thead><tr>' +
        '<th>文件</th><th>大小</th><th>来源</th><th>目标</th><th>状态</th>' +
        '</tr></thead><tbody>' +
        items.map(item => '<tr>' +
          '<td class="text-[12px]">' + esc(item.file_name || item.local_path || '-') + '</td>' +
          '<td class="text-[12px]">' + fmtSize(item.file_size) + '</td>' +
          '<td class="text-[12px]">' + esc(item.source_link || '-') + '</td>' +
          '<td class="text-[12px]">' + esc(item.target_path || '-') + '</td>' +
          '<td>' + statusBadge(item.status) + '</td>' +
          '</tr>').join('') +
        '</tbody></table>';
    }

    const totalItems = state.itemData[taskId] ? Object.values(state.itemData[taskId].summary || {}).reduce((a, b) => a + (b || 0), 0) : 0;
    const totalPages = Math.max(1, Math.ceil(totalItems / 50));
    pagEl.innerHTML =
      '<span class="text-[12px] text-muted">第 ' + page + ' / ' + totalPages + ' 页</span>' +
      '<div class="flex gap-2">' +
        '<button class="btn btn-sm" ' + (page <= 1 ? 'disabled' : '') + ' id="items-prev-page">' + t('items.page.previous') + '</button>' +
        '<button class="btn btn-sm" ' + (page >= totalPages ? 'disabled' : '') + ' id="items-next-page">' + t('items.page.next') + '</button>' +
      '</div>';

    const prevBtn = $('#items-prev-page');
    const nextBtn = $('#items-next-page');
    if (prevBtn) prevBtn.addEventListener('click', () => {
      state.itemPages[state.activeItemStatus] = Math.max(1, page - 1);
      loadTaskItems(taskId, state.activeItemStatus);
    });
    if (nextBtn) nextBtn.addEventListener('click', () => {
      state.itemPages[state.activeItemStatus] = page + 1;
      loadTaskItems(taskId, state.activeItemStatus);
    });
  } catch(e) {
    body.innerHTML = '<div class="p-8 text-center text-muted text-[13px]">加载失败</div>';
  }
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
  notice.className = 'text-[12px] text-muted mt-2';
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
    notice.className = 'text-[12px] text-success mt-2';
    notice.textContent = t('form.createSuccess');
    await loadTasks();
  } catch(err) {
    notice.className = 'text-[12px] text-danger mt-2';
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

function startPolling() {
  if (state.taskPollTimer) return;
  const fast = 3000, slow = 15000;
  let interval = fast, lastPoll = 0;

  async function poll() {
    if (document.hidden) { state.taskPollTimer = setTimeout(poll, interval); return; }
    const now = Date.now();
    if (now - lastPoll < interval - 500) { state.taskPollTimer = setTimeout(poll, interval); return; }
    lastPoll = now;
    try { await loadTasks(); } catch(e) {}
    interval = hasActiveTasks() ? fast : slow;
    state.taskPollTimer = setTimeout(poll, interval);
  }
  poll();
}

document.addEventListener('visibilitychange', () => {
  if (!document.hidden && state.taskPollTimer) {
    clearTimeout(state.taskPollTimer);
    state.taskPollTimer = null;
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
    if (resp.status === 401) return;
    const state = await resp.json();
    if (!state || !state.step) return;
    switch (state.step) {
      case 'pending': hideLogin(); return;
      case 'done': case 'none':
        hideLogin();
        loadTasks();
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
});

/* ====== Logout ====== */
$('#btn-logout').addEventListener('click', async () => {
  await fetch('/api/auth/logout', { method: 'POST' });
  window.location.reload();
});

/* ====== Records ====== */
async function loadRecords() {
  const tbody = $('#records-tbody');
  const empty = $('#records-empty');
  try {
    const data = await fetchJson('/api/download-records');
    const records = data.records || [];
    if (!records.length) {
      tbody.innerHTML = '';
      empty.style.display = '';
      return;
    }
    empty.style.display = 'none';
    tbody.innerHTML = records.map(r => '<tr>' +
      '<td class="text-[12px] font-mono text-muted">' + esc(String(r.chat_id || '-')) + '</td>' +
      '<td class="text-[12px] font-mono text-muted">' + esc(String(r.message_id || '-')) + '</td>' +
      '<td class="text-[12px] max-w-[200px] overflow-hidden text-ellipsis whitespace-nowrap">' + esc(r.file_path || r.file_name || '-') + '</td>' +
      '<td class="text-[12px]">' + fmtSize(r.file_size) + '</td>' +
      '<td class="text-[12px] text-muted">' + fmtTime(r.updated_at) + '</td>' +
      '</tr>').join('');
  } catch(e) {}
}

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
    return '<tr>' +
      '<td><span class="badge ' + typeCls + '">' + typeLabel + '</span></td>' +
      '<td class="text-[12px] max-w-[180px] overflow-hidden text-ellipsis whitespace-nowrap font-mono text-muted">' + esc(w.source_link || '-') + '</td>' +
      '<td class="text-[12px]">' + esc(w.target_link || '本地') + '</td>' +
      '<td><span class="badge ' + statusCls + '">' + statusLabel + '</span></td>' +
      '<td class="text-[12px] font-semibold">' + (w.event_count || 0) + '</td>' +
      '<td><div class="flex gap-1">' +
        (w.type === 'forward' ? '<button class="btn btn-sm" data-edit-watch="' + esc(w.id) + '">✎</button>' : '') +
        '<button class="btn btn-sm btn-danger" data-delete-watch="' + esc(w.id) + '">✕</button>' +
      '</div></td>' +
      '</tr>';
  }).join('');
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
});

function openEditWatchModal(watchId) {
  const watch = (state.watches || []).find(w => w.id === watchId);
  if (!watch) return;
  $('#edit-watch-id').value = watch.id;
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

$('#watch-edit-form')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const fd = new FormData(this);
  const watchId = fd.get('id');
  try {
    await fetch('/api/watches/' + encodeURIComponent(watchId), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
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

/* ====== Channel Download ====== */
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
    alert(t('channel.accepted'));
    this.reset();
  } catch(err) {
    alert(translateApiError(err, 'form.createFailed'));
  }
});

/* ====== Upload ====== */
$('#upload-form')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const fd = new FormData(this);
  try {
    await postJson('/api/uploads', {
      path: fd.get('path'),
      target_link: fd.get('target_link'),
      recursive: Boolean(fd.get('recursive')),
    });
    alert(t('uploads.accepted'));
    this.reset();
  } catch(err) {
    alert(translateApiError(err, 'form.createFailed'));
  }
});

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
  renderCheckboxGrid('download-type-grid', 'download_type', sg.download_type || []);
  /* forward types */
  renderCheckboxGrid('forward-type-grid', 'forward_type', sg.forward_type || []);
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

function renderCheckboxGrid(containerId, typeKey, selected) {
  const types = ['video','photo','audio','voice','animation','document','video_note'];
  const container = document.getElementById(containerId);
  if (!container) return;
  const sel = Array.isArray(selected) ? selected : [];
  container.innerHTML = types.map(t =>
    '<label class="flex items-center gap-2 text-[13px] text-text cursor-pointer">' +
      '<input type="checkbox" name="global.' + typeKey + '" value="' + t + '" class="w-4 h-4"' + (sel.includes(t) ? ' checked' : '') + '>' +
      '<span>' + t + '</span>' +
    '</label>'
  ).join('');
}

function renderMessageFilter(mf) {
  setCheckboxVal('global.message_filter.enabled', mf.enabled);
  /* media types */
  renderCheckboxGrid('filter-media-grid', 'message_filter.media_types', mf.media_types || []);
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
  const formData = new FormData();
  /* collect all named inputs */
  $$('#settings-body input, #settings-body select').forEach(el => {
    if (!el.name) return;
    if (el.type === 'checkbox' && !el.closest('[data-checkbox-group]')) {
      formData.append(el.name, el.checked ? '1' : '');
    } else if (el.type === 'checkbox') {
      /* grouped checkboxes handled below */
    } else {
      formData.append(el.name, el.value);
    }
  });

  /* collect grouped checkboxes */
  const payload = buildSettingsPayload();

  try {
    await patchJson('/api/settings', payload);
    notice.className = 'text-[12px] text-success mt-2';
    notice.textContent = t('settings.saved');
    notice.style.display = '';
    setTimeout(() => { notice.style.display = 'none'; }, 3000);
  } catch(err) {
    notice.className = 'text-[12px] text-danger mt-2';
    notice.textContent = translateApiError(err, 'form.requestFailed');
    notice.style.display = '';
  }
});

function buildSettingsPayload() {
  /* rebuild full settings structure from form */
  const payload = { user: {}, global: {} };
  const raw = state.settings || {};

  /* user settings */
  $$('[name^="user."]').forEach(el => {
    if (!el.name) return;
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
    const parts = el.name.split('.');
    if (parts[0] !== 'global') return;
    if (el.type === 'checkbox') {
      setNested(payload, parts, el.checked);
    } else if (el.value !== '') {
      setNested(payload, parts, el.value);
    }
  });

  /* download types */
  const downloadTypes = Array.from($$('input[name="global.download_type"]:checked')).map(cb => cb.value);
  if (downloadTypes.length) setNested(payload, ['global', 'download_type'], downloadTypes);

  /* forward types */
  const forwardTypes = Array.from($$('input[name="global.forward_type"]:checked')).map(cb => cb.value);
  if (forwardTypes.length) setNested(payload, ['global', 'forward_type'], forwardTypes);

  /* filter media types */
  const filterMedia = Array.from($$('input[name="global.message_filter.media_types"]:checked')).map(cb => cb.value);
  if (filterMedia.length) setNested(payload, ['global', 'message_filter', 'media_types'], filterMedia);

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

async function loadMedia() {
  try {
    const data = await fetchJson('/api/media/scan');
    mediaScanResult = data;
    renderMediaResult(data);
    loadCleanupLogs();
  } catch(e) {}
}

function renderMediaResult(data) {
  const container = $('#media-result');
  if (!data) { container.style.display = 'none'; return; }
  container.style.display = '';

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
  if (items.length) {
    itemsSection.style.display = '';
    $('#media-items-tbody').innerHTML = items.map(item => '<tr>' +
      '<td><input type="checkbox" class="media-cb" data-type="item" data-id="' + item.item_id + '"></td>' +
      '<td class="text-[12px] max-w-[240px] overflow-hidden text-ellipsis whitespace-nowrap" title="' + esc(item.local_path || '') + '">' + esc(item.file_name || item.local_path || '-') + '</td>' +
      '<td class="text-[12px] text-right">' + fmtSize(item.file_size) + '</td>' +
      '<td class="text-center">' + statusBadge(item.status || '') + '</td>' +
      '<td class="text-[12px] max-w-[160px] overflow-hidden text-ellipsis whitespace-nowrap">' + esc(item.source_link || '-') + '</td>' +
      '</tr>').join('');
  } else {
    itemsSection.style.display = 'none';
  }

  /* orphans */
  const files = orph.files || [];
  const orphansSection = $('#media-orphans-section');
  if (files.length) {
    orphansSection.style.display = '';
    $('#media-orphans-tbody').innerHTML = files.map(f => '<tr>' +
      '<td><input type="checkbox" class="media-cb" data-type="orphan" data-path="' + esc(f.path) + '"></td>' +
      '<td class="text-[12px] max-w-[240px] overflow-hidden text-ellipsis whitespace-nowrap" title="' + esc(f.path) + '">' + esc(f.path) + '</td>' +
      '<td class="text-[12px] text-right">' + fmtSize(f.size) + '</td>' +
      '<td class="text-[12px] text-muted">' + fmtTimestamp(f.mtime) + '</td>' +
      '</tr>').join('');
  } else {
    orphansSection.style.display = 'none';
  }

  /* select-all */
  $('#media-select-all-items').onclick = function() {
    $$('#media-items-tbody .media-cb').forEach(cb => cb.checked = this.checked);
  };
  $('#media-select-all-orphans').onclick = function() {
    $$('#media-orphans-tbody .media-cb').forEach(cb => cb.checked = this.checked);
  };
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
    loadMedia();
  } catch(e) {
    alert(translateApiError(e, 'form.requestFailed'));
  }
}

async function loadCleanupLogs() {
  try {
    const data = await fetchJson('/api/media/cleanup-logs');
    const logs = (data && data.logs) || [];
    const section = $('#media-logs-section');
    if (logs.length) {
      section.style.display = '';
      $('#media-logs-tbody').innerHTML = logs.map(log => '<tr>' +
        '<td class="text-[12px] max-w-[240px] overflow-hidden text-ellipsis whitespace-nowrap">' + esc(log.file_path || '-') + '</td>' +
        '<td class="text-[12px] text-right">' + fmtSize(log.file_size) + '</td>' +
        '<td class="text-[12px]">' + esc(log.reason || '-') + '</td>' +
        '<td class="text-[12px] text-muted">' + fmtTime(log.created_at) + '</td>' +
        '</tr>').join('');
    } else {
      section.style.display = 'none';
    }
  } catch(e) {}
}

$('#media-scan-btn')?.addEventListener('click', loadMedia);
$('#media-cleanup-btn')?.addEventListener('click', doMediaCleanup);

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
<style>
  :root {
    color-scheme: light;
    --bg: #F0F4FF;
    --surface: #ffffff;
    --surface-muted: #f0f3f5;
    --text: #17201b;
    --muted: #5b6670;
    --line: #d8dee4;
    --accent: #2563EB;
    --accent-strong: #1D4ED8;
    --blue: #2563eb;
    --danger: #b42318;
    --warn: #a15c07;
    --ok: #127c52;
    --font-xs: 12px;
    --font-sm: 13px;
    --font-md: 15px;
    --font-lg: 16px;
    --font-xl: 20px;
    --safe-bottom: env(safe-area-inset-bottom, 0px);
    --tab-height: 56px;
    --topbar-height: 48px;
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: var(--font-md);
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    min-height: 100svh;
    -webkit-tap-highlight-color: transparent;
    user-select: none;
    padding-top: var(--topbar-height);
    padding-bottom: calc(var(--tab-height) + var(--safe-bottom));
  }
  button, input, select, textarea {
    font: inherit;
  }
  button {
    border: 0;
    border-radius: 8px;
    padding: 12px 16px;
    background: var(--accent);
    color: #fff;
    font-weight: 600;
    cursor: pointer;
    min-height: 44px;
    min-width: 44px;
    transition: opacity .15s;
  }
  button:active { opacity: .75; }
  button.secondary {
    background: var(--surface);
    border: 1px solid var(--line);
    color: var(--text);
  }
  button.danger {
    background: transparent;
    color: var(--danger);
    border: 1px solid var(--danger);
  }
  button.small {
    padding: 8px 12px;
    min-height: 36px;
    font-size: var(--font-sm);
  }
  input, select, textarea {
    width: 100%;
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 12px 14px;
    background: var(--surface);
    color: var(--text);
    min-height: 44px;
    font-size: 16px;
  }
  input:focus, select:focus, textarea:focus {
    border-color: var(--accent);
    outline: none;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, .12);
  }
  label {
    display: grid;
    gap: 6px;
    color: var(--muted);
    font-size: var(--font-sm);
  }

  /* ---- Top Bar ---- */
  .mob-topbar {
    position: fixed;
    top: 0; left: 0; right: 0;
    height: var(--topbar-height);
    background: var(--surface);
    border-bottom: 1px solid var(--line);
    display: flex;
    align-items: center;
    padding: 0 14px;
    gap: 10px;
    z-index: 100;
  }
  .mob-brand {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 700;
    font-size: var(--font-lg);
  }
  .mob-brand .mark {
    width: 28px; height: 28px;
    border-radius: 6px;
    background: var(--accent);
    display: grid;
    place-items: center;
    color: #fff;
  }
  .mob-topbar-actions {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .mob-topbar-actions select {
    width: auto;
    min-height: 0;
    padding: 4px 8px;
    font-size: var(--font-sm);
    border-radius: 6px;
  }

  /* ---- Bottom Tab Bar ---- */
  .mob-tabbar {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    height: calc(var(--tab-height) + var(--safe-bottom));
    padding-bottom: var(--safe-bottom);
    background: var(--surface);
    border-top: 1px solid var(--line);
    display: flex;
    justify-content: space-around;
    align-items: flex-start;
    padding-top: 6px;
    z-index: 100;
  }
  .mob-tab {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    font-size: 10px;
    color: var(--muted);
    min-width: 44px;
    cursor: pointer;
    padding: 4px 0;
    border: 0;
    background: transparent;
    border-radius: 0;
    min-height: auto;
    font-weight: 400;
  }
  .mob-tab.active {
    color: var(--accent);
    font-weight: 600;
  }
  .mob-tab svg {
    width: 22px;
    height: 22px;
  }

  /* ---- Content Area ---- */
  .mob-content {
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    animation: mobRise .3s ease both;
  }
  @keyframes mobRise {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .mob-view {
    display: none;
  }
  .mob-view.active {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  /* ---- Card List ---- */
  .mob-card {
    background: var(--surface);
    border-radius: 10px;
    padding: 14px;
    border: 1px solid var(--line);
    box-shadow: 0 1px 3px rgba(0,0,0,.03);
    border-left: 3px solid var(--line);
    transition: border-color .2s, transform .15s;
    cursor: pointer;
  }
  .mob-card:active { transform: scale(.985); }
  .mob-card.status-pending { border-left-color: #94a3b8; }
  .mob-card.status-running { border-left-color: var(--accent); }
  .mob-card.status-paused { border-left-color: #eab308; }
  .mob-card.status-success { border-left-color: var(--blue); }
  .mob-card.status-failure { border-left-color: var(--danger); }
  .mob-card.status-cancelled { border-left-color: #94a3b8; }
  .mob-card.status-skipped { border-left-color: #8b5cf6; }
  .mob-card__head {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
  }
  .mob-card__title {
    font-weight: 650;
    font-size: var(--font-md);
    word-break: break-all;
    line-height: 1.3;
  }
  .mob-card__badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: var(--font-xs);
    font-weight: 600;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .mob-card__badge.pending { background: #f1f5f9; color: #475569; }
  .mob-card__badge.running { background: #dcfce7; color: #166534; }
  .mob-card__badge.paused { background: #fef9c3; color: #a16207; }
  .mob-card__badge.completed { background: #dbeafe; color: #1e40af; }
  .mob-card__badge.failure { background: #fee2e2; color: #b91c1c; }
  .mob-card__badge.cancelled { background: #f1f5f9; color: #64748b; }
  .mob-card__row {
    display: flex;
    justify-content: space-between;
    padding: 3px 0;
    font-size: var(--font-sm);
  }
  .mob-card__row .label {
    color: var(--muted);
  }
  .mob-card__progress {
    margin: 6px 0;
    height: 6px;
    border-radius: 3px;
    background: var(--surface-muted);
    overflow: hidden;
  }
  .mob-card__progress-fill {
    height: 100%;
    background: var(--accent);
    border-radius: 3px;
    transition: width .3s;
  }
  .mob-card__actions {
    display: flex;
    gap: 6px;
    margin-top: 8px;
    flex-wrap: wrap;
  }
  .mob-watch-events {
    margin-top: 8px;
    border-top: 1px solid var(--line, #e0e0e0);
    padding-top: 8px;
    font-size: 12px;
  }
  .mob-watch-events .watch-event-item {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    padding: 3px 0;
    border-bottom: 1px solid var(--line, #e0e0e0);
  }
  .mob-watch-events .watch-event-item:last-child { border-bottom: 0; }

  /* ---- Collapse Panel ---- */
  .mob-collapse {
    border: 1px solid var(--line);
    border-radius: 10px;
    overflow: hidden;
    background: var(--surface);
  }
  .mob-collapse__head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px;
    cursor: pointer;
    font-weight: 600;
    user-select: none;
  }
  .mob-collapse__head:active { background: var(--surface-muted); }
  .mob-collapse__arrow {
    transition: transform .2s;
    color: var(--muted);
  }
  .mob-collapse.open .mob-collapse__arrow {
    transform: rotate(180deg);
  }
  .mob-collapse__body {
    display: none;
    padding: 0 14px 14px;
    flex-direction: column;
    gap: 10px;
  }
  .mob-collapse.open .mob-collapse__body {
    display: flex;
  }

  /* ---- Drawer ---- */
  .mob-drawer-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,.35);
    z-index: 200;
    display: none;
    align-items: flex-end;
  }
  .mob-drawer-overlay.open {
    display: flex;
  }
  .mob-drawer {
    width: 100%;
    background: var(--surface);
    border-radius: 16px 16px 0 0;
    padding: 8px 0 calc(24px + var(--safe-bottom));
    max-height: 70vh;
    overflow: auto;
    animation: mobSlideUp .25s ease;
  }
  @keyframes mobSlideUp {
    from { transform: translateY(100%); }
    to { transform: translateY(0); }
  }
  .mob-drawer__handle {
    width: 36px;
    height: 4px;
    background: var(--line);
    border-radius: 2px;
    margin: 8px auto 12px;
  }
  .mob-drawer__item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 20px;
    font-size: var(--font-md);
    cursor: pointer;
    border: 0;
    background: transparent;
    width: 100%;
    min-height: auto;
    border-radius: 0;
    color: var(--text);
    font-weight: 400;
  }
  .mob-drawer__item:active {
    background: var(--surface-muted);
  }
  .mob-drawer__item svg {
    width: 20px;
    height: 20px;
    color: var(--muted);
  }
  .mob-drawer__separator {
    height: 1px;
    background: var(--line);
    margin: 8px 20px;
  }
  .mob-drawer__item--logout {
    color: var(--muted);
  }
  .mob-drawer__item--logout svg {
    color: var(--danger);
    opacity: .72;
  }

  /* ---- FAB ---- */
  .mob-fab {
    position: fixed;
    bottom: calc(var(--tab-height) + var(--safe-bottom) + 16px);
    right: 16px;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: var(--accent);
    color: #fff;
    font-size: 24px;
    display: grid;
    place-items: center;
    box-shadow: 0 4px 16px rgba(37, 99, 235, .4);
    z-index: 90;
    cursor: pointer;
    transition: transform .2s, box-shadow .2s;
    min-height: auto;
    min-width: auto;
    padding: 0;
  }
  .mob-fab:active {
    transform: scale(.92);
    box-shadow: 0 2px 8px rgba(37, 99, 235, .3);
  }

  /* ---- FAB Menu ---- */
  .mob-fab-menu {
    position: fixed;
    bottom: calc(var(--tab-height) + var(--safe-bottom) + 72px);
    right: 16px;
    display: none;
    flex-direction: column;
    gap: 8px;
    z-index: 90;
  }
  .mob-fab-menu.open {
    display: flex;
  }
  .mob-fab-menu__item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 10px;
    font-size: var(--font-sm);
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(0,0,0,.08);
    cursor: pointer;
    white-space: nowrap;
    min-height: auto;
    color: var(--text);
  }
  .mob-fab-menu__item:active {
    background: var(--surface-muted);
  }

  /* ---- Bottom Sheet ---- */
  .mob-sheet-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,.35);
    z-index: 300;
    display: none;
    align-items: flex-end;
  }
  .mob-sheet-overlay.open {
    display: flex;
  }
  .mob-sheet {
    width: 100%;
    background: var(--surface);
    border-radius: 16px 16px 0 0;
    padding: 20px 16px max(24px, var(--safe-bottom));
    max-height: 85vh;
    overflow: auto;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  .mob-sheet__title {
    font-size: var(--font-lg);
    font-weight: 700;
    margin: 0;
  }

  /* ---- Toast ---- */
  .mob-toast {
    position: fixed;
    bottom: calc(var(--tab-height) + var(--safe-bottom) + 16px);
    left: 50%;
    transform: translateX(-50%);
    background: var(--text);
    color: #fff;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: var(--font-sm);
    z-index: 400;
    opacity: 0;
    pointer-events: none;
    transition: opacity .25s;
    white-space: nowrap;
  }
  .mob-toast.show {
    opacity: 1;
    pointer-events: auto;
  }

  /* ---- Task Detail Sheet ---- */
  .mob-sheet__task-header {
    background: var(--surface-muted);
    border-radius: 8px;
    padding: 12px;
  }
  .mob-sheet__task-header .task-title {
    font-weight: 650;
    font-size: var(--font-md);
    word-break: break-all;
    margin-bottom: 4px;
  }
  .mob-sheet__task-header .task-meta {
    font-size: var(--font-xs);
    color: var(--muted);
    margin-bottom: 6px;
  }
  .mob-sheet-tabs {
    display: flex;
    gap: 4px;
    overflow-x: auto;
    padding-bottom: 2px;
  }
  .mob-sheet-tab {
    padding: 6px 10px;
    border-radius: 6px;
    font-size: var(--font-xs);
    font-weight: 600;
    border: 1px solid var(--line);
    background: var(--surface);
    color: var(--muted);
    cursor: pointer;
    white-space: nowrap;
    min-height: auto;
    min-width: auto;
    transition: .15s;
  }
  .mob-sheet-tab.active {
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
  }
  .mob-sheet-tab .count { margin-left: 3px; opacity: .8; }
  .mob-item-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid var(--line);
    font-size: var(--font-sm);
    gap: 6px;
  }
  .mob-item-row:last-child { border-bottom: 0; }
  .mob-item-row__name {
    flex: 1;
    word-break: break-all;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .mob-event-row {
    padding: 6px 0;
    border-bottom: 1px solid var(--line);
    font-size: var(--font-xs);
  }
  .mob-event-row:last-child { border-bottom: 0; }
  .mob-event-row time { color: var(--muted); margin-right: 6px; }
  .mob-sheet-pagination {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 6px;
    font-size: var(--font-xs);
    color: var(--muted);
  }

  /* ---- Empty State ---- */
  .mob-empty {
    text-align: center;
    color: var(--muted);
    padding: 40px 20px;
    font-size: var(--font-sm);
  }

  /* ---- Section Header ---- */
  .mob-section-title {
    font-size: var(--font-xs);
    text-transform: uppercase;
    letter-spacing: .06em;
    color: var(--muted);
    padding: 4px 0;
  }
  .mob-media-scan-btn {
    margin: 8px 0; width: 100%;
  }
  .mob-media-result { margin-top: 12px; font-size: var(--font-sm); }

  /* ---- Check Group (fieldset) ---- */
  .mob-check-group {
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 10px 14px;
    margin: 0;
  }
  .mob-check-group legend {
    font-size: var(--font-sm);
    color: var(--muted);
    padding: 0 4px;
  }

  /* ---- Scrollable Table ---- */
  .mob-table-wrap {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    border: 1px solid var(--line);
    border-radius: 8px;
  }
  .mob-table-wrap table {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--font-sm);
  }
  .mob-table-wrap th,
  .mob-table-wrap td {
    padding: 8px 10px;
    text-align: left;
    border-bottom: 1px solid var(--line);
    white-space: nowrap;
  }
  .mob-table-wrap th {
    background: var(--surface-muted);
    font-weight: 600;
    position: sticky;
    top: 0;
  }

  .login-container {
    display: none;
    position: fixed;
    inset: 0;
    background: var(--bg);
    z-index: 1000;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 20px;
    padding: 16px;
  }
  .login-container.active { display: flex; }
  .login-card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 24px;
    max-width: 420px;
    width: 100%;
    box-shadow: var(--shadow);
  }
  .login-card__title {
    font-size: 18px;
    font-weight: 700;
    margin: 0 0 6px;
    color: var(--text);
  }
  .login-card__subtitle {
    font-size: var(--font-sm);
    color: var(--muted);
    margin: 0 0 20px;
  }
  .login-card__step {
    font-size: var(--font-xs);
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: .06em;
    margin-bottom: 8px;
  }
  .login-field {
    margin-bottom: 16px;
  }
  .login-field label {
    display: block;
    font-size: var(--font-sm);
    font-weight: 500;
    color: var(--text);
    margin-bottom: 6px;
  }
  .login-field input {
    width: 100%;
    height: 42px;
    border: 1px solid var(--line);
    border-radius: 6px;
    padding: 0 12px;
    font-size: var(--font-md);
    background: var(--surface);
    color: var(--text);
    transition: border-color .18s ease;
  }
  .login-field input:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 2px rgba(37, 99, 235, .12);
  }
  .login-field__hint {
    font-size: var(--font-xs);
    color: var(--muted);
    margin-top: 4px;
  }
  .login-error {
    font-size: var(--font-sm);
    color: var(--danger);
    background: #fff4f2;
    border: 1px solid #f3b5ad;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 16px;
    display: none;
  }
  .login-error.visible { display: block; }
  .login-actions {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
  }
  .login-actions button {
    min-width: 100px;
  }
  .login-success {
    text-align: center;
    padding: 16px 0;
  }
  .login-success svg {
    width: 48px;
    height: 48px;
    color: var(--ok);
    margin-bottom: 12px;
  }
  .login-success__text {
    font-size: 16px;
    font-weight: 600;
    color: var(--ok);
    margin: 0;
  }
  .login-brand {
    text-align: center;
    margin-bottom: 4px;
  }
  .login-brand h1 {
    font-size: 24px;
    font-weight: 800;
    margin: 0;
    color: var(--text);
    letter-spacing: -.02em;
  }
  .login-brand p {
    font-size: var(--font-sm);
    color: var(--muted);
    margin: 2px 0 0;
  }
</style>
</head>
<body>
<div class="mob-topbar">
  <div class="mob-brand">
    <div class="mark" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
    </div>
    <span>TRMD</span>
  </div>
  <div class="mob-topbar-actions">
    <select id="language-select" aria-label="语言">
      <option value="zh">中文</option>
      <option value="en">EN</option>
    </select>
    <button class="secondary small" type="button" id="refresh" aria-label="刷新">
      <svg viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M20 12a8 8 0 1 1-2.34-5.66M20 4v5h-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
    </button>
  </div>
</div>

<div class="login-container" id="login-container">
  <div class="login-brand">
    <h1>TRMD</h1>
    <p>Telegram 账号登录</p>
  </div>
  <div class="login-card">
    <div class="login-error" id="login-error"></div>
    <div id="login-form-phone" class="login-step">
      <div class="login-card__step">步骤 1 / 3</div>
      <h2 class="login-card__title">输入电话号码</h2>
      <p class="login-card__subtitle">请输入您的 Telegram 账号绑定的手机号</p>
      <div class="login-field">
        <label for="login-phone">电话号码</label>
        <input id="login-phone" type="tel" placeholder="+8615000000000" autocomplete="tel">
        <div class="login-field__hint">需以「+地区号」开头，如中国 +86</div>
      </div>
      <div class="login-actions">
        <button type="button" id="login-btn-phone" class="login-submit">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          发送验证码
        </button>
      </div>
    </div>
    <div id="login-form-code" class="login-step" style="display:none">
      <div class="login-card__step">步骤 2 / 3</div>
      <h2 class="login-card__title">输入验证码</h2>
      <p class="login-card__subtitle" id="login-code-desc">验证码已发送到您的设备</p>
      <div class="login-field">
        <label for="login-code">验证码</label>
        <input id="login-code" type="text" inputmode="numeric" maxlength="10" placeholder="输入验证码" autocomplete="one-time-code">
      </div>
      <div class="login-actions">
        <button type="button" class="secondary" id="login-btn-back">返回</button>
        <button type="button" id="login-btn-code" class="login-submit">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          验证
        </button>
      </div>
    </div>
    <div id="login-form-password" class="login-step" style="display:none">
      <div class="login-card__step">步骤 2.5 / 3</div>
      <h2 class="login-card__title">两步验证密码</h2>
      <p class="login-card__subtitle" id="login-password-hint">该账号已设置两步验证</p>
      <div class="login-field">
        <label for="login-password">密码</label>
        <input id="login-password" type="password" placeholder="输入两步验证密码" autocomplete="current-password">
        <div class="login-field__hint" id="login-password-hint-text"></div>
      </div>
      <div class="login-actions">
        <button type="button" class="secondary" id="login-btn-back-pwd">取消</button>
        <button type="button" id="login-btn-password" class="login-submit">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          验证
        </button>
      </div>
    </div>
    <div id="login-form-recovery" class="login-step" style="display:none">
      <div class="login-card__step">密码恢复</div>
      <h2 class="login-card__title">输入恢复代码</h2>
      <p class="login-card__subtitle" id="login-recovery-desc">恢复代码已发送</p>
      <div class="login-field">
        <label for="login-recovery">恢复代码</label>
        <input id="login-recovery" type="text" placeholder="输入恢复代码">
      </div>
      <div class="login-actions">
        <button type="button" class="secondary" id="login-btn-back-recovery">返回</button>
        <button type="button" id="login-btn-recovery" class="login-submit">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          提交
        </button>
      </div>
    </div>
    <div id="login-form-signup" class="login-step" style="display:none">
      <div class="login-card__step">注册信息</div>
      <h2 class="login-card__title">完善个人信息</h2>
      <p class="login-card__subtitle">首次登录，请输入您的名字</p>
      <div class="login-field">
        <label for="login-first-name">名字</label>
        <input id="login-first-name" type="text" placeholder="名字">
      </div>
      <div class="login-field">
        <label for="login-last-name">姓氏</label>
        <input id="login-last-name" type="text" placeholder="姓氏（可选）">
      </div>
      <div class="login-actions">
        <button type="button" id="login-btn-signup" class="login-submit">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          完成注册
        </button>
      </div>
    </div>
    <div id="login-form-done" class="login-step" style="display:none">
      <div class="login-success">
        <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M8 12l3 3 5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <p class="login-success__text" id="login-user-name">登录成功</p>
      </div>
    </div>
  </div>
</div>

<div class="mob-content" id="mob-content">
  <!-- 转存任务 -->
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
          <label style="flex-direction:row;align-items:center;gap:8px;">
            <input type="checkbox" name="include_comment" style="width:auto;min-height:auto;">
            <span data-i18n="new.includeComment">包含评论区</span>
          </label>
          <button type="submit" style="width:100%;" data-i18n="new.create">创建任务</button>
          <p class="mob-empty" id="mob-form-notice" style="display:none;"></p>
        </form>
      </div>
    </div>
    <div id="mob-tasks-list"></div>
  </div>

  <!-- 实时监听 -->
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
              <input type="text" name="source_link" placeholder="https://t.me/source" style="display:none;">
            </label>
          </div>
          <div id="mob-watch-target-group" style="display:none;">
            <label><span data-i18n="watches.target">目标频道</span>
              <input type="text" name="target_link" placeholder="https://t.me/...">
            </label>
          </div>
          <div id="mob-watch-comment-group" style="display:none;">
            <label style="flex-direction:row;align-items:center;gap:8px;">
              <input type="checkbox" name="include_comment" style="width:auto;min-height:auto;">
              <span data-i18n="watches.includeComment">包含评论区</span>
            </label>
          </div>
          <button type="submit" style="width:100%;" data-i18n="watches.createDownload">新增监听</button>
          <p class="mob-empty" id="mob-watch-notice" style="display:none;"></p>
        </form>
      </div>
    </div>
    <div id="mob-watches-list"></div>
  </div>

  <!-- 设置 -->
  <div class="mob-view" id="mob-view-settings">
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
    <button id="mob-save-settings" style="width:100%;margin-top:4px;" data-i18n="settings.save">保存设置</button>
    <p class="mob-empty" id="mob-settings-notice" style="display:none;"></p>
  </div>

  <!-- 频道下载 -->
  <div class="mob-view" id="mob-view-channel-downloads">
    <div class="mob-collapse" id="collapse-channel-form">
      <div class="mob-collapse__head" data-i18n="channel.title">频道下载 <span class="mob-collapse__arrow">&#9660;</span></div>
      <div class="mob-collapse__body">
        <form id="mob-channel-form">
          <label><span data-i18n="channel.link">频道链接</span>
            <input type="text" name="chat_link" placeholder="https://t.me/..." required>
          </label>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
            <label><span data-i18n="channel.startDate">起始时间</span>
              <input type="datetime-local" name="start_date">
            </label>
            <label><span data-i18n="channel.endDate">结束时间</span>
              <input type="datetime-local" name="end_date">
            </label>
          </div>
          <label><span data-i18n="channel.keywords">关键词</span>
            <input type="text" name="keywords" data-i18n-placeholder="channel.keywordsPlaceholder" placeholder="逗号分隔，可留空">
          </label>
          <fieldset class="mob-check-group">
            <legend data-i18n="channel.types">下载类型</legend>
            <div id="mob-channel-download-types" style="display:grid;grid-template-columns:1fr 1fr;gap:2px 10px;">
              <label style="flex-direction:row;align-items:center;gap:4px;font-size:var(--font-sm);"><input type="checkbox" name="download_type" value="video" checked style="width:auto;min-height:auto;">video</label>
              <label style="flex-direction:row;align-items:center;gap:4px;font-size:var(--font-sm);"><input type="checkbox" name="download_type" value="photo" checked style="width:auto;min-height:auto;">photo</label>
              <label style="flex-direction:row;align-items:center;gap:4px;font-size:var(--font-sm);"><input type="checkbox" name="download_type" value="audio" checked style="width:auto;min-height:auto;">audio</label>
              <label style="flex-direction:row;align-items:center;gap:4px;font-size:var(--font-sm);"><input type="checkbox" name="download_type" value="voice" checked style="width:auto;min-height:auto;">voice</label>
              <label style="flex-direction:row;align-items:center;gap:4px;font-size:var(--font-sm);"><input type="checkbox" name="download_type" value="animation" checked style="width:auto;min-height:auto;">animation</label>
              <label style="flex-direction:row;align-items:center;gap:4px;font-size:var(--font-sm);"><input type="checkbox" name="download_type" value="document" checked style="width:auto;min-height:auto;">document</label>
              <label style="flex-direction:row;align-items:center;gap:4px;font-size:var(--font-sm);"><input type="checkbox" name="download_type" value="video_note" checked style="width:auto;min-height:auto;">video_note</label>
            </div>
          </fieldset>
          <label style="flex-direction:row;align-items:center;gap:8px;">
            <input type="checkbox" name="include_comment" style="width:auto;min-height:auto;">
            <span data-i18n="channel.includeComment">包含评论区</span>
          </label>
          <button type="submit" style="width:100%;" data-i18n="channel.create">创建频道下载</button>
          <p class="mob-empty" id="mob-channel-notice" style="display:none;"></p>
        </form>
      </div>
    </div>
    <div id="mob-channel-downloads-list"></div>
  </div>

  <!-- 本地上传 -->
  <div class="mob-view" id="mob-view-uploads">
    <div class="mob-collapse" id="collapse-upload-form">
      <div class="mob-collapse__head" data-i18n="uploads.title">本地上传 <span class="mob-collapse__arrow">&#9660;</span></div>
      <div class="mob-collapse__body">
        <form id="mob-upload-form">
          <label><span data-i18n="uploads.path">本地路径</span>
            <input type="text" name="path" placeholder="/path/to/file" required>
          </label>
          <label><span data-i18n="uploads.target">目标频道</span>
            <input type="text" name="target_link" placeholder="https://t.me/..." required>
          </label>
          <label style="flex-direction:row;align-items:center;gap:8px;">
            <input type="checkbox" name="recursive" style="width:auto;min-height:auto;">
            <span data-i18n="uploads.recursive">递归上传文件夹</span>
          </label>
          <button type="submit" style="width:100%;" data-i18n="uploads.create">创建上传</button>
          <p class="mob-empty" id="mob-upload-notice" style="display:none;"></p>
        </form>
      </div>
    </div>
    <div id="mob-uploads-list"></div>
  </div>

  <!-- 统计 -->
  <div class="mob-view" id="mob-view-statistics">
    <div class="mob-section-title" data-i18n="statistics.table">表格</div>
    <div id="mob-statistics-list"></div>
  </div>

  <!-- 下载记录 -->
  <div class="mob-view" id="mob-view-records">
    <div class="mob-section-title" data-i18n="records.title">下载记录</div>
    <div id="mob-records-list"></div>
  </div>
  <div class="mob-view" id="mob-view-media">
    <div class="mob-section-title" data-i18n="media.title">媒体管理</div>
    <button id="mob-media-scan-btn" class="mob-media-scan-btn" data-i18n="media.scan">扫描可清理文件</button>
    <div id="mob-media-result"></div>
  </div>
</div>

<!-- FAB + Menu -->
<div class="mob-fab-menu" id="mob-fab-menu">
  <button class="mob-fab-menu__item" id="mob-fab-new-transfer">
    <svg viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M7 7h10M7 12h10M7 17h6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
    <span data-i18n="new.title">新建转存</span>
  </button>
  <button class="mob-fab-menu__item" id="mob-fab-new-watch">
    <svg viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M4 12s3-6 8-6 8 6 8 6-3 6-8 6-8-6-8-6Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>
    <span data-i18n="watches.title">新建监听</span>
  </button>
</div>
<button class="mob-fab" id="mob-fab" aria-label="新建">+</button>

<!-- Bottom Tab Bar -->
<div class="mob-tabbar" id="mob-tabbar">
  <button class="mob-tab active" data-mob-nav="transfers">
    <svg viewBox="0 0 24 24" fill="none"><path d="M7 7h10M7 12h10M7 17h6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
    <span data-i18n="nav.transfers">转存</span>
  </button>
  <button class="mob-tab" data-mob-nav="watches">
    <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/><path d="M4 12s3-6 8-6 8 6 8 6-3 6-8 6-8-6-8-6Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M12 9v3l2 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
    <span data-i18n="nav.watches">监听</span>
  </button>
  <button class="mob-tab" data-mob-nav="settings">
    <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="3.5" stroke="currentColor" stroke-width="2"/><path d="M19.4 15a1.8 1.8 0 0 0 .36 1.98l.04.04a2 2 0 0 1-2.82 2.82l-.04-.04A1.8 1.8 0 0 0 15 19.4M4.6 9a1.8 1.8 0 0 0-.36-1.98l-.04-.04a2 2 0 0 1 2.82-2.82l.04.04A1.8 1.8 0 0 0 9 4.6" stroke="currentColor" stroke-width="1.5"/></svg>
    <span data-i18n="nav.settings">设置</span>
  </button>
  <button class="mob-tab" data-mob-nav="more">
    <svg viewBox="0 0 24 24" fill="none"><circle cx="5" cy="12" r="1.5" fill="currentColor"/><circle cx="12" cy="12" r="1.5" fill="currentColor"/><circle cx="19" cy="12" r="1.5" fill="currentColor"/></svg>
    <span>更多</span>
  </button>
</div>

<!-- 更多 Drawer -->
<div class="mob-drawer-overlay" id="mob-drawer-overlay">
  <div class="mob-drawer" id="mob-drawer">
    <div class="mob-drawer__handle"></div>
    <button class="mob-drawer__item" data-mob-drawer-nav="channel-downloads">
      <svg viewBox="0 0 24 24" fill="none"><path d="M5 5h14v10H8l-3 3V5Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>
      <span data-i18n="nav.channelDownloads">频道下载</span>
    </button>
    <button class="mob-drawer__item" data-mob-drawer-nav="uploads">
      <svg viewBox="0 0 24 24" fill="none"><path d="M12 16V4M7 9l5-5 5 5M5 20h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      <span data-i18n="nav.uploads">本地上传</span>
    </button>
    <button class="mob-drawer__item" data-mob-drawer-nav="statistics">
      <svg viewBox="0 0 24 24" fill="none"><path d="M5 19V9M12 19V5M19 19v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M4 19h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      <span data-i18n="nav.statistics">统计</span>
    </button>
    <button class="mob-drawer__item" data-mob-drawer-nav="records">
      <svg viewBox="0 0 24 24" fill="none"><path d="M5 4h14v16H5z" stroke="currentColor" stroke-width="2"/><path d="M8 8h8M8 12h8M8 16h5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      <span data-i18n="nav.records">下载记录</span>
    </button>
    <div class="mob-drawer__separator"></div>
    <button type="button" class="mob-drawer__item mob-drawer__item--logout" id="mob-btn-logout">
      <svg viewBox="0 0 24 24" fill="none"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      <span data-i18n="nav.logout">退出登录</span>
    </button>
  </div>
</div>

<!-- Bottom Sheet Overlay (通用) -->
<div class="mob-sheet-overlay" id="mob-sheet-overlay">
  <div class="mob-sheet" id="mob-sheet"></div>
</div>

<!-- Toast -->
<div class="mob-toast" id="mob-toast"></div>
<script>
  const i18n = {
    zh: {
      'app.subtitle': '转存控制台',
      'app.title': 'TRMD 转存控制台',
      'nav.transfers': '转存任务',
      'nav.watches': '实时监听',
      'nav.channelDownloads': '频道下载',
      'nav.uploads': '本地上传',
      'nav.statistics': '统计',
      'nav.settings': '设置',
      'nav.records': '下载记录',
      'nav.logout': '退出登录',
      'nav.primary': '主导航',
'side.failed': '失败',
      'hero.title': 'PikPak 转存队列',
      'hero.body': '创建、监控和配置 Telegram 受限内容转存任务。状态、文件进度、失败事件和下载成功记录会持久化保存。',
      'action.refresh': '刷新',
      'language.label': '语言',
      'new.title': '新建转存',
      'new.profileNote': '目标配置',
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
      'watches.title': '当前实时监听',
      'watches.downloadTitle': '监听下载',
      'watches.downloadMeta': '新消息转存',
      'watches.forwardTitle': '监听转发',
      'watches.forwardMeta': '新消息转发',
      'watches.sources': '来源频道',
      'watches.sourcesHint': '每行一个 Telegram 频道链接。监听下载会处理新到达的视频和图片。',
      'watches.source': '来源频道',
      'watches.target': '目标频道',
      'watches.includeComment': '包含评论区',
      'watches.forwardHint': '同一来源不能同时存在监听下载和监听转发。',
      'watches.createDownload': '新增监听下载',
      'watches.createForward': '新增监听转发',
      'watches.type': '类型',
      'watches.empty': '还没有实时监听。',
      'watches.delete': '移除监听',
      'watches.download': '监听下载',
      'watches.forward': '监听转发',
      'watches.created': '实时监听已接收。',
      'watches.deleted': '实时监听已移除。',
      'watches.edit': '编辑',
      'watches.updated': '实时监听已更新。',
      'watches.events': '转发记录',
      'watches.noEvents': '暂无转发记录',
      'watches.eventForwarded': '转发成功',
      'watches.eventSkipped': '已过滤',
      'watches.eventLoading': '加载中…',
      'watches.loadMore': '加载更多',
      'watches.targetRequired': '目标频道为必填项。',
      'action.cancel': '取消',
      'action.save': '保存',
      'channel.title': '频道下载',
      'channel.meta': '筛选后创建下载',
      'channel.link': '频道链接',
      'channel.startDate': '起始时间',
      'channel.endDate': '结束时间',
      'channel.types': '下载类型',
      'channel.keywords': '关键词',
      'channel.keywordsPlaceholder': '逗号分隔，可留空',
      'channel.includeComment': '包含评论区',
      'channel.hint': '频道下载会检索匹配消息并创建下载任务，执行时间取决于频道历史消息数量。',
      'channel.create': '创建频道下载',
      'channel.accepted': '频道下载已接收。',
      'uploads.title': '本地上传',
      'uploads.meta': '服务器路径',
      'uploads.path': '本地路径',
      'uploads.target': '目标频道',
      'uploads.recursive': '递归上传文件夹',
      'uploads.serverPathHint': '路径位于运行 TRMD 的服务器或容器，不是当前浏览器所在电脑。关闭递归时，文件夹只上传第一层文件；开启递归时包含子文件夹。',
      'uploads.create': '创建上传',
      'uploads.accepted': '上传任务已接收。',
      'statistics.title': '统计与导出',
      'statistics.meta': '运行态数据',
      'statistics.table': '表格',
      'statistics.available': '可用',
      'statistics.rows': '数量',
      'statistics.yes': '是',
      'statistics.no': '否',
      'statistics.link': '链接统计表',
      'statistics.count': '计数统计表',
      'statistics.upload': '上传统计表',
      'statistics.exportLink': '导出链接统计表',
      'statistics.exportCount': '导出计数统计表',
      'statistics.exportUpload': '导出上传统计表',
      'statistics.exported': '统计表已导出到：{directory}',
      'tasks.title': '转存任务',
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
      'items.selectTask': '选择一个任务',
      'items.empty': '该任务还没有文件记录。',
      'items.tabsLabel': '文件状态分类',
      'items.tab.running': '进行中',
      'items.tab.success': '已完成',
      'items.tab.skipped': '跳过',
      'items.tab.failure': '失败',
      'items.empty.running': '当前没有进行中的文件。',
      'items.empty.success': '当前没有已完成的文件。',
      'items.empty.skipped': '当前没有跳过的文件。',
      'items.empty.failure': '当前没有失败的文件。',
      'items.retryFailed': '重试当前任务失败项',
      'items.page.previous': '上一页',
      'items.page.next': '下一页',
      'items.page.status': '第 {page} / {pages} 页',
      'items.page.range': '{start}-{end} / {total}',
      'items.download': '下载',
      'items.upload': '上传',
      'items.loadMore': '加载更多文件',
      'items.remaining': '条剩余',
      'events.title': '最近事件',
      'events.empty': '没有事件记录。',
      'events.loadMore': '加载更多事件',
      'events.remaining': '条剩余',
      'settings.title': '设置',
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
      'settings.secretNotConfigured': '未配置',
      'settings.downloadTypes': '下载类型',
      'settings.forwardTypes': '转发类型',
      'settings.messageFilter': '消息过滤',
      'settings.mediaTypes': '媒体类型',
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
      'records.title': '下载成功记录',
      'records.chat': '频道 ID',
      'records.message': '消息 ID',
      'records.file': '文件',
      'records.size': '大小',
      'records.updated': '更新时间',
      'records.empty': '还没有下载成功记录。',
      'form.createFailed': '创建任务失败。',
      'form.requestFailed': '请求失败。',
      'form.creatingTransfer': '正在分析来源消息范围，Telegram 限流时可能需要等待。请保持页面打开。',
      'form.creatingTransferShort': '正在分析',
      'form.createSuccess': '任务已创建并开始排队。可以关闭页面，也可以继续查看进度。',
      'error.auth_required': '需要登录。',
      'error.invalid_task_id': '任务 ID 无效。',
      'error.task_not_found': '找不到任务。',
      'error.not_found': '找不到请求的资源。',
      'error.source_link_required': '请填写来源链接。',
      'error.target_link_required': '请填写目标链接。',
      'error.range_ids_required': '起始 ID 和结束 ID 必须同时填写。',
      'error.range_end_before_start': '结束 ID 必须大于或等于起始 ID。',
      'error.range_source_must_be_chat_link': '范围转存的来源必须是频道链接，不能是单条消息链接。',
      'error.transfer_range_detection_unavailable': '当前运行模式无法自动探测消息范围。',
      'error.transfer_range_detection_failed': '自动探测消息范围失败。',
      'error.transfer_range_empty': '来源中没有可访问的消息。',
      'error.create_task_failed': '创建任务失败。',
      'error.update_settings_failed': '更新设置失败。',
      'error.watch_source_conflict': '同一来源不能同时存在监听下载和监听转发。',
      'error.watch_already_exists': '实时监听已存在。',
      'error.watch_source_required': '请填写监听来源。',
      'error.watch_target_required': '请填写监听目标。',
      'error.invalid_payload': '请求内容无效。',
      'error.invalid_watch_type': '实时监听类型无效。',
      'error.invalid_watch_source': '监听来源必须以 https://t.me/ 开头。',
      'error.invalid_watch_target': '监听目标必须以 https://t.me/ 开头。',
      'error.watch_operations_unavailable': '实时监听操作不可用。',
      'error.upload_path_not_found': '服务器或容器中找不到该路径。',
      'error.upload_path_required': '请填写上传路径。',
      'error.upload_target_required': '请填写上传目标。',
      'error.upload_recursive_requires_directory': '递归上传需要选择文件夹路径。',
      'error.invalid_upload_target': '上传目标必须是 Telegram 链接、me 或 self。',
      'error.upload_operations_unavailable': '上传操作不可用。',
      'error.invalid_table_type': '统计表类型无效。',
      'error.table_operations_unavailable': '统计表操作不可用。',
      'error.invalid_channel_link': '频道链接必须以 https://t.me/ 开头。',
      'error.channel_link_required': '请填写频道链接。',
      'error.channel_download_type_required': '请至少选择一种下载类型。',
      'error.invalid_channel_download_type': '频道下载类型无效。',
      'error.channel_download_operations_unavailable': '频道下载操作不可用。',
      'action.taskUpdated': '任务操作已提交。',
      'error.invalid_date_range': '时间范围格式无效。',
      'error.date_range_end_before_start': '结束时间必须大于或等于起始时间。',
      'event.level.info': '信息',
      'event.level.warning': '警告',
      'event.level.error': '错误',
      'event.fileReady': '文件已准备上传到目标：{name}',
      'event.sentToTarget': '已发送到目标：{name}',
      'event.uploadFailed': '上传失败：{reason}',
      'event.reusedDownload': '已复用下载成功记录：{name}',
      'event.directForward': '已直接发送到目标：{link}',
      'event.rangeAssigned': '范围转存已分配：{range}',
      'event.rangeAssignedWithFallback': '范围转存已分配：{range}，回退下载 {count} 条。',
      'event.singleAssigned': '单条消息转存已分配。',
      'event.singleAssignedWithFallback': '单条消息转存已分配，回退下载 {count} 条。',
      'status.pending': '等待',
      'status.running': '运行中',
      'status.paused': '已暂停',
      'status.success': '成功',
      'status.failure': '失败',
      'status.skipped': '跳过',
      'nav.media': '媒体管理',
      'media.title': '媒体管理',
      'media.meta': '扫描并清理磁盘上的残留媒体文件',
      'media.scan': '扫描可清理文件',
      'media.scanning': '正在扫描...',
      'media.totalFiles': '可清理文件',
      'media.totalSize': '总大小',
      'media.retentionDays': '保留天数',
      'media.transferItems': '转存任务文件',
      'media.orphanFiles': '遗留文件 (超过保留天数)',
      'media.file': '文件',
      'media.size': '大小',
      'media.status': '任务状态',
      'media.source': '来源',
      'media.path': '路径',
      'media.mtime': '最后修改',
      'media.cleanup': '清理选中文件',
      'media.cleaning': '清理中...',
      'media.selected': '已选',
      'media.files': '个文件',
      'media.noSelection': '请先选择要清理的文件。',
      'media.confirmCleanup': '确定要删除选中的文件吗？此操作不可撤销。',
      'media.cleanupDone': '清理完成：已删除 {count} 个文件 ({size})。',
      'media.cleanupHistory': '清理历史',
      'media.reason': '原因',
      'media.time': '时间',
      'media.filterByTask': '按任务筛选：',
      'media.allTasks': '全部任务'
    },
    en: {
      'app.subtitle': 'Transfer Console',
      'app.title': 'TRMD Transfer Console',
      'nav.transfers': 'Transfer tasks',
      'nav.watches': 'Live watches',
      'nav.channelDownloads': 'Channel downloads',
      'nav.uploads': 'Local uploads',
      'nav.statistics': 'Statistics',
      'nav.settings': 'Settings',
      'nav.records': 'Download records',
      'nav.logout': 'Log out',
      'nav.primary': 'Primary navigation',
'side.failed': 'Failed',
      'hero.title': 'PikPak transfer queue',
      'hero.body': 'Create, monitor, and configure Telegram restricted content transfer tasks. State, file progress, failure events, and download success records are persisted.',
      'action.refresh': 'Refresh',
      'language.label': 'Language',
      'new.title': 'New transfer',
      'new.profileNote': 'Target profile',
      'new.source': 'Source link',
      'new.target': 'Target',
      'new.targetProfile': 'Target profile',
      'profile.pikpak': 'PikPak document transfer',
      'profile.generic': 'Generic Telegram target',
      'new.startId': 'Start ID',
      'new.endId': 'End ID',
      'new.optional': 'Optional',
      'new.includeComment': 'Include discussion replies',
      'new.hint': 'Leave the range empty for a message link. For a channel or group link, empty IDs auto-detect the accessible range, or you can set start and end IDs manually.',
      'new.create': 'Create task',
      'watches.title': 'Current live watches',
      'watches.downloadTitle': 'Download watch',
      'watches.downloadMeta': 'Transfer new messages',
      'watches.forwardTitle': 'Forward watch',
      'watches.forwardMeta': 'Forward new messages',
      'watches.sources': 'Source channels',
      'watches.sourcesHint': 'One Telegram channel link per line. Download watches handle new video and photo messages.',
      'watches.source': 'Source channel',
      'watches.target': 'Target channel',
      'watches.includeComment': 'Include discussion replies',
      'watches.forwardHint': 'The same source cannot have a download watch and a forward watch at the same time.',
      'watches.createDownload': 'Add download watch',
      'watches.createForward': 'Add forward watch',
      'watches.type': 'Type',
      'watches.empty': 'No live watches yet.',
      'watches.delete': 'Remove watch',
      'watches.download': 'Download watch',
      'watches.forward': 'Forward watch',
      'watches.created': 'Live watch accepted.',
      'watches.deleted': 'Live watch removed.',
      'watches.edit': 'Edit',
      'watches.updated': 'Live watch updated.',
      'watches.events': 'Forwarding log',
      'watches.noEvents': 'No forwarding events yet.',
      'watches.eventForwarded': 'Forwarded',
      'watches.eventSkipped': 'Filtered',
      'watches.eventLoading': 'Loading…',
      'watches.loadMore': 'Load more',
      'watches.targetRequired': 'Target link is required.',
      'action.cancel': 'Cancel',
      'action.save': 'Save',
      'channel.title': 'Channel download',
      'channel.meta': 'Create downloads after filtering',
      'channel.link': 'Channel link',
      'channel.startDate': 'Start time',
      'channel.endDate': 'End time',
      'channel.types': 'Download types',
      'channel.keywords': 'Keywords',
      'channel.keywordsPlaceholder': 'Comma-separated, optional',
      'channel.includeComment': 'Include discussion replies',
      'channel.hint': 'Channel download scans matching messages and creates download tasks. Runtime depends on channel history size.',
      'channel.create': 'Create channel download',
      'channel.accepted': 'Channel download accepted.',
      'uploads.title': 'Local upload',
      'uploads.meta': 'Server path',
      'uploads.path': 'Local path',
      'uploads.target': 'Target channel',
      'uploads.recursive': 'Upload folder recursively',
      'uploads.serverPathHint': 'The path is on the server or container running TRMD, not on this browser device. With recursion off, a folder uploads only its top-level files; with recursion on, subfolders are included.',
      'uploads.create': 'Create upload',
      'uploads.accepted': 'Upload request accepted.',
      'statistics.title': 'Statistics and export',
      'statistics.meta': 'Runtime data',
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
      'statistics.exported': 'Table exported to: {directory}',
      'tasks.title': 'Transfer tasks',
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
      'items.title': 'File progress',
      'items.selectTask': 'Select a task',
      'items.empty': 'No file records for this task yet.',
      'items.tabsLabel': 'File status categories',
      'items.tab.running': 'Running',
      'items.tab.success': 'Completed',
      'items.tab.skipped': 'Skipped',
      'items.tab.failure': 'Failed',
      'items.empty.running': 'No running files in this task.',
      'items.empty.success': 'No completed files in this task.',
      'items.empty.skipped': 'No skipped files in this task.',
      'items.empty.failure': 'No failed files in this task.',
      'items.retryFailed': 'Retry failed items in this task',
      'items.page.previous': 'Previous',
      'items.page.next': 'Next',
      'items.page.status': 'Page {page} / {pages}',
      'items.page.range': '{start}-{end} / {total}',
      'items.download': 'Download',
      'items.upload': 'Upload',
      'items.loadMore': 'Load more files',
      'items.remaining': 'remaining',
      'events.title': 'Latest events',
      'events.empty': 'No events recorded.',
      'events.loadMore': 'Load more events',
      'events.remaining': 'remaining',
      'settings.title': 'Settings',
      'settings.safeNote': 'Sensitive fields only show configured state',
      'settings.paths': 'Paths and tasks',
      'settings.saveDirectory': 'Save directory',
      'settings.tempDirectory': 'Temp directory',
      'settings.sessionDirectory': 'Session directory',
      'settings.maxDownload': 'Max download tasks',
      'settings.maxUpload': 'Max upload tasks',
      'settings.retryDownload': 'Download retries',
      'settings.retryUpload': 'Upload retries',
      'settings.pikpakMaxFileSize': 'PikPak size limit (bytes)',
      'settings.pikpakArchive': 'PikPak archive',
      'settings.pikpakArchiveEnable': 'Archive PikPak by source channel',
      'settings.pikpakArchiveRemote': 'PikPak rclone remote',
      'settings.pikpakArchiveSource': 'PikPak source folder',
      'settings.pikpakArchiveRoot': 'PikPak archive root',
      'settings.pikpakArchivePoll': 'Ingest poll seconds',
      'settings.pikpakArchiveInterval': 'Poll interval seconds',
      'settings.pikpakArchiveWindow': 'Match window seconds',
      'settings.behavior': 'Behavior',
      'settings.notice': 'Bot notifications',
      'settings.shutdown': 'Shutdown after exit',
      'settings.downloadUpload': 'Download then upload restricted forwards',
      'settings.uploadDelete': 'Delete local file after upload',
      'settings.pendingLimit': 'Upload-after-download queue',
      'settings.sensitive': 'Account and proxy',
      'settings.proxyPassword': 'Proxy password',
      'settings.secretConfigured': 'Configured; enter a new value to replace',
      'settings.secretNotConfigured': 'Not configured',
      'settings.downloadTypes': 'Download types',
      'settings.forwardTypes': 'Forward types',
      'settings.messageFilter': 'Message filter',
      'settings.mediaTypes': 'Media types',
      'settings.dateRange': 'Date range',
      'settings.keywords': 'Keywords',
      'settings.enabled': 'Enabled',
      'settings.startDate': 'Start date',
      'settings.endDate': 'End date',
      'settings.keywordList': 'Keywords (comma separated)',
      'settings.keywordPlaceholder': 'Enter keywords, separated by commas',
      'settings.exports': 'Table exports',
      'settings.exportLink': 'Link table',
      'settings.exportCount': 'Count table',
      'settings.exportUpload': 'Upload table',
      'settings.save': 'Save settings',
      'settings.saved': 'Settings saved.',
      'records.title': 'Download success records',
      'records.chat': 'Channel ID',
      'records.message': 'Message ID',
      'records.file': 'File',
      'records.size': 'Size',
      'records.updated': 'Updated',
      'records.empty': 'No download success records yet.',
      'form.createFailed': 'Create task failed.',
      'form.requestFailed': 'Request failed.',
      'form.creatingTransfer': 'Analyzing the source message range. Telegram flood waits can take a while; keep this page open.',
      'form.creatingTransferShort': 'Analyzing',
      'form.createSuccess': 'Task created and queued. You can close this page or keep watching progress.',
      'error.auth_required': 'Authentication required.',
      'error.invalid_task_id': 'Invalid task ID.',
      'error.task_not_found': 'Task not found.',
      'error.not_found': 'Resource not found.',
      'error.source_link_required': 'Source link is required.',
      'error.target_link_required': 'Target link is required.',
      'error.range_ids_required': 'Start ID and End ID must be provided together.',
      'error.range_end_before_start': 'End ID must be greater than or equal to Start ID.',
      'error.range_source_must_be_chat_link': 'Range transfer source must be a chat link, not a message link.',
      'error.transfer_range_detection_unavailable': 'Automatic message range detection is unavailable in this runtime.',
      'error.transfer_range_detection_failed': 'Automatic message range detection failed.',
      'error.transfer_range_empty': 'No accessible messages were found for the source.',
      'error.create_task_failed': 'Create task failed.',
      'error.update_settings_failed': 'Update settings failed.',
      'error.watch_source_conflict': 'The same source cannot have a download watch and a forward watch at the same time.',
      'error.watch_already_exists': 'Live watch already exists.',
      'error.watch_source_required': 'Watch source is required.',
      'error.watch_target_required': 'Watch target is required.',
      'error.invalid_payload': 'Invalid request payload.',
      'error.invalid_watch_type': 'Invalid live watch type.',
      'error.invalid_watch_source': 'Watch source must start with https://t.me/.',
      'error.invalid_watch_target': 'Watch target must start with https://t.me/.',
      'error.watch_operations_unavailable': 'Live watch operations are unavailable.',
      'error.upload_path_not_found': 'Path not found on the server or container.',
      'error.upload_path_required': 'Upload path is required.',
      'error.upload_target_required': 'Upload target is required.',
      'error.upload_recursive_requires_directory': 'Recursive upload requires a folder path.',
      'error.invalid_upload_target': 'Upload target must be a Telegram link, me, or self.',
      'error.upload_operations_unavailable': 'Upload operations are unavailable.',
      'error.invalid_table_type': 'Invalid table type.',
      'error.table_operations_unavailable': 'Table operations are unavailable.',
      'error.invalid_channel_link': 'Channel link must start with https://t.me/.',
      'error.channel_link_required': 'Channel link is required.',
      'error.channel_download_type_required': 'Select at least one download type.',
      'error.invalid_channel_download_type': 'Invalid channel download type.',
      'error.channel_download_operations_unavailable': 'Channel download operations are unavailable.',
      'error.invalid_date_range': 'Invalid date range.',
      'error.date_range_end_before_start': 'End time must be greater than or equal to start time.',
      'action.taskUpdated': 'Task action submitted.',
      'event.level.info': 'info',
      'event.level.warning': 'warning',
      'event.level.error': 'error',
      'event.fileReady': 'File ready for target upload: {name}',
      'event.sentToTarget': 'Sent to target: {name}',
      'event.uploadFailed': 'Upload failed: {reason}',
      'event.reusedDownload': 'Reused download success record: {name}',
      'event.directForward': 'Directly sent to target: {link}',
      'event.rangeAssigned': 'Range transfer assigned: {range}',
      'event.rangeAssignedWithFallback': 'Range transfer assigned: {range}; fallback downloads: {count}.',
      'event.singleAssigned': 'Single-message transfer assigned.',
      'event.singleAssignedWithFallback': 'Single-message transfer assigned; fallback downloads: {count}.',
      'status.pending': 'pending',
      'status.running': 'running',
      'status.paused': 'paused',
      'status.success': 'success',
      'status.failure': 'failure',
      'status.skipped': 'skipped',
      'nav.media': 'Media',
      'media.title': 'Media Management',
      'media.meta': 'Scan and clean residual media files on disk',
      'media.scan': 'Scan for cleanable files',
      'media.scanning': 'Scanning...',
      'media.totalFiles': 'Cleanable files',
      'media.totalSize': 'Total size',
      'media.retentionDays': 'Retention days',
      'media.transferItems': 'Transfer task files',
      'media.orphanFiles': 'Orphan files (exceeding retention)',
      'media.file': 'File',
      'media.size': 'Size',
      'media.status': 'Task status',
      'media.source': 'Source',
      'media.path': 'Path',
      'media.mtime': 'Last modified',
      'media.cleanup': 'Clean selected',
      'media.cleaning': 'Cleaning...',
      'media.selected': 'Selected',
      'media.files': 'files',
      'media.noSelection': 'Select files to clean first.',
      'media.confirmCleanup': 'Are you sure you want to delete selected files? This cannot be undone.',
      'media.cleanupDone': 'Cleanup done: {count} files deleted ({size}).',
      'media.cleanupHistory': 'Cleanup history',
      'media.reason': 'Reason',
      'media.time': 'Time',
      'media.filterByTask': 'Filter by task:',
      'media.allTasks': 'All tasks'
    }
  };

  const state = {
    lang: localStorage.getItem('trmd-lang') || 'zh',
    selectedTaskId: null,
    settings: null,
    schema: null,
    tasks: [],
    items: [],
    events: [],
    records: [],
    watches: [],
    statistics: null,
    lastSync: null,
    activeItemStatus: 'running',
    itemPages: {
      running: 1,
      success: 1,
      skipped: 1,
      failure: 1
    },
    itemsTotal: 0,
    eventsTotal: 0,
    itemsOffset: 0,
    eventsOffset: 0,
    hasMoreItems: false,
    hasMoreEvents: false,
    taskPollTimer: null,
    loadingDetail: false
  };

  const $ = selector => document.querySelector(selector);
  const $$ = selector => Array.from(document.querySelectorAll(selector));
  const ITEMS_PAGE_SIZE = 10;
  const ITEM_STATUS_TABS = ['running', 'success', 'skipped', 'failure'];

  function t(key) {
    return (i18n[state.lang] && i18n[state.lang][key]) || i18n.zh[key] || key;
  }

  function interpolate(template, values) {
    return String(template).replace(/\{(\w+)}/g, (_, key) => values[key] ?? '');
  }

  function esc(value) {
    return String(value ?? '').replace(/[&<>"']/g, ch => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[ch]));
  }

  function pct(current, total) {
    current = Number(current || 0);
    total = Number(total || 0);
    return total > 0 ? Math.min(100, Math.round((current / total) * 100)) : 0;
  }

  function formatBytes(value) {
    value = Number(value || 0);
    const units = ['B', 'KiB', 'MiB', 'GiB'];
    let unit = 0;
    while (value >= 1024 && unit < units.length - 1) {
      value = value / 1024;
      unit += 1;
    }
    return `${value.toFixed(unit ? 1 : 0)} ${units[unit]}`;
  }

  function translateApiError(payload, fallbackKey = 'form.requestFailed') {
    if (payload && payload.error_code) {
      const key = `error.${payload.error_code}`;
      const message = t(key);
      return message === key ? (payload.error || t(fallbackKey)) : message;
    }
    return (payload && payload.error) || t(fallbackKey);
  }

  function showNotice(selector, message, ok = true) {
    const notice = $(selector);
    if (!notice) return;
    notice.textContent = message;
    notice.classList.toggle('ok', ok);
    notice.classList.add('is-visible');
  }

  function showFormMessage(message, ok = true) {
    const formNotice = $('#form-error');
    formNotice.textContent = message;
    formNotice.classList.toggle('ok', ok);
    formNotice.classList.add('is-visible');
  }

  async function withLoading(button, task) {
    const previous = button ? button.disabled : false;
    if (button) button.disabled = true;
    try {
      return await task();
    } finally {
      if (button) button.disabled = previous;
    }
  }

  async function fetchJson(path) {
    const res = await fetch(path);
    const data = await res.json();
    if (!res.ok) throw data;
    return data;
  }

  async function postJson(path, payload) {
    const res = await fetch(path, {
      method: 'POST',
      headers: {'content-type': 'application/json'},
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw data;
    return data;
  }

  function localizeEventMessage(event) {
    const message = String((event && event.message) || '');
    let match = message.match(/^File ready for target upload: (.+)$/);
    if (match) return interpolate(t('event.fileReady'), {name: match[1]});
    match = message.match(/^Sent to target: (.+)$/);
    if (match) return interpolate(t('event.sentToTarget'), {name: match[1]});
    match = message.match(/^Upload failed: (.+)$/);
    if (match) return interpolate(t('event.uploadFailed'), {reason: match[1]});
    match = message.match(/^Reused download success record: (.+)$/);
    if (match) return interpolate(t('event.reusedDownload'), {name: match[1]});
    match = message.match(/^Direct forward succeeded: (.+)$/);
    if (match) return interpolate(t('event.directForward'), {link: match[1]});
    match = message.match(/^Range transfer assigned: (.+)\. Fallback downloads: (\d+)\.$/);
    if (match) return interpolate(t('event.rangeAssignedWithFallback'), {range: match[1], count: match[2]});
    match = message.match(/^Range transfer assigned: (.+)\.$/);
    if (match) return interpolate(t('event.rangeAssigned'), {range: match[1]});
    match = message.match(/^Single-message transfer assigned\. Fallback downloads: (\d+)\.$/);
    if (match) return interpolate(t('event.singleAssignedWithFallback'), {count: match[1]});
    if (message === 'Single-message transfer assigned.') return t('event.singleAssigned');
    return message;
  }

  function localizeEventLevel(level) {
    const key = `event.level.${level}`;
    const translated = t(key);
    return translated === key ? level : translated;
  }

  function applyLanguage() {
    document.documentElement.lang = state.lang === 'zh' ? 'zh-CN' : 'en';
    document.title = t('app.title');
    $('#language-select').value = state.lang;
    $$('[data-i18n]').forEach(el => {
      el.textContent = t(el.dataset.i18n);
    });
    $$('[data-i18n-placeholder]').forEach(el => {
      el.placeholder = t(el.dataset.i18nPlaceholder);
    });
    $$('[data-i18n-aria-label]').forEach(el => {
      el.setAttribute('aria-label', t(el.dataset.i18nAriaLabel));
    });
    $$('[data-i18n-title]').forEach(el => {
      el.setAttribute('title', t(el.dataset.i18nTitle));
    });
  }

  function refreshVisibleDynamicText() {
    renderTasks();
    $('#selected-task').textContent = state.selectedTaskId ? `#${state.selectedTaskId}` : t('items.selectTask');
    renderItems(state.items);
    renderEvents(state.events);
    renderRecords();
    if (state.settings) fillSettingsForm();
  }

  function applyLanguageAndRefresh() {
    applyLanguage();
    refreshVisibleDynamicText();
  }

  async function handleLogout() {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
    } catch (_) { /* proceed regardless */ }
    window.location.href = '/';
  }

  function switchView(view) {
    $$('.view').forEach(el => el.classList.toggle('active', el.id === `view-${view}`));
    $$('[data-nav]').forEach(el => el.classList.toggle('active', el.dataset.nav === view));
    if (view === 'settings') loadSettings();
    if (view === 'records') loadRecords();
    if (view === 'watches') loadWatches();
    if (view === 'statistics') loadStatistics();
  }

  function badge(status) {
    return `<span class="badge ${esc(status)}">${esc(t(`status.${status}`))}</span>`;
  }

  function taskProgress(task) {
    const total = Number(task.total_items || 0);
    const done = Number(task.completed_items || 0);
    const failed = Number(task.failed_items || 0);
    const percent = total > 0 ? Math.round(((done + failed) / total) * 100) : 0;
    const progressLabel = `${percent}% · ${done}/${total}${failed ? ` · ${failed} ${t('side.failed')}` : ''}`;
    return `
      <div class="task-progress" aria-label="${esc(progressLabel)}">
        <div class="task-progress__head">
          <span class="task-progress__percent">${percent}%</span>
          <span class="task-progress__detail">
            ${done}/${total}${failed ? ` <span class="task-progress__failed">${failed} ${esc(t('side.failed'))}</span>` : ''}
          </span>
        </div>
        <div class="progress" title="${esc(progressLabel)}"><div style="width:${percent}%"></div></div>
      </div>
    `;
  }

  function renderTasks() {
    const tasks = state.tasks || [];
$('#metric-failed').textContent = tasks.filter(task => task.status === 'failure').length;
    if (state.lastSync) $('#last-sync').textContent = state.lastSync;
    $('#empty').style.display = tasks.length ? 'none' : 'block';
    $('#tasks').innerHTML = tasks.map(task => `
      <tr data-task-id="${task.id}">
        <td class="mono">#${task.id}</td>
        <td>${badge(task.status)}</td>
        <td class="mono">${esc(task.source_link)}</td>
        <td class="mono">${esc(task.target_link)}</td>
        <td>${taskProgress(task)}</td>
        <td>
           <div class="task-actions">
            ${task.status === 'running' || task.status === 'paused'
            ? `<button class="secondary icon-only" type="button" title="${esc(t(task.status === 'paused' ? 'tasks.resume' : 'tasks.pause'))}" aria-label="${esc(t(task.status === 'paused' ? 'tasks.resume' : 'tasks.pause'))}" onclick="${task.status === 'paused' ? `resumeTask(event, ${task.id})` : `pauseTask(event, ${task.id})`}">
              ${task.status === 'paused'
                ? '<svg viewBox="0 0 24 24" fill="none"><path d="M8 5v14l11-7L8 5Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>'
                : '<svg viewBox="0 0 24 24" fill="none"><path d="M8 5v14M16 5v14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'}
              <span class="sr-only">${esc(t(task.status === 'paused' ? 'tasks.resume' : 'tasks.pause'))}</span>
            </button>`
            : ''}
            <button class="secondary icon-only" type="button" title="${esc(t('tasks.retryFailed'))}" aria-label="${esc(t('tasks.retryFailed'))}" onclick="retryFailedTask(event, ${task.id})" ${Number(task.failed_items || 0) ? '' : 'disabled'}>
              <svg viewBox="0 0 24 24" fill="none"><path d="M20 12a8 8 0 1 1-2.34-5.66M20 4v5h-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 8v4l3 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
              <span class="sr-only">${esc(t('tasks.retryFailed'))}</span>
            </button>
            <button class="danger icon-only" type="button" title="${esc(t('tasks.delete'))}" aria-label="${esc(t('tasks.delete'))}" onclick="deleteTask(event, ${task.id})">
              <svg viewBox="0 0 24 24" fill="none"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 14h10l1-14M9 7V4h6v3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              <span class="sr-only" data-i18n="tasks.delete">${esc(t('tasks.delete'))}</span>
            </button>
          </div>
        </td>
      </tr>
    `).join('');
    $$('tr[data-task-id]').forEach(row => {
      row.addEventListener('click', () => loadTask(row.dataset.taskId));
    });
  }

  async function loadTasks() {
    const res = await fetch('/api/tasks');
    const data = await res.json();
    state.tasks = data.tasks || [];
    state.lastSync = new Date().toLocaleTimeString();
    renderTasks();
    if (!state.selectedTaskId && state.tasks[0]) {
      await loadTaskDetail(state.tasks[0].id, true);
    } else if (state.selectedTaskId) {
      await loadTaskSummary(state.selectedTaskId);
    } else {
      state.items = [];
      state.events = [];
      state.itemsTotal = 0;
      state.eventsTotal = 0;
      $('#selected-task').textContent = t('items.selectTask');
      renderItems();
      renderEvents();
    }
  }

  async function loadTaskSummary(id) {
    const taskId = Number(id);
    const res = await fetch(`/api/tasks/${taskId}/summary`);
    if (!res.ok) return;
    const data = await res.json();
    if (data && data.task) {
      state.selectedTaskId = taskId;
      state.itemsTotal = data.item_count || 0;
      state.eventsTotal = data.event_count || 0;
      updateTaskSummaryDisplay(data.task);
      if (data.recent_events && data.recent_events.length) {
        mergeRecentEvents(data.recent_events);
      }
    }
  }

  function updateTaskSummaryDisplay(task) {
    $('#selected-task').textContent = `#${task.id}`;
    renderEventCount();
  }

  async function loadTaskDetail(id, keepExistingItems) {
    const taskId = Number(id);
    if (state.selectedTaskId !== taskId) {
      resetItemPages();
      state.items = [];
      state.events = [];
      state.itemsOffset = 0;
      state.eventsOffset = 0;
      state.hasMoreItems = false;
      state.hasMoreEvents = false;
    }
    state.selectedTaskId = taskId;
    state.loadingDetail = true;
    try {
      const res = await fetch(`/api/tasks/${taskId}?items_limit=200&items_offset=0&events_limit=100&events_offset=0`);
      if (!res.ok) {
        state.selectedTaskId = null;
        state.items = [];
        state.events = [];
        $('#selected-task').textContent = t('items.selectTask');
        renderItems();
        renderEvents();
        return;
      }
      const data = await res.json();
      $('#selected-task').textContent = `#${taskId}`;
      state.items = data.items || [];
      state.events = data.events || [];
      state.itemsTotal = data.item_count || 0;
      state.eventsTotal = data.event_count || 0;
      state.itemsOffset = data.items_offset || 0;
      state.eventsOffset = data.events_offset || 0;
      state.hasMoreItems = data.has_more_items || false;
      state.hasMoreEvents = data.has_more_events || false;
      renderItems();
      renderEvents();
    } finally {
      state.loadingDetail = false;
    }
  }

  async function loadMoreItems() {
    if (state.loadingDetail) return;
    const taskId = state.selectedTaskId;
    if (!taskId) return;
    const offset = state.itemsOffset + 200;
    state.loadingDetail = true;
    try {
      const res = await fetch(`/api/tasks/${taskId}?items_limit=200&items_offset=${offset}&events_limit=0&events_offset=0`);
      if (!res.ok) return;
      const data = await res.json();
      state.items = state.items.concat(data.items || []);
      state.itemsTotal = data.item_count || state.itemsTotal;
      state.itemsOffset = offset;
      state.hasMoreItems = data.has_more_items || false;
      renderItems();
    } finally {
      state.loadingDetail = false;
    }
  }

  async function loadMoreEvents() {
    if (state.loadingDetail) return;
    const taskId = state.selectedTaskId;
    if (!taskId) return;
    const offset = state.eventsOffset + 100;
    state.loadingDetail = true;
    try {
      const res = await fetch(`/api/tasks/${taskId}?items_limit=0&items_offset=0&events_limit=100&events_offset=${offset}`);
      if (!res.ok) return;
      const data = await res.json();
      state.events = state.events.concat(data.events || []);
      state.eventsTotal = data.event_count || state.eventsTotal;
      state.eventsOffset = offset;
      state.hasMoreEvents = data.has_more_events || false;
      renderEvents();
    } finally {
      state.loadingDetail = false;
    }
  }

  // 保留 loadTask 作为点击任务时的入口
  async function loadTask(id) {
    await loadTaskDetail(id, false);
  }

  function progressLine(label, current, total) {
    const percent = pct(current, total);
    return `<div><div>${esc(label)} ${percent}%</div><div class="progress"><div style="width:${percent}%"></div></div><div class="mono">${formatBytes(current)} / ${formatBytes(total)}</div></div>`;
  }

  function itemStatusGroup(item) {
    const status = String((item && item.status) || 'pending');
    if (status === 'success' || status === 'skipped' || status === 'failure') return status;
    if (['pending', 'running'].includes(status)) return 'running';
    return 'running';
  }

  function categorizedItems(items) {
    const groups = {
      running: [],
      success: [],
      skipped: [],
      failure: []
    };
    (items || []).forEach(item => {
      groups[itemStatusGroup(item)].push(item);
    });
    return groups;
  }

  function itemPageState(total) {
    const pages = Math.max(1, Math.ceil(total / ITEMS_PAGE_SIZE));
    const current = Math.min(Math.max(Number(state.itemPages[state.activeItemStatus] || 1), 1), pages);
    state.itemPages[state.activeItemStatus] = current;
    const startIndex = (current - 1) * ITEMS_PAGE_SIZE;
    const endIndex = Math.min(startIndex + ITEMS_PAGE_SIZE, total);
    return {current, pages, startIndex, endIndex};
  }

  function renderItemTabs(groups) {
    ITEM_STATUS_TABS.forEach(status => {
      const tab = $(`[data-item-tab="${status}"]`);
      const count = $(`[data-item-count="${status}"]`);
      if (!tab || !count) return;
      const active = state.activeItemStatus === status;
      tab.classList.toggle('active', active);
      tab.setAttribute('aria-selected', active ? 'true' : 'false');
      count.textContent = groups[status].length;
    });
  }

  function renderItems(items) {
    items = items || state.items;
    const groups = categorizedItems(items);
    const activeItems = groups[state.activeItemStatus] || [];
    const page = itemPageState(activeItems.length);
    const visibleItems = activeItems.slice(page.startIndex, page.endIndex);
    renderItemTabs(groups);
    const retryButton = $('#retry-selected-failed');
    if (retryButton) {
      retryButton.disabled = !(state.selectedTaskId && groups.failure.length);
      retryButton.style.display = state.activeItemStatus === 'failure' ? 'inline-flex' : 'none';
    }
    const loadMoreHtml = state.hasMoreItems
      ? `<div class="load-more-row"><button type="button" class="load-more-btn" onclick="loadMoreItems()">
          ${esc(t('items.loadMore'))} (${state.itemsTotal - items.length} ${esc(t('items.remaining'))})
        </button></div>`
      : '';
    $('#items').innerHTML = (visibleItems.length ? visibleItems.map(item => `
      <div class="file-row">
        <div>
          <div>${esc(item.file_name || item.local_path || item.source_link || `#${item.source_message_id || item.id}`)}</div>
          <div class="mono">${esc(item.source_chat_id || '')} ${esc(item.source_message_id || '')}</div>
        </div>
        <div>${badge(item.status)}</div>
        ${progressLine(t('items.download'), item.download_current, item.download_total)}
        ${progressLine(t('items.upload'), item.upload_current, item.upload_total)}
      </div>
    `).join('') : `<div class="empty">${esc(t(`items.empty.${state.activeItemStatus}`))}</div>`) + loadMoreHtml;

    const range = activeItems.length
      ? interpolate(t('items.page.range'), {
        start: page.startIndex + 1,
        end: page.endIndex,
        total: activeItems.length
      })
      : interpolate(t('items.page.range'), {start: 0, end: 0, total: 0});
    $('#items-page-range').textContent = range;
    $('#items-page-summary').textContent = interpolate(t('items.page.status'), {
      page: page.current,
      pages: page.pages
    });
    $('#items-page-prev').disabled = page.current <= 1;
    $('#items-page-next').disabled = page.current >= page.pages;
  }

  function resetItemPages() {
    ITEM_STATUS_TABS.forEach(status => {
      state.itemPages[status] = 1;
    });
  }

  function switchItemTab(status) {
    if (!ITEM_STATUS_TABS.includes(status)) return;
    state.activeItemStatus = status;
    renderItems(state.items);
  }

  function renderEvents() {
    const events = state.events || [];
    const countText = state.eventsTotal > events.length
      ? `${events.length} / ${state.eventsTotal}`
      : String(events.length);
    $('#event-count').textContent = countText;
    const loadMoreHtml = state.hasMoreEvents
      ? `<div class="load-more-row"><button type="button" class="load-more-btn" onclick="loadMoreEvents()">
          ${esc(t('events.loadMore'))} (${state.eventsTotal - events.length} ${esc(t('events.remaining'))})
        </button></div>`
      : '';
    $('#events').innerHTML = (events.length ? events.map(event => `
      <div class="event">
        <time>${esc(event.created_at)}</time>
        <span>${esc(localizeEventLevel(event.level))}</span>
        <div>${esc(localizeEventMessage(event))}</div>
      </div>
    `).join('') : `<div class="empty">${esc(t('events.empty'))}</div>`) + loadMoreHtml;
  }

  function renderEventCount() {
    if (state.events && state.events.length) {
      const countText = state.eventsTotal > state.events.length
        ? `${state.events.length} / ${state.eventsTotal}`
        : String(state.events.length);
      $('#event-count').textContent = countText;
    }
  }

  function mergeRecentEvents(recentEvents) {
    const existingIds = new Set((state.events || []).map(function(e) { return e.id; }));
    var newEvents = recentEvents.filter(function(e) { return !existingIds.has(e.id); });
    if (!newEvents.length) return;
    var merged = state.events || [];
    newEvents.sort(function(a, b) { return (b.id || 0) - (a.id || 0); });
    merged = newEvents.concat(merged);
    merged.sort(function(a, b) { return (b.id || 0) - (a.id || 0); });
    var maxKeep = Math.max(state.eventsTotal || 0, merged.length, 200);
    state.events = merged.slice(0, maxKeep);
    renderEvents();
  }

  async function loadWatches() {
    const res = await fetch('/api/watches');
    const data = await res.json();
    state.watches = data.watches || [];
    renderWatches();
  }

  async function refreshWatchesAfterMutation() {
    try {
      await loadWatches();
    } catch (error) {
      console.warn('Failed to refresh watches after mutation.', error);
    }
  }

  function renderWatches() {
    const watches = state.watches || [];
    $('#watch-count').textContent = watches.length;
    $('#watches-empty').style.display = watches.length ? 'none' : 'block';
    $('#watches').innerHTML = watches.map(watch => {
      const sanitized = (watch.id || '').replace(/:/g, '_');
      const ec = watch.event_count || 0;
      const eventBadge = watch.type === 'forward' && ec ? ` <span class="badge info">${ec}</span>` : '';
      const rowClick = watch.type === 'forward' ? ` class="watch-row" onclick="toggleWatchEvents('${encodeURIComponent(watch.id)}')"` : '';
      const eventsRow = watch.type === 'forward' ? `
      <tr class="watch-events-row" id="watch-events-${sanitized}">
        <td colspan="5"><div class="watch-events-panel" id="watch-events-panel-${sanitized}"></div></td>
      </tr>` : '';
      return `<tr${rowClick}>
        <td>${esc(t(`watches.${watch.type}`))}</td>
        <td>${badge(watch.status || 'running')}${eventBadge}</td>
        <td class="mono">${esc(watch.source_link || '')}</td>
        <td class="mono">${esc(watch.target_link || '')}${watch.include_comment ? `<div>${esc(t('watches.includeComment'))}</div>` : ''}${watch.error_message ? `<div>${esc(watch.error_message)}</div>` : ''}</td>
        <td>
          ${watch.type === 'forward' ? `<button class="secondary" type="button" onclick="event.stopPropagation(); openEditWatchModal('${encodeURIComponent(watch.id)}','${encodeURIComponent(watch.source_link || '')}','${encodeURIComponent(watch.target_link || '')}','${watch.include_comment ? '1' : '0'}')">
            <svg viewBox="0 0 24 24" fill="none"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span data-i18n="watches.edit">${esc(t('watches.edit'))}</span>
          </button>` : ''}
          <button class="danger" type="button" onclick="event.stopPropagation(); deleteWatch('${encodeURIComponent(watch.id)}')">
            <svg viewBox="0 0 24 24" fill="none"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 14h10l1-14M9 7V4h6v3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span data-i18n="watches.delete">${esc(t('watches.delete'))}</span>
          </button>
        </td>
      </tr>${eventsRow}`;
    }).join('');
  }

  async function toggleWatchEvents(encodedId) {
    const watchId = decodeURIComponent(encodedId);
    const sanitized = watchId.replace(/:/g, '_');
    const row = document.getElementById(`watch-events-${sanitized}`);
    if (!row) return;
    const isOpen = row.classList.contains('open');
    if (isOpen) {
      row.classList.remove('open');
      return;
    }
    row.classList.add('open');
    await loadWatchEvents(watchId, sanitized, 0);
  }
  window.toggleWatchEvents = toggleWatchEvents;

  async function loadWatchEvents(watchId, sanitized, offset) {
    const panel = document.getElementById(`watch-events-panel-${sanitized}`);
    if (!panel) return;
    if (offset === 0) panel.innerHTML = `<div class="watch-event-item">${esc(t('watches.eventLoading'))}</div>`;
    try {
      const res = await fetch(`/api/watches/${encodeURIComponent(watchId)}/events?limit=50&offset=${offset}`);
      const data = await res.json();
      if (!res.ok) { panel.innerHTML = `<div class="watch-event-item">${esc(data.error || 'Load failed')}</div>`; return; }
      const items = data.events || [];
      if (offset === 0) panel.innerHTML = '';
      if (!items.length && offset === 0) {
        panel.innerHTML = `<div class="watch-event-item">${esc(t('watches.noEvents'))}</div>`;
        return;
      }
      items.forEach(evt => {
        const time = new Date(evt.created_at + 'Z').toLocaleString();
        const statusClass = evt.status === 'success' ? 'success' : 'warning';
        const statusLabel = evt.status === 'success' ? t('watches.eventForwarded') : t('watches.eventSkipped');
        const div = document.createElement('div');
        div.className = 'watch-event-item';
        div.innerHTML = `<span class="watch-event-time">${esc(time)}</span>`
          + `<span class="watch-event-badge"><span class="badge ${statusClass}">${esc(statusLabel)}</span></span>`
          + `<span class="watch-event-info">${esc(evt.message)} ${esc(t('watches.source'))}: #${esc(String(evt.source_message_id || ''))} → ${esc(t('watches.target'))}: ${esc(evt.target_link || evt.target_chat_id || '')}</span>`;
        panel.appendChild(div);
      });
      if (data.has_more) {
        const btn = document.createElement('button');
        btn.className = 'watch-events-load-more small';
        btn.textContent = t('watches.loadMore');
        btn.onclick = () => loadWatchEvents(watchId, sanitized, offset + items.length);
        panel.appendChild(btn);
      }
    } catch (e) {
      panel.innerHTML = `<div class="watch-event-item">${esc(t('form.requestFailed'))}</div>`;
    }
  }

  async function deleteWatch(encodedId) {
    if (!window.confirm(t('watches.delete'))) return;
    const res = await fetch(`/api/watches/${encodedId}`, {method: 'DELETE'});
    const data = await res.json();
    if (!res.ok) {
      showNotice('#watch-download-notice', translateApiError(data), false);
      return;
    }
    showNotice('#watch-download-notice', t('watches.deleted'), true);
    await loadWatches();
  }
  window.deleteWatch = deleteWatch;

  let editingWatchId = null;

  function openEditWatchModal(encodedId, encodedSource, encodedTarget, includeCommentFlag) {
    editingWatchId = decodeURIComponent(encodedId);
    document.getElementById('watch-edit-type').value = t('watches.forward');
    document.getElementById('watch-edit-source').value = decodeURIComponent(encodedSource);
    document.getElementById('watch-edit-target').value = decodeURIComponent(encodedTarget);
    document.getElementById('watch-edit-include-comment').checked = includeCommentFlag === '1';
    document.getElementById('watch-edit-notice').style.display = 'none';
    document.getElementById('watch-edit-notice').textContent = '';
    document.getElementById('watch-edit-overlay').classList.add('open');
    document.getElementById('watch-edit-target').focus();
  }
  window.openEditWatchModal = openEditWatchModal;

  function closeEditWatchModal() {
    editingWatchId = null;
    document.getElementById('watch-edit-overlay').classList.remove('open');
  }
  window.closeEditWatchModal = closeEditWatchModal;

  async function submitEditWatch(event) {
    event.preventDefault();
    const button = event.submitter;
    const target = document.getElementById('watch-edit-target').value.trim();
    const includeComment = document.getElementById('watch-edit-include-comment').checked;
    if (!target) {
      showEditWatchNotice(t('watches.targetRequired'), false);
      return;
    }
    await withLoading(button, async () => {
      try {
        await fetch(`/api/watches/${encodeURIComponent(editingWatchId)}`, {
          method: 'PUT',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({target_link: target, include_comment: includeComment})
        }).then(res => res.json().then(data => res.ok ? data : Promise.reject(data)));
      } catch (payload) {
        showEditWatchNotice(translateApiError(payload), false);
        return;
      }
      showEditWatchNotice(t('watches.updated'), true);
      closeEditWatchModal();
      await refreshWatchesAfterMutation();
    });
  }
  window.submitEditWatch = submitEditWatch;

  function showEditWatchNotice(message, success) {
    const el = document.getElementById('watch-edit-notice');
    el.textContent = message;
    el.className = 'notice is-visible' + (success ? ' ok' : '');
  }

  async function loadStatistics() {
    const res = await fetch('/api/statistics');
    const data = await res.json();
    state.statistics = data;
    renderStatistics();
  }

  function renderStatistics() {
    const tables = (state.statistics && state.statistics.tables) || {};
    const rows = ['link', 'count', 'upload'];
    $('#statistics').innerHTML = rows.map(type => {
      const table = tables[type] || {};
      const exportKey = type === 'link' ? 'statistics.exportLink' : type === 'count' ? 'statistics.exportCount' : 'statistics.exportUpload';
      return `
        <tr>
          <td>${esc(t(`statistics.${type}`))}</td>
          <td>${esc(table.available ? t('statistics.yes') : t('statistics.no'))}</td>
          <td class="mono">${esc(table.rows || 0)}</td>
          <td>
            <button type="button" onclick="exportTable('${type}')">
              <svg viewBox="0 0 24 24" fill="none"><path d="M12 5v10M8 11l4 4 4-4M5 20h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              <span>${esc(t(exportKey))}</span>
            </button>
          </td>
        </tr>
      `;
    }).join('');
  }

  async function exportTable(tableType) {
    try {
      const data = await postJson('/api/tables/export', {table_type: tableType});
      showNotice('#statistics-notice', interpolate(t('statistics.exported'), {directory: data.directory || ''}), true);
      await loadStatistics();
    } catch (payload) {
      showNotice('#statistics-notice', translateApiError(payload), false);
    }
  }
  window.exportTable = exportTable;

  async function postTaskAction(taskId, action) {
    const res = await fetch(`/api/tasks/${taskId}/${action}`, {method: 'POST'});
    const data = await res.json();
    if (!res.ok) throw data;
    return data;
  }

  async function runTaskAction(event, taskId, action) {
    event.stopPropagation();
    const button = event.currentTarget;
    await withLoading(button, async () => {
      try {
        await postTaskAction(taskId, action);
        showFormMessage(t('action.taskUpdated'), true);
        await loadTasks();
      } catch (payload) {
        showFormMessage(translateApiError(payload), false);
      }
    });
  }

  function pauseTask(event, taskId) {
    return runTaskAction(event, taskId, 'pause');
  }
  window.pauseTask = pauseTask;

  function resumeTask(event, taskId) {
    return runTaskAction(event, taskId, 'resume');
  }
  window.resumeTask = resumeTask;

  function retryFailedTask(event, taskId) {
    return runTaskAction(event, taskId, 'retry-failed');
  }
  window.retryFailedTask = retryFailedTask;

  async function deleteTask(event, taskId) {
    event.stopPropagation();
    const res = await fetch(`/api/tasks/${taskId}`, {method: 'DELETE'});
    if (res.ok && state.selectedTaskId === taskId) {
      state.selectedTaskId = null;
      state.items = [];
      state.events = [];
      resetItemPages();
      $('#selected-task').textContent = t('items.selectTask');
      renderItems();
      renderEvents();
    }
    await loadTasks();
  }
  window.deleteTask = deleteTask;

  function getPath(obj, path) {
    return path.split('.').reduce((cur, key) => cur && cur[key], obj);
  }

  function setPath(obj, path, value) {
    const parts = path.split('.');
    let cur = obj;
    parts.slice(0, -1).forEach(key => {
      cur[key] = cur[key] || {};
      cur = cur[key];
    });
    cur[parts[parts.length - 1]] = value;
  }

  async function loadSettings() {
    const res = await fetch('/api/settings');
    const data = await res.json();
    state.settings = data.settings || {};
    state.schema = data.schema || {};
    renderTypeSettings();
    fillSettingsForm();
  }

  function renderTypeSettings() {
    const downloadTypes = state.schema.download_type || [];
    const forwardTypes = state.schema.forward_type || [];
    const filterMediaTypes = (state.schema.message_filter && state.schema.message_filter.media_types) || forwardTypes;
    $('#download-type-settings').innerHTML = downloadTypes.map(type => `
      <label class="check-card"><input name="user.download_type" value="${esc(type)}" type="checkbox"><span>${esc(type)}</span></label>
    `).join('');
    var fwdEl = $('#forward-type-settings');
    if (fwdEl) {
      fwdEl.innerHTML = forwardTypes.map(type => `
        <label class="check-card"><input name="global.forward_type.${esc(type)}" type="checkbox"><span>${esc(type)}</span></label>
      `).join('');
    }
    // 消息过滤 — 媒体类型
    var filterEl = $('#filter-media-types');
    if (filterEl) {
      filterEl.innerHTML = filterMediaTypes.map(type => `
        <label class="check-card"><input name="global.message_filter.media_types.${esc(type)}" type="checkbox"><span>${esc(type)}</span></label>
      `).join('');
    }
  }

  function fillSettingsForm() {
    const form = $('#settings-form');
    Array.from(form.elements).forEach(el => {
      if (!el.name) return;
      if (el.name === 'user.download_type') {
        el.checked = (getPath(state.settings, 'user.download_type') || []).includes(el.value);
        return;
      }
      // 消息过滤 — 日期范围：timestamp → datetime-local
      if (el.name === 'global.message_filter.date_range.start_date' || el.name === 'global.message_filter.date_range.end_date') {
        const ts = getPath(state.settings, el.name);
        el.value = ts ? new Date(ts * 1000).toISOString().slice(0, 16) : '';
        return;
      }
      // 消息过滤 — 关键词：数组 → 逗号分隔字符串
      if (el.name === 'global.message_filter.keywords.words') {
        const words = getPath(state.settings, el.name);
        el.value = Array.isArray(words) ? words.join(', ') : '';
        return;
      }
      const value = getPath(state.settings, el.name);
      if (el.type === 'checkbox') {
        el.checked = Boolean(value);
      } else if (value && typeof value === 'object' && 'configured' in value) {
        el.placeholder = value.configured ? t('settings.secretConfigured') : t('settings.secretNotConfigured');
        el.value = '';
      } else {
        el.value = value ?? '';
      }
    });
  }

  function settingsPayload() {
    const payload = {};
    const downloadTypes = [];
    Array.from($('#settings-form').elements).forEach(el => {
      if (!el.name) return;
      if (el.name === 'user.download_type') {
        if (el.checked) downloadTypes.push(el.value);
        return;
      }
      // 消息过滤 — 日期范围：datetime-local → timestamp
      if (el.name === 'global.message_filter.date_range.start_date' || el.name === 'global.message_filter.date_range.end_date') {
        const v = el.value;
        setPath(payload, el.name, v ? (new Date(v).getTime() / 1000) : null);
        return;
      }
      // 消息过滤 — 关键词：逗号分隔字符串 → 数组
      if (el.name === 'global.message_filter.keywords.words') {
        const words = el.value ? el.value.split(',').map(function(s) { return s.trim(); }).filter(Boolean) : [];
        setPath(payload, el.name, words);
        return;
      }
      let value = el.type === 'checkbox' ? el.checked : el.value;
      if (el.type === 'number') value = value === '' ? null : Number(value);
      if (el.type === 'password' && value === '') return;
      setPath(payload, el.name, value);
    });
    setPath(payload, 'user.download_type', downloadTypes);
    return payload;
  }

  async function saveSettings(event) {
    event.preventDefault();
    const res = await fetch('/api/settings', {
      method: 'PATCH',
      headers: {'content-type': 'application/json'},
      body: JSON.stringify(settingsPayload())
    });
    const data = await res.json();
    const notice = $('#settings-notice');
    notice.style.display = 'block';
    notice.classList.toggle('ok', res.ok);
    notice.textContent = res.ok ? t('settings.saved') : translateApiError(data, 'error.update_settings_failed');
    if (res.ok) {
      state.settings = data.settings || {};
      state.schema = data.schema || state.schema;
      fillSettingsForm();
    }
  }

  async function createDownloadWatch(event) {
    event.preventDefault();
    const button = event.submitter;
    await withLoading(button, async () => {
      const sourceLinks = new FormData(event.currentTarget)
        .get('source_links')
        .split(/\r?\n/)
        .map(value => value.trim())
        .filter(Boolean);
      try {
        await postJson('/api/watches', {type: 'download', source_links: sourceLinks});
      } catch (payload) {
        showNotice('#watch-download-notice', translateApiError(payload), false);
        return;
      }
      showNotice('#watch-download-notice', t('watches.created'), true);
      event.currentTarget.reset();
      await refreshWatchesAfterMutation();
    });
  }

  async function createForwardWatch(event) {
    event.preventDefault();
    const button = event.submitter;
    await withLoading(button, async () => {
      const form = new FormData(event.currentTarget);
      try {
        await postJson('/api/watches', {
          type: 'forward',
          source_link: form.get('source_link'),
          target_link: form.get('target_link'),
          include_comment: Boolean(form.get('include_comment'))
        });
      } catch (payload) {
        showNotice('#watch-forward-notice', translateApiError(payload), false);
        return;
      }
      showNotice('#watch-forward-notice', t('watches.created'), true);
      event.currentTarget.reset();
      await refreshWatchesAfterMutation();
    });
  }

  async function createChannelDownload(event) {
    event.preventDefault();
    const button = event.submitter;
    await withLoading(button, async () => {
      const form = new FormData(event.currentTarget);
      const downloadType = Array.from(event.currentTarget.querySelectorAll('input[name="download_type"]:checked')).map(el => el.value);
      const keywords = String(form.get('keywords') || '').split(',').map(value => value.trim()).filter(Boolean);
      try {
        await postJson('/api/channel-downloads', {
          chat_link: form.get('chat_link'),
          date_range: {
            start_date: form.get('start_date') || null,
            end_date: form.get('end_date') || null
          },
          download_type: downloadType,
          keywords,
          include_comment: Boolean(form.get('include_comment'))
        });
        showNotice('#channel-download-notice', t('channel.accepted'), true);
      } catch (payload) {
        showNotice('#channel-download-notice', translateApiError(payload), false);
      }
    });
  }

  async function createUpload(event) {
    event.preventDefault();
    const button = event.submitter;
    await withLoading(button, async () => {
      const form = new FormData(event.currentTarget);
      try {
        await postJson('/api/uploads', {
          path: form.get('path'),
          target_link: form.get('target_link'),
          recursive: Boolean(form.get('recursive'))
        });
        showNotice('#upload-notice', t('uploads.accepted'), true);
      } catch (payload) {
        showNotice('#upload-notice', translateApiError(payload), false);
      }
    });
  }

  async function loadRecords() {
    const res = await fetch('/api/download-records');
    const data = await res.json();
    state.records = data.records || [];
    renderRecords();
  }

  function renderRecords() {
    const records = state.records || [];
    $('#record-count').textContent = records.length;
    $('#records-empty').style.display = records.length ? 'none' : 'block';
    $('#records').innerHTML = records.map(record => `
      <tr>
        <td class="mono">${esc(record.source_chat_id)}</td>
        <td class="mono">${esc(record.source_message_id)}</td>
        <td><div>${esc(record.file_name || '')}</div><div class="mono">${esc(record.local_path || '')}</div></td>
        <td>${formatBytes(record.file_size)}</td>
        <td class="mono">${esc(record.updated_at || record.downloaded_at)}</td>
      </tr>
    `).join('');
  }

  /* ====== 退出登录 ====== */
  var btnLogout = $('#btn-logout');
  if (btnLogout) btnLogout.addEventListener('click', handleLogout);
  var mobBtnLogout = $('#mob-btn-logout');
  if (mobBtnLogout) mobBtnLogout.addEventListener('click', handleLogout);
</script>
<script>
  /* ====== 登录流程（移动端） ====== */
  var authPollTimer = null;
  var authStep = '';

  function showLoginStep(step) {
    authStep = step;
    var steps = ['login-form-phone', 'login-form-code', 'login-form-password', 'login-form-recovery', 'login-form-signup', 'login-form-done'];
    steps.forEach(function(id) { var el = document.getElementById(id); if (el) el.style.display = 'none'; });
    var el = document.getElementById('login-form-' + step);
    if (el) el.style.display = '';
    var container = document.getElementById('login-container');
    if (container) container.classList.add('active');
    var loginError = document.getElementById('login-error');
    if (loginError) loginError.classList.remove('visible');
  }

  function hideLogin() {
    var container = document.getElementById('login-container');
    if (container) container.classList.remove('active');
    if (authPollTimer) { clearInterval(authPollTimer); authPollTimer = null; }
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
      if (resp.status === 401) return;
      var state = await resp.json();
      if (!state || !state.step) return;
      switch (state.step) {
        case 'pending':
          var container = document.getElementById('login-container');
          if (container) container.classList.remove('active');
          return;
        case 'done': case 'none':
          hideLogin();
          loadTasks();
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
            if (desc) desc.textContent = '\u9a8c\u8bc1\u7801\u5df2\u901a\u8fc7\u300c' + state.code_type + '\u300d\u53d1\u9001';
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
    var btn = document.querySelector('.login-submit');
    if (btn) btn.disabled = true;
    showLoginError('');
    try {
      await fetch('/api/auth/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      await new Promise(function(r) { setTimeout(r, 500); });
      await checkAuthStatus();
    } catch (e) {
      showLoginError('\u63d0\u4ea4\u5931\u8d25\uff0c\u8bf7\u91cd\u8bd5');
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  /* phone submit */
  var phoneBtn = document.getElementById('login-btn-phone');
  if (phoneBtn) {
    phoneBtn.addEventListener('click', function() {
      var phone = document.getElementById('login-phone').value.trim();
      if (!phone) { showLoginError('\u8bf7\u8f93\u5165\u7535\u8bdd\u53f7\u7801'); return; }
      if (!phone.startsWith('+')) { showLoginError('\u7535\u8bdd\u53f7\u7801\u9700\u4ee5 +\u5730\u533a\u53f7\u5f00\u5934'); return; }
      submitAuth({ phone: phone });
    });
  }

  var codeBtn = document.getElementById('login-btn-code');
  if (codeBtn) {
    codeBtn.addEventListener('click', function() {
      var code = document.getElementById('login-code').value.trim();
      if (!code) { showLoginError('\u8bf7\u8f93\u5165\u9a8c\u8bc1\u7801'); return; }
      submitAuth({ code: code });
    });
  }

  var backBtn = document.getElementById('login-btn-back');
  if (backBtn) {
    backBtn.addEventListener('click', function() {
      showLoginStep('phone');
      document.getElementById('login-code').value = '';
    });
  }

  var pwdBtn = document.getElementById('login-btn-password');
  if (pwdBtn) {
    pwdBtn.addEventListener('click', function() {
      var pwd = document.getElementById('login-password').value;
      submitAuth({ password: pwd });
    });
  }

  var pwdBackBtn = document.getElementById('login-btn-back-pwd');
  if (pwdBackBtn) {
    pwdBackBtn.addEventListener('click', function() {
      showLoginStep('code');
      document.getElementById('login-password').value = '';
    });
  }

  var recBtn = document.getElementById('login-btn-recovery');
  if (recBtn) {
    recBtn.addEventListener('click', function() {
      var code = document.getElementById('login-recovery').value.trim();
      if (!code) { showLoginError('\u8bf7\u8f93\u5165\u6062\u590d\u4ee3\u7801'); return; }
      submitAuth({ recovery_code: code });
    });
  }

  var recBackBtn = document.getElementById('login-btn-back-recovery');
  if (recBackBtn) {
    recBackBtn.addEventListener('click', function() {
      showLoginStep('password');
      document.getElementById('login-recovery').value = '';
    });
  }

  var signupBtn = document.getElementById('login-btn-signup');
  if (signupBtn) {
    signupBtn.addEventListener('click', function() {
      var first = document.getElementById('login-first-name').value.trim();
      if (!first) { showLoginError('\u8bf7\u8f93\u5165\u540d\u5b57'); return; }
      submitAuth({ first_name: first, last_name: document.getElementById('login-last-name').value.trim() });
    });
  }

  (function() {
    checkAuthStatus();
    authPollTimer = setInterval(function() {
      if (authStep === 'done' || authStep === 'none') {
        clearInterval(authPollTimer);
        authPollTimer = null;
        return;
      }
      checkAuthStatus();
    }, 2000);
  })();

  /* ====== 移动端初始化 ====== */
  function hasActiveTasks() {
    return state.tasks.some(function(t) { return t.status === 'pending' || t.status === 'running'; });
  }

  function startPolling() {
    if (state.taskPollTimer) return;
    var fastInterval = 3000;
    var slowInterval = 15000;
    var currentInterval = fastInterval;
    var lastPollTime = 0;

    async function poll() {
      if (document.hidden) { scheduleNext(currentInterval); return; }
      var now = Date.now();
      var minGap = currentInterval - 500;
      if (now - lastPollTime < minGap) { scheduleNext(currentInterval); return; }
      lastPollTime = now;
      try { await loadTasks(); } catch (e) { console.warn('Poll failed:', e); }
      currentInterval = hasActiveTasks() ? fastInterval : slowInterval;
      scheduleNext(currentInterval);
    }

    function scheduleNext(interval) {
      state.taskPollTimer = setTimeout(poll, interval);
    }

    poll();
  }

  function stopPolling() {
    if (state.taskPollTimer) {
      clearTimeout(state.taskPollTimer);
      state.taskPollTimer = null;
    }
  }

  /* ====== 移动端视图切换 ====== */
  function mobSwitchView(view) {
    $$('.mob-view').forEach(el => el.classList.toggle('active', el.id === `mob-view-${view}`));
    $$('.mob-tab').forEach(el => el.classList.toggle('active', el.dataset.mobNav === view));
    closeDrawer();
    closeFabMenu();
    if (view === 'settings') loadSettings();
    if (view === 'records') loadRecords();
    if (view === 'watches') loadWatches();
    if (view === 'statistics') loadStatistics();
    if (view === 'media') loadMediaMobile();
  }

  async function loadMediaMobile() {
    var info = $('#mob-media-result');
    info.innerHTML = '<p>' + t('media.scanning') + '</p>';
    try {
      var data = await fetchJson('/api/media/scan');
      var ti = data.transfer_items || {};
      var orph = data.orphan_files || {};
      var totalCount = data.total_count || 0;
      var totalSize = data.total_size || 0;
      info.innerHTML =
        '<p><strong>' + t('media.totalFiles') + ':</strong> ' + totalCount + '</p>' +
        '<p><strong>' + t('media.totalSize') + ':</strong> ' + formatBytes(totalSize) + '</p>';
    } catch (err) {
      info.innerHTML = '<p>' + translateApiError(err, 'form.requestFailed') + '</p>';
    }
  }

  // mobile media scan button
  var mobMediaBtn = $('#mob-media-scan-btn');
  if (mobMediaBtn) mobMediaBtn.addEventListener('click', loadMediaMobile);

  /* ====== 抽屉（更多菜单） ====== */
  function openDrawer() {
    $('#mob-drawer-overlay').classList.add('open');
  }
  function closeDrawer() {
    $('#mob-drawer-overlay').classList.remove('open');
  }

  /* ====== FAB 菜单 ====== */
  function toggleFabMenu() {
    const menu = $('#mob-fab-menu');
    const fab = $('#mob-fab');
    const isOpen = menu.classList.contains('open');
    if (isOpen) {
      menu.classList.remove('open');
      fab.textContent = '+';
    } else {
      menu.classList.add('open');
      fab.textContent = '\u00d7';
    }
  }
  function closeFabMenu() {
    const menu = $('#mob-fab-menu');
    const fab = $('#mob-fab');
    menu.classList.remove('open');
    fab.textContent = '+';
  }

  /* ====== 折叠面板 ====== */
  function toggleCollapse(head) {
    head.closest('.mob-collapse').classList.toggle('open');
  }

  /* ====== Toast ====== */
  let mobToastTimer = null;
  function showToast(message, duration) {
    if (duration === void 0) duration = 2500;
    const toast = $('#mob-toast');
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(mobToastTimer);
    mobToastTimer = setTimeout(function() { toast.classList.remove('show'); }, duration);
  }

  /* ====== 卡片状态徽章 ====== */
  function mobBadge(status) {
    var cls;
    if (status === 'running') cls = 'running';
    else if (status === 'success') cls = 'completed';
    else if (status === 'paused') cls = 'paused';
    else if (status === 'failure') cls = 'failure';
    else if (status === 'cancelled') cls = 'cancelled';
    else cls = 'pending';
    return '<span class="mob-card__badge ' + cls + '">' + esc(t('status.' + status)) + '</span>';
  }

  /* ====== 渲染转存任务卡片列表 ====== */
  function renderMobTasks() {
    var tasks = state.tasks || [];
    var container = $('#mob-tasks-list');
    if (!tasks.length) {
      container.innerHTML = '<div class="mob-empty" data-i18n="tasks.empty">' + t('tasks.empty') + '</div>';
      return;
    }
    container.innerHTML = tasks.map(function(task) {
      var total = Number(task.total_items || 0);
      var done = Number(task.completed_items || 0);
      var failed = Number(task.failed_items || 0);
      var percent = total > 0 ? Math.round(((done + failed) / total) * 100) : 0;
      var actions = '';
      if (task.status === 'running') actions += '<button class="secondary small" data-pause="' + task.id + '">' + t('tasks.pause') + '</button>';
      if (task.status === 'paused') actions += '<button class="secondary small" data-resume="' + task.id + '">' + t('tasks.resume') + '</button>';
      if (task.failed_items > 0) actions += '<button class="secondary small" data-retry="' + task.id + '">' + t('tasks.retryFailed') + '</button>';
      actions += '<button class="danger small" data-delete="' + task.id + '">' + t('tasks.delete') + '</button>';
      return '<div class="mob-card status-' + task.status + '">'
        + '<div class="mob-card__head">'
        + '<span class="mob-card__title">' + esc(task.source_link) + '</span>'
        + mobBadge(task.status)
        + '</div>'
        + '<div class="mob-card__row"><span class="label">' + t('tasks.target') + '</span><span>' + esc(task.target_link) + '</span></div>'
        + '<div class="mob-card__row"><span class="label">' + t('tasks.progress') + '</span><span>' + done + '/' + total + (failed ? ' (' + failed + ' ' + t('side.failed') + ')' : '') + '</span></div>'
        + '<div class="mob-card__progress"><div class="mob-card__progress-fill" style="width:' + percent + '%"></div></div>'
        + '<div class="mob-card__actions">' + actions + '</div>'
        + '</div>';
    }).join('');

    container.querySelectorAll('[data-pause]').forEach(function(btn) {
      btn.addEventListener('click', function(e) { runTaskAction(e, Number(btn.dataset.pause), 'pause'); });
    });
    container.querySelectorAll('[data-resume]').forEach(function(btn) {
      btn.addEventListener('click', function(e) { runTaskAction(e, Number(btn.dataset.resume), 'resume'); });
    });
    container.querySelectorAll('[data-retry]').forEach(function(btn) {
      btn.addEventListener('click', function(e) { runTaskAction(e, Number(btn.dataset.retry), 'retry-failed'); });
    });
    container.querySelectorAll('[data-delete]').forEach(function(btn) {
      btn.addEventListener('click', function(e) { deleteTask(e, Number(btn.dataset.delete)); });
    });

    // 点击卡片打开详情
    container.querySelectorAll('.mob-card').forEach(function(card, idx) {
      card.addEventListener('click', function(e) {
        if (e.target.closest('button')) return;
        openTaskDetail(tasks[idx].id);
      });
    });
  }

  /* ====== 渲染监听卡片列表 ====== */
  function renderMobWatches() {
    var watches = state.watches || [];
    var container = $('#mob-watches-list');
    if (!watches.length) {
      container.innerHTML = '<div class="mob-empty" data-i18n="watches.empty">' + t('watches.empty') + '</div>';
      return;
    }
    container.innerHTML = watches.map(function(w) {
      var typeLabel = w.type === 'download' ? t('watches.download') : t('watches.forward');
      var sourceHtml = '';
      if (w.source_links) {
        sourceHtml = '<div class="mob-card__row"><span class="label">' + t('watches.sources') + '</span><span>' + esc((w.source_links || []).join(', ')) + '</span></div>';
      } else if (w.source_link) {
        sourceHtml = '<div class="mob-card__row"><span class="label">' + t('watches.source') + '</span><span>' + esc(w.source_link) + '</span></div>';
      }
      var targetHtml = '';
      if (w.target_link) {
        targetHtml = '<div class="mob-card__row"><span class="label">' + t('watches.target') + '</span><span>' + esc(w.target_link) + '</span></div>';
      }
      var watchId = w.encoded_id || w.id;
      var sanitized = (watchId || '').replace(/:/g, '_');
      var eventsBtn = '';
      var eventsPanel = '';
      if (w.type === 'forward') {
        var ec = w.event_count || 0;
        eventsBtn = '<button class="small" data-watch-events="' + watchId + '">' + t('watches.events') + (ec ? ' (' + ec + ')' : '') + '</button>';
        eventsPanel = '<div class="mob-watch-events" id="mob-watch-events-' + sanitized + '" style="display:none;"></div>';
      }
      return '<div class="mob-card status-' + (w.status || 'running') + '">'
        + '<div class="mob-card__head">'
        + '<span class="mob-card__title">' + typeLabel + '</span>'
        + '<span class="mob-card__badge running">' + esc(w.type) + '</span>'
        + '</div>'
        + sourceHtml + targetHtml
        + '<div class="mob-card__actions">'
        + '<button class="danger small" data-delete-watch="' + watchId + '">' + t('watches.delete') + '</button>'
        + eventsBtn
        + '</div>'
        + eventsPanel
        + '</div>';
    }).join('');

    container.querySelectorAll('[data-delete-watch]').forEach(function(btn) {
      btn.addEventListener('click', function() { deleteWatch(btn.dataset.deleteWatch); });
    });

    container.querySelectorAll('[data-watch-events]').forEach(function(btn) {
      btn.addEventListener('click', function() {
        var watchId = btn.dataset.watchEvents;
        var sanitized = watchId.replace(/:/g, '_');
        var panel = document.getElementById('mob-watch-events-' + sanitized);
        if (!panel) return;
        if (panel.style.display === 'none' || panel.style.display === '') {
          panel.style.display = 'block';
          loadMobileWatchEvents(watchId, sanitized);
        } else {
          panel.style.display = 'none';
        }
      });
    });
  }

  async function loadMobileWatchEvents(watchId, sanitized) {
    var panel = document.getElementById('mob-watch-events-' + sanitized);
    if (!panel) return;
    panel.innerHTML = '<div class="watch-event-item">' + esc(t('watches.eventLoading')) + '</div>';
    try {
      var res = await fetch('/api/watches/' + encodeURIComponent(watchId) + '/events?limit=50&offset=0');
      var data = await res.json();
      if (!res.ok) { panel.innerHTML = '<div class="watch-event-item">' + esc(data.error || 'Load failed') + '</div>'; return; }
      var items = data.events || [];
      if (!items.length) {
        panel.innerHTML = '<div class="watch-event-item">' + esc(t('watches.noEvents')) + '</div>';
        return;
      }
      panel.innerHTML = '';
      items.forEach(function(evt) {
        var time = new Date(evt.created_at + 'Z').toLocaleString();
        var statusClass = evt.status === 'success' ? 'success' : 'warning';
        var statusLabel = evt.status === 'success' ? t('watches.eventForwarded') : t('watches.eventSkipped');
        var div = document.createElement('div');
        div.className = 'watch-event-item';
        div.innerHTML = '<span class="watch-event-time">' + esc(time) + '</span>'
          + '<span class="watch-event-badge"><span class="badge ' + statusClass + '">' + esc(statusLabel) + '</span></span>'
          + '<span class="watch-event-info">' + esc(evt.message) + ' #' + esc(String(evt.source_message_id || '')) + '</span>';
        panel.appendChild(div);
      });
    } catch (e) {
      panel.innerHTML = '<div class="watch-event-item">' + esc(t('form.requestFailed')) + '</div>';
    }
  }

  /* ====== 任务详情 Sheet ====== */
  var sheetTaskId = null;
  var sheetItems = [];
  var sheetEvents = [];
  var sheetItemTotal = 0;
  var sheetEventTotal = 0;
  var sheetItemOffset = 0;
  var sheetEventOffset = 0;
  var sheetHasMoreItems = false;
  var sheetHasMoreEvents = false;
  var sheetActiveTab = 'running';
  var sheetItemPage = 1;
  var sheetItemPageSize = 10;

  async function openTaskDetail(taskId) {
    sheetTaskId = taskId;
    state.selectedTaskId = taskId;
    sheetItems = [];
    sheetEvents = [];
    sheetActiveTab = 'running';
    sheetItemPage = 1;
    sheetItemOffset = 0;
    sheetEventOffset = 0;
    try {
      var res = await fetch('/api/tasks/' + taskId + '?items_limit=200&items_offset=0&events_limit=100&events_offset=0');
      if (!res.ok) { showToast(translateApiError(await res.json())); return; }
      var data = await res.json();
      sheetItems = data.items || [];
      sheetEvents = data.events || [];
      sheetItemTotal = data.item_count || 0;
      sheetEventTotal = data.event_count || 0;
      sheetItemOffset = data.items_offset || 0;
      sheetEventOffset = data.events_offset || 0;
      sheetHasMoreItems = data.has_more_items || false;
      sheetHasMoreEvents = data.has_more_events || false;
    } catch (e) { showToast(t('form.requestFailed')); return; }

    var task = state.tasks.find(function(t) { return t.id === taskId; });
    var total = Number((task && task.total_items) || 0);
    var done = Number((task && task.completed_items) || 0);
    var failed = Number((task && task.failed_items) || 0);
    var percent = total > 0 ? Math.round(((done + failed) / total) * 100) : 0;

    var groups = categorizeSheetItems();
    var html = '<h3 class="mob-sheet__title">#' + taskId + ' ' + esc((task && task.source_link) || '') + '</h3>'
      + '<div class="mob-sheet__task-header">'
      + '<div class="task-title">' + esc((task && task.source_link) || '') + '</div>'
      + '<div class="task-meta">' + (task ? (mobBadge(task.status) + ' ' + esc(task.target_link || '')) : '') + '</div>'
      + '<div class="mob-card__row"><span class="label">' + t('tasks.progress') + '</span><span>' + done + '/' + total + (failed ? ' (' + failed + ' ' + t('side.failed') + ')' : '') + '</span></div>'
      + '<div class="mob-card__progress"><div class="mob-card__progress-fill" style="width:' + percent + '%"></div></div>'
      + '</div>'
      + '<div class="mob-sheet-tabs" id="mob-sheet-item-tabs">'
      + renderSheetTab('running', groups.running.length)
      + renderSheetTab('success', groups.success.length)
      + renderSheetTab('skipped', groups.skipped.length)
      + renderSheetTab('failure', groups.failure.length)
      + '</div>'
      + '<div id="mob-sheet-items"></div>'
      + '<div id="mob-sheet-items-pagination"></div>'
      + '<div class="mob-section-title" style="margin-top:6px;">' + t('events.title') + ' (' + String(sheetEvents.length) + (sheetEventTotal > sheetEvents.length ? ' / ' + sheetEventTotal : '') + ')</div>'
      + '<div id="mob-sheet-events"></div>';

    var sheet = $('#mob-sheet');
    sheet.innerHTML = html;
    $('#mob-sheet-overlay').classList.add('open');

    bindSheetTabClicks();
    renderSheetItemPage();
    renderSheetEvents();

    // Sheet overlay 点击关闭
    $('#mob-sheet-overlay').onclick = function(e) {
      if (e.target === this) closeSheet();
    };
  }

  function closeSheet() {
    $('#mob-sheet-overlay').classList.remove('open');
    sheetTaskId = null;
  }

  function renderSheetTab(status, count) {
    var labelKey = 'items.tab.' + status;
    var active = sheetActiveTab === status ? ' active' : '';
    return '<button class="mob-sheet-tab' + active + '" data-sheet-tab="' + status + '">' + t(labelKey) + '<span class="count">' + count + '</span></button>';
  }

  function bindSheetTabClicks() {
    var tabs = document.querySelectorAll('#mob-sheet-item-tabs .mob-sheet-tab');
    tabs.forEach(function(tab) {
      tab.addEventListener('click', function() {
        sheetActiveTab = this.dataset.sheetTab;
        sheetItemPage = 1;
        var allTabs = document.querySelectorAll('#mob-sheet-item-tabs .mob-sheet-tab');
        allTabs.forEach(function(t) { t.classList.remove('active'); });
        this.classList.add('active');
        renderSheetItemPage();
      });
    });
  }

  function categorizeSheetItems() {
    var groups = { running: [], success: [], skipped: [], failure: [] };
    (sheetItems || []).forEach(function(item) {
      var status = String((item && item.status) || 'pending');
      if (status === 'success' || status === 'skipped' || status === 'failure') {
        groups[status].push(item);
      } else {
        groups.running.push(item);
      }
    });
    return groups;
  }

  function renderSheetItemPage() {
    var groups = categorizeSheetItems();
    var activeItems = groups[sheetActiveTab] || [];
    var total = activeItems.length;
    var pages = Math.max(1, Math.ceil(total / sheetItemPageSize));
    if (sheetItemPage > pages) sheetItemPage = pages;
    var start = (sheetItemPage - 1) * sheetItemPageSize;
    var end = Math.min(start + sheetItemPageSize, total);
    var pageItems = activeItems.slice(start, end);

    var container = $('#mob-sheet-items');
    if (!pageItems.length) {
      container.innerHTML = '<div class="mob-empty">' + t('items.empty.' + sheetActiveTab) + '</div>';
    } else {
      container.innerHTML = pageItems.map(function(item) {
        var dlPct = pct(item.download_current, item.download_total);
        var ulPct = pct(item.upload_current, item.upload_total);
        return '<div class="mob-item-row">'
          + '<div class="mob-item-row__name">' + esc(item.file_name || item.local_path || '#' + (item.source_message_id || item.id)) + '</div>'
          + '<div style="text-align:right;font-size:var(--font-xs);color:var(--muted);flex-shrink:0;">'
          + '<div>' + t('items.download') + ' ' + dlPct + '%</div>'
          + '<div>' + t('items.upload') + ' ' + ulPct + '%</div>'
          + '</div>'
          + '</div>';
      }).join('');
    }

    var pagEl = $('#mob-sheet-items-pagination');
    var pagHtml = '';
    if (pages > 1) {
      pagHtml += '<div class="mob-sheet-pagination">'
        + '<button class="secondary small" ' + (sheetItemPage <= 1 ? 'disabled' : '') + ' onclick="sheetPrevPage()">' + t('items.page.previous') + '</button>'
        + '<span>' + interpolate(t('items.page.range'), { start: start + 1, end: end, total: total }) + '</span>'
        + '<button class="secondary small" ' + (sheetItemPage >= pages ? 'disabled' : '') + ' onclick="sheetNextPage()">' + t('items.page.next') + '</button>'
        + '</div>';
    }
    if (sheetHasMoreItems && sheetItems.length < sheetItemTotal) {
      pagHtml += '<div class="mob-load-more"><button class="secondary small" onclick="loadMoreSheetItems()">' + t('items.loadMore') + ' (' + (sheetItemTotal - sheetItems.length) + ' ' + t('items.remaining') + ')</button></div>';
    }
    pagEl.innerHTML = pagHtml;
  }

  function renderSheetEvents() {
    var container = $('#mob-sheet-events');
    if (!sheetEvents.length) {
      container.innerHTML = '<div class="mob-empty">' + t('events.empty') + '</div>';
      return;
    }
    var html = sheetEvents.map(function(event) {
      return '<div class="mob-event-row">'
        + '<time>' + esc(event.created_at) + '</time>'
        + '<span style="color:var(--accent);">[' + esc(localizeEventLevel(event.level)) + ']</span> '
        + esc(localizeEventMessage(event))
        + '</div>';
    }).join('');
    if (sheetHasMoreEvents && sheetEvents.length < sheetEventTotal) {
      html += '<div class="mob-load-more"><button class="secondary small" onclick="loadMoreSheetEvents()">' + t('events.loadMore') + ' (' + (sheetEventTotal - sheetEvents.length) + ' ' + t('events.remaining') + ')</button></div>';
    }
    container.innerHTML = html;
  }

  function sheetPrevPage() {
    if (sheetItemPage > 1) { sheetItemPage--; renderSheetItemPage(); }
  }
  function sheetNextPage() {
    sheetItemPage++;
    renderSheetItemPage();
  }
  window.sheetPrevPage = sheetPrevPage;
  window.sheetNextPage = sheetNextPage;

  async function loadMoreSheetItems() {
    if (!sheetTaskId) return;
    var offset = sheetItemOffset + 200;
    try {
      var res = await fetch('/api/tasks/' + sheetTaskId + '?items_limit=200&items_offset=' + offset + '&events_limit=0&events_offset=0');
      if (!res.ok) return;
      var data = await res.json();
      sheetItems = sheetItems.concat(data.items || []);
      sheetItemTotal = data.item_count || sheetItemTotal;
      sheetItemOffset = offset;
      sheetHasMoreItems = data.has_more_items || false;
      renderSheetItemPage();
    } catch (e) { /* ignore */ }
  }
  window.loadMoreSheetItems = loadMoreSheetItems;

  async function loadMoreSheetEvents() {
    if (!sheetTaskId) return;
    var offset = sheetEventOffset + 100;
    try {
      var res = await fetch('/api/tasks/' + sheetTaskId + '?items_limit=0&items_offset=0&events_limit=100&events_offset=' + offset);
      if (!res.ok) return;
      var data = await res.json();
      sheetEvents = sheetEvents.concat(data.events || []);
      sheetEventTotal = data.event_count || sheetEventTotal;
      sheetEventOffset = offset;
      sheetHasMoreEvents = data.has_more_events || false;
      renderSheetEvents();
    } catch (e) { /* ignore */ }
  }
  window.loadMoreSheetEvents = loadMoreSheetEvents;

  /* ====== 渲染设置表单 ====== */
  function renderMobSettingsForm() {
    if (!state.settings || !state.schema) return;
    var s = state.settings;
    var schema = state.schema;
    var user = s.user || {};
    var glob = s.global || {};
    var tp = (glob.target_profiles || {});
    var pikpak = tp.pikpak || {};
    var archive = pikpak.archive || {};
    var upload = glob.upload || {};
    var sensitiveKeys = schema.sensitive_keys || [];
    var downloadTypes = schema.download_type || [];
    var forwardTypes = schema.forward_type || [];
    var selectedDownload = user.download_type || [];
    var exportTable = glob.export_table || {};

    // Path & Task
    var maxTasks = user.max_tasks || {};
    var maxRetries = user.max_retries || {};
    $('#mob-settings-path-fields').innerHTML =
      '<label><span>' + t('settings.saveDirectory') + '</span><input type="text" name="user.save_directory" value="' + esc(user.save_directory || '') + '"></label>'
      + '<label><span>' + t('settings.tempDirectory') + '</span><input type="text" name="user.temp_directory" value="' + esc(user.temp_directory || '') + '"></label>'
      + '<label><span>' + t('settings.sessionDirectory') + '</span><input type="text" name="user.session_directory" value="' + esc(user.session_directory || '') + '"></label>'
      + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">'
      + '<label><span>' + t('settings.maxDownload') + '</span><input type="number" name="user.max_tasks.download" value="' + esc(maxTasks.download || '') + '" min="1"></label>'
      + '<label><span>' + t('settings.maxUpload') + '</span><input type="number" name="user.max_tasks.upload" value="' + esc(maxTasks.upload || '') + '" min="1"></label>'
      + '</div>'
      + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">'
      + '<label><span>' + t('settings.retryDownload') + '</span><input type="number" name="user.max_retries.download" value="' + esc(maxRetries.download || '') + '" min="0"></label>'
      + '<label><span>' + t('settings.retryUpload') + '</span><input type="number" name="user.max_retries.upload" value="' + esc(maxRetries.upload || '') + '" min="0"></label>'
      + '</div>'
      + '<label><span>' + t('settings.pikpakMaxFileSize') + '</span><input type="number" name="global.target_profiles.pikpak.max_file_size" value="' + esc(pikpak.max_file_size || '') + '" min="1"></label>';

    // Behavior
    $('#mob-settings-behavior-fields').innerHTML =
      '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.notice" style="width:auto;min-height:auto;"' + (glob.notice ? ' checked' : '') + '><span>' + t('settings.notice') + '</span></label>'
      + '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="user.is_shutdown" style="width:auto;min-height:auto;"' + (user.is_shutdown ? ' checked' : '') + '><span>' + t('settings.shutdown') + '</span></label>'
      + '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.upload.download_upload" style="width:auto;min-height:auto;"' + (upload.download_upload ? ' checked' : '') + '><span>' + t('settings.downloadUpload') + '</span></label>'
      + '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.upload.delete" style="width:auto;min-height:auto;"' + (upload.delete ? ' checked' : '') + '><span>' + t('settings.uploadDelete') + '</span></label>'
      + '<label><span>' + t('settings.pendingLimit') + '</span><input type="number" name="global.upload.pending_limit" value="' + esc(upload.pending_limit || '') + '" min="1" max="5"></label>';

    // PikPak Archive
    $('#mob-settings-archive-fields').innerHTML =
      '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.target_profiles.pikpak.archive.enable" style="width:auto;min-height:auto;"' + (archive.enable ? ' checked' : '') + '><span>' + t('settings.pikpakArchiveEnable') + '</span></label>'
      + '<label><span>' + t('settings.pikpakArchiveRemote') + '</span><input type="text" name="global.target_profiles.pikpak.archive.remote" value="' + esc(archive.remote || '') + '"></label>'
      + '<label><span>' + t('settings.pikpakArchiveSource') + '</span><input type="text" name="global.target_profiles.pikpak.archive.source_directory" value="' + esc(archive.source_directory || '') + '"></label>'
      + '<label><span>' + t('settings.pikpakArchiveRoot') + '</span><input type="text" name="global.target_profiles.pikpak.archive.root_directory" value="' + esc(archive.root_directory || '') + '"></label>'
      + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">'
      + '<label><span>' + t('settings.pikpakArchivePoll') + '</span><input type="number" name="global.target_profiles.pikpak.archive.poll_seconds" value="' + esc(archive.poll_seconds || '') + '" min="0"></label>'
      + '<label><span>' + t('settings.pikpakArchiveInterval') + '</span><input type="number" name="global.target_profiles.pikpak.archive.poll_interval_seconds" value="' + esc(archive.poll_interval_seconds || '') + '" min="0"></label>'
      + '</div>'
      + '<label><span>' + t('settings.pikpakArchiveWindow') + '</span><input type="number" name="global.target_profiles.pikpak.archive.match_window_seconds" value="' + esc(archive.match_window_seconds || '') + '" min="0"></label>';

    // Account & Proxy
    $('#mob-settings-sensitive-fields').innerHTML =
      '<label><span>API ID</span><input type="text" name="user.api_id" value="' + esc(user.api_id || '') + '"></label>'
      + sensitiveKeys.map(function(k) {
        var v = getPath(user, getSettingLeafKey(k));
        return '<label><span>' + esc(k) + '</span><input type="password" name="user.' + esc(k) + '" placeholder="' + (v && v.configured ? t('settings.secretConfigured') : t('settings.secretNotConfigured')) + '" autocomplete="new-password"></label>';
      }).join('');

    // Download Types
    $('#mob-settings-download-types-fields').innerHTML = renderCheckCards('user.download_type', downloadTypes, selectedDownload);

    // Forward Types
    $('#mob-settings-forward-types-fields').innerHTML = renderCheckCards('global.forward_type', forwardTypes, selectedForward(glob));

    // Message Filter
    var mf = glob.message_filter || {};
    var mfMediaTypes = (state.schema.message_filter && state.schema.message_filter.media_types) || forwardTypes;
    var mfDateRange = mf.date_range || {};
    var mfKeywords = mf.keywords || {};
    var mfDateStart = mfDateRange.start_date ? new Date(mfDateRange.start_date * 1000).toISOString().slice(0, 16) : '';
    var mfDateEnd = mfDateRange.end_date ? new Date(mfDateRange.end_date * 1000).toISOString().slice(0, 16) : '';
    var mfKwStr = Array.isArray(mfKeywords.words) ? mfKeywords.words.join(', ') : '';
    $('#mob-settings-message-filter-fields').innerHTML =
      '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.message_filter.enabled" style="width:auto;min-height:auto;"' + (mf.enabled !== false ? ' checked' : '') + '><span>' + t('settings.enabled') + '</span></label>'
      + '<div class="mob-subsection"><h4>' + t('settings.mediaTypes') + '</h4>'
      + renderCheckCards('global.message_filter.media_types', mfMediaTypes, selectedMediaTypes(glob))
      + '</div>'
      + '<div class="mob-subsection"><h4>' + t('settings.dateRange') + '</h4>'
      + '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.message_filter.date_range.enabled" style="width:auto;min-height:auto;"' + (mfDateRange.enabled ? ' checked' : '') + '><span>' + t('settings.enabled') + '</span></label>'
      + '<div class="field-grid field-grid--two" style="margin-top:8px">'
      + '<label class="field"><span>' + t('settings.startDate') + '</span><input name="global.message_filter.date_range.start_date" type="datetime-local" value="' + escAttr(mfDateStart) + '"></label>'
      + '<label class="field"><span>' + t('settings.endDate') + '</span><input name="global.message_filter.date_range.end_date" type="datetime-local" value="' + escAttr(mfDateEnd) + '"></label>'
      + '</div></div>'
      + '<div class="mob-subsection"><h4>' + t('settings.keywords') + '</h4>'
      + '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.message_filter.keywords.enabled" style="width:auto;min-height:auto;"' + (mfKeywords.enabled ? ' checked' : '') + '><span>' + t('settings.enabled') + '</span></label>'
      + '<label class="field" style="margin-top:8px"><span>' + t('settings.keywordList') + '</span><input name="global.message_filter.keywords.words" value="' + escAttr(mfKwStr) + '" placeholder="' + t('settings.keywordPlaceholder') + '"></label>'
      + '</div>';

    // Export Tables
    $('#mob-settings-exports-fields').innerHTML =
      '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.export_table.link" style="width:auto;min-height:auto;"' + (exportTable.link ? ' checked' : '') + '><span>' + t('settings.exportLink') + '</span></label>'
      + '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.export_table.count" style="width:auto;min-height:auto;"' + (exportTable.count ? ' checked' : '') + '><span>' + t('settings.exportCount') + '</span></label>'
      + '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.export_table.upload" style="width:auto;min-height:auto;"' + (exportTable.upload ? ' checked' : '') + '><span>' + t('settings.exportUpload') + '</span></label>';
  }

  function getSettingLeafKey(key) {
    return key;
  }

  function selectedForward(glob) {
    var ft = glob.forward_type || {};
    var result = [];
    for (var k in ft) { if (ft[k]) result.push(k); }
    return result;
  }

  function selectedMediaTypes(glob) {
    var mf = glob.message_filter || {};
    var mt = mf.media_types || glob.forward_type || {};
    var result = [];
    for (var k in mt) { if (mt[k]) result.push(k); }
    return result;
  }

  function escAttr(value) {
    return String(value || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function renderCheckCards(baseName, types, selected) {
    return types.map(function(type) {
      return '<label style="flex-direction:row;align-items:center;gap:8px;padding:6px 0;"><input type="checkbox" name="' + baseName + '" value="' + esc(type) + '" style="width:auto;min-height:auto;"' + (selected.indexOf(type) >= 0 ? ' checked' : '') + '><span>' + esc(type) + '</span></label>';
    }).join('');
  }

  /* ====== 覆盖：renderTasks / loadTasks / loadWatches / loadSettings ====== */
  var _origRenderTasks = renderTasks;
  renderTasks = function() {
    try { _origRenderTasks(); } catch(e) {}
    if (state.tasks) renderMobTasks();
  };
  var _origLoadTasks = loadTasks;
  loadTasks = async function() {
    try { await _origLoadTasks(); } catch(e) {}
    if (state.tasks) renderMobTasks();
  };

  var _origLoadWatches = loadWatches;
  loadWatches = async function() {
    try { await _origLoadWatches(); } catch(e) {}
    if (state.watches) renderMobWatches();
  };
  var _origRenderWatches = renderWatches;
  renderWatches = function() {
    try { _origRenderWatches(); } catch(e) {}
    if (state.watches) renderMobWatches();
  };

  var _origLoadSettings = loadSettings;
  loadSettings = async function() {
    try { await _origLoadSettings(); } catch(e) {}
    renderMobSettingsForm();
  };

  /* ====== 事件绑定 ====== */
  $('#language-select').addEventListener('change', function(event) {
    state.lang = event.target.value;
    localStorage.setItem('trmd-lang', state.lang);
    applyLanguageAndRefresh();
    renderMobTasks();
    renderMobWatches();
    renderMobRecords();
    renderMobStatistics();
    renderMobSettingsForm();
  });

  $('#refresh').addEventListener('click', function() {
    loadTasks();
    var activeView = document.querySelector('.mob-view.active');
    if (activeView) {
      var viewId = activeView.id.replace('mob-view-', '');
      if (viewId === 'settings') loadSettings();
      if (viewId === 'watches') loadWatches();
    }
    showToast(t('action.refresh') + ' OK');
  });

  /* Tab 栏点击 */
  $$('.mob-tab').forEach(function(tab) {
    tab.addEventListener('click', function() { mobSwitchView(tab.dataset.mobNav); });
  });

  /* "更多"按钮 -> 打开 Drawer */
  var moreTab = document.querySelector('.mob-tab[data-mob-nav="more"]');
  if (moreTab) moreTab.addEventListener('click', openDrawer);

  /* Drawer 内菜单项点击 */
  $$('[data-mob-drawer-nav]').forEach(function(item) {
    item.addEventListener('click', function() { mobSwitchView(item.dataset.mobDrawerNav); });
  });

  /* Drawer overlay 点击关闭 */
  $('#mob-drawer-overlay').addEventListener('click', function(e) {
    if (e.target === this) closeDrawer();
  });

  /* FAB 点击 */
  $('#mob-fab').addEventListener('click', toggleFabMenu);

  /* FAB 菜单项 */
  $('#mob-fab-new-transfer').addEventListener('click', function() {
    closeFabMenu();
    var collapse = $('#collapse-transfer-form');
    collapse.classList.add('open');
    collapse.scrollIntoView({ behavior: 'smooth' });
  });
  $('#mob-fab-new-watch').addEventListener('click', function() {
    closeFabMenu();
    mobSwitchView('watches');
    var collapse = $('#collapse-watch-form');
    collapse.classList.add('open');
    collapse.scrollIntoView({ behavior: 'smooth' });
  });

  /* 折叠面板切换 */
  $$('.mob-collapse__head').forEach(function(head) {
    head.addEventListener('click', function() { toggleCollapse(head); });
  });

  /* 点击外部关闭 FAB 菜单 */
  document.addEventListener('click', function(e) {
    if (!e.target.closest('#mob-fab') && !e.target.closest('#mob-fab-menu')) {
      closeFabMenu();
    }
  });

  /* 监听类型切换 */
  var watchTypeSelect = $('#mob-watch-type');
  if (watchTypeSelect) {
    watchTypeSelect.addEventListener('change', function() {
      var isForward = this.value === 'forward';
      var textarea = document.querySelector('#mob-watch-source-group textarea[name="source_links"]');
      var input = document.querySelector('#mob-watch-source-group input[name="source_link"]');
      var sourceLabel = $('#mob-watch-source-label').querySelector('span');
      if (isForward) {
        if (textarea) { textarea.style.display = 'none'; textarea.required = false; }
        if (input) { input.style.display = ''; input.required = true; }
        if (sourceLabel) sourceLabel.textContent = t('watches.source');
      } else {
        if (textarea) { textarea.style.display = ''; textarea.required = true; }
        if (input) { input.style.display = 'none'; input.required = false; }
        if (sourceLabel) sourceLabel.textContent = t('watches.sources');
      }
      $('#mob-watch-target-group').style.display = isForward ? '' : 'none';
      $('#mob-watch-comment-group').style.display = isForward ? '' : 'none';
    });
  }

  /* 新建转存表单提交 */
  var transferForm = $('#mob-transfer-form');
  if (transferForm) {
    transferForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      var form = new FormData(this);
      var payload = Object.fromEntries(form.entries());
      payload.start_id = payload.start_id ? Number(payload.start_id) : null;
      payload.end_id = payload.end_id ? Number(payload.end_id) : null;
      payload.include_comment = !!payload.include_comment;
      try {
        await postJson('/api/tasks', payload);
        showToast(t('form.transferCreated'));
        this.reset();
        $('#collapse-transfer-form').classList.remove('open');
        loadTasks();
      } catch (err) {
        showToast(translateApiError(err, 'form.requestFailed'));
      }
    });
  }

  /* 新建监听表单提交 */
  var watchForm = $('#mob-watch-form');
  if (watchForm) {
    watchForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      var form = new FormData(this);
      var payload = Object.fromEntries(form.entries());
      var isForward = payload.type === 'forward';
      if (isForward) {
        delete payload.source_links;
        payload.include_comment = !!payload.include_comment;
      } else {
        delete payload.source_link;
        delete payload.target_link;
        delete payload.include_comment;
        payload.source_links = String(payload.source_links || '').split('\n').map(function(s) { return s.trim(); }).filter(Boolean);
      }
      try {
        await postJson('/api/watches', payload);
        showToast(t('watches.created'));
        this.reset();
        $('#collapse-watch-form').classList.remove('open');
        loadWatches();
      } catch (err) {
        showToast(translateApiError(err, 'form.requestFailed'));
      }
    });
  }

  /* 保存设置 */
  var saveBtn = $('#mob-save-settings');
  if (saveBtn) {
    saveBtn.addEventListener('click', async function() {
      var userPayload = {};
      var globalPayload = {};
      var downloadTypes = [];

      // 收集所有设置区域的 input
      var allInputs = document.querySelectorAll('#mob-settings-path-fields input, #mob-settings-behavior-fields input, #mob-settings-sensitive-fields input, #mob-settings-archive-fields input, #mob-settings-download-types-fields input, #mob-settings-forward-types-fields input, #mob-settings-message-filter-fields input, #mob-settings-exports-fields input');

      allInputs.forEach(function(input) {
        var name = input.name || '';
        if (!name) return;
        var value;
        if (input.type === 'checkbox') {
          value = input.checked;
        } else if (input.type === 'number') {
          value = input.value === '' ? null : Number(input.value);
        } else if (input.type === 'password' && input.value === '') {
          return;
        } else {
          value = input.value;
        }

        // 收集 download_type 多选
        if (name === 'user.download_type' && input.type === 'checkbox' && input.checked) {
          downloadTypes.push(input.value);
          return;
        }
        // 收集 forward_type 多选
        if (name === 'global.forward_type' && input.type === 'checkbox') {
          setPath(globalPayload, 'forward_type.' + input.value, input.checked);
          return;
        }
        // 消息过滤 — 日期范围：datetime-local → timestamp
        if (name === 'global.message_filter.date_range.start_date' || name === 'global.message_filter.date_range.end_date') {
          var ts = input.value ? (new Date(input.value).getTime() / 1000) : null;
          setPath(globalPayload, name.substring(7), ts);
          return;
        }
        // 消息过滤 — 关键词：逗号分隔字符串 → 数组
        if (name === 'global.message_filter.keywords.words') {
          var words = input.value ? input.value.split(',').map(function(s) { return s.trim(); }).filter(Boolean) : [];
          setPath(globalPayload, name.substring(7), words);
          return;
        }

        if (name.startsWith('user.')) {
          setPath(userPayload, name.substring(5), value);
        } else if (name.startsWith('global.')) {
          setPath(globalPayload, name.substring(7), value);
        }
      });

      setPath(userPayload, 'download_type', downloadTypes);

      try {
        await postJson('/api/settings', { user: userPayload, global: globalPayload });
        showToast(t('settings.saved'));
        loadSettings();
      } catch (err) {
        showToast(translateApiError(err, 'form.requestFailed'));
      }
    });
  }

  /* ====== Phase 2: 频道下载 ====== */
  function renderMobRecords() {
    var records = state.records || [];
    var container = $('#mob-records-list');
    if (!records.length) {
      container.innerHTML = '<div class="mob-empty" data-i18n="records.empty">' + t('records.empty') + '</div>';
      return;
    }
    container.innerHTML = records.map(function(r) {
      return '<div class="mob-card">'
        + '<div class="mob-card__head"><span class="mob-card__title">' + esc(r.file_name || r.local_path || '') + '</span></div>'
        + '<div class="mob-card__row"><span class="label">' + t('records.chat') + '</span><span>' + esc(r.source_chat_id || '-') + '</span></div>'
        + '<div class="mob-card__row"><span class="label">' + t('records.message') + '</span><span>' + esc(r.source_message_id || '-') + '</span></div>'
        + '<div class="mob-card__row"><span class="label">' + t('records.size') + '</span><span>' + formatBytes(r.file_size) + '</span></div>'
        + '<div class="mob-card__row"><span class="label">' + t('records.updated') + '</span><span>' + esc(r.updated_at || r.downloaded_at || '') + '</span></div>'
        + '</div>';
    }).join('');
  }

  /* ====== Phase 2: 统计表格 ====== */
  function renderMobStatistics() {
    var stats = state.statistics;
    var container = $('#mob-statistics-list');
    if (!stats || !stats.tables) {
      container.innerHTML = '<div class="mob-empty">' + t('tasks.empty') + '</div>';
      return;
    }
    var tables = stats.tables;
    var html = '';
    var tableNames = { link: t('statistics.link'), count: t('statistics.count'), upload: t('statistics.upload') };
    for (var key in tables) {
      if (!tables.hasOwnProperty(key)) continue;
      var tbl = tables[key];
      html += '<div class="mob-card" style="margin-bottom:10px;">'
        + '<div class="mob-card__row"><span class="label">' + (tableNames[key] || key) + '</span><span>' + t('statistics.available') + ': ' + (tbl.available ? t('statistics.yes') : t('statistics.no')) + '</span></div>'
        + '<div class="mob-card__row"><span class="label">' + t('statistics.rows') + '</span><span>' + (tbl.rows || 0) + '</span></div>'
        + '</div>';
    }
    container.innerHTML = html || '<div class="mob-empty">' + t('tasks.empty') + '</div>';
  }

  /* ====== 覆盖 loadRecords / renderRecords / loadStatistics ====== */
  var _origLoadRecords = loadRecords;
  loadRecords = async function() {
    try { await _origLoadRecords(); } catch(e) {}
    renderMobRecords();
  };
  var _origRenderRecords = renderRecords;
  renderRecords = function() {
    try { _origRenderRecords(); } catch(e) {}
    renderMobRecords();
  };
  var _origLoadStatistics = loadStatistics;
  loadStatistics = async function() {
    try { await _origLoadStatistics(); } catch(e) {}
    renderMobStatistics();
  };

  /* ====== Phase 2 事件绑定 ====== */

  /* 频道下载表单 */
  var channelForm = $('#mob-channel-form');
  if (channelForm) {
    channelForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      var form = new FormData(this);
      var payload = Object.fromEntries(form.entries());
      payload.include_comment = !!payload.include_comment;
      if (payload.start_date) {
        payload.date_range = { start_date: new Date(payload.start_date).getTime() / 1000 };
        delete payload.start_date;
      }
      if (payload.end_date) {
        payload.date_range = payload.date_range || {};
        payload.date_range.end_date = new Date(payload.end_date).getTime() / 1000;
        delete payload.end_date;
      }
      if (payload.keywords) {
        payload.keywords = String(payload.keywords).split(',').map(function(s) { return s.trim(); }).filter(Boolean);
      } else {
        payload.keywords = [];
      }
      payload.download_type = Array.from(document.querySelectorAll('#mob-channel-download-types input[name="download_type"]:checked')).map(function(el) { return el.value; });
      try {
        await postJson('/api/channel-downloads', payload);
        showToast(t('channel.accepted'));
        this.reset();
        $('#collapse-channel-form').classList.remove('open');
      } catch (err) {
        showToast(translateApiError(err, 'form.requestFailed'));
      }
    });
  }

  /* 本地上传表单 */
  var uploadForm = $('#mob-upload-form');
  if (uploadForm) {
    uploadForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      var form = new FormData(this);
      var payload = Object.fromEntries(form.entries());
      payload.recursive = !!payload.recursive;
      try {
        await postJson('/api/uploads', payload);
        showToast(t('uploads.accepted'));
        this.reset();
        $('#collapse-upload-form').classList.remove('open');
      } catch (err) {
        showToast(translateApiError(err, 'form.requestFailed'));
      }
    });
  }

  /* 统计导出 */
  /* 已通过 loadStatistics 覆盖自动渲染 */

  /* ====== 初始加载（由 checkAuthStatus 驱动） ====== */
</script>
</body>
</html>"""

LOGIN_PAGE_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TRMD · 登录</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>/*! tailwindcss v4.1.18 | MIT License | https://tailwindcss.com */
@layer properties{@supports (((-webkit-hyphens:none)) and (not (margin-trim:inline))) or ((-moz-orient:inline) and (not (color:rgb(from red r g b)))){*,:before,:after,::backdrop{--tw-rotate-x:initial;--tw-rotate-y:initial;--tw-rotate-z:initial;--tw-skew-x:initial;--tw-skew-y:initial;--tw-border-style:solid;--tw-font-weight:initial;--tw-shadow:0 0 #0000;--tw-shadow-color:initial;--tw-shadow-alpha:100%;--tw-inset-shadow:0 0 #0000;--tw-inset-shadow-color:initial;--tw-inset-shadow-alpha:100%;--tw-ring-color:initial;--tw-ring-shadow:0 0 #0000;--tw-inset-ring-color:initial;--tw-inset-ring-shadow:0 0 #0000;--tw-ring-inset:initial;--tw-ring-offset-width:0px;--tw-ring-offset-color:#fff;--tw-ring-offset-shadow:0 0 #0000;--tw-outline-style:solid;--tw-blur:initial;--tw-brightness:initial;--tw-contrast:initial;--tw-grayscale:initial;--tw-hue-rotate:initial;--tw-invert:initial;--tw-opacity:initial;--tw-saturate:initial;--tw-sepia:initial;--tw-drop-shadow:initial;--tw-drop-shadow-color:initial;--tw-drop-shadow-alpha:100%;--tw-drop-shadow-size:initial;--tw-backdrop-blur:initial;--tw-backdrop-brightness:initial;--tw-backdrop-contrast:initial;--tw-backdrop-grayscale:initial;--tw-backdrop-hue-rotate:initial;--tw-backdrop-invert:initial;--tw-backdrop-opacity:initial;--tw-backdrop-saturate:initial;--tw-backdrop-sepia:initial;--tw-tracking:initial;--tw-duration:initial;--tw-leading:initial}}}@layer theme{:root,:host{--font-sans:ui-sans-serif,system-ui,sans-serif,"Apple Color Emoji","Segoe UI Emoji","Segoe UI Symbol","Noto Color Emoji";--font-mono:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono","Courier New",monospace;--color-red-200:oklch(88.5% .062 18.334);--color-red-300:oklch(80.8% .114 19.571);--color-orange-50:oklch(98% .016 73.684);--color-slate-100:oklch(96.8% .007 247.896);--color-slate-300:oklch(86.9% .022 252.894);--color-slate-500:oklch(55.4% .046 257.417);--color-black:#000;--color-white:#fff;--spacing:.25rem;--text-xs:.75rem;--text-xs--line-height:calc(1/.75);--text-sm:.875rem;--text-sm--line-height:calc(1.25/.875);--text-lg:1.125rem;--text-lg--line-height:calc(1.75/1.125);--text-xl:1.25rem;--text-xl--line-height:calc(1.75/1.25);--text-2xl:1.5rem;--text-2xl--line-height:calc(2/1.5);--font-weight-medium:500;--font-weight-semibold:600;--font-weight-bold:700;--font-weight-extrabold:800;--leading-tight:1.25;--radius-lg:.5rem;--radius-xl:.75rem;--animate-spin:spin 1s linear infinite;--default-transition-duration:.15s;--default-transition-timing-function:cubic-bezier(.4,0,.2,1);--default-font-family:var(--font-sans);--default-mono-font-family:var(--font-mono);--color-primary:#2563eb;--color-primary-light:#3b82f6;--color-primary-soft:#eff6ff;--color-primary-ghost:#dbeafe;--color-primary-dark:#1d4ed8;--color-bg:#f0f4ff;--color-surface:#fff;--color-surface-alt:#f8fafc;--color-surface-hover:#f1f5f9;--color-text:#1e293b;--color-text-secondary:#475569;--color-muted:#94a3b8;--color-line:#e2e8f0;--color-line-light:#f1f5f9;--color-success:#10b981;--color-success-bg:#ecfdf5;--color-warning:#f59e0b;--color-danger:#ef4444;--color-danger-bg:#fef2f2;--color-cta:#f97316;--font-heading:"Poppins",ui-sans-serif,system-ui,sans-serif;--font-body:"Open Sans",ui-sans-serif,system-ui,sans-serif}}@layer base{*,:after,:before,::backdrop{box-sizing:border-box;border:0 solid;margin:0;padding:0}::file-selector-button{box-sizing:border-box;border:0 solid;margin:0;padding:0}html,:host{-webkit-text-size-adjust:100%;tab-size:4;line-height:1.5;font-family:var(--default-font-family,ui-sans-serif,system-ui,sans-serif,"Apple Color Emoji","Segoe UI Emoji","Segoe UI Symbol","Noto Color Emoji");font-feature-settings:var(--default-font-feature-settings,normal);font-variation-settings:var(--default-font-variation-settings,normal);-webkit-tap-highlight-color:transparent}hr{height:0;color:inherit;border-top-width:1px}abbr:where([title]){-webkit-text-decoration:underline dotted;text-decoration:underline dotted}h1,h2,h3,h4,h5,h6{font-size:inherit;font-weight:inherit}a{color:inherit;-webkit-text-decoration:inherit;-webkit-text-decoration:inherit;-webkit-text-decoration:inherit;text-decoration:inherit}b,strong{font-weight:bolder}code,kbd,samp,pre{font-family:var(--default-mono-font-family,ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono","Courier New",monospace);font-feature-settings:var(--default-mono-font-feature-settings,normal);font-variation-settings:var(--default-mono-font-variation-settings,normal);font-size:1em}small{font-size:80%}sub,sup{vertical-align:baseline;font-size:75%;line-height:0;position:relative}sub{bottom:-.25em}sup{top:-.5em}table{text-indent:0;border-color:inherit;border-collapse:collapse}:-moz-focusring{outline:auto}progress{vertical-align:baseline}summary{display:list-item}ol,ul,menu{list-style:none}img,svg,video,canvas,audio,iframe,embed,object{vertical-align:middle;display:block}img,video{max-width:100%;height:auto}button,input,select,optgroup,textarea{font:inherit;font-feature-settings:inherit;font-variation-settings:inherit;letter-spacing:inherit;color:inherit;opacity:1;background-color:#0000;border-radius:0}::file-selector-button{font:inherit;font-feature-settings:inherit;font-variation-settings:inherit;letter-spacing:inherit;color:inherit;opacity:1;background-color:#0000;border-radius:0}:where(select:is([multiple],[size])) optgroup{font-weight:bolder}:where(select:is([multiple],[size])) optgroup option{padding-inline-start:20px}::file-selector-button{margin-inline-end:4px}::placeholder{opacity:1}@supports (not ((-webkit-appearance:-apple-pay-button))) or (contain-intrinsic-size:1px){::placeholder{color:currentColor}@supports (color:color-mix(in lab, red, red)){::placeholder{color:color-mix(in oklab,currentcolor 50%,transparent)}}}textarea{resize:vertical}::-webkit-search-decoration{-webkit-appearance:none}::-webkit-date-and-time-value{min-height:1lh;text-align:inherit}::-webkit-datetime-edit{display:inline-flex}::-webkit-datetime-edit-fields-wrapper{padding:0}::-webkit-datetime-edit{padding-block:0}::-webkit-datetime-edit-year-field{padding-block:0}::-webkit-datetime-edit-month-field{padding-block:0}::-webkit-datetime-edit-day-field{padding-block:0}::-webkit-datetime-edit-hour-field{padding-block:0}::-webkit-datetime-edit-minute-field{padding-block:0}::-webkit-datetime-edit-second-field{padding-block:0}::-webkit-datetime-edit-millisecond-field{padding-block:0}::-webkit-datetime-edit-meridiem-field{padding-block:0}::-webkit-calendar-picker-indicator{line-height:1}:-moz-ui-invalid{box-shadow:none}button,input:where([type=button],[type=reset],[type=submit]){appearance:button}::file-selector-button{appearance:button}::-webkit-inner-spin-button{height:auto}::-webkit-outer-spin-button{height:auto}[hidden]:where(:not([hidden=until-found])){display:none!important}html{font-family:var(--font-body);color:var(--color-text);background:var(--color-bg);font-size:14px}body{min-height:100vh;display:flex}button,input,select,textarea{font-family:inherit;font-size:inherit}button{cursor:pointer}button:disabled{cursor:not-allowed;opacity:.55}}@layer components{.sidebar{top:calc(var(--spacing)*0);z-index:50;border-right-style:var(--tw-border-style);border-right-width:1px;border-color:var(--color-line);background-color:var(--color-white);width:250px;height:100vh;padding-inline:calc(var(--spacing)*4);padding-block:calc(var(--spacing)*6);flex-direction:column;display:flex;position:sticky}.sidebar-brand{margin-bottom:calc(var(--spacing)*3);align-items:center;gap:calc(var(--spacing)*3);border-bottom-style:var(--tw-border-style);border-bottom-width:1px;border-color:var(--color-line);padding-bottom:calc(var(--spacing)*5);display:flex}.sidebar-brand-mark{height:calc(var(--spacing)*10);width:calc(var(--spacing)*10);font-size:var(--text-lg);line-height:var(--tw-leading,var(--text-lg--line-height));--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold);color:var(--color-white);background:linear-gradient(135deg,var(--color-primary),var(--color-primary-light));font-family:var(--font-heading);border-radius:10px;justify-content:center;align-items:center;display:flex;box-shadow:0 4px 10px #2563eb4d}.sidebar-nav-section{flex:1;overflow-y:auto}.sidebar-nav-label{padding-inline:calc(var(--spacing)*2.5);padding-top:calc(var(--spacing)*4);padding-bottom:calc(var(--spacing)*2);--tw-font-weight:var(--font-weight-semibold);font-size:11px;font-weight:var(--font-weight-semibold);--tw-tracking:.08em;letter-spacing:.08em;color:var(--color-muted);text-transform:uppercase}.sidebar-nav-item{cursor:pointer;align-items:center;gap:calc(var(--spacing)*2.5);border-style:var(--tw-border-style);width:100%;padding-inline:calc(var(--spacing)*3);padding-block:calc(var(--spacing)*2.5);text-align:left;--tw-font-weight:var(--font-weight-medium);font-size:13px;font-weight:var(--font-weight-medium);color:var(--color-text-secondary);transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;background-color:#0000;border-width:0;border-radius:8px;font-family:inherit;transition-duration:.15s;display:flex}.sidebar-nav-item:hover{background-color:var(--color-primary-soft);color:var(--color-primary)}.sidebar-nav-item.active{background-color:var(--color-primary-soft);--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-primary)}.sidebar-nav-item svg{flex-shrink:0;width:18px;height:18px}.sidebar-nav-badge{background-color:var(--color-primary-ghost);padding-inline:calc(var(--spacing)*2);padding-block:calc(var(--spacing)*.5);--tw-font-weight:var(--font-weight-bold);font-size:11px;font-weight:var(--font-weight-bold);color:var(--color-primary);border-radius:3.40282e38px;margin-left:auto}.sidebar-footer{margin-top:calc(var(--spacing)*2);gap:calc(var(--spacing)*1.5);border-top-style:var(--tw-border-style);border-top-width:1px;border-color:var(--color-line);padding-top:calc(var(--spacing)*4);flex-direction:column;display:flex}.sidebar-footer-info{align-items:center;gap:calc(var(--spacing)*2);padding-inline:calc(var(--spacing)*2);padding-block:calc(var(--spacing)*1);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));color:var(--color-text-secondary);display:flex}.sidebar-status-dot{height:calc(var(--spacing)*2);width:calc(var(--spacing)*2);background:var(--color-success);border-radius:3.40282e38px;flex-shrink:0;box-shadow:0 0 0 3px #10b98133}.sidebar-version{padding-inline:calc(var(--spacing)*2);color:var(--color-muted);opacity:.7;font-size:11px}.main-content{min-width:calc(var(--spacing)*0);gap:calc(var(--spacing)*6);padding:calc(var(--spacing)*7);flex-direction:column;flex:1;display:flex}.topbar{justify-content:space-between;align-items:flex-start;gap:calc(var(--spacing)*4);display:flex}.topbar h1{font-size:var(--text-2xl);line-height:var(--tw-leading,var(--text-2xl--line-height));--tw-leading:var(--leading-tight);line-height:var(--leading-tight);--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold);color:var(--color-text);font-family:var(--font-heading)}.topbar p{margin-top:calc(var(--spacing)*1);color:var(--color-muted);font-size:13px}.btn{cursor:pointer;align-items:center;gap:calc(var(--spacing)*1.5);border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);padding-inline:calc(var(--spacing)*4);padding-block:calc(var(--spacing)*2);--tw-font-weight:var(--font-weight-medium);font-size:13px;font-weight:var(--font-weight-medium);white-space:nowrap;color:var(--color-text);transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;border-radius:6px;font-family:inherit;transition-duration:.15s;display:inline-flex}.btn:hover{border-color:var(--color-primary-light);background-color:var(--color-primary-soft)}.btn svg{height:calc(var(--spacing)*4);width:calc(var(--spacing)*4);flex-shrink:0}.btn-primary{border-color:var(--color-primary);background-color:var(--color-primary);--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-white)}.btn-primary:hover{border-color:var(--color-primary-dark);background-color:var(--color-primary-dark);color:var(--color-white)}.btn-danger{border-color:var(--color-red-200);color:var(--color-danger)}.btn-danger:hover{border-color:var(--color-danger);background-color:var(--color-danger-bg);color:var(--color-danger)}.btn-sm{padding-inline:calc(var(--spacing)*2.5);padding-block:calc(var(--spacing)*1);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height))}.btn-icon{width:34px;height:34px;padding:calc(var(--spacing)*0);justify-content:center}.stat-grid{gap:calc(var(--spacing)*4);grid-template-columns:repeat(4,minmax(0,1fr));display:grid}.stat-card{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);--tw-shadow:0 1px 3px 0 var(--tw-shadow-color,#0000001a),0 1px 2px -1px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow);transition-property:box-shadow;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.2s;border-radius:12px;justify-content:space-between;align-items:flex-start;padding:18px;transition-duration:.2s;display:flex}.stat-card:hover{border-color:var(--color-primary-ghost);--tw-shadow:0 4px 6px -1px var(--tw-shadow-color,#0000001a),0 2px 4px -2px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow)}.stat-card-icon{height:calc(var(--spacing)*10);width:calc(var(--spacing)*10);border-radius:8px;flex-shrink:0;justify-content:center;align-items:center;display:flex}.stat-card-icon.blue{background-color:var(--color-primary-soft);color:var(--color-primary)}.stat-card-icon.green{background-color:var(--color-success-bg);color:var(--color-success)}.stat-card-icon.orange{background-color:var(--color-orange-50);color:var(--color-cta)}.stat-card-icon.red{background-color:var(--color-danger-bg);color:var(--color-danger)}.stat-card-icon svg{height:calc(var(--spacing)*5);width:calc(var(--spacing)*5)}.stat-card-value{text-align:right;--tw-leading:var(--leading-tight);font-size:28px;line-height:var(--leading-tight);--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold);color:var(--color-text);font-family:var(--font-heading)}.stat-card-label{margin-top:calc(var(--spacing)*1);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-medium);font-weight:var(--font-weight-medium);color:var(--color-muted)}.panel{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);--tw-shadow:0 1px 3px 0 var(--tw-shadow-color,#0000001a),0 1px 2px -1px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow);border-radius:12px;flex-direction:column;display:flex;overflow:hidden}.panel-header{border-bottom-style:var(--tw-border-style);border-bottom-width:1px;border-color:var(--color-line);background-color:var(--color-surface-alt);padding-inline:18px;padding-block:calc(var(--spacing)*3.5);justify-content:space-between;align-items:center;display:flex}.panel-header h3{font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-text);font-family:var(--font-heading)}.panel-body{flex:1;padding:18px;overflow-y:auto}.panel-tabs{gap:calc(var(--spacing)*.5);display:flex}.panel-tab{cursor:pointer;border-style:var(--tw-border-style);padding-inline:calc(var(--spacing)*2.5);padding-block:calc(var(--spacing)*1);--tw-font-weight:var(--font-weight-medium);font-size:11px;font-weight:var(--font-weight-medium);color:var(--color-text-secondary);transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.1s;background-color:#0000;border-width:0;border-radius:.25rem;font-family:inherit;transition-duration:.1s}.panel-tab:hover{background-color:var(--color-primary-soft);color:var(--color-primary)}.panel-tab.active{background-color:var(--color-primary-soft);--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);color:var(--color-primary)}.form-group{margin-bottom:calc(var(--spacing)*3.5)}.form-label{margin-bottom:calc(var(--spacing)*1.5);font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height));--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold);--tw-tracking:.04em;letter-spacing:.04em;color:var(--color-muted);text-transform:uppercase;display:block}.form-input,.form-select{height:calc(var(--spacing)*10);border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);width:100%;padding-inline:calc(var(--spacing)*3);color:var(--color-text);transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;--tw-outline-style:none;border-radius:6px;outline-style:none;font-family:inherit;font-size:13px;transition-duration:.15s}.form-input:focus,.form-select:focus{border-color:var(--color-primary);box-shadow:0 0 0 3px #2563eb1f}.form-row{gap:calc(var(--spacing)*2.5);grid-template-columns:repeat(2,minmax(0,1fr));display:grid}.form-submit{margin-top:calc(var(--spacing)*1.5);height:calc(var(--spacing)*10);cursor:pointer;justify-content:center;align-items:center;gap:calc(var(--spacing)*1.5);border-style:var(--tw-border-style);background-color:var(--color-primary);--tw-font-weight:var(--font-weight-semibold);width:100%;font-size:13px;font-weight:var(--font-weight-semibold);color:var(--color-white);transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;border-width:0;border-radius:6px;font-family:inherit;transition-duration:.15s;display:flex}.form-submit:hover{background-color:var(--color-primary-dark)}.data-table{border-collapse:collapse;width:100%;font-size:13px}.data-table thead th{top:calc(var(--spacing)*0);border-bottom-style:var(--tw-border-style);border-bottom-width:2px;border-color:var(--color-line);background-color:var(--color-surface-alt);padding-inline:calc(var(--spacing)*3);padding-block:calc(var(--spacing)*2.5);text-align:left;--tw-font-weight:var(--font-weight-semibold);font-size:11px;font-weight:var(--font-weight-semibold);--tw-tracking:.05em;letter-spacing:.05em;white-space:nowrap;color:var(--color-muted);text-transform:uppercase;position:sticky}.data-table tbody td{border-bottom-style:var(--tw-border-style);border-bottom-width:1px;border-color:var(--color-line-light);padding-inline:calc(var(--spacing)*3);padding-block:calc(var(--spacing)*2.5);vertical-align:middle;font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height))}.data-table tbody tr{cursor:pointer;transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:75ms;transition-duration:75ms}.data-table tbody tr:hover{background-color:var(--color-surface-hover)}.data-table tbody tr.selected{background-color:var(--color-primary-soft)}.badge{padding-inline:calc(var(--spacing)*2.5);padding-block:calc(var(--spacing)*.5);--tw-font-weight:var(--font-weight-semibold);font-size:11px;font-weight:var(--font-weight-semibold);border-radius:3.40282e38px;align-items:center;display:inline-flex}.badge-running{background-color:var(--color-primary-soft);color:var(--color-primary)}.badge-success{background-color:var(--color-success-bg);color:var(--color-success)}.badge-failed{background-color:var(--color-danger-bg);color:var(--color-danger)}.badge-pending{background-color:var(--color-orange-50);color:var(--color-cta)}.badge-paused,.badge-skipped{background-color:var(--color-slate-100);color:var(--color-slate-500)}.progress-bar{height:calc(var(--spacing)*1.5);background-color:var(--color-slate-100);border-radius:3.40282e38px;overflow:hidden}.progress-fill{height:100%;transition-property:all;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.3s;background:linear-gradient(90deg,var(--color-primary-light),var(--color-primary));border-radius:3.40282e38px;transition-duration:.3s}.status-dot{margin-right:calc(var(--spacing)*1.5);height:calc(var(--spacing)*1.5);width:calc(var(--spacing)*1.5);vertical-align:middle;border-radius:3.40282e38px;display:inline-block}.status-dot.running{background-color:var(--color-primary)}.status-dot.success{background-color:var(--color-success)}.status-dot.failed{background-color:var(--color-danger)}.status-dot.pending{background-color:var(--color-warning)}.status-dot.paused{background-color:var(--color-slate-300)}.activity-item{gap:calc(var(--spacing)*2);border-bottom-style:var(--tw-border-style);border-bottom-width:1px;border-color:var(--color-line-light);padding-block:calc(var(--spacing)*1.5);--tw-leading:1.4;font-size:11px;line-height:1.4;display:flex}.activity-item:last-child{border-bottom-style:var(--tw-border-style);border-bottom-width:0}.activity-time{white-space:nowrap;min-width:44px;color:var(--color-muted);font-family:ui-monospace,monospace;font-size:10px}.activity-badge{--tw-font-weight:var(--font-weight-semibold);font-size:10px;font-weight:var(--font-weight-semibold);white-space:nowrap}.activity-badge.ok{color:var(--color-success)}.activity-badge.warn{color:var(--color-warning)}.activity-badge.err{color:var(--color-danger)}.view{display:none}.view.active{gap:18px;display:grid}.login-page{background-color:var(--color-bg);min-height:100vh;padding:calc(var(--spacing)*6);justify-content:center;align-items:center;display:flex}.login-card{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);width:100%;max-width:448px;padding:calc(var(--spacing)*10);--tw-shadow:0 10px 15px -3px var(--tw-shadow-color,#0000001a),0 4px 6px -4px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow);border-radius:16px}.login-brand{margin-bottom:calc(var(--spacing)*8);text-align:center}.login-brand-mark{margin-bottom:calc(var(--spacing)*4);--tw-font-weight:var(--font-weight-bold);width:52px;height:52px;font-size:24px;font-weight:var(--font-weight-bold);color:var(--color-white);background:linear-gradient(135deg,var(--color-primary),var(--color-primary-light));font-family:var(--font-heading);border-radius:14px;justify-content:center;align-items:center;display:inline-flex}.login-brand h1{--tw-font-weight:var(--font-weight-extrabold);font-size:28px;font-weight:var(--font-weight-extrabold);color:var(--color-text);font-family:var(--font-heading)}.login-brand p{margin-top:calc(var(--spacing)*1.5);color:var(--color-muted);font-size:13px}.login-error{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-red-300);background-color:var(--color-danger-bg);padding-inline:calc(var(--spacing)*3.5);padding-block:calc(var(--spacing)*2.5);color:var(--color-danger);border-radius:8px;margin-bottom:18px;font-size:13px;display:none}.login-error.visible{display:block}.login-field{margin-bottom:calc(var(--spacing)*5)}.login-field label{margin-bottom:calc(var(--spacing)*2);--tw-font-weight:var(--font-weight-medium);font-size:13px;font-weight:var(--font-weight-medium);color:var(--color-text);display:block}.login-field input{border-style:var(--tw-border-style);border-width:1px;border-color:var(--color-line);background-color:var(--color-surface);width:100%;height:46px;padding-inline:calc(var(--spacing)*3.5);font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height));color:var(--color-text);transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;--tw-outline-style:none;border-radius:8px;outline-style:none;font-family:inherit;transition-duration:.15s}.login-field input:focus{border-color:var(--color-primary);box-shadow:0 0 0 3px #2563eb1f}.login-options{margin-bottom:calc(var(--spacing)*7);justify-content:space-between;align-items:center;display:flex}.login-checkbox{cursor:pointer;align-items:center;gap:calc(var(--spacing)*2);color:var(--color-muted);-webkit-user-select:none;user-select:none;font-size:13px;display:flex}.login-submit{cursor:pointer;justify-content:center;align-items:center;gap:calc(var(--spacing)*2);border-style:var(--tw-border-style);background-color:var(--color-primary);--tw-font-weight:var(--font-weight-semibold);width:100%;height:46px;font-size:15px;font-weight:var(--font-weight-semibold);color:var(--color-white);transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.15s;border-width:0;border-radius:8px;font-family:inherit;transition-duration:.15s;display:flex}.login-submit:hover{background-color:var(--color-primary-dark)}.login-submit:disabled{cursor:not-allowed;opacity:.7}.login-submit:disabled:hover{background-color:var(--color-primary)}.spinner{width:18px;height:18px;animation:var(--animate-spin);border-style:var(--tw-border-style);border-width:2px;border-color:#ffffff4d;border-radius:3.40282e38px;flex-shrink:0}@supports (color:color-mix(in lab, red, red)){.spinner{border-color:color-mix(in oklab,var(--color-white)30%,transparent)}}.spinner{border-top-color:var(--color-white)}.watch-overlay{pointer-events:none;inset:calc(var(--spacing)*0);z-index:999;background-color:#00000059;justify-content:center;align-items:center;display:flex;position:fixed}@supports (color:color-mix(in lab, red, red)){.watch-overlay{background-color:color-mix(in oklab,var(--color-black)35%,transparent)}}.watch-overlay{opacity:0;transition-property:opacity;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration));--tw-duration:.2s;transition-duration:.2s}.watch-overlay.open{pointer-events:auto;opacity:1}.watch-dialog{gap:calc(var(--spacing)*4);background-color:var(--color-surface);width:440px;max-width:calc(100vw - 32px);padding:calc(var(--spacing)*6);--tw-shadow:0 10px 15px -3px var(--tw-shadow-color,#0000001a),0 4px 6px -4px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow);border-radius:10px;display:grid}@media (max-width:1200px){.stat-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media (max-width:960px){.sidebar{display:none}.main-content{padding:calc(var(--spacing)*4)}}}@layer utilities{.collapse{visibility:collapse}.invisible{visibility:hidden}.visible{visibility:visible}.sr-only{clip-path:inset(50%);white-space:nowrap;border-width:0;width:1px;height:1px;margin:-1px;padding:0;position:absolute;overflow:hidden}.absolute{position:absolute}.fixed{position:fixed}.relative{position:relative}.static{position:static}.sticky{position:sticky}.bottom-0{bottom:calc(var(--spacing)*0)}.container{width:100%}@media (min-width:40rem){.container{max-width:40rem}}@media (min-width:48rem){.container{max-width:48rem}}@media (min-width:64rem){.container{max-width:64rem}}@media (min-width:80rem){.container{max-width:80rem}}@media (min-width:96rem){.container{max-width:96rem}}.mt-1{margin-top:calc(var(--spacing)*1)}.mt-2{margin-top:calc(var(--spacing)*2)}.mt-3{margin-top:calc(var(--spacing)*3)}.mt-4{margin-top:calc(var(--spacing)*4)}.mb-2{margin-bottom:calc(var(--spacing)*2)}.mb-3{margin-bottom:calc(var(--spacing)*3)}.mb-4{margin-bottom:calc(var(--spacing)*4)}.ml-1{margin-left:calc(var(--spacing)*1)}.block{display:block}.contents{display:contents}.flex{display:flex}.grid{display:grid}.hidden{display:none}.inline-flex{display:inline-flex}.table{display:table}.h-4{height:calc(var(--spacing)*4)}.w-4{width:calc(var(--spacing)*4)}.max-w-\[160px\]{max-width:160px}.max-w-\[180px\]{max-width:180px}.max-w-\[200px\]{max-width:200px}.max-w-\[240px\]{max-width:240px}.flex-shrink{flex-shrink:1}.border-collapse{border-collapse:collapse}.transform{transform:var(--tw-rotate-x,)var(--tw-rotate-y,)var(--tw-rotate-z,)var(--tw-skew-x,)var(--tw-skew-y,)}.cursor-pointer{cursor:pointer}.resize{resize:both}.grid-cols-2{grid-template-columns:repeat(2,minmax(0,1fr))}.flex-wrap{flex-wrap:wrap}.items-center{align-items:center}.justify-between{justify-content:space-between}.gap-1{gap:calc(var(--spacing)*1)}.gap-2{gap:calc(var(--spacing)*2)}.gap-3{gap:calc(var(--spacing)*3)}.gap-5{gap:calc(var(--spacing)*5)}.overflow-hidden{overflow:hidden}.overflow-x-auto{overflow-x:auto}.rounded{border-radius:.25rem}.rounded-lg{border-radius:var(--radius-lg)}.border{border-style:var(--tw-border-style);border-width:1px}.border-t{border-top-style:var(--tw-border-style);border-top-width:1px}.border-line{border-color:var(--color-line)}.bg-surface-alt{background-color:var(--color-surface-alt)}.bg-white{background-color:var(--color-white)}.p-4{padding:calc(var(--spacing)*4)}.p-8{padding:calc(var(--spacing)*8)}.py-3{padding-block:calc(var(--spacing)*3)}.pt-3{padding-top:calc(var(--spacing)*3)}.text-center{text-align:center}.text-right{text-align:right}.font-mono{font-family:var(--font-mono)}.text-sm{font-size:var(--text-sm);line-height:var(--tw-leading,var(--text-sm--line-height))}.text-xl{font-size:var(--text-xl);line-height:var(--tw-leading,var(--text-xl--line-height))}.text-xs{font-size:var(--text-xs);line-height:var(--tw-leading,var(--text-xs--line-height))}.text-\[10px\]{font-size:10px}.text-\[11px\]{font-size:11px}.text-\[12px\]{font-size:12px}.text-\[13px\]{font-size:13px}.font-bold{--tw-font-weight:var(--font-weight-bold);font-weight:var(--font-weight-bold)}.font-semibold{--tw-font-weight:var(--font-weight-semibold);font-weight:var(--font-weight-semibold)}.text-ellipsis{text-overflow:ellipsis}.whitespace-nowrap{white-space:nowrap}.text-danger{color:var(--color-danger)}.text-muted{color:var(--color-muted)}.text-primary{color:var(--color-primary)}.text-success{color:var(--color-success)}.text-text{color:var(--color-text)}.overline{text-decoration-line:overline}.underline{text-decoration-line:underline}.shadow{--tw-shadow:0 1px 3px 0 var(--tw-shadow-color,#0000001a),0 1px 2px -1px var(--tw-shadow-color,#0000001a);box-shadow:var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow)}.outline{outline-style:var(--tw-outline-style);outline-width:1px}.grayscale{--tw-grayscale:grayscale(100%);filter:var(--tw-blur,)var(--tw-brightness,)var(--tw-contrast,)var(--tw-grayscale,)var(--tw-hue-rotate,)var(--tw-invert,)var(--tw-saturate,)var(--tw-sepia,)var(--tw-drop-shadow,)}.invert{--tw-invert:invert(100%);filter:var(--tw-blur,)var(--tw-brightness,)var(--tw-contrast,)var(--tw-grayscale,)var(--tw-hue-rotate,)var(--tw-invert,)var(--tw-saturate,)var(--tw-sepia,)var(--tw-drop-shadow,)}.filter{filter:var(--tw-blur,)var(--tw-brightness,)var(--tw-contrast,)var(--tw-grayscale,)var(--tw-hue-rotate,)var(--tw-invert,)var(--tw-saturate,)var(--tw-sepia,)var(--tw-drop-shadow,)}.backdrop-filter{-webkit-backdrop-filter:var(--tw-backdrop-blur,)var(--tw-backdrop-brightness,)var(--tw-backdrop-contrast,)var(--tw-backdrop-grayscale,)var(--tw-backdrop-hue-rotate,)var(--tw-backdrop-invert,)var(--tw-backdrop-opacity,)var(--tw-backdrop-saturate,)var(--tw-backdrop-sepia,);backdrop-filter:var(--tw-backdrop-blur,)var(--tw-backdrop-brightness,)var(--tw-backdrop-contrast,)var(--tw-backdrop-grayscale,)var(--tw-backdrop-hue-rotate,)var(--tw-backdrop-invert,)var(--tw-backdrop-opacity,)var(--tw-backdrop-saturate,)var(--tw-backdrop-sepia,)}.transition{transition-property:color,background-color,border-color,outline-color,text-decoration-color,fill,stroke,--tw-gradient-from,--tw-gradient-via,--tw-gradient-to,opacity,box-shadow,transform,translate,scale,rotate,filter,-webkit-backdrop-filter,backdrop-filter,display,content-visibility,overlay,pointer-events;transition-timing-function:var(--tw-ease,var(--default-transition-timing-function));transition-duration:var(--tw-duration,var(--default-transition-duration))}.select-all{-webkit-user-select:all;user-select:all}.scrollbar-thin{scrollbar-width:thin;scrollbar-color:var(--color-line)transparent}}@property --tw-rotate-x{syntax:"*";inherits:false}@property --tw-rotate-y{syntax:"*";inherits:false}@property --tw-rotate-z{syntax:"*";inherits:false}@property --tw-skew-x{syntax:"*";inherits:false}@property --tw-skew-y{syntax:"*";inherits:false}@property --tw-border-style{syntax:"*";inherits:false;initial-value:solid}@property --tw-font-weight{syntax:"*";inherits:false}@property --tw-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-shadow-color{syntax:"*";inherits:false}@property --tw-shadow-alpha{syntax:"<percentage>";inherits:false;initial-value:100%}@property --tw-inset-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-inset-shadow-color{syntax:"*";inherits:false}@property --tw-inset-shadow-alpha{syntax:"<percentage>";inherits:false;initial-value:100%}@property --tw-ring-color{syntax:"*";inherits:false}@property --tw-ring-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-inset-ring-color{syntax:"*";inherits:false}@property --tw-inset-ring-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-ring-inset{syntax:"*";inherits:false}@property --tw-ring-offset-width{syntax:"<length>";inherits:false;initial-value:0}@property --tw-ring-offset-color{syntax:"*";inherits:false;initial-value:#fff}@property --tw-ring-offset-shadow{syntax:"*";inherits:false;initial-value:0 0 #0000}@property --tw-outline-style{syntax:"*";inherits:false;initial-value:solid}@property --tw-blur{syntax:"*";inherits:false}@property --tw-brightness{syntax:"*";inherits:false}@property --tw-contrast{syntax:"*";inherits:false}@property --tw-grayscale{syntax:"*";inherits:false}@property --tw-hue-rotate{syntax:"*";inherits:false}@property --tw-invert{syntax:"*";inherits:false}@property --tw-opacity{syntax:"*";inherits:false}@property --tw-saturate{syntax:"*";inherits:false}@property --tw-sepia{syntax:"*";inherits:false}@property --tw-drop-shadow{syntax:"*";inherits:false}@property --tw-drop-shadow-color{syntax:"*";inherits:false}@property --tw-drop-shadow-alpha{syntax:"<percentage>";inherits:false;initial-value:100%}@property --tw-drop-shadow-size{syntax:"*";inherits:false}@property --tw-backdrop-blur{syntax:"*";inherits:false}@property --tw-backdrop-brightness{syntax:"*";inherits:false}@property --tw-backdrop-contrast{syntax:"*";inherits:false}@property --tw-backdrop-grayscale{syntax:"*";inherits:false}@property --tw-backdrop-hue-rotate{syntax:"*";inherits:false}@property --tw-backdrop-invert{syntax:"*";inherits:false}@property --tw-backdrop-opacity{syntax:"*";inherits:false}@property --tw-backdrop-saturate{syntax:"*";inherits:false}@property --tw-backdrop-sepia{syntax:"*";inherits:false}@property --tw-tracking{syntax:"*";inherits:false}@property --tw-duration{syntax:"*";inherits:false}@property --tw-leading{syntax:"*";inherits:false}@keyframes spin{to{transform:rotate(360deg)}}</style>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--color-bg, #F0F4FF);
    color: var(--color-text, #1E293B);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    font-family: 'Open Sans', ui-sans-serif, system-ui, sans-serif;
    font-size: 14px;
  }
  .login-page {
    width: 100%;
    max-width: 448px;
    display: grid;
    gap: 32px;
  }
  .login-brand {
    text-align: center;
    animation: fadeIn .5s ease both;
  }
  .login-brand-mark {
    width: 52px; height: 52px;
    border-radius: 14px;
    display: inline-grid;
    place-items: center;
    color: #fff;
    font-family: 'Poppins', sans-serif;
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 16px;
    background: linear-gradient(135deg, #2563EB, #3B82F6);
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3);
  }
  .login-brand h1 {
    font-family: 'Poppins', sans-serif;
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -.02em;
    color: var(--color-text, #1E293B);
  }
  .login-brand p {
    font-size: 13px;
    color: var(--color-muted, #64748B);
    margin-top: 6px;
  }
  .login-card {
    background: #fff;
    border: 1px solid var(--color-line, #E2E8F0);
    border-radius: 16px;
    padding: 40px;
    box-shadow: 0 20px 48px rgba(37, 99, 235, 0.08);
    animation: fadeIn .5s ease .1s both;
  }
  .login-card h2 {
    font-family: 'Poppins', sans-serif;
    font-size: 20px;
    font-weight: 650;
    margin-bottom: 28px;
    color: var(--color-text, #1E293B);
  }
  .login-error {
    font-size: 13px;
    color: #EF4444;
    background: #FEF2F2;
    border: 1px solid #FCA5A5;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 18px;
    display: none;
  }
  .login-error.visible { display: block; animation: shake .4s ease; }
  .login-field {
    margin-bottom: 20px;
  }
  .login-field label {
    display: block;
    font-size: 13px;
    font-weight: 500;
    color: var(--color-text, #1E293B);
    margin-bottom: 8px;
  }
  .login-field input {
    width: 100%;
    height: 46px;
    border: 1px solid var(--color-line, #E2E8F0);
    border-radius: 8px;
    padding: 0 14px;
    font-size: 14px;
    font-family: inherit;
    background: #fff;
    color: var(--color-text, #1E293B);
    transition: border-color .18s ease, box-shadow .18s ease;
    outline: none;
  }
  .login-field input:focus {
    border-color: #2563EB;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, .12);
  }
  .login-options {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 28px;
  }
  .login-checkbox {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-size: 13px;
    color: var(--color-muted, #64748B);
    user-select: none;
  }
  .login-submit {
    width: 100%;
    height: 46px;
    border: 0;
    border-radius: 8px;
    background: #2563EB;
    color: #fff;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    transition: background .18s ease, box-shadow .18s ease;
    font-family: inherit;
  }
  .login-submit:hover { background: #1D4ED8; }
  .login-submit:disabled { cursor: not-allowed; opacity: .72; }
  .login-submit:disabled:hover { background: #2563EB; }
  .spinner {
    width: 18px; height: 18px;
    border: 2px solid rgba(255,255,255,.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin .6s linear infinite;
    flex-shrink: 0;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    20%, 60% { transform: translateX(-6px); }
    40%, 80% { transform: translateX(6px); }
  }
  @media (max-width: 480px) {
    body { padding: 20px; align-items: flex-start; padding-top: 12vh; }
    .login-card { padding: 24px; }
  }
</style>
</head>
<body>
<div class="login-page">
  <div class="login-brand">
    <div class="login-brand-mark" aria-hidden="true">T</div>
    <h1>TRMD</h1>
    <p>Telegram Restricted Media Downloader</p>
  </div>
  <div class="login-card">
    <h2>登录控制台</h2>
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
          <input type="checkbox" id="remember-me" name="remember_me" style="width:16px;height:16px;accent-color:#2563EB;">
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

WEB_UI_CSS = r"""
  :root {
    color-scheme: light;
    --bg: #F0F4FF;
    --surface: #ffffff;
    --surface-muted: #f0f3f5;
    --text: #17201b;
    --muted: #5b6670;
    --line: #d8dee4;
    --accent: #2563EB;
    --accent-strong: #1D4ED8;
    --blue: #2563eb;
    --danger: #b42318;
    --warn: #a15c07;
    --ok: #127c52;
    --font-xs: 12px;
    --font-sm: 13px;
    --font-md: 15px;
    --font-lg: 16px;
    --font-xl: 20px;
    --safe-bottom: env(safe-area-inset-bottom, 0px);
    --tab-height: 56px;
    --topbar-height: 48px;
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: var(--font-md);
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    min-height: 100svh;
    -webkit-tap-highlight-color: transparent;
    user-select: none;
    padding-top: var(--topbar-height);
    padding-bottom: calc(var(--tab-height) + var(--safe-bottom));
  }
  button, input, select, textarea {
    font: inherit;
  }
  button {
    border: 0;
    border-radius: 8px;
    padding: 12px 16px;
    background: var(--accent);
    color: #fff;
    font-weight: 600;
    cursor: pointer;
    min-height: 44px;
    min-width: 44px;
    transition: opacity .15s;
  }
  button:active { opacity: .75; }
  button.secondary {
    background: var(--surface);
    border: 1px solid var(--line);
    color: var(--text);
  }
  button.danger {
    background: transparent;
    color: var(--danger);
    border: 1px solid var(--danger);
  }
  button.small {
    padding: 8px 12px;
    min-height: 36px;
    font-size: var(--font-sm);
  }
  input, select, textarea {
    width: 100%;
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 12px 14px;
    background: var(--surface);
    color: var(--text);
    min-height: 44px;
    font-size: 16px;
  }
  input:focus, select:focus, textarea:focus {
    border-color: var(--accent);
    outline: none;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, .12);
  }
  label {
    display: grid;
    gap: 6px;
    color: var(--muted);
    font-size: var(--font-sm);
  }

  /* ---- Top Bar ---- */
  .mob-topbar {
    position: fixed;
    top: 0; left: 0; right: 0;
    height: var(--topbar-height);
    background: var(--surface);
    border-bottom: 1px solid var(--line);
    display: flex;
    align-items: center;
    padding: 0 14px;
    gap: 10px;
    z-index: 100;
  }
  .mob-brand {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 700;
    font-size: var(--font-lg);
  }
  .mob-brand .mark {
    width: 28px; height: 28px;
    border-radius: 6px;
    background: var(--accent);
    display: grid;
    place-items: center;
    color: #fff;
  }
  .mob-topbar-actions {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .mob-topbar-actions select {
    width: auto;
    min-height: 0;
    padding: 4px 8px;
    font-size: var(--font-sm);
    border-radius: 6px;
  }

  /* ---- Bottom Tab Bar ---- */
  .mob-tabbar {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    height: calc(var(--tab-height) + var(--safe-bottom));
    padding-bottom: var(--safe-bottom);
    background: var(--surface);
    border-top: 1px solid var(--line);
    display: flex;
    justify-content: space-around;
    align-items: flex-start;
    padding-top: 6px;
    z-index: 100;
  }
  .mob-tab {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    font-size: 10px;
    color: var(--muted);
    min-width: 44px;
    cursor: pointer;
    padding: 4px 0;
    border: 0;
    background: transparent;
    border-radius: 0;
    min-height: auto;
    font-weight: 400;
  }
  .mob-tab.active {
    color: var(--accent);
    font-weight: 600;
  }
  .mob-tab svg {
    width: 22px;
    height: 22px;
  }

  /* ---- Content Area ---- */
  .mob-content {
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    animation: mobRise .3s ease both;
  }
  @keyframes mobRise {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .mob-view {
    display: none;
  }
  .mob-view.active {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  /* ---- Card List ---- */
  .mob-card {
    background: var(--surface);
    border-radius: 10px;
    padding: 14px;
    border: 1px solid var(--line);
    box-shadow: 0 1px 3px rgba(0,0,0,.03);
    border-left: 3px solid var(--line);
    transition: border-color .2s, transform .15s;
    cursor: pointer;
  }
  .mob-card:active { transform: scale(.985); }
  .mob-card.status-pending { border-left-color: #94a3b8; }
  .mob-card.status-running { border-left-color: var(--accent); }
  .mob-card.status-paused { border-left-color: #eab308; }
  .mob-card.status-success { border-left-color: var(--blue); }
  .mob-card.status-failure { border-left-color: var(--danger); }
  .mob-card.status-cancelled { border-left-color: #94a3b8; }
  .mob-card.status-skipped { border-left-color: #8b5cf6; }
  .mob-card__head {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
  }
  .mob-card__title {
    font-weight: 650;
    font-size: var(--font-md);
    word-break: break-all;
    line-height: 1.3;
  }
  .mob-card__badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: var(--font-xs);
    font-weight: 600;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .mob-card__badge.pending { background: #f1f5f9; color: #475569; }
  .mob-card__badge.running { background: #dcfce7; color: #166534; }
  .mob-card__badge.paused { background: #fef9c3; color: #a16207; }
  .mob-card__badge.completed { background: #dbeafe; color: #1e40af; }
  .mob-card__badge.failure { background: #fee2e2; color: #b91c1c; }
  .mob-card__badge.cancelled { background: #f1f5f9; color: #64748b; }
  .mob-card__row {
    display: flex;
    justify-content: space-between;
    padding: 3px 0;
    font-size: var(--font-sm);
  }
  .mob-card__row .label {
    color: var(--muted);
  }
  .mob-card__progress {
    margin: 6px 0;
    height: 6px;
    border-radius: 3px;
    background: var(--surface-muted);
    overflow: hidden;
  }
  .mob-card__progress-fill {
    height: 100%;
    background: var(--accent);
    border-radius: 3px;
    transition: width .3s;
  }
  .mob-card__actions {
    display: flex;
    gap: 6px;
    margin-top: 8px;
    flex-wrap: wrap;
  }
  .mob-watch-events {
    margin-top: 8px;
    border-top: 1px solid var(--line, #e0e0e0);
    padding-top: 8px;
    font-size: 12px;
  }
  .mob-watch-events .watch-event-item {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    padding: 3px 0;
    border-bottom: 1px solid var(--line, #e0e0e0);
  }
  .mob-watch-events .watch-event-item:last-child { border-bottom: 0; }

  /* ---- Collapse Panel ---- */
  .mob-collapse {
    border: 1px solid var(--line);
    border-radius: 10px;
    overflow: hidden;
    background: var(--surface);
  }
  .mob-collapse__head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px;
    cursor: pointer;
    font-weight: 600;
    user-select: none;
  }
  .mob-collapse__head:active { background: var(--surface-muted); }
  .mob-collapse__arrow {
    transition: transform .2s;
    color: var(--muted);
  }
  .mob-collapse.open .mob-collapse__arrow {
    transform: rotate(180deg);
  }
  .mob-collapse__body {
    display: none;
    padding: 0 14px 14px;
    flex-direction: column;
    gap: 10px;
  }
  .mob-collapse.open .mob-collapse__body {
    display: flex;
  }

  /* ---- Drawer ---- */
  .mob-drawer-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,.35);
    z-index: 200;
    display: none;
    align-items: flex-end;
  }
  .mob-drawer-overlay.open {
    display: flex;
  }
  .mob-drawer {
    width: 100%;
    background: var(--surface);
    border-radius: 16px 16px 0 0;
    padding: 8px 0 calc(24px + var(--safe-bottom));
    max-height: 70vh;
    overflow: auto;
    animation: mobSlideUp .25s ease;
  }
  @keyframes mobSlideUp {
    from { transform: translateY(100%); }
    to { transform: translateY(0); }
  }
  .mob-drawer__handle {
    width: 36px;
    height: 4px;
    background: var(--line);
    border-radius: 2px;
    margin: 8px auto 12px;
  }
  .mob-drawer__item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 20px;
    font-size: var(--font-md);
    cursor: pointer;
    border: 0;
    background: transparent;
    width: 100%;
    min-height: auto;
    border-radius: 0;
    color: var(--text);
    font-weight: 400;
  }
  .mob-drawer__item:active {
    background: var(--surface-muted);
  }
  .mob-drawer__item svg {
    width: 20px;
    height: 20px;
    color: var(--muted);
  }
  .mob-drawer__separator {
    height: 1px;
    background: var(--line);
    margin: 8px 20px;
  }
  .mob-drawer__item--logout {
    color: var(--muted);
  }
  .mob-drawer__item--logout svg {
    color: var(--danger);
    opacity: .72;
  }

  /* ---- FAB ---- */
  .mob-fab {
    position: fixed;
    bottom: calc(var(--tab-height) + var(--safe-bottom) + 16px);
    right: 16px;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: var(--accent);
    color: #fff;
    font-size: 24px;
    display: grid;
    place-items: center;
    box-shadow: 0 4px 16px rgba(37, 99, 235, .4);
    z-index: 90;
    cursor: pointer;
    transition: transform .2s, box-shadow .2s;
    min-height: auto;
    min-width: auto;
    padding: 0;
  }
  .mob-fab:active {
    transform: scale(.92);
    box-shadow: 0 2px 8px rgba(37, 99, 235, .3);
  }

  /* ---- FAB Menu ---- */
  .mob-fab-menu {
    position: fixed;
    bottom: calc(var(--tab-height) + var(--safe-bottom) + 72px);
    right: 16px;
    display: none;
    flex-direction: column;
    gap: 8px;
    z-index: 90;
  }
  .mob-fab-menu.open {
    display: flex;
  }
  .mob-fab-menu__item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 10px;
    font-size: var(--font-sm);
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(0,0,0,.08);
    cursor: pointer;
    white-space: nowrap;
    min-height: auto;
    color: var(--text);
  }
  .mob-fab-menu__item:active {
    background: var(--surface-muted);
  }

  /* ---- Bottom Sheet ---- */
  .mob-sheet-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,.35);
    z-index: 300;
    display: none;
    align-items: flex-end;
  }
  .mob-sheet-overlay.open {
    display: flex;
  }
  .mob-sheet {
    width: 100%;
    background: var(--surface);
    border-radius: 16px 16px 0 0;
    padding: 20px 16px max(24px, var(--safe-bottom));
    max-height: 85vh;
    overflow: auto;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  .mob-sheet__title {
    font-size: var(--font-lg);
    font-weight: 700;
    margin: 0;
  }

  /* ---- Toast ---- */
  .mob-toast {
    position: fixed;
    bottom: calc(var(--tab-height) + var(--safe-bottom) + 16px);
    left: 50%;
    transform: translateX(-50%);
    background: var(--text);
    color: #fff;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: var(--font-sm);
    z-index: 400;
    opacity: 0;
    pointer-events: none;
    transition: opacity .25s;
    white-space: nowrap;
  }
  .mob-toast.show {
    opacity: 1;
    pointer-events: auto;
  }

  /* ---- Task Detail Sheet ---- */
  .mob-sheet__task-header {
    background: var(--surface-muted);
    border-radius: 8px;
    padding: 12px;
  }
  .mob-sheet__task-header .task-title {
    font-weight: 650;
    font-size: var(--font-md);
    word-break: break-all;
    margin-bottom: 4px;
  }
  .mob-sheet__task-header .task-meta {
    font-size: var(--font-xs);
    color: var(--muted);
    margin-bottom: 6px;
  }
  .mob-sheet-tabs {
    display: flex;
    gap: 4px;
    overflow-x: auto;
    padding-bottom: 2px;
  }
  .mob-sheet-tab {
    padding: 6px 10px;
    border-radius: 6px;
    font-size: var(--font-xs);
    font-weight: 600;
    border: 1px solid var(--line);
    background: var(--surface);
    color: var(--muted);
    cursor: pointer;
    white-space: nowrap;
    min-height: auto;
    min-width: auto;
    transition: .15s;
  }
  .mob-sheet-tab.active {
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
  }
  .mob-sheet-tab .count { margin-left: 3px; opacity: .8; }
  .mob-item-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid var(--line);
    font-size: var(--font-sm);
    gap: 6px;
  }
  .mob-item-row:last-child { border-bottom: 0; }
  .mob-item-row__name {
    flex: 1;
    word-break: break-all;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .mob-event-row {
    padding: 6px 0;
    border-bottom: 1px solid var(--line);
    font-size: var(--font-xs);
  }
  .mob-event-row:last-child { border-bottom: 0; }
  .mob-event-row time { color: var(--muted); margin-right: 6px; }
  .mob-sheet-pagination {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 6px;
    font-size: var(--font-xs);
    color: var(--muted);
  }

  /* ---- Empty State ---- */
  .mob-empty {
    text-align: center;
    color: var(--muted);
    padding: 40px 20px;
    font-size: var(--font-sm);
  }

  /* ---- Section Header ---- */
  .mob-section-title {
    font-size: var(--font-xs);
    text-transform: uppercase;
    letter-spacing: .06em;
    color: var(--muted);
    padding: 4px 0;
  }
  .mob-media-scan-btn {
    margin: 8px 0; width: 100%;
  }
  .mob-media-result { margin-top: 12px; font-size: var(--font-sm); }

  /* ---- Check Group (fieldset) ---- */
  .mob-check-group {
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 10px 14px;
    margin: 0;
  }
  .mob-check-group legend {
    font-size: var(--font-sm);
    color: var(--muted);
    padding: 0 4px;
  }

  /* ---- Scrollable Table ---- */
  .mob-table-wrap {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    border: 1px solid var(--line);
    border-radius: 8px;
  }
  .mob-table-wrap table {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--font-sm);
  }
  .mob-table-wrap th,
  .mob-table-wrap td {
    padding: 8px 10px;
    text-align: left;
    border-bottom: 1px solid var(--line);
    white-space: nowrap;
  }
  .mob-table-wrap th {
    background: var(--surface-muted);
    font-weight: 600;
    position: sticky;
    top: 0;
  }

  .login-container {
    display: none;
    position: fixed;
    inset: 0;
    background: var(--bg);
    z-index: 1000;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 20px;
    padding: 16px;
  }
  .login-container.active { display: flex; }
  .login-card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 24px;
    max-width: 420px;
    width: 100%;
    box-shadow: var(--shadow);
  }
  .login-card__title {
    font-size: 18px;
    font-weight: 700;
    margin: 0 0 6px;
    color: var(--text);
  }
  .login-card__subtitle {
    font-size: var(--font-sm);
    color: var(--muted);
    margin: 0 0 20px;
  }
  .login-card__step {
    font-size: var(--font-xs);
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: .06em;
    margin-bottom: 8px;
  }
  .login-field {
    margin-bottom: 16px;
  }
  .login-field label {
    display: block;
    font-size: var(--font-sm);
    font-weight: 500;
    color: var(--text);
    margin-bottom: 6px;
  }
  .login-field input {
    width: 100%;
    height: 42px;
    border: 1px solid var(--line);
    border-radius: 6px;
    padding: 0 12px;
    font-size: var(--font-md);
    background: var(--surface);
    color: var(--text);
    transition: border-color .18s ease;
  }
  .login-field input:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 2px rgba(37, 99, 235, .12);
  }
  .login-field__hint {
    font-size: var(--font-xs);
    color: var(--muted);
    margin-top: 4px;
  }
  .login-error {
    font-size: var(--font-sm);
    color: var(--danger);
    background: #fff4f2;
    border: 1px solid #f3b5ad;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 16px;
    display: none;
  }
  .login-error.visible { display: block; }
  .login-actions {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
  }
  .login-actions button {
    min-width: 100px;
  }
  .login-success {
    text-align: center;
    padding: 16px 0;
  }
  .login-success svg {
    width: 48px;
    height: 48px;
    color: var(--ok);
    margin-bottom: 12px;
  }
  .login-success__text {
    font-size: 16px;
    font-weight: 600;
    color: var(--ok);
    margin: 0;
  }
  .login-brand {
    text-align: center;
    margin-bottom: 4px;
  }
  .login-brand h1 {
    font-size: 24px;
    font-weight: 800;
    margin: 0;
    color: var(--text);
    letter-spacing: -.02em;
  }
  .login-brand p {
    font-size: var(--font-sm);
    color: var(--muted);
    margin: 2px 0 0;
  }
"""
WEB_UI_MOBILE_CSS = WEB_UI_CSS

WEB_UI_MOBILE_BODY = r"""<div class="mob-topbar">
  <div class="mob-brand">
    <div class="mark" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
    </div>
    <span>TRMD</span>
  </div>
  <div class="mob-topbar-actions">
    <select id="language-select" aria-label="语言">
      <option value="zh">中文</option>
      <option value="en">EN</option>
    </select>
    <button class="secondary small" type="button" id="refresh" aria-label="刷新">
      <svg viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M20 12a8 8 0 1 1-2.34-5.66M20 4v5h-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
    </button>
  </div>
</div>

<div class="login-container" id="login-container">
  <div class="login-brand">
    <h1>TRMD</h1>
    <p>Telegram 账号登录</p>
  </div>
  <div class="login-card">
    <div class="login-error" id="login-error"></div>
    <div id="login-form-phone" class="login-step">
      <div class="login-card__step">步骤 1 / 3</div>
      <h2 class="login-card__title">输入电话号码</h2>
      <p class="login-card__subtitle">请输入您的 Telegram 账号绑定的手机号</p>
      <div class="login-field">
        <label for="login-phone">电话号码</label>
        <input id="login-phone" type="tel" placeholder="+8615000000000" autocomplete="tel">
        <div class="login-field__hint">需以「+地区号」开头，如中国 +86</div>
      </div>
      <div class="login-actions">
        <button type="button" id="login-btn-phone" class="login-submit">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          发送验证码
        </button>
      </div>
    </div>
    <div id="login-form-code" class="login-step" style="display:none">
      <div class="login-card__step">步骤 2 / 3</div>
      <h2 class="login-card__title">输入验证码</h2>
      <p class="login-card__subtitle" id="login-code-desc">验证码已发送到您的设备</p>
      <div class="login-field">
        <label for="login-code">验证码</label>
        <input id="login-code" type="text" inputmode="numeric" maxlength="10" placeholder="输入验证码" autocomplete="one-time-code">
      </div>
      <div class="login-actions">
        <button type="button" class="secondary" id="login-btn-back">返回</button>
        <button type="button" id="login-btn-code" class="login-submit">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          验证
        </button>
      </div>
    </div>
    <div id="login-form-password" class="login-step" style="display:none">
      <div class="login-card__step">步骤 2.5 / 3</div>
      <h2 class="login-card__title">两步验证密码</h2>
      <p class="login-card__subtitle" id="login-password-hint">该账号已设置两步验证</p>
      <div class="login-field">
        <label for="login-password">密码</label>
        <input id="login-password" type="password" placeholder="输入两步验证密码" autocomplete="current-password">
        <div class="login-field__hint" id="login-password-hint-text"></div>
      </div>
      <div class="login-actions">
        <button type="button" class="secondary" id="login-btn-back-pwd">取消</button>
        <button type="button" id="login-btn-password" class="login-submit">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          验证
        </button>
      </div>
    </div>
    <div id="login-form-recovery" class="login-step" style="display:none">
      <div class="login-card__step">密码恢复</div>
      <h2 class="login-card__title">输入恢复代码</h2>
      <p class="login-card__subtitle" id="login-recovery-desc">恢复代码已发送</p>
      <div class="login-field">
        <label for="login-recovery">恢复代码</label>
        <input id="login-recovery" type="text" placeholder="输入恢复代码">
      </div>
      <div class="login-actions">
        <button type="button" class="secondary" id="login-btn-back-recovery">返回</button>
        <button type="button" id="login-btn-recovery" class="login-submit">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          提交
        </button>
      </div>
    </div>
    <div id="login-form-signup" class="login-step" style="display:none">
      <div class="login-card__step">注册信息</div>
      <h2 class="login-card__title">完善个人信息</h2>
      <p class="login-card__subtitle">首次登录，请输入您的名字</p>
      <div class="login-field">
        <label for="login-first-name">名字</label>
        <input id="login-first-name" type="text" placeholder="名字">
      </div>
      <div class="login-field">
        <label for="login-last-name">姓氏</label>
        <input id="login-last-name" type="text" placeholder="姓氏（可选）">
      </div>
      <div class="login-actions">
        <button type="button" id="login-btn-signup" class="login-submit">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          完成注册
        </button>
      </div>
    </div>
    <div id="login-form-done" class="login-step" style="display:none">
      <div class="login-success">
        <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M8 12l3 3 5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <p class="login-success__text" id="login-user-name">登录成功</p>
      </div>
    </div>
  </div>
</div>

<div class="mob-content" id="mob-content">
  <!-- 转存任务 -->
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
          <label style="flex-direction:row;align-items:center;gap:8px;">
            <input type="checkbox" name="include_comment" style="width:auto;min-height:auto;">
            <span data-i18n="new.includeComment">包含评论区</span>
          </label>
          <button type="submit" style="width:100%;" data-i18n="new.create">创建任务</button>
          <p class="mob-empty" id="mob-form-notice" style="display:none;"></p>
        </form>
      </div>
    </div>
    <div id="mob-tasks-list"></div>
  </div>

  <!-- 实时监听 -->
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
              <input type="text" name="source_link" placeholder="https://t.me/source" style="display:none;">
            </label>
          </div>
          <div id="mob-watch-target-group" style="display:none;">
            <label><span data-i18n="watches.target">目标频道</span>
              <input type="text" name="target_link" placeholder="https://t.me/...">
            </label>
          </div>
          <div id="mob-watch-comment-group" style="display:none;">
            <label style="flex-direction:row;align-items:center;gap:8px;">
              <input type="checkbox" name="include_comment" style="width:auto;min-height:auto;">
              <span data-i18n="watches.includeComment">包含评论区</span>
            </label>
          </div>
          <button type="submit" style="width:100%;" data-i18n="watches.createDownload">新增监听</button>
          <p class="mob-empty" id="mob-watch-notice" style="display:none;"></p>
        </form>
      </div>
    </div>
    <div id="mob-watches-list"></div>
  </div>

  <!-- 设置 -->
  <div class="mob-view" id="mob-view-settings">
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
    <button id="mob-save-settings" style="width:100%;margin-top:4px;" data-i18n="settings.save">保存设置</button>
    <p class="mob-empty" id="mob-settings-notice" style="display:none;"></p>
  </div>

  <!-- 频道下载 -->
  <div class="mob-view" id="mob-view-channel-downloads">
    <div class="mob-collapse" id="collapse-channel-form">
      <div class="mob-collapse__head" data-i18n="channel.title">频道下载 <span class="mob-collapse__arrow">&#9660;</span></div>
      <div class="mob-collapse__body">
        <form id="mob-channel-form">
          <label><span data-i18n="channel.link">频道链接</span>
            <input type="text" name="chat_link" placeholder="https://t.me/..." required>
          </label>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
            <label><span data-i18n="channel.startDate">起始时间</span>
              <input type="datetime-local" name="start_date">
            </label>
            <label><span data-i18n="channel.endDate">结束时间</span>
              <input type="datetime-local" name="end_date">
            </label>
          </div>
          <label><span data-i18n="channel.keywords">关键词</span>
            <input type="text" name="keywords" data-i18n-placeholder="channel.keywordsPlaceholder" placeholder="逗号分隔，可留空">
          </label>
          <fieldset class="mob-check-group">
            <legend data-i18n="channel.types">下载类型</legend>
            <div id="mob-channel-download-types" style="display:grid;grid-template-columns:1fr 1fr;gap:2px 10px;">
              <label style="flex-direction:row;align-items:center;gap:4px;font-size:var(--font-sm);"><input type="checkbox" name="download_type" value="video" checked style="width:auto;min-height:auto;">video</label>
              <label style="flex-direction:row;align-items:center;gap:4px;font-size:var(--font-sm);"><input type="checkbox" name="download_type" value="photo" checked style="width:auto;min-height:auto;">photo</label>
              <label style="flex-direction:row;align-items:center;gap:4px;font-size:var(--font-sm);"><input type="checkbox" name="download_type" value="audio" checked style="width:auto;min-height:auto;">audio</label>
              <label style="flex-direction:row;align-items:center;gap:4px;font-size:var(--font-sm);"><input type="checkbox" name="download_type" value="voice" checked style="width:auto;min-height:auto;">voice</label>
              <label style="flex-direction:row;align-items:center;gap:4px;font-size:var(--font-sm);"><input type="checkbox" name="download_type" value="animation" checked style="width:auto;min-height:auto;">animation</label>
              <label style="flex-direction:row;align-items:center;gap:4px;font-size:var(--font-sm);"><input type="checkbox" name="download_type" value="document" checked style="width:auto;min-height:auto;">document</label>
              <label style="flex-direction:row;align-items:center;gap:4px;font-size:var(--font-sm);"><input type="checkbox" name="download_type" value="video_note" checked style="width:auto;min-height:auto;">video_note</label>
            </div>
          </fieldset>
          <label style="flex-direction:row;align-items:center;gap:8px;">
            <input type="checkbox" name="include_comment" style="width:auto;min-height:auto;">
            <span data-i18n="channel.includeComment">包含评论区</span>
          </label>
          <button type="submit" style="width:100%;" data-i18n="channel.create">创建频道下载</button>
          <p class="mob-empty" id="mob-channel-notice" style="display:none;"></p>
        </form>
      </div>
    </div>
    <div id="mob-channel-downloads-list"></div>
  </div>

  <!-- 本地上传 -->
  <div class="mob-view" id="mob-view-uploads">
    <div class="mob-collapse" id="collapse-upload-form">
      <div class="mob-collapse__head" data-i18n="uploads.title">本地上传 <span class="mob-collapse__arrow">&#9660;</span></div>
      <div class="mob-collapse__body">
        <form id="mob-upload-form">
          <label><span data-i18n="uploads.path">本地路径</span>
            <input type="text" name="path" placeholder="/path/to/file" required>
          </label>
          <label><span data-i18n="uploads.target">目标频道</span>
            <input type="text" name="target_link" placeholder="https://t.me/..." required>
          </label>
          <label style="flex-direction:row;align-items:center;gap:8px;">
            <input type="checkbox" name="recursive" style="width:auto;min-height:auto;">
            <span data-i18n="uploads.recursive">递归上传文件夹</span>
          </label>
          <button type="submit" style="width:100%;" data-i18n="uploads.create">创建上传</button>
          <p class="mob-empty" id="mob-upload-notice" style="display:none;"></p>
        </form>
      </div>
    </div>
    <div id="mob-uploads-list"></div>
  </div>

  <!-- 统计 -->
  <div class="mob-view" id="mob-view-statistics">
    <div class="mob-section-title" data-i18n="statistics.table">表格</div>
    <div id="mob-statistics-list"></div>
  </div>

  <!-- 下载记录 -->
  <div class="mob-view" id="mob-view-records">
    <div class="mob-section-title" data-i18n="records.title">下载记录</div>
    <div id="mob-records-list"></div>
  </div>
  <div class="mob-view" id="mob-view-media">
    <div class="mob-section-title" data-i18n="media.title">媒体管理</div>
    <button id="mob-media-scan-btn" class="mob-media-scan-btn" data-i18n="media.scan">扫描可清理文件</button>
    <div id="mob-media-result"></div>
  </div>
</div>

<!-- FAB + Menu -->
<div class="mob-fab-menu" id="mob-fab-menu">
  <button class="mob-fab-menu__item" id="mob-fab-new-transfer">
    <svg viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M7 7h10M7 12h10M7 17h6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
    <span data-i18n="new.title">新建转存</span>
  </button>
  <button class="mob-fab-menu__item" id="mob-fab-new-watch">
    <svg viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M4 12s3-6 8-6 8 6 8 6-3 6-8 6-8-6-8-6Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>
    <span data-i18n="watches.title">新建监听</span>
  </button>
</div>
<button class="mob-fab" id="mob-fab" aria-label="新建">+</button>

<!-- Bottom Tab Bar -->
<div class="mob-tabbar" id="mob-tabbar">
  <button class="mob-tab active" data-mob-nav="transfers">
    <svg viewBox="0 0 24 24" fill="none"><path d="M7 7h10M7 12h10M7 17h6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
    <span data-i18n="nav.transfers">转存</span>
  </button>
  <button class="mob-tab" data-mob-nav="watches">
    <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/><path d="M4 12s3-6 8-6 8 6 8 6-3 6-8 6-8-6-8-6Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M12 9v3l2 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
    <span data-i18n="nav.watches">监听</span>
  </button>
  <button class="mob-tab" data-mob-nav="settings">
    <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="3.5" stroke="currentColor" stroke-width="2"/><path d="M19.4 15a1.8 1.8 0 0 0 .36 1.98l.04.04a2 2 0 0 1-2.82 2.82l-.04-.04A1.8 1.8 0 0 0 15 19.4M4.6 9a1.8 1.8 0 0 0-.36-1.98l-.04-.04a2 2 0 0 1 2.82-2.82l.04.04A1.8 1.8 0 0 0 9 4.6" stroke="currentColor" stroke-width="1.5"/></svg>
    <span data-i18n="nav.settings">设置</span>
  </button>
  <button class="mob-tab" data-mob-nav="more">
    <svg viewBox="0 0 24 24" fill="none"><circle cx="5" cy="12" r="1.5" fill="currentColor"/><circle cx="12" cy="12" r="1.5" fill="currentColor"/><circle cx="19" cy="12" r="1.5" fill="currentColor"/></svg>
    <span>更多</span>
  </button>
</div>

<!-- 更多 Drawer -->
<div class="mob-drawer-overlay" id="mob-drawer-overlay">
  <div class="mob-drawer" id="mob-drawer">
    <div class="mob-drawer__handle"></div>
    <button class="mob-drawer__item" data-mob-drawer-nav="channel-downloads">
      <svg viewBox="0 0 24 24" fill="none"><path d="M5 5h14v10H8l-3 3V5Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>
      <span data-i18n="nav.channelDownloads">频道下载</span>
    </button>
    <button class="mob-drawer__item" data-mob-drawer-nav="uploads">
      <svg viewBox="0 0 24 24" fill="none"><path d="M12 16V4M7 9l5-5 5 5M5 20h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      <span data-i18n="nav.uploads">本地上传</span>
    </button>
    <button class="mob-drawer__item" data-mob-drawer-nav="statistics">
      <svg viewBox="0 0 24 24" fill="none"><path d="M5 19V9M12 19V5M19 19v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M4 19h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      <span data-i18n="nav.statistics">统计</span>
    </button>
    <button class="mob-drawer__item" data-mob-drawer-nav="records">
      <svg viewBox="0 0 24 24" fill="none"><path d="M5 4h14v16H5z" stroke="currentColor" stroke-width="2"/><path d="M8 8h8M8 12h8M8 16h5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      <span data-i18n="nav.records">下载记录</span>
    </button>
    <div class="mob-drawer__separator"></div>
    <button type="button" class="mob-drawer__item mob-drawer__item--logout" id="mob-btn-logout">
      <svg viewBox="0 0 24 24" fill="none"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      <span data-i18n="nav.logout">退出登录</span>
    </button>
  </div>
</div>

<!-- Bottom Sheet Overlay (通用) -->
<div class="mob-sheet-overlay" id="mob-sheet-overlay">
  <div class="mob-sheet" id="mob-sheet"></div>
</div>

<!-- Toast -->
<div class="mob-toast" id="mob-toast"></div>"""

SHARED_WEB_UI_SCRIPT = r"""
  const i18n = {
    zh: {
      'app.subtitle': '转存控制台',
      'app.title': 'TRMD 转存控制台',
      'nav.transfers': '转存任务',
      'nav.watches': '实时监听',
      'nav.channelDownloads': '频道下载',
      'nav.uploads': '本地上传',
      'nav.statistics': '统计',
      'nav.settings': '设置',
      'nav.records': '下载记录',
      'nav.logout': '退出登录',
      'nav.primary': '主导航',
'side.failed': '失败',
      'hero.title': 'PikPak 转存队列',
      'hero.body': '创建、监控和配置 Telegram 受限内容转存任务。状态、文件进度、失败事件和下载成功记录会持久化保存。',
      'action.refresh': '刷新',
      'language.label': '语言',
      'new.title': '新建转存',
      'new.profileNote': '目标配置',
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
      'watches.title': '当前实时监听',
      'watches.downloadTitle': '监听下载',
      'watches.downloadMeta': '新消息转存',
      'watches.forwardTitle': '监听转发',
      'watches.forwardMeta': '新消息转发',
      'watches.sources': '来源频道',
      'watches.sourcesHint': '每行一个 Telegram 频道链接。监听下载会处理新到达的视频和图片。',
      'watches.source': '来源频道',
      'watches.target': '目标频道',
      'watches.includeComment': '包含评论区',
      'watches.forwardHint': '同一来源不能同时存在监听下载和监听转发。',
      'watches.createDownload': '新增监听下载',
      'watches.createForward': '新增监听转发',
      'watches.type': '类型',
      'watches.empty': '还没有实时监听。',
      'watches.delete': '移除监听',
      'watches.download': '监听下载',
      'watches.forward': '监听转发',
      'watches.created': '实时监听已接收。',
      'watches.deleted': '实时监听已移除。',
      'watches.edit': '编辑',
      'watches.updated': '实时监听已更新。',
      'watches.events': '转发记录',
      'watches.noEvents': '暂无转发记录',
      'watches.eventForwarded': '转发成功',
      'watches.eventSkipped': '已过滤',
      'watches.eventLoading': '加载中…',
      'watches.loadMore': '加载更多',
      'watches.targetRequired': '目标频道为必填项。',
      'action.cancel': '取消',
      'action.save': '保存',
      'channel.title': '频道下载',
      'channel.meta': '筛选后创建下载',
      'channel.link': '频道链接',
      'channel.startDate': '起始时间',
      'channel.endDate': '结束时间',
      'channel.types': '下载类型',
      'channel.keywords': '关键词',
      'channel.keywordsPlaceholder': '逗号分隔，可留空',
      'channel.includeComment': '包含评论区',
      'channel.hint': '频道下载会检索匹配消息并创建下载任务，执行时间取决于频道历史消息数量。',
      'channel.create': '创建频道下载',
      'channel.accepted': '频道下载已接收。',
      'uploads.title': '本地上传',
      'uploads.meta': '服务器路径',
      'uploads.path': '本地路径',
      'uploads.target': '目标频道',
      'uploads.recursive': '递归上传文件夹',
      'uploads.serverPathHint': '路径位于运行 TRMD 的服务器或容器，不是当前浏览器所在电脑。关闭递归时，文件夹只上传第一层文件；开启递归时包含子文件夹。',
      'uploads.create': '创建上传',
      'uploads.accepted': '上传任务已接收。',
      'statistics.title': '统计与导出',
      'statistics.meta': '运行态数据',
      'statistics.table': '表格',
      'statistics.available': '可用',
      'statistics.rows': '数量',
      'statistics.yes': '是',
      'statistics.no': '否',
      'statistics.link': '链接统计表',
      'statistics.count': '计数统计表',
      'statistics.upload': '上传统计表',
      'statistics.exportLink': '导出链接统计表',
      'statistics.exportCount': '导出计数统计表',
      'statistics.exportUpload': '导出上传统计表',
      'statistics.exported': '统计表已导出到：{directory}',
      'tasks.title': '转存任务',
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
      'items.selectTask': '选择一个任务',
      'items.empty': '该任务还没有文件记录。',
      'items.tabsLabel': '文件状态分类',
      'items.tab.running': '进行中',
      'items.tab.success': '已完成',
      'items.tab.skipped': '跳过',
      'items.tab.failure': '失败',
      'items.empty.running': '当前没有进行中的文件。',
      'items.empty.success': '当前没有已完成的文件。',
      'items.empty.skipped': '当前没有跳过的文件。',
      'items.empty.failure': '当前没有失败的文件。',
      'items.retryFailed': '重试当前任务失败项',
      'items.page.previous': '上一页',
      'items.page.next': '下一页',
      'items.page.status': '第 {page} / {pages} 页',
      'items.page.range': '{start}-{end} / {total}',
      'items.download': '下载',
      'items.upload': '上传',
      'items.loadMore': '加载更多文件',
      'items.remaining': '条剩余',
      'events.title': '最近事件',
      'events.empty': '没有事件记录。',
      'events.loadMore': '加载更多事件',
      'events.remaining': '条剩余',
      'settings.title': '设置',
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
      'settings.secretNotConfigured': '未配置',
      'settings.downloadTypes': '下载类型',
      'settings.forwardTypes': '转发类型',
      'settings.messageFilter': '消息过滤',
      'settings.mediaTypes': '媒体类型',
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
      'records.title': '下载成功记录',
      'records.chat': '频道 ID',
      'records.message': '消息 ID',
      'records.file': '文件',
      'records.size': '大小',
      'records.updated': '更新时间',
      'records.empty': '还没有下载成功记录。',
      'form.createFailed': '创建任务失败。',
      'form.requestFailed': '请求失败。',
      'form.creatingTransfer': '正在分析来源消息范围，Telegram 限流时可能需要等待。请保持页面打开。',
      'form.creatingTransferShort': '正在分析',
      'form.createSuccess': '任务已创建并开始排队。可以关闭页面，也可以继续查看进度。',
      'error.auth_required': '需要登录。',
      'error.invalid_task_id': '任务 ID 无效。',
      'error.task_not_found': '找不到任务。',
      'error.not_found': '找不到请求的资源。',
      'error.source_link_required': '请填写来源链接。',
      'error.target_link_required': '请填写目标链接。',
      'error.range_ids_required': '起始 ID 和结束 ID 必须同时填写。',
      'error.range_end_before_start': '结束 ID 必须大于或等于起始 ID。',
      'error.range_source_must_be_chat_link': '范围转存的来源必须是频道链接，不能是单条消息链接。',
      'error.transfer_range_detection_unavailable': '当前运行模式无法自动探测消息范围。',
      'error.transfer_range_detection_failed': '自动探测消息范围失败。',
      'error.transfer_range_empty': '来源中没有可访问的消息。',
      'error.create_task_failed': '创建任务失败。',
      'error.update_settings_failed': '更新设置失败。',
      'error.watch_source_conflict': '同一来源不能同时存在监听下载和监听转发。',
      'error.watch_already_exists': '实时监听已存在。',
      'error.watch_source_required': '请填写监听来源。',
      'error.watch_target_required': '请填写监听目标。',
      'error.invalid_payload': '请求内容无效。',
      'error.invalid_watch_type': '实时监听类型无效。',
      'error.invalid_watch_source': '监听来源必须以 https://t.me/ 开头。',
      'error.invalid_watch_target': '监听目标必须以 https://t.me/ 开头。',
      'error.watch_operations_unavailable': '实时监听操作不可用。',
      'error.upload_path_not_found': '服务器或容器中找不到该路径。',
      'error.upload_path_required': '请填写上传路径。',
      'error.upload_target_required': '请填写上传目标。',
      'error.upload_recursive_requires_directory': '递归上传需要选择文件夹路径。',
      'error.invalid_upload_target': '上传目标必须是 Telegram 链接、me 或 self。',
      'error.upload_operations_unavailable': '上传操作不可用。',
      'error.invalid_table_type': '统计表类型无效。',
      'error.table_operations_unavailable': '统计表操作不可用。',
      'error.invalid_channel_link': '频道链接必须以 https://t.me/ 开头。',
      'error.channel_link_required': '请填写频道链接。',
      'error.channel_download_type_required': '请至少选择一种下载类型。',
      'error.invalid_channel_download_type': '频道下载类型无效。',
      'error.channel_download_operations_unavailable': '频道下载操作不可用。',
      'action.taskUpdated': '任务操作已提交。',
      'error.invalid_date_range': '时间范围格式无效。',
      'error.date_range_end_before_start': '结束时间必须大于或等于起始时间。',
      'event.level.info': '信息',
      'event.level.warning': '警告',
      'event.level.error': '错误',
      'event.fileReady': '文件已准备上传到目标：{name}',
      'event.sentToTarget': '已发送到目标：{name}',
      'event.uploadFailed': '上传失败：{reason}',
      'event.reusedDownload': '已复用下载成功记录：{name}',
      'event.directForward': '已直接发送到目标：{link}',
      'event.rangeAssigned': '范围转存已分配：{range}',
      'event.rangeAssignedWithFallback': '范围转存已分配：{range}，回退下载 {count} 条。',
      'event.singleAssigned': '单条消息转存已分配。',
      'event.singleAssignedWithFallback': '单条消息转存已分配，回退下载 {count} 条。',
      'status.pending': '等待',
      'status.running': '运行中',
      'status.paused': '已暂停',
      'status.success': '成功',
      'status.failure': '失败',
      'status.skipped': '跳过',
      'nav.media': '媒体管理',
      'media.title': '媒体管理',
      'media.meta': '扫描并清理磁盘上的残留媒体文件',
      'media.scan': '扫描可清理文件',
      'media.scanning': '正在扫描...',
      'media.totalFiles': '可清理文件',
      'media.totalSize': '总大小',
      'media.retentionDays': '保留天数',
      'media.transferItems': '转存任务文件',
      'media.orphanFiles': '遗留文件 (超过保留天数)',
      'media.file': '文件',
      'media.size': '大小',
      'media.status': '任务状态',
      'media.source': '来源',
      'media.path': '路径',
      'media.mtime': '最后修改',
      'media.cleanup': '清理选中文件',
      'media.cleaning': '清理中...',
      'media.selected': '已选',
      'media.files': '个文件',
      'media.noSelection': '请先选择要清理的文件。',
      'media.confirmCleanup': '确定要删除选中的文件吗？此操作不可撤销。',
      'media.cleanupDone': '清理完成：已删除 {count} 个文件 ({size})。',
      'media.cleanupHistory': '清理历史',
      'media.reason': '原因',
      'media.time': '时间',
      'media.filterByTask': '按任务筛选：',
      'media.allTasks': '全部任务'
    },
    en: {
      'app.subtitle': 'Transfer Console',
      'app.title': 'TRMD Transfer Console',
      'nav.transfers': 'Transfer tasks',
      'nav.watches': 'Live watches',
      'nav.channelDownloads': 'Channel downloads',
      'nav.uploads': 'Local uploads',
      'nav.statistics': 'Statistics',
      'nav.settings': 'Settings',
      'nav.records': 'Download records',
      'nav.logout': 'Log out',
      'nav.primary': 'Primary navigation',
'side.failed': 'Failed',
      'hero.title': 'PikPak transfer queue',
      'hero.body': 'Create, monitor, and configure Telegram restricted content transfer tasks. State, file progress, failure events, and download success records are persisted.',
      'action.refresh': 'Refresh',
      'language.label': 'Language',
      'new.title': 'New transfer',
      'new.profileNote': 'Target profile',
      'new.source': 'Source link',
      'new.target': 'Target',
      'new.targetProfile': 'Target profile',
      'profile.pikpak': 'PikPak document transfer',
      'profile.generic': 'Generic Telegram target',
      'new.startId': 'Start ID',
      'new.endId': 'End ID',
      'new.optional': 'Optional',
      'new.includeComment': 'Include discussion replies',
      'new.hint': 'Leave the range empty for a message link. For a channel or group link, empty IDs auto-detect the accessible range, or you can set start and end IDs manually.',
      'new.create': 'Create task',
      'watches.title': 'Current live watches',
      'watches.downloadTitle': 'Download watch',
      'watches.downloadMeta': 'Transfer new messages',
      'watches.forwardTitle': 'Forward watch',
      'watches.forwardMeta': 'Forward new messages',
      'watches.sources': 'Source channels',
      'watches.sourcesHint': 'One Telegram channel link per line. Download watches handle new video and photo messages.',
      'watches.source': 'Source channel',
      'watches.target': 'Target channel',
      'watches.includeComment': 'Include discussion replies',
      'watches.forwardHint': 'The same source cannot have a download watch and a forward watch at the same time.',
      'watches.createDownload': 'Add download watch',
      'watches.createForward': 'Add forward watch',
      'watches.type': 'Type',
      'watches.empty': 'No live watches yet.',
      'watches.delete': 'Remove watch',
      'watches.download': 'Download watch',
      'watches.forward': 'Forward watch',
      'watches.created': 'Live watch accepted.',
      'watches.deleted': 'Live watch removed.',
      'watches.edit': 'Edit',
      'watches.updated': 'Live watch updated.',
      'watches.events': 'Forwarding log',
      'watches.noEvents': 'No forwarding events yet.',
      'watches.eventForwarded': 'Forwarded',
      'watches.eventSkipped': 'Filtered',
      'watches.eventLoading': 'Loading…',
      'watches.loadMore': 'Load more',
      'watches.targetRequired': 'Target link is required.',
      'action.cancel': 'Cancel',
      'action.save': 'Save',
      'channel.title': 'Channel download',
      'channel.meta': 'Create downloads after filtering',
      'channel.link': 'Channel link',
      'channel.startDate': 'Start time',
      'channel.endDate': 'End time',
      'channel.types': 'Download types',
      'channel.keywords': 'Keywords',
      'channel.keywordsPlaceholder': 'Comma-separated, optional',
      'channel.includeComment': 'Include discussion replies',
      'channel.hint': 'Channel download scans matching messages and creates download tasks. Runtime depends on channel history size.',
      'channel.create': 'Create channel download',
      'channel.accepted': 'Channel download accepted.',
      'uploads.title': 'Local upload',
      'uploads.meta': 'Server path',
      'uploads.path': 'Local path',
      'uploads.target': 'Target channel',
      'uploads.recursive': 'Upload folder recursively',
      'uploads.serverPathHint': 'The path is on the server or container running TRMD, not on this browser device. With recursion off, a folder uploads only its top-level files; with recursion on, subfolders are included.',
      'uploads.create': 'Create upload',
      'uploads.accepted': 'Upload request accepted.',
      'statistics.title': 'Statistics and export',
      'statistics.meta': 'Runtime data',
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
      'statistics.exported': 'Table exported to: {directory}',
      'tasks.title': 'Transfer tasks',
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
      'items.title': 'File progress',
      'items.selectTask': 'Select a task',
      'items.empty': 'No file records for this task yet.',
      'items.tabsLabel': 'File status categories',
      'items.tab.running': 'Running',
      'items.tab.success': 'Completed',
      'items.tab.skipped': 'Skipped',
      'items.tab.failure': 'Failed',
      'items.empty.running': 'No running files in this task.',
      'items.empty.success': 'No completed files in this task.',
      'items.empty.skipped': 'No skipped files in this task.',
      'items.empty.failure': 'No failed files in this task.',
      'items.retryFailed': 'Retry failed items in this task',
      'items.page.previous': 'Previous',
      'items.page.next': 'Next',
      'items.page.status': 'Page {page} / {pages}',
      'items.page.range': '{start}-{end} / {total}',
      'items.download': 'Download',
      'items.upload': 'Upload',
      'items.loadMore': 'Load more files',
      'items.remaining': 'remaining',
      'events.title': 'Latest events',
      'events.empty': 'No events recorded.',
      'events.loadMore': 'Load more events',
      'events.remaining': 'remaining',
      'settings.title': 'Settings',
      'settings.safeNote': 'Sensitive fields only show configured state',
      'settings.paths': 'Paths and tasks',
      'settings.saveDirectory': 'Save directory',
      'settings.tempDirectory': 'Temp directory',
      'settings.sessionDirectory': 'Session directory',
      'settings.maxDownload': 'Max download tasks',
      'settings.maxUpload': 'Max upload tasks',
      'settings.retryDownload': 'Download retries',
      'settings.retryUpload': 'Upload retries',
      'settings.pikpakMaxFileSize': 'PikPak size limit (bytes)',
      'settings.pikpakArchive': 'PikPak archive',
      'settings.pikpakArchiveEnable': 'Archive PikPak by source channel',
      'settings.pikpakArchiveRemote': 'PikPak rclone remote',
      'settings.pikpakArchiveSource': 'PikPak source folder',
      'settings.pikpakArchiveRoot': 'PikPak archive root',
      'settings.pikpakArchivePoll': 'Ingest poll seconds',
      'settings.pikpakArchiveInterval': 'Poll interval seconds',
      'settings.pikpakArchiveWindow': 'Match window seconds',
      'settings.behavior': 'Behavior',
      'settings.notice': 'Bot notifications',
      'settings.shutdown': 'Shutdown after exit',
      'settings.downloadUpload': 'Download then upload restricted forwards',
      'settings.uploadDelete': 'Delete local file after upload',
      'settings.pendingLimit': 'Upload-after-download queue',
      'settings.sensitive': 'Account and proxy',
      'settings.proxyPassword': 'Proxy password',
      'settings.secretConfigured': 'Configured; enter a new value to replace',
      'settings.secretNotConfigured': 'Not configured',
      'settings.downloadTypes': 'Download types',
      'settings.forwardTypes': 'Forward types',
      'settings.messageFilter': 'Message filter',
      'settings.mediaTypes': 'Media types',
      'settings.dateRange': 'Date range',
      'settings.keywords': 'Keywords',
      'settings.enabled': 'Enabled',
      'settings.startDate': 'Start date',
      'settings.endDate': 'End date',
      'settings.keywordList': 'Keywords (comma separated)',
      'settings.keywordPlaceholder': 'Enter keywords, separated by commas',
      'settings.exports': 'Table exports',
      'settings.exportLink': 'Link table',
      'settings.exportCount': 'Count table',
      'settings.exportUpload': 'Upload table',
      'settings.save': 'Save settings',
      'settings.saved': 'Settings saved.',
      'records.title': 'Download success records',
      'records.chat': 'Channel ID',
      'records.message': 'Message ID',
      'records.file': 'File',
      'records.size': 'Size',
      'records.updated': 'Updated',
      'records.empty': 'No download success records yet.',
      'form.createFailed': 'Create task failed.',
      'form.requestFailed': 'Request failed.',
      'form.creatingTransfer': 'Analyzing the source message range. Telegram flood waits can take a while; keep this page open.',
      'form.creatingTransferShort': 'Analyzing',
      'form.createSuccess': 'Task created and queued. You can close this page or keep watching progress.',
      'error.auth_required': 'Authentication required.',
      'error.invalid_task_id': 'Invalid task ID.',
      'error.task_not_found': 'Task not found.',
      'error.not_found': 'Resource not found.',
      'error.source_link_required': 'Source link is required.',
      'error.target_link_required': 'Target link is required.',
      'error.range_ids_required': 'Start ID and End ID must be provided together.',
      'error.range_end_before_start': 'End ID must be greater than or equal to Start ID.',
      'error.range_source_must_be_chat_link': 'Range transfer source must be a chat link, not a message link.',
      'error.transfer_range_detection_unavailable': 'Automatic message range detection is unavailable in this runtime.',
      'error.transfer_range_detection_failed': 'Automatic message range detection failed.',
      'error.transfer_range_empty': 'No accessible messages were found for the source.',
      'error.create_task_failed': 'Create task failed.',
      'error.update_settings_failed': 'Update settings failed.',
      'error.watch_source_conflict': 'The same source cannot have a download watch and a forward watch at the same time.',
      'error.watch_already_exists': 'Live watch already exists.',
      'error.watch_source_required': 'Watch source is required.',
      'error.watch_target_required': 'Watch target is required.',
      'error.invalid_payload': 'Invalid request payload.',
      'error.invalid_watch_type': 'Invalid live watch type.',
      'error.invalid_watch_source': 'Watch source must start with https://t.me/.',
      'error.invalid_watch_target': 'Watch target must start with https://t.me/.',
      'error.watch_operations_unavailable': 'Live watch operations are unavailable.',
      'error.upload_path_not_found': 'Path not found on the server or container.',
      'error.upload_path_required': 'Upload path is required.',
      'error.upload_target_required': 'Upload target is required.',
      'error.upload_recursive_requires_directory': 'Recursive upload requires a folder path.',
      'error.invalid_upload_target': 'Upload target must be a Telegram link, me, or self.',
      'error.upload_operations_unavailable': 'Upload operations are unavailable.',
      'error.invalid_table_type': 'Invalid table type.',
      'error.table_operations_unavailable': 'Table operations are unavailable.',
      'error.invalid_channel_link': 'Channel link must start with https://t.me/.',
      'error.channel_link_required': 'Channel link is required.',
      'error.channel_download_type_required': 'Select at least one download type.',
      'error.invalid_channel_download_type': 'Invalid channel download type.',
      'error.channel_download_operations_unavailable': 'Channel download operations are unavailable.',
      'error.invalid_date_range': 'Invalid date range.',
      'error.date_range_end_before_start': 'End time must be greater than or equal to start time.',
      'action.taskUpdated': 'Task action submitted.',
      'event.level.info': 'info',
      'event.level.warning': 'warning',
      'event.level.error': 'error',
      'event.fileReady': 'File ready for target upload: {name}',
      'event.sentToTarget': 'Sent to target: {name}',
      'event.uploadFailed': 'Upload failed: {reason}',
      'event.reusedDownload': 'Reused download success record: {name}',
      'event.directForward': 'Directly sent to target: {link}',
      'event.rangeAssigned': 'Range transfer assigned: {range}',
      'event.rangeAssignedWithFallback': 'Range transfer assigned: {range}; fallback downloads: {count}.',
      'event.singleAssigned': 'Single-message transfer assigned.',
      'event.singleAssignedWithFallback': 'Single-message transfer assigned; fallback downloads: {count}.',
      'status.pending': 'pending',
      'status.running': 'running',
      'status.paused': 'paused',
      'status.success': 'success',
      'status.failure': 'failure',
      'status.skipped': 'skipped',
      'nav.media': 'Media',
      'media.title': 'Media Management',
      'media.meta': 'Scan and clean residual media files on disk',
      'media.scan': 'Scan for cleanable files',
      'media.scanning': 'Scanning...',
      'media.totalFiles': 'Cleanable files',
      'media.totalSize': 'Total size',
      'media.retentionDays': 'Retention days',
      'media.transferItems': 'Transfer task files',
      'media.orphanFiles': 'Orphan files (exceeding retention)',
      'media.file': 'File',
      'media.size': 'Size',
      'media.status': 'Task status',
      'media.source': 'Source',
      'media.path': 'Path',
      'media.mtime': 'Last modified',
      'media.cleanup': 'Clean selected',
      'media.cleaning': 'Cleaning...',
      'media.selected': 'Selected',
      'media.files': 'files',
      'media.noSelection': 'Select files to clean first.',
      'media.confirmCleanup': 'Are you sure you want to delete selected files? This cannot be undone.',
      'media.cleanupDone': 'Cleanup done: {count} files deleted ({size}).',
      'media.cleanupHistory': 'Cleanup history',
      'media.reason': 'Reason',
      'media.time': 'Time',
      'media.filterByTask': 'Filter by task:',
      'media.allTasks': 'All tasks'
    }
  };

  const state = {
    lang: localStorage.getItem('trmd-lang') || 'zh',
    selectedTaskId: null,
    settings: null,
    schema: null,
    tasks: [],
    items: [],
    events: [],
    records: [],
    watches: [],
    statistics: null,
    lastSync: null,
    activeItemStatus: 'running',
    itemPages: {
      running: 1,
      success: 1,
      skipped: 1,
      failure: 1
    },
    itemsTotal: 0,
    eventsTotal: 0,
    itemsOffset: 0,
    eventsOffset: 0,
    hasMoreItems: false,
    hasMoreEvents: false,
    taskPollTimer: null,
    loadingDetail: false
  };

  const $ = selector => document.querySelector(selector);
  const $$ = selector => Array.from(document.querySelectorAll(selector));
  const ITEMS_PAGE_SIZE = 10;
  const ITEM_STATUS_TABS = ['running', 'success', 'skipped', 'failure'];

  function t(key) {
    return (i18n[state.lang] && i18n[state.lang][key]) || i18n.zh[key] || key;
  }

  function interpolate(template, values) {
    return String(template).replace(/\{(\w+)}/g, (_, key) => values[key] ?? '');
  }

  function esc(value) {
    return String(value ?? '').replace(/[&<>"']/g, ch => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[ch]));
  }

  function pct(current, total) {
    current = Number(current || 0);
    total = Number(total || 0);
    return total > 0 ? Math.min(100, Math.round((current / total) * 100)) : 0;
  }

  function formatBytes(value) {
    value = Number(value || 0);
    const units = ['B', 'KiB', 'MiB', 'GiB'];
    let unit = 0;
    while (value >= 1024 && unit < units.length - 1) {
      value = value / 1024;
      unit += 1;
    }
    return `${value.toFixed(unit ? 1 : 0)} ${units[unit]}`;
  }

  function translateApiError(payload, fallbackKey = 'form.requestFailed') {
    if (payload && payload.error_code) {
      const key = `error.${payload.error_code}`;
      const message = t(key);
      return message === key ? (payload.error || t(fallbackKey)) : message;
    }
    return (payload && payload.error) || t(fallbackKey);
  }

  function showNotice(selector, message, ok = true) {
    const notice = $(selector);
    if (!notice) return;
    notice.textContent = message;
    notice.classList.toggle('ok', ok);
    notice.classList.add('is-visible');
  }

  function showFormMessage(message, ok = true) {
    const formNotice = $('#form-error');
    formNotice.textContent = message;
    formNotice.classList.toggle('ok', ok);
    formNotice.classList.add('is-visible');
  }

  async function withLoading(button, task) {
    const previous = button ? button.disabled : false;
    if (button) button.disabled = true;
    try {
      return await task();
    } finally {
      if (button) button.disabled = previous;
    }
  }

  async function fetchJson(path) {
    const res = await fetch(path);
    const data = await res.json();
    if (!res.ok) throw data;
    return data;
  }

  async function postJson(path, payload) {
    const res = await fetch(path, {
      method: 'POST',
      headers: {'content-type': 'application/json'},
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw data;
    return data;
  }

  function localizeEventMessage(event) {
    const message = String((event && event.message) || '');
    let match = message.match(/^File ready for target upload: (.+)$/);
    if (match) return interpolate(t('event.fileReady'), {name: match[1]});
    match = message.match(/^Sent to target: (.+)$/);
    if (match) return interpolate(t('event.sentToTarget'), {name: match[1]});
    match = message.match(/^Upload failed: (.+)$/);
    if (match) return interpolate(t('event.uploadFailed'), {reason: match[1]});
    match = message.match(/^Reused download success record: (.+)$/);
    if (match) return interpolate(t('event.reusedDownload'), {name: match[1]});
    match = message.match(/^Direct forward succeeded: (.+)$/);
    if (match) return interpolate(t('event.directForward'), {link: match[1]});
    match = message.match(/^Range transfer assigned: (.+)\. Fallback downloads: (\d+)\.$/);
    if (match) return interpolate(t('event.rangeAssignedWithFallback'), {range: match[1], count: match[2]});
    match = message.match(/^Range transfer assigned: (.+)\.$/);
    if (match) return interpolate(t('event.rangeAssigned'), {range: match[1]});
    match = message.match(/^Single-message transfer assigned\. Fallback downloads: (\d+)\.$/);
    if (match) return interpolate(t('event.singleAssignedWithFallback'), {count: match[1]});
    if (message === 'Single-message transfer assigned.') return t('event.singleAssigned');
    return message;
  }

  function localizeEventLevel(level) {
    const key = `event.level.${level}`;
    const translated = t(key);
    return translated === key ? level : translated;
  }

  function applyLanguage() {
    document.documentElement.lang = state.lang === 'zh' ? 'zh-CN' : 'en';
    document.title = t('app.title');
    $('#language-select').value = state.lang;
    $$('[data-i18n]').forEach(el => {
      el.textContent = t(el.dataset.i18n);
    });
    $$('[data-i18n-placeholder]').forEach(el => {
      el.placeholder = t(el.dataset.i18nPlaceholder);
    });
    $$('[data-i18n-aria-label]').forEach(el => {
      el.setAttribute('aria-label', t(el.dataset.i18nAriaLabel));
    });
    $$('[data-i18n-title]').forEach(el => {
      el.setAttribute('title', t(el.dataset.i18nTitle));
    });
  }

  function refreshVisibleDynamicText() {
    renderTasks();
    $('#selected-task').textContent = state.selectedTaskId ? `#${state.selectedTaskId}` : t('items.selectTask');
    renderItems(state.items);
    renderEvents(state.events);
    renderRecords();
    if (state.settings) fillSettingsForm();
  }

  function applyLanguageAndRefresh() {
    applyLanguage();
    refreshVisibleDynamicText();
  }

  async function handleLogout() {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
    } catch (_) { /* proceed regardless */ }
    window.location.href = '/';
  }

  function switchView(view) {
    $$('.view').forEach(el => el.classList.toggle('active', el.id === `view-${view}`));
    $$('[data-nav]').forEach(el => el.classList.toggle('active', el.dataset.nav === view));
    if (view === 'settings') loadSettings();
    if (view === 'records') loadRecords();
    if (view === 'watches') loadWatches();
    if (view === 'statistics') loadStatistics();
  }

  function badge(status) {
    return `<span class="badge ${esc(status)}">${esc(t(`status.${status}`))}</span>`;
  }

  function taskProgress(task) {
    const total = Number(task.total_items || 0);
    const done = Number(task.completed_items || 0);
    const failed = Number(task.failed_items || 0);
    const percent = total > 0 ? Math.round(((done + failed) / total) * 100) : 0;
    const progressLabel = `${percent}% · ${done}/${total}${failed ? ` · ${failed} ${t('side.failed')}` : ''}`;
    return `
      <div class="task-progress" aria-label="${esc(progressLabel)}">
        <div class="task-progress__head">
          <span class="task-progress__percent">${percent}%</span>
          <span class="task-progress__detail">
            ${done}/${total}${failed ? ` <span class="task-progress__failed">${failed} ${esc(t('side.failed'))}</span>` : ''}
          </span>
        </div>
        <div class="progress" title="${esc(progressLabel)}"><div style="width:${percent}%"></div></div>
      </div>
    `;
  }

  function renderTasks() {
    const tasks = state.tasks || [];
$('#metric-failed').textContent = tasks.filter(task => task.status === 'failure').length;
    if (state.lastSync) $('#last-sync').textContent = state.lastSync;
    $('#empty').style.display = tasks.length ? 'none' : 'block';
    $('#tasks').innerHTML = tasks.map(task => `
      <tr data-task-id="${task.id}">
        <td class="mono">#${task.id}</td>
        <td>${badge(task.status)}</td>
        <td class="mono">${esc(task.source_link)}</td>
        <td class="mono">${esc(task.target_link)}</td>
        <td>${taskProgress(task)}</td>
        <td>
           <div class="task-actions">
            ${task.status === 'running' || task.status === 'paused'
            ? `<button class="secondary icon-only" type="button" title="${esc(t(task.status === 'paused' ? 'tasks.resume' : 'tasks.pause'))}" aria-label="${esc(t(task.status === 'paused' ? 'tasks.resume' : 'tasks.pause'))}" onclick="${task.status === 'paused' ? `resumeTask(event, ${task.id})` : `pauseTask(event, ${task.id})`}">
              ${task.status === 'paused'
                ? '<svg viewBox="0 0 24 24" fill="none"><path d="M8 5v14l11-7L8 5Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>'
                : '<svg viewBox="0 0 24 24" fill="none"><path d="M8 5v14M16 5v14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'}
              <span class="sr-only">${esc(t(task.status === 'paused' ? 'tasks.resume' : 'tasks.pause'))}</span>
            </button>`
            : ''}
            <button class="secondary icon-only" type="button" title="${esc(t('tasks.retryFailed'))}" aria-label="${esc(t('tasks.retryFailed'))}" onclick="retryFailedTask(event, ${task.id})" ${Number(task.failed_items || 0) ? '' : 'disabled'}>
              <svg viewBox="0 0 24 24" fill="none"><path d="M20 12a8 8 0 1 1-2.34-5.66M20 4v5h-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 8v4l3 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
              <span class="sr-only">${esc(t('tasks.retryFailed'))}</span>
            </button>
            <button class="danger icon-only" type="button" title="${esc(t('tasks.delete'))}" aria-label="${esc(t('tasks.delete'))}" onclick="deleteTask(event, ${task.id})">
              <svg viewBox="0 0 24 24" fill="none"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 14h10l1-14M9 7V4h6v3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              <span class="sr-only" data-i18n="tasks.delete">${esc(t('tasks.delete'))}</span>
            </button>
          </div>
        </td>
      </tr>
    `).join('');
    $$('tr[data-task-id]').forEach(row => {
      row.addEventListener('click', () => loadTask(row.dataset.taskId));
    });
  }

  async function loadTasks() {
    const res = await fetch('/api/tasks');
    const data = await res.json();
    state.tasks = data.tasks || [];
    state.lastSync = new Date().toLocaleTimeString();
    renderTasks();
    if (!state.selectedTaskId && state.tasks[0]) {
      await loadTaskDetail(state.tasks[0].id, true);
    } else if (state.selectedTaskId) {
      await loadTaskSummary(state.selectedTaskId);
    } else {
      state.items = [];
      state.events = [];
      state.itemsTotal = 0;
      state.eventsTotal = 0;
      $('#selected-task').textContent = t('items.selectTask');
      renderItems();
      renderEvents();
    }
  }

  async function loadTaskSummary(id) {
    const taskId = Number(id);
    const res = await fetch(`/api/tasks/${taskId}/summary`);
    if (!res.ok) return;
    const data = await res.json();
    if (data && data.task) {
      state.selectedTaskId = taskId;
      state.itemsTotal = data.item_count || 0;
      state.eventsTotal = data.event_count || 0;
      updateTaskSummaryDisplay(data.task);
      if (data.recent_events && data.recent_events.length) {
        mergeRecentEvents(data.recent_events);
      }
    }
  }

  function updateTaskSummaryDisplay(task) {
    $('#selected-task').textContent = `#${task.id}`;
    renderEventCount();
  }

  async function loadTaskDetail(id, keepExistingItems) {
    const taskId = Number(id);
    if (state.selectedTaskId !== taskId) {
      resetItemPages();
      state.items = [];
      state.events = [];
      state.itemsOffset = 0;
      state.eventsOffset = 0;
      state.hasMoreItems = false;
      state.hasMoreEvents = false;
    }
    state.selectedTaskId = taskId;
    state.loadingDetail = true;
    try {
      const res = await fetch(`/api/tasks/${taskId}?items_limit=200&items_offset=0&events_limit=100&events_offset=0`);
      if (!res.ok) {
        state.selectedTaskId = null;
        state.items = [];
        state.events = [];
        $('#selected-task').textContent = t('items.selectTask');
        renderItems();
        renderEvents();
        return;
      }
      const data = await res.json();
      $('#selected-task').textContent = `#${taskId}`;
      state.items = data.items || [];
      state.events = data.events || [];
      state.itemsTotal = data.item_count || 0;
      state.eventsTotal = data.event_count || 0;
      state.itemsOffset = data.items_offset || 0;
      state.eventsOffset = data.events_offset || 0;
      state.hasMoreItems = data.has_more_items || false;
      state.hasMoreEvents = data.has_more_events || false;
      renderItems();
      renderEvents();
    } finally {
      state.loadingDetail = false;
    }
  }

  async function loadMoreItems() {
    if (state.loadingDetail) return;
    const taskId = state.selectedTaskId;
    if (!taskId) return;
    const offset = state.itemsOffset + 200;
    state.loadingDetail = true;
    try {
      const res = await fetch(`/api/tasks/${taskId}?items_limit=200&items_offset=${offset}&events_limit=0&events_offset=0`);
      if (!res.ok) return;
      const data = await res.json();
      state.items = state.items.concat(data.items || []);
      state.itemsTotal = data.item_count || state.itemsTotal;
      state.itemsOffset = offset;
      state.hasMoreItems = data.has_more_items || false;
      renderItems();
    } finally {
      state.loadingDetail = false;
    }
  }

  async function loadMoreEvents() {
    if (state.loadingDetail) return;
    const taskId = state.selectedTaskId;
    if (!taskId) return;
    const offset = state.eventsOffset + 100;
    state.loadingDetail = true;
    try {
      const res = await fetch(`/api/tasks/${taskId}?items_limit=0&items_offset=0&events_limit=100&events_offset=${offset}`);
      if (!res.ok) return;
      const data = await res.json();
      state.events = state.events.concat(data.events || []);
      state.eventsTotal = data.event_count || state.eventsTotal;
      state.eventsOffset = offset;
      state.hasMoreEvents = data.has_more_events || false;
      renderEvents();
    } finally {
      state.loadingDetail = false;
    }
  }

  // 保留 loadTask 作为点击任务时的入口
  async function loadTask(id) {
    await loadTaskDetail(id, false);
  }

  function progressLine(label, current, total) {
    const percent = pct(current, total);
    return `<div><div>${esc(label)} ${percent}%</div><div class="progress"><div style="width:${percent}%"></div></div><div class="mono">${formatBytes(current)} / ${formatBytes(total)}</div></div>`;
  }

  function itemStatusGroup(item) {
    const status = String((item && item.status) || 'pending');
    if (status === 'success' || status === 'skipped' || status === 'failure') return status;
    if (['pending', 'running'].includes(status)) return 'running';
    return 'running';
  }

  function categorizedItems(items) {
    const groups = {
      running: [],
      success: [],
      skipped: [],
      failure: []
    };
    (items || []).forEach(item => {
      groups[itemStatusGroup(item)].push(item);
    });
    return groups;
  }

  function itemPageState(total) {
    const pages = Math.max(1, Math.ceil(total / ITEMS_PAGE_SIZE));
    const current = Math.min(Math.max(Number(state.itemPages[state.activeItemStatus] || 1), 1), pages);
    state.itemPages[state.activeItemStatus] = current;
    const startIndex = (current - 1) * ITEMS_PAGE_SIZE;
    const endIndex = Math.min(startIndex + ITEMS_PAGE_SIZE, total);
    return {current, pages, startIndex, endIndex};
  }

  function renderItemTabs(groups) {
    ITEM_STATUS_TABS.forEach(status => {
      const tab = $(`[data-item-tab="${status}"]`);
      const count = $(`[data-item-count="${status}"]`);
      if (!tab || !count) return;
      const active = state.activeItemStatus === status;
      tab.classList.toggle('active', active);
      tab.setAttribute('aria-selected', active ? 'true' : 'false');
      count.textContent = groups[status].length;
    });
  }

  function renderItems(items) {
    items = items || state.items;
    const groups = categorizedItems(items);
    const activeItems = groups[state.activeItemStatus] || [];
    const page = itemPageState(activeItems.length);
    const visibleItems = activeItems.slice(page.startIndex, page.endIndex);
    renderItemTabs(groups);
    const retryButton = $('#retry-selected-failed');
    if (retryButton) {
      retryButton.disabled = !(state.selectedTaskId && groups.failure.length);
      retryButton.style.display = state.activeItemStatus === 'failure' ? 'inline-flex' : 'none';
    }
    const loadMoreHtml = state.hasMoreItems
      ? `<div class="load-more-row"><button type="button" class="load-more-btn" onclick="loadMoreItems()">
          ${esc(t('items.loadMore'))} (${state.itemsTotal - items.length} ${esc(t('items.remaining'))})
        </button></div>`
      : '';
    $('#items').innerHTML = (visibleItems.length ? visibleItems.map(item => `
      <div class="file-row">
        <div>
          <div>${esc(item.file_name || item.local_path || item.source_link || `#${item.source_message_id || item.id}`)}</div>
          <div class="mono">${esc(item.source_chat_id || '')} ${esc(item.source_message_id || '')}</div>
        </div>
        <div>${badge(item.status)}</div>
        ${progressLine(t('items.download'), item.download_current, item.download_total)}
        ${progressLine(t('items.upload'), item.upload_current, item.upload_total)}
      </div>
    `).join('') : `<div class="empty">${esc(t(`items.empty.${state.activeItemStatus}`))}</div>`) + loadMoreHtml;

    const range = activeItems.length
      ? interpolate(t('items.page.range'), {
        start: page.startIndex + 1,
        end: page.endIndex,
        total: activeItems.length
      })
      : interpolate(t('items.page.range'), {start: 0, end: 0, total: 0});
    $('#items-page-range').textContent = range;
    $('#items-page-summary').textContent = interpolate(t('items.page.status'), {
      page: page.current,
      pages: page.pages
    });
    $('#items-page-prev').disabled = page.current <= 1;
    $('#items-page-next').disabled = page.current >= page.pages;
  }

  function resetItemPages() {
    ITEM_STATUS_TABS.forEach(status => {
      state.itemPages[status] = 1;
    });
  }

  function switchItemTab(status) {
    if (!ITEM_STATUS_TABS.includes(status)) return;
    state.activeItemStatus = status;
    renderItems(state.items);
  }

  function renderEvents() {
    const events = state.events || [];
    const countText = state.eventsTotal > events.length
      ? `${events.length} / ${state.eventsTotal}`
      : String(events.length);
    $('#event-count').textContent = countText;
    const loadMoreHtml = state.hasMoreEvents
      ? `<div class="load-more-row"><button type="button" class="load-more-btn" onclick="loadMoreEvents()">
          ${esc(t('events.loadMore'))} (${state.eventsTotal - events.length} ${esc(t('events.remaining'))})
        </button></div>`
      : '';
    $('#events').innerHTML = (events.length ? events.map(event => `
      <div class="event">
        <time>${esc(event.created_at)}</time>
        <span>${esc(localizeEventLevel(event.level))}</span>
        <div>${esc(localizeEventMessage(event))}</div>
      </div>
    `).join('') : `<div class="empty">${esc(t('events.empty'))}</div>`) + loadMoreHtml;
  }

  function renderEventCount() {
    if (state.events && state.events.length) {
      const countText = state.eventsTotal > state.events.length
        ? `${state.events.length} / ${state.eventsTotal}`
        : String(state.events.length);
      $('#event-count').textContent = countText;
    }
  }

  function mergeRecentEvents(recentEvents) {
    const existingIds = new Set((state.events || []).map(function(e) { return e.id; }));
    var newEvents = recentEvents.filter(function(e) { return !existingIds.has(e.id); });
    if (!newEvents.length) return;
    var merged = state.events || [];
    newEvents.sort(function(a, b) { return (b.id || 0) - (a.id || 0); });
    merged = newEvents.concat(merged);
    merged.sort(function(a, b) { return (b.id || 0) - (a.id || 0); });
    var maxKeep = Math.max(state.eventsTotal || 0, merged.length, 200);
    state.events = merged.slice(0, maxKeep);
    renderEvents();
  }

  async function loadWatches() {
    const res = await fetch('/api/watches');
    const data = await res.json();
    state.watches = data.watches || [];
    renderWatches();
  }

  async function refreshWatchesAfterMutation() {
    try {
      await loadWatches();
    } catch (error) {
      console.warn('Failed to refresh watches after mutation.', error);
    }
  }

  function renderWatches() {
    const watches = state.watches || [];
    $('#watch-count').textContent = watches.length;
    $('#watches-empty').style.display = watches.length ? 'none' : 'block';
    $('#watches').innerHTML = watches.map(watch => {
      const sanitized = (watch.id || '').replace(/:/g, '_');
      const ec = watch.event_count || 0;
      const eventBadge = watch.type === 'forward' && ec ? ` <span class="badge info">${ec}</span>` : '';
      const rowClick = watch.type === 'forward' ? ` class="watch-row" onclick="toggleWatchEvents('${encodeURIComponent(watch.id)}')"` : '';
      const eventsRow = watch.type === 'forward' ? `
      <tr class="watch-events-row" id="watch-events-${sanitized}">
        <td colspan="5"><div class="watch-events-panel" id="watch-events-panel-${sanitized}"></div></td>
      </tr>` : '';
      return `<tr${rowClick}>
        <td>${esc(t(`watches.${watch.type}`))}</td>
        <td>${badge(watch.status || 'running')}${eventBadge}</td>
        <td class="mono">${esc(watch.source_link || '')}</td>
        <td class="mono">${esc(watch.target_link || '')}${watch.include_comment ? `<div>${esc(t('watches.includeComment'))}</div>` : ''}${watch.error_message ? `<div>${esc(watch.error_message)}</div>` : ''}</td>
        <td>
          ${watch.type === 'forward' ? `<button class="secondary" type="button" onclick="event.stopPropagation(); openEditWatchModal('${encodeURIComponent(watch.id)}','${encodeURIComponent(watch.source_link || '')}','${encodeURIComponent(watch.target_link || '')}','${watch.include_comment ? '1' : '0'}')">
            <svg viewBox="0 0 24 24" fill="none"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span data-i18n="watches.edit">${esc(t('watches.edit'))}</span>
          </button>` : ''}
          <button class="danger" type="button" onclick="event.stopPropagation(); deleteWatch('${encodeURIComponent(watch.id)}')">
            <svg viewBox="0 0 24 24" fill="none"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 14h10l1-14M9 7V4h6v3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span data-i18n="watches.delete">${esc(t('watches.delete'))}</span>
          </button>
        </td>
      </tr>${eventsRow}`;
    }).join('');
  }

  async function toggleWatchEvents(encodedId) {
    const watchId = decodeURIComponent(encodedId);
    const sanitized = watchId.replace(/:/g, '_');
    const row = document.getElementById(`watch-events-${sanitized}`);
    if (!row) return;
    const isOpen = row.classList.contains('open');
    if (isOpen) {
      row.classList.remove('open');
      return;
    }
    row.classList.add('open');
    await loadWatchEvents(watchId, sanitized, 0);
  }
  window.toggleWatchEvents = toggleWatchEvents;

  async function loadWatchEvents(watchId, sanitized, offset) {
    const panel = document.getElementById(`watch-events-panel-${sanitized}`);
    if (!panel) return;
    if (offset === 0) panel.innerHTML = `<div class="watch-event-item">${esc(t('watches.eventLoading'))}</div>`;
    try {
      const res = await fetch(`/api/watches/${encodeURIComponent(watchId)}/events?limit=50&offset=${offset}`);
      const data = await res.json();
      if (!res.ok) { panel.innerHTML = `<div class="watch-event-item">${esc(data.error || 'Load failed')}</div>`; return; }
      const items = data.events || [];
      if (offset === 0) panel.innerHTML = '';
      if (!items.length && offset === 0) {
        panel.innerHTML = `<div class="watch-event-item">${esc(t('watches.noEvents'))}</div>`;
        return;
      }
      items.forEach(evt => {
        const time = new Date(evt.created_at + 'Z').toLocaleString();
        const statusClass = evt.status === 'success' ? 'success' : 'warning';
        const statusLabel = evt.status === 'success' ? t('watches.eventForwarded') : t('watches.eventSkipped');
        const div = document.createElement('div');
        div.className = 'watch-event-item';
        div.innerHTML = `<span class="watch-event-time">${esc(time)}</span>`
          + `<span class="watch-event-badge"><span class="badge ${statusClass}">${esc(statusLabel)}</span></span>`
          + `<span class="watch-event-info">${esc(evt.message)} ${esc(t('watches.source'))}: #${esc(String(evt.source_message_id || ''))} → ${esc(t('watches.target'))}: ${esc(evt.target_link || evt.target_chat_id || '')}</span>`;
        panel.appendChild(div);
      });
      if (data.has_more) {
        const btn = document.createElement('button');
        btn.className = 'watch-events-load-more small';
        btn.textContent = t('watches.loadMore');
        btn.onclick = () => loadWatchEvents(watchId, sanitized, offset + items.length);
        panel.appendChild(btn);
      }
    } catch (e) {
      panel.innerHTML = `<div class="watch-event-item">${esc(t('form.requestFailed'))}</div>`;
    }
  }

  async function deleteWatch(encodedId) {
    if (!window.confirm(t('watches.delete'))) return;
    const res = await fetch(`/api/watches/${encodedId}`, {method: 'DELETE'});
    const data = await res.json();
    if (!res.ok) {
      showNotice('#watch-download-notice', translateApiError(data), false);
      return;
    }
    showNotice('#watch-download-notice', t('watches.deleted'), true);
    await loadWatches();
  }
  window.deleteWatch = deleteWatch;

  let editingWatchId = null;

  function openEditWatchModal(encodedId, encodedSource, encodedTarget, includeCommentFlag) {
    editingWatchId = decodeURIComponent(encodedId);
    document.getElementById('watch-edit-type').value = t('watches.forward');
    document.getElementById('watch-edit-source').value = decodeURIComponent(encodedSource);
    document.getElementById('watch-edit-target').value = decodeURIComponent(encodedTarget);
    document.getElementById('watch-edit-include-comment').checked = includeCommentFlag === '1';
    document.getElementById('watch-edit-notice').style.display = 'none';
    document.getElementById('watch-edit-notice').textContent = '';
    document.getElementById('watch-edit-overlay').classList.add('open');
    document.getElementById('watch-edit-target').focus();
  }
  window.openEditWatchModal = openEditWatchModal;

  function closeEditWatchModal() {
    editingWatchId = null;
    document.getElementById('watch-edit-overlay').classList.remove('open');
  }
  window.closeEditWatchModal = closeEditWatchModal;

  async function submitEditWatch(event) {
    event.preventDefault();
    const button = event.submitter;
    const target = document.getElementById('watch-edit-target').value.trim();
    const includeComment = document.getElementById('watch-edit-include-comment').checked;
    if (!target) {
      showEditWatchNotice(t('watches.targetRequired'), false);
      return;
    }
    await withLoading(button, async () => {
      try {
        await fetch(`/api/watches/${encodeURIComponent(editingWatchId)}`, {
          method: 'PUT',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({target_link: target, include_comment: includeComment})
        }).then(res => res.json().then(data => res.ok ? data : Promise.reject(data)));
      } catch (payload) {
        showEditWatchNotice(translateApiError(payload), false);
        return;
      }
      showEditWatchNotice(t('watches.updated'), true);
      closeEditWatchModal();
      await refreshWatchesAfterMutation();
    });
  }
  window.submitEditWatch = submitEditWatch;

  function showEditWatchNotice(message, success) {
    const el = document.getElementById('watch-edit-notice');
    el.textContent = message;
    el.className = 'notice is-visible' + (success ? ' ok' : '');
  }

  async function loadStatistics() {
    const res = await fetch('/api/statistics');
    const data = await res.json();
    state.statistics = data;
    renderStatistics();
  }

  function renderStatistics() {
    const tables = (state.statistics && state.statistics.tables) || {};
    const rows = ['link', 'count', 'upload'];
    $('#statistics').innerHTML = rows.map(type => {
      const table = tables[type] || {};
      const exportKey = type === 'link' ? 'statistics.exportLink' : type === 'count' ? 'statistics.exportCount' : 'statistics.exportUpload';
      return `
        <tr>
          <td>${esc(t(`statistics.${type}`))}</td>
          <td>${esc(table.available ? t('statistics.yes') : t('statistics.no'))}</td>
          <td class="mono">${esc(table.rows || 0)}</td>
          <td>
            <button type="button" onclick="exportTable('${type}')">
              <svg viewBox="0 0 24 24" fill="none"><path d="M12 5v10M8 11l4 4 4-4M5 20h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              <span>${esc(t(exportKey))}</span>
            </button>
          </td>
        </tr>
      `;
    }).join('');
  }

  async function exportTable(tableType) {
    try {
      const data = await postJson('/api/tables/export', {table_type: tableType});
      showNotice('#statistics-notice', interpolate(t('statistics.exported'), {directory: data.directory || ''}), true);
      await loadStatistics();
    } catch (payload) {
      showNotice('#statistics-notice', translateApiError(payload), false);
    }
  }
  window.exportTable = exportTable;

  async function postTaskAction(taskId, action) {
    const res = await fetch(`/api/tasks/${taskId}/${action}`, {method: 'POST'});
    const data = await res.json();
    if (!res.ok) throw data;
    return data;
  }

  async function runTaskAction(event, taskId, action) {
    event.stopPropagation();
    const button = event.currentTarget;
    await withLoading(button, async () => {
      try {
        await postTaskAction(taskId, action);
        showFormMessage(t('action.taskUpdated'), true);
        await loadTasks();
      } catch (payload) {
        showFormMessage(translateApiError(payload), false);
      }
    });
  }

  function pauseTask(event, taskId) {
    return runTaskAction(event, taskId, 'pause');
  }
  window.pauseTask = pauseTask;

  function resumeTask(event, taskId) {
    return runTaskAction(event, taskId, 'resume');
  }
  window.resumeTask = resumeTask;

  function retryFailedTask(event, taskId) {
    return runTaskAction(event, taskId, 'retry-failed');
  }
  window.retryFailedTask = retryFailedTask;

  async function deleteTask(event, taskId) {
    event.stopPropagation();
    const res = await fetch(`/api/tasks/${taskId}`, {method: 'DELETE'});
    if (res.ok && state.selectedTaskId === taskId) {
      state.selectedTaskId = null;
      state.items = [];
      state.events = [];
      resetItemPages();
      $('#selected-task').textContent = t('items.selectTask');
      renderItems();
      renderEvents();
    }
    await loadTasks();
  }
  window.deleteTask = deleteTask;

  function getPath(obj, path) {
    return path.split('.').reduce((cur, key) => cur && cur[key], obj);
  }

  function setPath(obj, path, value) {
    const parts = path.split('.');
    let cur = obj;
    parts.slice(0, -1).forEach(key => {
      cur[key] = cur[key] || {};
      cur = cur[key];
    });
    cur[parts[parts.length - 1]] = value;
  }

  async function loadSettings() {
    const res = await fetch('/api/settings');
    const data = await res.json();
    state.settings = data.settings || {};
    state.schema = data.schema || {};
    renderTypeSettings();
    fillSettingsForm();
  }

  function renderTypeSettings() {
    const downloadTypes = state.schema.download_type || [];
    const forwardTypes = state.schema.forward_type || [];
    const filterMediaTypes = (state.schema.message_filter && state.schema.message_filter.media_types) || forwardTypes;
    $('#download-type-settings').innerHTML = downloadTypes.map(type => `
      <label class="check-card"><input name="user.download_type" value="${esc(type)}" type="checkbox"><span>${esc(type)}</span></label>
    `).join('');
    var fwdEl = $('#forward-type-settings');
    if (fwdEl) {
      fwdEl.innerHTML = forwardTypes.map(type => `
        <label class="check-card"><input name="global.forward_type.${esc(type)}" type="checkbox"><span>${esc(type)}</span></label>
      `).join('');
    }
    // 消息过滤 — 媒体类型
    var filterEl = $('#filter-media-types');
    if (filterEl) {
      filterEl.innerHTML = filterMediaTypes.map(type => `
        <label class="check-card"><input name="global.message_filter.media_types.${esc(type)}" type="checkbox"><span>${esc(type)}</span></label>
      `).join('');
    }
  }

  function fillSettingsForm() {
    const form = $('#settings-form');
    Array.from(form.elements).forEach(el => {
      if (!el.name) return;
      if (el.name === 'user.download_type') {
        el.checked = (getPath(state.settings, 'user.download_type') || []).includes(el.value);
        return;
      }
      // 消息过滤 — 日期范围：timestamp → datetime-local
      if (el.name === 'global.message_filter.date_range.start_date' || el.name === 'global.message_filter.date_range.end_date') {
        const ts = getPath(state.settings, el.name);
        el.value = ts ? new Date(ts * 1000).toISOString().slice(0, 16) : '';
        return;
      }
      // 消息过滤 — 关键词：数组 → 逗号分隔字符串
      if (el.name === 'global.message_filter.keywords.words') {
        const words = getPath(state.settings, el.name);
        el.value = Array.isArray(words) ? words.join(', ') : '';
        return;
      }
      const value = getPath(state.settings, el.name);
      if (el.type === 'checkbox') {
        el.checked = Boolean(value);
      } else if (value && typeof value === 'object' && 'configured' in value) {
        el.placeholder = value.configured ? t('settings.secretConfigured') : t('settings.secretNotConfigured');
        el.value = '';
      } else {
        el.value = value ?? '';
      }
    });
  }

  function settingsPayload() {
    const payload = {};
    const downloadTypes = [];
    Array.from($('#settings-form').elements).forEach(el => {
      if (!el.name) return;
      if (el.name === 'user.download_type') {
        if (el.checked) downloadTypes.push(el.value);
        return;
      }
      // 消息过滤 — 日期范围：datetime-local → timestamp
      if (el.name === 'global.message_filter.date_range.start_date' || el.name === 'global.message_filter.date_range.end_date') {
        const v = el.value;
        setPath(payload, el.name, v ? (new Date(v).getTime() / 1000) : null);
        return;
      }
      // 消息过滤 — 关键词：逗号分隔字符串 → 数组
      if (el.name === 'global.message_filter.keywords.words') {
        const words = el.value ? el.value.split(',').map(function(s) { return s.trim(); }).filter(Boolean) : [];
        setPath(payload, el.name, words);
        return;
      }
      let value = el.type === 'checkbox' ? el.checked : el.value;
      if (el.type === 'number') value = value === '' ? null : Number(value);
      if (el.type === 'password' && value === '') return;
      setPath(payload, el.name, value);
    });
    setPath(payload, 'user.download_type', downloadTypes);
    return payload;
  }

  async function saveSettings(event) {
    event.preventDefault();
    const res = await fetch('/api/settings', {
      method: 'PATCH',
      headers: {'content-type': 'application/json'},
      body: JSON.stringify(settingsPayload())
    });
    const data = await res.json();
    const notice = $('#settings-notice');
    notice.style.display = 'block';
    notice.classList.toggle('ok', res.ok);
    notice.textContent = res.ok ? t('settings.saved') : translateApiError(data, 'error.update_settings_failed');
    if (res.ok) {
      state.settings = data.settings || {};
      state.schema = data.schema || state.schema;
      fillSettingsForm();
    }
  }

  async function createDownloadWatch(event) {
    event.preventDefault();
    const button = event.submitter;
    await withLoading(button, async () => {
      const sourceLinks = new FormData(event.currentTarget)
        .get('source_links')
        .split(/\r?\n/)
        .map(value => value.trim())
        .filter(Boolean);
      try {
        await postJson('/api/watches', {type: 'download', source_links: sourceLinks});
      } catch (payload) {
        showNotice('#watch-download-notice', translateApiError(payload), false);
        return;
      }
      showNotice('#watch-download-notice', t('watches.created'), true);
      event.currentTarget.reset();
      await refreshWatchesAfterMutation();
    });
  }

  async function createForwardWatch(event) {
    event.preventDefault();
    const button = event.submitter;
    await withLoading(button, async () => {
      const form = new FormData(event.currentTarget);
      try {
        await postJson('/api/watches', {
          type: 'forward',
          source_link: form.get('source_link'),
          target_link: form.get('target_link'),
          include_comment: Boolean(form.get('include_comment'))
        });
      } catch (payload) {
        showNotice('#watch-forward-notice', translateApiError(payload), false);
        return;
      }
      showNotice('#watch-forward-notice', t('watches.created'), true);
      event.currentTarget.reset();
      await refreshWatchesAfterMutation();
    });
  }

  async function createChannelDownload(event) {
    event.preventDefault();
    const button = event.submitter;
    await withLoading(button, async () => {
      const form = new FormData(event.currentTarget);
      const downloadType = Array.from(event.currentTarget.querySelectorAll('input[name="download_type"]:checked')).map(el => el.value);
      const keywords = String(form.get('keywords') || '').split(',').map(value => value.trim()).filter(Boolean);
      try {
        await postJson('/api/channel-downloads', {
          chat_link: form.get('chat_link'),
          date_range: {
            start_date: form.get('start_date') || null,
            end_date: form.get('end_date') || null
          },
          download_type: downloadType,
          keywords,
          include_comment: Boolean(form.get('include_comment'))
        });
        showNotice('#channel-download-notice', t('channel.accepted'), true);
      } catch (payload) {
        showNotice('#channel-download-notice', translateApiError(payload), false);
      }
    });
  }

  async function createUpload(event) {
    event.preventDefault();
    const button = event.submitter;
    await withLoading(button, async () => {
      const form = new FormData(event.currentTarget);
      try {
        await postJson('/api/uploads', {
          path: form.get('path'),
          target_link: form.get('target_link'),
          recursive: Boolean(form.get('recursive'))
        });
        showNotice('#upload-notice', t('uploads.accepted'), true);
      } catch (payload) {
        showNotice('#upload-notice', translateApiError(payload), false);
      }
    });
  }

  async function loadRecords() {
    const res = await fetch('/api/download-records');
    const data = await res.json();
    state.records = data.records || [];
    renderRecords();
  }

  function renderRecords() {
    const records = state.records || [];
    $('#record-count').textContent = records.length;
    $('#records-empty').style.display = records.length ? 'none' : 'block';
    $('#records').innerHTML = records.map(record => `
      <tr>
        <td class="mono">${esc(record.source_chat_id)}</td>
        <td class="mono">${esc(record.source_message_id)}</td>
        <td><div>${esc(record.file_name || '')}</div><div class="mono">${esc(record.local_path || '')}</div></td>
        <td>${formatBytes(record.file_size)}</td>
        <td class="mono">${esc(record.updated_at || record.downloaded_at)}</td>
      </tr>
    `).join('');
  }

  /* ====== 退出登录 ====== */
  var btnLogout = $('#btn-logout');
  if (btnLogout) btnLogout.addEventListener('click', handleLogout);
  var mobBtnLogout = $('#mob-btn-logout');
  if (mobBtnLogout) mobBtnLogout.addEventListener('click', handleLogout);
"""
WEB_UI_MOBILE_SCRIPT = SHARED_WEB_UI_SCRIPT + r"""
  /* ====== 登录流程（移动端） ====== */
  var authPollTimer = null;
  var authStep = '';

  function showLoginStep(step) {
    authStep = step;
    var steps = ['login-form-phone', 'login-form-code', 'login-form-password', 'login-form-recovery', 'login-form-signup', 'login-form-done'];
    steps.forEach(function(id) { var el = document.getElementById(id); if (el) el.style.display = 'none'; });
    var el = document.getElementById('login-form-' + step);
    if (el) el.style.display = '';
    var container = document.getElementById('login-container');
    if (container) container.classList.add('active');
    var loginError = document.getElementById('login-error');
    if (loginError) loginError.classList.remove('visible');
  }

  function hideLogin() {
    var container = document.getElementById('login-container');
    if (container) container.classList.remove('active');
    if (authPollTimer) { clearInterval(authPollTimer); authPollTimer = null; }
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
      if (resp.status === 401) return;
      var state = await resp.json();
      if (!state || !state.step) return;
      switch (state.step) {
        case 'pending':
          var container = document.getElementById('login-container');
          if (container) container.classList.remove('active');
          return;
        case 'done': case 'none':
          hideLogin();
          loadTasks();
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
            if (desc) desc.textContent = '\u9a8c\u8bc1\u7801\u5df2\u901a\u8fc7\u300c' + state.code_type + '\u300d\u53d1\u9001';
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
    var btn = document.querySelector('.login-submit');
    if (btn) btn.disabled = true;
    showLoginError('');
    try {
      await fetch('/api/auth/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      await new Promise(function(r) { setTimeout(r, 500); });
      await checkAuthStatus();
    } catch (e) {
      showLoginError('\u63d0\u4ea4\u5931\u8d25\uff0c\u8bf7\u91cd\u8bd5');
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  /* phone submit */
  var phoneBtn = document.getElementById('login-btn-phone');
  if (phoneBtn) {
    phoneBtn.addEventListener('click', function() {
      var phone = document.getElementById('login-phone').value.trim();
      if (!phone) { showLoginError('\u8bf7\u8f93\u5165\u7535\u8bdd\u53f7\u7801'); return; }
      if (!phone.startsWith('+')) { showLoginError('\u7535\u8bdd\u53f7\u7801\u9700\u4ee5 +\u5730\u533a\u53f7\u5f00\u5934'); return; }
      submitAuth({ phone: phone });
    });
  }

  var codeBtn = document.getElementById('login-btn-code');
  if (codeBtn) {
    codeBtn.addEventListener('click', function() {
      var code = document.getElementById('login-code').value.trim();
      if (!code) { showLoginError('\u8bf7\u8f93\u5165\u9a8c\u8bc1\u7801'); return; }
      submitAuth({ code: code });
    });
  }

  var backBtn = document.getElementById('login-btn-back');
  if (backBtn) {
    backBtn.addEventListener('click', function() {
      showLoginStep('phone');
      document.getElementById('login-code').value = '';
    });
  }

  var pwdBtn = document.getElementById('login-btn-password');
  if (pwdBtn) {
    pwdBtn.addEventListener('click', function() {
      var pwd = document.getElementById('login-password').value;
      submitAuth({ password: pwd });
    });
  }

  var pwdBackBtn = document.getElementById('login-btn-back-pwd');
  if (pwdBackBtn) {
    pwdBackBtn.addEventListener('click', function() {
      showLoginStep('code');
      document.getElementById('login-password').value = '';
    });
  }

  var recBtn = document.getElementById('login-btn-recovery');
  if (recBtn) {
    recBtn.addEventListener('click', function() {
      var code = document.getElementById('login-recovery').value.trim();
      if (!code) { showLoginError('\u8bf7\u8f93\u5165\u6062\u590d\u4ee3\u7801'); return; }
      submitAuth({ recovery_code: code });
    });
  }

  var recBackBtn = document.getElementById('login-btn-back-recovery');
  if (recBackBtn) {
    recBackBtn.addEventListener('click', function() {
      showLoginStep('password');
      document.getElementById('login-recovery').value = '';
    });
  }

  var signupBtn = document.getElementById('login-btn-signup');
  if (signupBtn) {
    signupBtn.addEventListener('click', function() {
      var first = document.getElementById('login-first-name').value.trim();
      if (!first) { showLoginError('\u8bf7\u8f93\u5165\u540d\u5b57'); return; }
      submitAuth({ first_name: first, last_name: document.getElementById('login-last-name').value.trim() });
    });
  }

  (function() {
    checkAuthStatus();
    authPollTimer = setInterval(function() {
      if (authStep === 'done' || authStep === 'none') {
        clearInterval(authPollTimer);
        authPollTimer = null;
        return;
      }
      checkAuthStatus();
    }, 2000);
  })();

  /* ====== 移动端初始化 ====== */
  function hasActiveTasks() {
    return state.tasks.some(function(t) { return t.status === 'pending' || t.status === 'running'; });
  }

  function startPolling() {
    if (state.taskPollTimer) return;
    var fastInterval = 3000;
    var slowInterval = 15000;
    var currentInterval = fastInterval;
    var lastPollTime = 0;

    async function poll() {
      if (document.hidden) { scheduleNext(currentInterval); return; }
      var now = Date.now();
      var minGap = currentInterval - 500;
      if (now - lastPollTime < minGap) { scheduleNext(currentInterval); return; }
      lastPollTime = now;
      try { await loadTasks(); } catch (e) { console.warn('Poll failed:', e); }
      currentInterval = hasActiveTasks() ? fastInterval : slowInterval;
      scheduleNext(currentInterval);
    }

    function scheduleNext(interval) {
      state.taskPollTimer = setTimeout(poll, interval);
    }

    poll();
  }

  function stopPolling() {
    if (state.taskPollTimer) {
      clearTimeout(state.taskPollTimer);
      state.taskPollTimer = null;
    }
  }

  /* ====== 移动端视图切换 ====== */
  function mobSwitchView(view) {
    $$('.mob-view').forEach(el => el.classList.toggle('active', el.id === `mob-view-${view}`));
    $$('.mob-tab').forEach(el => el.classList.toggle('active', el.dataset.mobNav === view));
    closeDrawer();
    closeFabMenu();
    if (view === 'settings') loadSettings();
    if (view === 'records') loadRecords();
    if (view === 'watches') loadWatches();
    if (view === 'statistics') loadStatistics();
    if (view === 'media') loadMediaMobile();
  }

  async function loadMediaMobile() {
    var info = $('#mob-media-result');
    info.innerHTML = '<p>' + t('media.scanning') + '</p>';
    try {
      var data = await fetchJson('/api/media/scan');
      var ti = data.transfer_items || {};
      var orph = data.orphan_files || {};
      var totalCount = data.total_count || 0;
      var totalSize = data.total_size || 0;
      info.innerHTML =
        '<p><strong>' + t('media.totalFiles') + ':</strong> ' + totalCount + '</p>' +
        '<p><strong>' + t('media.totalSize') + ':</strong> ' + formatBytes(totalSize) + '</p>';
    } catch (err) {
      info.innerHTML = '<p>' + translateApiError(err, 'form.requestFailed') + '</p>';
    }
  }

  // mobile media scan button
  var mobMediaBtn = $('#mob-media-scan-btn');
  if (mobMediaBtn) mobMediaBtn.addEventListener('click', loadMediaMobile);

  /* ====== 抽屉（更多菜单） ====== */
  function openDrawer() {
    $('#mob-drawer-overlay').classList.add('open');
  }
  function closeDrawer() {
    $('#mob-drawer-overlay').classList.remove('open');
  }

  /* ====== FAB 菜单 ====== */
  function toggleFabMenu() {
    const menu = $('#mob-fab-menu');
    const fab = $('#mob-fab');
    const isOpen = menu.classList.contains('open');
    if (isOpen) {
      menu.classList.remove('open');
      fab.textContent = '+';
    } else {
      menu.classList.add('open');
      fab.textContent = '\u00d7';
    }
  }
  function closeFabMenu() {
    const menu = $('#mob-fab-menu');
    const fab = $('#mob-fab');
    menu.classList.remove('open');
    fab.textContent = '+';
  }

  /* ====== 折叠面板 ====== */
  function toggleCollapse(head) {
    head.closest('.mob-collapse').classList.toggle('open');
  }

  /* ====== Toast ====== */
  let mobToastTimer = null;
  function showToast(message, duration) {
    if (duration === void 0) duration = 2500;
    const toast = $('#mob-toast');
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(mobToastTimer);
    mobToastTimer = setTimeout(function() { toast.classList.remove('show'); }, duration);
  }

  /* ====== 卡片状态徽章 ====== */
  function mobBadge(status) {
    var cls;
    if (status === 'running') cls = 'running';
    else if (status === 'success') cls = 'completed';
    else if (status === 'paused') cls = 'paused';
    else if (status === 'failure') cls = 'failure';
    else if (status === 'cancelled') cls = 'cancelled';
    else cls = 'pending';
    return '<span class="mob-card__badge ' + cls + '">' + esc(t('status.' + status)) + '</span>';
  }

  /* ====== 渲染转存任务卡片列表 ====== */
  function renderMobTasks() {
    var tasks = state.tasks || [];
    var container = $('#mob-tasks-list');
    if (!tasks.length) {
      container.innerHTML = '<div class="mob-empty" data-i18n="tasks.empty">' + t('tasks.empty') + '</div>';
      return;
    }
    container.innerHTML = tasks.map(function(task) {
      var total = Number(task.total_items || 0);
      var done = Number(task.completed_items || 0);
      var failed = Number(task.failed_items || 0);
      var percent = total > 0 ? Math.round(((done + failed) / total) * 100) : 0;
      var actions = '';
      if (task.status === 'running') actions += '<button class="secondary small" data-pause="' + task.id + '">' + t('tasks.pause') + '</button>';
      if (task.status === 'paused') actions += '<button class="secondary small" data-resume="' + task.id + '">' + t('tasks.resume') + '</button>';
      if (task.failed_items > 0) actions += '<button class="secondary small" data-retry="' + task.id + '">' + t('tasks.retryFailed') + '</button>';
      actions += '<button class="danger small" data-delete="' + task.id + '">' + t('tasks.delete') + '</button>';
      return '<div class="mob-card status-' + task.status + '">'
        + '<div class="mob-card__head">'
        + '<span class="mob-card__title">' + esc(task.source_link) + '</span>'
        + mobBadge(task.status)
        + '</div>'
        + '<div class="mob-card__row"><span class="label">' + t('tasks.target') + '</span><span>' + esc(task.target_link) + '</span></div>'
        + '<div class="mob-card__row"><span class="label">' + t('tasks.progress') + '</span><span>' + done + '/' + total + (failed ? ' (' + failed + ' ' + t('side.failed') + ')' : '') + '</span></div>'
        + '<div class="mob-card__progress"><div class="mob-card__progress-fill" style="width:' + percent + '%"></div></div>'
        + '<div class="mob-card__actions">' + actions + '</div>'
        + '</div>';
    }).join('');

    container.querySelectorAll('[data-pause]').forEach(function(btn) {
      btn.addEventListener('click', function(e) { runTaskAction(e, Number(btn.dataset.pause), 'pause'); });
    });
    container.querySelectorAll('[data-resume]').forEach(function(btn) {
      btn.addEventListener('click', function(e) { runTaskAction(e, Number(btn.dataset.resume), 'resume'); });
    });
    container.querySelectorAll('[data-retry]').forEach(function(btn) {
      btn.addEventListener('click', function(e) { runTaskAction(e, Number(btn.dataset.retry), 'retry-failed'); });
    });
    container.querySelectorAll('[data-delete]').forEach(function(btn) {
      btn.addEventListener('click', function(e) { deleteTask(e, Number(btn.dataset.delete)); });
    });

    // 点击卡片打开详情
    container.querySelectorAll('.mob-card').forEach(function(card, idx) {
      card.addEventListener('click', function(e) {
        if (e.target.closest('button')) return;
        openTaskDetail(tasks[idx].id);
      });
    });
  }

  /* ====== 渲染监听卡片列表 ====== */
  function renderMobWatches() {
    var watches = state.watches || [];
    var container = $('#mob-watches-list');
    if (!watches.length) {
      container.innerHTML = '<div class="mob-empty" data-i18n="watches.empty">' + t('watches.empty') + '</div>';
      return;
    }
    container.innerHTML = watches.map(function(w) {
      var typeLabel = w.type === 'download' ? t('watches.download') : t('watches.forward');
      var sourceHtml = '';
      if (w.source_links) {
        sourceHtml = '<div class="mob-card__row"><span class="label">' + t('watches.sources') + '</span><span>' + esc((w.source_links || []).join(', ')) + '</span></div>';
      } else if (w.source_link) {
        sourceHtml = '<div class="mob-card__row"><span class="label">' + t('watches.source') + '</span><span>' + esc(w.source_link) + '</span></div>';
      }
      var targetHtml = '';
      if (w.target_link) {
        targetHtml = '<div class="mob-card__row"><span class="label">' + t('watches.target') + '</span><span>' + esc(w.target_link) + '</span></div>';
      }
      var watchId = w.encoded_id || w.id;
      var sanitized = (watchId || '').replace(/:/g, '_');
      var eventsBtn = '';
      var eventsPanel = '';
      if (w.type === 'forward') {
        var ec = w.event_count || 0;
        eventsBtn = '<button class="small" data-watch-events="' + watchId + '">' + t('watches.events') + (ec ? ' (' + ec + ')' : '') + '</button>';
        eventsPanel = '<div class="mob-watch-events" id="mob-watch-events-' + sanitized + '" style="display:none;"></div>';
      }
      return '<div class="mob-card status-' + (w.status || 'running') + '">'
        + '<div class="mob-card__head">'
        + '<span class="mob-card__title">' + typeLabel + '</span>'
        + '<span class="mob-card__badge running">' + esc(w.type) + '</span>'
        + '</div>'
        + sourceHtml + targetHtml
        + '<div class="mob-card__actions">'
        + '<button class="danger small" data-delete-watch="' + watchId + '">' + t('watches.delete') + '</button>'
        + eventsBtn
        + '</div>'
        + eventsPanel
        + '</div>';
    }).join('');

    container.querySelectorAll('[data-delete-watch]').forEach(function(btn) {
      btn.addEventListener('click', function() { deleteWatch(btn.dataset.deleteWatch); });
    });

    container.querySelectorAll('[data-watch-events]').forEach(function(btn) {
      btn.addEventListener('click', function() {
        var watchId = btn.dataset.watchEvents;
        var sanitized = watchId.replace(/:/g, '_');
        var panel = document.getElementById('mob-watch-events-' + sanitized);
        if (!panel) return;
        if (panel.style.display === 'none' || panel.style.display === '') {
          panel.style.display = 'block';
          loadMobileWatchEvents(watchId, sanitized);
        } else {
          panel.style.display = 'none';
        }
      });
    });
  }

  async function loadMobileWatchEvents(watchId, sanitized) {
    var panel = document.getElementById('mob-watch-events-' + sanitized);
    if (!panel) return;
    panel.innerHTML = '<div class="watch-event-item">' + esc(t('watches.eventLoading')) + '</div>';
    try {
      var res = await fetch('/api/watches/' + encodeURIComponent(watchId) + '/events?limit=50&offset=0');
      var data = await res.json();
      if (!res.ok) { panel.innerHTML = '<div class="watch-event-item">' + esc(data.error || 'Load failed') + '</div>'; return; }
      var items = data.events || [];
      if (!items.length) {
        panel.innerHTML = '<div class="watch-event-item">' + esc(t('watches.noEvents')) + '</div>';
        return;
      }
      panel.innerHTML = '';
      items.forEach(function(evt) {
        var time = new Date(evt.created_at + 'Z').toLocaleString();
        var statusClass = evt.status === 'success' ? 'success' : 'warning';
        var statusLabel = evt.status === 'success' ? t('watches.eventForwarded') : t('watches.eventSkipped');
        var div = document.createElement('div');
        div.className = 'watch-event-item';
        div.innerHTML = '<span class="watch-event-time">' + esc(time) + '</span>'
          + '<span class="watch-event-badge"><span class="badge ' + statusClass + '">' + esc(statusLabel) + '</span></span>'
          + '<span class="watch-event-info">' + esc(evt.message) + ' #' + esc(String(evt.source_message_id || '')) + '</span>';
        panel.appendChild(div);
      });
    } catch (e) {
      panel.innerHTML = '<div class="watch-event-item">' + esc(t('form.requestFailed')) + '</div>';
    }
  }

  /* ====== 任务详情 Sheet ====== */
  var sheetTaskId = null;
  var sheetItems = [];
  var sheetEvents = [];
  var sheetItemTotal = 0;
  var sheetEventTotal = 0;
  var sheetItemOffset = 0;
  var sheetEventOffset = 0;
  var sheetHasMoreItems = false;
  var sheetHasMoreEvents = false;
  var sheetActiveTab = 'running';
  var sheetItemPage = 1;
  var sheetItemPageSize = 10;

  async function openTaskDetail(taskId) {
    sheetTaskId = taskId;
    state.selectedTaskId = taskId;
    sheetItems = [];
    sheetEvents = [];
    sheetActiveTab = 'running';
    sheetItemPage = 1;
    sheetItemOffset = 0;
    sheetEventOffset = 0;
    try {
      var res = await fetch('/api/tasks/' + taskId + '?items_limit=200&items_offset=0&events_limit=100&events_offset=0');
      if (!res.ok) { showToast(translateApiError(await res.json())); return; }
      var data = await res.json();
      sheetItems = data.items || [];
      sheetEvents = data.events || [];
      sheetItemTotal = data.item_count || 0;
      sheetEventTotal = data.event_count || 0;
      sheetItemOffset = data.items_offset || 0;
      sheetEventOffset = data.events_offset || 0;
      sheetHasMoreItems = data.has_more_items || false;
      sheetHasMoreEvents = data.has_more_events || false;
    } catch (e) { showToast(t('form.requestFailed')); return; }

    var task = state.tasks.find(function(t) { return t.id === taskId; });
    var total = Number((task && task.total_items) || 0);
    var done = Number((task && task.completed_items) || 0);
    var failed = Number((task && task.failed_items) || 0);
    var percent = total > 0 ? Math.round(((done + failed) / total) * 100) : 0;

    var groups = categorizeSheetItems();
    var html = '<h3 class="mob-sheet__title">#' + taskId + ' ' + esc((task && task.source_link) || '') + '</h3>'
      + '<div class="mob-sheet__task-header">'
      + '<div class="task-title">' + esc((task && task.source_link) || '') + '</div>'
      + '<div class="task-meta">' + (task ? (mobBadge(task.status) + ' ' + esc(task.target_link || '')) : '') + '</div>'
      + '<div class="mob-card__row"><span class="label">' + t('tasks.progress') + '</span><span>' + done + '/' + total + (failed ? ' (' + failed + ' ' + t('side.failed') + ')' : '') + '</span></div>'
      + '<div class="mob-card__progress"><div class="mob-card__progress-fill" style="width:' + percent + '%"></div></div>'
      + '</div>'
      + '<div class="mob-sheet-tabs" id="mob-sheet-item-tabs">'
      + renderSheetTab('running', groups.running.length)
      + renderSheetTab('success', groups.success.length)
      + renderSheetTab('skipped', groups.skipped.length)
      + renderSheetTab('failure', groups.failure.length)
      + '</div>'
      + '<div id="mob-sheet-items"></div>'
      + '<div id="mob-sheet-items-pagination"></div>'
      + '<div class="mob-section-title" style="margin-top:6px;">' + t('events.title') + ' (' + String(sheetEvents.length) + (sheetEventTotal > sheetEvents.length ? ' / ' + sheetEventTotal : '') + ')</div>'
      + '<div id="mob-sheet-events"></div>';

    var sheet = $('#mob-sheet');
    sheet.innerHTML = html;
    $('#mob-sheet-overlay').classList.add('open');

    bindSheetTabClicks();
    renderSheetItemPage();
    renderSheetEvents();

    // Sheet overlay 点击关闭
    $('#mob-sheet-overlay').onclick = function(e) {
      if (e.target === this) closeSheet();
    };
  }

  function closeSheet() {
    $('#mob-sheet-overlay').classList.remove('open');
    sheetTaskId = null;
  }

  function renderSheetTab(status, count) {
    var labelKey = 'items.tab.' + status;
    var active = sheetActiveTab === status ? ' active' : '';
    return '<button class="mob-sheet-tab' + active + '" data-sheet-tab="' + status + '">' + t(labelKey) + '<span class="count">' + count + '</span></button>';
  }

  function bindSheetTabClicks() {
    var tabs = document.querySelectorAll('#mob-sheet-item-tabs .mob-sheet-tab');
    tabs.forEach(function(tab) {
      tab.addEventListener('click', function() {
        sheetActiveTab = this.dataset.sheetTab;
        sheetItemPage = 1;
        var allTabs = document.querySelectorAll('#mob-sheet-item-tabs .mob-sheet-tab');
        allTabs.forEach(function(t) { t.classList.remove('active'); });
        this.classList.add('active');
        renderSheetItemPage();
      });
    });
  }

  function categorizeSheetItems() {
    var groups = { running: [], success: [], skipped: [], failure: [] };
    (sheetItems || []).forEach(function(item) {
      var status = String((item && item.status) || 'pending');
      if (status === 'success' || status === 'skipped' || status === 'failure') {
        groups[status].push(item);
      } else {
        groups.running.push(item);
      }
    });
    return groups;
  }

  function renderSheetItemPage() {
    var groups = categorizeSheetItems();
    var activeItems = groups[sheetActiveTab] || [];
    var total = activeItems.length;
    var pages = Math.max(1, Math.ceil(total / sheetItemPageSize));
    if (sheetItemPage > pages) sheetItemPage = pages;
    var start = (sheetItemPage - 1) * sheetItemPageSize;
    var end = Math.min(start + sheetItemPageSize, total);
    var pageItems = activeItems.slice(start, end);

    var container = $('#mob-sheet-items');
    if (!pageItems.length) {
      container.innerHTML = '<div class="mob-empty">' + t('items.empty.' + sheetActiveTab) + '</div>';
    } else {
      container.innerHTML = pageItems.map(function(item) {
        var dlPct = pct(item.download_current, item.download_total);
        var ulPct = pct(item.upload_current, item.upload_total);
        return '<div class="mob-item-row">'
          + '<div class="mob-item-row__name">' + esc(item.file_name || item.local_path || '#' + (item.source_message_id || item.id)) + '</div>'
          + '<div style="text-align:right;font-size:var(--font-xs);color:var(--muted);flex-shrink:0;">'
          + '<div>' + t('items.download') + ' ' + dlPct + '%</div>'
          + '<div>' + t('items.upload') + ' ' + ulPct + '%</div>'
          + '</div>'
          + '</div>';
      }).join('');
    }

    var pagEl = $('#mob-sheet-items-pagination');
    var pagHtml = '';
    if (pages > 1) {
      pagHtml += '<div class="mob-sheet-pagination">'
        + '<button class="secondary small" ' + (sheetItemPage <= 1 ? 'disabled' : '') + ' onclick="sheetPrevPage()">' + t('items.page.previous') + '</button>'
        + '<span>' + interpolate(t('items.page.range'), { start: start + 1, end: end, total: total }) + '</span>'
        + '<button class="secondary small" ' + (sheetItemPage >= pages ? 'disabled' : '') + ' onclick="sheetNextPage()">' + t('items.page.next') + '</button>'
        + '</div>';
    }
    if (sheetHasMoreItems && sheetItems.length < sheetItemTotal) {
      pagHtml += '<div class="mob-load-more"><button class="secondary small" onclick="loadMoreSheetItems()">' + t('items.loadMore') + ' (' + (sheetItemTotal - sheetItems.length) + ' ' + t('items.remaining') + ')</button></div>';
    }
    pagEl.innerHTML = pagHtml;
  }

  function renderSheetEvents() {
    var container = $('#mob-sheet-events');
    if (!sheetEvents.length) {
      container.innerHTML = '<div class="mob-empty">' + t('events.empty') + '</div>';
      return;
    }
    var html = sheetEvents.map(function(event) {
      return '<div class="mob-event-row">'
        + '<time>' + esc(event.created_at) + '</time>'
        + '<span style="color:var(--accent);">[' + esc(localizeEventLevel(event.level)) + ']</span> '
        + esc(localizeEventMessage(event))
        + '</div>';
    }).join('');
    if (sheetHasMoreEvents && sheetEvents.length < sheetEventTotal) {
      html += '<div class="mob-load-more"><button class="secondary small" onclick="loadMoreSheetEvents()">' + t('events.loadMore') + ' (' + (sheetEventTotal - sheetEvents.length) + ' ' + t('events.remaining') + ')</button></div>';
    }
    container.innerHTML = html;
  }

  function sheetPrevPage() {
    if (sheetItemPage > 1) { sheetItemPage--; renderSheetItemPage(); }
  }
  function sheetNextPage() {
    sheetItemPage++;
    renderSheetItemPage();
  }
  window.sheetPrevPage = sheetPrevPage;
  window.sheetNextPage = sheetNextPage;

  async function loadMoreSheetItems() {
    if (!sheetTaskId) return;
    var offset = sheetItemOffset + 200;
    try {
      var res = await fetch('/api/tasks/' + sheetTaskId + '?items_limit=200&items_offset=' + offset + '&events_limit=0&events_offset=0');
      if (!res.ok) return;
      var data = await res.json();
      sheetItems = sheetItems.concat(data.items || []);
      sheetItemTotal = data.item_count || sheetItemTotal;
      sheetItemOffset = offset;
      sheetHasMoreItems = data.has_more_items || false;
      renderSheetItemPage();
    } catch (e) { /* ignore */ }
  }
  window.loadMoreSheetItems = loadMoreSheetItems;

  async function loadMoreSheetEvents() {
    if (!sheetTaskId) return;
    var offset = sheetEventOffset + 100;
    try {
      var res = await fetch('/api/tasks/' + sheetTaskId + '?items_limit=0&items_offset=0&events_limit=100&events_offset=' + offset);
      if (!res.ok) return;
      var data = await res.json();
      sheetEvents = sheetEvents.concat(data.events || []);
      sheetEventTotal = data.event_count || sheetEventTotal;
      sheetEventOffset = offset;
      sheetHasMoreEvents = data.has_more_events || false;
      renderSheetEvents();
    } catch (e) { /* ignore */ }
  }
  window.loadMoreSheetEvents = loadMoreSheetEvents;

  /* ====== 渲染设置表单 ====== */
  function renderMobSettingsForm() {
    if (!state.settings || !state.schema) return;
    var s = state.settings;
    var schema = state.schema;
    var user = s.user || {};
    var glob = s.global || {};
    var tp = (glob.target_profiles || {});
    var pikpak = tp.pikpak || {};
    var archive = pikpak.archive || {};
    var upload = glob.upload || {};
    var sensitiveKeys = schema.sensitive_keys || [];
    var downloadTypes = schema.download_type || [];
    var forwardTypes = schema.forward_type || [];
    var selectedDownload = user.download_type || [];
    var exportTable = glob.export_table || {};

    // Path & Task
    var maxTasks = user.max_tasks || {};
    var maxRetries = user.max_retries || {};
    $('#mob-settings-path-fields').innerHTML =
      '<label><span>' + t('settings.saveDirectory') + '</span><input type="text" name="user.save_directory" value="' + esc(user.save_directory || '') + '"></label>'
      + '<label><span>' + t('settings.tempDirectory') + '</span><input type="text" name="user.temp_directory" value="' + esc(user.temp_directory || '') + '"></label>'
      + '<label><span>' + t('settings.sessionDirectory') + '</span><input type="text" name="user.session_directory" value="' + esc(user.session_directory || '') + '"></label>'
      + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">'
      + '<label><span>' + t('settings.maxDownload') + '</span><input type="number" name="user.max_tasks.download" value="' + esc(maxTasks.download || '') + '" min="1"></label>'
      + '<label><span>' + t('settings.maxUpload') + '</span><input type="number" name="user.max_tasks.upload" value="' + esc(maxTasks.upload || '') + '" min="1"></label>'
      + '</div>'
      + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">'
      + '<label><span>' + t('settings.retryDownload') + '</span><input type="number" name="user.max_retries.download" value="' + esc(maxRetries.download || '') + '" min="0"></label>'
      + '<label><span>' + t('settings.retryUpload') + '</span><input type="number" name="user.max_retries.upload" value="' + esc(maxRetries.upload || '') + '" min="0"></label>'
      + '</div>'
      + '<label><span>' + t('settings.pikpakMaxFileSize') + '</span><input type="number" name="global.target_profiles.pikpak.max_file_size" value="' + esc(pikpak.max_file_size || '') + '" min="1"></label>';

    // Behavior
    $('#mob-settings-behavior-fields').innerHTML =
      '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.notice" style="width:auto;min-height:auto;"' + (glob.notice ? ' checked' : '') + '><span>' + t('settings.notice') + '</span></label>'
      + '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="user.is_shutdown" style="width:auto;min-height:auto;"' + (user.is_shutdown ? ' checked' : '') + '><span>' + t('settings.shutdown') + '</span></label>'
      + '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.upload.download_upload" style="width:auto;min-height:auto;"' + (upload.download_upload ? ' checked' : '') + '><span>' + t('settings.downloadUpload') + '</span></label>'
      + '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.upload.delete" style="width:auto;min-height:auto;"' + (upload.delete ? ' checked' : '') + '><span>' + t('settings.uploadDelete') + '</span></label>'
      + '<label><span>' + t('settings.pendingLimit') + '</span><input type="number" name="global.upload.pending_limit" value="' + esc(upload.pending_limit || '') + '" min="1" max="5"></label>';

    // PikPak Archive
    $('#mob-settings-archive-fields').innerHTML =
      '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.target_profiles.pikpak.archive.enable" style="width:auto;min-height:auto;"' + (archive.enable ? ' checked' : '') + '><span>' + t('settings.pikpakArchiveEnable') + '</span></label>'
      + '<label><span>' + t('settings.pikpakArchiveRemote') + '</span><input type="text" name="global.target_profiles.pikpak.archive.remote" value="' + esc(archive.remote || '') + '"></label>'
      + '<label><span>' + t('settings.pikpakArchiveSource') + '</span><input type="text" name="global.target_profiles.pikpak.archive.source_directory" value="' + esc(archive.source_directory || '') + '"></label>'
      + '<label><span>' + t('settings.pikpakArchiveRoot') + '</span><input type="text" name="global.target_profiles.pikpak.archive.root_directory" value="' + esc(archive.root_directory || '') + '"></label>'
      + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">'
      + '<label><span>' + t('settings.pikpakArchivePoll') + '</span><input type="number" name="global.target_profiles.pikpak.archive.poll_seconds" value="' + esc(archive.poll_seconds || '') + '" min="0"></label>'
      + '<label><span>' + t('settings.pikpakArchiveInterval') + '</span><input type="number" name="global.target_profiles.pikpak.archive.poll_interval_seconds" value="' + esc(archive.poll_interval_seconds || '') + '" min="0"></label>'
      + '</div>'
      + '<label><span>' + t('settings.pikpakArchiveWindow') + '</span><input type="number" name="global.target_profiles.pikpak.archive.match_window_seconds" value="' + esc(archive.match_window_seconds || '') + '" min="0"></label>';

    // Account & Proxy
    $('#mob-settings-sensitive-fields').innerHTML =
      '<label><span>API ID</span><input type="text" name="user.api_id" value="' + esc(user.api_id || '') + '"></label>'
      + sensitiveKeys.map(function(k) {
        var v = getPath(user, getSettingLeafKey(k));
        return '<label><span>' + esc(k) + '</span><input type="password" name="user.' + esc(k) + '" placeholder="' + (v && v.configured ? t('settings.secretConfigured') : t('settings.secretNotConfigured')) + '" autocomplete="new-password"></label>';
      }).join('');

    // Download Types
    $('#mob-settings-download-types-fields').innerHTML = renderCheckCards('user.download_type', downloadTypes, selectedDownload);

    // Forward Types
    $('#mob-settings-forward-types-fields').innerHTML = renderCheckCards('global.forward_type', forwardTypes, selectedForward(glob));

    // Message Filter
    var mf = glob.message_filter || {};
    var mfMediaTypes = (state.schema.message_filter && state.schema.message_filter.media_types) || forwardTypes;
    var mfDateRange = mf.date_range || {};
    var mfKeywords = mf.keywords || {};
    var mfDateStart = mfDateRange.start_date ? new Date(mfDateRange.start_date * 1000).toISOString().slice(0, 16) : '';
    var mfDateEnd = mfDateRange.end_date ? new Date(mfDateRange.end_date * 1000).toISOString().slice(0, 16) : '';
    var mfKwStr = Array.isArray(mfKeywords.words) ? mfKeywords.words.join(', ') : '';
    $('#mob-settings-message-filter-fields').innerHTML =
      '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.message_filter.enabled" style="width:auto;min-height:auto;"' + (mf.enabled !== false ? ' checked' : '') + '><span>' + t('settings.enabled') + '</span></label>'
      + '<div class="mob-subsection"><h4>' + t('settings.mediaTypes') + '</h4>'
      + renderCheckCards('global.message_filter.media_types', mfMediaTypes, selectedMediaTypes(glob))
      + '</div>'
      + '<div class="mob-subsection"><h4>' + t('settings.dateRange') + '</h4>'
      + '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.message_filter.date_range.enabled" style="width:auto;min-height:auto;"' + (mfDateRange.enabled ? ' checked' : '') + '><span>' + t('settings.enabled') + '</span></label>'
      + '<div class="field-grid field-grid--two" style="margin-top:8px">'
      + '<label class="field"><span>' + t('settings.startDate') + '</span><input name="global.message_filter.date_range.start_date" type="datetime-local" value="' + escAttr(mfDateStart) + '"></label>'
      + '<label class="field"><span>' + t('settings.endDate') + '</span><input name="global.message_filter.date_range.end_date" type="datetime-local" value="' + escAttr(mfDateEnd) + '"></label>'
      + '</div></div>'
      + '<div class="mob-subsection"><h4>' + t('settings.keywords') + '</h4>'
      + '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.message_filter.keywords.enabled" style="width:auto;min-height:auto;"' + (mfKeywords.enabled ? ' checked' : '') + '><span>' + t('settings.enabled') + '</span></label>'
      + '<label class="field" style="margin-top:8px"><span>' + t('settings.keywordList') + '</span><input name="global.message_filter.keywords.words" value="' + escAttr(mfKwStr) + '" placeholder="' + t('settings.keywordPlaceholder') + '"></label>'
      + '</div>';

    // Export Tables
    $('#mob-settings-exports-fields').innerHTML =
      '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.export_table.link" style="width:auto;min-height:auto;"' + (exportTable.link ? ' checked' : '') + '><span>' + t('settings.exportLink') + '</span></label>'
      + '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.export_table.count" style="width:auto;min-height:auto;"' + (exportTable.count ? ' checked' : '') + '><span>' + t('settings.exportCount') + '</span></label>'
      + '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.export_table.upload" style="width:auto;min-height:auto;"' + (exportTable.upload ? ' checked' : '') + '><span>' + t('settings.exportUpload') + '</span></label>';
  }

  function getSettingLeafKey(key) {
    return key;
  }

  function selectedForward(glob) {
    var ft = glob.forward_type || {};
    var result = [];
    for (var k in ft) { if (ft[k]) result.push(k); }
    return result;
  }

  function selectedMediaTypes(glob) {
    var mf = glob.message_filter || {};
    var mt = mf.media_types || glob.forward_type || {};
    var result = [];
    for (var k in mt) { if (mt[k]) result.push(k); }
    return result;
  }

  function escAttr(value) {
    return String(value || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function renderCheckCards(baseName, types, selected) {
    return types.map(function(type) {
      return '<label style="flex-direction:row;align-items:center;gap:8px;padding:6px 0;"><input type="checkbox" name="' + baseName + '" value="' + esc(type) + '" style="width:auto;min-height:auto;"' + (selected.indexOf(type) >= 0 ? ' checked' : '') + '><span>' + esc(type) + '</span></label>';
    }).join('');
  }

  /* ====== 覆盖：renderTasks / loadTasks / loadWatches / loadSettings ====== */
  var _origRenderTasks = renderTasks;
  renderTasks = function() {
    try { _origRenderTasks(); } catch(e) {}
    if (state.tasks) renderMobTasks();
  };
  var _origLoadTasks = loadTasks;
  loadTasks = async function() {
    try { await _origLoadTasks(); } catch(e) {}
    if (state.tasks) renderMobTasks();
  };

  var _origLoadWatches = loadWatches;
  loadWatches = async function() {
    try { await _origLoadWatches(); } catch(e) {}
    if (state.watches) renderMobWatches();
  };
  var _origRenderWatches = renderWatches;
  renderWatches = function() {
    try { _origRenderWatches(); } catch(e) {}
    if (state.watches) renderMobWatches();
  };

  var _origLoadSettings = loadSettings;
  loadSettings = async function() {
    try { await _origLoadSettings(); } catch(e) {}
    renderMobSettingsForm();
  };

  /* ====== 事件绑定 ====== */
  $('#language-select').addEventListener('change', function(event) {
    state.lang = event.target.value;
    localStorage.setItem('trmd-lang', state.lang);
    applyLanguageAndRefresh();
    renderMobTasks();
    renderMobWatches();
    renderMobRecords();
    renderMobStatistics();
    renderMobSettingsForm();
  });

  $('#refresh').addEventListener('click', function() {
    loadTasks();
    var activeView = document.querySelector('.mob-view.active');
    if (activeView) {
      var viewId = activeView.id.replace('mob-view-', '');
      if (viewId === 'settings') loadSettings();
      if (viewId === 'watches') loadWatches();
    }
    showToast(t('action.refresh') + ' OK');
  });

  /* Tab 栏点击 */
  $$('.mob-tab').forEach(function(tab) {
    tab.addEventListener('click', function() { mobSwitchView(tab.dataset.mobNav); });
  });

  /* "更多"按钮 -> 打开 Drawer */
  var moreTab = document.querySelector('.mob-tab[data-mob-nav="more"]');
  if (moreTab) moreTab.addEventListener('click', openDrawer);

  /* Drawer 内菜单项点击 */
  $$('[data-mob-drawer-nav]').forEach(function(item) {
    item.addEventListener('click', function() { mobSwitchView(item.dataset.mobDrawerNav); });
  });

  /* Drawer overlay 点击关闭 */
  $('#mob-drawer-overlay').addEventListener('click', function(e) {
    if (e.target === this) closeDrawer();
  });

  /* FAB 点击 */
  $('#mob-fab').addEventListener('click', toggleFabMenu);

  /* FAB 菜单项 */
  $('#mob-fab-new-transfer').addEventListener('click', function() {
    closeFabMenu();
    var collapse = $('#collapse-transfer-form');
    collapse.classList.add('open');
    collapse.scrollIntoView({ behavior: 'smooth' });
  });
  $('#mob-fab-new-watch').addEventListener('click', function() {
    closeFabMenu();
    mobSwitchView('watches');
    var collapse = $('#collapse-watch-form');
    collapse.classList.add('open');
    collapse.scrollIntoView({ behavior: 'smooth' });
  });

  /* 折叠面板切换 */
  $$('.mob-collapse__head').forEach(function(head) {
    head.addEventListener('click', function() { toggleCollapse(head); });
  });

  /* 点击外部关闭 FAB 菜单 */
  document.addEventListener('click', function(e) {
    if (!e.target.closest('#mob-fab') && !e.target.closest('#mob-fab-menu')) {
      closeFabMenu();
    }
  });

  /* 监听类型切换 */
  var watchTypeSelect = $('#mob-watch-type');
  if (watchTypeSelect) {
    watchTypeSelect.addEventListener('change', function() {
      var isForward = this.value === 'forward';
      var textarea = document.querySelector('#mob-watch-source-group textarea[name="source_links"]');
      var input = document.querySelector('#mob-watch-source-group input[name="source_link"]');
      var sourceLabel = $('#mob-watch-source-label').querySelector('span');
      if (isForward) {
        if (textarea) { textarea.style.display = 'none'; textarea.required = false; }
        if (input) { input.style.display = ''; input.required = true; }
        if (sourceLabel) sourceLabel.textContent = t('watches.source');
      } else {
        if (textarea) { textarea.style.display = ''; textarea.required = true; }
        if (input) { input.style.display = 'none'; input.required = false; }
        if (sourceLabel) sourceLabel.textContent = t('watches.sources');
      }
      $('#mob-watch-target-group').style.display = isForward ? '' : 'none';
      $('#mob-watch-comment-group').style.display = isForward ? '' : 'none';
    });
  }

  /* 新建转存表单提交 */
  var transferForm = $('#mob-transfer-form');
  if (transferForm) {
    transferForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      var form = new FormData(this);
      var payload = Object.fromEntries(form.entries());
      payload.start_id = payload.start_id ? Number(payload.start_id) : null;
      payload.end_id = payload.end_id ? Number(payload.end_id) : null;
      payload.include_comment = !!payload.include_comment;
      try {
        await postJson('/api/tasks', payload);
        showToast(t('form.transferCreated'));
        this.reset();
        $('#collapse-transfer-form').classList.remove('open');
        loadTasks();
      } catch (err) {
        showToast(translateApiError(err, 'form.requestFailed'));
      }
    });
  }

  /* 新建监听表单提交 */
  var watchForm = $('#mob-watch-form');
  if (watchForm) {
    watchForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      var form = new FormData(this);
      var payload = Object.fromEntries(form.entries());
      var isForward = payload.type === 'forward';
      if (isForward) {
        delete payload.source_links;
        payload.include_comment = !!payload.include_comment;
      } else {
        delete payload.source_link;
        delete payload.target_link;
        delete payload.include_comment;
        payload.source_links = String(payload.source_links || '').split('\n').map(function(s) { return s.trim(); }).filter(Boolean);
      }
      try {
        await postJson('/api/watches', payload);
        showToast(t('watches.created'));
        this.reset();
        $('#collapse-watch-form').classList.remove('open');
        loadWatches();
      } catch (err) {
        showToast(translateApiError(err, 'form.requestFailed'));
      }
    });
  }

  /* 保存设置 */
  var saveBtn = $('#mob-save-settings');
  if (saveBtn) {
    saveBtn.addEventListener('click', async function() {
      var userPayload = {};
      var globalPayload = {};
      var downloadTypes = [];

      // 收集所有设置区域的 input
      var allInputs = document.querySelectorAll('#mob-settings-path-fields input, #mob-settings-behavior-fields input, #mob-settings-sensitive-fields input, #mob-settings-archive-fields input, #mob-settings-download-types-fields input, #mob-settings-forward-types-fields input, #mob-settings-message-filter-fields input, #mob-settings-exports-fields input');

      allInputs.forEach(function(input) {
        var name = input.name || '';
        if (!name) return;
        var value;
        if (input.type === 'checkbox') {
          value = input.checked;
        } else if (input.type === 'number') {
          value = input.value === '' ? null : Number(input.value);
        } else if (input.type === 'password' && input.value === '') {
          return;
        } else {
          value = input.value;
        }

        // 收集 download_type 多选
        if (name === 'user.download_type' && input.type === 'checkbox' && input.checked) {
          downloadTypes.push(input.value);
          return;
        }
        // 收集 forward_type 多选
        if (name === 'global.forward_type' && input.type === 'checkbox') {
          setPath(globalPayload, 'forward_type.' + input.value, input.checked);
          return;
        }
        // 消息过滤 — 日期范围：datetime-local → timestamp
        if (name === 'global.message_filter.date_range.start_date' || name === 'global.message_filter.date_range.end_date') {
          var ts = input.value ? (new Date(input.value).getTime() / 1000) : null;
          setPath(globalPayload, name.substring(7), ts);
          return;
        }
        // 消息过滤 — 关键词：逗号分隔字符串 → 数组
        if (name === 'global.message_filter.keywords.words') {
          var words = input.value ? input.value.split(',').map(function(s) { return s.trim(); }).filter(Boolean) : [];
          setPath(globalPayload, name.substring(7), words);
          return;
        }

        if (name.startsWith('user.')) {
          setPath(userPayload, name.substring(5), value);
        } else if (name.startsWith('global.')) {
          setPath(globalPayload, name.substring(7), value);
        }
      });

      setPath(userPayload, 'download_type', downloadTypes);

      try {
        await postJson('/api/settings', { user: userPayload, global: globalPayload });
        showToast(t('settings.saved'));
        loadSettings();
      } catch (err) {
        showToast(translateApiError(err, 'form.requestFailed'));
      }
    });
  }

  /* ====== Phase 2: 频道下载 ====== */
  function renderMobRecords() {
    var records = state.records || [];
    var container = $('#mob-records-list');
    if (!records.length) {
      container.innerHTML = '<div class="mob-empty" data-i18n="records.empty">' + t('records.empty') + '</div>';
      return;
    }
    container.innerHTML = records.map(function(r) {
      return '<div class="mob-card">'
        + '<div class="mob-card__head"><span class="mob-card__title">' + esc(r.file_name || r.local_path || '') + '</span></div>'
        + '<div class="mob-card__row"><span class="label">' + t('records.chat') + '</span><span>' + esc(r.source_chat_id || '-') + '</span></div>'
        + '<div class="mob-card__row"><span class="label">' + t('records.message') + '</span><span>' + esc(r.source_message_id || '-') + '</span></div>'
        + '<div class="mob-card__row"><span class="label">' + t('records.size') + '</span><span>' + formatBytes(r.file_size) + '</span></div>'
        + '<div class="mob-card__row"><span class="label">' + t('records.updated') + '</span><span>' + esc(r.updated_at || r.downloaded_at || '') + '</span></div>'
        + '</div>';
    }).join('');
  }

  /* ====== Phase 2: 统计表格 ====== */
  function renderMobStatistics() {
    var stats = state.statistics;
    var container = $('#mob-statistics-list');
    if (!stats || !stats.tables) {
      container.innerHTML = '<div class="mob-empty">' + t('tasks.empty') + '</div>';
      return;
    }
    var tables = stats.tables;
    var html = '';
    var tableNames = { link: t('statistics.link'), count: t('statistics.count'), upload: t('statistics.upload') };
    for (var key in tables) {
      if (!tables.hasOwnProperty(key)) continue;
      var tbl = tables[key];
      html += '<div class="mob-card" style="margin-bottom:10px;">'
        + '<div class="mob-card__row"><span class="label">' + (tableNames[key] || key) + '</span><span>' + t('statistics.available') + ': ' + (tbl.available ? t('statistics.yes') : t('statistics.no')) + '</span></div>'
        + '<div class="mob-card__row"><span class="label">' + t('statistics.rows') + '</span><span>' + (tbl.rows || 0) + '</span></div>'
        + '</div>';
    }
    container.innerHTML = html || '<div class="mob-empty">' + t('tasks.empty') + '</div>';
  }

  /* ====== 覆盖 loadRecords / renderRecords / loadStatistics ====== */
  var _origLoadRecords = loadRecords;
  loadRecords = async function() {
    try { await _origLoadRecords(); } catch(e) {}
    renderMobRecords();
  };
  var _origRenderRecords = renderRecords;
  renderRecords = function() {
    try { _origRenderRecords(); } catch(e) {}
    renderMobRecords();
  };
  var _origLoadStatistics = loadStatistics;
  loadStatistics = async function() {
    try { await _origLoadStatistics(); } catch(e) {}
    renderMobStatistics();
  };

  /* ====== Phase 2 事件绑定 ====== */

  /* 频道下载表单 */
  var channelForm = $('#mob-channel-form');
  if (channelForm) {
    channelForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      var form = new FormData(this);
      var payload = Object.fromEntries(form.entries());
      payload.include_comment = !!payload.include_comment;
      if (payload.start_date) {
        payload.date_range = { start_date: new Date(payload.start_date).getTime() / 1000 };
        delete payload.start_date;
      }
      if (payload.end_date) {
        payload.date_range = payload.date_range || {};
        payload.date_range.end_date = new Date(payload.end_date).getTime() / 1000;
        delete payload.end_date;
      }
      if (payload.keywords) {
        payload.keywords = String(payload.keywords).split(',').map(function(s) { return s.trim(); }).filter(Boolean);
      } else {
        payload.keywords = [];
      }
      payload.download_type = Array.from(document.querySelectorAll('#mob-channel-download-types input[name="download_type"]:checked')).map(function(el) { return el.value; });
      try {
        await postJson('/api/channel-downloads', payload);
        showToast(t('channel.accepted'));
        this.reset();
        $('#collapse-channel-form').classList.remove('open');
      } catch (err) {
        showToast(translateApiError(err, 'form.requestFailed'));
      }
    });
  }

  /* 本地上传表单 */
  var uploadForm = $('#mob-upload-form');
  if (uploadForm) {
    uploadForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      var form = new FormData(this);
      var payload = Object.fromEntries(form.entries());
      payload.recursive = !!payload.recursive;
      try {
        await postJson('/api/uploads', payload);
        showToast(t('uploads.accepted'));
        this.reset();
        $('#collapse-upload-form').classList.remove('open');
      } catch (err) {
        showToast(translateApiError(err, 'form.requestFailed'));
      }
    });
  }

  /* 统计导出 */
  /* 已通过 loadStatistics 覆盖自动渲染 */

  /* ====== 初始加载（由 checkAuthStatus 驱动） ====== */
"""
