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
