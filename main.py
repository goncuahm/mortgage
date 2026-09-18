"""
Mortgage & Bond Math Toolkit — Streamlit Edition
=================================================
A currency-agnostic, typing-friendly rebuild of the original static HTML
"Mortgage & Bond Math Toolkit". All time-value-of-money formulas (annuity
present value / payment, Macaulay duration, effective annual rate, the
Fisher equation for real rates, and the cash-depletion simulation) are
ported 1:1 from the original tool and have been numerically re-verified.

Includes a Bond Pricing tab: price ↔ yield solving, Macaulay/modified
duration, convexity, and teaching plots showing price sensitivity to
yield changes.

Run with:
    streamlit run mortgage_toolkit_streamlit.py
"""

import math
import streamlit as st
import plotly.graph_objects as go

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Mortgage & Bond Math Toolkit",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# THEME COLORS (matches the original ledger/paper aesthetic)
# ============================================================
COL_INK = "#16233D"
COL_LEDGER = "#1F5C4B"
COL_LEDGER_L = "#2C7A63"
COL_GOLD = "#B08D2B"
COL_GOLD_L = "#D8B84F"
COL_BRICK = "#8C3B2E"
COL_PAPER = "#F5F2E9"
COL_CARD = "#FBF9F3"
COL_LINE = "#D9D2C0"
COL_GRID = "#E3DCC9"
COL_MUTED = "#6B6B63"

# ============================================================
# GLOBAL CSS — recreate the ledger / old-paper look
# ============================================================
st.markdown(f"""
<style>
  .stApp {{
      background-color: {COL_PAPER};
  }}
  html, body, [class*="css"]  {{
      font-family: Georgia, 'Iowan Old Style', 'Palatino Linotype', serif;
  }}
  h1, h2, h3 {{
      color: {COL_INK};
  }}
  /* Sidebar: LIGHT background + BLACK text, on purpose. A dark
     sidebar background forcing light text was fragile — Streamlit
     renders input boxes and dropdowns with their own light
     backgrounds regardless of the panel around them, so light text
     landed on light input backgrounds and disappeared. Light
     background + black text everywhere has no such failure mode:
     black text is readable against any light shade, full stop. */
  section[data-testid="stSidebar"] {{
      background-color: {COL_CARD};
      border-right: 1px solid {COL_LINE};
  }}
  section[data-testid="stSidebar"] * {{
      color: #000000 !important;
  }}
  section[data-testid="stSidebar"] .stSelectbox label,
  section[data-testid="stSidebar"] .stRadio label,
  section[data-testid="stSidebar"] .stTextInput label {{
      color: {COL_LEDGER} !important;
      font-style: italic;
      font-weight: bold;
  }}
  div[data-testid="stVerticalBlockBorderWrapper"] {{
      background-color: {COL_CARD};
      border: 1px solid {COL_LINE} !important;
      border-radius: 10px;
  }}
  .app-header {{
      background:{COL_INK};
      color:{COL_PAPER};
      padding:26px 30px 20px 30px;
      border-radius: 10px;
      border-bottom:5px solid {COL_GOLD};
      margin-bottom: 18px;
  }}
  .app-header h1 {{
      margin:0 0 6px 0;
      font-size:28px;
      font-weight:normal;
      color:{COL_PAPER};
      letter-spacing:0.3px;
  }}
  .app-header .sub {{
      font-size:14.5px;
      color:#CFCABB;
      font-style:italic;
      max-width:760px;
  }}
  .app-header .tag {{
      display:inline-block;
      margin-top:12px;
      font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
      font-size:11.5px;
      letter-spacing:0.5px;
      color:{COL_GOLD_L};
      border:1px solid rgba(216,184,79,0.45);
      border-radius:3px;
      padding:4px 10px;
  }}
  .card-title {{
      font-size:13px;
      color:{COL_LEDGER};
      font-style:italic;
      border-bottom:1px solid {COL_LINE};
      padding-bottom:8px;
      margin-bottom:10px;
  }}
  .stat {{
      background:{COL_CARD};
      border:1px solid {COL_LINE};
      border-radius:10px;
      padding:14px 16px;
      box-shadow: 0 1px 2px rgba(22,35,61,0.08), 0 4px 14px rgba(22,35,61,0.06);
      height: 100%;
  }}
  .stat .label {{
      font-size:11.5px;
      color:{COL_MUTED};
      font-style:italic;
  }}
  .stat .value {{
      font-family: ui-monospace, 'SF Mono', Menlo, monospace;
      font-size:21px;
      color:{COL_INK};
      margin-top:4px;
      font-weight:bold;
      word-break: break-word;
  }}
  .stat .value.gold {{color:{COL_GOLD};}}
  .stat .value.brick {{color:{COL_BRICK};}}
  .stat .value.ledger {{color:{COL_LEDGER};}}
  .stat .sub {{font-size:11px;color:#8a8578;margin-top:2px;}}

  .verdict {{
      border-radius:10px;
      padding:16px 20px;
      font-size:15px;
      box-shadow: 0 1px 2px rgba(22,35,61,0.08), 0 4px 14px rgba(22,35,61,0.06);
      border-left:6px solid {COL_LEDGER};
      background:{COL_CARD};
      color: {COL_INK};
      margin: 10px 0 4px 0;
  }}
  .verdict.bad {{border-left-color:{COL_BRICK};}}
  .verdict .vt {{font-weight:bold; margin-bottom:4px; display:block;}}
  .verdict.good .vt {{color:{COL_LEDGER};}}
  .verdict.bad .vt {{color:{COL_BRICK};}}

  .note {{font-size:12.5px; color:#7a7568; margin-top:8px; line-height:1.5;}}
  .note b {{color:{COL_INK};}}

  .chart-title {{font-size:12.5px; color:{COL_MUTED}; font-style:italic; margin-bottom:2px;}}

  footer, div[data-testid="stDecoration"] {{visibility:hidden;}}

  /* ============================================================
     READABILITY FIX — force theme-independent contrast everywhere.
     Streamlit's active theme (light or dark, which varies by how
     the app is deployed/configured) supplies default text colors
     for widget labels, typed input values, and dropdown menus. If
     that theme happens to use light/white text, it becomes
     invisible against this app's light "paper" and card
     backgrounds. The rules below hard-code visible colors instead
     of relying on the theme at all.
     ============================================================ */

  /* Main-area widget labels, radio/checkbox option text, tables —
     covers both older ("main") and newer ("stMain") Streamlit DOM. */
  .main label, div[data-testid="stMain"] label,
  .main .stMarkdown p, div[data-testid="stMain"] .stMarkdown p,
  .main .stMarkdown li, div[data-testid="stMain"] .stMarkdown li,
  .main .stRadio div[role="radiogroup"] label,
  div[data-testid="stMain"] .stRadio div[role="radiogroup"] label,
  .main .stCheckbox label, div[data-testid="stMain"] .stCheckbox label,
  .main table, div[data-testid="stMain"] table,
  .main th, div[data-testid="stMain"] th,
  .main td, div[data-testid="stMain"] td {{
      color: #000000 !important;
  }}

  /* The actual typed/selected VALUE inside inputs — main area,
     sidebar, and anywhere else. Plain black on a light card
     background: the highest-contrast, most theme-proof combination
     there is. This is also a higher-specificity selector (tag name)
     than the sidebar's blanket `*` rule above, so it wins there too. */
  input, textarea,
  div[data-baseweb="select"] > div,
  div[data-baseweb="base-input"] {{
      color: #000000 !important;
      background-color: {COL_CARD} !important;
  }}

  /* Dropdown / select popovers render in a portal attached to
     <body>, outside both the sidebar and main containers, so they
     need their own explicit rule regardless of active theme. */
  div[data-baseweb="popover"] {{
      background-color: {COL_CARD} !important;
  }}
  div[data-baseweb="popover"] * {{
      color: #000000 !important;
  }}

  /* Tab labels: explicit, theme-independent contrast (dark blue).
     Uses the stable ARIA role attributes (role="tab"/"tablist")
     rather than library-internal data-baseweb attributes, which can
     change between Streamlit versions. Covers the button itself,
     every element nested inside it (Streamlit wraps the visible
     label text in a child <p>/<div>), AND the hover state — an
     unhandled hover state is exactly what lets Streamlit's default
     accent color (red) show through on mouseover. */
  .stTabs [role="tablist"] [role="tab"],
  .stTabs [role="tablist"] [role="tab"] * {{
      color: {COL_INK} !important;
  }}
  .stTabs [role="tablist"] [role="tab"]:hover,
  .stTabs [role="tablist"] [role="tab"]:hover * {{
      color: {COL_INK} !important;
  }}
  .stTabs [role="tablist"] [role="tab"][aria-selected="true"],
  .stTabs [role="tablist"] [role="tab"][aria-selected="true"] * {{
      color: {COL_INK} !important;
      font-weight: bold;
  }}
  /* Belt-and-suspenders: also cover the data-baseweb attributes in
     case this Streamlit version does use them alongside the ARIA
     roles above. */
  .stTabs [data-baseweb="tab-list"] button,
  .stTabs [data-baseweb="tab-list"] button *,
  .stTabs [data-baseweb="tab"],
  .stTabs [data-baseweb="tab"] * {{
      color: {COL_INK} !important;
  }}

  /* Captions (e.g. the footer note) */
  [data-testid="stCaptionContainer"], .stCaption {{
      color: {COL_MUTED} !important;
  }}
</style>
""", unsafe_allow_html=True)


