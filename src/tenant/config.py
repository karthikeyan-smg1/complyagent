"""Pydantic models for a tenant's `config.yaml`.

Single source of truth for the schema. The pipeline reads `TenantConfig` instances;
adding a new tenant is a matter of dropping a `tenants/<slug>/config.yaml` that
validates against these models.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TenantInfo(BaseModel):
    slug: str
    display_name: str
    contact_email: str | None = None


class CodebaseConfig(BaseModel):
    provider: Literal["github"] = "github"
    repo: str
    default_branch: str = "main"
    language_hint: str | None = None


class ProductProfileRef(BaseModel):
    path: str


class RegulatoryScope(BaseModel):
    jurisdictions: list[str] = Field(default_factory=list)
    payment_rails: list[str] = Field(default_factory=list)
    card_networks: list[str] = Field(default_factory=list)
    central_banks: list[str] = Field(default_factory=list)


class ScheduleConfig(BaseModel):
    cron: str = "0 6 * * 1"
    timezone: str = "UTC"
    enabled: bool = False


class GitHubIssueTarget(BaseModel):
    repo: str
    labels: list[str] = Field(default_factory=list)
    assignees: list[str] = Field(default_factory=list)


class JiraIssueTarget(BaseModel):
    enabled: bool = False
    site: str | None = None
    project_key: str | None = None
    issue_type: str | None = None


class IssueTrackerConfig(BaseModel):
    primary: Literal["github", "jira"] = "github"
    github: GitHubIssueTarget | None = None
    jira: JiraIssueTarget = Field(default_factory=JiraIssueTarget)


class ChannelToggle(BaseModel):
    enabled: bool = False


class NotificationsConfig(BaseModel):
    slack: ChannelToggle = Field(default_factory=ChannelToggle)
    email: ChannelToggle = Field(default_factory=ChannelToggle)


class PriorityRubricConfig(BaseModel):
    use_default: bool = True
    weights: dict[str, float] | None = None


class EvalConfig(BaseModel):
    ground_truth_path: str


class TenantConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant: TenantInfo
    codebase: CodebaseConfig
    product_profile: ProductProfileRef
    regulatory_scope: RegulatoryScope
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)
    issue_tracker: IssueTrackerConfig
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)
    priority_rubric: PriorityRubricConfig = Field(default_factory=PriorityRubricConfig)
    eval: EvalConfig
