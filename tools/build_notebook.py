#!/usr/bin/env python3
"""Build the Notebook pages (listing + 3 explainers) into the portfolio root.

Diagrams are inline SVG with SMIL animations. Every animated element shares one
loop length per diagram (`dur` = cycle) and uses keyTimes to pick its moment, so a
whole diagram loops in sync. site.js pauses them off screen and shows a still frame
(data-still, seconds) for reduced motion.
"""
import html
import re
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------- svg helpers


def _kt(points, cycle):
    """points: [(seconds, value)] -> (values, keyTimes) strictly increasing in [0, 1]."""
    pts = sorted(points, key=lambda p: p[0])
    times, values = [], []
    last = -1.0
    for t, v in pts:
        k = min(max(t / cycle, 0.0), 1.0)
        if k <= last:
            k = last + 0.0005
        if k > 1:
            continue
        times.append(k)
        values.append(v)
        last = k
    if times[0] != 0:
        times.insert(0, 0.0)
        values.insert(0, values[0])
    if times[-1] < 1:
        times.append(1.0)
        values.append(values[-1])
    return ';'.join(str(v) for v in values), ';'.join(f'{t:.4f}' for t in times)


def opacity_anim(windows, cycle, fade=0.2):
    pts = [(0, 0)]
    for a, b in windows:
        pts += [(max(a, 0.001), 0), (a + fade, 1), (b, 1), (b + fade, 0)]
    pts.append((cycle, 0))
    values, kt = _kt(pts, cycle)
    return f'<animate attributeName="opacity" dur="{cycle}s" repeatCount="indefinite" values="{values}" keyTimes="{kt}"/>'


def node(x, y, w, h, title, sub='', cls='', sub2=''):
    cx = x + w / 2
    cy = y + h / 2
    parts = [f'<g class="d-node {cls}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14"/>']
    if sub2:
        parts.append(f'<text class="d-title" x="{cx}" y="{cy - 10}" text-anchor="middle">{title}</text>')
        parts.append(f'<text class="d-sub" x="{cx}" y="{cy + 9}" text-anchor="middle">{sub}</text>')
        parts.append(f'<text class="d-sub" x="{cx}" y="{cy + 26}" text-anchor="middle">{sub2}</text>')
    elif sub:
        parts.append(f'<text class="d-title" x="{cx}" y="{cy - 2}" text-anchor="middle">{title}</text>')
        parts.append(f'<text class="d-sub" x="{cx}" y="{cy + 17}" text-anchor="middle">{sub}</text>')
    else:
        parts.append(f'<text class="d-title" x="{cx}" y="{cy + 6}" text-anchor="middle">{title}</text>')
    parts.append('</g>')
    return ''.join(parts)


def glow(x, y, w, h, windows, cycle):
    return (f'<rect x="{x - 4}" y="{y - 4}" width="{w + 8}" height="{h + 8}" rx="17" fill="none" '
            f'stroke="#D9541E" stroke-width="3.5" opacity="0">{opacity_anim(windows, cycle)}</rect>')


def packet(path, t0, t1, cycle, cls='', r=7):
    """A dot that moves along `path` between t0 and t1 (seconds) once per loop."""
    points, kt = _kt([(0, 0), (t0, 0), (t1, 1), (cycle, 1)], cycle)
    return (f'<circle class="d-dot {cls}" r="{r}" opacity="0">'
            f'<animateMotion dur="{cycle}s" repeatCount="indefinite" calcMode="linear" path="{path}" '
            f'keyPoints="{points}" keyTimes="{kt}"/>'
            f'{opacity_anim([(t0 - 0.12, t1)], cycle, 0.12)}</circle>')


def label(x, y, text, cls='', anchor='middle', windows=None, cycle=None):
    if windows:
        return f'<text class="d-label {cls}" x="{x}" y="{y}" text-anchor="{anchor}" opacity="0">{text}{opacity_anim(windows, cycle)}</text>'
    return f'<text class="d-label {cls}" x="{x}" y="{y}" text-anchor="{anchor}">{text}</text>'


def tag(x, y, text, anchor='middle'):
    w = 7.2 * len(text) + 18
    x0 = x - w / 2 if anchor == 'middle' else x
    return (f'<g class="d-tag"><rect x="{x0}" y="{y - 14}" width="{w}" height="21" rx="10.5"/>'
            f'<text class="d-label" x="{x0 + w / 2}" y="{y + 1}" text-anchor="middle">{text}</text></g>')


def svg(vw, vh, label_text, body, still):
    return (f'<svg class="motion" viewBox="0 0 {vw} {vh}" role="img" aria-label="{html.escape(label_text)}" '
            f'data-still="{still}">{body}</svg>')


def legend(x, y, items):
    out = []
    for kind, text in items:
        if kind == 'orange':
            out.append(f'<circle class="d-dot" cx="{x}" cy="{y - 4}" r="6"/>')
        elif kind == 'ink':
            out.append(f'<circle class="d-dot is-ink" cx="{x}" cy="{y - 4}" r="6"/>')
        else:
            out.append(f'<path class="d-flow is-ink" d="M{x - 10} {y - 4}H{x + 12}"/>')
        out.append(f'<text class="d-legend" x="{x + 16}" y="{y}">{text}</text>')
        x += 30 + 7 * len(text)
    return ''.join(out)


# --------------------------------------------------------------------------- figures: trading platform

def fig_broker_stack():
    c = 9.5
    b = []
    b.append(label(232, 50, 'MONEY', 'is-orange', 'start'))
    b.append(label(232, 304, 'TRADING', 'is-orange', 'start'))
    # connectors
    b.append('<path class="d-line" d="M174 108H860"/>')
    b.append('<path class="d-flow" d="M174 108H860"/>')
    b.append('<path class="d-line" d="M765 146C765 230 655 240 655 320"/>')
    b.append('<path class="d-flow" d="M765 146C765 230 655 240 655 320"/>')
    b.append('<path class="d-line is-ink" d="M174 358H800"/>')
    b.append('<path class="d-flow is-ink is-reverse" d="M174 372H800"/>')
    # packets under the nodes
    money = 'M174 108H765C765 230 655 240 655 320'
    b.append(packet(money, 0.4, 4.0, c))
    b.append(packet('M174 352H870', 5.0, 6.6, c, 'is-ink'))
    # nodes
    b.append(node(24, 70, 150, 336, 'Trader', 'web, app,', 'is-dark', 'MT5 terminal'))
    b.append(node(230, 70, 170, 76, 'Client portal', 'sign up, deposit'))
    b.append(node(450, 70, 170, 76, 'PSP', 'cards, bank, crypto'))
    b.append(node(670, 70, 190, 76, 'Back office', 'KYC, wallets, CRM'))
    b.append(node(560, 320, 190, 76, 'MT5 server', 'accounts, orders', 'is-accent'))
    b.append(node(800, 320, 140, 76, 'Liquidity', 'banks, LPs'))
    # highlights follow the packets
    b.append(glow(230, 70, 170, 76, [(0.65, 1.4)], c))
    b.append(glow(450, 70, 170, 76, [(1.6, 2.35)], c))
    b.append(glow(670, 70, 190, 76, [(2.55, 3.2)], c))
    b.append(glow(560, 320, 190, 76, [(3.9, 4.8), (5.75, 6.15)], c))
    b.append(glow(800, 320, 140, 76, [(6.5, 7.3)], c))
    # connector labels
    b.append(tag(202, 96, 'sign up'))
    b.append(tag(425, 96, '$100'))
    b.append(tag(645, 96, 'paid'))
    b.append(tag(745, 238, 'Manager API: +$100'))
    b.append(tag(367, 346, 'buy 1 lot EURUSD'))
    b.append(tag(367, 396, 'prices stream back'))
    b.append(tag(775, 346, 'hedge'))
    # balance flips when the deposit lands
    b.append(label(655, 425, 'balance $0.00', '', 'middle', [(0, 3.95)], c))
    b.append(label(655, 425, 'balance $100.00', 'is-orange', 'middle', [(4.0, 9.2)], c))
    b.append(legend(40, 450, [('orange', 'money'), ('ink', 'orders'), ('flow', 'prices')]))
    return svg(960, 470, 'Diagram of a broker: the trader deposits through the client portal and PSP into the back office, which credits the MT5 account; orders go from the trader to the MT5 server and on to liquidity providers.', ''.join(b), 4.3)


def fig_trade_life():
    c = 11
    xs = [70, 207, 344, 481, 618, 755, 892]
    steps = [('Sign up', 'KYC check'), ('Deposit', 'via the PSP'), ('Fund MT5', 'wallet to account'),
             ('Open', 'buy EURUSD'), ('Price moves', 'profit floats'), ('Close', 'P&amp;L to balance'),
             ('Withdraw', 'back to the bank')]
    b = []
    b.append('<path class="d-line is-ink" d="M70 170H892"/>')
    # progress line draws across, holds, resets
    b.append('<path d="M70 170H892" fill="none" stroke="#D9541E" stroke-width="5" stroke-linecap="round" '
             'pathLength="1" stroke-dasharray="1" stroke-dashoffset="1">'
             f'<animate attributeName="stroke-dashoffset" dur="{c}s" repeatCount="indefinite" '
             f'values="1;1;0;0;1" keyTimes="0;0.03;0.78;0.95;1"/></path>')
    reach = [0.33 + i * (8.25 / 6) for i in range(7)]
    for i, (x, (t, s)) in enumerate(zip(xs, steps)):
        b.append(f'<circle cx="{x}" cy="170" r="20" fill="#FFFDF8" stroke="#111111" stroke-width="2"/>')
        b.append(f'<circle cx="{x}" cy="170" r="20" fill="#D9541E" stroke="#111111" stroke-width="2" opacity="0">'
                 f'{opacity_anim([(reach[i], 10.4)], c, 0.15)}</circle>')
        b.append(f'<text class="d-label" x="{x}" y="175" text-anchor="middle" style="font-size:13px;fill:#111">{i + 1:02d}</text>')
        b.append(f'<text class="d-title" x="{x}" y="222" text-anchor="middle" style="font-size:15px">{t}</text>')
        b.append(f'<text class="d-sub" x="{x}" y="241" text-anchor="middle">{s}</text>')
    # system bands
    b.append('<rect x="440" y="62" width="356" height="56" rx="12" fill="#111111"/>')
    b.append('<text class="d-label" x="618" y="86" text-anchor="middle" style="fill:#F3EEE3">INSIDE MT5</text>')
    b.append('<text class="d-sub" x="618" y="104" text-anchor="middle" style="fill:#b9b1a2">steps 04 to 06</text>')
    # small price chart above "Price moves"
    b.append('<polyline points="520,300 545,292 568,298 590,283 612,288 636,272 660,276 684,262 712,266" fill="none" '
             'stroke="#111111" stroke-width="2.5" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1">'
             f'<animate attributeName="stroke-dashoffset" dur="{c}s" repeatCount="indefinite" values="1;1;0;0;1" '
             'keyTimes="0;0.47;0.6;0.95;1"/></polyline>')
    b.append(label(712, 254, '+20 pips', 'is-orange', 'middle', [(6.6, 10.4)], c))
    return svg(960, 320, 'Timeline of a trade in seven steps: sign up, deposit, fund the MT5 account, open, price moves, close, withdraw. Steps 4 to 6 happen inside MT5.', ''.join(b), 10)


def fig_abook():
    c = 7
    b = []
    b.append('<path class="d-line is-ink" d="M180 180H330"/>')
    b.append('<path class="d-line" d="M530 170C620 170 640 78 720 78"/>')
    b.append('<path class="d-line" d="M530 190C620 190 640 282 720 282"/>')
    b.append(packet('M180 180H530C620 180 640 78 720 78', 0.3, 2.3, c))
    b.append(packet('M180 180H530C620 180 640 282 720 282', 3.8, 5.8, c, 'is-ink'))
    b.append(node(30, 142, 150, 76, 'Trader', 'buy 1 lot', 'is-dark'))
    b.append(node(330, 142, 200, 76, 'Broker', 'routing rules', 'is-accent'))
    b.append(node(720, 40, 210, 76, 'Liquidity provider', 'A-book: passed on'))
    b.append(node(720, 244, 210, 76, 'Own book', 'B-book: kept in house', 'is-dark'))
    b.append(glow(330, 142, 200, 76, [(1.0, 1.7), (4.5, 5.2)], c))
    b.append(glow(720, 40, 210, 76, [(2.2, 3.4)], c))
    b.append(glow(720, 244, 210, 76, [(5.7, 6.8)], c))
    b.append(label(825, 140, 'broker earns spread or commission', '', 'middle'))
    b.append(label(825, 344, 'broker is the counterparty', '', 'middle'))
    b.append(label(430, 250, 'route A', 'is-orange', 'middle', [(1.0, 3.4)], c))
    b.append(label(430, 250, 'route B', '', 'middle', [(4.5, 6.8)], c))
    return svg(960, 370, 'An order goes from the trader to the broker, whose routing rules send it either to a liquidity provider (A-book) or keep it in the broker\'s own book (B-book).', ''.join(b), 2.6)


# --------------------------------------------------------------------------- figures: PSP

