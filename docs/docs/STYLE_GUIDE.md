# Personal Style Guides

## Git

We use [Commitizen](https://github.com/commitizen-tools/commitizen) to manage both an auto-generated [Changelog](https://keepachangelog.com/en/1.0.0/) and incrementing the release version following [semver](https://semver.org/). For both of these automated outputs to work well, please follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) style, which is described in more detail below.

### Commitizen Types and Scopes

> `type(scope): description`

- **Types**
    - *fix*: A bug fix
    - *feat*: A new feature
    - *docs*: Documentation-only changes (code comments, separate docs)
    - *style*: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons)
    - *perf*: A code change that improves performance
    - *refactor*: A change to production code that is not a *fix*, *feat*, or *perf*
    - *test*: Adding missing or correcting existing tests
    - *build*: Changes that affect the build system or external dependencies
    - *ci*: Changes to our CI configuration files and scripts
    - A `!` can be used to indicate a breaking change (`refactor!: drop support for Node 6`)
    - **SemVer Rules**
        - Based on commit type, the version will be auto-incremented: `fix : PATCH // feat : MINOR // BREAKING CHANGE : MAJOR`
- **Scopes**
    - A Class, File name, Issue Number, other appropriate noun. As examples: `build(poetry): bump requests to v3` or `style(#32): add missing type annotations`
- **Tips**
    - What if a commit fits multiple types?
        - Go back and make multiple commits whenever possible. Part of the benefit of Conventional Commits is the focus on more organized and intentional changes
    - Use `git rebase -i` to fix commit names prior to merging if incorrect types/scopes are used

### Git Description Guidelines

