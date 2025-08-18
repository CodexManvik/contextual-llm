from __future__ import annotations
import os
import json
import time
import hashlib
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Optional, Union
import win32api  # requires pywin32

EXCLUDE_KEYWORDS = {
    'uninstall','installer','setup','updater','update','crash','report','helper',
    'service','repair','maintenance','elevation','diagnostic','benchmark',
    'redistributable','vc_redist','vcredist','license','activation','activate','cleanup',
    'agent','watchdog','monitor','telemetry','feedback','plugin','add-in','daemon','tool','utility'
}

PROGRAM_FILES_DIRS = [
    os.environ.get('ProgramFiles', r"C:\Program Files"),
    os.environ.get('ProgramFiles(x86)', r"C:\Program Files (x86)"),
]

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE_DIR = os.path.join(PROJECT_ROOT, "data")
CACHE_FILE = os.path.join(CACHE_DIR, "app_inventory.json")

def _read_file_version_info(file_path: str) -> Dict[str, str]:
    info: Dict[str, str] = {}
    try:
        size = win32api.GetFileVersionInfoSize(file_path) # type: ignore
        if not size:
            return info
        ver_info = win32api.GetFileVersionInfo(file_path, "\\")
        translations = ver_info.get('VarFileInfo', {}).get('Translation', [])
        candidates: List[str] = []
        for t in translations:
            if isinstance(t, tuple) and len(t) == 2:
                lang, codepage = t
                candidates.append(f'StringFileInfo\\{lang:04x}{codepage:04x}\\')
        if not candidates:
            candidates = ['StringFileInfo\\040904b0\\']  # en-US fallback
        for base in candidates:
            for key in ['ProductName', 'FileDescription', 'CompanyName', 'ProductVersion']:
                if key not in info:
                    try:
                        # type: ignore[reportAttributeAccessIssue]
                        val = win32api.VerQueryValue(ver_info, base + key) # type: ignore
                        if isinstance(val, bytes):
                            val = val.decode(errors='ignore')
                        info[key] = val
                    except Exception:
                        pass
    except Exception:
        pass
    return info

def _is_excluded_name(name: str) -> bool:
    n = (name or "").lower()
    return any(kw in n for kw in EXCLUDE_KEYWORDS)

def _score_candidate(name: str, meta: Dict[str, str]) -> float:
    score = 0.0
    low = (name or "").lower()
    if not _is_excluded_name(name):
        score += 1.0
    if meta.get('FileDescription'):
        score += 1.0
    if meta.get('ProductName'):
        score += 1.0
    if any(s in low for s in ['helper','service','updater','install']):
        score -= 0.5
    if any(s in low for s in ['chrome','firefox','edge','code','word','excel','powerpnt','notepad++']):
        score += 0.5
    return score

def _scan_dir_for_exes(base_dir: str, max_files: int = 30000) -> List[Dict]:
    results: List[Dict] = []
    if not base_dir or not os.path.isdir(base_dir):
        return results
    count = 0
    for root, _dirs, files in os.walk(base_dir):
        if any(skip in root.lower() for skip in ['uninstall','installer','updates','update','setup']):
            continue
        for f in files:
            if count >= max_files:
                return results
            if not f.lower().endswith('.exe'):
                continue
            full = os.path.join(root, f)
            try:
                if os.path.getsize(full) < 50 * 1024:
                    continue
            except Exception:
                continue
            meta = _read_file_version_info(full)
            results.append({
                'name': f,
                'path': full,
                'dir': root,
                'meta': {
                    'ProductName': meta.get('ProductName',''),
                    'FileDescription': meta.get('FileDescription',''),
                    'CompanyName': meta.get('CompanyName',''),
                    'ProductVersion': meta.get('ProductVersion',''),
                }
            })
            count += 1
    return results

def _consolidate_apps(exe_list: List[Dict]) -> List[Dict]:
    by_folder: Dict[str, List[Dict]] = {}
    for item in exe_list:
        by_folder.setdefault(item['dir'], []).append(item)

    consolidated: List[Dict] = []
    for folder, items in by_folder.items():
        best, best_score = None, -1e9
        for it in items:
            s = _score_candidate(it['name'], it['meta'])
            if s > best_score:
                best, best_score = it, s
        if not best:
            continue
        friendly = (best['meta'].get('ProductName')
                    or best['meta'].get('FileDescription')
                    or Path(best['name']).stem)
        if _is_excluded_name(friendly):
            sorted_items = sorted(items, key=lambda x: _score_candidate(x['name'], x['meta']), reverse=True)
            for alt in sorted_items:
                friendly_alt = (alt['meta'].get('ProductName')
                                or alt['meta'].get('FileDescription')
                                or Path(alt['name']).stem)
                if not _is_excluded_name(friendly_alt):
                    best = alt
                    friendly = friendly_alt
                    break
        consolidated.append({
            'app_name': friendly.strip(),
            'main_exe': best['path'],
            'folder': folder,
            'vendor': best['meta'].get('CompanyName',''),
            'version': best['meta'].get('ProductVersion',''),
            'alternates': [x['path'] for x in items if x['path'] != best['path']],
        })

    seen = set()
    unique: List[Dict] = []
    for app in consolidated:
        key = (app['app_name'].lower(), app['folder'].lower())
        if key not in seen:
            unique.append(app)
            seen.add(key)
    
    # FIX: Handle None values safely before calling .lower()
    unique.sort(key=lambda x: (
        (x.get('app_name') or "").lower(),
        (x.get('vendor') or "").lower()
    ))
    return unique

def _hash_dirs_state(dirs: List[str]) -> str:
    h = hashlib.sha1()
    for d in dirs:
        try:
            stat = os.stat(d)
            h.update(str(stat.st_mtime).encode())
        except Exception:
            h.update(b'0')
    return h.hexdigest()

def discover_installed_apps(rescan: bool = False, save_cache: bool = True) -> List[Dict]:
    os.makedirs(CACHE_DIR, exist_ok=True)
    dir_hash = _hash_dirs_state(PROGRAM_FILES_DIRS)
    if not rescan and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            if cached.get('_dir_hash') == dir_hash:
                return cached.get('apps', [])
        except Exception:
            pass

    exe_entries: List[Dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        futures = [ex.submit(_scan_dir_for_exes, d) for d in PROGRAM_FILES_DIRS]
        for fut in concurrent.futures.as_completed(futures):
            try:
                exe_entries.extend(fut.result())
            except Exception:
                continue

    apps = _consolidate_apps(exe_entries)

    if save_cache:
        data = {'_generated_at': int(time.time()), '_dir_hash': dir_hash, 'apps': apps}
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    return apps

def resolve_app(query: str, apps: Optional[List[Dict]] = None) -> Optional[Dict]:
    if apps is None:
        apps = discover_installed_apps(rescan=False)
    q = (query or "").strip().lower()
    if not q:
        return None
    # exact name
    for app in apps:
        if app['app_name'].lower() == q:
            return app
    # contains in app_name or vendor
    candidates = []
    for app in apps:
        if q in app['app_name'].lower() or q in (app.get('vendor') or '').lower():
            candidates.append(app)
    if candidates:
        candidates.sort(key=lambda x: (len(x['app_name']), x.get('vendor','')))
        return candidates[0]
    # match by exe stem
    for app in apps:
        if q in Path(app['main_exe']).stem.lower():
            return app
    return None
