from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from packaging.version import Version

from cli_base.cli_tools.git import Git, GitHistoryEntry, GithubInfo, GitlabInfo, get_git


def clean_text(text: str) -> str:
    """
    Clean the text via regex and remove all non-ascii chars and lower it.
    >>> clean_text('A ÄÖÜ äöüß Test Message 123!')
    'a test message 123'
    """
    text = text.lower()
    text = re.sub(r'[^a-z0-9]', ' ', text)  # Remove all non-ascii chars
    text = re.sub(r' +', ' ', text)  # Remove double spaces
    return text.strip()


class TagHistoryRenderer:
    def __init__(
        self,
        *,
        current_version: str,
        skip_prefixes: tuple[str],
        project_info: GithubInfo | GitlabInfo,
        main_branch_name: str = 'main',
        add_author: bool = True,
    ):
        self.current_version = Version(current_version)
        self.skip_prefixes = [txt.lower() for txt in skip_prefixes]
        self.project_info = project_info

        self.main_branch_name = main_branch_name
        self.add_author = add_author

        self.base_url = None  # Must be set in child class!

    def version2str(self, version: Version):
        return f'v{version}'

    def skip(self, comment) -> bool:
        comment = comment.lower()
        for skip_prefix in self.skip_prefixes:
            if comment.startswith(skip_prefix):
                return True
        return False

    def render(self, tags_history: list[GitHistoryEntry]) -> Iterable[str]:
        for entry in tags_history:
            if entry.last == 'HEAD':
                version: Version = entry.tag.version

                release_planing = self.current_version > version
                if release_planing:
                    new_version = self.version2str(self.current_version)
                    compare_url = self.project_info.compare_url(old=entry.next, new=new_version)
                    yield f'* [{new_version}]({compare_url})'
                else:
                    compare_url = self.project_info.compare_url(old=entry.next, new=self.main_branch_name)
                    yield f'* [**dev**]({compare_url})'
            else:
                compare_url = self.project_info.compare_url(old=entry.next, new=entry.last)
                yield f'* [{entry.last}]({compare_url})'

            seen_comments = set()
            for log_line in entry.log_lines:
                if self.skip(log_line.comment):
                    continue

                # Remove duplicate git commits, e.g.: serveral "update requirements" commits ;)
                cleaned_comment = clean_text(log_line.comment)
                if cleaned_comment in seen_comments:
                    continue
                seen_comments.add(cleaned_comment)

                if self.add_author:
                    author = f' {log_line.author}'
                else:
                    author = ''
                yield f'  * {log_line.date.isoformat()}{author} - {log_line.comment}'


def get_git_history(
    *,
    current_version: str,
    cwd: Path | None = None,
    add_author: bool = True,
    skip_prefixes: tuple[str, ...] = ('Release as', 'Prepare release'),
    verbose: bool = False,
) -> Iterable[str]:
    """
    Generate a project history base on git commits/tags.
    """
    git: Git = get_git(cwd=cwd)
    main_branch_name = git.get_main_branch_name(verbose=False)
    project_info = git.get_project_info(verbose=False)
    if project_info:
        tags_history: list[GitHistoryEntry] = git.get_tag_history(verbose=verbose)
        renderer = TagHistoryRenderer(
            current_version=current_version,
            skip_prefixes=skip_prefixes,
            project_info=project_info,
            main_branch_name=main_branch_name,
            add_author=add_author,
        )
        yield from renderer.render(tags_history)


if __name__ == '__main__':
    from cli_base import __version__

    for line in get_git_history(current_version=__version__):
        print(line)