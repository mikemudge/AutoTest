# AutoTest
Pull and test your git code.

To run these with cron is not that straight forward.

cron uses a different path to the rest of the world.

we need to update that path to include node and karma.
Karma doesn't like getting installed globally so we have to use the local path.

Crontab -e will let you update the path before the commands like this.
PATH=/Users/mudge/projects/WebPlatform/node_modules/karma/bin:/usr/local/bin:/usr/bin:/bin
crontab doesn't support all shell things (e.g ~ doesn't expand?)

