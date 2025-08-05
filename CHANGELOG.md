# Changelog

## v2.5.0

### Added

- Adds `--version` option to display the version of the tool.

## v2.4.0

### Added

- Support Atelier .spd files with different canvas sizes.

### Changed

- Bugfix: Ignore atelier files without sqlite data.
- Bugfix: Improves SPD layer support.

## v2.3.2

### Changed

- Bugfix: Detects bad TID entries and ignores them in atelier file conversion.

## v2.3.1

### Changed

- Bugfix: Adds support for .spd files in 'directory' command.
- Bugfix: Detect .spd files that cannot be decoded correctly.

## v2.3.0

### Added

- Adds support for Supernote Atelier files (.spd files).

## v2.2.0

### Added

- Adds configuration options `output_path_template` and `output_filename_template`
  to allow for customization of the output file path and name and extension.
- Prevents overwriting of output files if they've been modified since they were
  created (override with `--force` option).
- Adds `mtime` and `ctime` to the template variables to support custom date formatting.
- Documentation: adds emacs org-mode and HTML output examples.

### Changed

- The `markdown` template variable has been deprecated in favor of `llm_output`
- Bugfix: ensure metadata files are only created if output is generated.

## v2.1.0

### Added

- Adds support for PDF and PNG files.
- Adds --progress option to show progress bar.

## v2.0.0

### Added

- Support for [any plugin supported by the llm](https://llm.datasette.io/en/stable/plugins/directory.html#remote-apis)  library (gemini, ollama, etc)
- Adds `--model` option to set a specific model
- Adds `api_key` configuration option (replaces `openai_api_key`).

### Changed

- The `openai_api_key` configuration has been deprecated in favor of `api_key`

## v1.0.1

### Changed

- Updates supernotlib (adds support for Manta)
- Bugfix: ensure `prompt` in configuration file is used over the defaults.

## v1.0.0

### Added

- Adds support for a configuration file (thanks @atisharma)
- Adds support for keywords, titles, and links to output template
- Adds unit tests and CI to project.

### Changed

- The order of command line switches has changed (most options go before the file/directory command)

### Removed

- Removes langchain dependency.
- Removes `--template` option (use configuration file instead).

## v0.1.0

### Added

Initial release:

- Add support for supernotes .note format
- Supports conversion of images to markdown
- Can customize the template with --template option.

# About

<https://keepachangelog.com/en/1.1.0/>
