#!/usr/bin/env python3
"""CodeBuddy Menubar — macOS 菜单栏常驻的 CodeBuddy 积分监控 + 自动签到工具

核心功能:
  1. 实时监控: 菜单栏常驻显示腾讯云 CodeBuddy / WorkBuddy 积分余量与百分比,
     下拉可查看各套餐明细与到期时间, 低余额弹窗提醒
  2. 自动领积分: 每日自动签到, 签到成功弹系统通知

用量接口与鉴权方案参考自 wwenc6621/CodeBuddy-Usage (MIT):
  https://github.com/wwenc6621/CodeBuddy-Usage
感谢原作者对接口协议的逆向与分享。本项目与腾讯 CodeBuddy 官方无关。

依赖:
  python3 -m pip install --user -r requirements.txt

配置文件: ~/.codebuddy-menubar.json (参考 config.example.json)
  首次启动若配置不存在, 会自动尝试从 VS Code 的 codebuddyUsage 扩展配置导入;
  否则请自行创建并填入 cookie / user_agent。

启动: python3 codebuddy_menubar.py
一键安装(含开机自启): ./setup.sh --autostart
"""

import json
import os
import subprocess
import sys
import threading
import time
import urllib3

try:
    import requests
    import rumps
except ImportError:
    sys.exit('缺少依赖, 请先执行: python3 -m pip install --user -r requirements.txt')

CONFIG_PATH = os.path.expanduser('~/.codebuddy-menubar.json')
VSCODE_SETTINGS = os.path.expanduser(
    '~/Library/Application Support/Code/User/settings.json')
ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'bar_icon.png')

DEFAULTS = {
    'api_base': 'https://www.workbuddy.cn',   # 国际站改为 https://www.workbuddy.ai
    'refresh_minutes': 30,
    'auto_checkin': True,
    'low_balance': 100,
    'show_percent': True,
    'bar_icon': '🐱',                         # 图标文件缺失时的文字回退
    'verify_ssl': True,
}

# 用量接口的套餐筛选码, 与 CodeBuddy-Usage 保持一致
DEFAULT_PACKAGE_CODES = [
    'TCACA_code_008_cfWoLwvjU4', 'TCACA_code_009_0XmEQc2xOf',
    'TCACA_code_038_OhvqZtiPKr', 'TCACA_code_007_nzdH5h4Nl0',
    'TCACA_code_028_NtpWi0jzXs', 'TCACA_code_029_6wCGEWquYy',
    'TCACA_code_030_BjSt89qTvr',
]

MAX_SLOTS = 6  # 菜单里最多展示的套餐行数


