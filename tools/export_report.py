#!/usr/bin/env python3
"""
Export the GitHub-wiki-style report under LA_Noire/wiki into:
- LA_Noire/report_export/LA_Noire_Report.md (combined markdown)
- LA_Noire/report_export/LA_Noire_Report.tex (standalone LaTeX)

PDF build is done separately via MiKTeX (xelatex/pdflatex).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


WIKI_EXPORT_ORDER = [
    "Project-Overview.md",
    "Evaluation-Criteria.md",
    "Team-Responsibilities.md",
    "Project-Management.md",
    "Development-Conventions.md",
    "Development-Flow.md",
    "Key-Entities.md",
    "NPM-Packages.md",
    "AI-Usage.md",
    "Requirement-Analysis.md",
]


def _escape_latex_text(s: str) -> str:
    # Escape LaTeX special chars for normal text (not code blocks).
    s = s.replace("\\", r"\textbackslash{}")
    s = s.replace("&", r"\&")
    s = s.replace("%", r"\%")
    s = s.replace("$", r"\$")
    s = s.replace("#", r"\#")
    s = s.replace("_", r"\_")
    s = s.replace("{", r"\{")
    s = s.replace("}", r"\}")
    s = s.replace("~", r"\textasciitilde{}")
    s = s.replace("^", r"\textasciicircum{}")
    return s


@dataclass
class _Token:
    key: str
    latex: str


def _inline_md_to_latex(s: str) -> str:
    """
    Convert a minimal subset of inline Markdown to LaTeX:
    - `code`
    - [text](url)
    - **bold**
    - *italic*
    Anything else is treated as plain text and escaped.
    """

    tokens: list[_Token] = []

    def _stash(latex: str) -> str:
        key = f"@@T{len(tokens)}@@"
        tokens.append(_Token(key=key, latex=latex))
        return key

    # Code spans first.
    def repl_code(m: re.Match[str]) -> str:
        code = m.group(1)
        # detokenize avoids escaping file paths, underscores, etc.
        return _stash(r"\texttt{\detokenize{" + code + "}}")

    s = re.sub(r"`([^`]+)`", repl_code, s)

    # Links.
    def repl_link(m: re.Match[str]) -> str:
        label = _escape_latex_text(m.group(1))
        url = m.group(2).strip()
        return _stash(r"\href{\detokenize{" + url + "}}{" + label + "}")

    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl_link, s)

    # Bold.
    def repl_bold(m: re.Match[str]) -> str:
        txt = _escape_latex_text(m.group(1))
        return _stash(r"\textbf{" + txt + "}")

    s = re.sub(r"\*\*([^*]+)\*\*", repl_bold, s)

    # Italic (simple form; avoids matching bold since that's already stashed).
    def repl_italic(m: re.Match[str]) -> str:
        txt = _escape_latex_text(m.group(1))
        return _stash(r"\textit{" + txt + "}")

    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", repl_italic, s)

    # Escape remainder.
    s = _escape_latex_text(s)

    # Un-stash tokens.
    for tok in tokens:
        s = s.replace(_escape_latex_text(tok.key), tok.latex)  # key got escaped above
        s = s.replace(tok.key, tok.latex)

    return s


def markdown_to_latex(md: str) -> str:
    out: list[str] = []
    in_code = False
    in_list = False

    lines = md.splitlines()
    for raw in lines:
        line = raw.rstrip("\n")

        # Code fences.
        if line.strip().startswith("```"):
            if not in_code:
                if in_list:
                    out.append(r"\end{itemize}")
                    in_list = False
                out.append(r"\begin{lstlisting}")
                in_code = True
            else:
                out.append(r"\end{lstlisting}")
                in_code = False
            continue

        if in_code:
            out.append(line)
            continue

        # Raw LaTeX passthrough (rare, but useful).
        if line.startswith("\\"):
            if in_list:
                out.append(r"\end{itemize}")
                in_list = False
            out.append(line)
            continue

        # Headings.
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            if in_list:
                out.append(r"\end{itemize}")
                in_list = False
            level = len(m.group(1))
            title = _inline_md_to_latex(m.group(2).strip())
            if level == 1:
                out.append(r"\chapter{" + title + "}")
            elif level == 2:
                out.append(r"\section{" + title + "}")
            elif level == 3:
                out.append(r"\subsection{" + title + "}")
            else:
                out.append(r"\subsubsection{" + title + "}")
            continue

        # Bullet list.
        m = re.match(r"^- (.*)$", line)
        if m:
            if not in_list:
                out.append(r"\begin{itemize}")
                in_list = True
            out.append(r"\item " + _inline_md_to_latex(m.group(1).strip()))
            continue

        # Blank line closes a list.
        if not line.strip():
            if in_list:
                out.append(r"\end{itemize}")
                in_list = False
            out.append("")
            continue

        # Normal paragraph.
        if in_list:
            out.append(r"\end{itemize}")
            in_list = False
        out.append(_inline_md_to_latex(line))

    if in_list:
        out.append(r"\end{itemize}")
    if in_code:
        out.append(r"\end{lstlisting}")

    return "\n".join(out) + "\n"


def build_standalone_tex(body: str) -> str:
    return (
        r"\documentclass[11pt]{report}" "\n"
        r"\usepackage[margin=1in]{geometry}" "\n"
        r"\usepackage[T1]{fontenc}" "\n"
        r"\usepackage{hyperref}" "\n"
        r"\usepackage{xcolor}" "\n"
        r"\usepackage{listings}" "\n"
        r"\lstset{basicstyle=\ttfamily\small,breaklines=true,columns=fullflexible}" "\n"
        r"\setlength{\parindent}{0pt}" "\n"
        r"\setlength{\parskip}{0.6em}" "\n"
        "\n"
        r"\title{LA Noire Police Department Web System\\Project Report}" "\n"
        r"\author{Kiarash Joolaei (400100949)\\Mohammad Mahdi Farhadi (99105634)}" "\n"
        r"\date{\today}" "\n"
        "\n"
        r"\begin{document}" "\n"
        r"\maketitle" "\n"
        r"\tableofcontents" "\n"
        r"\clearpage" "\n"
        "\n"
        + body
        + "\n"
        r"\end{document}" "\n"
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    wiki_dir = repo_root / "wiki"
    out_dir = repo_root / "report_export"
    out_dir.mkdir(parents=True, exist_ok=True)

    combined_md_parts: list[str] = []
    for name in WIKI_EXPORT_ORDER:
        p = wiki_dir / name
        if not p.exists():
            raise SystemExit(f"Missing wiki file: {p}")
        combined_md_parts.append(p.read_text(encoding="utf-8").strip() + "\n")

    combined_md = "\n".join(combined_md_parts).strip() + "\n"
    (out_dir / "LA_Noire_Report.md").write_text(combined_md, encoding="utf-8", newline="\n")

    latex_body = markdown_to_latex(combined_md)
    standalone = build_standalone_tex(latex_body)
    (out_dir / "LA_Noire_Report.tex").write_text(standalone, encoding="utf-8", newline="\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