# ============================================================
# CORE FINANCE FUNCTIONS  (ported 1:1 from the original tool)
# ============================================================
def annuity_pv(M, r, n):
    """Present value of a level annuity of M paid n times at rate r per period."""
    if abs(r) < 1e-12:
        return M * n
    return M * (1 - (1 + r) ** -n) / r


def payment(P, r, n):
    """Level payment that amortizes principal P over n periods at rate r."""
    if abs(r) < 1e-12:
        return P / n
    return P * r / (1 - (1 + r) ** -n)


def remaining_balance(P0, r, n_total, k_paid):
    """Original payment M, outstanding balance B, and remaining periods after k_paid."""
    M = payment(P0, r, n_total)
    n_rem = max(n_total - k_paid, 0)
    B = annuity_pv(M, r, n_rem)
    return M, B, n_rem


def macaulay_duration_months(r, n):
    """Macaulay duration (in months) of a level-payment stream of n periods at rate r."""
    if n <= 0:
        return 0.0
    num = 0.0
    den = 0.0
    for t in range(1, int(n) + 1):
        pv = (1 + r) ** -t
        num += t * pv
        den += pv
    return num / den if den > 0 else 0.0


def ear(r_monthly):
    """Effective annual rate from a monthly nominal rate."""
    return (1 + r_monthly) ** 12 - 1


def monthly_from_ear(ear_annual):
    """Monthly rate implied by an effective annual rate."""
    return (1 + ear_annual) ** (1 / 12) - 1


def fisher_real(nominal_annual, inflation_annual):
    """Exact Fisher equation: real rate from nominal rate and inflation."""
    return (1 + nominal_annual) / (1 + inflation_annual) - 1


def pv_real_of_payments(M, n, infl_annual):
    """Present value of n level payments of M, discounted at the (monthly) inflation rate."""
    im = monthly_from_ear(infl_annual)
    s = 0.0
    for t in range(1, int(n) + 1):
        s += M / (1 + im) ** t
    return s


def simulate_depletion(invest_start, r_cash_annual, M, months):
    """Simulate an investment account earning r_cash_annual (EAR) while withdrawing M
    each month; report the trace, the month it first goes negative (if any), and the
    final balance."""
    r_cash_m = monthly_from_ear(r_cash_annual)
    bal = invest_start
    trace = [(0, bal)]
    depleted_at = None
    months = int(months)
    for t in range(1, months + 1):
        bal = bal * (1 + r_cash_m) - M
        trace.append((t, bal))
        if bal < 0 and depleted_at is None:
            depleted_at = t
    return trace, depleted_at, bal


# ============================================================
# BOND MATH  (price ↔ yield, Macaulay/modified duration, convexity)
#
# Standard "bullet" bond: fixed coupon paid `freq` times per year,
# face value redeemed at maturity, valued as of a coupon date (no
# accrued-interest / day-count adjustment — a standard simplifying
# assumption for a teaching tool).
# ============================================================
def bond_cashflows(face, coupon_rate_annual, n_periods, freq):
    """List of (period t, cash flow) pairs for a standard bullet bond."""
    C = face * coupon_rate_annual / freq
    cfs = []
    for t in range(1, n_periods + 1):
        cf = C + face if t == n_periods else C
        cfs.append((t, cf))
    return cfs


def bond_price(face, coupon_rate_annual, ytm_annual, n_periods, freq):
    """Price of a standard bullet bond given an annual yield to maturity.
    Reuses annuity_pv for the coupon stream, plus the discounted redemption."""
    y = ytm_annual / freq
    C = face * coupon_rate_annual / freq
    return annuity_pv(C, y, n_periods) + face * (1 + y) ** -n_periods


