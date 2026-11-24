"""
Publication figure generation script compliant with TJEECS graphic specifications:
- Font: Times New Roman with STIX math text
- Line weights: all lines (curves, grids, spines, ticks) strictly within 0.5-1.0 pt
- Dimensions: width 8-16 cm, height <= 20 cm
- Output: vector PDF (empty metadata) + 310 dpi PNG (>118 px/cm)
"""

import os
import sys
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import fitz

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from reliability_model.ctmc_model import WeightedSystemCTMC
from reliability_model.policies import PolicyI_CostModel
from reliability_model.optimizer import SystemOptimizer

FIG_DIR = ROOT_DIR / "figures"
RES_DIR = ROOT_DIR / "results"
FIG_DIR.mkdir(parents=True, exist_ok=True)

CM_TO_IN = 1.0 / 2.54
DPI = 310

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 8.0,
    "axes.titlesize": 8.5,
    "axes.labelsize": 8.0,
    "xtick.labelsize": 7.0,
    "ytick.labelsize": 7.0,
    "legend.fontsize": 6.8,
    "axes.linewidth": 0.60,
    "grid.linewidth": 0.50,
    "grid.linestyle": ":",
    "grid.color": "#cccccc",
    "lines.linewidth": 0.90,
    "patch.linewidth": 0.60,
    "xtick.major.width": 0.55,
    "ytick.major.width": 0.55,
    "xtick.minor.width": 0.50,
    "ytick.minor.width": 0.50,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.pad_inches": 0.04,
})


def strip_pdf_metadata(pdf_path: Path) -> None:
    tmp_path = pdf_path.with_suffix(".tmp.pdf")
    doc = fitz.open(str(pdf_path))
    doc.set_metadata({})
    try:
        doc.del_xml_metadata()
    except Exception:
        pass
    doc.save(str(tmp_path), garbage=4, deflate=True)
    doc.close()
    shutil.move(str(tmp_path), str(pdf_path))


def save_figure(fig: plt.Figure, stem: str) -> None:
    png_path = FIG_DIR / f"{stem}.png"
    pdf_path = FIG_DIR / f"{stem}.pdf"
    fig.savefig(str(png_path), dpi=DPI, bbox_inches="tight", metadata={})
    fig.savefig(str(pdf_path), bbox_inches="tight", metadata={})
    plt.close(fig)
    strip_pdf_metadata(pdf_path)
    print(f"Saved {stem}.{{pdf,png}}")


