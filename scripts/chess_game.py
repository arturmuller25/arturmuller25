#!/usr/bin/env python3
"""
Xadrez jogável no README do perfil.

- O visitante joga de Brancas; o bot (Stockfish, com fallback) responde de Pretas.
- Para jogar, abre-se uma issue com título:  chess|move|<lance-uci>
  (os links no README já geram essa issue prontinha).
- Em eventos que não sejam de issue (workflow_dispatch / push) o script apenas
  re-renderiza o tabuleiro atual — útil para "semear" o estado inicial.

Lê o evento via variáveis de ambiente definidas no workflow:
  GITHUB_EVENT_NAME, ISSUE_TITLE, ISSUE_AUTHOR, GITHUB_REPOSITORY
"""

import os
import re
import shutil
import hashlib
import datetime
import urllib.parse

import chess
import chess.svg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR = os.path.join(ROOT, "game")
FEN_FILE = os.path.join(GAME_DIR, "board.fen")
SVG_FILE = os.path.join(GAME_DIR, "board.svg")
STATS_FILE = os.path.join(GAME_DIR, "stats.txt")
HISTORY_FILE = os.path.join(GAME_DIR, "history.md")
COMMENT_FILE = os.path.join(GAME_DIR, "_comment.md")
README = os.path.join(ROOT, "README.md")

REPO = os.environ.get("GITHUB_REPOSITORY", "arturmuller25/arturmuller25")
PROFILE_URL = f"https://github.com/{REPO.split('/')[0]}"

MARK_START = "<!-- CHESS:START -->"
MARK_END = "<!-- CHESS:END -->"

PIECE_ICON = {
    (chess.PAWN, True): "♙", (chess.KNIGHT, True): "♘", (chess.BISHOP, True): "♗",
    (chess.ROOK, True): "♖", (chess.QUEEN, True): "♕", (chess.KING, True): "♔",
    (chess.PAWN, False): "♟", (chess.KNIGHT, False): "♞", (chess.BISHOP, False): "♝",
    (chess.ROOK, False): "♜", (chess.QUEEN, False): "♛", (chess.KING, False): "♚",
}

TERM_PT = {
    "CHECKMATE": "xeque-mate", "STALEMATE": "afogamento (stalemate)",
    "INSUFFICIENT_MATERIAL": "material insuficiente", "SEVENTYFIVE_MOVES": "regra dos 75 lances",
    "FIVEFOLD_REPETITION": "quíntupla repetição", "FIFTY_MOVES": "regra dos 50 lances",
    "THREEFOLD_REPETITION": "tripla repetição", "VARIANT_WIN": "vitória", "VARIANT_LOSS": "derrota",
    "VARIANT_DRAW": "empate",
}


# --------------------------------------------------------------------------- #
# Persistência
# --------------------------------------------------------------------------- #
def load_board():
    if os.path.exists(FEN_FILE):
        fen = open(FEN_FILE, encoding="utf-8").read().strip()
        if fen:
            try:
                return chess.Board(fen)
            except ValueError:
                pass
    return chess.Board()


def save_board(board):
    os.makedirs(GAME_DIR, exist_ok=True)
    with open(FEN_FILE, "w", encoding="utf-8") as f:
        f.write(board.fen() + "\n")


def read_stats():
    s = {"games": 0, "wins": 0, "losses": 0, "draws": 0, "moves": 0}
    if os.path.exists(STATS_FILE):
        for line in open(STATS_FILE, encoding="utf-8").read().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                if k.strip() in s:
                    try:
                        s[k.strip()] = int(v.strip())
                    except ValueError:
                        pass
    return s


def write_stats(s):
    os.makedirs(GAME_DIR, exist_ok=True)
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        for k in ("games", "wins", "losses", "draws", "moves"):
            f.write(f"{k}={s[k]}\n")


def archive_game(author, result_tag, reason):
    os.makedirs(GAME_DIR, exist_ok=True)
    today = datetime.date.today().isoformat()
    line = f"- `{today}` &mdash; **@{author}** &mdash; {result_tag} _({reason})_\n"
    prev = ""
    if os.path.exists(HISTORY_FILE):
        prev = open(HISTORY_FILE, encoding="utf-8").read()
    body = re.sub(r"^# .*?\n+", "", prev, flags=re.S).strip().splitlines()
    # mantém só as 12 partidas mais recentes
    body = [line.rstrip("\n")] + body
    body = body[:12]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        f.write("# 🏅 Hall da Fama do xadrez\n\nPartidas mais recentes:\n\n")
        f.write("\n".join(body) + "\n")


