# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.12.14 (main, Aug 25 2026, 14:00:49) [Clang 22.1.3 ]
# Embedded file name: <mashkamarks>
import json, os, traceback
VERSION = '1.0.2'
RES_KEY = 'mashka.marks.view'
BATTLE_KEY = 'mashka.marks.battle'
LAYOUT_PATH = 'coui://gui/gameface/mods/mashka_marks/Panel.html'
BATTLE_LAYOUT_PATH = 'coui://gui/gameface/mods/mashka_marks/Battle.html'
RES_NODE = (
 'mods', 'mashka', 'marks', 'views', 'Panel')
BATTLE_NODE = ('mods', 'mashka', 'marks', 'views', 'Battle')
RES_MAP_PATH = './res_mods/%s/gui/unbound/res_map.json'
CONFIG_DIR = './mods/configs/mashka_marks/'
HISTORY_FILE = CONFIG_DIR + 'history.json'
CONFIG_FILE = CONFIG_DIR + 'config.json'
PENDING_FILE = CONFIG_DIR + 'pending.json'
EMA_K = 0.02
RECALC_MIN = 0.005
LIVE_MIN = 0.05
MIN_TIER = 5
YOUNG_BATTLES = 2
GOAL_PERCENT = 95.0
GOAL_BATTLES = 20
MARK_STEPS = (65.0, 85.0, 95.0, 100.0)
_state = {}

_subscriptions = []
_callbacks = {}
_hooks = []
_scopeEpochs = {}

def _listen(event, handler, scope='global'):
    if any(e is event and h is handler for e, h, s in _subscriptions):
        return
    event.__iadd__(handler)
    _subscriptions.append((event, handler, scope))

def _schedule(delay, call, scope='global'):
    import BigWorld
    if _state.get('stopped'):
        return None
    lifecycle = _state.get('lifecycle', 0)
    epoch = _scopeEpochs.get(scope, 0)
    holder = []
    def invoke():
        if holder:
            _callbacks.pop(holder[0], None)
        if (not _state.get('stopped') and lifecycle == _state.get('lifecycle', 0)
                and epoch == _scopeEpochs.get(scope, 0)):
            _safe(call)
    token = BigWorld.callback(delay, invoke)
    holder.append(token)
    _callbacks[token] = scope
    return token

def _clearScope(scope):
    import BigWorld
    _scopeEpochs[scope] = _scopeEpochs.get(scope, 0) + 1
    for token, owner in list(_callbacks.items()):
        if owner == scope:
            _callbacks.pop(token, None)
            _safe(lambda token=token: BigWorld.cancelCallback(token))
    for event, handler, owner in list(_subscriptions):
        if owner == scope:
            _safe(lambda event=event, handler=handler: event.__isub__(handler))
            _subscriptions.remove((event, handler, owner))
    for cls, name, original, wrapper, owner, active in list(_hooks):
        if owner == scope:
            active[0] = False
            current = getattr(cls, name)
            if getattr(current, 'im_func', current) is wrapper:
                setattr(cls, name, original)
            _hooks.remove((cls, name, original, wrapper, owner, active))


def _log(text):
    try:
        import debug_utils
        debug_utils.LOG_NOTE('[Marks] %s' % (text,))
    except Exception:
        pass

    return


def _safe(call, note=''):
    try:
        return call()
    except Exception:
        _log('%s failed: %s' % (note or 'call',
         traceback.format_exc().replace('\n', ' | ')[:400]))
        return

    return


def _int(value, default=0):
    try:
        return int(round(float(value)))
    except Exception:
        return default

    return


def _num(value, digits=0):
    try:
        value = float(value)
    except Exception:
        return '--'

    if digits:
        return '%.*f' % (digits, value)
    text = '%d' % int(round(value))
    out = ''
    while len(text) > 3:
        out = ' ' + text[-3:] + out
        text = text[:-3]

    return text + out


def _ensureDir():
    if not os.path.isdir(CONFIG_DIR):
        try:
            os.makedirs(CONFIG_DIR)
        except Exception:
            pass

    return


LOOK = {'celebration': 1, 
   'battleSkin': 'plate', 
   'classicKind': 'v2', 
   'contourTank': 'bzt70', 
   'battleScale': 1.0, 
   'battleAlpha': 1.0, 
   'battleBackA': (-1.0), 
   'battleHide': False, 
   'rowStars': True, 
   'rowBar': True, 
   'rowDealt': True, 
   'rowGoal': True, 
   'rowAlt': True, 
   'altAlpha': 0.86, 
   'altRows': 'col', 
   'altSide': 'under', 
   'accent': '#f0c46a', 
   'thr65': '', 
   'thr85': '', 
   'thr95': '', 
   'thr100': '', 
   'cUp': '#7ce092', 
   'cDn': '#ff6a5a', 
   'cMark': '#f0c46a', 
   'cEven': '#f2f4f7', 
   'cTank': '', 
   'label': '', 
   'hangarSkin': 'full', 
   'hangarAlpha': 0.9, 
   'hangarCompact': False, 
   'hangarSteps': True, 
   'hangarOdds': True, 
   'hangarSession': True, 
   'hangarRows': True, 
   'hangarTh': True, 
   'thKind': 'moe', 
   'markKind': 'star', 
   'markAnim': 'glint'}

def _look():
    cfg = _config()
    out = {}
    for key, fallback in LOOK.items():
        value = cfg.get(key, fallback)
        if isinstance(fallback, bool):
            value = 1 if value else 0
        elif isinstance(fallback, str):
            value = str(value)
        out[key] = value

    if out.get('classicKind') == 'v1':
        out['classicKind'] = 'v2'
    return out


UI_SOUNDS = {'click': 'highlight', 'tab': 'shop_selecting_tab', 'toggle': 'highlight', 
   'tank': 'tank_selection', 'open': 'gui_pbs_overlay_open', 
   'close': 'gui_pbs_overlay_close'}

def _playUI(kind):
    cfg = _config()
    name = str(cfg.get('sound_' + kind) or UI_SOUNDS.get(kind) or '')
    if not name:
        return
    import SoundGroups
    SoundGroups.g_instance.playSound2D(name)
    return


def _configSet(key, value):
    if key not in LOOK:
        return
    cfg = _config()
    if key == 'contourTank' and value not in CONTOUR_TANKS:
        value = 'bzt70'
    if isinstance(LOOK[key], str):
        try:
            if not isinstance(value, (str, unicode)):
                value = str(value)
        except Exception:
            value = ''

        value = value[:24]
        cfg[key] = value
        _ensureDir()
        _safe((lambda : open(CONFIG_FILE, 'wb').write(json.dumps(cfg, indent=4))))
        _log('look: %s = %r' % (key, value))
        _safe(_payload)
        _safe(_battlePush)
        return
    if isinstance(LOOK[key], bool):
        value = bool(value) and str(value) not in ('0', 'false', 'False')
    else:
        try:
            value = float(value)
        except Exception:
            return

        if isinstance(LOOK[key], int) and not isinstance(LOOK[key], bool):
            value = int(round(value))
    cfg[key] = value
    _ensureDir()
    _safe((lambda : open(CONFIG_FILE, 'wb').write(json.dumps(cfg, indent=4))))
    _log('look: %s = %s' % (key, value))
    _safe(_payload)
    _safe(_battlePush)
    return


CONTOUR_TANKS = (
 'bzt70', 'sfac105', 'serpente', 't92hmc', 'bz176', 'wte100', 'type5', 'conqgc')

def _config():
    cfg = _state.get('config')
    if cfg is not None:
        return cfg
    else:
        cfg = {'ema': EMA_K, 'goalPercent': GOAL_PERCENT, 'goalBattles': GOAL_BATTLES, 
           'assistStun': True, 'panel': False, 'panelFlags': 'WINDOW', 
           'panelLayer': 'MARKER'}
        cfg.update(dict(LOOK))
        _ensureDir()
        if os.path.isfile(CONFIG_FILE):
            got = _safe((lambda : json.loads(open(CONFIG_FILE, 'rb').read())))
            if isinstance(got, dict):
                cfg.update(got)
            try:
                if abs(float(cfg.get('ema') or 0) - 0.1) < 1e-09:
                    cfg['ema'] = EMA_K
                    _safe((lambda : open(CONFIG_FILE, 'wb').write(json.dumps(cfg, indent=4))))
                    _log('the old moving-total factor 0.1 was replaced by %s' % (
                     EMA_K,))
            except Exception:
                pass

        else:
            _safe((lambda : open(CONFIG_FILE, 'wb').write(json.dumps(cfg, indent=4))))
        if cfg.get('contourTank') not in CONTOUR_TANKS:
            cfg['contourTank'] = 'bzt70'
            _safe((lambda : open(CONFIG_FILE, 'wb').write(json.dumps(cfg, indent=4))))
        _state['config'] = cfg
        return cfg


def _history():
    hist = _state.get('history')
    if hist is not None:
        return hist
    else:
        hist = {}
        if os.path.isfile(HISTORY_FILE):
            got = _safe((lambda : json.loads(open(HISTORY_FILE, 'rb').read())))
            if isinstance(got, dict):
                hist = got
        _state['history'] = hist
        return hist


OLD_FILE = CONFIG_DIR + 'marks.json'

def _importOld():
    if _history():
        return
    if not os.path.isfile(OLD_FILE):
        return
    data = _safe((lambda : json.loads(open(OLD_FILE, 'rb').read())))
    if not isinstance(data, dict):
        return
    hist = _history()
    taken = 0
    for key, row in data.items():
        rows = (row or {}).get('log') or []
        battles = []
        for item in rows:
            if not isinstance(item, (list, tuple)) or len(item) < 3:
                continue
            battles.append({'ts': 0, 'dmg': (int(item[1] or 0)), 'radio': 0, 'track': 0, 
               'stun': 0, 'rating': (float(item[2] or 0)), 
               'marks': (int((row or {}).get('marks') or 0))})

        if battles:
            vehicle = _vehicleByCD(key)
            hist[str(key)] = {'name': (_safe((lambda : vehicle.shortUserName)) or str(key)), 
               'battles': battles}
            taken += len(battles)

    if taken:
        _saveHistory()
        _log('took over %d battles on %d vehicles from the earlier marks file' % (
         taken, len(hist)))
    return


def _rowKey(row):
    return (
     round(float(row.get('prev') or -1), 2),
     round(float(row.get('rating') or -1), 2))


def _forget(key, rows):
    gone = _state.setdefault('dropped', {}).setdefault(str(key), set())
    for row in rows or ():
        gone.add(_rowKey(row))

    return gone


def _wasForgotten(key, row):
    return _rowKey(row) in (_state.get('dropped') or {}).get(str(key), ())


def _saveHistory():
    _ensureDir()
    hist = _history()
    disk = None
    if os.path.isfile(HISTORY_FILE):
        disk = _safe((lambda : json.loads(open(HISTORY_FILE, 'rb').read())))
    if isinstance(disk, dict):
        for key, row in disk.items():
            mine = hist.get(key)
            if mine is None:
                hist[key] = row
                continue
            known = set()
            for one in mine.get('battles') or ():
                known.add(_rowKey(one))

            extra = [one for one in row.get('battles') or () if _rowKey(one) not in known and not _wasForgotten(key, one)]
            if not extra:
                continue
            merged = list(mine.get('battles') or ())
            for one in extra:
                ends = one.get('rating')
                at = len(merged)
                if ends is not None:
                    for index in range(len(merged)):
                        starts = merged[index].get('prev')
                        if starts is not None and float(starts) >= float(ends) - 0.0001:
                            at = index
                            break

                merged.insert(at, one)

            mine['battles'] = merged
            _log('history: %d battle(s) of %s were kept from the file' % (
             len(extra), mine.get('name') or key))

    _safe((lambda : open(HISTORY_FILE, 'wb').write(json.dumps(hist))))
    return


def _items():
    from helpers import dependency
    from skeletons.gui.shared import IItemsCache
    return dependency.instance(IItemsCache).items


def _currentVehicle():
    from CurrentVehicle import g_currentVehicle
    if not g_currentVehicle.isPresent():
        return None
    else:
        return g_currentVehicle.item


def _vehicleByCD(intCD):
    return _safe((lambda : _items().getItemByCD(int(intCD))))


MARK_ON_GUN_RECORD = (
 'achievements', 'marksOnGun')

def _randomBattles(vehicle):
    if vehicle is None:
        return 0
    else:
        intCD = _safe((lambda : int(vehicle.intCD)))
        dossier = _safe((lambda : _items().getVehicleDossier(intCD)))
        if dossier is None:
            dossier = _safe((lambda : vehicle.getDossier()))
        if dossier is None:
            return 0
        rnd = _safe((lambda : dossier.getRandomStats()))
        if rnd is None:
            return 0
        return int(_safe((lambda : rnd.getBattlesCount())) or 0)


def _markData(vehicle):
    if vehicle is None:
        return (0, 0.0)
    else:
        intCD = _safe((lambda : int(vehicle.intCD)))
        dossier = _safe((lambda : _items().getVehicleDossier(intCD)))
        if dossier is None:
            dossier = _safe((lambda : vehicle.getDossier()))
        if dossier is None:
            return (0, 0.0)
        rnd = _safe((lambda : dossier.getRandomStats()))
        if rnd is None:
            return (0, 0.0)
        item = _safe((lambda : rnd.getAchievement(MARK_ON_GUN_RECORD)))
        if item is None:
            return (0, 0.0)
        count = int(_safe((lambda : item.getValue())) or 0)
        pct = float(_safe((lambda : item.getDamageRating())) or 0.0)
        return (count, pct)


TABLE_FILE = CONFIG_DIR + 'marks_table.json'
TABLE_PART = CONFIG_DIR + 'marks_table.part'
SEED_AT = 1791830589.768
SEED = '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'
TABLE_URLS = (
 'https://raw.githubusercontent.com/RavenStryker/wot-moe-thresholds/refs/heads/main/public/thresholds.json',)
MIRROR_URL = TABLE_URLS[0]
LAST_RESORT = 'https://gunmarks.app/api/tanks/%s'
TABLE_URL = 'https://gunmarks.app/api/tanks/%s'
BROWSER_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
TABLE_TTL = 3 * 3600
TABLE_COLUMNS = ((65.0, 'moe1'), (85.0, 'moe2'), (95.0, 'moe3'),
 (
  100.0, 'moe100'))
MASTERY_COLUMNS = (
 (
  '3', 'mastery3'), ('2', 'mastery2'),
 (
  '1', 'mastery1'), ('ace', 'mastery_ace'))

def _region():
    try:
        from realm import CURRENT_REALM
        realm = str(CURRENT_REALM or '').lower()
    except Exception:
        return

    if realm in ('asia', 'sea', 'as'):
        return 'asia'
    if realm in ('eu', 'na'):
        return realm
    else:
        return


def _parseTable(raw, trustedRegion=None):
    try:
        data = json.loads(raw)
    except Exception as exc:
        _log('the thresholds came back unreadable: %r' % (exc,))
        return

    if isinstance(data, dict) and data.get('region') and data['region'] != _region():
        return None
    if isinstance(data, dict) and isinstance(data.get('realms'), dict):
        realm = data['realms'].get(_region())
        if not isinstance(realm, dict):
            return None
        if isinstance(realm, dict):
            when = _safe((lambda : float(realm.get('updated_at') or 0))) or 0
            if when > 0:
                import time as _t
                _log('the thresholds in that table are from %s UTC (%.1f hours old)' % (
                 _t.strftime('%d.%m %H:%M', _t.gmtime(when)),
                 (_t.time() - when) / 3600.0))
                _state['tableMade'] = when
            data = realm.get('thresholds') or realm
    elif isinstance(data, dict) and data.get('region') == _region() and _region():
        pass
    elif not trustedRegion or trustedRegion != _region():
        _log('ignoring thresholds without matching regional provenance')
        return None
    for _ in (1, 2, 3):
        if not isinstance(data, dict):
            break
        for key in ('tanks', 'data', 'rows', 'result', 'marks', 'moe'):
            if isinstance(data.get(key), (dict, list)):
                data = data[key]
                break
        else:
            break

    out = {}

    def four(values):
        marks = {}
        for percent, value in values:
            try:
                value = int(round(float(value)))
            except Exception:
                continue

            if value > 0:
                marks[float(percent)] = value

        return marks

    if isinstance(data, list):
        for row in data:
            if not isinstance(row, dict):
                continue
            cd = row.get('tank_id', row.get('tankId', row.get('id')))
            try:
                cd = int(cd)
            except Exception:
                continue

            marks = four([(p, row.get(c)) for p, c in TABLE_COLUMNS])
            if not marks:
                marks = four([(p, row.get(str(int(p)))) for p in (65, 85, 95, 100)])
            if cd > 0 and cd & 15 == 1 and marks:
                out[cd] = marks
                badge = {}
                for name, column in MASTERY_COLUMNS:
                    value = row.get(column)
                    try:
                        value = int(round(float(value)))
                    except Exception:
                        continue

                    if value > 0:
                        badge[name] = value

                if badge:
                    _state.setdefault('masteryTable', {})[cd] = badge

    elif isinstance(data, dict):
        for key, row in data.items():
            try:
                cd = int(key)
            except Exception:
                continue

            if cd <= 0 or cd & 15 != 1:
                continue
            marks = {}
            if isinstance(row, list):
                tail = [x for x in row if not isinstance(x, basestring)]
                if len(tail) >= 4:
                    marks = four(zip((65, 85, 95, 100), tail[-4:]))
            elif isinstance(row, dict):
                marks = four([(p, row.get(str(int(p)), row.get(str(p)))) for p in (65,
                                                                                   85,
                                                                                   95,
                                                                                   100)])
                if not marks:
                    marks = four([(p, row.get(c)) for p, c in TABLE_COLUMNS])
            if marks:
                out[cd] = marks

    if not out:
        _log('the thresholds came back in a shape the mod cannot read')
        return
    else:
        return out