def bond_ytm(price, face, coupon_rate_annual, n_periods, freq,
             tol=1e-10, max_iter=200):
    """Yield to maturity implied by a market price, found by bisection.
    Bond price is monotonically decreasing in yield (for y > -100%), so
    bisection is robust and needs no derivative or starting guess."""
    lo, hi = -0.999999, 10.0  # -99.9999% to 1000% annual yield
    f_lo = bond_price(face, coupon_rate_annual, lo, n_periods, freq) - price
    f_hi = bond_price(face, coupon_rate_annual, hi, n_periods, freq) - price
    if f_lo * f_hi > 0:
        # Requested price sits outside this bracket's range — widen once.
        hi = 100.0
        f_hi = bond_price(face, coupon_rate_annual, hi, n_periods, freq) - price
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        f_mid = bond_price(face, coupon_rate_annual, mid, n_periods, freq) - price
        if abs(f_mid) < tol or (hi - lo) < tol:
            return mid
        if f_lo * f_mid <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2


def bond_duration_convexity(face, coupon_rate_annual, ytm_annual, n_periods, freq):
    """Macaulay duration (years), modified duration (years), and annualized
    convexity for a standard bullet bond, plus the price implied by ytm."""
    y = ytm_annual / freq
    price = bond_price(face, coupon_rate_annual, ytm_annual, n_periods, freq)
    cfs = bond_cashflows(face, coupon_rate_annual, n_periods, freq)

    weighted_time = 0.0
    convexity_sum = 0.0
    for t, cf in cfs:
        disc = (1 + y) ** -t
        weighted_time += t * cf * disc
        convexity_sum += t * (t + 1) * cf * disc / (1 + y) ** 2

    mac_dur_periods = weighted_time / price
    mac_dur_years = mac_dur_periods / freq
    mod_dur_years = mac_dur_years / (1 + y)
    convexity_years = (convexity_sum / price) / (freq ** 2)

    return price, mac_dur_years, mod_dur_years, convexity_years


def bond_pv_cashflow_curve(face, coupon_rate_annual, ytm_annual, n_periods, freq):
    """PV of each individual cash flow (for the duration 'center of mass' chart)."""
    y = ytm_annual / freq
    cfs = bond_cashflows(face, coupon_rate_annual, n_periods, freq)
    years = [t / freq for t, _ in cfs]
    pvs = [cf * (1 + y) ** -t for t, cf in cfs]
    return years, pvs


def bond_price_approx(price0, mod_dur, convexity, dy, use_convexity=True):
    """First-order (duration-only) or second-order (duration+convexity)
    Taylor approximation of the new bond price after an annual yield
    shift of dy (e.g. dy=0.01 for +100bp)."""
    pct_change = -mod_dur * dy
    if use_convexity:
        pct_change += 0.5 * convexity * dy ** 2
    return price0 * (1 + pct_change)


# ============================================================
# CURRENCY / FORMATTING
# ============================================================
CURRENCY_PRESETS = {
    "Turkish Lira": ("TL", "suffix", "period"),
    "US Dollar": ("$", "prefix", "comma"),
    "Euro": ("€", "suffix", "period"),
    "British Pound": ("£", "prefix", "comma"),
    "Japanese Yen": ("¥", "prefix", "comma"),
    "Indian Rupee": ("₹", "prefix", "comma"),
    "Custom / Other": ("", "suffix", "comma"),
}

FREQ_MAP = {
    "Annual (1/yr)": 1,
    "Semiannual (2/yr)": 2,
    "Quarterly (4/yr)": 4,
    "Monthly (12/yr)": 12,
}


def fmt_money(x, decimals=0):
    """Format a number using the session's chosen currency symbol, position, and
    thousands/decimal separator convention."""
    symbol = st.session_state.get("cur_symbol", "TL")
    position = st.session_state.get("cur_position", "suffix")
    sep_style = st.session_state.get("cur_sepstyle", "period")

    sign = "-" if x < 0 else ""
    x = abs(x)
    s = f"{x:,.{decimals}f}"  # e.g. "1,234,567.89" (US style by default)

    if sep_style == "period":
        # swap , and . to get European/Turkish style: 1.234.567,89
        s = s.replace(",", "\u0001").replace(".", ",").replace("\u0001", ".")

    if position == "prefix":
        return f"{sign}{symbol}{s}".strip()
    else:
        return f"{sign}{s} {symbol}".strip()


def fmt_pct(x, decimals=1):
    return f"{x*100:.{decimals}f}%"


def fmt_num(x, decimals=0):
    s = f"{x:,.{decimals}f}"
    if st.session_state.get("cur_sepstyle", "period") == "period":
        s = s.replace(",", "\u0001").replace(".", ",").replace("\u0001", ".")
    return s


# ============================================================
# UI HELPERS
# ============================================================
def stat_card(label, value, sub="", color="ink"):
    color_class = f" {color}" if color != "ink" else ""
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    return (
        f'<div class="stat"><div class="label">{label}</div>'
        f'<div class="value{color_class}">{value}</div>{sub_html}</div>'
    )


def stat_row(cards):
    cols = st.columns(len(cards))
    for c, card_html in zip(cols, cards):
        with c:
            st.markdown(card_html, unsafe_allow_html=True)


def verdict_box(good, text):
    cls = "good" if good else "bad"
    html = f'<div class="verdict {cls}"><span class="vt">Verdict</span>{text}</div>'
    st.markdown(html, unsafe_allow_html=True)


def note(text):
    html = f'<div class="note">{text}</div>'
    st.markdown(html, unsafe_allow_html=True)


def make_plot(title, xlabel, ylabel):
    fig = go.Figure()
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor=COL_CARD,
        plot_bgcolor=COL_CARD,
        font=dict(family="Georgia, serif", color=COL_INK, size=12),
        xaxis=dict(title=xlabel, gridcolor=COL_GRID, zeroline=False,
                   linecolor=COL_INK, tickfont=dict(family="ui-monospace, monospace")),
        yaxis=dict(title=ylabel, gridcolor=COL_GRID, zeroline=False,
                   linecolor=COL_INK, tickfont=dict(family="ui-monospace, monospace")),
        height=360,
        showlegend=False,
        hovermode="x unified",
    )
    return fig


