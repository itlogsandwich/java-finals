"""
Simplified flowchart for the Java Chat System (v2).

Strips the v1 swimlane diagram down to the essential happy path:
boot, connect, auth choice, branch into register / login, merge into chat,
send-and-broadcast loop, disconnect.

Outputs flowchart.png and flowchart.svg in this folder. Run from anywhere:

    python flowchart/v2/generate_flowchart.py
"""

import os

import matplotlib.pyplot as plt
from matplotlib.patches import (
    Ellipse,
    FancyArrowPatch,
    FancyBboxPatch,
    Polygon,
)


W, H = 980, 1080

C = {
    "bg":             "#ffffff",
    "title":          "#1f2937",
    "subtitle":       "#4b5563",
    "proc_fill":      "#eaf0f6",
    "proc_stroke":    "#4b5b73",
    "decision_fill":  "#f5efd9",
    "decision_str":   "#8a7333",
    "io_fill":        "#f0e6ea",
    "io_stroke":      "#7e5965",
    "start_fill":     "#e6e8f0",
    "start_stroke":   "#4c5267",
    "end_fill":       "#f0e3e3",
    "end_stroke":     "#7e5757",
    "arrow":          "#334155",
    "text":           "#1f2937",
    "label_bg":       "#ffffff",
    "label_border":   "#cbd5e1",
}


def make_figure():
    fig, ax = plt.subplots(figsize=(W / 100, H / 100), dpi=100)
    fig.patch.set_facecolor(C["bg"])
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def round_box(ax, cx, cy, w, h, fill, stroke, lw=1.8, radius=14):
    ax.add_patch(FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=fill, edgecolor=stroke, linewidth=lw, zorder=2))


def ellipse_node(ax, cx, cy, w, h, fill, stroke, lw=1.8):
    ax.add_patch(Ellipse((cx, cy), w, h, facecolor=fill,
                         edgecolor=stroke, linewidth=lw, zorder=2))


def diamond_node(ax, cx, cy, w, h, fill, stroke, lw=1.8):
    pts = [(cx, cy - h / 2), (cx + w / 2, cy),
           (cx, cy + h / 2), (cx - w / 2, cy)]
    ax.add_patch(Polygon(pts, closed=True, facecolor=fill,
                         edgecolor=stroke, linewidth=lw, zorder=2))


def parallelogram_node(ax, cx, cy, w, h, fill, stroke, skew=22, lw=1.8):
    x = cx - w / 2
    y = cy - h / 2
    pts = [(x + skew, y), (x + w, y),
           (x + w - skew, y + h), (x, y + h)]
    ax.add_patch(Polygon(pts, closed=True, facecolor=fill,
                         edgecolor=stroke, linewidth=lw, zorder=2))


def text(ax, cx, cy, content, size=12, weight=600, color=None):
    ax.text(cx, cy, content, ha="center", va="center",
            fontsize=size, fontweight=weight,
            color=color or C["text"], zorder=3)


def mtext(ax, cx, cy, lines, size=11, weight=600, color=None, lh=16):
    n = len(lines)
    top = cy - (n - 1) * lh / 2
    for i, line in enumerate(lines):
        text(ax, cx, top + i * lh, line, size=size, weight=weight, color=color)


def edge_label(ax, x, y, label, color):
    ax.text(x, y, label, ha="center", va="center",
            fontsize=10, fontweight=700, color=color,
            bbox=dict(boxstyle="round,pad=0.3",
                      facecolor=C["label_bg"],
                      edgecolor=C["label_border"], linewidth=0.8),
            zorder=4)


