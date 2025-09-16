from coldwatch import cli


def test_run_defaults():
    parser = cli.build_parser()
    args = parser.parse_args(["run"])
    cfg = cli._config_from_args(args)
    assert cfg.db_path == "accessibility_log.db"
    assert cfg.once is False
    assert cfg.capture_text is True


def test_run_no_text_flag():
    parser = cli.build_parser()
    args = parser.parse_args(["run", "--no-text", "--db", "custom.db"])
    cfg = cli._config_from_args(args)
    assert cfg.capture_text is False
    assert cfg.db_path == "custom.db"


def test_analyze_command():
    parser = cli.build_parser()
    args = parser.parse_args(["analyze", "sample.db"])
    assert args.command == "analyze"
    assert args.db == "sample.db"
