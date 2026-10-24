# Hosted agents

Ready-made setups for agents that run in someone else's cloud and take the
skill as an upload. Copy them as they are; each one is the whole configuration.

| Platform | Files | What you paste or apply |
| --- | --- | --- |
| Claude Managed Agents | [`claude-managed-agents/`](claude-managed-agents) | the agent (`agent.md`) and its sandbox (`environment.yaml`) |
| Microsoft Copilot Studio | [`copilot-studio/instructions.md`](copilot-studio/instructions.md) | the agent's **Instructions** |

## Claude Managed Agents

### In the Claude Console

1. Get the skill as a zip: `gftd pack`, or the zip attached to each
   [GitHub release](https://github.com/phuongbv00/get-fsa-training-done/releases).
2. **Skills** → upload the zip.
3. **Managed Agents → Create**:
   - **System prompt** — everything in [`agent.md`](claude-managed-agents/agent.md)
     below its second `---`.
   - **Model** — `claude-opus-5-5`, effort **High**.
   - **Tools** — keep the built-in tools (the skill needs `bash`); `web_search`
     and `web_fetch` can be off.
   - **Skills** — the skill you uploaded.
4. Create an environment with **Limited** networking and **allow package
   managers** on, as [`environment.yaml`](claude-managed-agents/environment.yaml)
   says. The skill installs its CLI from PyPI the first time it needs it; with
   no route to PyPI it can read its references but run none of its commands.
5. Start a session and try: *"Dùng skill get-fsa-training-done: tìm CLI theo
   SKILL.md rồi chạy `FSA --version` và `FSA doctor`."*

### With the `ant` CLI

From the repository root, after reviewing the plan it prints:

```bash
ant apply hosted/claude-managed-agents/agent.md hosted/claude-managed-agents/environment.yaml
```

This uploads the skill straight from `src/get_fsa_training_done/payload/`,
creates the environment and the agent, and records their IDs in
`claude-lock.json`; run it again after an update to publish a new version.

Deliverables land in `/mnt/session/outputs/`, where the Console lets you
download them.

## Microsoft Copilot Studio

Paste [`copilot-studio/instructions.md`](copilot-studio/instructions.md) into
the agent's **Instructions**, and add the skill zip where your Copilot Studio
offers skills. Copilot Studio is not known to give an agent a shell, so this
version tells the agent to say so and to do only what needs no command —
outlines, drafts, reviews against the skill's references — rather than claim a
check it could not run.