def fig_card_chain():
    c = 11
    xs = [16, 172, 328, 484, 640, 796]
    names = [('Trader', 'taps Deposit', 'is-dark'), ('Checkout', 'broker page', ''), ('PSP', 'one API', 'is-accent'),
             ('Acquirer', 'merchant bank', ''), ('Card network', 'Visa, Mastercard', ''), ('Issuer', "trader's bank", '')]
    b = []
    b.append(label(474, 62, 'AUTHORIZATION REQUEST', 'is-orange'))
    b.append('<path class="d-line" d="M82 80H862"/>')
    b.append('<path class="d-flow" d="M82 80H862"/>')
    b.append('<path class="d-line is-ink" d="M82 198H862"/>')
    b.append('<path class="d-flow is-ink is-reverse" d="M82 198H862"/>')
    b.append(label(474, 222, 'APPROVED, IN A SECOND OR TWO'))
    b.append('<path class="d-line" d="M394 198V280"/>')
    b.append('<path class="d-line" d="M488 318H560"/>')
    for x, (t, s, cls) in zip(xs, names):
        b.append(node(x, 100, 132, 76, t, s, cls))
    b.append(packet('M82 80H862', 0.3, 3.1, c))
    b.append(packet('M862 198H82', 3.6, 6.0, c, 'is-ink'))
    b.append(packet('M394 198V280', 6.3, 7.0, c))
    b.append(packet('M488 318H560', 7.6, 8.1, c))
    # glows along the request and the answer
    for i, x in enumerate(xs):
        t_out = 0.3 + (x + 66 - 82) / 780 * 2.8
        t_back = 3.6 + (862 - (x + 66)) / 780 * 2.4
        b.append(glow(x, 100, 132, 76, [(t_out - 0.2, t_out + 0.35), (t_back - 0.2, t_back + 0.35)], c))
    b.append(node(300, 280, 188, 76, 'Broker server', 'checks the signature'))
    b.append(node(560, 280, 170, 76, 'Wallet', '&#160;'))
    b.append(glow(300, 280, 188, 76, [(6.9, 7.7)], c))
    b.append(glow(560, 280, 170, 76, [(8.1, 10.5)], c))
    b.append(tag(394, 250, 'webhook: paid'))
    b.append(label(645, 338, '$0.00', '', 'middle', [(0, 8.1)], c))
    b.append(label(645, 338, '$100.00', 'is-orange', 'middle', [(8.15, 10.6)], c))
    b.append(legend(780, 390, [('orange', 'request'), ('ink', 'answer')]))
    return svg(960, 400, 'A card deposit: the authorization request travels from the trader through checkout, PSP, acquirer and card network to the issuer; the approval comes back; the PSP then sends a webhook to the broker server, which credits the wallet.', ''.join(b), 9)


def fig_webhook():
    c = 11
    b = []
    b.append('<path class="d-line is-ink" d="M210 165H700"/>')
    b.append(node(40, 127, 170, 76, 'PSP', 'sends the result', 'is-accent'))
    b.append(node(700, 127, 220, 76, 'Broker server', 'remembers event ids'))
    # attempt 1 gets lost half way
    b.append(packet('M210 165H455', 0.4, 1.8, c))
    b.append(label(455, 172, '✕', 'is-orange', 'middle', [(1.9, 3.0)], c).replace('d-label', 'd-big'))
    b.append(label(455, 112, 'timeout', '', 'middle', [(1.9, 3.0)], c))
    # attempt 2 lands
    b.append(packet('M210 165H700', 3.4, 5.4, c))
    b.append(glow(700, 127, 220, 76, [(5.3, 6.2)], c))
    b.append(label(810, 240, 'event 7f3a: credit $100', 'is-orange', 'middle', [(5.4, 10.4)], c))
    # attempt 3 is a duplicate
    b.append(packet('M210 165H700', 6.6, 8.6, c, 'is-ink'))
    b.append(glow(700, 127, 220, 76, [(8.5, 9.2)], c))
    b.append(label(810, 264, 'event 7f3a again: ignored', '', 'middle', [(8.7, 10.4)], c))
    for t0, t1, text in [(0.2, 3.0, 'attempt 1'), (3.2, 6.2, 'attempt 2'), (6.4, 9.6, 'attempt 3')]:
        b.append(label(300, 150, text, '', 'middle', [(t0, t1)], c))
    b.append(label(810, 96, 'balance $0.00', '', 'middle', [(0, 5.4)], c))
    b.append(label(810, 96, 'balance $100.00', 'is-orange', 'middle', [(5.45, 10.6)], c))
    return svg(960, 300, 'A webhook delivered three times: the first attempt times out, the second credits 100 dollars, the third carries the same event id and is ignored, so the balance stays at 100 dollars.', ''.join(b), 9.2)


def fig_recon():
    c = 9
    rows = [('DEP-1041', '100.00', True), ('DEP-1042', '250.00', True), ('DEP-1043', '75.00', True), ('DEP-1044', '500.00', False)]
    b = []
    b.append('<text class="d-title" x="60" y="54">Broker ledger</text>')
    b.append('<text class="d-title" x="570" y="54">PSP settlement report</text>')
    for i, (ref, amt, ok) in enumerate(rows):
        y = 78 + i * 62
        b.append(f'<g class="d-node"><rect x="60" y="{y}" width="330" height="46" rx="10"/></g>')
        b.append(f'<text class="d-label" x="80" y="{y + 28}">{ref}</text><text class="d-label" x="370" y="{y + 28}" text-anchor="end">{amt}</text>')
        if ok:
            b.append(f'<g class="d-node"><rect x="570" y="{y}" width="330" height="46" rx="10"/></g>')
            b.append(f'<text class="d-label" x="590" y="{y + 28}">{ref}</text><text class="d-label" x="880" y="{y + 28}" text-anchor="end">{amt}</text>')
            t0 = 0.6 + i * 1.1
            b.append(f'<path d="M390 {y + 23}H570" fill="none" stroke="#111111" stroke-width="2" pathLength="1" '
                     f'stroke-dasharray="1" stroke-dashoffset="1"><animate attributeName="stroke-dashoffset" dur="{c}s" '
                     f'repeatCount="indefinite" values="1;1;0;0;1" keyTimes="0;{t0 / c:.4f};{(t0 + 0.6) / c:.4f};{8.4 / c:.4f};1"/></path>')
            b.append(f'<circle cx="480" cy="{y + 23}" r="12" fill="#111111" opacity="0">{opacity_anim([(t0 + 0.6, 8.4)], c, 0.15)}</circle>')
            b.append(f'<path d="M474 {y + 23}l4 4 8-8" fill="none" stroke="#F3EEE3" stroke-width="2.4" stroke-linecap="round" opacity="0">{opacity_anim([(t0 + 0.6, 8.4)], c, 0.15)}</path>')
        else:
            b.append(f'<rect x="570" y="{y}" width="330" height="46" rx="10" fill="none" stroke="#cdc3b0" stroke-width="2" stroke-dasharray="6 6"/>')
            b.append(f'<text class="d-label" x="735" y="{y + 28}" text-anchor="middle">not in the report yet</text>')
            b.append(f'<circle cx="480" cy="{y + 23}" r="14" fill="#D9541E" opacity="0">{opacity_anim([(4.1, 8.4)], c, 0.15)}</circle>')
            b.append(f'<text x="480" y="{y + 29}" text-anchor="middle" font-family="Geist, sans-serif" font-weight="700" font-size="17" fill="#FFFDF8" opacity="0">!{opacity_anim([(4.1, 8.4)], c, 0.15)}</text>')
            b.append(label(480, y + 64, 'flag for review', 'is-orange', 'middle', [(4.3, 8.4)], c))
    return svg(960, 360, 'Reconciliation: three deposits in the broker ledger match the PSP settlement report; the fourth is missing from the report and is flagged for review.', ''.join(b), 6)


# --------------------------------------------------------------------------- figures: MT5 latency

def fig_mt5_arch():
    c = 11
    b = []
    pings = [('M174 225C220 225 220 102 270 102', 102, '48 ms'), ('M174 235H270', 235, '142 ms'),
             ('M174 245C220 245 220 368 270 368', 368, '231 ms')]
    for p, _, _ in pings:
        b.append(f'<path class="d-line" d="{p}"/>')
    b.append('<path class="d-line" d="M450 102C495 102 495 225 540 225"/>')
    b.append('<path class="d-line" d="M450 235H540"/>')
    b.append('<path class="d-line" d="M450 368C495 368 495 245 540 245"/>')
    b.append('<path class="d-line" d="M720 225C745 225 745 172 770 172"/>')
    b.append('<path class="d-line" d="M853 204V300"/>')
    b.append('<path class="d-line" d="M630 197V116" stroke-dasharray="4 5"/>')
    b.append('<path class="d-line" d="M630 273V354" stroke-dasharray="4 5"/>')
    for p, _, _ in pings:
        b.append(packet(p, 0.3, 1.2, c, 'is-ink', 5))
    order = 'M174 225C220 225 220 102 270 102L450 102C495 102 495 225 540 225L720 225C745 225 745 172 770 172L853 172L853 300'
    fill = 'M853 300L853 172L770 172C745 172 745 225 720 225L540 225C495 225 495 102 450 102L270 102C220 102 220 225 174 225'
    b.append(packet(order, 3.0, 5.6, c))
    b.append(packet(fill, 6.0, 8.6, c, 'is-ink'))
    b.append(node(24, 197, 150, 76, 'MT5 terminal', "trader's PC", 'is-dark'))
    for y, city in [(70, 'Singapore'), (203, 'London'), (336, 'New York')]:
        b.append(node(270, y, 180, 64, city, 'access server'))
    b.append(node(540, 197, 180, 76, 'Trade server', 'orders, accounts', 'is-accent'))
    b.append(node(540, 60, 180, 56, 'History server', ''))
    b.append(node(540, 354, 180, 56, 'Backup server', ''))
    b.append(node(770, 140, 166, 64, 'Gateway', 'bridge to liquidity'))
    b.append(node(770, 300, 166, 64, 'Liquidity', 'prices and fills'))
    for _, y, ms in pings:
        b.append(label(222, y - 10 if y != 235 else 226, ms, 'is-orange' if ms == '48 ms' else '', 'middle', [(1.2, 10.4)], c))
    b.append(glow(270, 70, 180, 64, [(1.6, 10.4)], c))
    b.append(label(360, 52, 'fastest: picked', 'is-orange', 'middle', [(1.6, 10.4)], c))
    b.append(glow(540, 197, 180, 76, [(3.75, 4.35), (7.2, 7.8)], c))
    b.append(glow(770, 140, 166, 64, [(4.3, 4.8)], c))
    b.append(glow(770, 300, 166, 64, [(5.4, 6.2)], c))
    b.append(glow(24, 197, 150, 76, [(8.5, 10.2)], c))
    b.append(label(99, 300, 'filled', 'is-orange', 'middle', [(8.6, 10.4)], c))
    b.append(legend(560, 452, [('ink', 'ping and fill'), ('orange', 'order')]))
    return svg(960, 470, 'MT5 architecture: the terminal pings access servers in Singapore, London and New York and picks the fastest; the order travels through it to the trade server, gateway and liquidity provider, and the fill returns the same way.', ''.join(b), 7.4)


def fig_latency_budget():
    c = 9
    segs = [('network to access server', 45), ('access to trade server', 2), ('margin and risk checks', 1),
            ('gateway and fill', 10), ('network back', 46)]
    total = sum(ms for _, ms in segs)
    x0, width = 40, 880
    scale = width / total
    b = []
    b.append(f'<rect x="{x0}" y="110" width="{width}" height="44" rx="8" fill="#FFFDF8" stroke="#111111" stroke-width="2"/>')
    x = x0
    t = 0.4
    span = 6.0
    milestones = []
    colors = ['#D9541E', '#111111', '#7d7568', '#111111', '#D9541E']
    for i, (name, ms) in enumerate(segs):
        w = ms * scale
        t_end = t + span * ms / total
        b.append(f'<rect x="{x:.1f}" y="112" width="0" height="40" fill="{colors[i]}">'
                 f'<animate attributeName="width" dur="{c}s" repeatCount="indefinite" values="0;0;{w:.1f};{w:.1f};0" '
                 f'keyTimes="0;{t / c:.4f};{t_end / c:.4f};{8.6 / c:.4f};1"/></rect>')
        mid = x + w / 2
        if ms >= 20:
            b.append(f'<text class="d-label" x="{mid:.1f}" y="186" text-anchor="middle">{name}</text>')
            b.append(f'<text class="d-big" x="{mid:.1f}" y="226" text-anchor="middle">{ms} ms</text>')
        else:
            ly = {1: 44, 2: 66, 3: 88}[i]
            lx = {1: 520, 2: 540, 3: 560}[i]
            b.append(f'<path d="M{mid:.1f} 108V{ly + 6}H{lx}" fill="none" stroke="#7d7568" stroke-width="1.2"/>')
            b.append(f'<text class="d-label" x="{lx + 6}" y="{ly + 10}">{name}: {ms} ms</text>')
        milestones.append((t_end, sum(m for _, m in segs[:i + 1])))
        x += w
        t = t_end
    b.append(f'<text class="d-legend" x="920" y="40" text-anchor="end">TOTAL ROUND TRIP</text>')
    prev = 0
    for i, (te, ms) in enumerate([(0.4, 0)] + milestones):
        nxt = milestones[i][0] if i < len(milestones) else 8.6
        b.append(f'<text class="d-big" x="920" y="80" text-anchor="end" opacity="0" style="fill:#D9541E">{ms} ms'
                 f'{opacity_anim([(te, nxt if i < len(milestones) else 8.6)], c, 0.05)}</text>')
    return svg(960, 250, f'Latency budget of one market order, about {total} milliseconds round trip: 45 ms and 46 ms for the two network legs, 2 ms from access to trade server, 1 ms of checks and 10 ms at the gateway and liquidity provider.', ''.join(b), 7)


def fig_execution():
    c = 8
    b = []
    b.append('<path class="d-line is-ink" d="M230 180H380"/>')
    b.append('<path class="d-line" d="M580 170C640 170 650 85 700 85"/>')
    b.append('<path class="d-line" d="M580 190C640 190 650 275 700 275"/>')
    b.append(packet('M230 180H480', 0.4, 2.4, c))
    b.append(packet('M480 175H580C640 170 650 85 700 85', 2.8, 3.8, c))
    b.append(packet('M480 185H580C640 190 650 275 700 275', 2.8, 3.8, c, 'is-ink'))
    b.append(node(30, 142, 200, 76, 'Buy EURUSD', 'clicked at 1.08520', 'is-dark'))
    b.append(node(380, 142, 200, 76, 'Trade server', 'checks the price', 'is-accent'))
    b.append(node(700, 40, 240, 90, 'Instant execution', 'price moved: requote', '', 'accept 1.08523?'))
    b.append(node(700, 230, 240, 90, 'Market execution', 'filled at 1.08523', '', 'slippage 0.3 pips'))
    b.append(glow(700, 40, 240, 90, [(3.8, 7.4)], c))
    b.append(glow(700, 230, 240, 90, [(3.8, 7.4)], c))
    b.append(label(480, 64, 'MARKET PRICE', '', 'middle'))
    for t0, t1, p in [(0, 1.2, '1.08520'), (1.25, 2.0, '1.08521'), (2.05, 7.6, '1.08523')]:
        b.append(f'<text class="d-big" x="480" y="104" text-anchor="middle" opacity="0"'
                 f'{" style=&quot;fill:#D9541E&quot;" if p == "1.08523" else ""}>{p}{opacity_anim([(t0, t1)], c, 0.05)}</text>')
    return svg(960, 340, 'A buy order clicked at 1.08520 arrives after the price moved to 1.08523: instant execution sends a requote, market execution fills at 1.08523 with 0.3 pips of slippage.', ''.join(b).replace('&quot;', '"'), 5)