# --------------------------------------------------------------------------- #
# Bot
# --------------------------------------------------------------------------- #
def bot_move(board):
    """Pretas. Tenta o Stockfish; se não houver, usa heurística gulosa."""
    sf = shutil.which("stockfish") or "/usr/games/stockfish"
    try:
        import chess.engine
        with chess.engine.SimpleEngine.popen_uci(sf) as eng:
            try:
                eng.configure({"Skill Level": 4})
            except Exception:
                pass
            res = eng.play(board, chess.engine.Limit(time=0.3))
            if res.move is not None:
                return res.move
    except Exception:
        pass
    return _greedy_move(board)


def _greedy_move(board):
    import random
    val = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
           chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
    moves = list(board.legal_moves)
    if not moves:
        return None
    random.shuffle(moves)
    best, best_val = moves[0], -1
    for m in moves:
        gain = 0
        if board.is_capture(m):
            cap = board.piece_at(m.to_square)
            if cap:
                gain = val.get(cap.piece_type, 0)
        if gain > best_val:
            best_val, best = gain, m
    return best


# --------------------------------------------------------------------------- #
# Renderização
# --------------------------------------------------------------------------- #
def render_svg(board, lastmove):
    check_sq = board.king(board.turn) if board.is_check() else None
    svg = chess.svg.board(
        board=board,
        lastmove=lastmove,
        check=check_sq,
        size=380,
        coordinates=True,
        colors={"square light": "#f0d9b5", "square dark": "#b58863"},
    )
    os.makedirs(GAME_DIR, exist_ok=True)
    with open(SVG_FILE, "w", encoding="utf-8") as f:
        f.write(svg)


def issue_link(uci):
    title = urllib.parse.quote(f"chess|move|{uci}")
    body = urllib.parse.quote(
        "Apenas clique em **Submit new issue** para jogar este lance. "
        "O bot responde em alguns segundos e o tabuleiro do perfil é atualizado automaticamente. ♟️\n\nBoa partida!"
    )
    return f"https://github.com/{REPO}/issues/new?title={title}&body={body}"


def move_links_md(board):
    if board.is_game_over():
        return "_Partida encerrada._"
    by_from = {}
    for m in board.legal_moves:
        by_from.setdefault(m.from_square, []).append(m)
    lines = []
    for from_sq in sorted(by_from, key=lambda s: (-chess.square_rank(s), chess.square_file(s))):
        piece = board.piece_at(from_sq)
        icon = PIECE_ICON[(piece.piece_type, piece.color)]
        from_name = chess.square_name(from_sq)
        targets = []
        for m in by_from[from_sq]:
            to_name = chess.square_name(m.to_square)
            label = to_name
            if m.promotion:
                label = f"{to_name}={chess.piece_symbol(m.promotion).upper()}"
            targets.append(f"[`{label}`]({issue_link(m.uci())})")
        lines.append(f"{icon} **{from_name}** &rarr; " + " ".join(targets))
    return "<br>\n".join(lines)


def build_section(board, lastmove, msg, stats):
    ver = hashlib.md5(board.fen().encode()).hexdigest()[:8]
    raw = f"https://raw.githubusercontent.com/{REPO}/main/game/board.svg?v={ver}"
    out = []
    out.append('<div align="center">\n')
    out.append(f'<img src="{raw}" width="360" alt="Tabuleiro de xadrez atual" />\n')
    out.append("</div>\n\n")
    if msg:
        out.append(f"> {msg}\n\n")
    side = "Brancas ♔" if board.turn == chess.WHITE else "Pretas ♚"
    out.append(
        f"**Vez das {side}.** Você joga de Brancas ♔ contra a IA (Stockfish). "
        "Clique em um lance abaixo &mdash; vai abrir uma _issue_ já preenchida, "
        "é só enviar (**Submit new issue**) que o bot responde em segundos. ♟️\n\n"
    )
    out.append("<details>\n<summary>♟️ <b>Ver lances possíveis</b></summary>\n\n")
    out.append(move_links_md(board) + "\n\n")
    out.append("</details>\n\n")
    out.append(
        f"`\U0001F3AE Partidas: {stats['games']}` &nbsp; "
        f"`\U0001F3C6 Suas vitórias: {stats['wins']}` &nbsp; "
        f"`\U0001F916 Vitórias da IA: {stats['losses']}` &nbsp; "
        f"`\U0001F91D Empates: {stats['draws']}` &nbsp; "
        f"`♟️ Lances: {stats['moves']}`\n"
    )
    return "".join(out)


