# `.github` README

## References

- `act`, a local GHA runner: <https://github.com/nektos/act>
- [abatilo/actions-poetry](https://github.com/abatilo/actions-poetry)
- [actions/cache](https://github.com/marketplace/actions/cache)
- [actions/checkout](https://github.com/actions/checkout)
- [actions/setup-python](https://github.com/actions/setup-python)
- [GitHub Action Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [pre-commit/action](https://github.com/pre-commit/action) (Now deprecated)
- [ts-graphviz/setup-graphviz](https://github.com/ts-graphviz/setup-graphviz)

The GitHub Workflows and Action were influenced by these excellent examples:

- [Re-engineering the SciPy Pipelines](https://labs.quansight.org/blog/2021/10/re-engineering-cicd-pipelines-for-scipy/) and [Example](https://github.com/scipy/scipy/blob/c4829bddb859ffe5716a88f6abd5e0d2dc1d9045/.github/workflows/linux_meson.yml)
    - SciPy also has good examples of building Docker image with layer caching, [docker.yml](https://github.com/scipy/scipy/blob/c4829bddb859ffe5716a88f6abd5e0d2dc1d9045/.github/workflows/docker.yml) and [gitpod.yml](https://github.com/scipy/scipy/blob/c4829bddb859ffe5716a88f6abd5e0d2dc1d9045/.github/workflows/gitpod.yml)
- [PostHog Guide on GHA](https://posthog.com/blog/automating-a-software-company-with-github-actions). Includes information on Cypress, working with Amazon ECS, version bumping, etc.
- ["Awesome" GHA](https://github.com/sdras/awesome-actions)
    - ["services" Can create PG or other services in workflows!](https://github.com/Nike-Inc/knockoff-factory/blob/1567a46e5eaa3fe1bdf989ef5253f9ee0dbd69b3/.github/workflows/python-test.yaml)
    - ["artifact" optionally upload the report.zip from successful builds](https://github.com/marketplace/actions/upload-a-build-artifact)
- [General Tips](https://www.datree.io/resources/github-actions-best-practices). Keep workflows short and fast (view [usage here](https://github.com/settings/billing)), cache, [user GitHub's secret management](https://help.github.com/en/actions/automating-your-workflow-with-github-actions/creating-and-using-encrypted-secrets), and environment variables can be [scoped to an individual step](https://docs.github.com/en/actions/learn-github-actions/environment-variables)
- There are many ways to run a workflow beyond only commit events, such as [workflow_dispatch, schedule, release, comment, review, etc.](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows). Once `workflow_dispatch` is set, [workflows can be run from the CLI](https://docs.github.com/en/actions/managing-workflow-runs/manually-running-a-workflow)
- [Inspiration for caching](https://github.com/MrThearMan/savestate/blob/fb299e220ef366727857b1df0631300a027840fc/.github/workflows/main.yml)
- [mdformat pipeline](https://github.com/executablebooks/mdformat/blob/4752321bb444b51f120d8a6933583129a6ecaabb/.github/workflows/tests.yaml)
- [decopatch has a cool use of dynamic matrices from nox](https://github.com/smarie/python-decopatch/blob/e7f5e7e3794a81af9254b2d30d1f43b7a9874399/.github/workflows/base.yml#L30-L44)

### CLI Notes

```bash
# Inspect a workflow interactively
gh workflow view
# See recent history
gh run list --workflow update_docs.yml
gh run list --workflow ci_pipeline.yml
# Additional arguments for triggering workflows: https://cli.github.com/manual/gh_workflow_run
gh workflow run <filename>.yml --ref <branch> --field <key>=<var>
```
