# Sources of the third-party documents used as test and RAG material

This project used two public documents from the e-wallet MoMo as realistic policy text for the policy-search (RAG) feature and for evaluation scenarios. They are **not redistributed as PDFs** in this repository: the copyright belongs to the publisher. This file records where they came from, so the material can be re-collected from the original pages.

| Document | Original page | Collected | What the copy contained | Local copy |
|---|---|---|---|---|
| MoMo "Frequently asked questions — transactions" | <https://www.momo.vn/hoi-dap> (stated on page 1 of the removed PDF: "Nguồn: Trang Hỏi đáp chính thức của MoMo") | 2026-08-07 (stated on page 1) | 239 questions, 83 pages, text kept verbatim, scope: transfers, top-ups and withdrawals, payments, incidents and complaints | `MoMo_FAQ_Giao_dich.pdf` removed; `MoMo_FAQ_Giao_dich.docx` still present, see below |
| MoMo "Terms and conditions of service" | A link to <https://www.momo.vn/quy-che-hoat-dong-ung-dung-tmdt> is embedded in the removed PDF. The exact page the terms were copied from is not recorded in the repository `[CHƯA XÁC MINH]` | PDF created 2026-08-07 (file metadata); no collection date stated | 18 pages | `MoMo_ToS.pdf` removed; `MoMo_ToS.docx` still present, see below |

Fingerprints of the removed files, so a re-collected copy can be compared (SHA-256, first 16 hex characters):

- `MoMo_FAQ_Giao_dich.pdf` — 5,210,820 bytes — `ffba12bb87c420db…`
- `MoMo_ToS.pdf` — 380,001 bytes — `43105749f2861c9c…`

The PDFs were added in a single commit, `53971a0` (2026-08-09). They remain in the git history until it is rewritten; see the removal instructions given with this change.

## Still present in this directory

- `MoMo_FAQ_Giao_dich.docx` and `MoMo_ToS.docx` hold the same text as the PDFs and are read by `eval/do_phu_kho.py`. They have the same copyright question and were **not** removed because the change request named the PDFs only. `[CHƯA XÁC MINH: whether to remove them as well]`
- `business_rules.md`, `scenario-candidates-momo-faq.md`, `utterance_bank.yaml` are this project's own notes and test utterances. Fee and limit numbers in them were taken from the public MoMo FAQ and, for the comparison in `scenario-candidates-momo-faq.md` §8, from public ZaloPay fee pages. They are modelling assumptions for a simulated dataset, not statements about either company's current terms.

## How to re-collect

1. Open the original pages above and save or print them to PDF/DOCX locally.
2. Keep the copies out of version control (`data/raw/*.pdf` is the place; add it to `.gitignore` if you want git to ignore it).
3. Compare with the fingerprints above only to see whether the page changed since 2026-08-07.