# --------------------------------------------------------------------------- figures: My Local Depositor

def _arrow(x1, y, x2, color='#cdc3b0'):
    d = 1 if x2 > x1 else -1
    return (f'<path d="M{x1} {y}H{x2 - 9 * d}" fill="none" stroke="{color}" stroke-width="2"/>'
            f'<path d="M{x2} {y}l{-11 * d} -6v12Z" fill="{color}"/>')


def fig_mld_sequence():
    import hashlib
    c = 15
    X = {'m': 110, 'g': 360, 'c': 610, 'b': 860}
    b = []
    heads = [('m', 'Merchant server', 'your backend', 'is-dark'), ('g', 'MLD API', 'deposits, payouts', 'is-accent'),
             ('c', 'Customer', 'browser or app', ''), ('b', 'Bank', 'collection account', '')]
    for k, _, _, _ in heads:
        b.append(f'<path d="M{X[k]} 86V560" fill="none" stroke="#cdc3b0" stroke-width="2" stroke-dasharray="5 6"/>')
    msgs = [('m', 'g', 128, 'GET /v2/quote', 0.4), ('g', 'm', 166, 'ref_no 7KQ2M9XA + bank account', 1.6),
            ('m', 'g', 210, 'POST /v2/deposits · LKR 25,000', 2.8), ('g', 'm', 248, 'checkout_url', 4.0),
            ('m', 'c', 292, 'redirect to checkout', 5.2), ('c', 'b', 336, 'bank transfer, ref 7KQ2M9XA', 6.4),
            ('c', 'g', 380, 'upload slip', 7.6), ('g', 'm', 478, 'webhook: deposit.confirmed', 10.0)]
    for f, t, y, text, t0 in msgs:
        x1, x2 = X[f], X[t]
        b.append(_arrow(x1, y, x2))
        b.append(f'<g opacity="0">{_arrow(x1, y, x2, "#111111")}{opacity_anim([(t0, c - 0.6)], c, 0.25)}</g>')
        b.append(packet(f'M{x1} {y}H{x2}', t0, t0 + 0.9, c))
        b.append(tag((x1 + x2) / 2, y - 12, text))
    # self steps
    b.append(f'<g class="d-node"><rect x="{X["g"] - 120}" y="408" width="240" height="40" rx="10"/></g>')
    b.append(f'<text class="d-label" x="{X["g"]}" y="433" text-anchor="middle">admin confirms the money arrived</text>')
    b.append(glow(X['g'] - 120, 408, 240, 40, [(8.8, 9.9)], c))
    b.append(f'<g class="d-node is-dark"><rect x="{X["m"] - 100}" y="506" width="200" height="40" rx="10"/></g>')
    b.append(f'<text class="d-label" x="{X["m"]}" y="531" text-anchor="middle" style="fill:#F3EEE3">credit LKR 25,000</text>')
    b.append(glow(X['m'] - 100, 506, 200, 40, [(11.2, 14.2)], c))
    for k, t, sub, cls in heads:
        b.append(node(X[k] - 92, 18, 184, 68, t, sub, cls))
    # deposit status
    b.append('<text class="d-legend" x="940" y="526" text-anchor="end">DEPOSIT STATUS</text>')
    for t0, t1, st, orange in [(0, 4.9, 'not created yet', False), (4.9, 8.5, 'awaiting_payment', False),
                               (8.5, 9.7, 'customer_claims_paid', False), (9.7, 14.6, 'confirmed', True)]:
        style = ' style="font-size:15px;fill:#D9541E"' if orange else ' style="font-size:15px"'
        b.append(f'<text class="d-label" x="940" y="550" text-anchor="end"{style} opacity="0">{st}{opacity_anim([(t0, t1)], c, 0.15)}</text>')
    return svg(960, 570, 'Sequence of an LKR deposit through hosted checkout: the merchant gets a quote with a reference number, creates the deposit and redirects the customer, who transfers money quoting the reference and uploads a slip; an admin confirms the payment and MLD sends a deposit.confirmed webhook so the merchant credits the wallet.', ''.join(b), 12.6)


def fig_mld_signing():
    import hashlib, hmac
    c = 10
    ts, method, path = '1795190400', 'POST', '/api/v2/deposits'
    body = '{"currency":"LKR","settlement_amount":"25000.00"}'
    bh = hashlib.sha256(body.encode()).hexdigest()
    sig = hmac.new(b'demo_signing_secret', f'{ts}.{method}.{path}.{bh}'.encode(), hashlib.sha256).hexdigest()
    parts = [(ts, 'X-Timestamp'), ('.', None), (method, 'method'), ('.', None), (path, 'path'), ('.', None),
             (bh[:10] + '…', 'sha256(body)')]
    cw = 7.9
    widths = [14 if p == '.' else len(p) * cw + 22 for p, _ in parts]
    x = (960 - sum(widths)) / 2
    b = ['<text class="d-legend" x="480" y="40" text-anchor="middle">CANONICAL STRING</text>']
    centers = []
    k = 0
    for (p, cap), w in zip(parts, widths):
        if p == '.':
            b.append(f'<text class="d-big" x="{x + w / 2:.1f}" y="100" text-anchor="middle" style="font-size:26px">.</text>')
        else:
            t0 = 0.3 + k * 0.6
            k += 1
            cx = x + w / 2
            centers.append(cx)
            b.append(f'<g opacity="0"><rect x="{x:.1f}" y="62" width="{w:.1f}" height="40" rx="9" fill="#FFFDF8" stroke="#111111" stroke-width="2"/>'
                     f'<text class="d-label" x="{cx:.1f}" y="87" text-anchor="middle" style="font-size:13px;fill:#111">{p}</text>'
                     f'<text class="d-legend" x="{cx:.1f}" y="124" text-anchor="middle">{cap}</text>'
                     f'{opacity_anim([(t0, 9.4)], c, 0.25)}</g>')
        x += w
    for cx in centers:
        d = f'M{cx:.1f} 134C{cx:.1f} 166 480 166 480 196'
        b.append(f'<path class="d-line" d="{d}"/>')
        b.append(packet(d, 2.7, 3.3, c, '', 5))
    b.append('<path class="d-line" d="M290 228H380"/><path class="d-line" d="M580 228H670"/>')
    b.append(packet('M290 228H380', 2.8, 3.3, c, 'is-ink'))
    b.append(packet('M580 228H670', 3.6, 4.1, c))
    b.append(node(60, 196, 230, 64, 'signing_secret', 'shown once in the portal', 'is-dark'))
    b.append(node(380, 196, 200, 64, 'HMAC-SHA256', 'keyed hash', 'is-accent'))
    b.append(glow(380, 196, 200, 64, [(3.2, 4.0)], c))
    b.append(f'<g opacity="0"><g class="d-node"><rect x="670" y="196" width="262" height="64" rx="14"/></g>'
             f'<text class="d-title" x="801" y="222" text-anchor="middle" style="font-size:15px">X-Client-Signature</text>'
             f'<text class="d-sub" x="801" y="243" text-anchor="middle">{sig[:22]}…</text>{opacity_anim([(4.0, 9.4)], c, 0.25)}</g>')
    d2 = 'M801 260C801 300 630 300 630 352'
    b.append(f'<path class="d-line" d="{d2}"/>')
    b.append(packet(d2, 4.5, 5.3, c))
    b.append(node(330, 324, 300, 64, 'MLD API', 'rebuilds the string and compares'))
    b.append(glow(330, 324, 300, 64, [(5.3, 9.4)], c))
    for i, (t0, text) in enumerate([(5.8, 'same signature'), (6.4, 'within 300 s of now')]):
        y = 344 + i * 28
        b.append(f'<g opacity="0"><circle cx="672" cy="{y}" r="10" fill="#111111"/>'
                 f'<path d="M667 {y}l3.5 3.5 6.5-7" fill="none" stroke="#F3EEE3" stroke-width="2.2" stroke-linecap="round"/>'
                 f'<text class="d-label" x="690" y="{y + 4}">{text}</text>{opacity_anim([(t0, 9.4)], c, 0.2)}</g>')
    b.append(f'<g opacity="0">{tag(880, 357, "201 Created")}{opacity_anim([(7.0, 9.4)], c, 0.2)}</g>')
    b.append('<text class="d-legend" x="60" y="350">otherwise 401 invalid_signature</text>')
    b.append('<text class="d-legend" x="60" y="372">or 401 stale_request</text>')
    return svg(960, 410, 'Signing a request: timestamp, method, path and a SHA-256 hash of the body are joined with dots, hashed with HMAC-SHA256 using the signing secret, and sent as X-Client-Signature; MLD rebuilds the string, checks the signature and that the timestamp is within 300 seconds, then answers 201 Created.', ''.join(b), 8)


def _state(x, y, w, h, text, cls=''):
    return (f'<g class="d-node {cls}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12"/>'
            f'<text class="d-title" x="{x + w / 2}" y="{y + h / 2 + 5}" text-anchor="middle" '
            f'style="font-family:var(--mono);font-size:14px;font-weight:500">{text}</text></g>')


def fig_mld_states():
    c = 11
    b = []
    A = (30, 150, 210, 56)
    B = (380, 150, 240, 56)
    finals = [('confirmed', 40, 'is-accent'), ('shortpaid', 108, ''), ('overpaid', 176, ''), ('rejected', 244, '')]
    b.append('<path class="d-line is-ink" d="M240 178H380"/>')
    b.append('<path d="M380 178l-11-6v12Z" fill="#111111"/>')
    for name, y, _ in finals:
        b.append(f'<path class="d-line" d="M620 178C670 178 670 {y + 24} 720 {y + 24}"/>')
    b.append('<path class="d-line" d="M135 206C135 260 105 260 105 310"/>')
    b.append('<path class="d-line" d="M135 206C135 260 285 260 285 310"/>')
    b.append('<path class="d-line" d="M500 92V150" stroke-dasharray="5 6"/>')
    b.append('<path d="M500 150l-6-11h12Z" fill="#cdc3b0"/>')
    b.append(_state(*A, 'awaiting_payment'))
    b.append(_state(*B, 'customer_claims_paid'))
    for name, y, cls in finals:
        b.append(_state(720, y, 210, 48, name, cls))
    b.append(_state(30, 310, 150, 48, 'expired', 'is-dark'))
    b.append(_state(210, 310, 150, 48, 'cancelled', 'is-dark'))
    b.append('<rect x="560" y="330" width="370" height="64" rx="12" fill="none" stroke="#cdc3b0" stroke-width="2" stroke-dasharray="6 6"/>')
    b.append('<text class="d-label" x="745" y="356" text-anchor="middle" style="fill:#111">already_approved · already_rejected</text>')
    b.append('<text class="d-legend" x="745" y="377" text-anchor="middle">a duplicate, closed (see duplicate_of)</text>')
    b.append(tag(310, 160, 'slip uploaded'))
    b.append(tag(500, 82, 'host-to-host starts here'))
    b.append('<text class="d-legend" x="135" y="138" text-anchor="middle">hosted checkout starts here</text>')
    b.append('<text class="d-legend" x="500" y="236" text-anchor="middle">admin review</text>')
    b.append('<text class="d-legend" x="60" y="276" text-anchor="middle">1 hour, unpaid</text>')
    b.append('<text class="d-legend" x="330" y="276" text-anchor="middle">POST …/cancel</text>')
    # glows
    b.append(glow(*A, [(0.3, 1.6), (6.4, 7.0)], c))
    b.append(glow(*B, [(2.2, 3.9)], c))
    b.append(glow(720, 40, 210, 48, [(4.5, 6.1)], c))
    b.append(glow(30, 310, 150, 48, [(7.6, 10.4)], c))
    # happy path marker
    path = 'M135 150H500C640 150 640 40 825 40'
    _, kt = _kt([(0, 0), (1.4, 0), (2.2, 0.5), (3.9, 0.5), (4.5, 1), (c, 1)], c)
    vals, _ = _kt([(0, 0), (1.4, 0), (2.2, 0.5), (3.9, 0.5), (4.5, 1), (c, 1)], c)
    b.append(f'<circle class="d-dot" r="9" opacity="0"><animateMotion dur="{c}s" repeatCount="indefinite" calcMode="linear" '
             f'path="{path}" keyPoints="{vals}" keyTimes="{kt}"/>{opacity_anim([(0.2, 6.1)], c, 0.15)}</circle>')
    path2 = 'M135 206C135 260 105 260 105 310'
    vals2, kt2 = _kt([(0, 0), (6.9, 0), (7.6, 1), (c, 1)], c)
    b.append(f'<circle class="d-dot is-ink" r="9" opacity="0"><animateMotion dur="{c}s" repeatCount="indefinite" calcMode="linear" '
             f'path="{path2}" keyPoints="{vals2}" keyTimes="{kt2}"/>{opacity_anim([(6.4, 10.4)], c, 0.15)}</circle>')
    return svg(960, 410, 'Deposit statuses: awaiting_payment moves to customer_claims_paid when a slip is uploaded, then admin review ends it as confirmed, shortpaid, overpaid or rejected. An unpaid deposit expires after one hour or can be cancelled. Host-to-host deposits start at customer_claims_paid. Duplicates close as already_approved or already_rejected.', ''.join(b), 5)