# ============================================================
# SIDEBAR — currency & display settings (applies to all tabs)
# ============================================================
with st.sidebar:
    st.markdown("## 🏦 Toolkit Settings")
    st.markdown("### Currency")
    preset_name = st.selectbox(
        "Currency preset",
        list(CURRENCY_PRESETS.keys()),
        index=0,
        help="Pick a common currency, or 'Custom / Other' to type your own symbol or code. "
             "This only changes how numbers are *displayed* — every calculation below works "
             "identically regardless of currency.",
    )
    preset_symbol, preset_position, preset_sep = CURRENCY_PRESETS[preset_name]

    if preset_name == "Custom / Other":
        cur_symbol = st.text_input("Currency symbol or code", value="")
    else:
        cur_symbol = st.text_input("Currency symbol or code (editable)", value=preset_symbol)

    cur_position = st.radio(
        "Symbol position", ["prefix", "suffix"],
        index=0 if preset_position == "prefix" else 1,
        format_func=lambda v: "Before amount ($ 1,234)" if v == "prefix" else "After amount (1,234 TL)",
        horizontal=True,
    )
    cur_sepstyle = st.radio(
        "Number format",
        ["comma", "period"],
        index=0 if preset_sep == "comma" else 1,
        format_func=lambda v: "1,234,567.89" if v == "comma" else "1.234.567,89",
        horizontal=True,
    )

    st.session_state["cur_symbol"] = cur_symbol
    st.session_state["cur_position"] = cur_position
    st.session_state["cur_sepstyle"] = cur_sepstyle

    st.markdown("---")
    st.markdown(
        "<span style='font-size:12px; color:#000000; font-style:italic;'>"
        "All figures are computed with standard time-value-of-money formulas "
        "(annuity PV/payment, Macaulay duration, effective annual rate, and the "
        "Fisher equation). Default numbers illustrate a high-inflation TL-style "
        "market, but every input can be typed exactly and the currency is fully "
        "generic.</span>",
        unsafe_allow_html=True,
    )

# ============================================================
# HEADER
# ============================================================
st.markdown(
    '<div class="app-header">'
    '<h1>Mortgage &amp; Bond Math Toolkit</h1>'
    '<div class="sub">Type any rate, payment, or amount exactly — every table, verdict, and chart '
    'updates immediately. Works with any currency.</div>'
    '<span class="tag">Currency-agnostic &middot; fixed-rate mortgages &middot; bond pricing &middot; exact numeric entry</span>'
    '</div>',
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs([
    "01 · Borrowing Capacity",
    "02 · Refinance Decision",
    "03 · Cash vs. Loan",
    "04 · Bond Pricing",
])

# ============================================================
# TAB 1 — BORROWING CAPACITY
# ============================================================
with tab1:
    left, right = st.columns([1, 2], gap="large")

    with left:
        with st.container(border=True):
            st.markdown('<div class="card-title">Assumptions</div>', unsafe_allow_html=True)
            r1_pct = st.number_input(
                "Monthly interest rate (%)", min_value=0.0, max_value=50.0,
                value=3.20, step=0.05, format="%.2f", key="r1",
                help="Nominal monthly rate on the mortgage.",
            )
            m1 = st.number_input(
                f"Affordable monthly payment", min_value=0.0, max_value=None,
                value=50000.0, step=1000.0, format="%.2f", key="m1",
                help="The maximum monthly payment the borrower can comfortably afford.",
            )
            term1_years = st.number_input(
                "Term to inspect closely (years)", min_value=0.25, max_value=100.0,
                value=8.0, step=0.25, format="%.2f", key="term1",
            )
        note(
            "Formula: <b>P = M · [1 − (1+r)<sup>−n</sup>] / r</b>, with n = 12 × years. "
            "Duration uses the Macaulay-duration definition on the same level-payment stream."
        )

    with right:
        r1 = r1_pct / 100.0
        n1 = term1_years * 12
        P1 = annuity_pv(m1, r1, n1)
        D1 = macaulay_duration_months(r1, n1)
        ceiling1 = m1 / r1 if r1 > 1e-12 else float("inf")

        stat_row([
            stat_card("Max. loan (selected term)", fmt_money(P1), f"{n1:.0f} monthly payments", "ledger"),
            stat_card("Effective annual rate", fmt_pct(ear(r1)), color="gold"),
            stat_card("Duration (selected term)", f"{D1/12:.2f} yrs"),
            stat_card("Theoretical ceiling (n→∞)", fmt_money(ceiling1) if math.isfinite(ceiling1) else "∞"),
        ])

        st.write("")
        with st.container(border=True):
            st.markdown('<div class="card-title">Reference-term comparison</div>', unsafe_allow_html=True)
            ref_terms = sorted(set([5.0, 8.0, 10.0, round(term1_years, 2)]))
            table_md = "| Term | Months | Max. loan | Duration (yrs) |\n|---:|---:|---:|---:|\n"
            for y in ref_terms:
                nn = y * 12
                PP = annuity_pv(m1, r1, nn)
                DD = macaulay_duration_months(r1, nn) / 12
                is_sel = math.isclose(y, term1_years, abs_tol=1e-6)
                y_label = f"**{y:g} years**" if is_sel else f"{y:g} years"
                table_md += (
                    f"| {y_label} | {nn:.0f} | "
                    f"{'**' if is_sel else ''}{fmt_money(PP)}{'**' if is_sel else ''} | "
                    f"{'**' if is_sel else ''}{DD:.2f}{'**' if is_sel else ''} |\n"
                )
            st.markdown(table_md)

        st.write("")
        with st.container(border=True):
            st.markdown(
                '<div class="chart-title">Borrowing power vs. term — saturates near the ceiling M/r</div>',
                unsafe_allow_html=True,
            )
            x_max = max(15.0, term1_years * 1.3)
            xs = [i * 0.1 for i in range(2, int(x_max * 10) + 1)]
            ys = [annuity_pv(m1, r1, x * 12) for x in xs]

            fig1 = make_plot("", "term (years)", f"max loan")
            fig1.add_trace(go.Scatter(
                x=xs, y=ys, mode="lines", line=dict(color=COL_LEDGER, width=2.6),
                name="Max loan", hovertemplate="term=%{x:.2f}y<br>loan=%{y:,.0f}<extra></extra>",
            ))
            if math.isfinite(ceiling1):
                fig1.add_hline(y=ceiling1, line=dict(color=COL_BRICK, width=1.6, dash="dash"),
                                annotation_text=f"ceiling M/r = {fmt_money(ceiling1)}",
                                annotation_position="top left",
                                annotation_font_color=COL_BRICK)
            for y in [5, 8, 10]:
                fig1.add_trace(go.Scatter(
                    x=[y], y=[annuity_pv(m1, r1, y * 12)], mode="markers",
                    marker=dict(color=COL_GOLD, size=9),
                    hovertemplate=f"{y}y<br>%{{y:,.0f}}<extra></extra>",
                ))
            fig1.add_trace(go.Scatter(
                x=[term1_years], y=[P1], mode="markers",
                marker=dict(color=COL_BRICK, size=13, line=dict(color="white", width=1)),
                hovertemplate=f"selected {term1_years:g}y<br>%{{y:,.0f}}<extra></extra>",
            ))
            st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})