def generate_fig1_mechanism_curves() -> None:
    rho_dense = np.linspace(1.03, 1.15, 25)
    rho_table = np.array([1.03, 1.05, 1.08, 1.10, 1.12, 1.15])

    fig, axes = plt.subplots(1, 3, figsize=(15.5 * CM_TO_IN, 5.6 * CM_TO_IN), dpi=DPI)
    ax_a, ax_b, ax_c = axes

    # Panel (a): Calibration curves gamma(rho)
    mech_specs = [
        ("Rotor (MF = 2.00)", 2.00, "#1f77b4", "-"),
        ("HGP B/E (MF = 6.05)", 6.05, "#d62728", "--"),
        ("HGP F ref. (MF = 9.97)", float(np.exp(2.3)), "#555555", ":"),
    ]
    for label, mf, col, ls in mech_specs:
        ax_a.plot(rho_dense, np.log(mf) / np.log(rho_dense), color=col, linestyle=ls, linewidth=0.95, label=label)
        ax_a.plot(rho_table, np.log(mf) / np.log(rho_table), "o", color=col, markersize=2.6, markeredgewidth=0.5)
    ax_a.set_title("(a) Mechanism Calibration Curves", pad=4)
    ax_a.set_xlabel(r"Overload ratio $\rho = P_{\mathrm{peak}} / P_{\mathrm{base}}$")
    ax_a.set_ylabel(r"Stress exponent $\gamma(\rho)$")
    ax_a.set_xlim(1.026, 1.154)
    ax_a.set_ylim(0, 82)
    ax_a.grid(True, alpha=0.7)
    ax_a.legend(loc="upper right", frameon=True, framealpha=0.92, edgecolor="#888888")

    # Panel (b) & (c): CT Area 1-3 response at k/W0=0.70, c2/c1=5 across dense rho
    areas = [
        ("CT Area 1", 11, 4, 465, "#1f77b4"),
        ("CT Area 2", 13, 4, 575, "#2ca02c"),
        ("CT Area 3", 15, 4, 685, "#d62728"),
    ]
    w1, w2 = 20, 55
    lam1_0, lam2_0 = 1.0 / 450.0, 1.0 / 969.0
    c1, c2 = 1.0, 5.0
    rho_eval = np.array([1.03, 1.04, 1.05, 1.06, 1.07, 1.08, 1.09, 1.10, 1.11, 1.12, 1.13, 1.14, 1.15])

    for name, n, m, W0, col in areas:
        k = int(np.ceil(0.70 * W0))
        ctmc0 = WeightedSystemCTMC(n, m, k, w1, w2, lam1_0, lam2_0, 0.0, 0.0)
        t_ind, _ = SystemOptimizer.optimize_t_policy_I(ctmc0, c1, c2, t_ub=2000.0)

        for mech_tag, mf, ls in [("Rotor", 2.00, "-"), ("HGP", 6.05, "--")]:
            t_vals = []
            pen_vals = []
            for r in rho_eval:
                g = np.log(mf) / np.log(r)
                ctmc = WeightedSystemCTMC(n, m, k, w1, w2, lam1_0, lam2_0, g, g)
                t_opt, bzm_opt = SystemOptimizer.optimize_t_policy_I(ctmc, c1, c2, t_ub=2000.0)
                mod = PolicyI_CostModel(ctmc, c1, c2)
                bzm_naive = mod.cost_rate(float(t_ind))
                pen = (bzm_naive - bzm_opt) / bzm_opt * 100.0
                t_vals.append(t_opt if np.isfinite(t_opt) else np.nan)
                pen_vals.append(pen)

            lbl = f"{name} ({mech_tag})" if mech_tag == "Rotor" else f"{name} ({mech_tag})"
            ax_b.plot(rho_eval, t_vals, color=col, linestyle=ls, linewidth=0.85, label=lbl if name != "CT Area 2" else None)
            ax_c.plot(rho_eval, pen_vals, color=col, linestyle=ls, linewidth=0.85, label=lbl)

    ax_b.set_title(r"(b) Optimal Age $t^*$ ($k/W_0=0.70$)", pad=4)
    ax_b.set_xlabel(r"Overload ratio $\rho$")
    ax_b.set_ylabel(r"Optimal replacement age $t^*$ (h)")
    ax_b.set_xlim(1.026, 1.154)
    ax_b.set_ylim(30, 128)
    ax_b.text(1.032, 33.5, r"HGP $t^*=\infty$ for $\rho \leq 1.05$", fontsize=6.0, color="#444444")
    ax_b.grid(True, alpha=0.7)
    # Compact custom legend for line style & color in panel (b)
    from matplotlib.lines import Line2D
    handles_b = [
        Line2D([0], [0], color="#1f77b4", lw=0.85, ls="-", label="Area 1 Rotor"),
        Line2D([0], [0], color="#2ca02c", lw=0.85, ls="-", label="Area 2 Rotor"),
        Line2D([0], [0], color="#d62728", lw=0.85, ls="-", label="Area 3 Rotor"),
        Line2D([0], [0], color="#333333", lw=0.85, ls="--", label="Dashed: HGP B/E"),
    ]
    ax_b.legend(handles=handles_b, loc="upper right", fontsize=6.2, frameon=True, framealpha=0.92, edgecolor="#888888", handlelength=1.8)

    ax_c.set_title(r"(c) Naive $\gamma=0$ Cost Penalty $\Delta\eta\%$", pad=4)
    ax_c.set_xlabel(r"Overload ratio $\rho$")
    ax_c.set_ylabel(r"Cost penalty $\Delta\eta\%$ (%)")
    ax_c.set_xlim(1.026, 1.154)
    ax_c.set_ylim(-1.5, 48.0)
    ax_c.grid(True, alpha=0.7)
    handles_c = [
        Line2D([0], [0], color="#1f77b4", lw=0.85, ls="-", label="Area 1"),
        Line2D([0], [0], color="#2ca02c", lw=0.85, ls="-", label="Area 2"),
        Line2D([0], [0], color="#d62728", lw=0.85, ls="-", label="Area 3"),
        Line2D([0], [0], color="#333333", lw=0.85, ls="-", label="Solid: Rotor"),
        Line2D([0], [0], color="#333333", lw=0.85, ls="--", label="Dashed: HGP B/E"),
    ]
    ax_c.legend(handles=handles_c, loc="upper left", ncol=2, fontsize=6.0, frameon=True, framealpha=0.92, edgecolor="#888888", handlelength=1.6, columnspacing=0.9)

    fig.tight_layout(w_pad=1.0)
    save_figure(fig, "fig1_mechanism_curves")