def mini_mld():
    c = 7
    xs = [14, 110, 206, 302]
    b = ['<path class="d-line" d="M56 80H248"/>', '<path class="d-line is-ink" d="M248 164H344"/>']
    b.append(packet('M56 80H248', 0.3, 2.3, c))
    b.append(packet('M248 164H344', 3.0, 3.8, c, 'is-ink'))
    for x, t in zip(xs, ['Payer', 'Bank', 'MLD', 'Broker']):
        b.append(node(x, 96, 84, 52, t, '', 'is-accent' if t == 'MLD' else ('is-dark' if t == 'Payer' else '')))
    b.append(label(152, 66, 'ref 7KQ2M9XA', 'is-orange'))
    b.append(label(296, 190, 'webhook'))
    b.append(label(200, 216, 'awaiting_payment', '', 'middle', [(0, 3.6)], c))
    b.append(label(200, 216, 'confirmed', 'is-orange', 'middle', [(3.6, 6.6)], c))
    return svg(400, 240, 'A bank transfer with a reference number reaches MLD, which confirms it and sends a webhook to the broker.', ''.join(b), 4)


# --------------------------------------------------------------------------- figures: FinTruvix + Fincashier

def _box(x, y, w, h, fill='#FFFDF8', stroke='#111111', sw=2, rx=12):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def _show(x, y, text, t0, c, cls='d-big', style='', anchor='start', end=None):
    end = end if end is not None else c - 0.5
    return (f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}" style="{style}" opacity="0">'
            f'{text}{opacity_anim([(t0, end)], c, 0.2)}</text>')


def fig_ft_custody():
    c = 8
    b = []
    p1 = 'M260 76C318 76 310 198 365 198'
    b.append(f'<path class="d-line" d="{p1}"/>')
    b.append('<path class="d-line" d="M595 198H720"/>')
    b.append('<path class="d-line" d="M480 246V300" stroke-dasharray="5 6"/>')
    b.append(packet(p1, 0.3, 1.2, c, 'is-ink', 6))
    b.append(packet(p1, 2.4, 3.2, c))
    b.append(packet('M595 198H720', 3.5, 4.2, c))
    b.append(node(30, 40, 230, 72, 'Strategist’s account', 'MT5 · read-only', 'is-dark'))
    b.append(node(365, 150, 230, 96, 'FinTruvix', 'Passport · Trust Score', 'is-accent', 'copy engine'))
    b.append(node(720, 150, 216, 96, 'Follower’s account', 'cTrader', '', 'trade-enabled'))
    b.append(node(365, 300, 230, 64, 'Wallet', 'top-ups and earnings only'))
    b.append(glow(365, 150, 230, 96, [(1.1, 1.8), (3.1, 3.6)], c))
    b.append(glow(720, 150, 216, 96, [(4.1, 5.4)], c))
    b.append(tag(150, 140, 'read-only: proves the track record'))
    b.append(tag(657, 178, 'copied order'))
    b.append(label(480, 136, 'track record updated', 'is-orange', 'middle', [(1.3, 2.3)], c))
    b.append(label(480, 136, 'strategist opens a trade', '', 'middle', [(2.4, 3.4)], c))
    b.append(label(828, 274, 'capital stays here', 'is-orange'))
    b.append(legend(40, 376, [('ink', 'trade data read'), ('orange', 'a new trade and its copy')]))
    return svg(960, 392, 'FinTruvix connections: the strategist’s MT5 account is read-only and feeds the track record; when the strategist trades, FinTruvix places a copied order in the follower’s trade-enabled cTrader account, where the capital stays. FinTruvix itself holds only a wallet for top-ups and earnings.', ''.join(b), 4.6)


def fig_ft_fanout():
    c = 9
    ys = [24, 108, 192, 276]
    rows = [('Follower A', 'lot multiplier 0.5×', '0.50 lot', ''), ('Follower B', 'fixed lot', '0.10 lot', ''),
            ('Follower C', 'equity $2,000 vs $20,000', '0.10 lot', ''), ('Follower D', 'daily loss limit reached', 'paused', 'is-ink')]
    b = ['<path class="d-line is-ink" d="M224 210H300"/>']
    for y in ys:
        b.append(f'<path class="d-line" d="M530 210C585 210 585 {y + 33} 640 {y + 33}"/>')
    b.append(packet('M224 210H300', 0.3, 1.0, c))
    for y, (_, _, _, cls) in zip(ys, rows):
        b.append(packet(f'M530 210C585 210 585 {y + 33} 640 {y + 33}', 3.0, 3.7, c, cls))
    b.append(node(24, 168, 200, 84, 'Strategist', 'buys 1.00 lot EURUSD', 'is-dark'))
    b.append(_box(300, 120, 230, 180, '#D9541E', '#111111', 2, 14))
    b.append('<text class="d-title" x="415" y="158" text-anchor="middle" style="fill:#FFFDF8">Copy engine</text>')
    for i, (text, t0, t1) in enumerate([('01 size per follower', 1.1, 1.9), ('02 run risk checks', 1.9, 2.7), ('03 place in parallel', 2.7, 3.8)]):
        y = 200 + i * 30
        b.append(f'<text class="d-label" x="328" y="{y}" style="fill:#FFFDF8;font-size:13px" opacity="0.55">{text}</text>')
        b.append(f'<text class="d-label" x="328" y="{y}" style="fill:#FFFDF8;font-size:13px;font-weight:600" opacity="0">{text}{opacity_anim([(t0, t1)], c, 0.1)}</text>')
    b.append(glow(300, 120, 230, 180, [(1.0, 3.8)], c))
    for y, (name, rule, result, cls) in zip(ys, rows):
        b.append(_box(640, y, 296, 66))
        b.append(f'<text class="d-title" x="660" y="{y + 29}" style="font-size:16px">{name}</text>')
        b.append(f'<text class="d-sub" x="660" y="{y + 49}">{rule}</text>')
        color = '#7d7568' if cls else '#D9541E'
        b.append(_show(916, y + 44, result, 3.7, c, 'd-big', f'font-size:26px;fill:{color}', 'end', 8.6))
    b.append(label(788, 366, 'all placed at the same moment', 'is-orange', 'middle', [(3.7, 8.6)], c))
    return svg(960, 380, 'The copy engine turns one strategist trade of 1.00 lot into a sized order per follower: 0.50 lot with a 0.5 multiplier, 0.10 lot fixed, 0.10 lot proportional to equity, and none for a follower paused by the daily loss limit. All orders are placed at once.', ''.join(b), 6)


def fig_ft_trust():
    c = 10
    comps = [('Profit factor', 25, 92), ('Risk-adjusted return', 20, 85), ('Drawdown management', 20, 95),
             ('Win rate', 15, 80), ('Reward to risk', 10, 90), ('Longevity', 10, 100)]
    P = sum(w * s for _, w, s in comps) / 100
    I = 60
    t1 = 0.6 * P + 0.4 * I
    cap = I + 15
    T = min(t1, cap)
    b = ['<text class="d-legend" x="40" y="40">PERFORMANCE, P</text>']
    for i, (name, w, sc) in enumerate(comps):
        y = 74 + i * 46
        t0 = 0.4 + i * 0.45
        b.append(f'<text class="d-label" x="40" y="{y + 5}" style="fill:#111">{name}</text>')
        b.append(f'<text class="d-legend" x="40" y="{y + 22}">weight {w}%</text>')
        b.append(_box(220, y - 6, 220, 16, '#FFFDF8', '#cdc3b0', 1.5, 8))
        b.append(f'<rect x="220" y="{y - 6}" width="0" height="16" rx="8" fill="#111111"><animate attributeName="width" dur="{c}s" '
                 f'repeatCount="indefinite" values="0;0;{sc * 2.2:.0f};{sc * 2.2:.0f};0" '
                 f'keyTimes="0;{t0 / c:.4f};{(t0 + 0.6) / c:.4f};{9.5 / c:.4f};1"/></rect>')
        b.append(_show(452, y + 6, str(sc), t0 + 0.5, c, 'd-label', 'fill:#111', 'start', 9.5))
    b.append('<text class="d-legend" x="40" y="366">copier profitability and consistency: 0%, not measured yet</text>')
    b.append('<path class="d-line" d="M520 40V380"/>')
    b.append(_show(560, 76, f'P = {P:.0f}', 3.4, c, end=9.5))
    b.append(_show(560, 98, 'from the six scores', 3.5, c, 'd-legend', end=9.5))
    b.append(_show(780, 76, f'I = {I}', 4.1, c, end=9.5))
    b.append(_show(780, 98, 'one open complaint', 4.2, c, 'd-legend', end=9.5))
    b.append('<text class="d-label" x="560" y="152" style="fill:#111;font-size:14px">T = min(0.6·P + 0.4·I, I + 15)</text>')
    b.append(_show(560, 198, f'0.6 × {P:.0f} + 0.4 × {I} = {t1:.0f}', 5.0, c, 'd-label', 'font-size:15px;fill:#111', end=9.5))
    b.append(_show(560, 232, f'{I} + 15 = {cap}', 5.8, c, 'd-label', 'font-size:15px;fill:#111', end=9.5))
    b.append(_show(560, 312, f'Trust = {T:.0f}', 6.6, c, 'd-big', 'font-size:56px;fill:#D9541E', end=9.5))
    b.append(_show(560, 346, 'the smaller one wins: integrity caps the score', 7.0, c, 'd-label', 'fill:#D9541E', end=9.5))
    return svg(960, 392, f'Trust Score example: six performance scores weighted into P = {P:.0f}, integrity I = {I}. The formula min(0.6 P + 0.4 I, I + 15) gives min({t1:.0f}, {cap}), so the Trust Score is {T:.0f}, capped by integrity.', ''.join(b), 8.5)


def fig_fc_routes():
    c = 9.6
    psps = ['Stripe', 'Adyen', 'Checkout.com', 'Nuvei', 'BitPay']
    ys = [30, 100, 170, 240, 310]
    pays = [('€25 · card · Germany', 1, 0.3), ('$40 · card · USA', 0, 3.4), ('50 USDT · crypto', 4, 6.5)]
    b = ['<path class="d-line is-ink" d="M204 208H300"/>']
    for y in ys:
        b.append(f'<path class="d-line" d="M510 208C575 208 575 {y + 26} 640 {y + 26}"/>')
    over = []
    for text, k, t0 in pays:
        y = ys[k]
        b.append(packet('M204 208H300', t0, t0 + 0.8, c))
        b.append(packet(f'M510 208C575 208 575 {y + 26} 640 {y + 26}', t0 + 1.1, t0 + 1.9, c))
        over.append(f'<g opacity="0">{tag(114, 148, text)}{opacity_anim([(t0 - 0.1, t0 + 2.7)], c, 0.15)}</g>')
        over.append(glow(640, y, 200, 52, [(t0 + 1.9, t0 + 2.8)], c))
        over.append(label(852, y + 31, 'approved', 'is-orange', 'start', [(t0 + 1.9, t0 + 2.8)], c))
    b.append(node(24, 168, 180, 80, 'Merchant', 'one integration', 'is-dark'))
    b.append(node(300, 140, 210, 136, 'Fincashier', 'routing, failover', 'is-accent', 'credential vault'))
    for y, name in zip(ys, psps):
        b.append(node(640, y, 200, 52, name, ''))
    b.append(glow(300, 140, 210, 136, [(t0 + 0.8, t0 + 1.2) for _, _, t0 in pays], c))
    b += over
    return svg(960, 380, 'Payment orchestration: the merchant integrates once with Fincashier, which routes each payment to a different provider: a euro card payment from Germany to Adyen, a dollar card payment from the USA to Stripe, and a USDT crypto payment to BitPay.', ''.join(b), 2.6)


def fig_fc_scores():
    c = 8.4
    rows = [('Stripe', '94.1%', '2.9%', '310 ms'), ('Adyen', '96.8%', '3.1%', '280 ms'), ('Checkout.com', '95.2%', '2.6%', '350 ms')]
    hx = [130, 420, 600, 770]
    b = []
    for i in range(3):
        b.append(_box(100, 108 + i * 58, 760, 48, '#FFFDF8', '#111111', 1.5, 10))
    b.append(f'<rect x="345" y="70" width="150" height="214" rx="12" fill="#D9541E" fill-opacity="0.13" stroke="#D9541E" stroke-width="2" opacity="0">{opacity_anim([(0.4, 3.9)], c)}</rect>')
    b.append(f'<rect x="535" y="70" width="130" height="214" rx="12" fill="#D9541E" fill-opacity="0.13" stroke="#D9541E" stroke-width="2" opacity="0">{opacity_anim([(4.4, 7.9)], c)}</rect>')
    for x, h in zip(hx, ['PSP', 'APPROVAL RATE', 'FEE', 'LATENCY']):
        b.append(f'<text class="d-legend" x="{x}" y="94" text-anchor="{"start" if x == 130 else "middle"}">{h}</text>')
    for i, (name, ap, fee, lat) in enumerate(rows):
        y = 108 + i * 58
        b.append(f'<text class="d-title" x="130" y="{y + 30}" style="font-size:16px">{name}</text>')
        for x, v in zip(hx[1:], (ap, fee, lat)):
            b.append(f'<text class="d-label" x="{x}" y="{y + 29}" text-anchor="middle" style="font-size:14px;fill:#111">{v}</text>')
    b.append(glow(100, 166, 760, 48, [(1.2, 3.9)], c))
    b.append(glow(100, 224, 760, 48, [(5.2, 7.9)], c))
    b.append(f'<g opacity="0">{tag(100, 40, "strategy: performance", "start")}{opacity_anim([(0.2, 3.9)], c)}</g>')
    b.append(f'<g opacity="0">{tag(100, 40, "strategy: cost", "start")}{opacity_anim([(4.2, 7.9)], c)}</g>')
    b.append(label(480, 318, 'routed to Adyen: highest approval rate', 'is-orange', 'middle', [(1.3, 3.9)], c))
    b.append(label(480, 318, 'routed to Checkout.com: lowest fee', 'is-orange', 'middle', [(5.3, 7.9)], c))
    b.append('<g transform="translate(850 36)"><circle r="9" fill="none" stroke="#cdc3b0" stroke-width="2.5"/>'
             '<path d="M0 -9A9 9 0 0 1 9 0" fill="none" stroke="#D9541E" stroke-width="2.5" stroke-linecap="round">'
             '<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="1.6s" repeatCount="indefinite"/></path></g>')
    b.append('<text class="d-legend" x="832" y="40" text-anchor="end">stats refresh every 60 s</text>')
    return svg(960, 340, 'Routing scoreboard with example numbers for Stripe, Adyen and Checkout.com. With the performance strategy the router picks Adyen for its 96.8% approval rate; with the cost strategy it picks Checkout.com for its 2.6% fee.', ''.join(b), 2.5)


