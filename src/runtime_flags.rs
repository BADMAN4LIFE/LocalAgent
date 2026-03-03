use crate::agent::PlanToolEnforcementMode;
use crate::cli_args::AgentMode;
use crate::planner::RunMode;
use crate::session::ExplicitFlags;
use crate::RunArgs;

#[derive(Debug, Clone, Copy, Default)]
pub(crate) struct CapabilityExplicitFlags {
    pub allow_shell: bool,
    pub allow_shell_in_workdir: bool,
    pub allow_write: bool,
    pub enable_write_tools: bool,
}

pub(crate) fn parse_explicit_flags() -> ExplicitFlags {
    let mut out = ExplicitFlags::default();
    for arg in std::env::args() {
        if arg == "--max-context-chars" || arg.starts_with("--max-context-chars=") {
            out.max_context_chars = true;
        } else if arg == "--compaction-mode" || arg.starts_with("--compaction-mode=") {
            out.compaction_mode = true;
        } else if arg == "--compaction-keep-last" || arg.starts_with("--compaction-keep-last=") {
            out.compaction_keep_last = true;
        } else if arg == "--tool-result-persist" || arg.starts_with("--tool-result-persist=") {
            out.tool_result_persist = true;
        } else if arg == "--tool-args-strict" || arg.starts_with("--tool-args-strict=") {
            out.tool_args_strict = true;
        } else if arg == "--caps" || arg.starts_with("--caps=") {
            out.caps_mode = true;
        } else if arg == "--hooks" || arg.starts_with("--hooks=") {
            out.hooks_mode = true;
        }
    }
    out
}

pub(crate) fn has_explicit_plan_tool_enforcement_flag() -> bool {
    std::env::args()
        .any(|arg| arg == "--enforce-plan-tools" || arg.starts_with("--enforce-plan-tools="))
}

pub(crate) fn parse_capability_explicit_flags() -> CapabilityExplicitFlags {
    let mut out = CapabilityExplicitFlags::default();
    for arg in std::env::args() {
        if arg == "--allow-shell" || arg.starts_with("--allow-shell=") {
            out.allow_shell = true;
        } else if arg == "--allow-shell-in-workdir" || arg.starts_with("--allow-shell-in-workdir=")
        {
            out.allow_shell_in_workdir = true;
        } else if arg == "--allow-write" || arg.starts_with("--allow-write=") {
            out.allow_write = true;
        } else if arg == "--enable-write-tools" || arg.starts_with("--enable-write-tools=") {
            out.enable_write_tools = true;
        }
    }
    out
}

pub(crate) fn apply_agent_mode_capability_baseline(
    args: &mut RunArgs,
    explicit: CapabilityExplicitFlags,
) {
    if !matches!(args.agent_mode, AgentMode::Plan) {
        return;
    }

    if !explicit.enable_write_tools {
        args.enable_write_tools = false;
    }
    if !explicit.allow_write {
        args.allow_write = false;
    }
    if !explicit.allow_shell {
        args.allow_shell = false;
    }
    if !explicit.allow_shell_in_workdir {
        args.allow_shell_in_workdir = false;
    }
}

pub(crate) fn resolve_plan_tool_enforcement(
    mode: RunMode,
    configured: PlanToolEnforcementMode,
    explicit: bool,
) -> PlanToolEnforcementMode {
    if matches!(mode, RunMode::PlannerWorker)
        && matches!(configured, PlanToolEnforcementMode::Off)
        && !explicit
    {
        PlanToolEnforcementMode::Hard
    } else {
        configured
    }
}