# ============================================================
# TAB 2 — REFINANCE DECISION
# ============================================================
with tab2:
    left, right = st.columns([1, 2], gap="large")

    with left:
        with st.container(border=True):
            st.markdown('<div class="card-title">Original loan</div>', unsafe_allow_html=True)
            P0 = st.number_input(
                "Original principal", min_value=0.0, max_value=None,
                value=2_000_000.0, step=50_000.0, format="%.2f", key="P0",
            )
            rold_pct = st.number_input(
                "Original monthly rate (%)", min_value=0.0, max_value=50.0,
                value=3.00, step=0.05, format="%.2f", key="rold",
            )
            nyears = st.number_input(
                "Original term (years)", min_value=0.25, max_value=100.0,
                value=10.0, step=0.25, format="%.2f", key="nyears",
            )
            n_total = int(round(nyears * 12))
            k_paid = st.number_input(
                "Months already paid", min_value=0, max_value=max(n_total - 1, 0),
                value=min(12, max(n_total - 1, 0)), step=1, key="k",
            )

        with st.container(border=True):
            st.markdown('<div class="card-title">Refinance offer</div>', unsafe_allow_html=True)
            rnew_pct = st.number_input(
                "New monthly rate (%)", min_value=0.0, max_value=50.0,
                value=2.00, step=0.05, format="%.2f", key="rnew",
            )
            pen1_pct = st.number_input(
                "Penalty if remaining > 36 mo (%)", min_value=0.0, max_value=25.0,
                value=2.00, step=0.25, format="%.2f", key="pen1",
            )
            pen2_pct = st.number_input(
                "Penalty if remaining ≤ 36 mo (%)", min_value=0.0, max_value=25.0,
                value=1.00, step=0.25, format="%.2f", key="pen2",
            )

    with right:
        rold = rold_pct / 100.0
        rnew = rnew_pct / 100.0
        pen1 = pen1_pct / 100.0
        pen2 = pen2_pct / 100.0

        M_old, B, n_rem = remaining_balance(P0, rold, n_total, k_paid)
        M_new = payment(B, rnew, n_rem) if n_rem > 0 else 0.0
        saving = M_old - M_new
        tier = pen1 if n_rem > 36 else pen2
        tier_label = (f">36 mo remaining → {pen1_pct:.2f}%" if n_rem > 36
                      else f"≤36 mo remaining → {pen2_pct:.2f}%")
        penalty = tier * B
        payback = penalty / saving if saving > 0 else float("inf")
        annuity_factor_new = (1 - (1 + rnew) ** -n_rem) / rnew if rnew > 1e-12 and n_rem > 0 else n_rem
        npv = saving * annuity_factor_new - penalty

        stat_row([
            stat_card("Remaining balance B", fmt_money(B)),
            stat_card("Remaining term", f"{n_rem} mo"),
            stat_card("Old payment → New payment", f"{fmt_money(M_old)} → {fmt_money(M_new)}", color="ledger"),
            stat_card("Monthly saving", f"{fmt_money(saving)}/mo", color="gold"),
        ])
        st.write("")
        stat_row([
            stat_card("Penalty tier applied", tier_label),
            stat_card("Penalty amount", fmt_money(penalty), color="brick"),
            stat_card("Simple payback", f"{payback:.1f} mo" if math.isfinite(payback) else "—"),
            stat_card("NPV of refinancing", fmt_money(npv)),
        ])

        st.write("")
        if npv > 0:
            verdict_box(True, f"NPV is positive ({fmt_money(npv)}): refinancing more than pays for "
                               f"the penalty over the remaining {n_rem} months. <b>Refinance.</b>")
        else:
            verdict_box(False, f"NPV is not positive ({fmt_money(npv)}): the penalty outweighs the "
                                f"discounted savings. <b>Keep the current loan.</b>")

        st.write("")
        with st.container(border=True):
            st.markdown(
                '<div class="chart-title">Cumulative savings vs. upfront penalty</div>',
                unsafe_allow_html=True,
            )
            step = max(1, round(n_rem / 60)) if n_rem > 0 else 1
            xs = list(range(0, n_rem + 1, step))
            if xs[-1] != n_rem:
                xs.append(n_rem)
            ys = [saving * t for t in xs]

            fig2 = make_plot("", "months since refinancing", "cumulative savings")
            fig2.add_trace(go.Scatter(
                x=xs, y=ys, mode="lines", line=dict(color=COL_LEDGER, width=2.6),
                hovertemplate="month %{x}<br>saved %{y:,.0f}<extra></extra>",
            ))
            fig2.add_hline(y=penalty, line=dict(color=COL_BRICK, width=1.6, dash="dash"),
                            annotation_text=f"penalty = {fmt_money(penalty)}",
                            annotation_position="top left",
                            annotation_font_color=COL_BRICK)
            if math.isfinite(payback) and payback <= n_rem:
                fig2.add_trace(go.Scatter(
                    x=[payback], y=[penalty], mode="markers",
                    marker=dict(color=COL_GOLD, size=11),
                    hovertemplate=f"breakeven ≈ {payback:.1f} mo<extra></extra>",
                ))
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        note(
            "NPV discounts the stream of monthly savings at the <b>new</b> loan's own rate over the "
            "remaining term, then subtracts the upfront penalty — a common simplifying convention. "
            "The simple payback (used for the gold breakeven marker) ignores discounting entirely."
        )