def fig_fc_cascade():
    c = 9
    b = ['<path class="d-line" d="M214 90H750"/>', '<path class="d-line" d="M119 130V230"/>']
    psps = [('Stripe', 290, 'declined (soft)', False, 1.0), ('Adyen', 520, 'timeout', False, 2.5), ('Checkout.com', 750, 'approved', True, 4.0)]
    b.append(packet('M214 90H385', 0.3, 1.0, c))
    b.append(packet('M385 90H615', 1.8, 2.5, c))
    b.append(packet('M615 90H845', 3.3, 4.0, c))
    for k, t in enumerate([1.3, 2.8, 4.3]):
        b.append(packet('M119 130V230', t, t + 0.5, c, 'is-ink' if k < 2 else '', 6))
    b.append(node(24, 50, 190, 80, 'Fincashier', 'session ses_9f2a', 'is-accent'))
    b.append(node(24, 230, 190, 76, 'Merchant server', 'receives webhooks', 'is-dark'))
    for i, (name, x, res, ok, t) in enumerate(psps):
        b.append(f'<text class="d-legend" x="{x + 95}" y="38" text-anchor="middle">attempt {i + 1}</text>')
        b.append(node(x, 50, 190, 80, name, ''))
        b.append(glow(x, 50, 190, 80, [(t - 0.1, t + 0.7)], c))
        col = '#D9541E' if ok else '#111111'
        if ok:
            icon = f'<path d="M{x + 24.5} 160l4 4 7.5-8" fill="none" stroke="#FFFDF8" stroke-width="2.4" stroke-linecap="round"/>'
        else:
            icon = f'<path d="M{x + 26} 156l8 8m0 -8l-8 8" fill="none" stroke="#FFFDF8" stroke-width="2.2" stroke-linecap="round"/>'
        b.append(f'<g opacity="0"><circle cx="{x + 30}" cy="160" r="11" fill="{col}"/>{icon}'
                 f'<text class="d-label" x="{x + 50}" y="165" style="font-size:13px;fill:{col}">{res}</text>'
                 f'{opacity_anim([(t, 8.6)], c, 0.15)}</g>')
    b.append('<rect x="250" y="206" width="690" height="116" rx="12" fill="#FFFDF8" stroke="#cdc3b0" stroke-width="2" stroke-dasharray="6 6"/>')
    b.append('<text class="d-legend" x="274" y="232">WEBHOOK EVENTS</text>')
    for i, (ev, note, t, ok) in enumerate([('session.rerouted', 'stripe: soft decline', 1.8, False),
                                           ('session.rerouted', 'adyen: timeout', 3.3, False),
                                           ('session.approved', 'checkout.com', 4.8, True)]):
        y = 262 + i * 24
        b.append(f'<g opacity="0"><text class="d-label" x="274" y="{y}" style="font-size:13px;fill:{"#D9541E" if ok else "#111"}">{ev}</text>'
                 f'<text class="d-legend" x="460" y="{y}">{note}</text>{opacity_anim([(t, 8.6)], c, 0.15)}</g>')
    return svg(960, 340, 'Failover cascade: Stripe gives a soft decline, Adyen times out, Checkout.com approves. Fincashier sends the merchant two session.rerouted webhooks and then session.approved.', ''.join(b), 6)


def mini_ft():
    c = 6
    ys = [30, 100, 170]
    b = ['<path class="d-line is-ink" d="M120 120H150"/>']
    for y in ys:
        b.append(f'<path class="d-line" d="M246 120C268 120 268 {y + 20} 290 {y + 20}"/>')
        b.append(packet(f'M246 120C268 120 268 {y + 20} 290 {y + 20}', 1.6, 2.4, c))
    b.append(packet('M120 120H150', 0.4, 1.1, c))
    b.append(node(10, 92, 110, 56, 'Strategist', '', 'is-dark'))
    b.append(node(150, 92, 96, 56, 'Engine', '', 'is-accent'))
    for y, t in zip(ys, ['0.50 lot', '0.10 lot', '0.10 lot']):
        b.append(node(290, y, 100, 40, t, ''))
        b.append(glow(290, y, 100, 40, [(2.4, 3.6)], c))
    b.append(glow(150, 92, 96, 56, [(1.1, 1.8)], c))
    b.append(label(200, 228, 'one trade, many accounts'))
    return svg(400, 240, 'One strategist trade goes through the engine and becomes three sized orders at once.', ''.join(b), 3)


def mini_fc():
    c = 7.5
    ys = [36, 102, 168]
    b = ['<path class="d-line is-ink" d="M104 122H140"/>']
    for y in ys:
        b.append(f'<path class="d-line" d="M240 122C263 122 263 {y + 20} 286 {y + 20}"/>')
    for k, t0 in [(1, 0.3), (0, 2.6), (2, 4.9)]:
        y = ys[k]
        b.append(packet('M104 122H140', t0, t0 + 0.5, c))
        b.append(packet(f'M240 122C263 122 263 {y + 20} 286 {y + 20}', t0 + 0.7, t0 + 1.3, c))
    b.append(node(14, 96, 90, 52, 'Shop', '', 'is-dark'))
    b.append(node(140, 96, 100, 52, 'Router', '', 'is-accent'))
    for (y, t), (k, t0) in zip(zip(ys, ['Stripe', 'Adyen', 'BitPay']), [(0, 2.6), (1, 0.3), (2, 4.9)]):
        b.append(node(286, y, 100, 40, t, ''))
        b.append(glow(286, y, 100, 40, [(t0 + 1.3, t0 + 2.1)], c))
    b.append(label(200, 228, 'best provider per payment'))
    return svg(400, 240, 'A router sends each payment to a different provider.', ''.join(b), 1.8)

# --------------------------------------------------------------------------- mini art for the listing

def mini_trading():
    c = 6
    b = ['<path class="d-line is-ink" d="M110 120H290"/>', '<path class="d-flow is-ink is-reverse" d="M110 140H290"/>']
    b.append(packet('M70 112H330', 0.4, 2.8, c))
    b.append(node(20, 86, 100, 56, 'Trader', '', 'is-dark'))
    b.append(node(150, 86, 100, 56, 'MT5', '', 'is-accent'))
    b.append(node(280, 86, 100, 56, 'Liquidity', ''))
    b.append(glow(150, 86, 100, 56, [(1.1, 1.8)], c))
    b.append(glow(280, 86, 100, 56, [(2.6, 3.4)], c))
    b.append(label(200, 196, 'orders out, prices back'))
    return svg(400, 240, 'Orders flow from trader to MT5 to liquidity, prices flow back.', ''.join(b), 2)


def mini_psp():
    c = 6
    xs = [14, 110, 206, 302]
    b = ['<path class="d-line" d="M50 92H350"/>', '<path class="d-line is-ink" d="M50 152H350"/>']
    b.append(packet('M50 92H350', 0.3, 2.3, c))
    b.append(packet('M350 152H50', 2.8, 4.8, c, 'is-ink'))
    for x, t in zip(xs, ['You', 'PSP', 'Bank', 'Issuer']):
        b.append(node(x, 96, 84, 52, t, '', 'is-accent' if t == 'PSP' else ('is-dark' if t == 'You' else '')))
    b.append(label(200, 74, 'authorize $100', 'is-orange'))
    b.append(label(200, 182, 'approved'))
    return svg(400, 240, 'A payment request travels to the issuer and the approval comes back.', ''.join(b), 2)


def mini_mt5():
    c = 6
    b = []
    for y in (50, 120, 190):
        b.append(f'<path class="d-line" d="M110 120C150 120 150 {y} 190 {y}"/>')
        b.append(packet(f'M110 120C150 120 150 {y} 190 {y}', 0.3, 1.2, c, 'is-ink', 5))
    b.append(node(14, 92, 96, 56, 'Terminal', '', 'is-dark'))
    for y, t in [(28, '48 ms'), (98, '142 ms'), (168, '231 ms')]:
        b.append(node(190, y, 110, 44, t, ''))
    b.append(glow(190, 28, 110, 44, [(1.5, 5.6)], c))
    b.append('<path class="d-line" d="M300 50H340V120"/>')
    b.append(packet('M300 50H340V120', 2.0, 3.0, c))
    b.append(node(316, 120, 72, 44, 'Server', '', 'is-accent'))
    return svg(400, 240, 'The terminal pings three access servers and connects through the fastest.', ''.join(b), 2)


# --------------------------------------------------------------------------- page chrome

FONTS = 'https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500&family=Instrument+Serif:ital@0;1&display=swap'


def page(title, desc, body, defs=False):
    pin_defs = '''  <!-- shared gradients for the Tackit-style pins on the sticky notes -->
  <svg class="svg-defs" aria-hidden="true" focusable="false">
    <defs>
      <radialGradient id="pin-ball" cx="0.36" cy="0.32" r="0.72">
        <stop offset="0" stop-color="#f6d4c7"/><stop offset="0.45" stop-color="#d9541e"/><stop offset="1" stop-color="#8f3110"/>
      </radialGradient>
      <linearGradient id="pin-steel" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stop-color="#f3f4f6"/><stop offset="0.5" stop-color="#a1a7b0"/><stop offset="1" stop-color="#525a66"/>
      </linearGradient>
    </defs>
  </svg>
''' if defs else ''
    e = html.escape
    return f'''<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)}</title>
  <meta name="description" content="{e(desc)}">
  <meta name="theme-color" content="#F3EEE3">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{e(title)}">
  <meta property="og:description" content="{e(desc)}">
  <meta property="og:image" content="https://azharadhly.github.io/portfolio/assets/img/profile/og-image.jpg">

  <link rel="icon" href="assets/img/favicon-48.png" sizes="48x48" type="image/png">
  <link rel="icon" href="assets/img/favicon-32.png" sizes="32x32" type="image/png">
  <link rel="apple-touch-icon" href="assets/img/apple-touch-icon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="{FONTS}" rel="stylesheet">
  <link href="assets/vendor/bootstrap-icons/bootstrap-icons.min.css" rel="stylesheet">
  <link href="assets/css/style.css" rel="stylesheet">
  <script>document.documentElement.classList.add('js');</script>
</head>

<body id="top">
  <a class="skip-link" href="#main">Skip to content</a>
{pin_defs}
  <header class="site-header">
    <div class="container nav">
      <a class="brand" href="index.html" aria-label="Adhly Azhar, home">
        <span>Adhly Azhar</span>
      </a>

      <nav id="site-menu" class="nav-links" aria-label="Main">
        <a href="index.html#work">Work Log</a>
        <a href="index.html#services">Toolkit</a>
        <a href="index.html#about">Bio</a>
        <a href="notebook.html" class="is-active" aria-current="page">Notebook</a>
        <a href="index.html#contact">Ping me</a>
        <a class="only-mobile" href="assets/resume/adhly-azhar-resume.pdf" download>Download résumé</a>
      </nav>

      <div class="nav-actions">
        <button class="sound-toggle" type="button" data-sound-toggle data-on="Pause music" data-off="Play music"
          aria-pressed="false" aria-label="Background music" title="Play music">
          <span class="eq" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
        </button>
        <a class="btn btn-ink btn-sm" href="index.html#contact">Let’s talk</a>
        <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-menu" aria-label="Open menu">
          <i class="bi bi-list" aria-hidden="true"></i><i class="bi bi-x-lg" aria-hidden="true"></i>
        </button>
      </div>
    </div>
  </header>

  <main id="main">
{body}
  </main>

  <footer class="site-footer">
    <div class="container footer-inner">
      <p>© <span data-year>2026</span> Adhly Azhar</p>
      <nav aria-label="Footer">
        <a href="index.html#work">Work Log</a>
        <a href="index.html#services">Toolkit</a>
        <a href="index.html#about">Bio</a>
        <a href="notebook.html">Notebook</a>
        <a href="index.html#contact">Ping me</a>
      </nav>
      <a class="footer-kofi" href="https://ko-fi.com/adhlyazhar" target="_blank" rel="noopener"><i class="bi bi-cup-hot" aria-hidden="true"></i> Buy me a coffee</a>
      <a class="to-top" href="#top">Back to top <i class="bi bi-arrow-up" aria-hidden="true"></i></a>
    </div>
    <div class="footer-mast" aria-hidden="true">Adhly Azhar</div>
  </footer>

  <script src="assets/js/site.js" defer></script>
  <script src="assets/js/sound.js" defer></script>
</body>

</html>
'''


def figure(n, svg_markup, caption):
    return f'''        <figure class="fig reveal">
          <div class="fig-stage">{svg_markup}</div>
          <figcaption><span class="fig-num">Fig. {n:02d}</span><span>{caption}<span class="fig-hint">Swipe sideways to see the whole diagram.</span></span></figcaption>
        </figure>
'''


def words(s):
    s = re.sub(r'<svg.*?</svg>', ' ', s, flags=re.S)
    return len(re.sub(r'<[^>]+>', ' ', s).split())


