
# Update notes

### 1.0.2

A lot of my week 5 time was actually counted when I was fixing up the previous version to account for the site update that broke some things, as well as making a demo (packaging and releasing took me 2 hackatime hours alone sob), and fixing up some weird bugs with screenshot uploading (you can test this by running `siege-cli edit --id ID` without passing `--screenshot`, which previously broke the screenshot rendering)

**Features added:**

- "Last updated" date from the project cards now stored and listed in project view
- Showing coin payouts for projects that received them
- Showing your total coins
- Displaying today's coding time from the /keep page
- Parsing time for each project and displaying the total time you spent on the Siege