# ============================================================
# TAB 3 — CASH VS. LOAN
# ============================================================
with tab3:
    left, right = st.columns([1, 2], gap="large")

    with left:
        with st.container(border=True):
            st.markdown('<div class="card-title">The purchase</div>', unsafe_allow_html=True)
            house = st.number_input(
                "House price", min_value=0.0, max_value=None,
                value=20_000_000.0, step=500_000.0, format="%.2f", key="house",
            )
            cash = st.number_input(
                "Own cash available", min_value=0.0, max_value=None,
                value=20_000_000.0, step=500_000.0, format="%.2f", key="cash",
            )
            max_loan = st.number_input(
                "Maximum loan obtainable", min_value=0.0, max_value=None,
                value=10_000_000.0, step=250_000.0, format="%.2f", key="maxloan",
            )
            loan_amt_default = min(10_000_000.0, max_loan)
            loan_amt = st.number_input(
                "Loan amount to actually take", min_value=0.0, max_value=max_loan,
                value=loan_amt_default, step=250_000.0, format="%.2f", key="loanamt",
            )

        with st.container(border=True):
            st.markdown('<div class="card-title">Rates</div>', unsafe_allow_html=True)
            rloan_pct = st.number_input(
                "Loan monthly rate (%)", min_value=0.0, max_value=50.0,
                value=3.00, step=0.05, format="%.2f", key="rloan",
            )
            loan_years = st.number_input(
                "Loan term (years)", min_value=0.25, max_value=100.0,
                value=10.0, step=0.25, format="%.2f", key="loanyears",
            )
            rcash_pct = st.number_input(
                "Cash / money-market monthly rate (%)", min_value=0.0, max_value=50.0,
                value=4.00, step=0.05, format="%.2f", key="rcash",
            )
            infl_pct = st.number_input(
                "Annual inflation (%)", min_value=0.0, max_value=500.0,
                value=30.0, step=0.5, format="%.2f", key="infl",
            )

    with right:
        r_loan = rloan_pct / 100.0
        n = int(round(loan_years * 12))
        r_cash = rcash_pct / 100.0
        infl = infl_pct / 100.0

        EAR_loan = ear(r_loan)
        EAR_cash = ear(r_cash)
        real_loan = fisher_real(EAR_loan, infl)
        real_cash = fisher_real(EAR_cash, infl)
        breakeven_infl = EAR_loan

        stat_row([
            stat_card("Loan EAR", fmt_pct(EAR_loan), color="brick"),
            stat_card("Cash EAR", fmt_pct(EAR_cash), color="ledger"),
            stat_card("Real rate of loan (Fisher)", fmt_pct(real_loan)),
            stat_card("Real rate of cash (Fisher)", fmt_pct(real_cash)),
        ])

        cash_paid_upfront = house - loan_amt
        leftover_cash = cash - cash_paid_upfront
        M = payment(loan_amt, r_loan, n) if loan_amt > 0 else 0.0
        if loan_amt > 0:
            trace, depleted_at, final_bal = simulate_depletion(max(leftover_cash, 0.0), EAR_cash, M, n)
        else:
            depleted_at, final_bal, trace = None, leftover_cash, [(0, leftover_cash)]

        st.write("")
        stat_row([
            stat_card("Breakeven inflation (= loan EAR)", fmt_pct(breakeven_infl), color="gold"),
            stat_card("Investment depletes at", f"month {depleted_at}" if depleted_at else
                      ("never (grows throughout)" if loan_amt > 0 else "—")),
            stat_card("Net position at term end", fmt_money(final_bal) + (" (shortfall)" if final_bal < 0 else "")),
            stat_card("Total paid over term", f"{fmt_money(M*n)} (interest {fmt_money(M*n - loan_amt)})" if loan_amt > 0 else "—"),
        ])

        st.write("")
        if loan_amt == 0:
            verdict_box(True, f"Paying fully in cash. With loan EAR {fmt_pct(EAR_loan)} vs. cash EAR "
                               f"{fmt_pct(EAR_cash)}, this is the value-maximizing choice whenever the "
                               f"loan rate exceeds the cash return by this much.")
        elif EAR_loan > EAR_cash:
            verdict_box(False, f"Financing {fmt_money(loan_amt)} costs {fmt_pct(EAR_loan)} EAR while idle "
                                f"cash earns only {fmt_pct(EAR_cash)} EAR — a negative carry of "
                                f"{fmt_pct(EAR_loan-EAR_cash)}/yr. At today's assumed inflation "
                                f"({fmt_pct(infl)}), the loan's real cost is {fmt_pct(real_loan)}. Unless "
                                f"you value the liquidity itself, financing less would be cheaper.")
        else:
            verdict_box(True, f"Cash EAR ({fmt_pct(EAR_cash)}) exceeds the loan EAR ({fmt_pct(EAR_loan)}) — "
                               f"a positive carry of {fmt_pct(EAR_cash-EAR_loan)}/yr. Leverage is attractive "
                               f"on a pure carry basis here, provided you trust that cash return to hold up "
                               f"(it is unlikely to be truly risk-free at this level).")

        st.write("")
        with st.container(border=True):
            st.markdown(
                '<div class="chart-title">If you finance the amount above: investment balance funding the mortgage over time</div>',
                unsafe_allow_html=True,
            )
            xs = [t for t, _ in trace]
            ys = [b for _, b in trace]
            fig3a = make_plot("", "month", "investment balance")
            fig3a.add_trace(go.Scatter(
                x=xs, y=ys, mode="lines", line=dict(color=COL_LEDGER, width=2.2),
                hovertemplate="month %{x}<br>balance %{y:,.0f}<extra></extra>",
            ))
            fig3a.add_hline(y=0, line=dict(color=COL_BRICK, width=1.3, dash="dash"))
            if depleted_at:
                fig3a.add_trace(go.Scatter(
                    x=[depleted_at], y=[0], mode="markers",
                    marker=dict(color=COL_GOLD, size=10),
                    hovertemplate=f"depletes at month {depleted_at}<extra></extra>",
                ))
            st.plotly_chart(fig3a, use_container_width=True, config={"displayModeBar": False})

        st.write("")
        with st.container(border=True):
            st.markdown(
                '<div class="chart-title">Real cost of the loan\'s payment stream, as a multiple of principal, vs. assumed inflation</div>',
                unsafe_allow_html=True,
            )
            princ_for_curve = loan_amt if loan_amt > 0 else 1_000_000.0
            M_fixed = M if loan_amt > 0 else payment(1_000_000.0, r_loan, n)
            infl_max_plot = max(80.0, breakeven_infl * 100 * 1.4)
            xs2 = list(range(1, int(infl_max_plot) + 1))
            ys2 = [pv_real_of_payments(M_fixed, n, p / 100.0) / princ_for_curve for p in xs2]

            fig3b = make_plot("", "annual inflation (%)", "real cost / principal")
            fig3b.add_trace(go.Scatter(
                x=xs2, y=ys2, mode="lines", line=dict(color=COL_LEDGER, width=2.2),
                hovertemplate="inflation %{x}%%<br>%{y:.2f}x<extra></extra>",
            ))
            fig3b.add_hline(y=1, line=dict(color=COL_BRICK, width=1.3, dash="dash"))
            fig3b.add_trace(go.Scatter(
                x=[breakeven_infl * 100], y=[1], mode="markers",
                marker=dict(color=COL_GOLD, size=12),
                hovertemplate=f"breakeven {fmt_pct(breakeven_infl)}<extra></extra>",
            ))
            fig3b.add_trace(go.Scatter(
                x=[infl_pct], y=[pv_real_of_payments(M_fixed, n, infl) / princ_for_curve], mode="markers",
                marker=dict(color=COL_BRICK, size=10),
                hovertemplate=f"today's assumption: {fmt_pct(infl)}<extra></extra>",
            ))
            st.plotly_chart(fig3b, use_container_width=True, config={"displayModeBar": False})

        note(
            "<b>Reading the second chart:</b> at low inflation a fixed-rate loan is expensive in real "
            "terms; the curve crosses 1.0× exactly at the loan's own effective annual rate — above that "
            "inflation rate the lender loses value in real terms and the borrower gains. The gold marker "
            "is the exact breakeven; the brick marker is today's assumed inflation."
        )


