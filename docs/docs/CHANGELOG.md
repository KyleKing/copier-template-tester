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
