"""
Generate flowchart.png (and flowchart.svg) for the Java Chat System.

The figure documents the runtime behavior of ChatServer.java and ChatClient.java
side by side, with cross-lane arrows for the wire protocol over the socket.

Run from the project root:

    python flowchart/generate_flowchart.py
"""

import os

import matplotlib.pyplot as plt
from matplotlib.patches import (
    Ellipse,
    FancyArrowPatch,
    FancyBboxPatch,
    Polygon,
    Rectangle,
)
from matplotlib.path import Path
from matplotlib.patches import PathPatch


W, H = 1360, 1880

C = {
    "bg":             "#ffffff",
    "title":          "#0f172a",
    "subtitle":       "#475569",
    "client_bg":      "#eff6ff",
    "server_bg":      "#ecfdf5",
    "client_stroke":  "#2563eb",
    "server_stroke":  "#16a34a",
    "lane_hdr_c":     "#1d4ed8",
    "lane_hdr_s":     "#15803d",
    "start_fill":     "#e0e7ff",
    "start_stroke":   "#4338ca",
    "proc_fill_c":    "#dbeafe",
    "proc_fill_s":    "#dcfce7",
    "decision_fill":  "#fef9c3",
    "decision_str":   "#ca8a04",
    "io_fill":        "#fce7f3",
    "io_stroke":      "#be185d",
    "error_fill":     "#fee2e2",
    "error_stroke":   "#dc2626",
    "arrow":          "#475569",
    "net_arrow":      "#7c3aed",
    "edge_lbl_fill":  "#ffffff",
    "edge_lbl_str":   "#cbd5e1",
    "text":           "#0f172a",
    "lane_border":    "#e2e8f0",
}


def make_figure():
    fig, ax = plt.subplots(figsize=(W / 100, H / 100), dpi=100)
    fig.patch.set_facecolor(C["bg"])
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)  # flip y so coords match top-down SVG layout
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def round_box(ax, cx, cy, w, h, fill, stroke, lw=1.5, radius=10):
    patch = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=fill, edgecolor=stroke, linewidth=lw, zorder=2)
    ax.add_patch(patch)


def ellipse_shape(ax, cx, cy, w, h, fill, stroke, lw=1.5):
    patch = Ellipse((cx, cy), w, h, facecolor=fill,
                    edgecolor=stroke, linewidth=lw, zorder=2)
    ax.add_patch(patch)


def diamond_shape(ax, cx, cy, w, h, fill, stroke, lw=1.5):
    pts = [(cx, cy - h / 2), (cx + w / 2, cy),
           (cx, cy + h / 2), (cx - w / 2, cy)]
    patch = Polygon(pts, closed=True, facecolor=fill,
                    edgecolor=stroke, linewidth=lw, zorder=2)
    ax.add_patch(patch)


def parallelogram_shape(ax, cx, cy, w, h, fill, stroke, skew=22, lw=1.5):
    x = cx - w / 2
    y = cy - h / 2
    pts = [(x + skew, y), (x + w, y),
           (x + w - skew, y + h), (x, y + h)]
    patch = Polygon(pts, closed=True, facecolor=fill,
                    edgecolor=stroke, linewidth=lw, zorder=2)
    ax.add_patch(patch)


def text(ax, cx, cy, content, size=12, weight=600, color=None):
    color = color or C["text"]
    ax.text(cx, cy, content, ha="center", va="center",
            fontsize=size, fontweight=weight, color=color, zorder=3)


def multiline_text(ax, cx, cy, lines, size=12, weight=600,
                   color=None, line_height=15):
    n = len(lines)
    top = cy - (n - 1) * line_height / 2
    for i, line in enumerate(lines):
        text(ax, cx, top + i * line_height, line,
             size=size, weight=weight, color=color)


def edge_label(ax, x, y, label, color):
    ax.text(x, y, label, ha="center", va="center",
            fontsize=9, fontweight=700, color=color,
            bbox=dict(boxstyle="round,pad=0.25",
                      facecolor=C["edge_lbl_fill"],
                      edgecolor=C["edge_lbl_str"],
                      linewidth=0.8),
            zorder=4)