# ============================================================
# TAB 4 — BOND PRICING
# ============================================================
with tab4:
    left, right = st.columns([1, 2], gap="large")

    with left:
        with st.container(border=True):
            st.markdown('<div class="card-title">Bond terms</div>', unsafe_allow_html=True)
            face = st.number_input(
                "Face (par) value", min_value=0.01, max_value=None,
                value=1_000.0, step=100.0, format="%.2f", key="bface",
                help="Redemption value paid at maturity.",
            )
            coupon_pct = st.number_input(
                "Annual coupon rate (%)", min_value=0.0, max_value=100.0,
                value=8.00, step=0.25, format="%.2f", key="bcoupon",
                help="Total coupon paid per year, as a % of face value.",
            )
            freq_label = st.selectbox(
                "Coupon frequency", list(FREQ_MAP.keys()), index=1, key="bfreq",
            )
            years_b = st.number_input(
                "Years to maturity", min_value=0.25, max_value=100.0,
                value=10.0, step=0.25, format="%.2f", key="byears",
            )

        with st.container(border=True):
            st.markdown('<div class="card-title">Solve for price or yield?</div>', unsafe_allow_html=True)
            solve_mode = st.radio(
                "I know the bond's:",
                ["Market price → solve for yield", "Yield → solve for price"],
                index=0, key="bsolvemode",
            )
            if solve_mode.startswith("Market price"):
                market_price_input = st.number_input(
                    "Market price", min_value=0.01, max_value=None,
                    value=950.0, step=10.0, format="%.2f", key="bprice_in",
                )
                ytm_input_pct = None
            else:
                ytm_input_pct = st.number_input(
                    "Annual yield to maturity (%)", min_value=0.0, max_value=200.0,
                    value=9.00, step=0.10, format="%.2f", key="byield_in",
                )
                market_price_input = None

        note(
            "Standard bullet-bond assumptions: fixed coupon, redemption at par on maturity, "
            "valued as of a coupon date (no accrued-interest / day-count adjustment). "
            "Yield is solved by bisection — robust because price is monotonically decreasing "
            "in yield, so no starting guess or derivative is needed."
        )

    with right:
        freq = FREQ_MAP[freq_label]
        coupon_rate = coupon_pct / 100.0
        n_periods_b = max(int(round(years_b * freq)), 1)

        if solve_mode.startswith("Market price"):
            ytm = bond_ytm(market_price_input, face, coupon_rate, n_periods_b, freq)
        else:
            ytm = ytm_input_pct / 100.0

        price_b, mac_dur, mod_dur, convexity = bond_duration_convexity(
            face, coupon_rate, ytm, n_periods_b, freq
        )
        current_yield = (face * coupon_rate) / price_b if price_b > 0 else float("nan")
        price_pct_of_par = price_b / face * 100 if face > 0 else float("nan")

        stat_row([
            stat_card("Price", fmt_money(price_b), f"{price_pct_of_par:.2f}% of par", "ledger"),
            stat_card("Yield to maturity", fmt_pct(ytm, 3), color="gold"),
            stat_card("Macaulay duration", f"{mac_dur:.2f} yrs"),
            stat_card("Modified duration", f"{mod_dur:.2f} yrs"),
        ])
        st.write("")
        stat_row([
            stat_card("Convexity", f"{convexity:.2f}"),
            stat_card("Current yield (coupon/price)", fmt_pct(current_yield, 2)),
            stat_card("Annual coupon amount", fmt_money(face * coupon_rate)),
            stat_card("Periods to maturity", f"{n_periods_b} ({freq_label.split(' ')[0].lower()})"),
        ])

        st.write("")
        if abs(coupon_pct / 100.0 - ytm) < 1e-6:
            verdict_box(True, f"Coupon rate ({fmt_pct(coupon_rate,2)}) ≈ yield ({fmt_pct(ytm,2)}) — "
                               f"the bond is priced almost exactly <b>at par</b>.")
        elif coupon_rate > ytm:
            verdict_box(True, f"Coupon rate ({fmt_pct(coupon_rate,2)}) exceeds the yield "
                               f"({fmt_pct(ytm,2)}) — the bond trades at a <b>premium</b> "
                               f"({price_pct_of_par:.1f}% of par).")
        else:
            verdict_box(False, f"Coupon rate ({fmt_pct(coupon_rate,2)}) is below the yield "
                                f"({fmt_pct(ytm,2)}) — the bond trades at a <b>discount</b> "
                                f"({price_pct_of_par:.1f}% of par).")

        # ---- Teaching plot A: Price vs Yield, with duration & convexity approximations ----
        st.write("")
        with st.container(border=True):
            st.markdown(
                '<div class="chart-title">Price vs. yield — actual curve vs. duration-only and '
                'duration+convexity approximations</div>',
                unsafe_allow_html=True,
            )
            spread = max(0.05, ytm * 0.75)
            y_lo = max(0.0005, ytm - spread)
            y_hi = ytm + spread
            n_pts = 80
            ys_yield = [y_lo + i * (y_hi - y_lo) / (n_pts - 1) for i in range(n_pts)]
            prices_actual = [bond_price(face, coupon_rate, y, n_periods_b, freq) for y in ys_yield]
            prices_dur = [bond_price_approx(price_b, mod_dur, convexity, y - ytm, use_convexity=False)
                          for y in ys_yield]
            prices_durconv = [bond_price_approx(price_b, mod_dur, convexity, y - ytm, use_convexity=True)
                               for y in ys_yield]

            figA = make_plot("", "yield to maturity (%)", "price")
            figA.add_trace(go.Scatter(
                x=[y * 100 for y in ys_yield], y=prices_actual, mode="lines",
                line=dict(color=COL_LEDGER, width=2.6), name="Actual price",
                hovertemplate="yield=%{x:.2f}%<br>price=%{y:,.2f}<extra>Actual</extra>",
            ))
            figA.add_trace(go.Scatter(
                x=[y * 100 for y in ys_yield], y=prices_dur, mode="lines",
                line=dict(color=COL_GOLD, width=2.0, dash="dash"), name="Duration-only approx.",
                hovertemplate="yield=%{x:.2f}%<br>approx=%{y:,.2f}<extra>Duration only</extra>",
            ))
            figA.add_trace(go.Scatter(
                x=[y * 100 for y in ys_yield], y=prices_durconv, mode="lines",
                line=dict(color=COL_BRICK, width=2.0, dash="dot"), name="Duration + convexity approx.",
                hovertemplate="yield=%{x:.2f}%<br>approx=%{y:,.2f}<extra>Dur.+convexity</extra>",
            ))
            figA.add_trace(go.Scatter(
                x=[ytm * 100], y=[price_b], mode="markers",
                marker=dict(color=COL_INK, size=12, line=dict(color="white", width=1)),
                hovertemplate=f"current: {ytm*100:.2f}%, {price_b:,.2f}<extra></extra>",
            ))
            figA.update_layout(showlegend=True, legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                font=dict(size=10),
            ))
            st.plotly_chart(figA, use_container_width=True, config={"displayModeBar": False})

        note(
            "The actual price–yield curve <b>bows above</b> both straight-line approximations — this "
            "bowing is exactly what \"convexity\" measures. The duration-only (tangent) line "
            "underestimates price for both large rises and large falls in yield; adding the "
            "convexity term corrects most of that error."
        )

        # ---- Teaching plot B: % price change sensitivity ----
        st.write("")
        with st.container(border=True):
            st.markdown(
                '<div class="chart-title">Sensitivity: % price change vs. yield shift '
                '(exact vs. duration vs. duration+convexity)</div>',
                unsafe_allow_html=True,
            )
            dys = [y - ytm for y in ys_yield]
            pct_actual = [(p / price_b - 1) * 100 for p in prices_actual]
            pct_dur = [(-mod_dur * dy) * 100 for dy in dys]
            pct_durconv = [(-mod_dur * dy + 0.5 * convexity * dy ** 2) * 100 for dy in dys]

            figB = make_plot("", "yield shift, Δy (percentage points)", "% price change")
            figB.add_trace(go.Scatter(
                x=[dy * 100 for dy in dys], y=pct_actual, mode="lines",
                line=dict(color=COL_LEDGER, width=2.6), name="Exact",
                hovertemplate="Δy=%{x:+.2f}pp<br>Δprice=%{y:+.2f}%<extra>Exact</extra>",
            ))
            figB.add_trace(go.Scatter(
                x=[dy * 100 for dy in dys], y=pct_dur, mode="lines",
                line=dict(color=COL_GOLD, width=2.0, dash="dash"), name="Duration only",
                hovertemplate="Δy=%{x:+.2f}pp<br>approx=%{y:+.2f}%<extra>Duration only</extra>",
            ))
            figB.add_trace(go.Scatter(
                x=[dy * 100 for dy in dys], y=pct_durconv, mode="lines",
                line=dict(color=COL_BRICK, width=2.0, dash="dot"), name="Duration + convexity",
                hovertemplate="Δy=%{x:+.2f}pp<br>approx=%{y:+.2f}%<extra>Dur.+convexity</extra>",
            ))
            figB.add_vline(x=0, line=dict(color=COL_INK, width=1, dash="dot"))
            figB.add_hline(y=0, line=dict(color=COL_INK, width=1, dash="dot"))
            figB.update_layout(showlegend=True, legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                font=dict(size=10),
            ))
            st.plotly_chart(figB, use_container_width=True, config={"displayModeBar": False})

        note(
            "Reading this chart: for small yield shifts (near Δy = 0) all three lines nearly "
            "overlap — duration alone is a fine approximation for small moves. As |Δy| grows, the "
            "gold duration-only line visibly diverges from the exact green curve, while the brick "
            "duration+convexity line keeps tracking it — this is precisely why convexity matters "
            "for large-rate-move scenarios."
        )

        # ---- Teaching plot C: cash-flow PV "center of mass" = Macaulay duration ----
        st.write("")
        with st.container(border=True):
            st.markdown(
                '<div class="chart-title">Macaulay duration as the \'center of mass\' of discounted cash flows</div>',
                unsafe_allow_html=True,
            )
            cf_years, cf_pvs = bond_pv_cashflow_curve(face, coupon_rate, ytm, n_periods_b, freq)

            figC = make_plot("", "time to cash flow (years)", "present value of that cash flow")
            figC.add_trace(go.Bar(
                x=cf_years, y=cf_pvs, marker=dict(color=COL_LEDGER_L),
                hovertemplate="t=%{x:.2f}y<br>PV=%{y:,.2f}<extra></extra>",
                width=max(cf_years[0] * 0.6, 0.05) if cf_years else 0.1,
            ))
            figC.add_vline(
                x=mac_dur, line=dict(color=COL_BRICK, width=2.2, dash="dash"),
                annotation_text=f"Macaulay duration = {mac_dur:.2f} yrs",
                annotation_position="top right",
                annotation_font_color=COL_BRICK,
            )
            st.plotly_chart(figC, use_container_width=True, config={"displayModeBar": False})

        note(
            "Each bar is the present value of one coupon (the tall final bar also includes the "
            "redemption of face value). Macaulay duration is the <b>time-weighted average</b> of "
            "these discounted cash flows — literally the balance point if you imagine the bars sitting "
            "on a seesaw. A bond with a large final principal repayment (like this one) has most of "
            "its 'weight' near maturity, pulling duration close to (but always below) the maturity date."
        )

