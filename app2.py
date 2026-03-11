import streamlit as st
import re
import time
import io
import datetime
import html
from PIL import Image
import pytesseract
from pypdf import PdfReader
from docx import Document as DocxDocument
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import pandas as pd
from openai import OpenAI

# ==============================
# PAGE CONFIG & STYLES
# ==============================
st.set_page_config(
    page_title="Reasoning Forge",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

:root {
    --bg:          #f7f5f0;
    --bg2:         #ffffff;
    --bg3:         #edeae3;
    --gold:        #a0732a;
    --gold-light:  #c9a84c;
    --border:      rgba(160,115,42,0.25);
    --text:        #1a1612;
    --muted:       #6b6560;
    --serif:       'Cormorant Garamond', Georgia, serif;
    --sans:        'DM Sans', sans-serif;
    --mono:        'DM Mono', monospace;
}

html, body, [data-testid="stAppViewContainer"], .stApp {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
}

[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* ── Chat bubbles ── */
.bubble-user {
    background: var(--gold);
    color: #ffffff;
    border-radius: 16px 16px 4px 16px;
    padding: 0.85rem 1.2rem;
    margin: 0.5rem 0 0.25rem 15%;
    line-height: 1.65;
    font-size: 0.95rem;
    word-wrap: break-word;
}
.bubble-ai {
    background: var(--bg2);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 16px 16px 16px 4px;
    padding: 0.85rem 1.2rem;
    margin: 0.5rem 15% 0.1rem 0;
    line-height: 1.75;
    font-size: 0.95rem;
    word-wrap: break-word;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    position: relative;
}
.bubble-ai::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    border-radius: 16px 16px 0 0;
    background: linear-gradient(90deg, var(--gold), var(--gold-light), transparent);
}
.bubble-ai p { margin: 0 0 0.6em 0; }
.bubble-ai p:last-child { margin-bottom: 0; }

.bubble-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: var(--muted);
    margin-bottom: 0.2rem;
}
.label-user { text-align: right; margin-right: 0.2rem; }
.label-ai   { text-align: left;  margin-left:  0.2rem; }

/* ── Timing badge ── */
.timing-badge {
    font-size: 0.7rem;
    color: var(--muted);
    margin: 0 0 0.75rem 0.2rem;
    display: flex;
    align-items: center;
    gap: 0.3rem;
}
.timing-bar {
    display: inline-block;
    height: 3px;
    border-radius: 2px;
    background: linear-gradient(90deg, var(--gold), var(--gold-light));
    vertical-align: middle;
    margin-right: 0.3rem;
}

/* ── Input area ── */
.stTextArea textarea {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 6px !important;
}

/* ── Buttons ── */
.stButton > button {
    background: var(--gold) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    width: 100%;
    transition: background 0.2s ease !important;
}
.stButton > button:hover { background: var(--gold-light) !important; }

.stDownloadButton > button {
    background: transparent !important;
    color: var(--gold) !important;
    border: 1.5px solid var(--gold) !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    width: 100%;
    transition: all 0.2s ease !important;
}
.stDownloadButton > button:hover {
    background: var(--gold) !important;
    color: #ffffff !important;
}