def straight_arrow(ax, x1, y1, x2, y2, color=None, dashed=False, label=None):
    color = color or C["arrow"]
    ls = (0, (5, 4)) if dashed else "-"
    arrow = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>", mutation_scale=14,
        linewidth=1.8, color=color, linestyle=ls,
        shrinkA=0, shrinkB=0, zorder=1)
    ax.add_patch(arrow)
    if label:
        edge_label(ax, (x1 + x2) / 2, (y1 + y2) / 2, label, color)


def poly_arrow(ax, points, color=None, dashed=False, label=None,
               label_at=None):
    color = color or C["arrow"]
    ls = (0, (5, 4)) if dashed else "solid"
    # draw connecting segments (no arrowhead)
    if len(points) > 2:
        xs = [p[0] for p in points[:-1]]
        ys = [p[1] for p in points[:-1]]
        # extend to second-last point only; final segment uses arrow
        ax.plot(xs + [points[-1][0]],
                ys + [points[-1][1]],
                color=color, linewidth=1.8, linestyle=ls,
                solid_capstyle="round", zorder=1)
        # arrowhead on the last segment, drawn over the line end
        arrow = FancyArrowPatch(
            points[-2], points[-1],
            arrowstyle="-|>", mutation_scale=14,
            linewidth=0, color=color,
            shrinkA=0, shrinkB=0, zorder=2)
        ax.add_patch(arrow)
    else:
        straight_arrow(ax, *points[0], *points[1],
                       color=color, dashed=dashed)
    if label:
        if label_at is None:
            mid = len(points) // 2
            p1, p2 = points[mid - 1], points[mid]
            label_at = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
        edge_label(ax, *label_at, label, color)


# Lane geometry
LANE_TOP = 100
LANE_BOTTOM = H - 110
LANE_W = 640
LANE_GAP = 50

LANE_C_X = 30
LANE_S_X = W - 30 - LANE_W
CX_C = LANE_C_X + LANE_W / 2
CX_S = LANE_S_X + LANE_W / 2

BW = 360
BH = 62


def node(ax, cx, cy, kind, body, w=BW, h=BH, lane="c"):
    fill_proc = C["proc_fill_c"] if lane == "c" else C["proc_fill_s"]
    stroke_proc = C["client_stroke"] if lane == "c" else C["server_stroke"]
    if kind == "start":
        ellipse_shape(ax, cx, cy, w - 60, h, C["start_fill"], C["start_stroke"])
        multiline_text(ax, cx, cy, body, size=13, weight=800)
    elif kind == "process":
        round_box(ax, cx, cy, w, h, fill_proc, stroke_proc)
        multiline_text(ax, cx, cy, body, size=10, weight=600)
    elif kind == "decision":
        diamond_shape(ax, cx, cy, w + 60, h + 50, C["decision_fill"],
                      C["decision_str"])
        multiline_text(ax, cx, cy, body, size=10, weight=700)
    elif kind == "io":
        parallelogram_shape(ax, cx, cy, w, h, C["io_fill"], C["io_stroke"])
        multiline_text(ax, cx, cy, body, size=10, weight=600)
    elif kind == "error":
        round_box(ax, cx, cy, w, h, C["error_fill"], C["error_stroke"])
        multiline_text(ax, cx, cy, body, size=10, weight=600)