def generate_fig2_turning_point() -> None:
    curves_df = pd.read_csv(RES_DIR / "case_E3_turning_point_curves.csv")
    summ_df = pd.read_csv(RES_DIR / "case_E3_turning_point_summary.csv")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.5 * CM_TO_IN, 6.2 * CM_TO_IN), dpi=DPI)
    specs = [
        ("CT_Area1", "CT Area 1", "#1f77b4", "-"),
        ("CT_Area2", "CT Area 2", "#2ca02c", "-"),
        ("CT_Area3", "CT Area 3", "#d62728", "-"),
        ("Coal_Area1", "Coal Area 1", "#333333", "-."),
    ]

    for ax in (ax1, ax2):
        ax.axvspan(4.96, 23.45, color="#dceaf7", alpha=0.55, linewidth=0.0,
                   label=r"Rotor $[4.96, 23.45]$" if ax is ax1 else None)
        ax.axvspan(12.88, 60.90, color="#fde2dc", alpha=0.42, linewidth=0.0,
                   label=r"HGP B/E $[12.88, 60.90]$" if ax is ax1 else None)

    for arr_key, label, col, ls in specs:
        sub = curves_df[(curves_df["array"] == arr_key) & (curves_df["k_frac"] == 0.7) & (curves_df["c2_c1"] == 5)].copy()
        sub = sub[sub["gamma"] >= 0.45].sort_values("gamma")
        srow = summ_df[(summ_df["array"] == arr_key) & (summ_df["k_frac"] == 0.7) & (summ_df["c2_c1"] == 5)].iloc[0]

        sub_fin = sub[np.isfinite(sub["t_star_h"])]
        ax1.plot(sub_fin["gamma"], sub_fin["t_star_h"], color=col, linestyle=ls, linewidth=0.90, label=label)
        if bool(srow["turning_point_found"]):
            g_tp = float(srow["gamma_tp"])
            t_tp = float(srow["t_min_h"])
            g_cm = float(srow["gamma_cm_1pct"])
            ax1.plot(g_tp, t_tp, "*", color=col, markersize=5.0, markeredgewidth=0.5)
            ax1.axvline(g_cm, color=col, linestyle=":", linewidth=0.60, alpha=0.75)

        ax2.plot(sub["gamma"], sub["cm_gap_pct"], color=col, linestyle=ls, linewidth=0.90, label=label)

    ax1.set_xscale("log")
    ax1.set_xlim(0.5, 110)
    ax1.set_ylim(25, 345)
    ax1.set_title(r"(a) Optimal Age Trajectory $t^*(\gamma)$ ($k/W_0=0.70, c_2/c_1=5$)", pad=4)
    ax1.set_xlabel(r"Load-sharing stress exponent $\gamma$ (log scale)")
    ax1.set_ylabel(r"Optimal replacement age $t^*$ (h)")
    ax1.grid(True, which="major", alpha=0.7)
    ax1.legend(loc="upper right", fontsize=6.2, frameon=True, framealpha=0.92, edgecolor="#888888", ncol=1)

    ax2.set_xscale("log")
    ax2.set_xlim(0.5, 110)
    ax2.set_ylim(-1.0, 42.0)
    ax2.axhline(1.0, color="#111111", linestyle="--", linewidth=0.75, label="1% CM threshold")
    ax2.set_title(r"(b) Relative CM-Only Cost Gap vs. Stress Exponent", pad=4)
    ax2.set_xlabel(r"Load-sharing stress exponent $\gamma$ (log scale)")
    ax2.set_ylabel(r"$[\eta(\infty) - \eta^*]/\eta(\infty)$ (%)")
    ax2.grid(True, which="major", alpha=0.7)
    ax2.legend(loc="upper right", frameon=True, framealpha=0.92, edgecolor="#888888")

    fig.tight_layout(w_pad=1.2)
    save_figure(fig, "fig2_gamma_turning_point")