.file-badge {
    display: block;
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 0.25rem 0.75rem;
    font-size: 0.8rem;
    color: var(--gold);
    margin-bottom: 0.4rem;
    font-weight: 500;
}
.turn-divider {
    border: none;
    border-top: 1px dashed var(--border);
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# SESSION STATE INIT
# ==============================
# message shape: {"role": "user"|"assistant", "content": str, "elapsed": float|None, "ts": str}
if "messages"     not in st.session_state: st.session_state.messages     = []
if "file_context" not in st.session_state: st.session_state.file_context = ""
if "file_names"   not in st.session_state: st.session_state.file_names   = []

# ==============================
# HELPERS
# ==============================
def extract_text(file) -> tuple[str, str]:
    ext = file.name.split(".")[-1].lower()
    try:
        if ext == "pdf":
            reader = PdfReader(file)
            return "\n".join(p.extract_text() or "" for p in reader.pages), "PDF"
        elif ext == "docx":
            doc = DocxDocument(file)
            return "\n".join(p.text for p in doc.paragraphs), "DOCX"
        elif ext in ["xlsx", "xls"]:
            xls = pd.ExcelFile(file)
            sheets = []
            for name in xls.sheet_names:
                df = xls.parse(name).dropna(how="all").fillna("")
                sheets.append(f"[Sheet: {name}]\n{df.to_markdown(index=False)}")
            return "\n\n".join(sheets), "Excel"
        elif ext == "csv":
            return pd.read_csv(file).fillna("").to_markdown(index=False), "CSV"
        elif ext in ["png", "jpg", "jpeg"]:
            return pytesseract.image_to_string(Image.open(file)), "Image (OCR)"
        else:
            return file.read().decode("utf-8"), "Text"
    except Exception as e:
        return f"Error: {e}", "Unknown"


def format_for_display(text: str) -> str:
    escaped = html.escape(text)
    paragraphs = re.split(r'\n{2,}', escaped.strip())
    return "".join(
        f"<p>{para.replace(chr(10), '<br>')}</p>"
        for para in paragraphs
    )


def elapsed_label(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    return f"{int(seconds // 60)}m {seconds % 60:.0f}s"


def bar_width(seconds: float) -> int:
    """Scale bar width (px) capped at 120px for display."""
    return min(int(seconds * 6), 120)


def build_messages_for_api(file_context: str, history: list) -> list:
    api_messages = []
    for i, msg in enumerate(history):
        content = msg["content"]
        if i == 0 and msg["role"] == "user" and file_context:
            content = f"CONTEXT FROM FILES:\n{file_context}\n\n---\n\nUSER: {content}"
        api_messages.append({"role": msg["role"], "content": content})
    return api_messages


def get_llm_response(history: list, file_context: str, provider: str) -> tuple[str, float]:
    """Returns (response_text, elapsed_seconds)."""
    try:
        client = OpenAI(
            api_key=st.secrets["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1"
        )
        if "Metal-llama" in provider:
            model_id = "meta-llama/llama-3.1-8b-instruct:free"
        elif "nemotron-3 by Nvidia" in provider:
            model_id = "nvidia/nemotron-3-super-120b-a12b:free"
        elif "Stepfun" in provider:
            model_id = "stepfun/step-3.5-flash:free"
        else:
            model_id = "meta-llama/llama-3.1-8b-instruct:free"

        api_messages = build_messages_for_api(file_context, history)

        t0 = time.time()
        response = client.chat.completions.create(
            model=model_id,
            messages=api_messages,
            extra_headers={
                "HTTP-Referer": "http://localhost:8501",
                "X-Title": "Reasoning Forge"
            }
        )
        elapsed = time.time() - t0
        return response.choices[0].message.content, elapsed
    except Exception as e:
        return f"Error: {str(e)}", 0.0


# ==============================
# WORD DOCUMENT EXPORT
# ==============================
def build_word_doc(history: list, provider: str, file_names: list) -> bytes:
    """Generate a nicely formatted .docx and return as bytes."""
    doc = DocxDocument()

    # ── Page margins (1 inch all sides) ──────────────────────
    section = doc.sections[0]
    section.top_margin    = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin   = Inches(1)
    section.right_margin  = Inches(1)

    GOLD   = RGBColor(0xA0, 0x73, 0x2A)
    DARK   = RGBColor(0x1A, 0x16, 0x12)
    MUTED  = RGBColor(0x6B, 0x65, 0x60)

    # ── Title ────────────────────────────────────────────────
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = title_para.add_run("Reasoning Forge")
    run.font.size  = Pt(26)
    run.font.bold  = True
    run.font.color.rgb = GOLD
    run.font.name  = "Georgia"

    sub = doc.add_paragraph()
    sr  = sub.add_run(f"Conversation Export  ·  Engine: {provider}")
    sr.font.size  = Pt(10)
    sr.font.color.rgb = MUTED
    sr.font.name  = "Arial"

    # ── Metadata table ───────────────────────────────────────
    timestamp  = datetime.datetime.now().strftime("%d %B %Y, %H:%M:%S")
    files_str  = ", ".join(file_names) if file_names else "None"
    turn_count = sum(1 for m in history if m["role"] == "user")

    meta = doc.add_table(rows=3, cols=2)
    meta.style = "Table Grid"
    labels = ["Date", "Files Attached", "Total Turns"]
    values = [timestamp, files_str, str(turn_count)]
    for i, (lbl, val) in enumerate(zip(labels, values)):
        lc = meta.rows[i].cells[0]
        vc = meta.rows[i].cells[1]
        lp = lc.paragraphs[0]
        vp = vc.paragraphs[0]
        lr = lp.add_run(lbl)
        lr.font.bold  = True
        lr.font.size  = Pt(9)
        lr.font.color.rgb = GOLD
        vr = vp.add_run(val)
        vr.font.size  = Pt(9)
        vr.font.color.rgb = DARK

    doc.add_paragraph()  # spacer

    # ── Conversation turns ───────────────────────────────────
    turn_num = 0
    for msg in history:
        if msg["role"] == "user":
            turn_num += 1
            # Turn header
            th = doc.add_paragraph()
            tr = th.add_run(f"Turn {turn_num}  ·  You")
            tr.font.bold  = True
            tr.font.size  = Pt(9)
            tr.font.color.rgb = GOLD
            tr.font.name  = "Arial"

            # User message box (shaded paragraph)
            up = doc.add_paragraph()
            up.paragraph_format.left_indent  = Inches(0.2)
            up.paragraph_format.right_indent = Inches(0.5)
            up.paragraph_format.space_after  = Pt(6)
            ur = up.add_run(msg["content"])
            ur.font.size  = Pt(10.5)
            ur.font.color.rgb = DARK
            ur.font.name  = "Arial"

        else:  # assistant
            # Strip <think> for export
            content = msg["content"]
            if "<think>" in content and "</think>" in content:
                content = content.split("</think>")[-1].strip()

            elapsed = msg.get("elapsed")
            ts      = msg.get("ts", "")

            # AI label
            al = doc.add_paragraph()
            ar = al.add_run(f"✦ Reasoning Forge  ·  {ts}")
            ar.font.bold  = True
            ar.font.size  = Pt(9)
            ar.font.color.rgb = MUTED
            ar.font.name  = "Arial"

            # Timing line
            if elapsed is not None:
                tl = doc.add_paragraph()
                tr2 = tl.add_run(f"⏱  Generated in {elapsed_label(elapsed)}")
                tr2.font.size      = Pt(8.5)
                tr2.font.italic    = True
                tr2.font.color.rgb = RGBColor(0xA0, 0x73, 0x2A)
                tr2.font.name      = "Arial"

            # AI response — split into paragraphs
            for para_text in re.split(r'\n{2,}', content.strip()):
                para_text = para_text.strip()
                if not para_text:
                    continue
                rp = doc.add_paragraph()
                rp.paragraph_format.left_indent  = Inches(0.2)
                rp.paragraph_format.right_indent = Inches(0.2)
                rp.paragraph_format.space_after  = Pt(4)
                rr = rp.add_run(para_text.replace('\n', ' '))
                rr.font.size  = Pt(10.5)
                rr.font.color.rgb = DARK
                rr.font.name  = "Arial"

            # Divider rule
            div = doc.add_paragraph()
            div_fmt = div.paragraph_format
            div_fmt.space_before = Pt(6)
            div_fmt.space_after  = Pt(6)
            div.paragraph_format.border_bottom = None
            # Use bottom border on the paragraph as a visual rule
            from docx.oxml.ns import qn
            from docx.oxml   import OxmlElement
            pPr = div._p.get_or_add_pPr()
            pBdr = OxmlElement('w:pBdr')
            bottom = OxmlElement('w:bottom')
            bottom.set(qn('w:val'),   'single')
            bottom.set(qn('w:sz'),    '4')
            bottom.set(qn('w:space'), '1')
            bottom.set(qn('w:color'), 'D4B896')
            pBdr.append(bottom)
            pPr.append(pBdr)

    # ── Footer note ──────────────────────────────────────────
    doc.add_paragraph()
    fn = doc.add_paragraph()
    fnr = fn.add_run("Exported from Reasoning Forge  ·  " + datetime.datetime.now().strftime("%Y-%m-%d"))
    fnr.font.size      = Pt(8)
    fnr.font.italic    = True
    fnr.font.color.rgb = MUTED
    fn.alignment       = WD_ALIGN_PARAGRAPH.CENTER

    # ── Serialize to bytes ───────────────────────────────────
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


# ==============================
# EXCEL EXPORT
# ==============================
def build_excel_doc(history: list, provider: str, file_names: list) -> bytes:
    """Generate a structured .xlsx with two sheets and return as bytes."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()

    GOLD_HEX   = "A0732A"
    GOLD_LIGHT = "F5ECD7"
    WHITE      = "FFFFFF"
    DARK       = "1A1612"
    USER_BG    = "FFF8EE"

    thin   = Side(style="thin", color="D4B896")
    border = Border(top=thin, bottom=thin, left=thin, right=thin)

    # ── Sheet 1: Full Conversation ───────────────────────────
    ws = wb.active
    ws.title = "Conversation"

    # Title bar
    ws.merge_cells("A1:E1")
    c = ws["A1"]
    c.value = "Reasoning Forge — Conversation Export"
    c.font  = Font(name="Arial", bold=True, size=15, color=GOLD_HEX)
    c.fill  = PatternFill("solid", fgColor=GOLD_LIGHT)
    c.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 28

    # Metadata rows
    meta = [
        ("Date",           datetime.datetime.now().strftime("%d %B %Y, %H:%M:%S")),
        ("Engine",         provider),
        ("Files Attached", ", ".join(file_names) if file_names else "None"),
        ("Total Turns",    str(sum(1 for m in history if m["role"] == "user"))),
    ]
    for r, (lbl, val) in enumerate(meta, start=2):
        lc = ws.cell(row=r, column=1, value=lbl)
        vc = ws.cell(row=r, column=2, value=val)
        lc.font = Font(name="Arial", bold=True, size=9, color=GOLD_HEX)
        vc.font = Font(name="Arial", size=9, color=DARK)
        ws.merge_cells(f"B{r}:E{r}")

    ws.row_dimensions[6].height = 8  # spacer

    # Column headers
    hdr_row = 7
    headers    = ["Turn", "Role", "Timestamp", "Response Time", "Message"]
    col_widths = [6, 12, 22, 16, 90]
    for col, (hdr, w) in enumerate(zip(headers, col_widths), start=1):
        cell = ws.cell(row=hdr_row, column=col, value=hdr)
        cell.font      = Font(name="Arial", bold=True, size=10, color=WHITE)
        cell.fill      = PatternFill("solid", fgColor=GOLD_HEX)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border    = border
        ws.column_dimensions[get_column_letter(col)].width = w
    ws.row_dimensions[hdr_row].height = 22

    # Data rows
    turn_num = 0
    data_row = hdr_row + 1
    for msg in history:
        role    = msg["role"]
        content = msg["content"]
        if "<think>" in content and "</think>" in content:
            content = content.split("</think>")[-1].strip()
        content = content.strip()

        if role == "user":
            turn_num  += 1
            role_label = "You"
            bg         = USER_BG
            time_val   = "—"
        else:
            role_label = "✦ AI"
            bg         = WHITE
            elapsed    = msg.get("elapsed")
            time_val   = elapsed_label(elapsed) if elapsed is not None else "—"

        row_fill = PatternFill("solid", fgColor=bg)
        values   = [turn_num if role == "user" else "", role_label,
                    msg.get("ts", ""), time_val, content]

        for col, val in enumerate(values, start=1):
            cell = ws.cell(row=data_row, column=col, value=val)
            cell.fill      = row_fill
            cell.border    = border
            cell.alignment = Alignment(vertical="top", wrap_text=True,
                                       horizontal="center" if col < 5 else "left")
            cell.font      = Font(
                name="Arial", size=9,
                color=GOLD_HEX if col == 2 else DARK,
                bold=(col == 2)
            )

        # Auto row height based on content length
        lines = max(1, len(content) // 100 + content.count('\n') + 1)
        ws.row_dimensions[data_row].height = min(max(20, lines * 15), 200)
        data_row += 1

    ws.freeze_panes = f"A{hdr_row + 1}"

    # ── Sheet 2: Timing Summary ──────────────────────────────
    ws2 = wb.create_sheet("Timing Summary")
    for col, w in zip(["A","B","C","D"], [8, 24, 30, 20]):
        ws2.column_dimensions[col].width = w

    ws2.merge_cells("A1:D1")
    t = ws2["A1"]
    t.value = "Response Timing by Turn"
    t.font  = Font(name="Arial", bold=True, size=13, color=GOLD_HEX)
    t.fill  = PatternFill("solid", fgColor=GOLD_LIGHT)
    t.alignment = Alignment(horizontal="left", vertical="center")
    ws2.row_dimensions[1].height = 26

    for col, hdr in enumerate(["Turn", "Timestamp", "Engine", "Response Time"], start=1):
        cell = ws2.cell(row=2, column=col, value=hdr)
        cell.font      = Font(name="Arial", bold=True, size=10, color=WHITE)
        cell.fill      = PatternFill("solid", fgColor=GOLD_HEX)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border    = border
    ws2.row_dimensions[2].height = 20

    turn_num2 = 0
    row2 = 3
    for msg in history:
        if msg["role"] == "user":
            turn_num2 += 1
            continue
        elapsed  = msg.get("elapsed")
        row_bg   = "FFF8EE" if row2 % 2 == 0 else WHITE
        for col, val in enumerate([
            turn_num2,
            msg.get("ts", ""),
            provider,
            elapsed_label(elapsed) if elapsed is not None else "—"
        ], start=1):
            cell = ws2.cell(row=row2, column=col, value=val)
            cell.font      = Font(name="Arial", size=9, color=DARK)
            cell.fill      = PatternFill("solid", fgColor=row_bg)
            cell.alignment = Alignment(horizontal="center")
            cell.border    = border
        ws2.row_dimensions[row2].height = 18
        row2 += 1

    ws2.freeze_panes = "A3"

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.markdown("### ✦ Settings")
    PROVIDER = st.selectbox(
        "Reasoning Engine",
        ["Metal-llama (Reasoning Expert)", "nemotron-3 by Nvidia (Logic Focused)", "Stepfun"]
    )

    st.markdown("---")
    st.markdown("**Attach Context Files**")
    st.caption("Files are loaded into every conversation turn automatically.")
    uploaded_files = st.file_uploader(
        "Upload files",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "xlsx", "xls", "csv"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    current_names = [f.name for f in uploaded_files] if uploaded_files else []
    if current_names != st.session_state.file_names:
        if uploaded_files:
            combined = ""
            for f in uploaded_files:
                f.seek(0)
                text, ftype = extract_text(f)
                combined += f"\n\n--- FILE: {f.name} ({ftype}) ---\n{text}\n"
            st.session_state.file_context = combined
        else:
            st.session_state.file_context = ""
        st.session_state.file_names = current_names

    if uploaded_files:
        for f in uploaded_files:
            st.markdown(f"<span class='file-badge'>📎 {f.name}</span>", unsafe_allow_html=True)

    st.markdown("---")

    if st.button("🗑 Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

    if st.session_state.messages:
        st.markdown("**⬇ Export Conversation**")
        ts_stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

        # Word doc
        docx_bytes = build_word_doc(
            st.session_state.messages, PROVIDER, st.session_state.file_names
        )
        st.download_button(
            label="📄 Download as Word (.docx)",
            data=docx_bytes,
            file_name=f"reasoning_forge_{ts_stamp}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        # Excel doc
        xlsx_bytes = build_excel_doc(
            st.session_state.messages, PROVIDER, st.session_state.file_names
        )
        st.download_button(
            label="📊 Download as Excel (.xlsx)",
            data=xlsx_bytes,
            file_name=f"reasoning_forge_{ts_stamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ==============================
# MAIN INTERFACE
# ==============================
st.markdown(
    "<h1 style='font-family:Cormorant Garamond; font-size:3.5rem; font-weight:300; margin-bottom:0;'>"
    "Reasoning <em style='color:#a0732a; font-style:italic;'>Forge</em></h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='color:#6b6560; margin-top:0.25rem; margin-bottom:1.5rem;'>"
    "Powered by AI · Multi-turn conversation · Upload any files</p>",
    unsafe_allow_html=True
)

# ── Render conversation history ──────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown("<p class='bubble-label label-user'>You</p>", unsafe_allow_html=True)
        st.markdown(f"<div class='bubble-user'>{html.escape(msg['content'])}</div>", unsafe_allow_html=True)
    else:
        content = msg["content"]
        if "<think>" in content and "</think>" in content:
            content = content.split("</think>")[-1].strip()

        elapsed = msg.get("elapsed")
        ts      = msg.get("ts", "")

        st.markdown("<p class='bubble-label label-ai'>✦ Reasoning Forge</p>", unsafe_allow_html=True)
        st.markdown(f"<div class='bubble-ai'>{format_for_display(content)}</div>", unsafe_allow_html=True)

        # Timing badge under the bubble
        if elapsed is not None:
            bw  = bar_width(elapsed)
            lbl = elapsed_label(elapsed)
            st.markdown(
                f"<div class='timing-badge'>"
                f"<span class='timing-bar' style='width:{bw}px'></span>"
                f"⏱ {lbl} &nbsp;·&nbsp; {ts}"
                f"</div>",
                unsafe_allow_html=True
            )

if st.session_state.messages:
    st.markdown("<hr class='turn-divider'>", unsafe_allow_html=True)

# ── Input ────────────────────────────────────────────────────
user_query = st.text_area(
    "Your message:" if st.session_state.messages else "Define your problem:",
    height=130,
    placeholder="Continue the conversation, or ask a follow-up question...",
    key="user_input"
)

col1, col2 = st.columns([3, 1])
with col1:
    send = st.button("✦ Send" if st.session_state.messages else "✦ Start Reasoning")
with col2:
    if st.session_state.messages and st.button("↩ New Chat"):
        st.session_state.messages = []
        st.rerun()

# ── Handle send ──────────────────────────────────────────────
if send:
    if not user_query.strip():
        st.warning("Please enter a message.")
    else:
        ts_now = datetime.datetime.now().strftime("%d %b %Y, %H:%M")
        st.session_state.messages.append({
            "role": "user", "content": user_query.strip(),
            "elapsed": None, "ts": ts_now
        })

        with st.spinner(f"{PROVIDER} is thinking..."):
            reply, elapsed = get_llm_response(
                st.session_state.messages,
                st.session_state.file_context,
                PROVIDER
            )

        st.session_state.messages.append({
            "role": "assistant", "content": reply,
            "elapsed": elapsed, "ts": ts_now
        })

        st.rerun()
