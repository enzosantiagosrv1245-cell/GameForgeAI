"""
Sistema de planos e feature flags (item 21 e 53 da especificação).

REGRA DE SEGURANÇA IMPORTANTE:
Não existe nenhum "código secreto" digitável no chat que desbloqueia PRO.
Um valor fixo desse tipo, uma vez exposto (print, log, captura de tela,
repositório), libera o produto pago para qualquer pessoa indefinidamente,
sem revogação possível. Em vez disso, o upgrade de plano acontece por:

  1. `User.is_admin = True`  -> setado diretamente no banco pelo operador
     (você), nunca por uma mensagem de chat.
  2. `Settings.ADMIN_EMAILS` -> lista de e-mails no .env que sempre recebem
     PRO automaticamente no login (útil para sua própria conta).
  3. `Settings.DEMO_UNLOCK_ALL_FEATURES=True` -> flag de ambiente para
     destravar tudo em modo demonstração/local.
  4. Futuro: assinatura paga real via gateway de pagamento (não
     implementada nesta versão - ver item 21 da especificação original).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.core.config import get_settings

settings = get_settings()


class Plan(str, Enum):
    FREE = "FREE"
    PRO = "PRO"


@dataclass(frozen=True)
class PlanLimits:
    can_generate_3d: bool
    chat_messages_per_day: int | None  # None = ilimitado
    projects_limit: int
    label: str


PLAN_LIMITS: dict[Plan, PlanLimits] = {
    Plan.FREE: PlanLimits(
        can_generate_3d=False,
        chat_messages_per_day=settings.FREE_CHAT_MESSAGES_PER_DAY,
        projects_limit=settings.FREE_PROJECTS_LIMIT,
        label="Free",
    ),
    Plan.PRO: PlanLimits(
        can_generate_3d=True,
        chat_messages_per_day=None,  # PRO = chat ilimitado, conforme solicitado
        projects_limit=settings.PRO_PROJECTS_LIMIT,
        label="Pro",
    ),
}


class PlanContext:
    """Encapsula as permissões efetivas de um usuário para a requisição atual."""

    def __init__(self, plan: Plan) -> None:
        self.plan = plan
        self.limits = PLAN_LIMITS[plan]

    def can_generate_3d(self) -> bool:
        return self.limits.can_generate_3d

    def chat_messages_per_day(self) -> int | None:
        return self.limits.chat_messages_per_day

    def projects_limit(self) -> int:
        return self.limits.projects_limit

    def is_unlimited_chat(self) -> bool:
        return self.limits.chat_messages_per_day is None

    @classmethod
    def for_user(cls, user) -> "PlanContext":
        """Resolve o plano efetivo de um usuário a partir do banco + config,
        nunca a partir de entrada de chat."""
        effective_plan = Plan.PRO if _is_effectively_pro(user) else Plan.FREE
        return cls(effective_plan)


def _is_effectively_pro(user) -> bool:
    if settings.DEMO_UNLOCK_ALL_FEATURES:
        return True
    if getattr(user, "is_admin", False):
        return True
    if getattr(user, "plan", "FREE") == Plan.PRO.value:
        return True
    if user.email and user.email.lower() in {e.lower() for e in settings.admin_emails_list}:
        return True
    return False