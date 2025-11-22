"""Copier answers file stabilization for deterministic output."""

import re
from functools import lru_cache
from pathlib import Path

from corallium.file_helpers import read_lines
from corallium.log import get_logger

from ._template_config import read_copier_template

logger = get_logger()

DEFAULT_ANSWER_FILE_NAME = '.copier-answers.yml'
"""Default answer file name.

References:
    https://github.com/copier-org/copier/blob/7f05baf4f004a4876fb6158e1c532b28290146a4/copier/subproject.py#L39

"""


@lru_cache(maxsize=1)
def find_answers_file(*, src_path: Path, dst_path: Path) -> Path:
    """Locate the copier answers file based on the copier template.

    Handles both static and templated answer file names. For templated names
    (e.g., `.copier-answers.{{project_name}}.yml`), uses glob pattern matching
    to find the actual generated file.

    Args:
        src_path: Path to the source copier template directory
        dst_path: Path to the destination directory containing the answers file

    Returns:
        Path to the located answers file

    Raises:
        ValueError: If templated filename matches 0 or multiple files
        FileNotFoundError: If copier template file is not found

    """
    copier_config = read_copier_template(src_path)
    answers_filename = copier_config.get('_answers_file') or DEFAULT_ANSWER_FILE_NAME
    if '{{' in answers_filename:
        # If the filename is created from the template, just grab the first match
        # Replace Jinja2 template variables (e.g., {{project_name}}) with glob wildcards
        search_name = re.sub(r'{{[^}]+}}', '*', answers_filename)
        matches = [*dst_path.glob(search_name)]
        if len(matches) != 1:  # pragma: no cover
            msg = f"Can't find just one copier answers file matching {dst_path / search_name}. Found: {matches}"
            raise ValueError(msg)
        return matches[0]
    return dst_path / answers_filename  # pragma: no cover


def stabilize_line(line: str, answers_path: Path) -> str:
    """Stabilize a single line from copier answers file for deterministic output.

    Converts variable values in the copier answers file to deterministic forms:
    - _src_path: Converts absolute paths to relative paths from the answers file
    - _commit: Converts specific commit hashes to 'HEAD' reference

    This ensures that generated templates produce consistent, reproducible output
    regardless of the absolute file system paths or git commit states.

    Args:
        line: A line from the copier answers file
        answers_path: Path to the copier answers file being processed

    Returns:
        The stabilized line with deterministic values, or the original line if no changes needed

    """
    # Convert _src_path to a deterministic relative path
    if line.startswith('_src_path'):
        logger.info('Replacing with deterministic value', line=line)
        raw_path = Path(line.split('_src_path:')[-1].strip())
        ans_dir = answers_path.parent
        if ans_dir.is_relative_to(raw_path):
            count_rel = len(ans_dir.relative_to(raw_path).parts)
            rel_path = '/'.join([*(['..'] * count_rel), raw_path.name])
            return f'_src_path: {rel_path}'
        return line
    # Create a stable tag for '_commit' that copier will still utilize
    if line.startswith('_commit'):
        logger.info('Replacing with deterministic value', line=line)
        return '_commit: HEAD'
    return line


def stabilize_answers_file(*, src_path: Path, dst_path: Path) -> None:
    """Ensure that the answers file contains deterministic values.

    Processes the copier answers file to replace environment-specific values
    (absolute paths, commit hashes) with deterministic equivalents.

    Args:
        src_path: Path to the source copier template directory
        dst_path: Path to the destination directory containing the answers file

    Raises:
        FileNotFoundError: If answers file cannot be located
        ValueError: If multiple potential answers files are found

    """
    answers_path = find_answers_file(src_path=src_path, dst_path=dst_path)
    lines = (stabilize_line(_l, answers_path) for _l in read_lines(answers_path) if _l.strip())
    answers_path.write_text('\n'.join(lines) + '\n')