def _tableSeed():
    if not SEED or _region() != 'eu':
        return False
    if os.path.isfile(TABLE_FILE):
        got = _safe((lambda : json.loads(open(TABLE_FILE, 'rb').read()))) or {}
        if got.get('region') == _region() and float(got.get('at') or 0) >= SEED_AT and got.get('rows'):
            return False

    def run():
        import base64, zlib
        raw = zlib.decompress(base64.b64decode(SEED))
        data = json.loads(raw)
        if data.get('region') != _region():
            return False
        _ensureDir()
        open(TABLE_FILE, 'wb').write(json.dumps(data))
        _log('the built-in thresholds were laid out: %d vehicles' % (
         len(data.get('rows') or {}),))
        return True

    return bool(_safe(run))


def _table():
    import time
    region = _region()
    if _state.get('tableRegion') != region:
        for key in ('table', 'tableAt', 'tableMade', 'tableFrom', 'tableMoved', 'masteryTable', 'masteryBusy', 'tableBusy', 'tableTry', 'tableRaw', 'seeded', 'seenCD', 'snapshot'):
            _state.pop(key, None)
        _state['tableRegion'] = region
        _state['tableGeneration'] = int(_state.get('tableGeneration') or 0) + 1
    if not _state.get('seeded'):
        _state['seeded'] = True
        _safe(_tableSeed)
    table = _state.get('table')
    if table is not None:
        age = time.time() - float(_state.get('tableAt') or 0)
        if age > TABLE_TTL and not _state.get('tableBusy'):
            _safe(_fetchTable)
        return table
    fresh = None
    if os.path.isfile(TABLE_FILE):
        got = _safe((lambda : json.loads(open(TABLE_FILE, 'rb').read())))
        if isinstance(got, dict) and region and got.get('region') == region and got.get('rows'):
            _state['tableAt'] = float(got.get('at') or 0)
            age = time.time() - float(got.get('at') or 0)
            fresh = got if age < TABLE_TTL else None
            if fresh is None:
                _log('the thresholds on disk are %d hours old, asking again' % (
                 age / 3600,))
            table = {}
            for key, row in (got.get('rows') or {}).items():
                table[_int(key)] = dict((float(k), _int(v)) for k, v in row.items() if _int(v) > 0)

            _state['table'] = table
            _state['tableFrom'] = str(got.get('src') or '')
            if isinstance(got.get('moved'), dict):
                _state['tableMoved'] = got['moved']
            badges = {}
            for key, row in (got.get('mastery') or {}).items():
                badges[_int(key)] = dict((str(k), _int(v)) for k, v in row.items() if _int(v) > 0)

            if badges:
                _state['masteryTable'] = badges
            else:
                _log('the table on disk has no badge figures')
                _safe(_masteryFetch)
    if fresh is None:
        _safe(_fetchTable)
    return _state.get('table')


def _requests():
    got = _state.get('requests')
    if got:
        return got
    else:
        try:
            import requests
            _state['requests'] = requests
            _log('the client has requests - the thresholds go through it')
            return requests
        except Exception as exc:
            if not _state.get('noRequests'):
                _state['noRequests'] = True
                _log('the client has no requests (%r) - urllib it is' % (exc,))

        return


def _httpGet(url, headers, timeout):
    lib = _state.get('requests')
    if lib:
        answer = lib.get(url, headers=headers, timeout=(10, timeout))
        heads = {}
        try:
            for key in answer.headers:
                heads[str(key).lower()] = answer.headers[key]

        except Exception:
            pass

        return (
         int(answer.status_code), heads, answer.content)
    import urllib2, zlib
    ask = urllib2.Request(url, headers=headers)
    try:
        answer = urllib2.urlopen(ask, timeout=timeout)
        code = int(answer.getcode() or 200)
    except urllib2.HTTPError as err:
        answer = err
        code = int(err.code)

    heads = {}
    try:
        for key in answer.info().keys():
            heads[str(key).lower()] = answer.info().get(key)

    except Exception:
        pass

    body = answer.read()
    packed = str(heads.get('content-encoding') or '').lower()
    if packed.find('gzip') >= 0:
        body = zlib.decompress(body, 16 + zlib.MAX_WBITS)
    elif packed.find('deflate') >= 0:
        body = zlib.decompress(body)
    return (
     code, heads, body)


def _tableAtOnce(url):
    try:
        code, heads, body = _httpGet(url, {'User-Agent': BROWSER_UA, 
           'Connection': 'close', 'Accept-Encoding': 'gzip, deflate'}, 30)
    except Exception as exc:
        _log('the thresholds did not come at once: %r' % (exc,))
        return

    if code != 200:
        _log('the thresholds answered %d' % (code,))
        return
    else:
        _log('the thresholds came back at once: %d bytes' % (len(body or ''),))
        return body


def _tableByChunks(url):
    import time
    step = 131072
    head = {'User-Agent': BROWSER_UA, 'Connection': 'close', 'Accept-Encoding': 'identity'}

    def oldPart():
        if not os.path.isfile(TABLE_PART):
            return (0, '')
        if time.time() - os.path.getmtime(TABLE_PART) > 3600:
            return (0, '')
        return (
         os.path.getsize(TABLE_PART), open(TABLE_PART, 'rb').read())

    got = _safe(oldPart) or (0, '')
    pos = int(got[0] or 0)
    parts = [got[1]] if got[1] else []
    if pos:
        _log('carrying on with the thresholds from %d bytes' % (pos,))
    total = None
    while True:
        ask = dict(head)
        ask['Range'] = 'bytes=%d-%d' % (pos, pos + step - 1)
        body = None
        for attempt in (1, 2, 3):
            try:
                code, heads, body = _httpGet(url, ask, 25)
            except Exception as exc:
                _log('a piece of the thresholds was lost (%d, try %d): %r' % (
                 pos, attempt, exc))
                body = None
                if attempt < 3:
                    time.sleep(3)
                continue

            if code == 200:
                _log('the thresholds came back whole: %d bytes' % (
                 len(body or ''),))
                _safe((lambda : os.remove(TABLE_PART)))
                return body
            if code != 206:
                _log('the thresholds answered %d' % (code,))
                return
            span = str(heads.get('content-range') or '')
            if span.find('/') >= 0:
                try:
                    total = int(span.split('/')[-1])
                except Exception:
                    total = None

            break

        if body is None:
            _ensureDir()
            _safe((lambda : open(TABLE_PART, 'wb').write(('').join(parts))))
            _log('the thresholds are %d bytes in so far, kept for later' % (
             pos,))
            return
        parts.append(body)
        pos += len(body)
        if not body or total and pos >= total:
            break
        if pos > 16777216:
            return

    raw = ('').join(parts)
    _safe((lambda : os.remove(TABLE_PART)))
    _log('the thresholds came back in %d pieces: %d bytes' % (
     len(parts), len(raw)))
    return raw


NEIGHBOURS = (
 CONFIG_DIR + '../app.gunmarks/moe/cache.json',)

def _tableSrc(url):
    text = str(url or '')
    i = text.find('://')
    if i >= 0:
        text = text[i + 3:]
    text = text.split('/')[0].split('?')[0].lower()
    if not text:
        return ''
    if text.startswith('www.'):
        text = text[4:]
    if text.startswith('raw.'):
        text = text[4:]
    return text


def _tableFromNeighbour():
    import time
    best = None
    for path in NEIGHBOURS:
        if not os.path.isfile(path):
            continue
        got = _safe((lambda path=path: json.loads(open(path, 'rb').read())))
        if not _region() or (got or {}).get('region') != _region():
            continue
        marks = (got or {}).get('marks') or {}
        tanks = marks.get('tanks') or {}
        when = float(marks.get('fetchedAt') or 0)
        if not tanks or when <= 0:
            continue
        if when <= float(_state.get('tableAt') or 0):
            continue
        if best is None or when > best[0]:
            best = (
             when, tanks)

    if best is None:
        return False
    else:
        when, tanks = best
        table = {}
        store = {}
        for key, row in tanks.items():
            try:
                cd = int(key)
            except Exception:
                continue

            if cd <= 0 or cd & 15 != 1 or not isinstance(row, list):
                continue
            marks = {}
            for i, percent in enumerate((65.0, 85.0, 95.0, 100.0)):
                try:
                    value = int(round(float(row[i + 1])))
                except Exception:
                    continue

                if value > 0:
                    marks[percent] = value

            if marks:
                table[cd] = marks
                store[str(cd)] = dict((str(k), v) for k, v in marks.items())

        if not table:
            return False
        _safe((lambda : _tableDiff(_state.get('table') or {}, table, 'gunmarks.app')))
        _state['tableFrom'] = 'gunmarks.app'
        _state['table'] = table
        _safe((lambda : _sweepGarage(' after a fresh table')))
        _state['tableAt'] = when
        _ensureDir()
        _safe((lambda : open(TABLE_FILE, 'wb').write(json.dumps({'at': when, 'region': _region(), 'rows': store, 'src': 'gunmarks.app', 
           'moved': (_state.get('tableMoved') or {}), 
           'mastery': (dict((str(k), v) for k, v in (_state.get('masteryTable') or {}).items()))}))))
        _log('the thresholds were taken from a neighbouring mod: %d vehicles, %d hours old' % (
         len(table), (time.time() - when) / 3600))
        _safe(_refresh)
        return True


def _tableFromFile():
    path = CONFIG_DIR + 'marks_table.raw'
    if not os.path.isfile(path):
        return None
    else:
        when = _safe((lambda : os.path.getmtime(path))) or 0
        if when <= float(_state.get('tableRaw') or 0):
            return None
        _state['tableRaw'] = when
        raw = _safe((lambda : open(path, 'rb').read()))
        if not raw:
            return None
        _log('a thresholds file was found beside the mod: %d bytes' % (
         len(raw),))
        return raw


def _fetchViaEngine(url, after):
    lifecycle = _state.get('lifecycle', 0)
    generation = _state.get('tableGeneration')
    region = _region()

    def run():
        import BigWorld
        if not hasattr(BigWorld, 'fetchURL'):
            _log('the client has no fetchURL of its own')
            return False

        def back(response):
            if (_state.get('stopped') or lifecycle != _state.get('lifecycle', 0) or
                    generation != _state.get('tableGeneration') or region != _region()):
                return
            code = int(_safe((lambda : int(response.responseCode))) or 0)
            body = _safe((lambda : response.body)) or ''
            _log('the thresholds (engine): code=%s, %d bytes' % (
             code, len(body)))
            if code != 200 and body:
                head = str(body)[:200].replace('\n', ' ').replace('\r', ' ')
                _log('the thresholds (engine) said: %s' % (head,))
            after(code, body)
            return

        BigWorld.fetchURL(url, back, [
         'User-Agent: ' + BROWSER_UA,
         'Accept: application/json'], 60, 'GET', '')
        _log('the thresholds were asked for through the client itself')
        return True

    return _safe(run)


def _fetchTable():
    if _state.get('tableBusy'):
        return
    import time as _time
    since = _time.time() - float(_state.get('tableTry') or 0)
    if since < 1800:
        return
    _state['tableTry'] = _time.time()
    region = _region()
    if not region:
        _log('regional thresholds unavailable: unsupported realm')
        return
    generation = _state.get('tableGeneration')
    lifecycle = _state.get('lifecycle', 0)

    def _requestCurrent():
        return (not _state.get('stopped') and _region() == region and
                generation == _state.get('tableGeneration') and
                lifecycle == _state.get('lifecycle', 0))

    custom = _config().get('tableUrl') or _config().get('tableUrls') or ''
    if isinstance(custom, (list, tuple)):
        sources = [str(x) for x in custom if x]
    else:
        sources = [str(custom)] if custom else []
    if not _state.get('table') and _safe(_tableFromNeighbour):
        return
    _state['tableBusy'] = True
    _safe(_requests)

    def keep(raw):
        import time
        if not _requestCurrent():
            return False
        url = (_state.get('tableSources') or [''])[0]
        trusted = region if url == TABLE_URL % region else None
        table = _parseTable(raw, trusted)
        if not table:
            _safe((lambda : os.remove(TABLE_PART)))
            return False
        store = {}
        for cd, marks in table.items():
            store[str(cd)] = dict((str(k), v) for k, v in marks.items())

        src = _tableSrc((_state.get('tableSources') or [''])[0])
        _safe((lambda : _tableDiff(_state.get('table') or {}, table, src)))
        _state['tableFrom'] = src
        _state['table'] = table
        _state['tableAt'] = time.time()
        _ensureDir()
        _safe((lambda : open(TABLE_FILE, 'wb').write(json.dumps({'at': (time.time()), 'region': region, 'rows': store, 'src': (_state.get('tableFrom') or ''), 
           'moved': (_state.get('tableMoved') or {}), 
           'mastery': (dict((str(k), v) for k, v in (_state.get('masteryTable') or {}).items()))}))))
        _log('thresholds for %d vehicles (%s)' % (len(table), region))
        _safe((lambda : _sweepGarage(' after a fresh table')))
        if not _state.get('masteryTable'):
            _safe(_masteryFetch)
        return True

    def viaEngine(code, body):
        if not _requestCurrent():
            return
        _state['tableBusy'] = False
        code = int(code or 0)
        if code in (200, 304) and body and _safe((lambda : keep(body))):
            _safe(_refresh)
            return
        if code == 304:
            _log('that source says nothing has changed - keeping the table we have')
            return
        rest = list(_state.get('tableSources') or [])[1:]
        if rest:
            _state['tableSources'] = rest
            _log('that source gave nothing - trying the next one')
            _state['tableBusy'] = True
            if _fetchViaEngine(rest[0], viaEngine):
                return
            _state['tableBusy'] = False
        _log('the fetch through the client brought nothing - trying python')
        _state['tableBusy'] = True
        _safe((lambda : __import__('threading').Thread(target=work).start()))
        return

    def work():
        import time
        url = (_state.get('tableSources') or [TABLE_URL % (region,)])[0]
        _log('asking for the thresholds: %s' % (url,))
        raw = _safe(_tableFromFile)
        if raw is None:
            raw = _safe((lambda : _tableAtOnce(url)))
        if raw is None:
            raw = _safe((lambda : _tableByChunks(url)))
        if raw is None:
            _state['tableBusy'] = False
            return
        else:
            if not _requestCurrent():
                return
            def finish():
                if not _requestCurrent():
                    return
                took = _safe(lambda: keep(raw))
                _state['tableBusy'] = False
                if took:
                    _safe(_refresh)
            _safe(lambda: _schedule(0.0, finish))
            return

    if not sources:
        sources = []
        for one in TABLE_URLS:
            sources.append(one % (region,) if one.count('%s') else one)

        if not _state.get('table'):
            sources.append(LAST_RESORT % (region,))
    _state['tableSources'] = list(sources)
    url = sources[0]
    if _fetchViaEngine(url, viaEngine):
        return
    try:
        import threading
        threading.Thread(target=work).start()
    except Exception as exc:
        _log('the thresholds request could not start: %r' % (exc,))
        _state['tableBusy'] = False
        return

    _log('the thresholds were asked for (%s)' % (region,))
    return


def _parseMastery(raw):
    data = _safe((lambda : json.loads(raw)))
    if isinstance(data, dict):
        for key in ('tanks', 'data', 'rows', 'result'):
            if isinstance(data.get(key), list):
                data = data[key]
                break

    if not isinstance(data, list):
        return {}
    out = {}
    for row in data:
        if not isinstance(row, dict):
            continue
        cd = _int(row.get('tank_id', row.get('tankId', row.get('id'))), -1)
        if cd <= 0 or cd & 15 != 1:
            continue
        badge = {}
        for name, column in MASTERY_COLUMNS:
            value = _int(row.get(column))
            if value > 0:
                badge[name] = value

        if badge:
            out[cd] = badge

    return out


def _masterySave():
    got = _safe((lambda : json.loads(open(TABLE_FILE, 'rb').read())))
    if not isinstance(got, dict) or not _region() or got.get('region') != _region() or not got.get('rows'):
        return False
    got['mastery'] = dict((str(k), v) for k, v in (_state.get('masteryTable') or {}).items())
    _ensureDir()
    _safe((lambda : open(TABLE_FILE, 'wb').write(json.dumps(got))))
    return True


