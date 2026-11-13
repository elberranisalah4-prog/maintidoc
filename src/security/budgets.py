"""Execution Budget & Quota Manager.

Enforces execution budgets specified in the cadrage:
- 3 MCP calls max per request
- 6 model calls max per request
- 60 seconds processing timeout
- Size and token limits
"""

import time
from typing import Optional
from config import settings

class ExecutionBudgetExceeded(Exception):
    pass

class RequestBudgetTracker:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.start_time = time.time()
        self.mcp_calls_count = 0
        self.model_calls_count = 0
        self.total_tokens_used = 0
        self.is_paused_for_human = False
        self.human_wait_elapsed = 0.0
        self._pause_timestamp: Optional[float] = None

    def record_model_call(self, tokens_used: int = 0):
        self.model_calls_count += 1
        self.total_tokens_used += tokens_used
        if self.model_calls_count > settings.budget.max_model_calls:
            raise ExecutionBudgetExceeded(
                f"Budget dépassé : {self.model_calls_count} appels au modèle (max {settings.budget.max_model_calls})"
            )
        self.check_timeout()

    def record_mcp_call(self):
        self.mcp_calls_count += 1
        if self.mcp_calls_count > settings.budget.max_mcp_calls:
            raise ExecutionBudgetExceeded(
                f"Budget dépassé : {self.mcp_calls_count} appels MCP (max {settings.budget.max_mcp_calls})"
            )
        self.check_timeout()

    def pause_for_human(self):
        """Pauses runtime clock while waiting for human technician feedback."""
        if not self.is_paused_for_human:
            self._pause_timestamp = time.time()
            self.is_paused_for_human = True

    def resume_from_human(self):
        """Resumes runtime clock after technician approved/rejected."""
        if self.is_paused_for_human and self._pause_timestamp:
            self.human_wait_elapsed += (time.time() - self._pause_timestamp)
            self.is_paused_for_human = False
            self._pause_timestamp = None

    def check_timeout(self):
        current_time = time.time()
        effective_elapsed = current_time - self.start_time - self.human_wait_elapsed
        if effective_elapsed > settings.budget.max_processing_time_sec:
            raise ExecutionBudgetExceeded(
                f"Délai d'exécution automatique dépassé ({effective_elapsed:.1f}s > {settings.budget.max_processing_time_sec}s)"
            )

    def get_summary(self) -> dict:
        current_time = time.time()
        effective_elapsed = current_time - self.start_time - self.human_wait_elapsed
        return {
            "mcp_calls": self.mcp_calls_count,
            "max_mcp_calls": settings.budget.max_mcp_calls,
            "model_calls": self.model_calls_count,
            "max_model_calls": settings.budget.max_model_calls,
            "elapsed_seconds": round(effective_elapsed, 2),
            "total_tokens_used": self.total_tokens_used
        }
