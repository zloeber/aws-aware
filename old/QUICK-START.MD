## Quick start install guide

Here is an example quick start for team1 PROD on a Linux server with the help of an included Makefile (which can also be used for aws sso auth if required)

```bash
# Choose an environment to deploy (uat or prod)
APP_ENV=prod

# Our base environment definition
MY_DEPLOY_TEMPLATE="./config/team1-${APP_ENV}.env"

# Clone this repo and jump into it
git clone https://github.com/zloeber/aws_aware/aws_aware.git

cd aws-aware

# Set base configuration file to our default via a simple link
rm -rf ./deploy.env
ln -s $MY_DEPLOY_TEMPLATE ./deploy.env

# Setup a new app configuration based on deployment file,
# then run the default set of threshold monitors with new config
# (Note: ensure things work and look as you would expect in the email)
make run-app-config run-app

# Create a scheduled task (4 hours by default) with new config
# (Note: This updates ${HOME}/.local/bin/auto-aws-aware.sh as well)
make dpl=${MY_DEPLOY_TEMPLATE} install-cron-task

# If you want to ensure your makefile targets your env file by default
mv ./deploy.env ./deploy.old
ln -s ./profiles/team1-prod.env ./deploy.env
```

> From here on out, if cron is running for user accounts on that server, you will start to receive notices every 4 hours when your thresholds have been surpassed.

You can also set warning thresholds with subsequent notices by copying the same steps but for multiple deployment files (or just update your newly created auto-script!).
