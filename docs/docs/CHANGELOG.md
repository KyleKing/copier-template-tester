## Unreleased

### Feat

- migrate to uv
- **#39**: add prepend_tasks and _skip_tasks

### Fix

- correct dependencies

### Refactor

- rename to pre, skip, and post tasks to complent copier's '_tasks'
- use private copier modules
- minor code cleanup

## 2.2.0 (2025-02-06)

### Feat

- add support for `_extra_tasks` in CTT TOML configuration (#36)

## 2.1.4 (2024-11-19)

### Fix

- **#34**: support `git init` on Windows (#35)

## 2.1.3 (2024-07-08)

### Fix

- update minimum Python version to 3.10.9

## 2.1.3rc0 (2024-07-05)

### Fix

- **wheel**: don't distribute top-level LICENSE file (#33)

## 2.1.2 (2024-05-02)

### Fix

- **#31**: defer to copier for template loading logic

### Refactor

- update ruff

## 2.1.1 (2023-11-23)

### Fix

- **#28**: catch untracked .ctt directory
- **#28**: append ctt-specific exclude rules

## 2.1.0 (2023-11-21)

### Feat

- improve error handling for recursion
- **#25**: add test when _subdir is not specified

### Fix

- patch Nox with Python 3.12
- don't remove the dst_path before copier run (from #24)
- include defaults in _exclude documentation

## 2.0.1 (2023-11-08)

### Fix

- **#27**: skip running copier when no copier.ya?ml file is present

## 2.0.0 (2023-10-14)

### Fix

- specifically handle templates that can't be updated
- check for answers file template
- **#24**: only write an answers file if there is content
- remove unused F401 and H303
- update copier to latest to unblock pydantic v2 upgrade

### Refactor

- remove optional beartype
- use literal to try to fix pyright errors


- pending pydantic v2 support

## 1.2.6 (2023-06-05)

### Fix

- support unsafe templates that utilize tasks

## 1.2.5 (2023-06-05)

### Fix

- support copier 8

## 1.2.4 (2023-05-22)

### Fix

- **#20**: set commit to HEAD

## 1.2.3 (2023-05-17)

### Refactor

- improve log output on post-copier steps

## 1.2.3rc0 (2023-05-17)

### Fix

- **#18**: ensure a single trailing newline at end of answerfile
- bump minimum pymdown dependency

## 1.2.2 (2023-05-11)

### Fix

- improve logging when run from pre-commit

## 1.2.1 (2023-05-11)

### Fix

- start implementation to replace the src_path

### Refactor

- run calcipy tool suite
- merge stabilization code
- provide better CLI output

## 1.2.0 (2023-04-22)

### Feat

- support templated copier answer files

## 1.2.0rc1 (2023-04-22)

### Fix

- write the commit as '-0' each time

## 1.2.0rc0 (2023-04-22)

### Feat

- remove _commit from the answers file

### Refactor

- experiment with a shadow copy
- use capture_shell
- split the main logic into three files

## 1.1.0 (2023-04-22)

### Feat

- add CLI arguments

### Fix

- correctly handle files in untracked directories
- **#3**: return error in pre-commit on new output directories (#5)
- **#2**: resolve issues in Github Workflows

### Refactor

- switch to the corallium logger

## 1.0.2 (2022-11-20)

### Fix

- use VCS-ref HEAD and remove .git if found

## 1.0.1 (2022-11-20)

### Fix

- use the proper directory for copier run

## 1.0.0 (2022-11-20)

### Feat

- first implementation of ctt
- init with copier

### Fix

- trying to defer to defaults
- use the public run_auto instead of .copy
- remove folder deletion
