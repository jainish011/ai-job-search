import re
from pathlib import Path
from typing import Dict, Any
from bot.config import Config
from bot.workflows.base_workflow import BaseWorkflow

class SetupWorkflow(BaseWorkflow):
    """
    Parses resume text or PDF content and updates:
    - CLAUDE.md (Identity, Education, Experience, Skills, Profile)
    - .claude/skills/job-application-assistant/01-candidate-profile.md
    """

    async def ingest_resume(self, resume_text: str) -> str:
        system_prompt = (
            "You are an expert resume parser and profile extractor for an AI job search assistant.\n"
            "Extract structured information from the provided resume text.\n"
            "Produce an updated, clean version of CLAUDE.md that preserves the exact markdown structure and section headers.\n\n"
            "Target Headers to fill in:\n"
            "- ### Identity (Name, Location, Status, Headline, Languages)\n"
            "- ### Education (Degrees, Year, Institution, Details)\n"
            "- ### Professional Experience (Job Title, Dates, Company, Location, Responsibilities, Achievements)\n"
            "- ### Technical Skills (Primary, Secondary, Domain, Software/Tools)\n"
            "- ### Certifications\n"
            "- ### Behavioral Profile & Strengths\n\n"
            "Rules:\n"
            "1. Be 100% factual — do not invent any experience, degrees, or companies.\n"
            "2. Preserve all existing template formatting.\n"
            "3. Return ONLY the markdown content for CLAUDE.md without commentary."
        )

        current_claude_md = self.read_file("CLAUDE.md")
        user_prompt = (
            f"=== BASE CLAUDE.md TEMPLATE ===\n{current_claude_md}\n\n"
            f"=== CANDIDATE RESUME / DETAILS ===\n{resume_text}\n\n"
            "Extract all facts and return the fully populated CLAUDE.md."
        )

        updated_claude_md = await self.llm.complete(
            system_prompt=system_prompt,
            user_message=user_prompt,
            temperature=0.1
        )

        # Clean markdown wrappers if returned
        clean_text = re.sub(r'^```markdown\s*', '', updated_claude_md, flags=re.MULTILINE)
        clean_text = re.sub(r'^```\s*$', '', clean_text, flags=re.MULTILINE).strip()

        # Save to CLAUDE.md
        claude_path = self.workspace_dir / "CLAUDE.md"
        with open(claude_path, "w", encoding="utf-8") as f:
            f.write(clean_text)

        # Also update 01-candidate-profile.md
        p01_path = self.workspace_dir / ".claude" / "skills" / "job-application-assistant" / "01-candidate-profile.md"
        if p01_path.exists():
            with open(p01_path, "w", encoding="utf-8") as f:
                f.write(clean_text)

        return clean_text
