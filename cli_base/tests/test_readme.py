from manageprojects.tests.base import BaseTestCase

from cli_base import constants
from cli_base.cli_dev import PACKAGE_ROOT
from cli_base.cli_tools.test_utils.assertion import assert_in
from cli_base.cli_tools.test_utils.cli_readme import assert_cli_help_in_readme
from cli_base.cli_tools.test_utils.rich_test_utils import (
    assert_no_color_env,
    assert_rich_click_no_color,
    assert_rich_no_color,
    assert_subprocess_rich_diagnose_no_color,
)
from cli_base.demo.cli import SETTINGS_DIR_NAME, SETTINGS_FILE_NAME
from cli_base.demo.settings import DemoSettings
from cli_base.toml_settings.test_utils.cli_mock import TomlSettingsCliMock


TERM_WIDTH = 100


class ReadmeTestCase(BaseTestCase):
    cli_mock = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        settings_overwrites = dict(
            systemd=dict(
                template_context=dict(
                    user='MockedUserName',
                    group='MockedUserName',
                )
            ),
        )

        cls.cli_mock = TomlSettingsCliMock(
            SettingsDataclass=DemoSettings,
            settings_overwrites=settings_overwrites,
            dir_name=SETTINGS_DIR_NAME,
            file_name=SETTINGS_FILE_NAME,
            width=TERM_WIDTH,
        )
        cls.cli_mock.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        cls.cli_mock.__exit__(None, None, None)

    def test_cli_mock(self):
        assert_no_color_env(width=TERM_WIDTH)
        assert_subprocess_rich_diagnose_no_color(width=TERM_WIDTH)
        assert_rich_no_color(width=TERM_WIDTH)
        assert_rich_click_no_color(width=TERM_WIDTH)

    def invoke_cli(self, *args):
        return self.cli_mock.invoke(cli_bin=PACKAGE_ROOT / 'cli.py', args=args, strip_line_prefix='usage: ')

    def invoke_dev_cli(self, *args):
        return self.cli_mock.invoke(cli_bin=PACKAGE_ROOT / 'dev-cli.py', args=args, strip_line_prefix='usage: ')

    def invoke_demo_cli(self, *args):
        return self.cli_mock.invoke(cli_bin=PACKAGE_ROOT / 'demo-cli.py', args=args, strip_line_prefix='usage: ')

    def assert_readme_block(self, *, text_block: str, marker: str):
        assert_cli_help_in_readme(
            readme_path=PACKAGE_ROOT / 'README.md',
            text_block=text_block,
            marker=marker,
            cli_epilog=constants.CLI_EPILOG,
        )

    def test_main_help(self):
        stdout = self.invoke_cli('--help')
        assert_in(
            content=stdout,
            parts=(
                'usage: ./cli.py [-h]',
                ' version ',
                constants.CLI_EPILOG,
            ),
        )
        self.assert_readme_block(text_block=stdout, marker='app help')

    def test_dev_help(self):
        stdout = self.invoke_dev_cli('--help')
        assert_in(
            content=stdout,
            parts=(
                'usage: ./dev-cli.py [-h]',
                'fix-code-style',
                'tox',
                constants.CLI_EPILOG,
            ),
        )
        self.assert_readme_block(text_block=stdout, marker='dev help')

    def test_demo_help(self):
        stdout = self.invoke_demo_cli('--help')
        assert_in(
            content=stdout,
            parts=(
                'usage: ./demo-cli.py [-h]',
                'edit-settings',
                'demo-endless-loop',
                constants.CLI_EPILOG,
            ),
        )
        self.assert_readme_block(text_block=stdout, marker='demo help')
