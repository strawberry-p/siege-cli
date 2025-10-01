# siege-cli

siege-cli is a CLI tool for interacting with the [Siege](https://siege.hackclub.com) website.
Currently, listing your projects and updating their information is supported.

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

## Installation

Note: for any pip packages, depending on your system you might need to use your normal package manager to install python packages, or pass --break-system-packages to pip. A venv can also be used.

For the first run, you will be asked to enter your Siege cookies. Read above for an explanation of that process.

### Pyinstaller

- Create and navigate to the directory you want siege-cli to reside in.
- Download the siege.exe build from the release (`git clone https://github.com/strawberry-p/siege-cli.git` and `cd siege-cli` also works for these steps)
- Run `dist/siege/siege.exe list` or `siege.exe list` to get started

### Python

- Create and navigate to the directory you want siege-cli to reside in.
- Download the `siege.py` file from the repo or from the release (`git clone https://github.com/strawberry-p/siege-cli.git` and `cd siege-cli` also works for these steps)
- Run `py siege.py list` to get started.