def arrow(ax, p1, p2, color=None, dashed=False, label=None):
    color = color or C["arrow"]
    ls = (0, (6, 4)) if dashed else "-"
    ax.add_patch(FancyArrowPatch(
        p1, p2, arrowstyle="-|>", mutation_scale=18,
        linewidth=2, color=color, linestyle=ls, zorder=1))
    if label:
        edge_label(ax, (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2, label, color)


def poly_arrow(ax, points, color=None, dashed=False, label=None, label_at=None):
    color = color or C["arrow"]
    ls = (0, (6, 4)) if dashed else "-"
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    ax.plot(xs, ys, color=color, linewidth=2, linestyle=ls,
            solid_capstyle="round", zorder=1)
    ax.add_patch(FancyArrowPatch(
        points[-2], points[-1], arrowstyle="-|>",
        mutation_scale=18, linewidth=0, color=color, zorder=2))
    if label:
        if label_at is None:
            mid = len(points) // 2
            p1, p2 = points[mid - 1], points[mid]
            label_at = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
        edge_label(ax, *label_at, label, color)


def render(ax):
    CX = W / 2

    # Geometry
    BW = 440
    BH = 76
    BRANCH_W = 320
    BRANCH_H = 90

    y_start    = 70
    y_boot     = 170
    y_connect  = 270
    y_auth     = 390
    y_reg      = 540
    y_login    = 540
    y_chat     = 680
    y_loop     = 810
    y_end      = 950

    LX = CX - 200
    RX = CX + 200

    # 1. Start
    ellipse_node(ax, CX, y_start, 280, 64,
                 C["start_fill"], C["start_stroke"])
    text(ax, CX, y_start, "Start chat app", size=15, weight=800)

    # 2. Server boot — file I/O shape
    parallelogram_node(ax, CX, y_boot, BW, BH,
                       C["io_fill"], C["io_stroke"])
    mtext(ax, CX, y_boot,
          ["ChatServer boots",
           "load users.txt   ·   listen on localhost:5000"],
          size=12, lh=20)

    # 3. Client connects
    round_box(ax, CX, y_connect, BW, BH,
              C["proc_fill"], C["proc_stroke"])
    mtext(ax, CX, y_connect,
          ["ChatClient connects",
           "open socket  +  start reader thread"],
          size=12, lh=20)

    # 4. Auth decision diamond
    diamond_node(ax, CX, y_auth, 440, 130,
                 C["decision_fill"], C["decision_str"])
    mtext(ax, CX, y_auth,
          ["User chooses…", "register   /   login"],
          size=12, weight=700, lh=22)

    # 5. Register branch
    round_box(ax, LX, y_reg, BRANCH_W, BRANCH_H,
              C["proc_fill"], C["proc_stroke"])
    mtext(ax, LX, y_reg,
          ["Register",
           "validate + append users.txt",
           "respond  REGISTER_OK"],
          size=11, lh=20)

    # 5. Login branch
    round_box(ax, RX, y_login, BRANCH_W, BRANCH_H,
              C["proc_fill"], C["proc_stroke"])
    mtext(ax, RX, y_login,
          ["Login",
           "verify + stream chat_history.txt",
           "respond  LOGIN_OK"],
          size=11, lh=20)

    # 6. Chat screen merge
    round_box(ax, CX, y_chat, BW, BH,
              C["proc_fill"], C["proc_stroke"])
    mtext(ax, CX, y_chat,
          ["Chat screen open",
           "history shown  ·  message box ready"],
          size=12, lh=20)

    # 7. Send + broadcast loop
    round_box(ax, CX, y_loop, BW, BH + 24,
              C["proc_fill"], C["proc_stroke"])
    mtext(ax, CX, y_loop,
          ["Send a message",
           "server timestamps + appends chat_history.txt",
           "broadcasts  MSG  to all logged-in clients"],
          size=11, lh=20)

    # 8. End
    ellipse_node(ax, CX, y_end, 300, 64,
                 C["end_fill"], C["end_stroke"])
    text(ax, CX, y_end, "Disconnect & cleanup",
         size=15, weight=800)

    # Vertical arrows
    arrow(ax, (CX, y_start + 32),   (CX, y_boot - 38))
    arrow(ax, (CX, y_boot + 38),    (CX, y_connect - 38))
    arrow(ax, (CX, y_connect + 38), (CX, y_auth - 65))

    # Decision → register / login
    poly_arrow(ax,
               [(CX - 220, y_auth),
                (LX, y_auth),
                (LX, y_reg - 45)],
               label="register",
               label_at=(LX, y_auth - 18))
    poly_arrow(ax,
               [(CX + 220, y_auth),
                (RX, y_auth),
                (RX, y_login - 45)],
               label="login",
               label_at=(RX, y_auth - 18))

    # Merge to chat
    poly_arrow(ax,
               [(LX, y_reg + 45),
                (LX, y_chat - 75),
                (CX, y_chat - 75),
                (CX, y_chat - 38)])
    poly_arrow(ax,
               [(RX, y_login + 45),
                (RX, y_chat - 75),
                (CX, y_chat - 75),
                (CX, y_chat - 38)])

    # Chat → loop
    arrow(ax, (CX, y_chat + 38), (CX, y_loop - 50))

    # Loop back to chat (dashed right-side curve)
    LOOP_X = CX + BW / 2 + 60
    poly_arrow(ax,
               [(CX + BW / 2, y_loop),
                (LOOP_X, y_loop),
                (LOOP_X, y_chat),
                (CX + BW / 2, y_chat)],
               dashed=True, label="repeat",
               label_at=(LOOP_X, (y_chat + y_loop) / 2))

    # Loop → end (on disconnect)
    arrow(ax, (CX, y_loop + 50), (CX, y_end - 32),
          dashed=True, label="window close")

    # Legend
    LY = H - 45
    LX0 = 70

    ax.add_patch(FancyBboxPatch(
        (LX0 - 16, LY - 22), W - 2 * LX0 + 32, 44,
        boxstyle="round,pad=0,rounding_size=10",
        facecolor=C["bg"], edgecolor="#e2e8f0",
        linewidth=1, zorder=0))

    def swatch(x, draw, label):
        draw(x)
        ax.text(x + 26, LY, label, ha="left", va="center",
                fontsize=10, fontweight=700, color=C["text"], zorder=3)

    swatch(LX0, lambda x: ellipse_node(
        ax, x + 12, LY, 30, 18, C["start_fill"], C["start_stroke"]),
        "Start / end")
    swatch(LX0 + 150, lambda x: round_box(
        ax, x + 12, LY, 30, 20, C["proc_fill"], C["proc_stroke"]),
        "Process")
    swatch(LX0 + 280, lambda x: diamond_node(
        ax, x + 12, LY, 30, 20, C["decision_fill"], C["decision_str"]),
        "Decision")
    swatch(LX0 + 410, lambda x: parallelogram_node(
        ax, x + 12, LY, 30, 20, C["io_fill"], C["io_stroke"], skew=6),
        "File I/O")

    arr_x = LX0 + 540
    ax.add_patch(FancyArrowPatch(
        (arr_x, LY), (arr_x + 60, LY),
        arrowstyle="-|>", mutation_scale=18,
        linewidth=2, color=C["arrow"], linestyle=(0, (6, 4)), zorder=3))
    ax.text(arr_x + 70, LY, "Loop / on-close",
            ha="left", va="center",
            fontsize=10, fontweight=700, color=C["text"], zorder=3)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    fig, ax = make_figure()
    render(ax)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(os.path.join(here, "flowchart.png"),
                dpi=150, facecolor=C["bg"],
                bbox_inches=None, pad_inches=0)
    fig.savefig(os.path.join(here, "flowchart.svg"),
                facecolor=C["bg"],
                bbox_inches=None, pad_inches=0)
    fig.savefig(os.path.join(here, "flowchart.pdf"),
                facecolor=C["bg"],
                bbox_inches=None, pad_inches=0)
    plt.close(fig)
    print(f"Wrote {os.path.join(here, 'flowchart.png')}")
    print(f"Wrote {os.path.join(here, 'flowchart.svg')}")
    print(f"Wrote {os.path.join(here, 'flowchart.pdf')}")


if __name__ == "__main__":
    main()