def generate_fig3_e4_heatmap() -> None:
    df4 = pd.read_csv(RES_DIR / "case_E4_consistency_map.csv")
    df4 = df4[df4["k_frac"] == 0.7].copy()

    ratios = [(1.00, r"$r_{\mathrm{OM}} = 1.00$ (Symmetric)"),
              (1.9574, r"$r_{\mathrm{OM}} = 1.96$ (EIA AEO 2026)"),
              (2.50, r"$r_{\mathrm{OM}} = 2.50$ (High Asymm.)")]
    arrays = [("CT_Area1", "CT Area 1 ($n=11, m_{\\mathrm{ref}}=4$)"),
              ("CT_Area3", "CT Area 3 ($n=15, m_{\\mathrm{ref}}=4$)")]

    gammas = sorted(df4["gamma"].unique(), reverse=True)
    cpens = sorted(df4["c_pen"].unique())

    fig, axes = plt.subplots(2, 3, figsize=(15.5 * CM_TO_IN, 8.6 * CM_TO_IN), dpi=DPI, sharex=True, sharey=True)
    vmax = 9.0

    for row_i, (arr_key, arr_lbl) in enumerate(arrays):
        for col_j, (r_val, r_lbl) in enumerate(ratios):
            ax = axes[row_i, col_j]
            sub = df4[(df4["array"] == arr_key) & (np.abs(df4["om_ratio"] - r_val) < 0.01)]
            mat = np.zeros((len(gammas), len(cpens)), dtype=int)
            for gi, g in enumerate(gammas):
                for ci, cp in enumerate(cpens):
                    cell = sub[(np.abs(sub["gamma"] - g) < 1e-4) & (sub["c_pen"] == cp)]
                    mat[gi, ci] = int(cell["m_star"].iloc[0])

            im = ax.imshow(mat, cmap="YlGnBu", vmin=0, vmax=vmax, aspect="auto")
            for gi in range(len(gammas)):
                for ci in range(len(cpens)):
                    val = mat[gi, ci]
                    txt_col = "#ffffff" if val >= 5 else "#111111"
                    weight = "bold" if 3 <= val <= 5 else "normal"
                    ax.text(ci, gi, f"{val}", ha="center", va="center", color=txt_col, fontsize=7.0, fontweight=weight)

            if row_i == 0:
                ax.set_title(r_lbl, pad=4)
            if row_i == 1:
                ax.set_xticks(range(len(cpens)))
                ax.set_xticklabels([str(c) for c in cpens])
                ax.set_xlabel(r"Outage penalty $c_{pen}$")
            if col_j == 0:
                ax.set_yticks(range(len(gammas)))
                ax.set_yticklabels([f"{g:.2f}" for g in gammas])
                ax.set_ylabel(f"{arr_lbl}\n" + r"Stress $\gamma$")

    cbar = fig.colorbar(im, ax=axes.ravel().tolist(), fraction=0.022, pad=0.02)
    cbar.outline.set_linewidth(0.55)
    cbar.ax.tick_params(width=0.50, labelsize=7.0)
    cbar.set_label(r"Optimal Type I count $m^*$", fontsize=7.5)

    fig.subplots_adjust(left=0.09, right=0.89, top=0.93, bottom=0.09, wspace=0.08, hspace=0.12)
    save_figure(fig, "fig3_e4_consistency_heatmap")