def _masteryFetch():
    if _state.get('masteryBusy') or _state.get('masteryTable'):
        return False
    region = _region()
    if not region:
        return False
    generation = _state.get('tableGeneration')
    lifecycle = _state.get('lifecycle', 0)
    url = TABLE_URL % (region,)
    _state['masteryBusy'] = True

    def take(raw):
        if (_state.get('stopped') or region != _region() or
                generation != _state.get('tableGeneration') or
                lifecycle != _state.get('lifecycle', 0)):
            return False
        got = _parseMastery(raw)
        _state['masteryBusy'] = False
        if not got:
            _log('the badge figures came back in a shape the mod cannot read')
            return False
        _state['masteryTable'] = got
        _log('class badge figures for %d vehicles (%s)' % (len(got), region))
        _safe(_masterySave)
        return True

    def viaEngine(code, body):
        if int(code or 0) == 200 and body and _safe((lambda : take(body))):
            _safe(_refresh)
            return
        _state['masteryBusy'] = False
        _log('the badge figures were not given (code=%s)' % (code,))
        return

    _log('asking for the class badge figures: %s' % (url,))
    if _fetchViaEngine(url, viaEngine):
        return True

    def work():
        raw = _safe((lambda : _tableAtOnce(url)))
        if raw is None:
            raw = _safe((lambda : _tableByChunks(url)))
        if raw is None:
            _state['masteryBusy'] = False
            return
        else:
            def finish():
                if _safe(lambda: take(raw)):
                    _safe(_refresh)
            _safe(lambda: _schedule(0.0, finish))
            return

    try:
        import threading
        threading.Thread(target=work).start()
        return True
    except Exception:
        _state['masteryBusy'] = False
        return False

    return


def _exact(intCD):
    table = _table()
    if not table:
        return None
    else:
        found = table.get(int(intCD))
        seen = _state.setdefault('seenCD', set())
        if intCD not in seen:
            seen.add(intCD)
            _log('thresholds for %s: %s (%d vehicles in the table)' % (
             intCD, 'yes' if found else 'no', len(table)))
        return found


def _totalAt(percent, marks):
    points = sorted(marks.items())
    if not points:
        return None
    else:
        percent = float(percent)
        if percent <= points[0][0]:
            return points[0][1] * percent / points[0][0]
        for i in range(1, len(points)):
            left, right = points[i - 1], points[i]
            if percent <= right[0]:
                span = right[0] - left[0]
                part = (percent - left[0]) / span if span else 0.0
                return left[1] + (right[1] - left[1]) * part

        return points[-1][1]


SHAPE = (
 (
  50.0, 0.4), (65.0, 0.566), (85.0, 0.801), (95.0, 1.0),
 (
  100.0, 1.133))

def _shapeAt(percent):
    percent = float(percent)
    if percent <= SHAPE[0][0]:
        first = SHAPE[0]
        return max(0.05, first[1] * percent / first[0])
    for i in range(1, len(SHAPE)):
        left, right = SHAPE[i - 1], SHAPE[i]
        if percent <= right[0]:
            span = right[0] - left[0]
            part = (percent - left[0]) / span if span else 0.0
            return left[1] + (right[1] - left[1]) * part

    return SHAPE[-1][1]


def _movingTotal(vehicle):
    dossier = _safe((lambda : _items().getVehicleDossier(int(vehicle.intCD))))
    if dossier is None:
        return
    else:
        descr = _safe((lambda : dossier.getDossierDescr()))
        if descr is None:
            return
        value = _safe((lambda : descr['achievements']['movingAvgDamage']))
        if value is None:
            value = _safe((lambda : descr.getRecordValue('achievements', 'movingAvgDamage')))
        try:
            value = float(value)
        except Exception:
            return

        if value > 0:
            return value
        return


def _accountPoint(vehicle):
    dossier = _safe((lambda : _items().getVehicleDossier(int(vehicle.intCD))))
    if dossier is None:
        return
    else:
        rnd = _safe((lambda : dossier.getRandomStats()))
        if rnd is None:
            return
        battles = int(_safe((lambda : rnd.getBattlesCount())) or 0)
        if battles < 1:
            return
        total = float(_safe((lambda : rnd.getDamageDealt())) or 0)
        total += float(_safe((lambda : rnd.getDamageAssistedRadio())) or 0)
        total += float(_safe((lambda : rnd.getDamageAssistedTrack())) or 0)
        if _config().get('assistStun'):
            total += float(_safe((lambda : rnd.getDamageAssistedStun())) or 0)
        return {'battles': battles, 'avg': (total / battles)}


def _value(entry):
    cfg = _config()
    radio = float(entry.get('radio') or 0)
    track = float(entry.get('track') or 0)
    assist = radio if radio >= track else track
    stun = float(entry.get('stun') or 0)
    if cfg.get('assistStun') and stun > assist:
        assist = stun
    return float(entry.get('dmg') or 0) + assist


def _battleOdds(snap):
    total = int(float(snap.get('total') or 0))
    if total <= 0:
        return
    else:
        step = max(250, int(round(total * 0.25 / 50.0)) * 50)
        rows = []
        for mult in (-2, -1, 0, 1, 2):
            value = total + step * mult
            if value <= 0:
                continue
            gain = _safe((lambda : _forecast(snap, value)))
            if gain is None:
                continue
            rows.append({'v': (_num(value)), 'raw': value, 'd': ('%+.2f' % gain), 
               'even': (1 if mult == 0 else 0)})

        if rows:
            return {'even': (_num(total)), 'rows': rows}
        return


def _stepsWatch(intCD, marks, quiet=False):
    import time
    if not marks:
        return
    else:
        now = dict((str(int(float(k))), int(v)) for k, v in marks.items() if v)
        if not now:
            return
        hist = _history()
        key = str(int(intCD))
        row = hist.get(key)
        if row is None:
            row = {'name': (_safe((lambda : _vehicleByCD(intCD).shortUserName)) or key), 
               'battles': []}
            hist[key] = row
        was = row.get('stepsSeen')
        if was == now:
            return False
        src = str(_state.get('tableFrom') or '')
        wasSrc = str(row.get('stepsSrc') or '')
        row['stepsSeen'] = now
        row['stepsSrc'] = src
        moved = False
        if was and (not src or not wasSrc or src == wasSrc):
            a = was.get('65')
            b = now.get('65')
            if a and b and a != b:
                row['recalcT'] = {'was': was, 'now': now, 'ts': (int(time.time()))}
                row.pop('recalc', None)
                moved = True
                if not quiet:
                    _log('the thresholds for %s moved while the mod was not looking: 65%% was %d, now %d' % (
                     row.get('name') or key, a, b))
        if not quiet:
            _safe(_saveHistory)
        return moved


def _garageCDs(quiet=False):

    def byCriteria():
        from gui.shared.utils.requesters import REQ_CRITERIA
        return _items().getVehicles(REQ_CRITERIA.INVENTORY)

    def plain():
        return _items().getVehicles()

    def noneCriteria():
        return _items().getVehicles(None)

    def byType():
        from gui.shared.gui_items import GUI_ITEM_TYPE
        return _items().getItems(GUI_ITEM_TYPE.VEHICLE, None)

    def fromInventory():
        from gui.shared.gui_items import GUI_ITEM_TYPE
        return _items().inventory.getItems(GUI_ITEM_TYPE.VEHICLE)

    ways = (
     (
      'the inventory criteria', byCriteria),
     (
      'the plain call', plain),
     (
      'the call with no criteria', noneCriteria),
     (
      'the item type', byType),
     (
      'the inventory requester', fromInventory))
    for name, call in ways:
        try:
            got = call()
        except Exception as exc:
            if not quiet:
                _log('the garage could not be read through %s: %r' % (
                 name, exc))
            continue

        if not got:
            if not quiet:
                _log('%s came back empty' % (name,))
            continue
        out = []
        for key in got:
            cd = _int(key, 0)
            if cd > 0:
                out.append(cd)

        if out:
            if not _state.get('garageSaid'):
                _state['garageSaid'] = True
                _log('the garage was read through %s: %d vehicles' % (
                 name, len(out)))
            return out
        _log('%s gave %d rows and not one usable number' % (
         name, len(got)))

    out = []
    for key in _history() or {}:
        cd = _int(key, 0)
        if cd > 0:
            out.append(cd)

    if not quiet:
        _log('the garage could not be read at all - falling back to the %d vehicles in the history' % (
         len(out),))
    return out


def _sweepAgain(last=0):
    if _state.get('sweptFor'):
        return
    cds = _garageCDs(quiet=not last)
    if not last and len(cds) <= len(_history() or {}):
        return
    if not cds:
        return
    _state['sweptFor'] = len(cds)
    _sweepGarage(' on the way in')
    return


def _sweepGarage(why=''):
    cds = _garageCDs()
    if not cds:
        _log('the garage walk%s found no vehicles at all' % (why,))
        return 0
    moved = 0
    seen = 0
    told = 0
    fresh = 0
    ahead = []
    for intCD in cds:
        marks = _safe((lambda cd=intCD: _exact(cd)))
        if marks:
            seen += 1
            if _safe((lambda cd=intCD, m=marks: _stepsWatch(cd, m, True))):
                moved += 1
        if _safe((lambda cd=intCD: _ratingWatch(cd))):
            told += 1
        had = bool((_history().get(str(int(intCD))) or {}).get('anchor'))
        got = _safe((lambda cd=intCD: _liveWatch(cd)))
        if got:
            ahead.append(got)
        if not had and (_history().get(str(int(intCD))) or {}).get('anchor'):
            fresh += 1

    _safe(_saveHistory)
    _log('the garage was walked%s: %d of %d vehicles have thresholds, %d of them moved; the client itself says the mark changed without a battle on %d' % (
     why, seen, len(cds), moved, told))
    if fresh:
        _log('the forecast was measured for the first time on %d vehicles' % (
         fresh,))
    if ahead:
        ahead.sort(key=(lambda row: -abs(row[0])))
        best = (', ').join('%s %+.2f' % (name, shift) for shift, name in ahead[:8])
        up = sum(1 for shift, name in ahead if shift > 0)
        _log('the thresholds are ahead of the client on %d of %d vehicles (%d of them in your favour): %s' % (
         len(ahead), len(cds), up, best))
    return moved + told


def _liveWatch(intCD):
    vehicle = _safe((lambda : _vehicleByCD(intCD)))
    if vehicle is None:
        return
    else:
        rating = (_safe((lambda : _markData(vehicle))) or (0, 0.0))[1]
        total = _safe((lambda : _movingTotal(vehicle))) or 0
        if not rating or not total:
            return
        row = _historyRow(intCD)
        got = _safe((lambda : _recalcLive(intCD, row, total, rating)))
        if not got:
            return
        return (
         float(got.get('delta') or 0), row.get('name') or str(intCD))


def _ratingWatch(intCD):
    vehicle = _safe((lambda : _vehicleByCD(intCD)))
    if vehicle is None:
        return False
    else:
        rating = (_safe((lambda : _markData(vehicle))) or (0, 0.0))[1]
        if not rating:
            return False
        was = ((_history().get(str(int(intCD))) or {}).get('seen') or {}).get('r')
        if not _safe((lambda : _recalcWatch(intCD, vehicle, rating, True))):
            return False
        return bool(was) and abs(float(was) - float(rating)) >= RECALC_MIN


def _saveMoved():
    if not os.path.isfile(TABLE_FILE):
        return
    got = _safe((lambda : json.loads(open(TABLE_FILE, 'rb').read())))
    if not isinstance(got, dict):
        return
    got['moved'] = _state.get('tableMoved') or {}
    _safe((lambda : open(TABLE_FILE, 'wb').write(json.dumps(got))))
    return


def _movedFor(intCD):
    got = (_state.get('tableMoved') or {}).get(str(int(intCD)))
    if not got or not got.get('was') or not got.get('now'):
        return
    import time
    if time.time() - float(got.get('ts') or 0) > 1209600:
        return
    else:
        return got


def _tableDiff(old, new, src=None):
    import time
    if not old:
        return
    else:
        if src is None:
            src = _tableSrc((_state.get('tableSources') or [''])[0])
        was = str(_state.get('tableFrom') or '')
        if was and src and was != src:
            _log('the thresholds now come from %s instead of %s - the two do not agree to the last point, so this is not a recount' % (
             src, was))
            return
        hist = _history()
        now = int(time.time())
        store = {}
        for cd, marks in new.items():
            before = old.get(cd)
            if not before or before == marks:
                continue
            a = before.get(65) or before.get('65')
            b = marks.get(65) or marks.get('65')
            if not a or not b or a == b:
                continue
            entry = {'was': (dict((str(k), int(v)) for k, v in before.items())), 
               'now': (dict((str(k), int(v)) for k, v in marks.items())), 
               'ts': now}
            store[str(cd)] = entry
            row = hist.get(str(cd))
            if row is not None:
                row['recalcT'] = entry
                row.pop('recalc', None)

        if not store:
            return
        keep = dict(_state.get('tableMoved') or {})
        keep.update(store)
        _state['tableMoved'] = keep
        mine = sum(1 for key in store if key in hist)
        _log('the server moved the thresholds on %d vehicles, %d of them with a history of their own' % (
         len(store), mine))
        if mine:
            _safe(_saveHistory)
        _safe(_saveMoved)
        return


def _recalcCount(row, rec):
    when = float(rec.get('ts') or 0)
    if when <= 0:
        return 0
    best = 0
    for item in row.get('battles') or ():
        if not item:
            continue
        if float(item.get('ts') or 0) <= when:
            best = max(best, int(item.get('bc') or 0))

    return best


def _recalcFresh(intCD, row, rec):
    if not rec:
        return False
    else:
        count = int(_safe((lambda : _randomBattles(_vehicleByCD(intCD)))) or 0)
        if count <= 0:
            return True
        was = rec.get('bc')
        if not was:
            was = _recalcCount(row, rec) or count
            rec['bc'] = was
            _safe(_saveHistory)
        else:
            real = _recalcCount(row, rec)
            if real and real < int(was):
                _log('the recount on %s happened on battle %d, not %d - the badge was holding on by %d battles' % (
                 row.get('name') or intCD, real, int(was),
                 int(was) - real))
                was = real
                rec['bc'] = was
                _safe(_saveHistory)
        if count > int(was):
            row.pop('recalcT', None)
            row.pop('recalc', None)
            _log('the recount on %s is no longer news - a battle has been played since' % (
             row.get('name') or intCD,))
            _safe(_saveHistory)
            return False
        return True


def _historyRow(intCD):
    hist = _history()
    key = str(int(intCD))
    row = hist.get(key)
    if row is None:
        row = {'name': (_safe((lambda : _vehicleByCD(intCD).shortUserName)) or key), 'battles': []}
        hist[key] = row
    return row


def _anchorAt(intCD, total, rating, quiet=False):
    import time
    if not total or not rating:
        return
    now = _curveNow(intCD, total)
    if now is None:
        return
    else:
        row = _historyRow(intCD)
        row['anchor'] = {'avg': (float(total)), 'r': (float(rating)), 'bias': (float(rating) - now), 
           'ts': (int(time.time())), 'bc': (int(_safe((lambda : _randomBattles(_vehicleByCD(intCD)))) or 0)), 
           'by': 'battle', 
           'v': 3}
        if not quiet:
            _log('the forecast on %s is anchored at %.0f damage: the client says %.2f%%, the table says %.2f%% - the line is out by %+.2f here' % (
             row.get('name') or intCD, float(total), float(rating),
             now, float(rating) - now))
        _safe(_saveHistory)
        return


def _firstStep(intCD):
    marks = _safe((lambda : _exact(intCD))) or {}
    best = None
    for key, value in marks.items():
        try:
            if float(key) <= 65.0001 and float(value) > 0:
                if best is None or float(value) < best:
                    best = float(value)
        except Exception:
            continue

    return best


def _curveNow(intCD, total):
    marks = _safe((lambda : _exact(intCD)))
    if not marks or not total or float(total) <= 0:
        return None
    points = []
    for key, value in marks.items():
        try:
            points.append([float(value), float(key)])
        except Exception:
            continue

    if len(points) < 2:
        return None
    else:
        points.sort()
        return _curveAt(points, float(total))


def _recalcAny(intCD, vehicle, total, rating):
    _state.pop('liveSaid', None)
    row = _historyRow(intCD)
    _safe((lambda : _recalcWatch(intCD, vehicle, rating, True)))
    return _safe((lambda : _recalcLive(intCD, row, total, rating)))


def _recalcLive(intCD, row, total, rating):
    import time
    now = _curveNow(intCD, total)
    if now is None or not rating:
        return
    rating = float(rating)
    anchor = row.get('anchor') or {}
    if anchor.get('by') != 'battle' or int(anchor.get('v') or 0) < 2:
        anchor = {}
    bias = None
    if anchor:
        was = int(anchor.get('bc') or 0)
        if was > 0:
            count = int(_safe((lambda : _randomBattles(_vehicleByCD(intCD)))) or 0)
            if count == was:
                bias = float(anchor.get('bias') or 0.0)
        elif anchor.get('avg') and abs(float(anchor['avg']) - float(total)) < 5.0:
            bias = float(anchor.get('bias') or 0.0)
    if bias is None:
        bias = 0.0
    floor = LIVE_MIN
    _state['liveSaid'] = int(intCD)
    shift = now + (bias or 0.0) - rating
    if abs(shift) < floor:
        return
    else:
        return {'delta': ('%+.2f' % shift), 'from': ('%.2f' % rating), 
           'to': ('%.2f' % (rating + shift)), 'kind': 'live', 
           'ts': (int(time.time()))}