- [Commit message guidelines](https://writingfordevelopers.substack.com/p/how-to-write-a-commit-message)
    - Full sentence with verb (*lowercase*) and concise description. Below are modified examples for Conventional Commits
        - `fix(roles): bug in admin role permissions`
        - `feat(ui): implement new button design`
        - `build(pip): upgrade package to remove vulnerabilities`
        - `refactor: file structure to improve code readability`
        - `perf(cli): rewrite methods`
        - `feat(api): endpoints to implement new customer dashboard`
- [How to write a good commit message](https://chris.beams.io/posts/git-commit/)
    - A diff will tell you what changed, but only the commit message can properly tell you why.
    - Keep in mind: [This](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html) [has](https://www.git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project#_commit_guidelines) [all](https://github.com/torvalds/subsurface-for-dirk/blob/master/README.md#contributing) [been](http://who-t.blogspot.co.at/2009/12/on-commit-messages.html) [said](https://github.com/erlang/otp/wiki/writing-good-commit-messages) [before](https://github.com/spring-projects/spring-framework/blob/30bce7/CONTRIBUTING.md#format-commit-messages).
    - From the seven rules of a great Git commit message:
        - (2) [Try for 50 characters, but consider 72 the hard limit](https://chris.beams.io/posts/git-commit/#limit-50)
        - (7) [Use the body to explain what and why vs. how](https://chris.beams.io/posts/git-commit/#why-not-how)

### Issue Labels and Milestones

Personal Guide

- For Issue Labels, see \[labels.yml\]\[labels\]
- Milestones
    - **Current Tasks**: main milestone (*name could change based on a specific project, sprint, or month*)
    - **Next Tasks**
    - **Blue Sky**

<details>
<summary>Research</summary>
<ul>
<li>[Sane GitHub Labels](https://medium.com/@dave_lunny/sane-github-labels-c5d2e6004b63) and see [sensible-github-labels](https://github.com/Relequestual/sensible-github-labels) for full descriptions of each</li>
    <ul>
        <li>“it is much more helpful to see the status and type of all issues at a glance.”</li>
        <li>One of each:</li>
        <ul>
            <li>Status: …</li>
                <ul><li>Abandoned, Accepted, Available, Blocked, Completed, In Progress, On Hold, Pending, Review Needed, Revision Needed</li></ul>
            <li>Type: …</li>
                <ul><li>Bug, Maintenance, Question, Enhancement</li></ul>
            <li>Priority: …</li>
                <ul><li>Critical, High, Medium, Low</li></ul>
        </ul>
    </ul>
    <li>[Britecharts](https://britecharts.github.io/britecharts/github-labels.html)</li>
    <ul>
        <li>Status: …</li>
            <ul>
                <li>On Review – Request that we are pondering if including or not</li>
                <li>Needs Reproducing – For bugs that need to be reproduced in order to get fixed</li>
                <li>Needs Design – Feature that needs a design</li>
                <li>Ready to Go – Issue that has been defined and is ready to get started with</li>
                <li>In Progress – Issue that is being worked on right now.</li>
                <li>Completed – Finished feature or fix</li>
            </ul>
        <li>Type: …</li>
            <ul>
                <li>Bug – An unexpected problem or unintended behavior</li>
                <li>Feature – A new feature request</li>
                <li>Maintenance – A regular maintenance chore or task, including refactors, build system, CI, performance improvements</li>
                <li>Documentation – A documentation improvement task</li>
                <li>Question – An issue or PR that needs more information or a user question</li>
            </ul>
        <li>Not Included</li>
            <ul>
                <li>Priority: They would add complexity and overhead due to the discussions, but could help with the roadmap</li>
                <li>Technology Labels: It can create too much overhead, as properly tag with technologies all the issues could be time consuming</li>
            </ul>
        </ul>
    </ul>
    <li>[Ian Bicking Blog](https://www.ianbicking.org/blog/2014/03/use-github-issues-to-organize-a-project.html)</li>
    <ul>
        <li>Milestone Overview</li>
        <ul>
            <li>What are we doing right now?</li>
            <li>What aren’t we doing right now?</li>
                <ul>
                    <li>2a. Stuff we’ll probably do soon</li>
                    <li>2b. Stuff we probably won’t do soon</li>
                </ul>
            <li>What aren’t we sure about?</li>
        </ul>
        <li>Milestone Descriptions</li>
        <ul>
            <li>Stuff we are doing right now: this is the “main” milestone. We give it a name (like Alpha 2 or Strawberry Rhubarb Pie) and we write down what we are trying to accomplish with the milestone. We create a new milestone when we are ready for the next iteration.</li>
            <li>Stuff we’ll probably do soon: this is a standing “**Next Tasks**” milestone. We never change or rename this milestone.</li>
                <ul><li>We use a permanent “Next Tasks” milestone (as opposed to renaming it to “Alpha 3” or actual-next-iteration milestone) because we don’t want to presume or default to including something in the real next iteration. When we’re ready to start planning the next iteration we’ll create a new milestone, and only deliberately move things into that milestone.</li></ul>
            <li>Stuff we probably won’t do soon: this is a standing “**Blue Sky**” milestone. We refer to these tickets and sometimes look through them, but they are easy to ignore, somewhat intentionally ignored.</li>
            <li>What aren’t we sure about?: issues with no milestone.</li>
        </ul>
        <li>Label: “Needs Discussion” - (addressed in a triage meeting) - use liberally for either big or small tickets</li>
        <li>“It’s better to give people more power: it’s actually helpful if people can overreach because it is an opportunity to establish where the limits really are and what purpose those limits have”</li>
    </ul>
</ul>
</details>

### External Links

<!-- Revisit -->

- \[Git: The Simple Guide\]\[simple_git\]
- \[Commit Messages\]\[gcmsg\] and [why use the present tense](https://news.ycombinator.com/item?id=8874177)
- [GitHub's Advice on GitHub](https://github.com/erlang/otp/wiki/Writing-good-commit-messages)
- [Most Comprehensive Guide](https://chris.beams.io/posts/git-commit/)
- [Git Pro Book (free)](https://git-scm.com/book/en/v2)
    - [Bash Tab-Completion Snippet](https://git-scm.com/book/en/v2/Appendix-A%3A-Git-in-Other-Environments-Git-in-Bash)

## Python

<!-- Revisit -->

- Python Style Guides
    - <https://gist.github.com/sloria/7001839>
    - <http://www.nilunder.com/blog/2013/08/03/pythonic-sensibilities/>
    - <https://innoq.github.io/cards42org_en/>
    - <https://docs.openstack.org/hacking/latest/user/hacking.html#styleguide>
    - <https://www.python.org/doc/humor/>
    - <https://docs.python-guide.org/writing/reading/>
    - <https://realpython.com/python-refactoring/>

## ADRs

<!-- Revisit -->

- ADR Approaches
    - <https://infraeng.dev/tech-spec> Template (And [associated review](https://infraeng.dev/tech-spec-review/)) vs. <https://infraeng.dev/decision-log/>
    - Y-Statements: [abbreviated shorthand](https://medium.com/olzzio/y-statements-10eb07b5a177). Add this as a one-line decision option if a full ADR isn't needed (or when referencing an existing ADR) (<https://scribe.rip/@docsoc/y-statements-10eb07b5a177>)
    - https://adr.github.io
    - More formal implementation of [ADRs (MADR) that this is based on](https://adr.github.io/madr/). Template: <https://github.com/adr/madr/blob/97fb8edec60b8dc70b8166ef62de34c4e26b46c0/template/adr-template.md>
    - [https://github.com/ethereum/EIPs/blob/confluenceuser/EIPS/eip-5639.md](https://github.com/ethereum/EIPs/blob/confluenceuser/EIPS/eip-5639.md)
- Examples
    - <https://github.com/pawamoy/mkdocstrings/issues/28>
    - <https://github.com/arachne-framework/architecture/blob/060a956277a5ad71df93da49fee52463408841af/adr-002-configuration.md>
    - <https://github.com/arachne-framework/architecture/tree/060a956277a5ad71df93da49fee52463408841af>
    - [https://github.com/ethereum/EIPs/blob/confluenceuser/EIPS/eip-1010.md](https://github.com/ethereum/EIPs/blob/confluenceuser/EIPS/eip-1010.md)
    - [https://docs-v1.prefect.io/core/pins/pin-01-introduce-pins.html](https://docs-v1.prefect.io/core/pins/pin-01-introduce-pins.html)
    - [https://peps.python.org/pep-0387/](https://peps.python.org/pep-0387)
    - <https://github.com/AICoE/aicoe-ci/blob/39de02af86a0d1f9dcd395fa88b858f1c6880411/docs/adr/0000-use-markdown-architectural-decision-records.md>
    - And many others!

<-- Links -->
  [simple_git]: http://rogerdudler.github.io/git-guide/
  [gcmsg]: https://github.com/atom/atom/blob/master/CONTRIBUTING.md#styleguides
  [labels]: https://github.com/kyleking/.github/labels.yml
