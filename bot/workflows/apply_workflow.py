import os
import re
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from bot.config import Config
from bot.workflows.base_workflow import BaseWorkflow
from bot.llm.base import LLMProvider

class ApplyWorkflow(BaseWorkflow):
    """
    Executes the fit evaluation and document drafting workflow.
    """

    async def fetch_job_text_if_url(self, job_text_or_url: str) -> str:
        """
        If user passed a URL, automatically fetch the actual job description content.
        """
        cleaned = job_text_or_url.strip()
        if cleaned.startswith("http://") or cleaned.startswith("https://"):
            loop = asyncio.get_running_loop()
            def _fetch():
                import urllib.request
                from bs4 import BeautifulSoup
                req = urllib.request.Request(
                    cleaned,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                )
                try:
                    with urllib.request.urlopen(req, timeout=12) as res:
                        html = res.read().decode("utf-8")
                    soup = BeautifulSoup(html, "html.parser")

                    # Try LinkedIn container first
                    desc = soup.find("div", class_="show-more-less-html__markup")
                    if desc:
                        return desc.get_text(separator="\n", strip=True)

                    # Try general article / main / body text
                    main = soup.find("main") or soup.find("article") or soup.find("body")
                    if main:
                        # Strip script and style
                        for s in main(["script", "style", "nav", "footer", "header"]):
                            s.decompose()
                        return main.get_text(separator="\n", strip=True)[:8000]
                except Exception as e:
                    print(f"[WARN] Failed fetching job URL: {e}")
                return cleaned

            fetched = await loop.run_in_executor(None, _fetch)
            if fetched and len(fetched) > 100:
                return fetched
        return cleaned

    async def evaluate_fit(self, job_text_or_url: str) -> Dict[str, Any]:
        """
        Step 1: Evaluate candidate fit against the job description using LLM.
        """
        actual_job_content = await self.fetch_job_text_if_url(job_text_or_url)
        profile_context = self.get_candidate_profile_context()
        rubric = self.read_file(".claude/skills/job-application-assistant/04-job-evaluation.md")

        system_prompt = (
            "You are an expert career advisor and technical recruiter evaluating job fit for a candidate in India.\n"
            "Evaluate the provided job posting against the candidate's background and rubric.\n\n"
            f"{profile_context}\n\n"
            f"=== EVALUATION RUBRIC ===\n{rubric}\n\n"
            "Format your output in clean Markdown with:\n"
            "1. **Job & Company Overview**\n"
            "2. **Skills Match & Gaps** (Matching vs Missing tech stack)\n"
            "3. **Experience & Location Match** (1-3+ yr expectation, Indian tech hubs/remote)\n"
            "4. **Overall Fit Rating** (e.g. 85/100 — Strong Fit / Moderate Fit / Weak Fit)\n"
            "5. **Recommendation & Key Tailoring Strategy**"
        )

        user_message = f"Please evaluate fit for this job posting:\n\n{actual_job_content}"

        response = await self.llm.complete(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.2
        )

        return {
            "evaluation": response,
            "raw_input": job_text_or_url
        }

    async def draft_and_compile(
        self,
        job_text_or_url: str,
        company_clean: str = "Company",
        role_clean: str = "Backend_Engineer"
    ) -> Tuple[Optional[Path], Optional[Path], str]:
        """
        Directly drafts tailored LaTeX CV, saves .tex, and compiles to PDF if compiler is available.
        Bypasses lengthy narrative evaluations to save tokens and speed up generation.
        Returns: (cv_pdf_path, cover_pdf_path, status_notes)
        """
        # Fetch clean job description text if URL was passed
        actual_job_content = await self.fetch_job_text_if_url(job_text_or_url)

        profile_context = self.get_candidate_profile_context()
        cv_template = self.read_file("cv/main_example.tex")

        safe_company = re.sub(r'[^a-zA-Z0-9_]', '', company_clean.replace(" ", "_"))
        safe_role = re.sub(r'[^a-zA-Z0-9_]', '', role_clean.replace(" ", "_"))

        cv_tex_path = self.workspace_dir / "cv" / f"main_{safe_company}_{safe_role}.tex"
        cover_tex_path = self.workspace_dir / "cover_letters" / f"cover_{safe_company}_{safe_role}.tex"

        system_prompt = (
            "You are an expert technical resume tailor.\n"
            "Generate ONLY the complete, ready-to-compile LaTeX source code for the candidate's CV.\n"
            "STRICT RULES:\n"
            "1. You MUST use the EXACT LaTeX document structure, preamble, package definitions, and custom macros "
            "(\\resumeItem, \\resumeSubheading, \\resumeSubSubheading, \\section) provided in the BASE CV TEMPLATE.\n"
            "2. Do NOT switch to any other LaTeX class or template (do NOT use moderncv, do NOT use res.cls, etc.).\n"
            "3. Tailor the \\section{Professional Summary}, relevant \\resumeItem bullet points under projects, and \\section{Skills} "
            "to highlight alignment with the target job posting.\n"
            "4. Strictly preserve the candidate's factual details (Crest Data, project names, education, awards).\n"
            "5. Return ONLY raw valid LaTeX code starting with \\documentclass and ending with \\end{document}. "
            "Do NOT include markdown formatting like ```latex or conversational commentary.\n\n"
            f"{profile_context}\n"
        )

        prompt = (
            f"=== TARGET JOB POSTING ===\n{actual_job_content[:4000]}\n\n"
            f"=== BASE CV TEMPLATE (MANDATORY STRUCTURE) ===\n{cv_template}\n\n"
            "Generate the tailored CV following the exact template above."
        )

        # Single direct call to LLM to draft tailored CV
        cv_code = await self.llm.complete(system_prompt=system_prompt, user_message=prompt)
        clean_cv = re.sub(r'^```latex\s*', '', cv_code, flags=re.MULTILINE)
        clean_cv = re.sub(r'^```\s*$', '', clean_cv, flags=re.MULTILINE).strip()

        with open(cv_tex_path, "w", encoding="utf-8") as f:
            f.write(clean_cv)

        # Check compiler availability: pdflatex or lualatex
        cv_pdf_path = None
        cover_pdf_path = None
        notes = []

        compiler = None
        # Check standard PATH as well as default MiKTeX install path
        candidate_compilers = [
            "pdflatex",
            r"C:\Users\jainish chauhan\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe",
            "lualatex",
            "xelatex"
        ]
        for candidate_cmd in candidate_compilers:
            try:
                res = subprocess.run([candidate_cmd, "--version"], capture_output=True, text=True)
                if res.returncode == 0:
                    compiler = candidate_cmd
                    break
            except (FileNotFoundError, OSError):
                continue

        if compiler:
            try:
                cmd = [compiler, "-interaction=nonstopmode"]
                if "miktex" in compiler.lower() or "pdflatex" in compiler.lower():
                    cmd.append("--enable-installer")
                cmd.append(cv_tex_path.name)

                subprocess.run(
                    cmd,
                    cwd=str(cv_tex_path.parent),
                    capture_output=True,
                    timeout=90
                )
                potential_pdf = cv_tex_path.with_suffix(".pdf")
                if potential_pdf.exists():
                    cv_pdf_path = potential_pdf
                    notes.append(f"✅ CV PDF compiled successfully with `{Path(compiler).stem}`.")
            except Exception as e:
                notes.append(f"⚠️ Compilation note: {e}")
        else:
            notes.append(
                "ℹ️ Tailored LaTeX source generated using your custom template and saved to:\n"
                f"`cv/{cv_tex_path.name}`\n\n"
                "To auto-compile into PDF locally on your PC, install MiKTeX (see guide below)."
            )

        return cv_pdf_path, cover_pdf_path, "\n".join(notes)