def _recalcAcross(intCD, row, was, rating, moved, slope):
    import time
    shift = float(rating or 0) - float(was or 0)
    moved = float(moved or 0)
    if abs(shift) < 0.01 or abs(moved) < 0.5:
        return
    if (moved > 0) == (shift > 0):
        return
    else:
        slope = float(slope or 0)
        if slope <= 0:
            return
        jump = shift - moved * slope
        if abs(jump) < 0.01:
            return
        hist = _history()
        key = str(int(intCD))
        row = hist.get(key)
        if row is None:
            return
        row['recalc'] = {'delta': ('%+.2f' % jump), 'from': ('%.2f' % float(was or 0)), 'to': ('%.2f' % float(rating or 0)), 
           'ts': (int(time.time()))}
        _log('the server recounted the mark on %s across a battle: the total moved %+.0f (worth %+.2f per cent) while the mark moved %+.2f - %+.2f of it is the recount' % (
         row.get('name') or key, moved, moved * slope, shift, jump))
        return row['recalc']


def _recalcWatch(intCD, vehicle, rating, quiet=False):
    import time
    if vehicle is None or not rating:
        return
    count = int(_randomBattles(vehicle) or 0)
    if count <= 0:
        return
    else:
        hist = _history()
        key = str(intCD)
        row = hist.get(key)
        if row is None:
            row = {'name': (_safe((lambda : vehicle.shortUserName)) or key), 
               'battles': []}
            hist[key] = row
        seen = row.get('seen') or {}
        if not seen:
            last = (row.get('battles') or [{}])[-1] or {}
            if last.get('bc') and last.get('rating'):
                seen = {'r': (float(last.get('rating'))), 'bc': (int(last.get('bc'))), 'ts': (int(last.get('ts') or 0))}
        was = float(seen.get('r') or 0)
        wasCount = int(seen.get('bc') or 0)
        dirty = False
        if was and wasCount == count:
            shift = float(rating) - was
            if abs(shift) >= RECALC_MIN:
                row['recalc'] = {'delta': ('%+.2f' % shift), 'from': ('%.2f' % was), 'to': ('%.2f' % float(rating)), 
                   'ts': (int(time.time()))}
                dirty = True
                _log('the server recounted the mark on %s: %.2f -> %.2f (%+.2f) with the battle counter standing at %d' % (
                 row.get('name') or key, was, float(rating), shift,
                 count))
        if wasCount != count or abs(was - float(rating)) >= 0.005:
            row['seen'] = {'r': (float(rating)), 'bc': count, 'ts': (int(time.time()))}
            dirty = True
        if dirty and not quiet:
            _safe(_saveHistory)
        if quiet:
            return row.get('recalc')
        last = row.get('recalc')
        if not last:
            return
        if time.time() - float(last.get('ts') or 0) > 1209600:
            return
        if not _recalcFresh(intCD, row, last):
            return
        return last


def _dayMove(battles, intCD=None):
    _state['dayFor'] = intCD
    start = _dayStart()
    rows = [b for b in battles or () if int(b.get('ts') or 0) >= start]
    if not rows:
        return {'n': 0, 'd': 0.0}
    else:
        move = 0.0
        for row in rows:
            before = row.get('prev')
            after = row.get('rating')
            if before is not None and after is not None:
                move += float(after) - float(before)

        avg = sum(_value(item) for item in rows) / float(len(rows))
        return {'n': (len(rows)), 'd': move, 'avg': (_num(int(round(avg))))}


def _periodMove(battles, seconds):
    import time
    now = time.time()
    first = None
    count = 0
    for item in battles or ():
        stamp = float(item.get('ts') or 0)
        if not stamp or now - stamp > seconds:
            continue
        if first is None:
            first = item
        count += 1

    if first is None or not count:
        return
    before = first.get('prev')
    after = (battles[-1] or {}).get('rating')
    if before is None or after is None:
        return
    return {'n': count, 'delta': ('%+.2f' % (float(after) - float(before)))}


def _series(intCD):
    row = _history().get(str(intCD)) or {}
    return list(row.get('battles') or [])


def _ema(values, k=None):
    if not values:
        return 0.0
    else:
        if k is None:
            k = float(_config().get('ema') or EMA_K)
        avg = float(values[0])
        for value in values[1:]:
            avg = avg * (1.0 - k) + float(value) * k

        return avg


def _fit(points):
    pts = [(float(x), float(y)) for x, y in points if x is not None and y is not None]
    if len(pts) < 4:
        return
    else:
        n = float(len(pts))
        sx = sum(p[0] for p in pts)
        sy = sum(p[1] for p in pts)
        sxx = sum(p[0] * p[0] for p in pts)
        sxy = sum(p[0] * p[1] for p in pts)
        denom = n * sxx - sx * sx
        if abs(denom) < 1e-06:
            return
        b = (n * sxy - sx * sy) / denom
        a = (sy - b * sx) / n
        if b <= 0:
            return
        return (
         a, b)


def _needFor(percent, line):
    if not line:
        return None
    else:
        a, b = line
        return (float(percent) - a) / b


def _perBattle(target, current, battles, k=None):
    if target is None:
        return
    else:
        if k is None:
            k = float(_config().get('ema') or EMA_K)
        rest = (1.0 - k) ** max(1, int(battles))
        if abs(1.0 - rest) < 1e-06:
            return
        return (float(target) - float(current) * rest) / (1.0 - rest)


def _onResults(isSuccess, results):
    if not isSuccess or not isinstance(results, dict):
        return
    personal = results.get('personal') or {}
    common = results.get('common') or {}
    bonus = int(common.get('bonusType') or 0)
    if bonus not in (1, ):
        return
    for key, rec in personal.items():
        if not isinstance(rec, dict) or 'damageDealt' not in rec:
            continue
        intCD = _safe((lambda : int(key)))
        if not intCD:
            continue
        entry = {'ts': (int(common.get('arenaCreateTime') or 0)), 
           'dmg': (int(rec.get('damageDealt') or 0)), 
           'radio': (int(rec.get('damageAssistedRadio') or 0)), 
           'track': (int(rec.get('damageAssistedTrack') or 0)), 
           'stun': (int(rec.get('damageAssistedStun') or 0)), 
           'rating': (float(rec.get('damageRating') or 0) / 100.0), 
           'marks': (int(rec.get('marksOnGun') or 0))}
        arena = _arena(common.get('arenaTypeID'))
        if arena:
            entry['map'] = arena[0]
            entry['mapName'] = arena[1]
        _state['serverCell'] = dict(entry, cd=int(intCD))
        _safe((lambda : _serverFix(intCD, entry)))
        cell = _state.get('bt') or {}
        if cell:
            _log('measure: ours dmg=%d radio=%d track=%d stun=%d | server dmg=%d radio=%d track=%d stun=%d rating=%.2f marks=%d' % (
             cell.get('dmg') or 0, cell.get('radio') or 0,
             cell.get('track') or 0, cell.get('stun') or 0,
             entry['dmg'], entry['radio'], entry['track'],
             entry['stun'], entry['rating'], entry['marks']))

    _saveHistory()
    _safe(_refresh)
    return


def _arena(arenaTypeID):
    if not arenaTypeID:
        return
    else:

        def read():
            import ArenaType
            arena = ArenaType.g_cache[int(arenaTypeID)]
            geometry = str(getattr(arena, 'geometryName', '') or '')
            if '/' in geometry:
                geometry = geometry.split('/')[-1]
            name = ''
            try:
                name = str(arena.name or '')
            except Exception:
                name = ''

            if name.startswith('#'):
                try:
                    import i18n
                    name = str(i18n.makeString(name))
                except Exception:
                    name = ''

            return (
             geometry, name)

        out = _safe(read)
        if out and out[0]:
            return out
        return


def _serverFix(intCD, server):
    row = _history().get(str(int(intCD)))
    battles = (row or {}).get('battles') or []
    if not battles:
        return False
    else:
        last = battles[-1]
        if last.get('srv'):
            return False
        if abs(float(last.get('rating') or 0) - float(server.get('rating') or 0)) > 0.005:
            return False
        was = int(_value(last))
        for name in ('dmg', 'radio', 'track', 'stun', 'marks'):
            if server.get(name) is not None:
                last[name] = server[name]

        if not last.get('ts') and server.get('ts'):
            last['ts'] = server['ts']
        last['srv'] = 1
        now = int(_value(last))
        if was != now:
            _log('the server corrected the battle on %s: %d -> %d (dmg %d, radio %d, track %d, stun %d)' % (
             row.get('name') or intCD, was, now, last.get('dmg') or 0,
             last.get('radio') or 0, last.get('track') or 0,
             last.get('stun') or 0))
        _safe(_saveHistory)
        _safe(_refresh)
        return True


def _add(intCD, entry):
    hist = _history()
    key = str(intCD)
    row = hist.get(key)
    if row is None:
        vehicle = _vehicleByCD(intCD)
        row = {'name': (_safe((lambda : vehicle.shortUserName)) or key), 'battles': []}
        hist[key] = row
    prev = row['battles'][-1] if row['battles'] else None
    if prev is not None and entry.get('prev') is not None and prev.get('prev') == entry.get('prev') and prev.get('rating') == entry.get('rating'):
        _log('the same battle came twice - the second one is dropped')
        return
    else:
        row['battles'].append(entry)
        ses = _state.setdefault('session', {})
        cell = ses.setdefault(key, {'n': 0, 'd': 0.0})
        cell['n'] += 1
        if prev and prev.get('rating') and entry.get('rating'):
            cell['d'] += float(entry['rating']) - float(prev['rating'])
        if len(row['battles']) > 1000:
            row['battles'] = row['battles'][-1000:]
        _log('battle written: %s value=%d rating=%.2f' % (
         row.get('name'), _value(entry), entry.get('rating') or 0))
        return


def _trimHistory(intCD, stamp):
    try:
        key = str(int(intCD))
        stamp = int(stamp)
    except Exception:
        return

    if stamp <= 0:
        return
    row = _history().get(key)
    if not row:
        return
    kept = [b for b in row.get('battles') or [] if int(b.get('ts') or 0) > stamp]
    gone = len(row.get('battles') or []) - len(kept)
    if gone <= 0:
        return
    _forget(key, [b for b in row.get('battles') or [] if int(b.get('ts') or 0) <= stamp])
    row['battles'] = kept
    _log('%d battles cut from the history of %s' % (
     gone, row.get('name') or key))
    _safe(_saveHistory)
    return


def _trimBelow(intCD, place):
    try:
        key = str(int(intCD))
    except Exception:
        return

    want = _pickedRows(place)
    if not want:
        return
    else:
        place = sorted(want)[0]
        value = want[place]
        row = _history().get(key)
        if not row or place < 0:
            return
        battles = row.get('battles') or []
        if place < len(battles) and value is not None:
            here = int(_value(battles[place]))
            if here != value:
                _log('place %d on %s holds %d, not the %d that was ticked - nothing was cut' % (
                 place, row.get('name') or key, here, value))
                return
        kept = [b for n, b in enumerate(battles) if n > place]
        gone = len(battles) - len(kept)
        if gone <= 0:
            return
        _forget(key, [b for n, b in enumerate(battles) if n <= place])
        row['battles'] = kept
        _log('%d battles cut from %s - everything up to place %d' % (
         gone, row.get('name') or key, place))
        _safe(_saveHistory)
        _safe(_refresh)
        return


def _pickedRows(text):
    want = {}
    for part in str(text or '').split(','):
        part = part.strip()
        if not part:
            continue
        value = None
        if ':' in part:
            part, _sep, tail = part.partition(':')
            value = _int(tail, -1)
            if value < 0:
                value = None
        place = _int(part, -1)
        if place >= 0:
            want[place] = value

    return want


def _dropBattles(intCD, stamps):
    try:
        key = str(int(intCD))
    except Exception:
        return

    want = _pickedRows(stamps)
    if not want:
        _log('nothing to drop: the window sent %r' % (stamps,))
        return
    else:
        row = _history().get(key)
        if not row:
            _log('no history for %s - nothing to drop' % (key,))
            return
        battles = row.get('battles') or []
        name = row.get('name') or key
        drop = set()
        for place, value in want.items():
            if place >= len(battles):
                _log('the window asked for place %d, and %s has %d battles' % (
                 place, name, len(battles)))
                continue
            if value is not None:
                here = int(_value(battles[place]))
                if here != value:
                    _log('place %d on %s holds %d, not the %d that was ticked - left alone' % (
                     place, name, here, value))
                    continue
            drop.add(place)

        if not drop:
            _log('nothing matched on %s - not one battle was removed' % (name,))
            return
        kept = [b for n, b in enumerate(battles) if n not in drop]
        gone = len(battles) - len(kept)
        _forget(key, [b for n, b in enumerate(battles) if n in drop])
        row['battles'] = kept
        _log('%d of the %d battles on %s removed (places %s)' % (
         gone, len(battles), name, sorted(drop)))
        _safe(_saveHistory)
        _safe(_refresh)
        return


def _masteryRows(intCD):
    table = _state.get('masteryTable') or {}
    badge = table.get(int(intCD))
    if not badge:
        return []
    out = []
    for name, _column in MASTERY_COLUMNS:
        value = _int(badge.get(name))
        if value <= 0:
            continue
        out.append({'k': name, 'need': (_num(value)), 'raw': value})

    return out


def _masteryNow(vehicle):
    if vehicle is None:
        return 0
    else:
        dossier = _safe((lambda : _items().getVehicleDossier(int(vehicle.intCD))))
        descr = _safe((lambda : dossier.getDossierDescr()))
        value = _safe((lambda : descr['achievements']['markOfMastery']))
        if value is None:
            value = _safe((lambda : descr.getRecordValue('achievements', 'markOfMastery')))
        if value is None:
            value = _safe((lambda : _items().getAccountDossier().getRandomStats().getMarkOfMasteryForVehicle(int(vehicle.intCD))))
        try:
            return int(value or 0)
        except Exception:
            return 0

        return


def _sessionReset(intCD):
    import time
    now = int(time.time())
    try:
        key = str(int(intCD))
    except Exception:
        key = ''

    ses = _state.setdefault('session', {})
    if key:
        ses.pop(key, None)
    else:
        ses.clear()
    cfg = _config()
    marks = cfg.get('sessionFrom')
    if not isinstance(marks, dict):
        marks = {}
    if key:
        marks[key] = now
    else:
        marks = {}
    cfg['sessionFrom'] = marks
    _ensureDir()
    _safe((lambda : open(CONFIG_FILE, 'wb').write(json.dumps(cfg, indent=4))))
    _log('the session was started again at %d' % (now,))
    _safe(_refresh)
    return


ROMAN = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI', 7: 'VII', 8: 'VIII', 
   9: 'IX', 10: 'X', 11: 'XI'}

def _lang():
    try:
        from helpers import getClientLanguage
        code = str(getClientLanguage() or '').lower().replace('-', '_').split('_')[0].split('.')[0]
        code = {'ua': 'uk', 'cz': 'cs'}.get(code, code)
        if code in ('en', 'ru', 'uk', 'de', 'fr', 'pl', 'cs', 'es', 'it', 'hu', 'tr'):
            return code
        return 'en'
    except Exception:
        return 'en'

    return


def _logRows(battles, limit=40):
    rows = []
    prev = None
    place = -1
    for item in battles:
        place += 1
        value = _value(item)
        rating = float(item.get('rating') or 0)
        before = item.get('prev')
        delta = None
        if before is not None and rating:
            delta = rating - float(before)
        elif prev is not None and rating and item.get('avgPrev'):
            delta = rating - prev
        prev = rating if rating else prev
        rows.append({'v': (_num(value)), 'raw': value, 'r': ('%.2f' % rating if rating else '--'), 
           'rr': rating, 
           'pr': (float(before) if before is not None else 0), 
           'prKnown': (before is not None), 
           'bc': (int(item.get('bc') or 0)), 
           'd': ('%+.2f' % delta if delta is not None else ''), 
           'm': (str(item.get('map') or '')), 
           'ts': (int(item.get('ts') or 0)), 
           'i': place, 
           'mn': (str(item.get('mapName') or ''))})

    rows.reverse()
    return rows[:limit]


def _bestRow(battles):
    best = None
    for item in battles:
        value = _value(item)
        if best is None or value > best[0]:
            best = (
             value, item)

    if best is None:
        return
    else:
        value, item = best
        return {'v': (_num(value)), 'r': ('%.2f' % float(item.get('rating') or 0)), 'map': (str(item.get('map') or '')), 
           'mapName': (str(item.get('mapName') or ''))}


def _curveSlope(points, x):
    if not points or len(points) < 2 or not x:
        return 0.0
    x = float(x)
    first = points[0]
    if x < first[0] and first[0] > 0:
        return first[1] / float(first[0])
    else:
        best = None
        for i in range(len(points) - 1):
            d1, p1 = points[i]
            d2, p2 = points[i + 1]
            if d2 <= d1:
                continue
            step = (p2 - p1) / (d2 - d1)
            if best is None:
                best = step
            if d1 <= x <= d2:
                return step
            if x < d1:
                return step

        return best or 0.0