NOTES = [
    {
        'file': 'how-copy-trading-works.html',
        'num': '05', 'topic': 'Trading', 'eyebrow': 'Trading · Copy trading', 'new': True,
        'title': 'How cross-broker copy trading works',
        'h1': 'How cross-broker <span>copy trading</span> works',
        'card': 'One trade copied into many broker accounts at once: the Trader Passport, the Trust Score formula and the copy engine behind FinTruvix.',
        'lead': 'Copy trading sounds simple: when a strategist trades, followers trade too. The hard parts are deciding whom to trust and placing hundreds of orders at once, inside other people’s broker accounts. FinTruvix builds its whole platform around those two problems.',
        'meta_topic': 'Copy trading and trust',
        'mini': mini_ft,
        'source': ('FinTruvix website', 'https://fintruvix.com/'),
    },
    {
        'file': 'how-payment-orchestration-works.html',
        'num': '06', 'topic': 'Payments', 'eyebrow': 'Payments · Orchestration', 'new': True,
        'title': 'How payment orchestration works',
        'h1': 'How payment <span>orchestration</span> works',
        'card': 'One API in front of many payment providers: smart routing, failover cascades and webhooks, read from the Fincashier site and developer docs.',
        'lead': 'A business that takes payments in many countries ends up with many payment providers, each with its own API, fees and approval rates. An orchestration layer such as Fincashier sits in front of all of them: the business integrates once, and the platform decides where each payment goes.',
        'meta_topic': 'Routing across PSPs',
        'mini': mini_fc,
    },
    {
        'file': 'how-local-deposit-gateways-work.html',
        'num': '04', 'topic': 'Payments', 'eyebrow': 'Payments · Local deposits',
        'title': 'How a local deposit gateway works',
        'h1': 'How a local <span>deposit gateway</span> works',
        'card': 'Bank transfers turned into an API: reference numbers, slips, signed requests and webhooks, read from the My Local Depositor docs.',
        'lead': 'Not every customer pays by card. Many send a local bank transfer, and someone then has to match each transfer to the right person. My Local Depositor (MLD) turns that whole job into an API. Here is how version 2 of it fits together.',
        'meta_topic': 'Bank deposits and payouts',
        'mini': mini_mld,
    },
    {
        'file': 'how-trading-platforms-work.html',
        'num': '01', 'topic': 'Trading', 'eyebrow': 'Trading · Brokerage',
        'title': 'How a trading platform works',
        'h1': 'How a trading <span>platform</span> works',
        'card': 'The systems behind a forex broker, how a deposit turns into a trade, and what A-book and B-book really mean.',
        'lead': 'To a trader, a broker is one app. Underneath, it is a handful of separate systems passing messages: a client portal, a back office, a payment provider, the MetaTrader 5 trading server and a liquidity provider. Here is what each one does and how they talk.',
        'meta_topic': 'Forex and CFD brokers',
        'mini': mini_trading,
    },
    {
        'file': 'how-payment-providers-work.html',
        'num': '02', 'topic': 'Payments', 'eyebrow': 'Payments · PSP',
        'title': 'How a payment provider works',
        'h1': 'How a <span>payment provider</span> works',
        'card': 'What happens in the seconds after you tap Deposit, why webhooks arrive twice, and how reconciliation catches the gaps.',
        'lead': 'When a trader taps Deposit, the money passes through four or five companies in a second or two. A payment service provider, or PSP, hides all of them behind one checkout and one API.',
        'meta_topic': 'Deposits and payouts',
        'mini': mini_psp,
    },
    {
        'file': 'mt5-latency-engine.html',
        'num': '03', 'topic': 'MetaTrader 5', 'eyebrow': 'Trading · MetaTrader 5',
        'title': "Inside MT5's latency engine",
        'h1': "Inside MT5’s <span>latency engine</span>",
        'card': 'Access servers, ping, gateways and slippage: how MetaTrader 5 gets an order filled in milliseconds.',
        'lead': 'In a fast market, a quote can be out of date within milliseconds. MetaTrader 5 is built as a network of servers whose main job is to keep the trip from click to fill short.',
        'meta_topic': 'Latency and execution',
        'mini': mini_mt5,
    },
]

# --------------------------------------------------------------------------- article bodies

BODY = {}

BODY['how-trading-platforms-work.html'] = lambda: f'''
        <div class="prose reveal">
          <h2><span class="h-num">01</span>The parts of a broker</h2>
          <p>Every forex or CFD broker runs some version of the same stack. The names change, the jobs don’t.</p>
          <ul>
            <li><strong>Client portal.</strong> The website or app where people sign up, upload documents, deposit, withdraw and open trading accounts. It is the front door and holds no trading logic itself.</li>
            <li><strong>Back office (CRM).</strong> The broker’s source of truth for people and money: KYC status, wallets, transactions, partners and staff permissions.</li>
            <li><strong>Payment provider (PSP).</strong> Moves real money in and out through cards, bank transfers, e-wallets and crypto, and tells the back office when a payment succeeds. <a class="link-arrow" href="how-payment-providers-work.html">Note 02</a> covers this.</li>
            <li><strong>MT5 trade server.</strong> Holds trading accounts, balances and open positions, streams prices and executes orders. Traders reach it through the MetaTrader 5 terminal.</li>
            <li><strong>Liquidity provider.</strong> Banks and prime brokers that supply prices and take the other side of the trades a broker passes on.</li>
          </ul>
        </div>
{figure(1, fig_broker_stack(), 'A deposit (orange) goes from the portal to the PSP and the back office, which credits the MT5 account. An order (black) goes from the terminal to the trade server and on to liquidity, while prices stream back.')}
        <div class="prose reveal">
          <h2><span class="h-num">02</span>How the systems talk</h2>
          <p>The back office and MT5 don’t share a database. They talk through the <strong>MT5 Manager API</strong>. When a deposit clears, the back office calls the API to credit the trading account. When a client opens a new account, it creates the account and sets its group and leverage.</p>
          <p>Prices travel the other way. Liquidity providers stream quotes through a <strong>bridge</strong> or gateway into the trade server, which applies the broker’s spread and pushes them to every connected terminal many times a second.</p>
          <div class="callout"><strong>Why two balances?</strong>A client usually has a wallet in the back office and a separate balance inside each MT5 account. Moving money between them is an internal transfer, which is how one deposit can fund several trading accounts.</div>

          <h2><span class="h-num">03</span>The life of a trade</h2>
          <ol>
            <li><strong>Sign up and KYC.</strong> Identity documents are checked before any money moves.</li>
            <li><strong>Deposit.</strong> The PSP charges the card and confirms the payment to the back office.</li>
            <li><strong>Fund the trading account.</strong> The back office credits the MT5 account through the Manager API.</li>
            <li><strong>Open a position.</strong> The trader buys 1 lot of EURUSD in the terminal. The trade server checks the margin first.</li>
            <li><strong>The market moves.</strong> Floating profit and loss update with every price tick.</li>
            <li><strong>Close.</strong> The realized profit or loss is added to the MT5 balance.</li>
            <li><strong>Withdraw.</strong> Money goes back to the wallet, then out through the PSP after a review.</li>
          </ol>
        </div>
{figure(2, fig_trade_life(), 'Seven steps across four systems. Only steps 04 to 06 happen inside MT5.')}
        <div class="prose reveal">
          <h2><span class="h-num">04</span>A-book and B-book</h2>
          <p>When an order reaches the trade server, the broker’s routing rules decide where the risk goes.</p>
          <ul>
            <li><strong>A-book.</strong> The order is passed to a liquidity provider. The broker earns the spread or a commission and carries no market risk.</li>
            <li><strong>B-book.</strong> The broker keeps the order in house and becomes the counterparty. If the client loses, the broker gains, and the other way round.</li>
            <li><strong>Hybrid.</strong> Most brokers mix both, routing by account type, trade size or a client’s track record.</li>
          </ul>
        </div>
{figure(3, fig_abook(), 'Same order, two destinations. The routing rule decides, not the trader.')}
        <div class="prose reveal">
          <h2><span class="h-num">05</span>Where it gets hard</h2>
          <p>The interesting work happens at the seams: keeping the back office and MT5 in sync when one of them is slow, making sure a payment callback never credits an account twice, and showing each staff member only their own branch’s clients.</p>
          <p>Money math matters too. Amounts are stored as whole cents or exact decimals, never as floating point numbers, because 0.1 + 0.2 is not exactly 0.3 to a computer.</p>

          <h2><span class="h-num">06</span>Words to know</h2>
          <dl class="glossary">
            <div><dt>Spread</dt><dd>The gap between the buy and sell price. The basic way a broker earns.</dd></div>
            <div><dt>Lot</dt><dd>Standard trade size. One lot of EURUSD is 100,000 euros.</dd></div>
            <div><dt>Leverage</dt><dd>Borrowed exposure. At 1:100, 1,000 dollars of margin controls a 100,000 dollar position.</dd></div>
            <div><dt>Margin</dt><dd>Money set aside to keep a position open.</dd></div>
            <div><dt>Manager API</dt><dd>The MT5 interface brokers use to create accounts, move balances and read trades.</dd></div>
            <div><dt>Bridge</dt><dd>Software that connects the trade server to liquidity providers.</dd></div>
          </dl>
        </div>
'''

BODY['how-payment-providers-work.html'] = lambda: f'''
        <div class="prose reveal">
          <h2><span class="h-num">01</span>Who’s in the chain</h2>
          <p>A card payment touches more companies than most people expect.</p>
          <ul>
            <li><strong>Checkout.</strong> The broker’s payment page, often hosted by the PSP so card numbers never touch the broker’s servers.</li>
            <li><strong>PSP.</strong> Collects the payment details and routes them. One integration gives the broker cards, bank transfers and local payment methods.</li>
            <li><strong>Acquirer.</strong> The merchant’s bank. It sends the request into the card network and later pays the money out.</li>
            <li><strong>Card network.</strong> Visa or Mastercard, passing messages between the banks.</li>
            <li><strong>Issuer.</strong> The trader’s bank. It checks the balance and fraud signals, then approves or declines.</li>
          </ul>
          <p>Often the issuer first asks for <strong>3-D Secure</strong>: a one-time code or a tap in the banking app that proves the card holder is really there.</p>
        </div>
{figure(1, fig_card_chain(), 'The authorization request (orange) goes out to the issuer and the answer (black) comes back. Then the PSP sends a webhook to the broker’s server, which credits the wallet.')}
        <div class="prose reveal">
          <h2><span class="h-num">02</span>Callbacks, not answers</h2>
          <p>The redirect back to the broker after paying is not proof of payment. The trader can close the tab, and a redirect can be faked. The real answer arrives separately as a <strong>webhook</strong>: the PSP calls the broker’s server directly with the result, signed so it can’t be forged.</p>
          <p>Webhooks are delivered at least once, which sometimes means more than once. A network blip makes the PSP retry, and the same event can arrive twice.</p>
        </div>
{figure(2, fig_webhook(), 'Attempt 1 times out, attempt 2 credits $100 and attempt 3 is a duplicate. The server remembers each event id, so the balance stays at $100.')}
        <div class="prose reveal">
          <p>Two habits make this safe:</p>
          <ul>
            <li><strong>Idempotency.</strong> Every event has a unique id. Save it in the same database transaction as the credit, and ignore any id you’ve already seen.</li>
            <li><strong>Status sync.</strong> If a callback never comes, ask the PSP. A scheduled job checks payments stuck in pending and settles them either way.</li>
          </ul>

          <h2><span class="h-num">03</span>Fees, worked out</h2>
          <p>PSPs usually charge a percentage plus a fixed amount per transaction. For a 100 dollar deposit at 2.5% + $0.30:</p>
          <div class="fee-slip" aria-label="Fee example">
            <div><span>Deposit</span><i></i><b>$100.00</b></div>
            <div><span>Percentage fee, 2.5%</span><i></i><b>$2.50</b></div>
            <div><span>Fixed fee</span><i></i><b>$0.30</b></div>
            <div class="is-total"><span>Total fee</span><i></i><b>$2.80</b></div>
            <div><span>Credited if the client pays</span><i></i><b>$97.20</b></div>
            <div><span>Credited if the broker pays</span><i></i><b>$100.00</b></div>
          </div>
          <p>Who pays is a business choice. Either way, calculate in exact decimals and round once, at the end.</p>

          <h2><span class="h-num">04</span>Withdrawals go the other way</h2>
          <p>A withdrawal, or payout, starts in the back office. Staff or automated rules check it first. Is the account verified? Is the money still needed as margin for open positions? Is it going back to the method it came from? Returning money the way it came in is a standard anti-money laundering rule. Only then does the broker ask the PSP to pay out.</p>

          <h2><span class="h-num">05</span>Reconciliation</h2>
          <p>Every day the PSP sends a settlement report listing what it actually collected and paid out. Reconciliation matches that report line by line against the broker’s own ledger.</p>
        </div>
{figure(3, fig_recon(), 'Three deposits match. The fourth is in the ledger but not in the report yet, so it is flagged for a person to check.')}
        <div class="prose reveal">
          <p>Mismatches are normal. Settlement lags a day or two behind, fees are deducted, refunds and chargebacks arrive later. The goal isn’t zero mismatches; it’s that none goes unnoticed.</p>

          <h2><span class="h-num">06</span>Words to know</h2>
          <dl class="glossary">
            <div><dt>PSP</dt><dd>Payment service provider. One API in front of many payment methods and banks.</dd></div>
            <div><dt>Acquirer</dt><dd>The merchant’s bank, which processes card payments and settles the money.</dd></div>
            <div><dt>Issuer</dt><dd>The bank that issued the card and approves or declines each payment.</dd></div>
            <div><dt>3-D Secure</dt><dd>An extra check by the card holder’s bank, such as a code or an app approval.</dd></div>
            <div><dt>Webhook</dt><dd>A message the PSP sends to the broker’s server when something happens.</dd></div>
            <div><dt>Idempotency key</dt><dd>A unique id that lets the same request be repeated safely.</dd></div>
            <div><dt>Settlement</dt><dd>When collected money actually moves to the merchant’s bank account.</dd></div>
            <div><dt>Chargeback</dt><dd>The card holder disputes a payment and their bank pulls the money back.</dd></div>
          </dl>
        </div>
'''