def generate_supplementary_figures() -> None:
    regimes = [
        ("Regime 0 (Independent)", 0.0, 0.0, "#1f77b4", "-"),
        ("Regime 1 (Symmetric 0.8)", 0.8, 0.8, "#2ca02c", "--"),
        ("Regime 2 (Asymmetric 1.5, 0.5)", 1.5, 0.5, "#ff7f0e", "-."),
        ("Regime 3 (Severe 1.5, 1.5)", 1.5, 1.5, "#d62728", ":"),
    ]

    # S1: Reliability, Early Hazard Rate & Regime 2 Tail Non-monotonicity
    t_vals_1 = np.linspace(0.01, 6.0, 150)
    t_tail = np.linspace(8.0, 37.0, 300)
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15.5 * CM_TO_IN, 5.4 * CM_TO_IN), dpi=DPI)
    short_labels = {
        "Regime 0 (Independent)": "Reg. 0 (0.0, 0.0)",
        "Regime 1 (Symmetric 0.8)": "Reg. 1 (0.8, 0.8)",
        "Regime 2 (Asymmetric 1.5, 0.5)": "Reg. 2 (1.5, 0.5)",
        "Regime 3 (Severe 1.5, 1.5)": "Reg. 3 (1.5, 1.5)",
    }
    for label, g1, g2, col, ls in regimes:
        ctmc = WeightedSystemCTMC(15, 5, 15, 1, 2, 0.2, 0.1, g1, g2)
        slbl = short_labels[label]
        ax1.plot(t_vals_1, [ctmc.reliability(float(t)) for t in t_vals_1], label=slbl, color=col, ls=ls, lw=0.85)
        ax2.plot(t_vals_1, [ctmc.hazard_rate(float(t)) for t in t_vals_1], label=slbl, color=col, ls=ls, lw=0.85)
    ax1.set_title(r"(a) Reliability $R_{sys}(t)$ ($m=5$)", pad=4)
    ax1.set_xlabel(r"Operational time $t$")
    ax1.set_ylabel(r"$R_{sys}(t)$")
    ax1.set_ylim(-0.02, 1.02)
    ax1.grid(True, alpha=0.7)
    ax1.legend(loc="lower left", fontsize=5.8, frameon=True, framealpha=0.92, edgecolor="#888888")

    ax2.set_title(r"(b) Early Hazard $h_{sys}(t)$ ($m=5$)", pad=4)
    ax2.set_xlabel(r"Operational time $t$")
    ax2.set_ylabel(r"$h_{sys}(t)$")
    ax2.set_ylim(0.0, 1.5)
    ax2.grid(True, alpha=0.7)
    ax2.legend(loc="upper left", fontsize=5.8, frameon=True, framealpha=0.92, edgecolor="#888888")

    tail_specs = [
        (5, "#1f77b4", "-"),
        (6, "#2ca02c", "--"),
        (7, "#ff7f0e", "-."),
        (8, "#d62728", ":"),
    ]
    for m_tail, col, ls in tail_specs:
        ctmc_t = WeightedSystemCTMC(15, m_tail, 15, 1, 2, 0.2, 0.1, 1.5, 0.5)
        h_vals = [ctmc_t.hazard_rate(float(t)) for t in t_tail]
        ax3.plot(t_tail, h_vals, label=f"$m={m_tail}$", color=col, ls=ls, lw=0.85)
    ax3.set_title(r"(c) Regime 2 Tail ($dh_{sys}/dt < 0$)", pad=4)
    ax3.set_xlabel(r"Operational time $t$")
    ax3.set_ylabel(r"$h_{sys}(t)$")
    ax3.set_xlim(8.0, 37.0)
    ax3.grid(True, alpha=0.7)
    ax3.legend(loc="lower right", fontsize=5.8, frameon=True, framealpha=0.92, edgecolor="#888888", ncol=2)

    fig.tight_layout(w_pad=0.9)
    save_figure(fig, "figS1_reliability_hazard")

    # S2: Policy I Cost Rate Convexity
    t_vals_2 = np.linspace(0.5, 5.0, 120)
    fig, ax = plt.subplots(figsize=(11.5 * CM_TO_IN, 6.8 * CM_TO_IN), dpi=DPI)
    for label, g1, g2, col, ls in regimes:
        ctmc = WeightedSystemCTMC(15, 5, 15, 1, 2, 0.2, 0.1, g1, g2)
        mod = PolicyI_CostModel(ctmc, 1.0, 5.0)
        t_opt, bzm_opt = SystemOptimizer.optimize_t_policy_I(ctmc, 1.0, 5.0)
        ax.plot(t_vals_2, [mod.cost_rate(float(t)) for t in t_vals_2],
                label=f"{label} ($t^*={t_opt:.2f}, \\eta^*={bzm_opt:.3f}$)", color=col, ls=ls, lw=0.90)
        ax.plot(t_opt, bzm_opt, "o", color=col, markersize=3.5, markeredgewidth=0.5)
    ax.set_title(r"Policy I Cost Rate $\eta_I(t)$ ($n=15, k=15, m=5$)", pad=4)
    ax.set_xlabel(r"Preventive replacement age $t$")
    ax.set_ylabel(r"$\eta_I(t)$")
    ax.set_ylim(0.4, 1.5)
    ax.grid(True, alpha=0.7)
    ax.legend(loc="upper right", frameon=True, framealpha=0.92, edgecolor="#888888")
    fig.tight_layout()
    save_figure(fig, "figS2_cost_convexity")

    # S3: Policy II Component-Mix MINLP
    df_s4 = pd.read_csv(RES_DIR / "synthetic_table4_policyII.csv")
    m_vals = df_s4["m"].values
    bzm_vals = df_s4["bzm_star"].values
    t_fin = df_s4["t_star"].replace([np.inf, "inf"], np.nan).astype(float).values
    best_idx = int(np.argmin(bzm_vals))

    fig, ax1 = plt.subplots(figsize=(12.5 * CM_TO_IN, 6.8 * CM_TO_IN), dpi=DPI)
    ax1.plot(m_vals, bzm_vals, "s-", color="#1f77b4", lw=0.90, markersize=3.2, label=r"$\eta_{II}^*(m)$")
    ax1.plot(m_vals[best_idx], bzm_vals[best_idx], "*", color="#d62728", markersize=7.0, markeredgewidth=0.5,
             label=f"Optimum $m^*={m_vals[best_idx]}$ ($\\eta^*={bzm_vals[best_idx]:.4f}$)")
    ax1.set_xlabel(r"Number of Type I units $m$")
    ax1.set_ylabel(r"Minimum cost rate $\eta_{II}^*$", color="#1f77b4")
    ax1.set_xticks(m_vals)
    ax1.set_ylim(1.2, 6.6)
    ax1.grid(True, alpha=0.7)

    ax2 = ax1.twinx()
    fin_mask = np.isfinite(t_fin)
    ax2.plot(m_vals[fin_mask], t_fin[fin_mask], "^--", color="#ff7f0e", lw=0.80, markersize=3.0, label=r"$t_{II}^*(m)$ ($m \leq 14$)")
    ax2.set_ylabel(r"Optimal replacement age $t_{II}^*$", color="#b85600")
    ax2.spines["right"].set_linewidth(0.60)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper center", bbox_to_anchor=(0.47, 0.98), frameon=True, framealpha=0.95, edgecolor="#888888")
    ax1.set_title(r"Policy II Mix and Age Optimization ($n=15, k=15$, Regime 2)", pad=4)
    fig.tight_layout()
    save_figure(fig, "figS3_policy2_minlp")

    # S4: 2D Contour Surface
    g_grid = np.linspace(0.0, 2.5, 22)
    G1, G2 = np.meshgrid(g_grid, g_grid)
    Z = np.zeros_like(G1)
    for i in range(G1.shape[0]):
        for j in range(G1.shape[1]):
            ctmc = WeightedSystemCTMC(15, 5, 15, 1, 2, 0.2, 0.1, float(G1[i, j]), float(G2[i, j]))
            _, bzm = SystemOptimizer.optimize_t_policy_I(ctmc, 1.0, 5.0)
            Z[i, j] = bzm

    fig, ax = plt.subplots(figsize=(11.5 * CM_TO_IN, 7.6 * CM_TO_IN), dpi=DPI)
    cf = ax.contourf(G1, G2, Z, levels=16, cmap="viridis")
    cs = ax.contour(G1, G2, Z, levels=8, colors="white", linewidths=0.55, alpha=0.75)
    ax.clabel(cs, inline=True, fontsize=6.5, fmt="%.2f")
    cbar = fig.colorbar(cf, ax=ax)
    cbar.outline.set_linewidth(0.55)
    cbar.ax.tick_params(width=0.50, labelsize=7.0)
    cbar.set_label(r"Minimum cost rate $\eta^*$", fontsize=7.5)
    ax.set_title(r"Sensitivity Contour Surface over $(\gamma_1, \gamma_2)$ ($n=15, k=15, m=5$)", pad=4)
    ax.set_xlabel(r"Type I stress exponent $\gamma_1$")
    ax.set_ylabel(r"Type II stress exponent $\gamma_2$")
    fig.tight_layout()
    save_figure(fig, "figS4_contour_sensitivity")


if __name__ == "__main__":
    generate_fig1_mechanism_curves()
    generate_fig2_turning_point()
    generate_fig3_e4_heatmap()
    generate_supplementary_figures()
    print("All TJEECS-compliant figures generated cleanly.")