def _calibration(battles, points=None, total=0):
    here = _curveSlope(points, total)
    battles = list(battles or ())
    if here > 0:
        near = []
        for item in battles:
            was = float(item.get('avgPrev') or 0)
            if was <= 0:
                continue
            there = _curveSlope(points, was)
            if there > 0 and 0.8 <= there / here <= 1.25:
                near.append(item)

        if len(near) >= 3:
            battles = near
        else:
            battles = []
    ks, slopes = [], []
    sumT = sumP = sumV = 0.0
    for item in battles or ():
        before = float(item.get('avgPrev') or 0)
        after = float(item.get('avg') or 0)
        if before <= 0 or after <= 0:
            continue
        value = float(_value(item))
        was = float(item.get('prev') or 0)
        now = float(item.get('rating') or 0)
        recount = was > 0 and now > 0 and (after - before) * (now - was) < 0 and abs(now - was) > 0.05
        if value > 0 and abs(value - before) > 1.0 and not recount:
            ratio = (after - before) / (value - before)
            if 0.005 < ratio < 0.08:
                ks.append(ratio)
                sumT += after - before
                sumV += value - before
        if was > 0 and now > 0 and abs(after - before) > 0.5 and abs(now - was) < 1.5 and not recount:
            step = (now - was) / (after - before)
            if 0.0005 < step < 0.08:
                slopes.append(step)
                sumP += now - was

    def median(values):
        if not values:
            return None
        else:
            values = sorted(values)
            middle = len(values) // 2
            if len(values) % 2:
                return values[middle]
            return (values[middle - 1] + values[middle]) / 2.0

    kOut = median(ks) if len(ks) >= 3 else None
    sOut = median(slopes) if len(slopes) >= 3 else None
    if kOut is None and abs(sumV) > 50 and 0.005 < sumT / sumV < 0.08:
        kOut = sumT / sumV
    if sOut is None and abs(sumT) >= 20 and sumP:
        step = sumP / sumT
        if 0.0005 < step < 0.08:
            sOut = step
    return (
     kOut, sOut, len(ks), len(slopes))