st.markdown("---")
st.caption(
    "Standalone tool — all computation runs locally in this app (no external financial data or APIs). "
    "Default figures illustrate a high-inflation, TL-style market, following the original companion "
    "tool's assumptions, but every input, and the currency itself, is fully editable above."
)

# ============================================================
# TAB-LABEL COLOR — reinforced, injected LAST
#
# CSS cascade ties (equal specificity + !important) are broken by
# source order: the rule that appears LATER in the document wins.
# Injecting this block at the very end (after the tabs already
# exist in the DOM) gives it the best possible chance of overriding
# Streamlit's own tab styling, which is exactly what was winning
# before (shown by the default red hover color coming through).
# ============================================================
st.markdown(f"""
<style>
  .stTabs [role="tablist"] [role="tab"],
  .stTabs [role="tablist"] [role="tab"] *,
  .stTabs [data-baseweb="tab-list"] button,
  .stTabs [data-baseweb="tab-list"] button *,
  .stTabs [data-baseweb="tab"],
  .stTabs [data-baseweb="tab"] * {{
      color: {COL_INK} !important;
  }}
  .stTabs [role="tablist"] [role="tab"]:hover,
  .stTabs [role="tablist"] [role="tab"]:hover *,
  .stTabs [data-baseweb="tab-list"] button:hover,
  .stTabs [data-baseweb="tab-list"] button:hover * {{
      color: {COL_INK} !important;
  }}
  .stTabs [role="tablist"] [role="tab"][aria-selected="true"],
  .stTabs [role="tablist"] [role="tab"][aria-selected="true"] *,
  .stTabs [data-baseweb="tab-list"] button[aria-selected="true"],
  .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] * {{
      color: {COL_INK} !important;
      font-weight: bold;
  }}
  /* Kill the red highlight bar Streamlit draws under the active tab,
     matching it to the app's palette instead. */
  .stTabs [data-baseweb="tab-highlight"] {{
      background-color: {COL_LEDGER} !important;
  }}
  .stTabs [data-baseweb="tab-border"] {{
      background-color: {COL_LINE} !important;
  }}
</style>
""", unsafe_allow_html=True)