BODY['mt5-latency-engine.html'] = lambda: f'''
        <div class="prose reveal">
          <h2><span class="h-num">01</span>One login, many servers</h2>
          <p>When a trader logs in, the MT5 terminal doesn’t talk to the trade server directly. A broker’s MT5 platform is a group of servers with separate jobs:</p>
          <ul>
            <li><strong>Access servers.</strong> Spread around the world. They accept the terminal’s connection and pass requests on, and they shield the trade server from attacks.</li>
            <li><strong>Trade server.</strong> The core. It holds accounts and positions, checks margin and executes orders.</li>
            <li><strong>History server.</strong> Stores price history, so charts load without slowing down trading.</li>
            <li><strong>Backup server.</strong> Keeps a live copy of the trade server, ready to take over.</li>
            <li><strong>Gateway.</strong> Connects the platform to liquidity providers and other markets.</li>
          </ul>
          <p>The terminal measures the ping to the access points it knows and connects through the fastest. That is the first trick: put the entry point close to the trader.</p>
        </div>
{figure(1, fig_mt5_arch(), 'The terminal pings three access servers and picks the fastest, Singapore here. The order (orange) travels through it to the trade server and gateway, and the fill (black) comes back the same way. Ping times are illustrative.')}
        <div class="prose reveal">
          <h2><span class="h-num">02</span>Where the milliseconds go</h2>
          <p>Follow one market order and add up the delay at each hop.</p>
        </div>
{figure(2, fig_latency_budget(), 'An illustrative round trip of 104 ms. The two network legs take 91 ms; everything inside the data center takes 13.')}
        <div class="prose reveal">
          <p>The pattern holds almost everywhere: the servers are fast and the distance is slow.</p>

          <h2><span class="h-num">03</span>The speed of light is the limit</h2>
          <p>Light in optical fiber covers about 200 km per millisecond. Sri Lanka to London is about 8,700 km in a straight line and longer by cable, so one round trip takes at least 87 ms before a single router gets involved. Software can’t beat that. It can only move closer.</p>

          <h2><span class="h-num">04</span>Execution modes</h2>
          <p>Latency matters most in the moment between clicking and filling. If the price changes in that moment, MT5 handles it according to the symbol’s execution mode:</p>
          <ul>
            <li><strong>Instant execution.</strong> The order fills at the price the trader saw, or not at all. If the price moved, the trader gets a <strong>requote</strong> and can accept the new price.</li>
            <li><strong>Market execution.</strong> The order fills at the current price, whatever it is. No requotes, but the fill can differ from the screen. That difference is <strong>slippage</strong>.</li>
            <li><strong>Request execution.</strong> The terminal asks for a price first, then trades on it.</li>
            <li><strong>Exchange execution.</strong> Orders go to an external exchange and fill there.</li>
          </ul>
        </div>
{figure(3, fig_execution(), 'The trader clicks Buy at 1.08520, but by the time the order arrives the price is 1.08523. Instant execution sends a requote; market execution fills at 1.08523, 0.3 pips worse.')}
        <div class="prose reveal">
          <h2><span class="h-num">05</span>How traders and brokers cut latency</h2>
          <ul>
            <li><strong>Host next to the trade server.</strong> Traders who run expert advisors use a VPS in the same data center, which can bring the round trip down to a millisecond or two.</li>
            <li><strong>Co-locate the gateway.</strong> Brokers put the trade server and gateway in the same data center as their liquidity providers. London’s LD4, New York’s NY4 and Tokyo’s TY3 are the usual forex hubs.</li>
            <li><strong>Add access servers.</strong> An access point near each big client region shortens the first network leg.</li>
            <li><strong>Skip Wi-Fi and mobile data</strong> for anything time sensitive. They add jitter as well as delay.</li>
          </ul>

          <h2><span class="h-num">06</span>Words to know</h2>
          <dl class="glossary">
            <div><dt>Latency</dt><dd>The time a message takes to get somewhere. In trading, usually measured in milliseconds.</dd></div>
            <div><dt>Ping</dt><dd>A round trip test: how long it takes to reach a server and hear back.</dd></div>
            <div><dt>Access server</dt><dd>An MT5 entry point near the trader that forwards requests to the trade server.</dd></div>
            <div><dt>Trade server</dt><dd>The core MT5 server that holds accounts and executes orders.</dd></div>
            <div><dt>Gateway</dt><dd>The link between MT5 and outside liquidity or exchanges.</dd></div>
            <div><dt>Slippage</dt><dd>The difference between the expected price and the fill price.</dd></div>
            <div><dt>Requote</dt><dd>A new price offered when the requested one is no longer available.</dd></div>
            <div><dt>VPS</dt><dd>A virtual server rented in a data center, often close to the broker.</dd></div>
          </dl>
        </div>
'''


BODY['how-local-deposit-gateways-work.html'] = lambda: f'''
        <div class="prose reveal">
          <h2><span class="h-num">01</span>The pieces</h2>
          <p>MLD’s merchant API lets a business create deposits and withdrawals in any currency its account is enabled for, track their status and get told when money arrives. A few terms carry the whole design:</p>
          <ul>
            <li><strong>Collection account.</strong> A bank account the customer pays into. <code>GET /v2/collection-accounts</code> lists the active ones.</li>
            <li><strong>Reference number.</strong> An 8-character code such as <code>7KQ2M9XA</code> that the customer quotes on the transfer, so the money can be matched to the right deposit. It comes from <code>GET /v2/quote</code>, lasts one hour and works once.</li>
            <li><strong>Slip.</strong> The customer’s proof of payment: a JPEG, PNG or PDF of up to 5 MB.</li>
            <li><strong>Deposits and withdrawals.</strong> Money in and money out. Each has a ULID id and a status the merchant can look up at any time.</li>
          </ul>
        </div>
{figure(1, fig_mld_sequence(), 'An LKR 25,000 deposit through hosted checkout. The quote reserves a reference number, the customer pays and uploads a slip, an admin confirms the money arrived, and a signed webhook tells the merchant to credit the wallet.')}
        <div class="prose reveal">
          <h2><span class="h-num">02</span>Two ways to take a deposit</h2>
          <p><strong>Hosted checkout.</strong> The merchant creates the deposit without a slip and sends the customer to the <code>checkout_url</code> it gets back. That page shows where to pay and collects the slip. Until then the deposit is <code>awaiting_payment</code>, and it expires when the hour runs out.</p>
          <p><strong>Host-to-host.</strong> The merchant collects the slip in its own app and includes it in the <code>POST /v2/deposits</code> request. The deposit starts as <code>customer_claims_paid</code>, never expires unpaid and can’t be cancelled. These requests should carry an <code>Idempotency-Key</code> header: sending the same key again returns the original response instead of creating a second deposit.</p>
          <div class="callout"><strong>Why the reference number matters</strong>A bank transfer shows up as an amount, a date and whatever the sender typed. The reference number is what ties that line on a statement to one deposit, and the API can search by it: <code>GET /v2/deposits?ref_no=7KQ2M9XA</code>.</div>

          <h2><span class="h-num">03</span>Signing every request</h2>
          <p>Every call carries three headers: <code>X-Client-Id</code>, <code>X-Timestamp</code> in Unix seconds, and <code>X-Client-Signature</code>. The signature is an HMAC-SHA256 of four parts joined with dots: the timestamp, the HTTP method, the path and a SHA-256 hash of the raw body. The key is a signing secret the merchant portal shows only once.</p>
        </div>
{figure(2, fig_mld_signing(), 'Signing a deposit request. The body hash covers the exact bytes sent, so changing one character of the JSON breaks the signature. All values are examples.')}
        <div class="prose reveal">
          <p>MLD rebuilds the same string and compares. A wrong signature gets <code>401 invalid_signature</code>. A timestamp more than 300 seconds away from MLD’s clock gets <code>401 stale_request</code>, so a captured request can’t be replayed later.</p>

          <h2><span class="h-num">04</span>The life of a deposit</h2>
          <p>A deposit always has exactly one status, and only a few moves between them are possible.</p>
        </div>
{figure(3, fig_mld_states(), 'Deposit statuses. The orange marker follows a normal deposit to confirmed; the black one shows an unpaid deposit expiring after its hour.')}
        <div class="prose reveal">
          <ul>
            <li><strong>awaiting_payment</strong> is the only status that can be cancelled, with <code>POST /v2/deposits/{{ulid}}/cancel</code>.</li>
            <li><strong>customer_claims_paid</strong> means the customer says they paid and a slip is attached. It waits for review.</li>
            <li><strong>confirmed</strong>, <strong>shortpaid</strong>, <strong>overpaid</strong> and <strong>rejected</strong> are the outcomes of that review.</li>
            <li><strong>already_approved</strong> and <strong>already_rejected</strong> close a deposit that duplicates another one, which <code>duplicate_of</code> points to.</li>
          </ul>

          <h2><span class="h-num">05</span>Webhooks, verified</h2>
          <p>When an admin confirms a deposit, MLD sends a <code>deposit.confirmed</code> webhook, and payouts send events such as <code>payout.processing</code>. Each one is signed: the <code>X-Signature</code> header holds an HMAC-SHA256 of the timestamp and the raw body. The receiving server should:</p>
          <ol>
            <li><strong>Verify the signature</strong> against the raw body, using a constant-time comparison.</li>
            <li><strong>Reject old timestamps</strong>, outside a window of about 300 seconds.</li>
            <li><strong>Skip duplicates</strong> by remembering each <code>X-Event-Id</code>.</li>
            <li><strong>Answer with any 2xx</strong>. Anything else is retried with backoff.</li>
          </ol>
          <p>It’s the at-least-once delivery from <a class="link-arrow" href="how-payment-providers-work.html">Note 02</a> again. If webhooks stop arriving, the docs suggest polling <code>GET /v2/deposits/{{ulid}}</code> instead.</p>

          <h2><span class="h-num">06</span>Paying out</h2>
          <p>A withdrawal sends money to a customer’s bank account or e-wallet. The merchant posts the exact amount the customer should receive, plus the bank, account number and account name. It moves from <code>pending</code> to <code>processing</code> to <code>completed</code>, or ends as <code>rejected</code> or <code>cancelled</code>. For LKR the only fee is a percentage service charge billed to the merchant on top, so the customer receives the full amount.</p>

          <h2><span class="h-num">07</span>Beyond LKR</h2>
          <p>The same endpoints handle other local currencies. <code>GET /v2/currencies</code> describes each one: minimum and maximum amounts, decimal places, which customer details are required and which payment methods or banks are available. The customer pays on the checkout page by bank account, QR code or payment link. For these deposits the response also shows <code>received_amount</code>, what actually arrived, and <code>received_net</code>, what is credited after the service charge. <code>GET /v2/rates</code> gives live buy and sell rates.</p>

          <h2><span class="h-num">08</span>The API at a glance</h2>
          <p>All paths sit under <code>/api</code>.</p>
          <div class="endpoints">
            <div><b>GET</b><code>/v2/ping</code><span>Check that keys and signing work</span></div>
            <div><b>GET</b><code>/v2/currencies</code><span>Currencies, limits and required fields</span></div>
            <div><b>GET</b><code>/v2/quote</code><span>Reserve a reference number (LKR)</span></div>
            <div><b>GET</b><code>/v2/rates</code><span>Live buy and sell rates</span></div>
            <div><b>POST</b><code>/v2/deposits</code><span>Create a deposit</span></div>
            <div><b>GET</b><code>/v2/deposits/{{ulid}}</code><span>Check one deposit</span></div>
            <div><b>POST</b><code>/v2/deposits/{{ulid}}/slip</code><span>Attach or replace the slip</span></div>
            <div><b>POST</b><code>/v2/deposits/{{ulid}}/cancel</code><span>Cancel while awaiting payment</span></div>
            <div><b>POST</b><code>/v2/withdrawals</code><span>Create a payout</span></div>
            <div><b>GET</b><code>/v2/withdrawals/{{ulid}}</code><span>Check one payout</span></div>
          </div>

          <h2><span class="h-num">09</span>Words to know</h2>
          <dl class="glossary">
            <div><dt>Reference number</dt><dd>An 8-character code the customer quotes on the transfer so it can be matched.</dd></div>
            <div><dt>Collection account</dt><dd>The bank account customers pay into.</dd></div>
            <div><dt>Slip</dt><dd>The customer’s proof of transfer, uploaded as an image or PDF.</dd></div>
            <div><dt>Hosted checkout</dt><dd>MLD’s own payment page, reached through the deposit’s checkout_url.</dd></div>
            <div><dt>Host-to-host</dt><dd>The merchant sends everything, slip included, straight from its own server.</dd></div>
            <div><dt>HMAC-SHA256</dt><dd>A hash keyed with a secret, so only someone holding the secret can produce it.</dd></div>
            <div><dt>Idempotency-Key</dt><dd>A header that makes a repeated request return the first result instead of acting twice.</dd></div>
            <div><dt>ULID</dt><dd>A unique id that also sorts by creation time.</dd></div>
          </dl>
          <p class="note-source">Based on the public <a href="https://sandbox.mylocaldepositor.com/docs/api" target="_blank" rel="noopener">My Local Depositor API v2 reference</a>. Example values are made up.</p>
        </div>
'''