def _dayStart():
    now = _safe((lambda : __import__('time').time())) or 0
    if now <= 0:
        return 0
    day = 86400
    start = int((now - 14400) // day) * day + 14400
    marks = _config().get('sessionFrom')
    if isinstance(marks, dict):
        mark = int(marks.get(str(_state.get('dayFor') or ''), 0) or 0)
    else:
        mark = int(marks or 0)
    if mark > start:
        return mark
    return start


def _percentFor(points, value):
    if not points or value <= 0:
        return 0.0
    curve = list(points)
    if curve[0][0] > 1.0:
        curve = [
         [
          0.0, 0.0]] + curve
    out = _curveAt(curve, float(value))
    if out < 0.0:
        out = 0.0
    elif out > 100.0:
        out = 100.0
    return out


def _sessionCard(battles, points):
    start = _dayStart()
    rows = [b for b in battles or () if int(b.get('ts') or 0) >= start and int(b.get('ts') or 0) > 0]
    if not rows:
        return {'n': 0}
    else:
        cfg = _config()
        total = 0.0
        dmg = 0.0
        assist = 0.0
        for row in rows:
            total += _value(row)
            dmg += float(row.get('dmg') or 0)
            radio = float(row.get('radio') or 0)
            track = float(row.get('track') or 0)
            best = radio if radio >= track else track
            stun = float(row.get('stun') or 0)
            if cfg.get('assistStun') and stun > best:
                best = stun
            assist += best

        count = float(len(rows))
        avg = total / count
        first = rows[0]
        moved = None
        if first.get('prev') is not None and rows[-1].get('rating') is not None:
            moved = float(rows[-1]['rating']) - float(first['prev'])
        return {'n': (len(rows)), 'avg': (_num(int(round(avg)))), 'avgRaw': (int(round(avg))), 'dmg': (_num(int(round(dmg / count)))), 
           'assist': (_num(int(round(assist / count)))), 
           'percent': ('%.2f' % _percentFor(points, avg)), 
           'delta': ('%+.2f' % moved if moved is not None else '')}


def _curvePoints(steps, rating, total):
    points = []
    for step in steps or ():
        need = str(step.get('need') or '').replace(b'\xa0', '').replace(' ', '')
        try:
            need = int(need)
        except Exception:
            continue

        if need > 0:
            points.append([float(need), float(step.get('p') or 0)])

    points.sort()
    out = []
    for point in points:
        if out and abs(point[0] - out[-1][0]) < 1.0:
            continue
        out.append(point)

    return out


def _curveAt(points, x):
    if not points:
        return 0.0
    if len(points) == 1:
        return points[0][1]
    if x <= points[0][0]:
        d1, p1 = points[0]
        if d1 <= 0:
            return 0.0
        return p1 * float(x) / d1
    if x >= points[-1][0]:
        (d1, p1), (d2, p2) = points[-2], points[-1]
        return p2 + (p2 - p1) / (d2 - d1) * (x - d2)
    for i in range(len(points) - 1):
        d1, p1 = points[i]
        d2, p2 = points[i + 1]
        if d1 <= x <= d2 and d2 > d1:
            return p1 + (p2 - p1) / (d2 - d1) * (x - d1)

    return points[-1][1]


def _slopeAt(steps, rating, total):
    points = []
    for step in steps or ():
        need = str(step.get('need') or '').replace(b'\xa0', '').replace(' ', '')
        try:
            need = int(need)
        except Exception:
            continue

        if need > 0:
            points.append((float(need), float(step.get('p') or 0)))

    if total and rating:
        points.append((float(total), float(rating)))
    points.sort()
    if len(points) < 2:
        return 0.0
    else:
        best = None
        for index in range(len(points) - 1):
            left, right = points[index], points[index + 1]
            if left[0] <= total <= right[0]:
                best = (
                 left, right)
                break

        if best is None:
            best = (points[0], points[1]) if total < points[0][0] else (
             points[-2], points[-1])
        (d1, p1), (d2, p2) = best
        if d2 - d1 <= 0:
            return 0.0
        here = (p2 - p1) / (d2 - d1)
        index = points.index(best[0])
        before = None
        after = None
        if index > 0:
            prev = points[index - 1]
            if d1 - prev[0] > 0:
                before = (p1 - prev[1]) / (d1 - prev[0])
        if index + 2 < len(points):
            nxt = points[index + 2]
            if nxt[0] - d2 > 0:
                after = (nxt[1] - p2) / (nxt[0] - d2)
        near = before if total - d1 < d2 - total else after
        if near and near > 0 and here > 0:
            here = 2.0 * here * near / (here + near)
        return here


def _payload():
    vehicle = _currentVehicle()
    if vehicle is None:
        return json.dumps({'ok': False})
    _state['lastVehicle'] = _safe((lambda : vehicle.shortUserName)) or ''
    intCD = _safe((lambda : int(vehicle.intCD))) or 0
    marks, rating = _markData(vehicle)
    battles = _series(intCD)
    values = [_value(b) for b in battles]
    avg = _ema(values)
    account = None
    if not values:
        account = _accountPoint(vehicle)
        if account:
            avg = account['avg']
    cfg = _config()
    points = []
    running = []
    for item in battles:
        running.append(_value(item))
        got = item.get('rating')
        if got:
            points.append((_ema(running), float(got)))

    line = _fit(points)
    exact = _exact(intCD)
    if account is None:
        account = _accountPoint(vehicle)
    total = _movingTotal(vehicle)
    if total:
        avg = total
        if not _state.get('totalLogged'):
            _state['totalLogged'] = True
            _log('moving total from the dossier: %d (percent %.2f)' % (
             total, rating))
    scale = None
    source = ''
    anchor = float(total or 0)
    if anchor <= 0 and account:
        anchor = float(account.get('avg') or 0)
    if anchor > 0 and rating > 0:
        shape = _shapeAt(rating)
        if shape > 0.01:
            scale = anchor / shape
            source = 'shape'
    if exact:
        source = 'exact'
        _safe((lambda : _stepsWatch(intCD, exact)))
    steps = []
    for step in MARK_STEPS:
        need = exact.get(step) if exact else None
        # Missing published regional thresholds remain unavailable.
        guess = 0 if exact and exact.get(step) else 1
        steps.append({'p': step, 'need': (_num(need) if need else '--'), 'g': guess, 
           'done': (1 if rating >= step else 0)})

    goalP = float(cfg.get('goalPercent') or GOAL_PERCENT)
    goalN = int(cfg.get('goalBattles') or GOAL_BATTLES)
    goalTarget = None
    for step in MARK_STEPS:
        if rating < step:
            goalP = step
            goalTarget = (exact or {}).get(step)
            # Do not substitute a shape model for missing regional thresholds.
            break

    goalNeed = _perBattle(goalTarget, total or avg, goalN)
    topNeed = float((exact or {}).get(100.0) or 0)
    # topNeed remains absent when regional data is missing.
    if goalNeed and topNeed and goalNeed > topNeed * 3.0:
        goalNeed = None
    last = battles[-1] if battles else None
    prev = battles[-2] if len(battles) > 1 else None
    delta = None
    if last and prev and last.get('rating') and prev.get('rating'):
        delta = float(last['rating']) - float(prev['rating'])
    ses = _dayMove(battles, intCD)
    nextDone = False
    for step in steps:
        if not step['done'] and not nextDone:
            step['next'] = 1
            nextDone = True
        else:
            step['next'] = 0

    tier = _safe((lambda : int(vehicle.level))) or 0
    if 0 < tier < MIN_TIER:
        if _state.get('tierOff') != intCD:
            _state['tierOff'] = intCD
            _log('tier %d: marks are given from %d up - the panel stays away' % (
             tier, MIN_TIER))
        _state['snapshot'] = {'cd': intCD, 'tier': tier, 'skip': 1}
        return json.dumps({'ok': False})
    else:
        nextNeed = 0
        for step in steps:
            if not step['done']:
                nextNeed = _safe((lambda : int(str(step['need']).replace(b'\xa0', '').replace(' ', '')))) or 0
                break

        kMeasured, slopeMeasured, kN, slopeN = _calibration(battles, _curvePoints(steps, rating, total or avg or 0), total or avg or 0)
        slopeShape = _slopeAt(steps, rating, total or avg or 0)
        if not _state.get('calibLogged'):
            _state['calibLogged'] = True
            _log('calibration: k=%s (%d battles) slope=%s (%d) table slope=%.5f' % (
             kMeasured, kN, slopeMeasured, slopeN, slopeShape))
        slopeUse = slopeMeasured or slopeShape
        slopeOk = 1 if slopeMeasured else 0
        if slopeMeasured and slopeShape > 0:
            if slopeMeasured < slopeShape * 0.4 or slopeMeasured > slopeShape * 2.5:
                _log('the measured slope %.5f is far from the curve %.5f - the curve is used' % (
                 slopeMeasured, slopeShape))
                slopeUse = slopeShape
                slopeOk = 0
        recalcNow = _safe((lambda : _recalcAny(intCD, vehicle, total or avg or 0, rating)))
        _state['snapshot'] = {'cd': intCD, 'curve': (_curvePoints(steps, rating, total or avg or 0)), 
           'slope': slopeUse, 
           'slopeExact': slopeOk, 
           'ema': (kMeasured or float(cfg.get('ema') or EMA_K)), 
           'emaExact': (1 if kMeasured else 0), 
           'rating': rating, 
           'off': (_safe((lambda : float((recalcNow or {}).get('delta') or 0))) or 0.0), 
           'file': ((_safe((lambda : str(vehicle.name))) or '').replace(':', '-')), 
           'battles': (_randomBattles(vehicle)), 
           'young': (1 if int(_randomBattles(vehicle) or 0) <= YOUNG_BATTLES else 0), 
           'table': (1 if source == 'exact' else 0), 
           'percent': ('%.2f' % rating), 
           'marks': marks, 'tier': tier, 
           'total': (int(total or avg or 0)), 
           'next': nextNeed, 'name': (_safe((lambda : vehicle.shortUserName)) or '')}
        return json.dumps({'ok': True, 
           'lang': (_lang()), 
           'cd': (int(intCD)), 
           'pos': (cfg.get('pos')), 
           'winPos': (cfg.get('winPos')), 
           'lookPos': (cfg.get('lookPos')), 
           'name': (_safe((lambda : vehicle.shortUserName)) or ''), 
           'file': ((_safe((lambda : str(vehicle.name))) or '').replace(':', '-')), 
           'nation': (_safe((lambda : str(vehicle.nationName))) or ''), 
           'tier': tier, 
           'tierRoman': (ROMAN.get(tier, '')), 
           'session': {'avg': (ses.get('avg') or ''), 'n': (int(ses.get('n') or 0)), 
                       'delta': ('%+.2f' % float(ses.get('d') or 0.0))}, 
           'recalc': recalcNow, 
           'odds': (_safe((lambda : _battleOdds(_state.get('snapshot') or {})))), 
           'marks': marks, 
           'percent': ('%.2f' % rating), 
           'percentRaw': rating, 
           'avg': (_num(total) if total else '--'), 
           'battles': (len(battles)), 
           'points': (len(points)), 
           'fitted': (1 if line else 0), 
           'source': source,
           'region': _region(),
           'regionalMissing': not bool(exact),
           'predictionEstimated': True, 
           'accountBattles': ((account or {}).get('battles', 0)), 
           'steps': steps, 
           'mastery': (_safe((lambda : _masteryRows(intCD))) or []), 
           'masteryNow': (_safe((lambda : _masteryNow(vehicle))) or 0), 
           'goal': {'p': goalP, 'n': goalN, 'g': (0 if source == 'exact' else 1), 
                    'need': (_num(goalNeed) if goalNeed else '--')}, 
           'look': (_look()), 
           'over': (_safe(_overHangar) or 0), 
           'log': (_logRows(battles)), 
           'best': (_bestRow(battles)), 
           'today': (_sessionCard(battles, _curvePoints(steps, rating, total or avg or 0))), 
           'last': ({'value': (_num(_value(last))), 'rating': ('%.2f' % (last.get('rating') or 0)), 'delta': ('%+.2f' % delta if delta is not None else '')} if last else None)})


CSS_URL = 'coui://gui/gameface/mods/mashka_marks/panel.css'
JS_URL = 'coui://gui/gameface/mods/mashka_marks/panel.js'
PREV_CSS = 'coui://gui/gameface/mods/mashka_marks/preview.css'
PREV_JS = 'coui://gui/gameface/mods/mashka_marks/preview.js'
INJECT_NAME = 'mashkaMarks'

def _panelView():
    cls = _state.get('panelCls')
    if cls is not None:
        return cls
    else:
        from frameworks.wulf import ViewModel
        from gui.impl.pub.view_component import ViewComponent
        from openwg_gameface import gf_mod_inject

        class MarksPanelModel(ViewModel):
            __slots__ = ('onAction', )
            _DATA = 1

            def __init__(self, properties=2, commands=1):
                self.onAction = None
                super(MarksPanelModel, self).__init__(properties=properties, commands=commands)
                return

            def _initialize(self):
                super(MarksPanelModel, self)._initialize()
                gf_mod_inject(self, INJECT_NAME, styles=[PREV_CSS, CSS_URL], modules=[
                 PREV_JS, JS_URL])
                self._addStringProperty('data', '')
                self.onAction = self._addCommand('onAction')
                return

            def setData(self, value):
                self._setString(self._DATA, value)
                return

        class MarksPanelView(ViewComponent):

            def __init__(self, layoutID, model=MarksPanelModel):
                super(MarksPanelView, self).__init__(layoutID=layoutID, model=model)
                return

            def _onLoading(self, *args, **kwargs):
                super(MarksPanelView, self)._onLoading(*args, **kwargs)
                model = self.getViewModel()
                _state['panelModel'] = model
                if model is not None and model.onAction is not None:
                    model.onAction += _onAction
                _log('the panel view is loaded in the hangar')
                _safe(_refresh)
                return

            def _finalize(self):
                model = self.getViewModel()
                if _state.get('panelModel') is model:
                    _state.pop('panelModel', None)
                if model is not None and model.onAction is not None:
                    _safe((lambda : model.onAction.__isub__(_onAction)))
                super(MarksPanelView, self)._finalize()
                return

        _state['panelCls'] = MarksPanelView
        return MarksPanelView


def _escapePressed():
    _state['escAt'] = _safe((lambda : __import__('BigWorld').time())) or 0.0
    if _state.get('escHooked'):
        return

    def hook():
        from helpers import dependency
        from skeletons.gui.impl import IGuiLoader
        manager = dependency.instance(IGuiLoader).windowsManager

        def changed(uid, status):
            now = _safe((lambda : __import__('BigWorld').time())) or 0.0
            if now - float(_state.get('escAt') or 0) > 0.5:
                return
            else:
                window = _safe((lambda : manager.getWindow(uid)))
                if window is None:
                    return
                name = ''
                content = _safe((lambda : window.content))
                if content is not None:
                    name = type(content).__name__.lower()
                if 'menu' not in name:
                    return
                _state['escAt'] = 0.0
                _log('the lobby menu opened on our Esc - closing it (%s)' % name)
                _safe(window.destroy)
                return

        _listen(manager.onWindowStatusChanged, changed, 'lobby')
        _state['escHooked'] = changed
        return True

    if _safe(hook):
        _log('the Esc guard is installed')
    return


def _onAction(*args):
    for arg in args:
        if not isinstance(arg, dict):
            continue
        if arg.get('action') == 'battleMove':
            cfg = _config()
            try:
                cfg['battlePos'] = {'x': (float(arg.get('x') or 0)), 'y': (float(arg.get('y') or 0))}
            except Exception:
                continue

            _ensureDir()
            _safe((lambda : open(CONFIG_FILE, 'wb').write(json.dumps(cfg, indent=4))))
            _log('the battle panel was moved to %s' % (cfg['battlePos'],))
            continue
        if arg.get('action') == 'sound':
            _safe((lambda : _playUI(str(arg.get('name') or 'click'))))
            continue
        if arg.get('action') == 'trimBelow':
            _safe((lambda : _trimBelow(arg.get('cd'), arg.get('ts'))))
            continue
        if arg.get('action') == 'trimList':
            _safe((lambda : _dropBattles(arg.get('cd'), arg.get('ts'))))
            continue
        if arg.get('action') == 'trim':
            _safe((lambda : _trimHistory(arg.get('cd'), arg.get('ts'))))
            continue
        if arg.get('action') == 'sesreset':
            _safe((lambda : _sessionReset(arg.get('cd'))))
            continue
        if arg.get('action') == 'look':
            _safe((lambda : _configSet(str(arg.get('key') or ''), arg.get('value'))))
            continue
        if arg.get('action') == 'dragGrab':
            _safe((lambda : _dragStart(arg.get('x'), arg.get('y'))))
            continue
        if arg.get('action') == 'dragDrop':
            _safe((lambda : _dragDrop(arg.get('x'), arg.get('y'))))
            continue
        if arg.get('action') == 'escape':
            _safe(_escapePressed)
            continue
        if arg.get('action') == 'lookmove':
            cfg = _config()
            try:
                cfg['lookPos'] = {'x': (float(arg.get('x') or 0)), 'y': (float(arg.get('y') or 0))}
            except Exception:
                continue

            _ensureDir()
            _safe((lambda : open(CONFIG_FILE, 'wb').write(json.dumps(cfg, indent=4))))
            continue
        if arg.get('action') in ('move', 'winmove'):
            cfg = _config()
            key = 'pos' if arg.get('action') == 'move' else 'winPos'
            try:
                cfg[key] = {'x': (float(arg.get('x') or 0)), 'y': (float(arg.get('y') or 0))}
            except Exception:
                continue

            _ensureDir()
            _safe((lambda : open(CONFIG_FILE, 'wb').write(json.dumps(cfg, indent=4))))
            _log('%s moved to %s' % (key, cfg[key]))
            continue

    return


def getStateMachineRegistrators():
    return (
     _lobbyEarly, _lobbyStates)


def _lobbyEarly(machine, *args, **kwargs):
    return


def getViewSettings():
    return ()


def getContextMenuHandlers():
    return ()


def getBusinessHandlers():
    return ()


def _lobbyPackage():
    if _state.get('lobbyPackage'):
        return
    from gui.shared.system_factory import registerScaleformLobbyPackages
    registerScaleformLobbyPackages((__name__,))
    _state['lobbyPackage'] = 1
    _log('registered %s as a lobby package' % (__name__,))
    return


def _lobbyStates(machine, *args, **kwargs):
    try:
        _state['lobbyMachine'] = machine
        _log('the lobby machine is here')
    except Exception:
        pass

    return


_SCREENS = (
 'loadout', 'allvehicles', 'equipment', 'shells', 'consumable',
 'instruction', 'directive', 'tankequip', 'ammunition',
 'playlist', 'crewbook', 'storage', 'barracks')

def _lobbyAway():
    machine = _state.get('lobbyMachine')
    if machine is None:
        return
    else:
        state = _safe((lambda : machine.visibleState))
        name = _safe((lambda : state.__class__.__name__)) or ''
        low = name.lower()
        if low != _state.get('overSaidName'):
            _state['overSaidName'] = low
            _safe((lambda : _log('the lobby shows %s' % (name or '?',))))
        if not low:
            return 0
        for mark in _SCREENS:
            if mark in low:
                return 1

        return 0


def _overHangar():
    told = _safe(_lobbyAway)
    if told is None:
        return 0
    else:
        if _config().get('hideOnSubView') is False:
            return 0
        return told


def _mountPanel():
    if _state.get('mounted'):
        return True
    else:
        resID = _resourceID()
        if resID is None:
            return False
        from gui.shared.system_factory import registerDynamicRandomHangarPresenters

        def build():
            view = _safe((lambda : _panelView()(resID)))
            if view is None:
                from gui.impl.pub.view_component import ViewComponent
                view = ViewComponent(layoutID=resID, enabled=False)
            return view

        registerDynamicRandomHangarPresenters(resID, build)
        _state['mounted'] = True
        _log('the panel is registered as a child of the hangar (layout %s)' % (
         resID,))
        return True


def _resourceID():
    if _state.get('resID'):
        return _state['resID']
    found = _resourceIDLook()
    if found:
        _state['resID'] = found
    return found


def _nativeResID(node):
    from gui.impl.gen import R
    step = R
    for name in node:
        nxt = getattr(step, name, None)
        if nxt is None:
            nxt = _safe((lambda step=step, name=name: step.dyn(name)))
        if nxt is None:
            return
        step = nxt

    resID = _safe((lambda : step()))
    try:
        resID = int(resID)
    except Exception:
        return

    return resID or None


def openwgResID(key):
    import openwg_gameface
    return int(openwg_gameface.res_id_by_key(key) or 0) or None


def _clientVersion():
    if 'version' in _state:
        return _state['version']
    else:
        import re
        text = ''
        for get in ((lambda : __import__('BigWorld').wg_getClientVersionShort()),
         (lambda : open('./version.xml', 'rb').read())):
            text = _safe(get) or ''
            if text:
                break

        found = _safe((lambda : re.search('(\\d+(?:\\.\\d+)+)', str(text))))
        version = found.group(1) if found else None
        _state['version'] = version
        return version


def _resMapPath():
    version = _clientVersion()
    if not version:
        return
    else:
        path = RES_MAP_PATH % (version,)
        if os.path.isfile(path):
            return path
        return


def _resourceIDLook():
    resID = _safe((lambda : _nativeResID(RES_NODE)))
    if resID:
        _log('layout id %s from R.%s' % (resID, ('.').join(RES_NODE)))
        return resID
    else:
        resID = _safe((lambda : openwgResID(RES_KEY)))
        if resID:
            _log('layout id %s from the key %s' % (resID, RES_KEY))
            return resID
        path = _resMapPath()
        if path:
            data = _safe((lambda : json.loads(open(path, 'rb').read()))) or {}
            for key, item in data.items():
                if isinstance(item, dict) and item.get('path') == LAYOUT_PATH:
                    _log('layout id %s from %s' % (int(key, 16), path))
                    return int(key, 16)

        _log('no layout id anywhere: not on R.%s, not from the key %s, and no res_map.json with %s - the panel cannot be drawn' % (
         ('.').join(RES_NODE), RES_KEY, LAYOUT_PATH))
        return


def _refresh(*_a):
    model = _state.get('panelModel')
    if model is None:
        return
    else:
        data = _safe(_payload)
        if data is None:
            return
        _safe((lambda : model.setData(data)))
        _state['shownCD'] = int((_state.get('snapshot') or {}).get('cd') or 0)
        return


def _panelWatch():

    def run():
        import BigWorld
        if _state.get('panelModel') is not None:
            vehicle = _currentVehicle()
            cd = _safe((lambda : int(vehicle.intCD))) if vehicle else 0
            if cd and int(_state.get('shownCD') or 0) != int(cd):
                _log('the panel shows %s while the hangar has %d - redrawing' % (
                 _state.get('shownCD'), cd))
                _safe(_refresh)
            now = _safe(_overHangar) or 0
            if now != _state.get('overNow'):
                _state['overNow'] = now
                _log('a screen over the hangar: %s%s' % (
                 'yes' if now else 'no',
                 ' (%s)' % _state.get('overWhy') if now else ''))
                _safe(_refresh)
        _schedule(0.5, _panelWatch, 'lobby')
        return

    _safe(run)
    return


def _tableTick():
    _safe(_table)
    _safe((lambda : _schedule(600.0, _tableTick, 'lobby')))
    return


def _onLobby(*_a):
    if _state.get('battleActive'):
        _onBattleEnd()
    if _state.get('inLobby'):
        return
    _state['inLobby'] = True
    from PlayerEvents import g_playerEvents
    from CurrentVehicle import g_currentVehicle
    if not _state.get('resultsHooked'):
        _state['resultsHooked'] = True
        _listen(g_playerEvents.onBattleResultsReceived, _onResults)
    _listen(g_currentVehicle.onChanged, _refresh, 'lobby')
    _safe(_watchSync)
    _safe(_importOld)
    _safe(_pendingLoad)
    _safe(_mountPanel)
    _safe(_afterSync)
    if not _state.get('sweptGarage'):
        _state['sweptGarage'] = True
        tries = (8.0, 20.0, 45.0, 90.0, 180.0)
        for delay in tries:
            last = 1 if delay == tries[-1] else 0
            _safe((lambda d=delay, f=last: _schedule(d, (lambda : _safe((lambda : _sweepAgain(f)))), 'lobby')))

    for delay in (4.0, 12.0):
        _safe((lambda delay=delay: _schedule(delay, (lambda : _safe(_afterSync)), 'lobby')))

    if not _state.get('watchers'):
        _state['watchers'] = True
        _safe(_panelWatch)
        _safe(_tableTick)
    _log('installed %s (history: %d vehicles; panel: %s)' % (
     VERSION, len(_history()),
     'on' if _config().get('panel', True) else 'off - battles are written down only'))
    return


def _onLobbyLeft(*_a):
    if not _state.get('inLobby'):
        return
    _safe(_payload)
    _state['inLobby'] = False
    _clearScope('lobby')
    for key in ('watchers', 'escHooked', 'sweptGarage'):
        _state.pop(key, None)
    from PlayerEvents import g_playerEvents
    from CurrentVehicle import g_currentVehicle

    def drop(event, fn):
        try:
            if fn in event:
                event.remove(fn)
        except Exception:
            pass

        return

    # Subscription removed by _clearScope above.
    return


def _battleReset():
    _state['bt'] = {'dmg': 0, 'radio': 0, 'track': 0, 'stun': 0, 'blocked': 0, 
       'shots': 0, 'last': 0.0, 'name': '', 'id': (int((_safe((lambda : __import__('time').time())) or 0) * 1000))}
    _state['ctrl'] = 0
    _state['alt'] = 0
    return


def _battleAdd(kind, value):
    cell = _state.get('bt')
    if cell is None:
        _battleReset()
        cell = _state['bt']
    try:
        cell[kind] = int(cell.get(kind) or 0) + int(value or 0)
    except Exception:
        return

    _safe(_battlePush)
    now = _safe((lambda : __import__('BigWorld').time())) or 0.0
    if now - float(cell.get('last') or 0) < 10.0:
        return
    else:
        cell['last'] = now
        _safe(_battlePush)
        _safe(_pendingSave)
        _log('battle %s: dmg=%d radio=%d track=%d stun=%d blocked=%d' % (
         cell.get('name') or '?', cell.get('dmg') or 0,
         cell.get('radio') or 0, cell.get('track') or 0,
         cell.get('stun') or 0, cell.get('blocked') or 0))
        return


def _feedbackMap():
    cached = _state.get('feMap')
    if cached is not None:
        return cached
    else:
        out = {}

        def build():
            from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID
            pairs = (
             ('PLAYER_DAMAGED_HP_ENEMY', 'dmg'),
             ('PLAYER_ASSIST_TO_KILL_ENEMY', 'radio'),
             ('PLAYER_ASSIST_TO_STUN_ENEMY', 'stun'),
             ('DAMAGE_BLOCKED_BY_PLAYER', 'blocked'))
            for name, key in pairs:
                value = getattr(FEEDBACK_EVENT_ID, name, None)
                if value is not None:
                    out[value] = key

            return True

        _safe(build)
        _state['feMap'] = out
        return out


def _summaryID():
    if 'sumID' in _state:
        return _state['sumID']

    def ask():
        from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID
        return getattr(FEEDBACK_EVENT_ID, 'DAMAGE_LOG_SUMMARY', None)

    got = _safe(ask)
    _state['sumID'] = got
    return got


_SUM_RADIO = '_BattleSummaryFeedbackEvent__radioAssistDamage'
_SUM_TRACK = '_BattleSummaryFeedbackEvent__trackAssistDamage'

def _takeSummary(event):
    cell = _state.get('bt')
    if cell is None:
        return False
    radio = _safe((lambda : int(getattr(event, _SUM_RADIO) or 0)))
    track = _safe((lambda : int(getattr(event, _SUM_TRACK) or 0)))
    if radio is None and track is None:
        return False
    else:
        dmg = _safe((lambda : int(event.getTotalDamage() or 0)))
        stun = _safe((lambda : int(event.getTotalStunDamage() or 0)))
        blocked = _safe((lambda : int(event.getTotalBlockedDamage() or 0)))
        if dmg is not None:
            cell['dmg'] = dmg
        cell['radio'] = int(radio or 0)
        cell['track'] = int(track or 0)
        if stun is not None:
            cell['stun'] = stun
        if blocked is not None:
            cell['blocked'] = blocked
        if not cell.get('exact'):
            cell['exact'] = 1
            _log('assistance is taken apart by the client: radio and track are counted separately from now on')
        _safe(_battlePush)
        return True


def _assistKinds():
    if 'assistKinds' in _state:
        return _state['assistKinds']

    def ask():
        from BattleFeedbackCommon import BATTLE_EVENT_TYPE as B
        out = {}
        for name, key in (('RADIO_ASSIST', 'radio'),
         ('TRACK_ASSIST', 'track'),
         ('STUN_ASSIST', 'stun'),
         ('SMOKE_ASSIST', 'radio'),
         ('INSPIRE_ASSIST', 'radio')):
            got = getattr(B, name, None)
            if got is not None:
                out[int(got)] = key

        return out

    got = _safe(ask) or {}
    _state['assistKinds'] = got
    if not got:
        _log('the client does not name the kinds of assistance: spotting and tracking will be counted together')
    return got


def _onSummary(event):
    if _state.get('battleActive'):
        _safe(lambda: _takeSummary(event))


def _onFeedback(events):
    if not _state.get('battleActive'):
        return

    def handle():
        table = _feedbackMap()
        for event in events or ():
            etype = _safe((lambda : event.getType()))
            if not table:
                continue
            if (_state.get('bt') or {}).get('exact'):
                continue
            key = table.get(etype)
            if key is None:
                continue
            if key == 'radio':
                kinds = _assistKinds()
                if kinds:
                    kind = kinds.get(_safe((lambda : int(event.getBattleEventType()))))
                    if kind:
                        key = kind
            extra = _safe((lambda : event.getExtra()))
            if extra is None:
                continue
            if _safe((lambda : extra.isNone())):
                continue
            damage = _safe((lambda : int(extra.getDamage() or 0))) or 0
            if damage:
                _battleAdd(key, damage)

        return True

    _safe(handle)
    return


def _guiEvents():

    def ask():
        from gui.shared import events
        out = []
        for name in ('GUI_VISIBILITY', 'FULL_STATS', 'EVENT_STATS', 'FULL_STATS_QUEST_PROGRESS',
                     'FULL_STATS_PERSONAL_RESERVES', 'HIDE_EXTERNAL_COMPONENTS',
                     'SHOW_EXTERNAL_COMPONENTS', 'GO_TO_PREBATTLE_HIGHLIGHTS', 'RETURN_FROM_PREBATTLE_HIGHLIGHTS'):
            got = getattr(events.GameEvent, name, None)
            if got is not None:
                out.append((name, got))

        return out

    return _safe(ask) or []


def _onGuiEvent(name, event):
    ctx = _safe((lambda : dict(event.ctx or {}))) or {}
    if name in ('HIDE_EXTERNAL_COMPONENTS', 'GO_TO_PREBATTLE_HIGHLIGHTS'):
        hide = True
    elif name in ('SHOW_EXTERNAL_COMPONENTS', 'RETURN_FROM_PREBATTLE_HIGHLIGHTS'):
        hide = False
    elif name in ('FULL_STATS', 'EVENT_STATS', 'FULL_STATS_QUEST_PROGRESS', 'FULL_STATS_PERSONAL_RESERVES'):
        hide = bool(ctx.get('isDown', ctx.get('visible', True)))
    else:
        hide = not bool(ctx.get('visible', True))
    if bool(_state.get('guiHidden')) == bool(hide):
        return
    _state['guiHidden'] = bool(hide)
    _safe(_battlePush)
    return


def _killCamCtrl():

    def run():
        from helpers import dependency
        from skeletons.gui.battle_session import IBattleSessionProvider
        return dependency.instance(IBattleSessionProvider).shared.killCamCtrl

    return _safe(run)


def _killCamOn():
    ctrl = _killCamCtrl()
    if ctrl is None:
        return False
    else:
        return bool(_safe((lambda : getattr(ctrl, '_KillCameraController__isKillCamActive', False))))


def _killCamWatch():
    if _state.get('killCamHooked'):
        return True
    else:
        ctrl = _killCamCtrl()
        if ctrl is None:
            return False

        def changed(*_a, **_kw):
            _safe(_battlePush)
            return

        def subscribe():
            _listen(ctrl.onKillCamModeStateChanged, changed, 'battle')
            _listen(ctrl.onKillCamInterrupted, changed, 'battle')
            return True

        if not _safe(subscribe):
            return False
        _state['killCamHooked'] = True
        _log('the kill camera is being watched')
        return True


def _highlightsOn():

    def run():
        from helpers import dependency
        from skeletons.gui.battle_session import IBattleSessionProvider
        session = dependency.instance(IBattleSessionProvider)
        ctrl = session.dynamic.prebattleHighlightsController
        if ctrl is None:
            return False
        else:
            return bool(ctrl.displayingHighlights)

    return bool(_safe(run))


def _guiWatch(on):
    pairs = _guiEvents()
    if not pairs:
        return

    def run():
        from gui.shared import g_eventBus, EVENT_BUS_SCOPE
        handlers = _state.get('guiHandlers')
        if on:
            if handlers is not None:
                return True
            handlers = {}
            for name, eid in pairs:

                def make(name=name):
                    return (lambda event: _safe((lambda : _onGuiEvent(name, event))))

                handlers[name] = make()
                g_eventBus.addListener(eid, handlers[name], EVENT_BUS_SCOPE.BATTLE)

            _state['guiHandlers'] = handlers
            return True
        else:
            if handlers is None:
                return True
            for name, eid in pairs:
                if name in handlers:
                    _safe((lambda eid=eid, name=name: g_eventBus.removeListener(eid, handlers[name], EVENT_BUS_SCOPE.BATTLE)))

            _state.pop('guiHandlers', None)
            return True

    _safe(run)
    return


def _battleIsRandom():

    def run():
        import BigWorld
        from constants import ARENA_BONUS_TYPE
        bonus = int(BigWorld.player().arena.bonusType)
        return bonus == int(ARENA_BONUS_TYPE.REGULAR)

    got = _safe(run)
    if got is None:
        return True
    else:
        return bool(got)


def _onBattleStart(*_a):
    if _state.get('battleActive'):
        return
    _clearScope('battle')
    _state['battleActive'] = True
    _battleReset()
    _state['guiHidden'] = False
    if not _battleIsRandom():
        _state['bt']['skip'] = True
        _log('not a random battle - the panel stays away')
        return
    else:

        def arena():
            import BigWorld
            return _arena(BigWorld.player().arenaTypeID)

        got = _safe(arena)
        if got:
            _state['bt']['map'] = got[0]
            _state['bt']['mapName'] = got[1]
        _safe(_pendingSave)
        _state['bt']['name'] = _state.get('lastVehicle') or ''
        snap = _state.get('snapshot')
        if snap:
            _state['bt']['snap'] = dict(snap)
        _state.pop('plateSaid', None)
        _log('battle started on %s: moving total %d, recount carried in %+.2f' % (
         _state['bt'].get('name') or '?',
         int((snap or {}).get('total') or 0),
         float((snap or {}).get('off') or 0)))

        def attach():
            from helpers import dependency
            from skeletons.gui.battle_session import IBattleSessionProvider
            session = dependency.instance(IBattleSessionProvider)
            feedback = session.shared.feedback
            _listen(feedback.onPlayerFeedbackReceived, _onFeedback, 'battle')
            _listen(feedback.onPlayerSummaryFeedbackReceived, _onSummary, 'battle')
            _state['feedback'] = feedback
            return True

        if not _safe(attach):
            _log('the battle feedback could not be reached - nothing is written')
        _safe(_battleKeys)
        _safe(_killCamWatch)
        _safe(_battleOpen)
        return


def _onBattleEnd(*_a):
    _state['battleActive'] = False
    _clearScope('battle')
    _state.pop('keysHooked', None)
    _state.pop('killCamHooked', None)
    _safe(_battleClose)
    _safe((lambda : _pendingPark(_state.get('bt'), _state.get('snapshot'))))
    _state.pop('bt', None)
    _state.pop('feedback', None)
    cell = _state.get('bt')
    if cell:
        _log('battle over: dmg=%d radio=%d track=%d stun=%d blocked=%d' % (
         cell.get('dmg') or 0, cell.get('radio') or 0,
         cell.get('track') or 0, cell.get('stun') or 0,
         cell.get('blocked') or 0))
    return


def _battleResID():
    if _state.get('battleResID'):
        return _state['battleResID']
    else:
        resID = _safe((lambda : _nativeResID(BATTLE_NODE)))
        if resID:
            _log('battle layout id %s from R.%s' % (
             resID, ('.').join(BATTLE_NODE)))
            _state['battleResID'] = resID
            return resID
        resID = _safe((lambda : openwgResID(BATTLE_KEY)))
        if resID:
            _log('battle layout id %s from the key %s' % (resID, BATTLE_KEY))
            _state['battleResID'] = resID
            return resID
        path = _resMapPath()
        if path:
            data = _safe((lambda : json.loads(open(path, 'rb').read()))) or {}
            for key, item in data.items():
                if isinstance(item, dict) and item.get('path') == BATTLE_LAYOUT_PATH:
                    resID = int(key, 16)
                    _log('battle layout id %s from %s' % (resID, path))
                    _state['battleResID'] = resID
                    return resID

        _log('no battle layout id: neither on R.%s nor from the key %s nor in the res_map of this client' % (
         ('.').join(BATTLE_NODE), BATTLE_KEY))
        return


def _battleViewClass():
    cls = _state.get('battleCls')
    if cls is not None:
        return cls
    else:
        from frameworks.wulf import ViewSettings, ViewFlags, ViewModel
        from gui.impl.pub import ViewImpl

        class MarksBattleModel(ViewModel):
            __slots__ = ('onAction', )

            def __init__(self, properties=1, commands=1):
                self.onAction = None
                super(MarksBattleModel, self).__init__(properties=properties, commands=commands)
                return

            def _initialize(self):
                super(MarksBattleModel, self)._initialize()
                self._addStringProperty('data', '')
                self.onAction = self._addCommand('onAction')
                return

            def setData(self, text):
                self._setString(0, text)
                return

        class MarksBattleView(ViewImpl):
            __slots__ = ()

            def __init__(self, layoutID):
                settings = ViewSettings(layoutID)
                want = str(_config().get('battleViewFlags') or 'VIEW')
                settings.flags = getattr(ViewFlags, want, ViewFlags.VIEW)
                settings.model = MarksBattleModel()
                super(MarksBattleView, self).__init__(settings)
                return

            @property
            def viewModel(self):
                return super(MarksBattleView, self).getViewModel()

            def _onLoading(self, *args, **kwargs):
                super(MarksBattleView, self)._onLoading(*args, **kwargs)
                model = self.viewModel
                _state['battleModel'] = model
                if model is not None and model.onAction is not None:
                    model.onAction += _onAction
                _safe(_battlePush)
                return

            def _finalize(self):
                model = self.viewModel
                if model is not None and model.onAction is not None:
                    _safe(lambda: model.onAction.__isub__(_onAction))
                if _state.get('battleModel') is model:
                    _state['battleModel'] = None
                super(MarksBattleView, self)._finalize()
                return

        _state['battleCls'] = MarksBattleView
        return MarksBattleView


def _battleKeys():
    if _state.get('keysHooked'):
        return True
    import Keys
    from Avatar import PlayerAvatar
    original = PlayerAvatar.handleKey
    active = [True]

    def handleKey(self, isDown, key, mods, *args, **kwargs):
        if not active[0]:
            return original(self, isDown, key, mods, *args, **kwargs)
        if key in (Keys.KEY_LALT, Keys.KEY_RALT):
            want = 1 if isDown else 0
            if int(_state.get('alt') or 0) != want:
                _state['alt'] = want
                _safe(_battlePush)
        if key in (Keys.KEY_LCONTROL, Keys.KEY_RCONTROL):
            want = 1 if isDown else 0
            if int(_state.get('ctrl') or 0) != want:
                _state['ctrl'] = want
                _safe(_battlePush)
        return original(self, isDown, key, mods, *args, **kwargs)

    PlayerAvatar.handleKey = handleKey
    _hooks.append((PlayerAvatar, 'handleKey', original, handleKey, 'battle', active))
    _state['keysHooked'] = True
    return True


def _battleOpen():
    if _state.get('battleWindow') is not None:
        return
    else:
        if not _config().get('battlePanel', True):
            return
        resID = _battleResID()
        if not resID:
            _log('the battle layout is not registered - no panel in battle')
            return

        def build():
            from frameworks.wulf import WindowFlags, WindowLayer
            from gui.impl.pub.window_impl import WindowImpl
            cfg = _config()
            want = str(cfg.get('battleLayer') or 'WINDOW')
            layer = getattr(WindowLayer, want, None)
            if layer is None:
                layer = WindowLayer.WINDOW
            parent = None

            def mainWindow():
                from helpers import dependency
                from skeletons.gui.impl import IGuiLoader
                return dependency.instance(IGuiLoader).windowsManager.getMainWindow()

            parent = _safe(mainWindow)
            flags = WindowFlags.WINDOW
            if _config().get('battleFullscreen', False):
                flags = flags | WindowFlags.WINDOW_FULLSCREEN
            view = _battleViewClass()(resID)

            class MarksBattleWindow(WindowImpl):
                __slots__ = ()

                def _onReady(self):
                    _safe((lambda : self.show(False)))
                    _log('battle window ready')
                    _safe((lambda : _battlePlace(self)))
                    return

            window = _safe((lambda : MarksBattleWindow(wndFlags=flags, content=view, parent=parent, layer=layer, name='mashkaMarksBattle')))
            if window is None:
                window = MarksBattleWindow(wndFlags=flags, content=view, parent=parent, layer=layer)
            _listen(window.onSizeChanged, lambda *_a: _safe(lambda: _battlePlace(window)), 'battle')
            window.load()
            names = {}
            try:
                from frameworks.wulf import WindowStatus
                for name in dir(WindowStatus):
                    if name.isupper():
                        names[int(getattr(WindowStatus, name))] = name

            except Exception:
                names = {}

            _log('battle window: layer=%s parent=%s status=%s %s' % (
             want, 'main' if parent is not None else 'none',
             _safe((lambda : int(window.windowStatus))), names))
            return window

        window = _safe(build)
        if window is None:
            _log('the battle panel could not be opened')
            return
        _state['battleWindow'] = window

        def late():
            if _state.get('battleWindow') is not window:
                return
            _safe((lambda : window.show(False)))
            _safe((lambda : _battlePlace(window)))
            _log('battle panel after two seconds: status=%s' % (
             _safe((lambda : int(window.windowStatus))),))
            return

        _safe((lambda : _schedule(2.0, (lambda : _safe(late)), 'battle')))
        if not _config().get('battleFullscreen', False):
            _safe((lambda : _battlePlace(window)))
            for delay in (1.0, 3.0):
                _safe((lambda d=delay: _schedule(d, (lambda : _safe((lambda : _battlePlace(_state.get('battleWindow'))))), 'battle')))

        _guiWatch(True)
        _log('the battle panel is open (%s, status=%s)' % (
         type(window).__name__, _safe((lambda : int(window.windowStatus)))))
        return


def _battlePlace(window):
    if window is None:
        return
    else:
        if _state.get('drag') is not None:
            return

        def run():
            from helpers import dependency
            from skeletons.gui.impl import IGuiLoader
            main = dependency.instance(IGuiLoader).windowsManager.getMainWindow()
            if main is None:
                return
            else:
                width, height = window.size
                screenW, screenH = main.size
                width = int(width or 0)
                height = int(height or 0)
                screenW = int(screenW or 0)
                screenH = int(screenH or 0)
                if width <= 0 or height <= 0 or screenW <= 0 or screenH <= 0:
                    if _state.get('placeWait') != (width, height, screenW, screenH):
                        _state['placeWait'] = (
                         width, height, screenW, screenH)
                        _log('the battle panel has no size yet: %dx%d on %dx%d' % (
                         width, height, screenW, screenH))
                    return
                cfg = _config()
                pos = cfg.get('battlePos') or {'x': 0.015, 'y': 0.42}
                x = int(float(pos.get('x') or 0) * screenW)
                y = int(float(pos.get('y') or 0) * screenH)
                x = max(-24, min(max(0, screenW - 60), x))
                y = max(-140, min(max(0, screenH - 60), y))
                if _state.get('placed') == (x, y, width, height):
                    return
                _state['placed'] = (
                 x, y, width, height)
                window.move(x, y)
                _log('the battle panel %dx%d is placed at %d,%d of %dx%d' % (
                 width, height, x, y, screenW, screenH))
                return True

        _safe(run)
        return


def _cursorPos():

    def run():
        import GUI
        from helpers import dependency
        from skeletons.gui.impl import IGuiLoader
        main = dependency.instance(IGuiLoader).windowsManager.getMainWindow()
        width, height = main.size
        width = int(width or 0) or 1920
        height = int(height or 0) or 1080
        point = GUI.mcursor().position
        x = (float(point.x) + 1.0) / 2.0 * width
        y = (1.0 - float(point.y)) / 2.0 * height
        return (int(x), int(y), width, height)

    return _safe(run)


def _dragDrop(left, top):
    _state.pop('drag', None)
    width, height = _mainSize()
    if width <= 0 or height <= 0:
        return
    try:
        x = int(left or 0)
        y = int(top or 0)
    except Exception:
        return

    cfg = _config()
    cfg['battlePos'] = {'x': (float(x) / float(width)), 'y': (float(y) / float(height))}
    _state.pop('placed', None)
    _ensureDir()
    _safe((lambda : open(CONFIG_FILE, 'wb').write(json.dumps(cfg, indent=4))))
    _log('the battle panel was moved to %s' % (cfg['battlePos'],))
    _safe((lambda : _battlePlace(_state.get('battleWindow'))))
    _safe(_battlePush)
    return


def _dragStart(grabX, grabY):
    window = _state.get('battleWindow')
    if window is None:
        return
    else:
        here = _cursorPos()
        if here is None:
            return
        _state['drag'] = {'dx': (int(grabX or 0)), 'dy': (int(grabY or 0)), 'n': 0}
        _dragStep()
        return


def _dragStep():
    cell = _state.get('drag')
    window = _state.get('battleWindow')
    if cell is None or window is None:
        return
    cell['n'] = int(cell.get('n') or 0) + 1
    if cell['n'] > 20000:
        _dragEnd()
        return
    else:
        held = _safe((lambda : __import__('BigWorld').isKeyDown(__import__('Keys').KEY_LEFTMOUSE)))
        if held is False:
            _dragEnd()
            return
        here = _cursorPos()
        if here is not None:
            x, y, width, height = here
            left = max(0, min(width - 1, x - int(cell.get('dx') or 0)))
            top = max(0, min(height - 1, y - int(cell.get('dy') or 0)))
            cell['pos'] = (left, top, width, height)
            _safe((lambda : window.move(left, top)))
        _safe((lambda : _schedule(0.0, _dragStep, 'battle')))
        return


def _dragEnd():
    cell = _state.pop('drag', None)
    _state['dragOff'] = int(_state.get('dragOff') or 0) + 1
    _safe(_battlePush)
    if not cell or not cell.get('pos'):
        return
    left, top, width, height = cell['pos']
    cfg = _config()
    cfg['battlePos'] = {'x': (float(left) / float(width or 1)), 'y': (float(top) / float(height or 1))}
    size = _safe((lambda : _state.get('battleWindow').size)) or (0, 0)
    _state['placed'] = (int(left), int(top), int(size[0]), int(size[1]))
    _ensureDir()
    _safe((lambda : open(CONFIG_FILE, 'wb').write(json.dumps(cfg, indent=4))))
    _log('the battle panel was moved to %s' % (cfg['battlePos'],))
    _safe(_battlePush)
    return


def _battleClose():
    _guiWatch(False)
    _state['guiHidden'] = False
    _state.pop('drag', None)
    _state.pop('placed', None)
    _state.pop('placeWait', None)
    window = _state.pop('battleWindow', None)
    _state['battleModel'] = None
    if window is not None:
        _safe(window.destroy)
    return


def _slopeNow(snap):
    slope = float(snap.get('slope') or 0)
    if snap.get('slopeExact') and slope > 0:
        return slope
    return 0.0


def _movedNow(snap, value):
    if not snap:
        return 0
    total = float(snap.get('total') or 0)
    k = float(snap.get('ema') or EMA_K)
    return int(round(total + k * (float(value) - total)))


def _forecast(snap, value):
    if not snap:
        return 0.0
    total = float(snap.get('total') or 0)
    moved = float(_movedNow(snap, value))
    points = snap.get('curve') or []
    slope = _slopeNow(snap)
    if slope > 0:
        gain = slope * (moved - total)
    elif points:
        gain = _curveAt(points, moved) - _curveAt(points, total)
    else:
        gain = float(snap.get('slope') or 0) * (moved - total)
    limit = 100.0
    if total > 0 and total >= float(value or 0) * 0.5:
        limit = 6.0
    if gain > limit:
        gain = limit
    elif gain < -limit:
        gain = -limit
    gain += float(snap.get('off') or 0.0)
    if gain > 30.0:
        gain = 30.0
    elif gain < -30.0:
        gain = -30.0
    return round(gain, 2)


def _nextWhole(snap, value):
    import math
    rating = float(snap.get('rating') or 0)
    target = math.floor(rating) + 1.0
    if target > 100.0:
        target = 100.0
    return target


def _needThisBattle(snap, target):
    points = snap.get('curve') or []
    total = float(snap.get('total') or 0)
    k = float(snap.get('ema') or EMA_K)
    if k <= 0:
        return 0
    else:
        slope = _slopeNow(snap)
        if slope > 0:
            rating = float(snap.get('rating') or 0)
            want = total + (float(target) - rating) / slope
            need = total + (want - total) / k
            if 0.0 < need <= _ceiling(points, total):
                return int(round(need))
            return 0
        if not points:
            return 0
        want = None
        for index in range(len(points) - 1):
            d1, p1 = points[index]
            d2, p2 = points[index + 1]
            if p2 == p1:
                continue
            if p1 <= target <= p2 or index == 0 and target < p1 or index == len(points) - 2 and target > p2:
                want = d1 + (d2 - d1) * (target - p1) / (p2 - p1)
                break

        if want is None:
            return 0
        need = total + (want - total) / k
        if 0.0 < need <= _ceiling(points, total):
            return int(round(need))
        return 0


def _ceiling(points, total):
    top = 0.0
    if points:
        top = float(points[-1][0] or 0)
    if top <= 0:
        top = float(total or 0) * 2.0
    return top * 3.0


def _plateSaid(snap, value):
    gain = _forecast(snap, value)
    said = _state.get('plateSaid')
    show = False
    if said is None:
        show = True
    elif (said >= 0) != (gain >= 0):
        show = True
    elif abs(gain - said) >= 0.5:
        show = True
    if show:
        _state['plateSaid'] = gain
        _log('the plate on %s: damage %d, total %d, recount %+.2f, slope %.5f, k %.4f -> forecast %+.2f' % (
         snap.get('name') or snap.get('cd'), int(value or 0),
         int(snap.get('total') or 0), float(snap.get('off') or 0),
         float(_slopeNow(snap) or 0), float(snap.get('ema') or 0),
         gain))
    return gain


def _remember(gain):
    cell = _state.get('bt')
    if cell is not None:
        cell['forecast'] = gain
    return gain


def _mainSize():

    def ask():
        from helpers import dependency
        from skeletons.gui.impl import IGuiLoader
        main = dependency.instance(IGuiLoader).windowsManager.getMainWindow()
        if main is None:
            return (0, 0)
        else:
            width, height = main.size
            return (int(width or 0), int(height or 0))

    return _safe(ask) or (0, 0)


def _lowEdge(cfg):

    def run():
        window = _state.get('battleWindow')
        if window is None:
            return 0
        else:
            height = int((window.size or (0, 0))[1] or 0)
            screenH = int(_mainSize()[1] or 0)
            if height <= 0 or screenH <= 0:
                return 0
            pos = cfg.get('battlePos') or {'x': 0.015, 'y': 0.42}
            top = float(pos.get('y') or 0) * screenH
            if top + height > screenH - 1:
                return 1
            return 0

    return int(_safe(run) or 0)


def _tableFlag(snap):
    cd = int(snap.get('cd') or 0)
    if cd > 0:
        found = _safe((lambda : _exact(cd)))
        if found:
            if not int(snap.get('table') or 0):
                _log('the thresholds for %s are in the table after all - the snapshot was taken before it had loaded' % (
                 cd,))
                snap['table'] = 1
            return 1
    return 0


def _battlePush():
    model = _state.get('battleModel')
    if model is None:
        return
    else:
        snap = _state.get('snapshot') or {}
        cell = _state.get('bt') or {}
        cfg = _config()
        if snap.get('skip') or 0 < int(snap.get('tier') or 0) < MIN_TIER:
            _safe((lambda : model.setData(json.dumps({'ok': False}))))
            return
        value = int(_value(cell))
        data = {'ok': True, 
           'lang': (_lang()), 
           'line': (1 if cfg.get('battleLine') else 0), 
           'percent': (snap.get('percent') or '--'), 
           'ratingRaw': (float(snap.get('rating') or 0)), 
           'marks': (snap.get('marks') or 0), 
           'total': (snap.get('total') or 0), 
           'moved': (_movedNow(snap, value)), 
           'next': (snap.get('next') or 0), 
           'value': value, 
           'gain': (_remember(_plateSaid(snap, value))), 
           'nextPct': (_nextWhole(snap, value)), 
           'nextNeed': (_needThisBattle(snap, _nextWhole(snap, value))), 
           'exact': 0,
           'predictionEstimated': True,
           'region': _region(),
           'regionalMissing': not bool(_exact(int(snap.get('cd') or 0))), 
           'pos': (cfg.get('battlePos') or {'x': 0.015, 'y': 0.42}), 
           'lowEdge': (_lowEdge(cfg)), 
           'slack': (float(cfg.get('battleSlack') or 0)), 
           'hide': (1 if _state.get('guiHidden') or _highlightsOn() or _killCamOn() else 0), 
           'dragOff': (int(_state.get('dragOff') or 0)), 
           'screen': (list(_mainSize())), 
           'ctrl': (int(_state.get('ctrl') or 0)), 
           'alt': (int(_state.get('alt') or 0)), 
           'look': (_look()), 
           'file': (snap.get('file') or ''), 
           'table': (_tableFlag(snap)), 
           'young': (int(snap.get('young') or 0)), 
           'steps': [{'p': (int(point[1])), 'need': (_num(int(point[0])))} for point in snap.get('curve') or []]}
        _safe((lambda : model.setData(json.dumps(data))))
        return


def _pendingQueue():
    queue = _state.get('pendingList')
    if queue is None:
        queue = _state['pendingList'] = []
    return queue


def _pendingWrite():
    _ensureDir()
    live = None
    cell = _state.get('bt')
    snap = (cell or {}).get('snap') or _state.get('snapshot')
    if cell and snap and not cell.get('saved') and not cell.get('skip'):
        live = {'bt': (dict(cell)), 'snapshot': (dict(snap))}
    data = {'queue': (_pendingQueue()), 'live': live}
    _safe((lambda : open(PENDING_FILE, 'wb').write(json.dumps(data))))
    return


def _pendingSave():
    _pendingWrite()
    return


def _pendingPark(cell, snap):

    def once(why):
        mark = (cell or {}).get('id') or 0
        if _state.get('parkSaid') != (mark, why):
            _state['parkSaid'] = (
             mark, why)
            _log('the finished battle was not queued: %s' % why)
        return

    if not cell:
        once('the mod has no battle of its own in hand')
        return
    if cell.get('skip'):
        return
    own = cell.get('snap')
    if own and own.get('cd'):
        snap = own
    if cell.get('saved'):
        return
    if not snap:
        once('there is no snapshot of the vehicle to compare it with')
        return
    if not snap.get('cd'):
        once('the snapshot has no vehicle in it')
        return
    mineName = str(cell.get('name') or '')
    snapName = str(snap.get('name') or '')
    if mineName and snapName and mineName != snapName:
        _log('the waiting battle on %s does not belong to %s - not queued' % (
         mineName, snapName))
        return
    queue = _pendingQueue()
    mine = cell.get('id')
    for item in queue:
        other = (item.get('bt') or {}).get('id')
        if mine and other and other == mine:
            return

    queue.append({'bt': (dict(cell)), 'snapshot': (dict(snap))})
    if len(queue) > 8:
        del queue[:-8]
    _pendingWrite()
    return


def _pendingDrop():
    _safe((lambda : os.remove(PENDING_FILE)))
    return


def _pendingLoad():
    if _state.get('pendingRead'):
        return
    _state['pendingRead'] = True
    if not os.path.isfile(PENDING_FILE):
        return
    data = _safe((lambda : json.loads(open(PENDING_FILE, 'rb').read())))
    if not isinstance(data, dict):
        _pendingDrop()
        return
    queue = _pendingQueue()
    for item in data.get('queue') or []:
        if isinstance(item, dict) and (item.get('snapshot') or {}).get('cd'):
            queue.append(item)

    live = data.get('live')
    if isinstance(live, dict) and (live.get('snapshot') or {}).get('cd'):
        queue.append(live)
    if queue:
        _log('%d battle(s) from the previous run are waiting' % len(queue))
    return


def _bestCopy(items):
    if len(items) < 2:
        if items:
            return items[0]
        return
    best = None
    bestErr = None
    for item in items:
        snap = item.get('snapshot') or {}
        cell = item.get('bt') or {}
        total = float(snap.get('total') or 0)
        vehicle = _vehicleByCD(int(snap.get('cd') or 0))
        now = float(_movingTotal(vehicle) or 0) if vehicle is not None else 0.0
        value = _value(cell)
        if total <= 0 or now <= 0 or abs(value - total) < 1.0:
            continue
        k = (now - total) / (value - total)
        err = abs(k - float(snap.get('ema') or EMA_K))
        if bestErr is None or err < bestErr:
            best = item
            bestErr = err

    if best is None:
        return items[0]
    else:
        if len(items) > 1:
            _log('%d copies of one battle were waiting; kept the one worth %d' % (
             len(items), _value(best.get('bt') or {})))
        return best


def _afterSync(*_a):
    live = _state.get('bt')
    snap = _state.get('snapshot')
    said = (
     len(_pendingQueue()), 1 if live else 0, 1 if snap else 0,
     int((live or {}).get('saved') or 0),
     int((snap or {}).get('cd') or 0))
    if _state.get('syncSaid') != said:
        _state['syncSaid'] = said
        _log('the dossier synced: %d waiting, battle=%s, snapshot=%s' % (
         said[0],
         'saved' if said[3] else 'yes' if said[1] else 'no',
         said[4] or 'none'))
    if live and snap and not live.get('saved'):
        _pendingPark(live, snap)
    queue = _pendingQueue()
    if not queue:
        return
    else:
        groups = []
        index = {}
        for item in queue:
            snap = item.get('snapshot') or {}
            key = (int(snap.get('cd') or 0), round(float(snap.get('rating') or 0), 2))
            at = index.get(key)
            if at is None:
                index[key] = len(groups)
                groups.append([item])
            else:
                groups[at].append(item)

        rest = []
        changed = False
        for group in groups:
            item = _safe((lambda group=group: _bestCopy(group))) or group[0]
            if len(group) > 1:
                changed = True
            if not _safe((lambda item=item: _recordPending(item))):
                rest.append(item)
            else:
                changed = True

        if changed:
            _state['pendingList'] = rest
            _pendingWrite()
            _safe(_refresh)
        return


def _recordPending(item):
    cell = item.get('bt') or {}
    snap = item.get('snapshot') or {}
    intCD = int(snap.get('cd') or 0)
    if not intCD:
        _log('a waiting battle has no vehicle in it - it is dropped')
        return True
    else:
        vehicle = _vehicleByCD(intCD)
        if vehicle is None:
            _log('the vehicle of a waiting battle (%s) is not in the garage - it keeps waiting' % (
             intCD,))
            return False
        marks, rating = _markData(vehicle)
        was = float(snap.get('rating') or 0)
        if rating <= 0:
            _log('the client gives no mark percentage for %s yet - the battle keeps waiting' % (
             intCD,))
            return False
        shifted = abs(rating - was) >= 0.0001
        wasCount = int(snap.get('battles') or 0)
        if not shifted:
            if wasCount <= 0:
                return False
            if _randomBattles(vehicle) <= wasCount:
                return False
        nowTotal = _movingTotal(vehicle) or 0
        srv = _state.get('serverCell') or {}
        if srv and int(srv.get('cd') or 0) == int(intCD):
            _state['serverCell'] = None
            if int(_value(srv)) != int(_value(cell)):
                _log('the server counted this battle differently: ours %d, server %d (radio %d vs %d, track %d vs %d)' % (
                 int(_value(cell)), int(_value(srv)),
                 cell.get('radio') or 0, srv.get('radio') or 0,
                 cell.get('track') or 0, srv.get('track') or 0))
            cell = dict(cell)
            for name in ('dmg', 'radio', 'track', 'stun'):
                cell[name] = srv.get(name) or 0

            fromServer = 1
        else:
            fromServer = 0
        moved = float(nowTotal or 0) - float(snap.get('total') or 0)
        guessed = 0
        if not fromServer and int(_value(cell)) <= 0 and moved > 0.5:
            k = float(snap.get('ema') or 0)
            if not 0.005 < k < 0.08:
                k = float(_config().get('ema') or EMA_K)
            if 0.005 < k < 0.08:
                worth = float(snap.get('total') or 0) + moved / k
                if worth > 0:
                    cell = dict(cell, dmg=int(round(worth)), radio=0, track=0, stun=0)
                    guessed = 1
                    _log('the battle on %s came back empty, and the moving total still moved %+.0f: it was worth about %d (k=%.4f) - written down as worked out, not counted' % (
                     snap.get('name') or intCD, moved, int(round(worth)),
                     k))
        entry = {'ts': (int(_safe((lambda : __import__('time').time())) or 0)), 
           'avgPrev': (int(snap.get('total') or 0)), 
           'avg': (int(nowTotal or 0)), 
           'dmg': (int(cell.get('dmg') or 0)), 
           'radio': (int(cell.get('radio') or 0)), 
           'track': (int(cell.get('track') or 0)), 
           'stun': (int(cell.get('stun') or 0)), 
           'rating': rating, 
           'prev': was, 
           'bc': (_randomBattles(vehicle)), 
           'srv': fromServer, 
           'est': guessed, 
           'marks': marks}
        if cell.get('map'):
            entry['map'] = cell.get('map')
            entry['mapName'] = cell.get('mapName') or ''
        live = _state.get('bt')
        if live is not None and live.get('id') and live.get('id') == cell.get('id'):
            live['saved'] = True
        _add(intCD, entry)
        _safe((lambda : _anchorAt(intCD, nowTotal, rating)))
        value = _value(entry)
        moved = float(nowTotal or 0) - float(snap.get('total') or 0)
        _safe((lambda : _recalcAcross(intCD, row=None, was=was, rating=rating, moved=moved, slope=snap.get('slope'))))
        _saveHistory()
        _log('battle taken from the dossier: %s %.2f -> %.2f (%+.2f), forecast %+.2f; total %s -> %s, our value %d, so k=%.4f and one point is worth %.5f per cent' % (
         cell.get('name') or '?', was, rating, rating - was,
         float(cell.get('forecast') or 0), snap.get('total'), nowTotal,
         value,
         moved / (value - float(snap.get('total') or 1)) if value != float(snap.get('total') or 0) else 0.0,
         (rating - was) / moved if abs(moved) > 0.0001 else 0.0))
        return True


def _watchSync():
    if _state.get('syncHooked'):
        return True
    from helpers import dependency
    from skeletons.gui.shared import IItemsCache
    cache = dependency.instance(IItemsCache)
    _listen(cache.onSyncCompleted, _afterSync)
    _listen(cache.onSyncCompleted, lambda *_a: _safe(_payload))
    _state['syncHooked'] = True
    return True


def _startHook(attempt=0):
    if _safe(_mountPanel):
        return
    if attempt < 40:
        _safe((lambda : _schedule(1.0, (lambda : _startHook(attempt + 1)))))
    return


def _start(attempt=0):
    if _state.get('started') or _state.get('stopped'):
        return
    try:
        from PlayerEvents import g_playerEvents
        _listen(g_playerEvents.onAccountShowGUI, _onLobby)
        _listen(g_playerEvents.onAvatarBecomePlayer, _onLobbyLeft)
        _listen(g_playerEvents.onAvatarReady, _onBattleStart)
        _listen(g_playerEvents.onAvatarBecomeNonPlayer, _onBattleEnd)
        _state['started'] = True
        _safe(_lobbyPackage)
        _safe((lambda : _startHook(0)))
        _log('loaded %s' % (VERSION,))
        return
    except Exception:
        pass

    if attempt < 12:
        try:
            import BigWorld
            _schedule(5.0, (lambda : _start(attempt + 1)))
        except Exception:
            pass

    return


def fini():
    if _state.get('stopped'):
        return
    _safe(_onBattleEnd)
    _safe(_pendingSave)
    _state['stopped'] = True
    _state['lifecycle'] = _state.get('lifecycle', 0) + 1
    for scope in ('battle', 'lobby', 'global'):
        _clearScope(scope)
    model = _state.pop('panelModel', None)
    if model is not None and model.onAction is not None:
        _safe(lambda: model.onAction.__isub__(_onAction))
    for flag in ('started', 'watchers', 'syncHooked', 'resultsHooked', 'escHooked', 'killCamHooked', 'keysHooked', 'inLobby'):
        _state.pop(flag, None)

def init():
    _state['stopped'] = False
    _start()

_start()
