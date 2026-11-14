import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from bot.config import Config
from bot.llm.base import LLMProvider
from bot.llm.factory import get_llm_provider

class BaseWorkflow:
    """
    Base class for orchestrating application workflows in Python.
    Reuses existing markdown files from .claude/skills/ and .claude/commands/
    as direct context and instructions for the configured LLM.
    """

    def __init__(self, llm: Optional[LLMProvider] = None, workspace_dir: Optional[Path] = None):
        self.workspace_dir = workspace_dir or Config.WORKSPACE_DIR
        self.llm = llm or get_llm_provider()

    def read_file(self, relative_path: str) -> str:
        """
        Safely reads a text file relative to the workspace directory.
        Returns empty string if the file does not exist.
        """
        file_path = self.workspace_dir / relative_path
        if not file_path.exists():
            return ""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"[WARN] Failed to read {file_path}: {e}")
            return ""

    def get_candidate_profile_context(self) -> str:
        """
        Loads the core candidate identity, profile and evaluation rules:
        - CLAUDE.md
        - 01-candidate-profile.md
        - 04-job-evaluation.md
        Dynamically computes the current date and years of experience (YOE)
        so no experience numbers or dates are ever statically hardcoded.
        """
        import datetime
        now = datetime.datetime.now()
        current_date_str = now.strftime("%B %d, %Y")

        parts = [
            f"=== REAL-TIME TEMPORAL CONTEXT ===\n"
            f"• Current Date: {current_date_str}\n"
            f"• Instructions for Experience Calculation: Calculate the candidate's exact years of experience "
            f"dynamically by measuring from their work history start dates up to the Current Date ({current_date_str}). "
            f"Do not assume static historical dates from when the resume was originally authored.\n"
        ]

        claude_md = self.read_file("CLAUDE.md")
        if claude_md:
            parts.append(f"=== CANDIDATE PROFILE (CLAUDE.md) ===\n{claude_md}\n")

        p01 = self.read_file(".claude/skills/job-application-assistant/01-candidate-profile.md")
        if p01:
            parts.append(f"=== STRUCTURED PROFILE (01-candidate-profile.md) ===\n{p01}\n")

        p04 = self.read_file(".claude/skills/job-application-assistant/04-job-evaluation.md")
        if p04:
            parts.append(f"=== JOB EVALUATION RUBRIC (04-job-evaluation.md) ===\n{p04}\n")

        return "\n".join(parts)

    def load_command_instructions(self, command_name: str) -> str:
        """
        Loads the instructions from .claude/commands/<command_name>.md
        """
        path = f".claude/commands/{command_name}.md"
        content = self.read_file(path)
        if not content:
            # Fallback check under skills
            path = f".claude/skills/{command_name}/SKILL.md"
            content = self.read_file(path)
        return content

    async def run(self, *args: Any, **kwargs: Any) -> Any:
        """
        Execute workflow logic. Must be implemented by subclasses.
        """
        raise NotImplementedError("Workflows must implement run()")