def load_config():
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH) as f:
            cfg.update(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return cfg


def ensure_config():
    """配置不存在时, 尝试从 VS Code 的 codebuddyUsage 扩展配置导入。"""
    if os.path.exists(CONFIG_PATH):
        return
    imported = {}
    try:
        with open(VSCODE_SETTINGS) as f:
            vs = json.load(f)
        if vs.get('codebuddyUsage.cookie'):
            imported['cookie'] = vs['codebuddyUsage.cookie']
            imported['user_agent'] = vs.get('codebuddyUsage.userAgent', '')
    except (OSError, json.JSONDecodeError):
        pass
    with open(CONFIG_PATH, 'w') as f:
        json.dump({**DEFAULTS, **imported}, f, indent=2, ensure_ascii=False)


def fmt(n):
    s = f'{float(n):.2f}'.rstrip('0').rstrip('.')
    return s or '0'


class Api:
    """workbuddy 用量/签到接口的极简封装 (Cookie 鉴权)。"""

    def __init__(self, cfg):
        self.cfg = cfg
        self.verify = bool(cfg.get('verify_ssl', True))
        self.session = requests.Session()

    def _headers(self):
        base = self.cfg['api_base'].rstrip('/')
        return {
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json',
            'cookie': self.cfg['cookie'],
            'origin': base,
            'referer': base + '/profile/plans-usage',
            'x-client-platform': 'web',
            'user-agent': self.cfg['user_agent'],
        }

    def _request(self, method, path, payload=None):
        url = self.cfg['api_base'].rstrip('/') + path
        kwargs = dict(headers=self._headers(), timeout=20, verify=self.verify)
        if payload is not None:
            kwargs['data'] = json.dumps(payload)
        try:
            resp = self.session.request(method, url, **kwargs)
        except requests.exceptions.SSLError:
            # 本机网络存在 TLS 中间层(自签证书)时回退为不校验, 并记住该选择
            self.verify = False
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            kwargs['verify'] = False
            resp = self.session.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def checkin(self):
        """每日签到。返回 (freshly_claimed, credit or None)。"""
        j = self._request('POST', '/billing/meter/daily-checkin', {})
        code = j.get('code')
        if code == 0:
            credit = (j.get('data') or {}).get('credit')
            return True, credit
        if code == 10001:  # 网关幂等: 今日已签到
            return False, None
        return False, None

    def usage(self):
        j = self._request('POST', '/billing/meter/get-user-resource', {
            'PageNumber': 1, 'PageSize': 200, 'ProductCode': 'p_tcaca',
            'Status': [0, 3], 'OnlyValidPeriod': True,
            'PackageCodes': self.cfg.get('package_codes') or DEFAULT_PACKAGE_CODES,
            'NeedInUsage': True,
        })
        accounts = ((j.get('data') or {}).get('Response') or {}).get('Data', {}) \
            .get('Accounts') or []
        pkgs, remain, total = [], 0.0, 0.0
        for a in accounts:
            r = float(a.get('CycleCapacityRemainPrecise')
                      or a.get('CapacityRemainPrecise') or 0)
            s = float(a.get('CycleCapacitySizePrecise')
                      or a.get('CapacitySizePrecise') or 0)
            if r > 0:
                total += s
            remain += r
            expire = (a.get('CycleEndTime') or '')[5:10]  # MM-DD
            pkgs.append((a.get('PackageName') or '-', r, s, expire))
        pkgs.sort(key=lambda p: p[3])
        return remain, total, pkgs


class CodeBuddyApp(rumps.App):

    def __init__(self):
        ensure_config()
        self.cfg = load_config()

        self._mi_title = rumps.MenuItem('CodeBuddy 积分',
                                        callback=self.on_refresh)
        self._pkg_slots = [rumps.MenuItem('', callback=self.on_open)
                           for _ in range(MAX_SLOTS)]
        self._mi_checkin = rumps.MenuItem('签到: -', callback=self._noop)
        self._mi_updated = rumps.MenuItem('更新于: -', callback=self._noop)
        menu = [
            self._mi_title, None,
            *self._pkg_slots, None,
            self._mi_checkin, self._mi_updated, None,
            rumps.MenuItem('立即刷新', callback=self.on_refresh),
            rumps.MenuItem('打开用量页面', callback=self.on_open),
            rumps.MenuItem('重新载入配置', callback=self.on_reload),
        ]

        self._use_icon = os.path.exists(ICON_PATH)
        if self._use_icon:
            # 单色 template 图标, 随系统深/浅色菜单栏自动变色
            super().__init__('CodeBuddy', icon=ICON_PATH, template=True,
                             title='…', menu=menu, quit_button='退出')
        else:
            super().__init__('CodeBuddy',
                             title=f"{self.cfg.get('bar_icon', '🐱')} …",
                             menu=menu, quit_button='退出')
        for slot in self._pkg_slots:
            slot.hide()

        self._result = None
        self._dirty = False
        self._working = False
        self._last_fetch = 0.0
        self._low_notified = False
        rumps.Timer(self._tick, 1).start()

    # ---------- 调度 (主线程) ----------

    def _tick(self, _sender):
        if self._dirty:
            self._dirty = False
            self._render()
        interval = max(60, int(self.cfg.get('refresh_minutes', 30)) * 60)
        if not self._working and time.time() - self._last_fetch >= interval:
            self._start_worker()

    def _start_worker(self):
        self._working = True
        if self._last_fetch == 0.0:
            self.title = '…' if self._use_icon \
                else f"{self.cfg.get('bar_icon', '🐱')} …"
        threading.Thread(target=self._work, daemon=True).start()

    # ---------- 后台拉取 ----------

    def _work(self):
        result = {'ok': False, 'at': time.time()}
        cfg = self.cfg
        try:
            if not cfg.get('cookie'):
                raise RuntimeError('NO_COOKIE')
            api = Api(cfg)
            checkin_msg = None
            if cfg.get('auto_checkin', True):
                try:
                    fresh, credit = api.checkin()
                    if fresh:
                        checkin_msg = '签到成功' + (f' +{fmt(credit)}' if credit else '')
                except Exception:
                    checkin_msg = None  # 签到失败不影响余量展示
            remain, total, pkgs = api.usage()
            result.update(ok=True, remain=remain, total=total,
                          pkgs=pkgs, checkin=checkin_msg)
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else 0
            result['error'] = ('Cookie 已失效' if status in (401, 403)
                               else f'HTTP {status}')
        except RuntimeError as e:
            result['error'] = '未配置 Cookie' if str(e) == 'NO_COOKIE' else str(e)
        except Exception as e:  # 网络/超时等
            result['error'] = str(e)[:80] or type(e).__name__
        self._result = result
        self._last_fetch = time.time()
        self._working = False
        self._dirty = True

    # ---------- 渲染 (主线程) ----------

    def _bar_title(self, remain, pct):
        """状态栏标题: [图标] 积分 · 百分比"""
        if remain >= 100:
            num = f'{remain:.0f}'
        elif remain >= 10:
            num = f'{remain:.1f}'
        else:
            num = f'{remain:.2f}'
        prefix = '' if self._use_icon \
            else self.cfg.get('bar_icon', '🐱') + ' '
        if self.cfg.get('show_percent', True):
            # 截断到一位小数, 不四舍五入 (99.99 -> 99.9)
            pct_s = f'{int(pct * 10) / 10:.1f}'.rstrip('0').rstrip('.') + '%'
            return f'{prefix}{num} · {pct_s}'
        return f'{prefix}{num}'

    def _render(self):
        r = self._result
        if r is None:
            return
        if not r.get('ok'):
            self.title = '?' if self._use_icon \
                else f"{self.cfg.get('bar_icon', '🐱')} ?"
            self._mi_title.title = 'CodeBuddy 积分 — 拉取失败'
            self._mi_checkin.title = '错误: ' + r.get('error', '未知')
            self._mi_updated.title = '更新于: -'
            for slot in self._pkg_slots:
                slot.hide()
            return

        remain, total, pkgs = r['remain'], r['total'], r['pkgs']
        pct = (remain / total * 100) if total > 0 else 0
        self.title = self._bar_title(remain, pct)
        self._mi_title.title = (f'余量 {fmt(remain)} / {fmt(total)}'
                                f'（{pct:.1f}%）')
        for i, slot in enumerate(self._pkg_slots):
            if i < len(pkgs) and i < MAX_SLOTS:
                name, pr, ps, exp = pkgs[i]
                slot.title = f'✦ {name}  {fmt(pr)}/{fmt(ps)}（{exp}到期）'
                slot.show()
            else:
                slot.hide()
        self._mi_checkin.title = r['checkin'] or '今日已签到' \
            if self.cfg.get('auto_checkin', True) else '签到: 已关闭'
        self._mi_updated.title = '更新于: ' + \
            time.strftime('%H:%M:%S', time.localtime(r['at']))

        # 低余额提醒 (越过阈值只提醒一次)
        low = float(self.cfg.get('low_balance', 100) or 0)
        if low > 0 and remain <= low and not self._low_notified:
            self._low_notified = True
            rumps.notification('CodeBuddy 积分不足', '',
                               f'当前仅剩 {fmt(remain)} 积分，请及时关注')
        elif remain > low:
            self._low_notified = False

        if r.get('checkin'):
            rumps.notification('CodeBuddy 每日签到', '', r['checkin'])

    # ---------- 菜单动作 ----------

    def _noop(self, _sender):
        pass

    def on_refresh(self, _sender):
        self._last_fetch = 0.0  # 让下一个 tick 立即触发

    def on_open(self, _sender):
        subprocess.Popen(['open', self.cfg['api_base'].rstrip('/')
                          + '/profile/plans-usage'])

    def on_reload(self, _sender):
        self.cfg = load_config()
        self._last_fetch = 0.0


if __name__ == '__main__':
    CodeBuddyApp().run()