def inject_readme(section):
    content = open(README, encoding="utf-8").read()
    block = MARK_START + "\n" + section + MARK_END
    if MARK_START in content and MARK_END in content:
        content = re.sub(
            re.escape(MARK_START) + ".*?" + re.escape(MARK_END),
            lambda _: block, content, flags=re.S,
        )
    else:
        content = content.rstrip() + "\n\n" + block + "\n"
    with open(README, "w", encoding="utf-8") as f:
        f.write(content)


def write_comment(text):
    os.makedirs(GAME_DIR, exist_ok=True)
    with open(COMMENT_FILE, "w", encoding="utf-8") as f:
        f.write(text or "")


# --------------------------------------------------------------------------- #
# Lógica de fim de jogo
# --------------------------------------------------------------------------- #
def settle_if_over(board, stats, author):
    """Se a partida acabou, atualiza placar/histórico e devolve o texto do resultado."""
    if not board.is_game_over(claim_draw=True):
        return ""
    outcome = board.outcome(claim_draw=True)
    reason = TERM_PT.get(outcome.termination.name, outcome.termination.name.lower())
    stats["games"] += 1
    if outcome.winner is None:
        stats["draws"] += 1
        tag = "\U0001F91D Empate!"
    elif outcome.winner == chess.WHITE:
        stats["wins"] += 1
        tag = f"\U0001F3C6 **@{author}** venceu a IA!"
    else:
        stats["losses"] += 1
        tag = "\U0001F916 A IA venceu desta vez!"
    archive_game(author, tag, reason)
    return f"{tag} _({reason})_ Uma nova partida já está no tabuleiro &mdash; faça o primeiro lance!"


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    board = load_board()
    stats = read_stats()
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    title = os.environ.get("ISSUE_TITLE", "").strip()
    author = (os.environ.get("ISSUE_AUTHOR", "") or "jogador").strip()
    lastmove = board.peek() if board.move_stack else None
    msg = ""
    comment = ""

    is_move = event == "issues" and title.lower().startswith("chess|move|")

    if is_move:
        uci = title.split("|", 2)[2].strip().lower()
        try:
            mv = chess.Move.from_uci(uci)
        except Exception:
            mv = None

        if mv is None or mv not in board.legal_moves:
            msg = "⚠️ Lance inválido ou desatualizado &mdash; o tabuleiro não mudou. Tente de novo abaixo!"
            comment = (
                f"❌ Não consegui jogar `{uci}`. Provavelmente alguém moveu antes de você "
                f"ou o link estava velho.\n\nVeja o tabuleiro atual no [meu perfil]({PROFILE_URL}) "
                "e escolha um novo lance. ♟️"
            )
        else:
            seq = []
            human_san = board.san(mv)
            board.push(mv)
            lastmove = mv
            stats["moves"] += 1
            seq.append(f"**@{author}** jogou **{human_san}**")
            res = settle_if_over(board, stats, author)
            if res:
                seq.append(res)
                board = chess.Board()
                lastmove = None
            else:
                bmv = bot_move(board)
                if bmv is not None:
                    bot_san = board.san(bmv)
                    board.push(bmv)
                    lastmove = bmv
                    stats["moves"] += 1
                    seq.append(f"a IA respondeu **{bot_san}**")
                    res = settle_if_over(board, stats, author)
                    if res:
                        seq.append(res)
                        board = chess.Board()
                        lastmove = None
            msg = " &middot; ".join(seq) + "."
            comment = (
                f"{msg}\n\n\U0001F449 Continue a partida no [meu perfil]({PROFILE_URL})! "
                "Obrigado por jogar. ♟️"
            )

    render_svg(board, lastmove)
    section = build_section(board, lastmove, msg, stats)
    inject_readme(section)
    save_board(board)
    write_stats(stats)
    write_comment(comment)
    print("OK:", "move" if is_move else "refresh", "| turno:", "brancas" if board.turn else "pretas")


if __name__ == "__main__":
    main()
