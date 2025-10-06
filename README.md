# siege-cli

<img width="485" height="199" alt="siege-build" src="https://github.com/user-attachments/assets/ee82fb2c-ee98-44d4-b491-fa8d8eb62fee" />

siege-cli is a CLI tool for interacting with the [Siege](https://siege.hackclub.com) website.
Currently, listing your projects and updating their information is supported.
Update notes are in a [separate file](UPDATE.md)

## Cookies

siege-cli requires your `_siege_session` and sometimes `cf_clearance` cookies to work.
You might be asked to retrieve them from time to time, if a request gets denied because of them expiring.

In case you are being asked for a cf_clearance and it is not present in the cookie list, it is most likely okay to just create/overwrite the `session.json` file with `{"cf_clearance":""}` to suppress the warning.
This can also be done by pressing Enter to the cf_clearance prompt without pasting anything.

### Firefox

- Open devtools with F12 or right click>Inspect
- Switch to the Storage tab
- In the devtools sidebar, select Cookies>https://siege.hackclub.com
- Triple click the value of the respective cookie and copy it

### Chromium

- Open devtools with F12 or right click>Inspect
- Switch to the Application tab
- In the devtools sidebar, under the Storage group, select Cookies>https://siege.hackclub.com
- Triple click the value of the respective cookie and copy it

## Usage

`py siege.py`/`siege.exe` take subcommands:
list - no other args needed, lists your Siege projects
show - `--id` arg needed, shows info about one of your Siege projects matching the ID
edit - `--id` arg needed, updates properties of your Siege project matching the ID according to the Update flags you pass:\

- `-t TITLE` `--title TITLE` Project display name
- `-b DESC` `--description DESC` Project description
- `-d LINK` `--demo LINK` Link to the project's demo
- `-r LINK` `--repo LINK` Link to the project's repository
- `-s PATH` `--screenshot PATH` Local path from the cwd to the screenshot you want to upload
- `-x` `--remove-screenshot` Flag for removing the current project screenshot
- `-w` `--hackatime HACKATIME_NAME` Name of the hackatime project associated with this project

## Demo

https://github.com/user-attachments/assets/21890ec3-e85b-48b1-8cd9-b8458c5169f1

## Installation

Note: for any pip packages, depending on your system you might need to use your normal package manager to install python packages, or pass --break-system-packages to pip. A venv can also be used.

For the first run, you will be asked to enter your Siege cookies. Read above for an explanation of that process.

### Package

- Create and navigate to the directory you want siege-cli to reside in.
- Run `pipx install siege-cli` or `uvx install siege-cli`
- Run `siege-cli` to get started 

### Pyinstaller

- Create and navigate to the directory you want siege-cli to reside in.
- Download the siege.exe build from the release (`git clone https://github.com/strawberry-p/siege-cli.git` and `cd siege-cli` also works for these steps)
- Run `dist/siege.exe list` or `siege.exe list` to get started

### Python

- Create and navigate to the directory you want siege-cli to reside in.
- Download the `siege.py` file from the repo or from the release (`git clone https://github.com/strawberry-p/siege-cli.git` and `cd siege-cli` also works for these steps)
- Run `py siege.py list` to get started.