def render(ax):
    # Title
    ax.text(W / 2, 38, "Java Chat System — Runtime Flow",
            ha="center", va="center",
            fontsize=22, fontweight=800, color=C["title"])
    ax.text(W / 2, 70,
            "Swing GUI client and multi-threaded socket server on "
            "localhost:5000",
            ha="center", va="center",
            fontsize=12, fontweight=500, color=C["subtitle"])

    # Lane backgrounds
    lane_c = FancyBboxPatch(
        (LANE_C_X, LANE_TOP), LANE_W, LANE_BOTTOM - LANE_TOP,
        boxstyle="round,pad=0,rounding_size=16",
        facecolor=C["client_bg"], edgecolor=C["client_stroke"],
        linewidth=1.5, zorder=0)
    lane_s = FancyBboxPatch(
        (LANE_S_X, LANE_TOP), LANE_W, LANE_BOTTOM - LANE_TOP,
        boxstyle="round,pad=0,rounding_size=16",
        facecolor=C["server_bg"], edgecolor=C["server_stroke"],
        linewidth=1.5, zorder=0)
    ax.add_patch(lane_c)
    ax.add_patch(lane_s)

    ax.text(CX_C, LANE_TOP + 32, "CLIENT  ·  ChatClient.java",
            ha="center", va="center",
            fontsize=16, fontweight=800, color=C["lane_hdr_c"], zorder=1)
    ax.text(CX_S, LANE_TOP + 32, "SERVER  ·  ChatServer.java",
            ha="center", va="center",
            fontsize=16, fontweight=800, color=C["lane_hdr_s"], zorder=1)

    # =========================================================
    # CLIENT LANE
    # =========================================================
    y_c_start = 210
    y_c_gui = 300
    y_c_connect = 385
    y_c_auth = 475
    y_c_click = 585
    y_c_send = 710
    y_c_reader = 830
    y_c_handle = 940
    y_c_login = 1070
    y_c_msg = 1070
    y_c_register = 1170
    y_c_error = 1170
    y_c_chat = 1300
    y_c_input = 1395
    y_c_close = 1525

    CX_C_L = CX_C - 130
    CX_C_R = CX_C + 130

    node(ax, CX_C, y_c_start, "start", ["Start ChatClient"])
    node(ax, CX_C, y_c_gui, "process", [
        "configureLookAndFeel  +  buildGui",
        "CardLayout: auth panel + chat panel"])
    node(ax, CX_C, y_c_connect, "process", [
        "connect():  new Socket(\"localhost\", 5000)",
        "open DataInput/Output, start daemon reader thread"])
    node(ax, CX_C, y_c_auth, "process", [
        "Show auth panel",
        "Status: Connected to localhost:5000"])
    node(ax, CX_C, y_c_click, "decision", [
        "User clicks button", "Login  /  Register"])
    node(ax, CX_C, y_c_send, "process", [
        "sendAuthCommand(cmd):  validate fields",
        "out.writeUTF(\"/login | /register  <user>  <pass>\")"])
    node(ax, CX_C, y_c_reader, "process", [
        "Reader thread loop:  in.readUTF()",
        "→ handleServerMessage(message)"])
    node(ax, CX_C, y_c_handle, "decision", ["Message prefix?"])

    node(ax, CX_C_L, y_c_login, "process",
         ["LOGIN_OK", "switch CardLayout to chat panel"], w=260)
    node(ax, CX_C_R, y_c_msg, "process",
         ["MSG  <text>", "appendChat → chatArea.append"], w=260)
    node(ax, CX_C_L, y_c_register, "process",
         ["REGISTER_OK", "JOptionPane info dialog"], w=260)
    node(ax, CX_C_R, y_c_error, "process",
         ["ERROR  <text>", "JOptionPane error dialog"], w=260)

    node(ax, CX_C, y_c_chat, "process", [
        "Chat screen ready",
        "messageField + Send button + chat area"])
    node(ax, CX_C, y_c_input, "process", [
        "User types  →  Enter / Send",
        "sendMessage():  out.writeUTF(text)"])
    node(ax, CX_C, y_c_close, "error", [
        "WindowClosing → closeConnection()",
        "socket.close()"])

    # Client control-flow edges
    straight_arrow(ax, CX_C, y_c_start + 31, CX_C, y_c_gui - 31)
    straight_arrow(ax, CX_C, y_c_gui + 31, CX_C, y_c_connect - 31)
    straight_arrow(ax, CX_C, y_c_connect + 31, CX_C, y_c_auth - 31)
    straight_arrow(ax, CX_C, y_c_auth + 31, CX_C, y_c_click - 56)
    straight_arrow(ax, CX_C, y_c_click + 56, CX_C, y_c_send - 31)

    straight_arrow(ax, CX_C, y_c_reader + 31, CX_C, y_c_handle - 56)

    poly_arrow(ax,
               [(CX_C - 230, y_c_handle),
                (CX_C_L, y_c_handle),
                (CX_C_L, y_c_login - 31)],
               label="LOGIN_OK",
               label_at=(CX_C_L, y_c_handle - 14))
    poly_arrow(ax,
               [(CX_C + 230, y_c_handle),
                (CX_C_R, y_c_handle),
                (CX_C_R, y_c_msg - 31)],
               label="MSG ...",
               label_at=(CX_C_R, y_c_handle - 14))
    poly_arrow(ax,
               [(CX_C_L, y_c_login + 31),
                (CX_C_L, y_c_register - 31)],
               label="REGISTER_OK",
               label_at=(CX_C_L - 90,
                         (y_c_login + 31 + y_c_register - 31) / 2))
    poly_arrow(ax,
               [(CX_C_R, y_c_msg + 31),
                (CX_C_R, y_c_error - 31)],
               label="ERROR ...",
               label_at=(CX_C_R + 80,
                         (y_c_msg + 31 + y_c_error - 31) / 2))

    poly_arrow(ax,
               [(CX_C_L, y_c_login + 31),
                (CX_C_L, y_c_chat - 80),
                (CX_C, y_c_chat - 80),
                (CX_C, y_c_chat - 31)])
    straight_arrow(ax, CX_C, y_c_chat + 31, CX_C, y_c_input - 31)
    straight_arrow(ax, CX_C, y_c_input + 31, CX_C, y_c_close - 31,
                   dashed=True, label="on window close")

    # =========================================================
    # SERVER LANE
    # =========================================================
    y_s_start = 210
    y_s_load = 300
    y_s_bind = 385
    y_s_accept = 480
    y_s_spawn = 575
    y_s_read = 690
    y_s_decision = 820
    y_s_branch = 965
    y_s_persist = 1070
    y_s_response = 1180
    y_s_disconnect = 1320
    y_s_files = 1470

    SX_L = CX_S - 200
    SX_M = CX_S
    SX_R = CX_S + 200

    node(ax, CX_S, y_s_start, "start", ["Start ChatServer"], lane="s")
    node(ax, CX_S, y_s_load, "io",
         ["loadUsers()  ←  users.txt",
          "into ConcurrentHashMap<user,pass>"], lane="s")
    node(ax, CX_S, y_s_bind, "process",
         ["ServerSocket(5000, 50, loopback)",
          "log: \"Chat server running on localhost port 5000\""],
         lane="s")
    node(ax, CX_S, y_s_accept, "process",
         ["Accept loop:  socket = serverSocket.accept()"], lane="s")
    node(ax, CX_S, y_s_spawn, "process",
         ["Spawn new Thread(ClientHandler)",
          "clients.add(handler)"], lane="s")
    node(ax, CX_S, y_s_read, "process",
         ["ClientHandler.run():  while(true) { in.readUTF() }"], lane="s")
    node(ax, CX_S, y_s_decision, "decision",
         ["input starts with…", "/register  ·  /login  ·  else"], lane="s")

    node(ax, SX_L, y_s_branch, "process",
         ["handleRegister(input)",
          "validate, dedupe in users map"], lane="s", w=240)
    node(ax, SX_M, y_s_branch, "process",
         ["handleLogin(input)",
          "verify creds + not already in",
          "loggedInUsers"], lane="s", w=240)
    node(ax, SX_R, y_s_branch, "process",
         ["handleMessage(input)",
          "(requires username != null)"], lane="s", w=240)

    node(ax, SX_L, y_s_persist, "io",
         ["users.put + append line",
          "users.txt"], lane="s", w=240)
    node(ax, SX_M, y_s_persist, "process",
         ["loggedInUsers.add(user)",
          "set this.username"], lane="s", w=240)
    node(ax, SX_R, y_s_persist, "io",
         ["format \"[HH:mm:ss] user: msg\"",
          "append chat_history.txt"], lane="s", w=240)

    node(ax, SX_L, y_s_response, "process",
         ["out.writeUTF(REGISTER_OK)",
          "or  ERROR <reason>"], lane="s", w=240)
    node(ax, SX_M, y_s_response, "process",
         ["out.writeUTF(LOGIN_OK)",
          "sendHistory:",
          "HISTORY_START → MSG lines → HISTORY_END"],
         lane="s", w=240, h=80)
    node(ax, SX_R, y_s_response, "process",
         ["broadcast(): for each client",
          "if logged in → MSG <text>"], lane="s", w=240)

    node(ax, CX_S, y_s_disconnect, "error",
         ["EOFException / IOException  →  disconnect()",
          "clients.remove + loggedInUsers.remove + socket.close()"],
         lane="s", w=540)
    node(ax, CX_S, y_s_files, "io",
         ["Persistence:   users.txt   ·   chat_history.txt"],
         lane="s", w=540)

    # Server control-flow edges
    straight_arrow(ax, CX_S, y_s_start + 31, CX_S, y_s_load - 31)
    straight_arrow(ax, CX_S, y_s_load + 31, CX_S, y_s_bind - 31)
    straight_arrow(ax, CX_S, y_s_bind + 31, CX_S, y_s_accept - 31)
    straight_arrow(ax, CX_S, y_s_accept + 31, CX_S, y_s_spawn - 31)
    straight_arrow(ax, CX_S, y_s_spawn + 31, CX_S, y_s_read - 31)
    straight_arrow(ax, CX_S, y_s_read + 31, CX_S, y_s_decision - 56)

    poly_arrow(ax,
               [(CX_S - 230, y_s_decision),
                (SX_L, y_s_decision),
                (SX_L, y_s_branch - 31)],
               label="/register",
               label_at=(SX_L, y_s_decision - 14))
    straight_arrow(ax, CX_S, y_s_decision + 56, SX_M, y_s_branch - 31,
                   label="/login")
    poly_arrow(ax,
               [(CX_S + 230, y_s_decision),
                (SX_R, y_s_decision),
                (SX_R, y_s_branch - 31)],
               label="else  (text)",
               label_at=(SX_R, y_s_decision - 14))

    straight_arrow(ax, SX_L, y_s_branch + 31, SX_L, y_s_persist - 31)
    straight_arrow(ax, SX_L, y_s_persist + 31, SX_L, y_s_response - 31)
    straight_arrow(ax, SX_M, y_s_branch + 31, SX_M, y_s_persist - 31)
    straight_arrow(ax, SX_M, y_s_persist + 31, SX_M, y_s_response - 41)
    straight_arrow(ax, SX_R, y_s_branch + 31, SX_R, y_s_persist - 31)
    straight_arrow(ax, SX_R, y_s_persist + 31, SX_R, y_s_response - 31)

    poly_arrow(ax,
               [(SX_L, y_s_response + 31),
                (SX_L, y_s_disconnect - 80),
                (CX_S, y_s_disconnect - 80),
                (CX_S, y_s_disconnect - 31)])
    poly_arrow(ax,
               [(SX_M, y_s_response + 41),
                (SX_M, y_s_disconnect - 60),
                (CX_S, y_s_disconnect - 60),
                (CX_S, y_s_disconnect - 31)])
    poly_arrow(ax,
               [(SX_R, y_s_response + 31),
                (SX_R, y_s_disconnect - 80),
                (CX_S, y_s_disconnect - 80),
                (CX_S, y_s_disconnect - 31)])
    straight_arrow(ax, CX_S, y_s_disconnect + 31, CX_S, y_s_files - 31,
                   dashed=True, label="reads / writes")

    # Read-loop self-loop (next message)
    LOOP_X = CX_S + LANE_W / 2 - 35
    poly_arrow(ax,
               [(CX_S + BW / 2, y_s_read),
                (LOOP_X, y_s_read),
                (LOOP_X, y_s_read - 95),
                (CX_S, y_s_read - 95),
                (CX_S, y_s_read - 31)],
               dashed=True, label="next message",
               label_at=(LOOP_X - 110, y_s_read - 95))

    # =========================================================
    # CROSS-LANE NETWORK ARROWS
    # =========================================================
    net = C["net_arrow"]

    # C: sendAuthCommand → S: read loop / decision
    poly_arrow(ax,
               [(CX_C + BW / 2, y_c_send),
                (LANE_C_X + LANE_W + 12, y_c_send),
                (LANE_C_X + LANE_W + 12, y_s_read - 95),
                (CX_S - BW / 2 - 12, y_s_read - 95),
                (CX_S - BW / 2 - 12, y_s_read),
                (CX_S - BW / 2, y_s_read)],
               color=net, dashed=True,
               label="/register | /login   over socket",
               label_at=((CX_C + CX_S) / 2, y_s_read - 95 - 12))

    # S: REGISTER_OK / ERROR → C: reader
    poly_arrow(ax,
               [(SX_L - 120, y_s_response),
                (CX_C + BW / 2 + 12, y_s_response),
                (CX_C + BW / 2 + 12, y_c_reader),
                (CX_C + BW / 2, y_c_reader)],
               color=net, dashed=True,
               label="REGISTER_OK | ERROR",
               label_at=((SX_L + CX_C) / 2 + 40, y_s_response - 14))

    # S: LOGIN_OK + history → C: reader
    poly_arrow(ax,
               [(SX_M - 120, y_s_response - 20),
                (CX_C + BW / 2 + 32, y_s_response - 20),
                (CX_C + BW / 2 + 32, y_c_reader + 10),
                (CX_C + BW / 2, y_c_reader + 10)],
               color=net, dashed=True,
               label="LOGIN_OK  +  HISTORY_START / MSG / HISTORY_END",
               label_at=((SX_M + CX_C) / 2 + 10, y_s_response - 36))

    # C: input → S: chat-text branch
    poly_arrow(ax,
               [(CX_C + BW / 2, y_c_input),
                (LANE_C_X + LANE_W + 32, y_c_input),
                (LANE_C_X + LANE_W + 32, y_s_branch - 100),
                (SX_R, y_s_branch - 100),
                (SX_R, y_s_branch - 31)],
               color=net, dashed=True,
               label="chat text   over socket",
               label_at=((CX_C + SX_R) / 2 + 40, y_s_branch - 114))

    # S: broadcast → C: reader (MSG)
    poly_arrow(ax,
               [(SX_R - 120, y_s_response),
                (CX_C + BW / 2 + 55, y_s_response),
                (CX_C + BW / 2 + 55, y_c_reader + 30),
                (CX_C + BW / 2, y_c_reader + 30)],
               color=net, dashed=True,
               label="MSG  [HH:mm:ss] user: text",
               label_at=((SX_R + CX_C) / 2, y_s_response - 14))

    # =========================================================
    # LEGEND
    # =========================================================
    LX = 60
    LY = H - 70

    # Legend background
    ax.add_patch(FancyBboxPatch(
        (LX - 16, LY - 22), W - 2 * LX + 32, 50,
        boxstyle="round,pad=0,rounding_size=10",
        facecolor=C["bg"], edgecolor=C["lane_border"],
        linewidth=1, zorder=0))

    def swatch_text(x, swatch_draw, label):
        swatch_draw(x)
        ax.text(x + 24, LY, label, ha="left", va="center",
                fontsize=10, fontweight=700, color=C["text"], zorder=3)

    swatch_text(LX, lambda x: ellipse_shape(
        ax, x + 10, LY, 28, 16, C["start_fill"], C["start_stroke"]),
        "Start")
    swatch_text(LX + 110, lambda x: round_box(
        ax, x + 10, LY, 28, 20, C["proc_fill_c"], C["client_stroke"]),
        "Client process")
    swatch_text(LX + 270, lambda x: round_box(
        ax, x + 10, LY, 28, 20, C["proc_fill_s"], C["server_stroke"]),
        "Server process")
    swatch_text(LX + 440, lambda x: diamond_shape(
        ax, x + 10, LY, 28, 20, C["decision_fill"], C["decision_str"]),
        "Decision")
    swatch_text(LX + 570, lambda x: parallelogram_shape(
        ax, x + 10, LY, 28, 20, C["io_fill"], C["io_stroke"], skew=6),
        "File I/O")
    swatch_text(LX + 690, lambda x: round_box(
        ax, x + 10, LY, 28, 20, C["error_fill"], C["error_stroke"]),
        "Disconnect / error")

    # Network message arrow
    nx = LX + 900
    arrow = FancyArrowPatch(
        (nx, LY), (nx + 60, LY),
        arrowstyle="-|>", mutation_scale=14, linewidth=1.8,
        color=C["net_arrow"], linestyle=(0, (5, 4)), zorder=3)
    ax.add_patch(arrow)
    ax.text(nx + 70, LY, "Socket network message",
            ha="left", va="center", fontsize=10, fontweight=700,
            color=C["text"], zorder=3)

    arrow2 = FancyArrowPatch(
        (nx, LY + 22), (nx + 60, LY + 22),
        arrowstyle="-|>", mutation_scale=14, linewidth=1.8,
        color=C["arrow"], zorder=3)
    ax.add_patch(arrow2)
    ax.text(nx + 70, LY + 22, "Control flow within a process",
            ha="left", va="center", fontsize=10, fontweight=700,
            color=C["text"], zorder=3)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    fig, ax = make_figure()
    render(ax)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    png_path = os.path.join(here, "flowchart.png")
    svg_path = os.path.join(here, "flowchart.svg")
    fig.savefig(png_path, dpi=150, facecolor=C["bg"], bbox_inches=None,
                pad_inches=0)
    fig.savefig(svg_path, facecolor=C["bg"], bbox_inches=None, pad_inches=0)
    plt.close(fig)
    print(f"Wrote {png_path}")
    print(f"Wrote {svg_path}")


if __name__ == "__main__":
    main()