BODY['how-copy-trading-works.html'] = lambda: f'''
        <div class="prose reveal">
          <h2><span class="h-num">01</span>One record across brokers</h2>
          <p>Most copy trading lives inside a single broker, so a strategist’s history disappears when they move. FinTruvix calls itself a cross-broker social trading platform: the record belongs to the trader, not to the broker. That record is the <strong>Trader Passport</strong>, created with the account, and the site says it can’t be deleted, reset or transferred. It holds:</p>
          <ul>
            <li><strong>Verified identity.</strong> KYC is done once, when the account is created.</li>
            <li><strong>Roles.</strong> Follower, strategist, signalist or programme manager.</li>
            <li><strong>Score history and conduct record.</strong> Every score change and every complaint stays on file.</li>
            <li><strong>Connected brokers.</strong> The trading accounts linked to the passport.</li>
          </ul>

          <h2><span class="h-num">02</span>Connecting a broker</h2>
          <p>A MetaTrader 5, cTrader or TradeLocker account can be connected in one of two modes. <strong>Read-only</strong> lets FinTruvix read the trades, which is how a strategist proves a track record. <strong>Trade-enabled</strong> lets it place copied orders, which is what a follower needs. For MT5, the site says the password is used once to confirm ownership and is never stored.</p>
        </div>
{figure(1, fig_ft_custody(), 'Two kinds of connection. Trades are read from the strategist’s account (black) and copied into the follower’s account (orange). The follower’s capital never leaves their own broker.')}
        <div class="prose reveal">
          <p>The money doesn’t move. Capital stays in the follower’s own broker account, and FinTruvix only mirrors trades into it. The one balance it holds is a wallet for top-ups and earnings, and the site says plainly that this wallet is not a bank account.</p>

          <h2><span class="h-num">03</span>One trade, many orders</h2>
          <p>When a strategist opens a trade, the copy engine has to turn it into a separate order for every follower, each sized for that follower’s account. A managed programme picks one sizing rule:</p>
          <ul>
            <li><strong>Lot multiplier.</strong> 1.00 lot × 0.5 = 0.50 lot.</li>
            <li><strong>Fixed lot.</strong> Always the same size, such as 0.10 lot.</li>
            <li><strong>Proportional.</strong> Scaled to the follower’s allocation, equity or balance. A $2,000 account copying a $20,000 one gets a tenth of the size.</li>
          </ul>
          <p>Before anything is sent, risk checks clamp the position size and enforce the allocation cap. A separate monitor pauses copying for anyone who hits a drawdown or daily loss limit. Then every order goes out at the same time.</p>
        </div>
{figure(2, fig_ft_fanout(), 'One 1.00 lot trade becomes four outcomes: three orders sized by different rules, and one follower skipped because their daily loss limit was reached.')}
        <div class="prose reveal">
          <p>Speed matters, because a follower whose order lands later gets a worse price. FinTruvix reports a fan-out time of 12 ms at the 99th percentile for 250 followers. That was measured against a mock broker, so real broker execution comes on top, and the design target is 100 ms.</p>

          <h2><span class="h-num">04</span>The Trust Score</h2>
          <p>Strategies are listed by Trust Score, and the site says nobody can pay to move up. The score has two parts:</p>
          <ul>
            <li><strong>Performance, P.</strong> Profit factor 25%, risk-adjusted return 20%, drawdown management 20%, win rate 15%, reward to risk 10% and longevity 10%. Copier profitability and consistency are declared at 0% until they can be measured.</li>
            <li><strong>Integrity, I.</strong> Built from the conduct record, unresolved complaints and how complete the strategist’s disclosures are.</li>
          </ul>
          <p>They combine as <code>T = min(0.6 × P + 0.4 × I, I + 15)</code>. The second term is the clever part: no strategist can score more than 15 points above their integrity, however good their returns look.</p>
        </div>
{figure(3, fig_ft_trust(), 'A worked example. Strong performance gives P = 90, but one unresolved complaint keeps I at 60. The weighted score would be 78; the integrity cap brings it down to 75.')}
        <div class="prose reveal">
          <h2><span class="h-num">05</span>How fees work</h2>
          <p>Followers pay no platform fee on their capital. Strategists set a performance fee, charged on realised profit, and can add a high-water mark so they’re only paid on new highs. No performance fee is charged for a period that ends in a loss. FinTruvix takes its share from the strategist’s earnings.</p>

          <h2><span class="h-num">06</span>AI that can look but not touch</h2>
          <p>FinTruvix supports the Model Context Protocol, so an AI assistant can read a user’s Trust Score, copy results and the marketplace. The number of tools that can place a trade, change a copy, move money or change a setting is zero. The assistant only sees what the user sees, and only while they allow it.</p>

          <h2><span class="h-num">07</span>Words to know</h2>
          <dl class="glossary">
            <div><dt>Trader Passport</dt><dd>A permanent record of one trader: identity, roles, scores and conduct.</dd></div>
            <div><dt>Trust Score</dt><dd>A 0 to 100 score that mixes performance with integrity.</dd></div>
            <div><dt>Strategist</dt><dd>A trader whose trades others can copy.</dd></div>
            <div><dt>Signalist</dt><dd>Publishes trade ideas to a channel that followers can act on.</dd></div>
            <div><dt>PAMM</dt><dd>A pooled account where investors hold units in one shared trading account.</dd></div>
            <div><dt>High-water mark</dt><dd>A fee rule that only pays on profit above the previous peak.</dd></div>
            <div><dt>Drawdown</dt><dd>How far an account falls from its peak before recovering.</dd></div>
            <div><dt>Fan-out</dt><dd>Turning one event into many parallel actions, here one trade into many orders.</dd></div>
          </dl>
          <p class="note-source">Based on the public <a href="https://fintruvix.com/" target="_blank" rel="noopener">FinTruvix website</a>. Figures are the company’s own; the Trust Score example values are made up.</p>
        </div>
'''

BODY['how-payment-orchestration-works.html'] = lambda: f'''
        <div class="prose reveal">
          <h2><span class="h-num">01</span>Why orchestrate</h2>
          <p>No single payment provider is best everywhere. One approves more cards in Germany, another is cheaper in the US, a third handles crypto, and any of them can go down. Connecting to each one separately means a new integration, a new dashboard and new reconciliation every time.</p>
          <p>A payment orchestration platform puts one API in front of all of them. Fincashier describes itself as exactly that: the business integrates once and Fincashier handles the providers behind it, more than 80 of them according to its site.</p>
        </div>
{figure(1, fig_fc_routes(), 'One integration, many providers. Each payment is routed on its own: a German card to Adyen, a US card to Stripe, a USDT payment to BitPay.')}
        <div class="prose reveal">
          <h2><span class="h-num">02</span>Creating a payment</h2>
          <p>Everything starts with a payment session. The merchant sends the amount in minor units (2500 means €25.00), the currency, the customer and how the payment should be routed:</p>
          <pre class="code"><code>POST /v1/sessions

{{
  "amount": 2500,
  "currency": "EUR",
  "customer": {{ "id": "cus_8841" }},
  "routing": {{
    "strategy": "performance",
    "retries": 3,
    "failover": true
  }}
}}</code></pre>
          <p>The response carries the session id, a status of <code>pending</code>, <code>approved</code> or <code>failed</code>, and the provider that took the payment. Requests accept an idempotency key, so a retried call never charges twice.</p>

          <h2><span class="h-num">03</span>Smart routing</h2>
          <p>The router picks a provider for each payment using live numbers. The site says approval rates, latency and error rates update every 60 seconds. The routing strategy decides what best means:</p>
          <ul>
            <li><strong>performance</strong>: the highest approval rate.</li>
            <li><strong>cost</strong>: the lowest fee.</li>
            <li><strong>geo</strong>: the provider that works best for the customer’s country.</li>
            <li><strong>round_robin</strong>: take turns, to spread the volume.</li>
            <li><strong>custom</strong>: the merchant’s own rules.</li>
          </ul>
        </div>
{figure(2, fig_fc_scores(), 'The same three providers, two strategies, two different winners. All numbers are examples.')}
        <div class="prose reveal">
          <h2><span class="h-num">04</span>Failover cascades</h2>
          <p>If the first provider declines or doesn’t answer, the payment can move to the next one in an ordered list, such as Stripe, then Adyen, then Checkout.com. The customer only sees one payment that went through.</p>
        </div>
{figure(3, fig_fc_cascade(), 'Three attempts, one payment. The merchant hears about each reroute through a webhook, then gets session.approved.')}
        <div class="prose reveal">
          <div class="callout"><strong>Not every decline should be retried</strong>A soft decline, such as a timeout or a bank that’s briefly unavailable, is worth trying elsewhere. A hard decline, such as a card reported stolen, should stop the cascade. Retrying it makes a business look risky to the card networks.</div>

          <h2><span class="h-num">05</span>Webhooks and reconciliation</h2>
          <p>Every change is reported by webhook, with events such as <code>session.approved</code>, <code>session.rerouted</code> and <code>refund.processed</code>. Each is signed with HMAC-SHA256 and retried with exponential backoff, and the site says events stay in a log for 72 hours so they can be replayed. Settlements from every provider are then matched against the transactions automatically, the same reconciliation shown in <a class="link-arrow" href="how-payment-providers-work.html">Note 02</a>.</p>

          <h2><span class="h-num">06</span>More than taking payments</h2>
          <p>The same layer sends payouts to banks, cards and wallets, one at a time or in batches. It keeps every provider’s API keys in one vault with role-based access, runs fraud rules before a payment is routed, and offers a hosted or embedded checkout that decides when to ask for 3-D Secure.</p>

          <h2><span class="h-num">07</span>Words to know</h2>
          <dl class="glossary">
            <div><dt>Payment orchestration</dt><dd>One layer that connects to many payment providers and routes between them.</dd></div>
            <div><dt>PSP</dt><dd>Payment service provider, such as Stripe or Adyen.</dd></div>
            <div><dt>Routing strategy</dt><dd>The rule that decides which provider gets a payment.</dd></div>
            <div><dt>Cascade</dt><dd>An ordered list of providers to try when one fails.</dd></div>
            <div><dt>Soft decline</dt><dd>A temporary failure that may succeed on retry or elsewhere.</dd></div>
            <div><dt>Approval rate</dt><dd>The share of payment attempts a provider approves.</dd></div>
            <div><dt>Minor units</dt><dd>Amounts as whole cents, so 2500 means 25.00.</dd></div>
            <div><dt>Idempotency key</dt><dd>A unique key that makes a repeated request safe.</dd></div>
          </dl>
          <p class="note-source">Based on the public <a href="https://www.fincashier.com/" target="_blank" rel="noopener">Fincashier website</a> and developer page. Figures are the company’s own; scoreboard numbers are examples.</p>
        </div>
'''

# --------------------------------------------------------------------------- build


def build():
    built = []
    for i, n in enumerate(NOTES):
        body = BODY[n['file']]()
        minutes = max(3, round(words(body + n['lead']) / 210))
        n['minutes'] = minutes
        nxt = NOTES[(i + 1) % len(NOTES)]
        main = f'''    <div class="container">
      <header class="note-head">
        <a class="back-link" href="notebook.html"><i class="bi bi-arrow-left" aria-hidden="true"></i> Notebook</a>
        <p class="label case-eyebrow"><span>(Note {n['num']})</span>{n['eyebrow']}{'<span class="nb-new">New</span>' if n.get('new') else ''}</p>
        <h1>{n['h1']}</h1>
        <p class="note-lead">{n['lead']}</p>
        <dl class="case-meta">
          <div><dt>Reading time</dt><dd>{minutes} min</dd></div>
          <div><dt>Topic</dt><dd>{n['meta_topic']}</dd></div>
          <div><dt>Diagrams</dt><dd>3, animated</dd></div>
          <div><dt>Updated</dt><dd>Nov 2026</dd></div>
        </dl>
      </header>

      <article class="note-body">
{body}
      </article>

      <nav class="case-next" aria-label="Next note">
        <a href="{nxt['file']}">
          <span><small>Next note</small><strong>{nxt['title']}</strong></span>
          <span class="work-arrow" aria-hidden="true"><i class="bi bi-arrow-right"></i></span>
        </a>
      </nav>
    </div>'''
        (OUT / n['file']).write_text(page(f"{n['title']} · Notebook · Adhly Azhar", n['lead'], main))
        built.append((n['file'], minutes, words(body)))

    cards = []
    for n in NOTES:
        cards.append(f'''        <a class="nb-card reveal{' is-new' if n.get('new') else ''}" href="{n['file']}">
          <div class="nb-card-body">
            <p class="nb-num">{'<span class="nb-new"><i class="bi bi-stars" aria-hidden="true"></i>New</span>' if n.get('new') else ''}Note {n['num']} · {n['topic']}</p>
            <h2>{n['title'].replace("'", "’")}</h2>
            <p>{n['card']}</p>
            <div class="nb-meta"><span>{n['minutes']} min read</span><span>3 animated diagrams</span></div>
            <span class="nb-read">Read the note <i class="bi bi-arrow-right" aria-hidden="true"></i></span>
          </div>
          <div class="nb-card-art" aria-hidden="true">{n['mini']()}</div>
        </a>''')
    pin = ('<span class="drop-pin"><span class="pin-shadow"></span><span class="pin-body"><svg class="pin-art" viewBox="0 0 22 30">'
           '<path d="M10.2 15.5H11.8L11.35 27.6L11 30L10.65 27.6Z" fill="url(#pin-steel)"/>'
           '<path d="M8.6 15.2H13.4L12.3 17.6H9.7Z" fill="#8f3110"/>'
           '<circle cx="11" cy="9" r="7.6" fill="url(#pin-ball)" stroke="rgba(15, 23, 42, 0.35)" stroke-width="0.6"/>'
           '<ellipse cx="8.3" cy="6.1" rx="2.7" ry="1.9" fill="#fff" opacity="0.75" transform="rotate(-30 8.3 6.1)"/>'
           '<circle cx="14.4" cy="12.6" r="1" fill="#fff" opacity="0.25"/></svg></span></span>')
    listing = f'''    <div class="container">
      <header class="nb-hero">
        <p class="label"><span>(Notebook)</span>How fintech works</p>
        <h1 class="nb-title">Note<span>book</span></h1>
        <div class="nb-intro">
          <p>How fintech systems actually work, drawn as diagrams that move. Notes from building a brokerage platform: trading, payments and the plumbing in between.</p>
          <p class="nb-count">{len(NOTES)} notes · updated Nov 2026</p>
        </div>
      </header>

      <div class="nb-list">
{chr(10).join(cards)}
        <div class="nb-more">
          <div class="drop-note note-nb" aria-hidden="true">
            <div class="drop-paper" style="--r: 4deg">{pin}<p>More notes on the <u>way</u></p></div>
          </div>
        </div>
      </div>
    </div>'''
    (OUT / 'notebook.html').write_text(page('Notebook · Adhly Azhar',
                                             'How fintech systems work, explained with animated diagrams: trading platforms, payment providers and MT5 latency.',
                                             listing, defs=True))
    for f, m, w in built:
        print(f'{f:36s} {w:5d} words  {m} min')
    print('notebook.html')


if __name__ == '__main__':
    build()
